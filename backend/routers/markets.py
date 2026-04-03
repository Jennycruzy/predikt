"""
Markets Router

Markets are created exclusively by the automated daemon (GenLayer intelligent
contracts + Venice AI news analysis). Users cannot create markets directly —
staking on YES/NO happens through the Base Sepolia BetFactory contracts.
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.models.schemas import MarketSummary, MarketListResponse
from backend.services.chain import chain_service

router = APIRouter(tags=["markets"])

# ── Simple in-memory cache (30 s TTL) ────────────────────────────────────────
_cache: dict = {"ts": 0.0, "data": None}
_CACHE_TTL = 30  # seconds


# ── List markets ──────────────────────────────────────────────────────────────

@router.get("/markets", response_model=MarketListResponse)
async def list_markets():
    """
    Return all prediction markets.
    Primary source: GenLayer Studionet intelligent contract.
    Fallback: Base Sepolia BetFactory (includes live stake totals).
    Cached for 30 s to avoid re-fetching 40+ contracts on every request.
    """
    now = time.time()
    if _cache["data"] is not None and now - _cache["ts"] < _CACHE_TTL:
        return _cache["data"]

    gl_markets = []
    try:
        gl_markets = await chain_service.get_all_markets_onchain()
    except Exception as exc:
        print(f"[MARKETS] GenLayer fetch failed: {exc}")

    if not gl_markets:
        print("[MARKETS] Falling back to Base Sepolia…")
        try:
            gl_markets = await chain_service.get_all_markets_base_sepolia()
        except Exception as exc:
            print(f"[MARKETS] Base Sepolia fetch failed: {exc}")

    if not gl_markets:
        return MarketListResponse(markets=[])

    markets = []
    for m in gl_markets:
        predikt_raw    = m.get("predikt", -1)
        confidence_raw = m.get("confidence", -1)
        markets.append(MarketSummary(
            id              = str(m.get("id", "")),
            question        = m.get("question", ""),
            category        = m.get("category", "general"),
            status          = m.get("status", "open"),
            predikt         = float(predikt_raw) / 100.0
                              if predikt_raw not in (-1, None) else None,
            confidence      = float(confidence_raw) / 100.0
                              if confidence_raw not in (-1, None) else None,
            validator_count = int(m.get("validator_count", 0)),
            total_yes       = float(m.get("total_yes", 0.0)),
            total_no        = float(m.get("total_no", 0.0)),
            created_at      = m.get("created_at", datetime.now(timezone.utc).isoformat()),
            deadline        = m.get("deadline", ""),
        ))

    result = MarketListResponse(markets=markets)
    _cache["ts"] = time.time()
    _cache["data"] = result
    return result


# ── Single market ─────────────────────────────────────────────────────────────

@router.get("/markets/{market_id}")
async def get_market(market_id: str):
    """Return full market detail including on-chain predictions."""
    try:
        mid = int(market_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="market_id must be an integer")

    market = await chain_service.get_market_onchain(mid)
    if not market:
        # Fall back to Base Sepolia
        try:
            bs_markets = await chain_service.get_all_markets_base_sepolia()
            for m in bs_markets:
                if int(m.get("id", -1)) == mid:
                    market = m
                    break
        except Exception:
            pass

    if not market:
        raise HTTPException(status_code=404, detail=f"Market {mid} not found")

    predictions = await chain_service.get_predictions_onchain(mid)
    return {**market, "predictions": predictions}


# ── Market creation is disabled for users ─────────────────────────────────────

@router.post("/create-market")
async def create_market_disabled():
    """
    Market creation is automated by the predikt daemon.
    In a future version, users who hold sufficient mUSDL may propose markets.
    """
    raise HTTPException(
        status_code=403,
        detail=(
            "Market creation is currently automated by the predikt daemon. "
            "Markets are generated from crypto, science, sports, and world news "
            "every few hours via GenLayer intelligent contracts. "
            "Stay tuned — staker-created markets are on the roadmap."
        ),
    )


# ── Manual resolution trigger (admin) ────────────────────────────────────────

@router.post("/resolve-market/{market_id}")
async def resolve_market(market_id: str, resolution_url: str = ""):
    """
    Admin endpoint: manually trigger AI resolution for a specific market.
    The GenLayer intelligent contract fetches live data from resolution_url.
    """
    try:
        mid = int(market_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="market_id must be an integer")

    if not resolution_url:
        market = await chain_service.get_market_onchain(mid)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        import urllib.parse
        resolution_url = (
            "https://www.google.com/search?q="
            + urllib.parse.quote_plus(market.get("question", ""))
        )

    tx = await chain_service.resolve_market_onchain(mid, resolution_url)
    return {
        "status":         "resolution_triggered",
        "market_id":      mid,
        "resolution_url": resolution_url,
        "tx_hash":        tx,
    }
