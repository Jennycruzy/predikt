"""
predikt Market Daemon — Autonomous market lifecycle manager.

Responsibilities:
  1. Periodic market generation (new markets every 6 hours, one per category)
  2. Check expired markets → trigger AI debate → bridge resolution to Base Sepolia

Run:
    python -m backend.market_daemon
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from backend.services.chain import chain_service
from backend.cron_market_generator import generate_and_deploy, generate_initial_batch
from backend.core import debate_engine
from backend.core.predikt import compute_predikt, generate_summary
from backend.core.reputation import reputation_manager
from backend.services.storage import storage_service
from backend.services.llm import parse_json

# Intervals (seconds)
GENERATION_INTERVAL = 6 * 3600   # new market every 6 hours
JUDGING_INTERVAL    = 2 * 60     # check for expired markets every 2 min
FIRST_BATCH         = bool(os.getenv("GENERATE_INITIAL_BATCH", "true").lower() == "true")


# ── Real-world outcome determination ────────────────────────────────────────

async def determine_actual_outcome(question: str, category: str, deadline: str) -> tuple:
    """
    Ask Venice AI to determine the ACTUAL real-world outcome — did the event
    happen (YES) or not (NO)?  This is a factual query, not a prediction.
    Returns (resolved_yes: bool | None, confidence: float).
    None means the call failed and the caller should fall back to debate consensus.
    """
    from backend.services.llm import llm_service, parse_json

    system_prompt = (
        "You are a market resolution judge for a prediction market platform. "
        "Your sole job is to determine whether a prediction market question resolved "
        "YES or NO based on what ACTUALLY happened in the real world by the deadline. "
        "Use your knowledge of real events, prices, and outcomes. "
        "Do NOT predict what will happen — determine what DID happen. "
        "Be definitive. Output only valid JSON."
    )

    user_prompt = (
        f"Market question: {question}\n"
        f"Category: {category}\n"
        f"Resolution deadline: {deadline}\n\n"
        "Did this event actually occur / resolve YES or NO by the deadline?\n"
        "Answer ONLY with this JSON (no other text):\n"
        '{"outcome": "YES" or "NO", "confidence": <integer 0-100>, '
        '"reasoning": "<one sentence: what actually happened>"}'
    )

    try:
        resp = await llm_service._call(
            model="llama-3.3-70b",
            system=system_prompt,
            user=user_prompt,
            temperature=0.1,
            max_tokens=200,
        )
        data = parse_json(resp.content)
        if not data or "outcome" not in data:
            return None, 0.5
        outcome_str = str(data.get("outcome", "")).strip().upper()
        confidence  = float(data.get("confidence", 50)) / 100.0
        reasoning   = data.get("reasoning", "")
        resolved_yes = outcome_str == "YES"
        print(f"[DAEMON] Real-world outcome: {outcome_str} (conf={confidence:.0%}) — {reasoning}")
        return resolved_yes, confidence
    except Exception as exc:
        print(f"[DAEMON] Real-world outcome call failed: {exc}")
        return None, 0.5


# ── Debate + resolution pipeline ─────────────────────────────────────────────

async def run_debate_and_resolve(market_id: int, market: dict) -> None:
    """
    Full AI debate pipeline for an expired market:
      1. Generate predictions from all 5 validators (Venice AI)
      2. Run 2 debate rounds with cross-critiques
      3. Score reasoning quality
      4. Compute intelligence-weighted predikt
      5. Finalize on GenLayer intelligent contract
      6. Use contract's AI resolution to fetch real-world data
      7. Bridge result to Base Sepolia
    """
    question = market.get("question", "")
    category = market.get("category", "general")
    print(f"\n[DAEMON] ⚖️  Debating market {market_id}: '{question[:60]}…'")

    # ── Phase 1: Parallel predictions ────────────────────────────────────────
    predictions = await debate_engine.generate_all_predictions(
        question=question,
        category=category,
    )
    if not predictions:
        print(f"[DAEMON] No predictions generated for market {market_id}, skipping.")
        return

    # Submit predictions to GenLayer contract
    for pred in predictions:
        await chain_service.submit_prediction_onchain(
            market_id=market_id,
            prediction=int(pred.prediction * 100),
            reasoning_hash=pred.reasoning_hash,
            model_name=pred.model,
        )

    # ── Phase 2: Debate rounds ────────────────────────────────────────────────
    debate_rounds, all_critiques = await debate_engine.run_debate_rounds(
        predictions=predictions,
        question=question,
        num_rounds=2,
    )

    # Submit challenges to GenLayer
    for critique in all_critiques:
        if critique.get("valid"):
            from backend.services.chain import hash_reasoning
            await chain_service.submit_challenge_onchain(
                market_id=market_id,
                target_validator=critique["target"],
                challenge_hash=hash_reasoning(critique["critique"]),
                challenge_type=critique["type"],
            )

    # ── Phase 3: Score ────────────────────────────────────────────────────────
    rep_store = reputation_manager.get_all()
    predictions = await debate_engine.score_predictions(
        predictions=predictions,
        question=question,
        critiques=all_critiques,
        reputation_store=rep_store,
    )

    # ── Phase 4: Compute predikt ──────────────────────────────────────────────
    predikt_val, confidence_val = compute_predikt(predictions)
    print(f"[DAEMON] Predikt: {predikt_val:.1%}, Confidence: {confidence_val:.1%}")

    # ── Phase 5: Generate summary & store off-chain ───────────────────────────
    from backend.models.market import Market as MarketModel, MarketStatus

    mock_market = MarketModel(
        id=str(market_id),
        question=question,
        category=category,
        deadline=market.get("deadline", ""),
        validators=predictions,
        debate_rounds=debate_rounds,
        predikt=predikt_val,
        confidence=confidence_val,
    )
    summary      = generate_summary(mock_market)
    summary_hash = storage_service.store_summary(str(market_id), summary)

    # ── Phase 6: Finalize on GenLayer ─────────────────────────────────────────
    await chain_service.finalize_onchain(
        market_id=market_id,
        predikt=int(predikt_val * 100),
        confidence=int(confidence_val * 100),
        summary_hash=summary_hash,
    )

    # ── Phase 7: GenLayer AI resolution (fetches live web data) ──────────────
    resolution_url = _build_resolution_url(question, category)
    print(f"[DAEMON] Triggering GenLayer AI resolution: {resolution_url[:80]}")
    await chain_service.resolve_market_onchain(
        market_id=market_id,
        resolution_url=resolution_url,
    )

    # ── Phase 8: Update reputations ───────────────────────────────────────────
    reputation_manager.update_after_predikt(predictions, predikt_val)

    # ── Phase 9: Determine actual real-world outcome ──────────────────────────
    # Primary: ask Venice AI what ACTUALLY happened (factual, not predictive).
    # Fallback: use debate consensus (predikt >= 0.5) if the factual call fails.
    actual_yes, actual_conf = await determine_actual_outcome(
        question=question,
        category=category,
        deadline=market.get("deadline", ""),
    )
    if actual_yes is not None:
        resolved_yes = actual_yes
        print(f"[DAEMON] Using real-world outcome: YES={resolved_yes} (conf={actual_conf:.0%})")
    else:
        resolved_yes = predikt_val >= 0.5
        print(f"[DAEMON] Falling back to debate consensus: YES={resolved_yes} (predikt={predikt_val:.1%})")

    # ── Phase 10: Bridge to Base Sepolia ──────────────────────────────────────
    await chain_service.resolve_on_base_sepolia(
        market_id=market_id,
        resolved_yes=resolved_yes,
        consensus=int(predikt_val * 100),
        confidence=int(confidence_val * 100),
        summary_hash=summary_hash,
    )
    print(f"[DAEMON] ✅ Market {market_id} resolved: YES={resolved_yes} "
          f"(predikt={predikt_val:.1%})")


def _build_resolution_url(question: str, category: str) -> str:
    """Build a resolution URL the GenLayer contract can fetch for AI verification."""
    import urllib.parse
    q = urllib.parse.quote_plus(question)
    urls = {
        "crypto":     f"https://api.coingecko.com/api/v3/search?query={q}",
        "sports":     f"https://www.google.com/search?q={q}",
        "technology": f"https://news.ycombinator.com/search?q={q}",
        "science":    f"https://www.google.com/search?q={q}+site:nature.com+OR+site:nasa.gov",
        "finance":    f"https://finance.yahoo.com/quote/{q}",
        "politics":   f"https://www.google.com/search?q={q}",
        "genlayer":   "https://studio.genlayer.com",
    }
    return urls.get(category, f"https://www.google.com/search?q={q}")


# ── Market lifecycle loop ─────────────────────────────────────────────────────

async def check_and_resolve_markets() -> None:
    """Find expired open markets and trigger AI debate. Uses Base Sepolia as fallback."""
    print("[DAEMON] Checking for expired markets…")
    now = datetime.now(timezone.utc)

    markets_to_check: list[tuple[int, dict]] = []
    seen_ids: set[int] = set()

    # Try GenLayer first
    count = await chain_service.get_market_count_onchain()
    if count > 0:
        for i in range(count):
            market = await chain_service.get_market_onchain(i)
            if market:
                markets_to_check.append((i, market))
                seen_ids.add(i)

    # Always fall back to Base Sepolia (primary when GenLayer is unavailable)
    try:
        bs_markets = await chain_service.get_all_markets_base_sepolia()
        for m in bs_markets:
            mid = int(m.get("id", -1))
            if mid >= 0 and mid not in seen_ids:
                markets_to_check.append((mid, m))
                seen_ids.add(mid)
    except Exception as exc:
        print(f"[DAEMON] Base Sepolia fetch error: {exc}")

    if not markets_to_check:
        print("[DAEMON] No markets found on any chain.")
        return

    print(f"[DAEMON] Evaluating {len(markets_to_check)} market(s)…")

    for market_id, market in markets_to_check:
        status = market.get("status", "")
        deadline_str = market.get("deadline", "")

        if status not in ("open", "debating"):
            continue

        if not deadline_str:
            continue

        try:
            deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        if now <= deadline:
            remaining = (deadline - now).total_seconds() / 60
            print(f"[DAEMON] Market {market_id} active — {remaining:.0f} min remaining.")
            continue

        # Expired — transition to DEBATING and run debate
        print(f"[DAEMON] Market {market_id} EXPIRED — triggering debate…")
        try:
            await chain_service.start_debate_base_sepolia(market_id)
            await run_debate_and_resolve(market_id, market)
        except Exception as exc:
            print(f"[DAEMON] ❌ Debate failed for market {market_id}: {exc}")


# ── Main loop ─────────────────────────────────────────────────────────────────

async def main() -> None:
    print("🚀 predikt Market Daemon starting…")

    # Seed initial markets if requested
    if FIRST_BATCH:
        gl_count = await chain_service.get_market_count_onchain()
        bs_count = 0
        try:
            bs_markets = await chain_service.get_all_markets_base_sepolia()
            bs_count = len(bs_markets)
        except Exception:
            pass
        total_existing = gl_count + bs_count
        if total_existing == 0:
            print("[DAEMON] No markets found — generating initial batch…")
            await generate_initial_batch(count=7)
        else:
            print(f"[DAEMON] {total_existing} market(s) already exist (GL={gl_count}, Base={bs_count}).")

    last_gen = 0.0

    while True:
        # ── Resolution check (every 15 min) ──────────────────────────────────
        try:
            await check_and_resolve_markets()
        except Exception as exc:
            print(f"[DAEMON] Resolution cycle error: {exc}")

        # ── Generation (every 6 hours) ────────────────────────────────────────
        import time
        if time.time() - last_gen > GENERATION_INTERVAL:
            print("\n[DAEMON] ⚡ Generating new market…")
            try:
                await generate_and_deploy()
                last_gen = time.time()
            except Exception as exc:
                print(f"[DAEMON] Generation failed: {exc}")

        print(f"\n[DAEMON] Sleeping {JUDGING_INTERVAL // 60} min…")
        await asyncio.sleep(JUDGING_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
