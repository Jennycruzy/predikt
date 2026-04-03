"""
Market Generator — Autonomous market creation from real news.

Rotates through categories: crypto, science, sports, technology, politics, finance, genlayer.
For each cycle:
  1. Fetches real context from NewsService
  2. Uses Venice AI (LLMService) to generate a realistic YES/NO question
  3. Deploys to Base Sepolia BetFactory (staking contract)
  4. Registers on GenLayer intelligent contract (AI resolution)

Run directly:
    python -m backend.cron_market_generator

Or call generate_and_deploy() from the daemon.
"""

import asyncio
import time
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from backend.services.news import news_service
from backend.services.llm import llm_service
from backend.services.chain import chain_service


# ── Category rotation ─────────────────────────────────────────────────────────

CATEGORIES = [
    "crypto",
    "science",
    "sports",
    "technology",
    "politics",
    "finance",
    "genlayer",
]

CATEGORY_DEADLINE_HOURS = {
    "crypto":     24,   # price questions resolve daily
    "science":    72,   # science events may take a few days
    "sports":     48,   # next match / tournament result
    "technology": 48,
    "politics":   72,
    "finance":    24,   # market close same day
    "genlayer":   48,
}


def _next_category(offset: int = 0) -> str:
    """Pick category based on current hour to spread variety."""
    idx = (int(time.time() // 3600) + offset) % len(CATEGORIES)
    return CATEGORIES[idx]


# ── Core generate + deploy ────────────────────────────────────────────────────

async def generate_and_deploy(category: Optional[str] = None) -> dict:
    """
    Full pipeline: fetch news → generate question → deploy to both chains.
    Returns market data dict.
    """
    category = category or _next_category()
    print(f"\n[GEN] Category: {category}")

    # 1. Fetch real context
    print("[GEN] Fetching live context…")
    try:
        context = await news_service.get_context_for_category(category)
    except Exception as exc:
        print(f"[GEN] Context fetch failed ({exc}), using minimal context.")
        context = f"Today is {datetime.utcnow().strftime('%B %d, %Y')} UTC."

    # 2. Generate market question via Venice AI
    deadline_hours = CATEGORY_DEADLINE_HOURS.get(category, 24)
    print("[GEN] Generating market question via Venice AI…")
    market_data = await llm_service.generate_market_question(
        category=category,
        context=context,
        deadline_hours=deadline_hours,
    )

    question       = market_data.get("question", "")
    resolution_hint = market_data.get("resolution_hint", "https://google.com")
    deadline_hours  = int(market_data.get("deadline_hours_from_now", deadline_hours))

    if not question or len(question) < 15:
        question = f"Will a major {category} event occur in the next {deadline_hours} hours?"

    print(f"[GEN] Market: '{question}' (category={category}, deadline={deadline_hours}h)")

    deadline_dt  = datetime.now(timezone.utc) + timedelta(hours=deadline_hours)
    deadline_iso = deadline_dt.isoformat()
    end_ts       = int(deadline_dt.timestamp())

    results = {
        "question":         question,
        "category":         category,
        "deadline_iso":     deadline_iso,
        "end_timestamp":    end_ts,
        "resolution_hint":  resolution_hint,
        "gl_tx":            None,
        "base_market_id":   None,
    }

    # 3. Deploy to Base Sepolia (staking)
    print("[GEN] Deploying to Base Sepolia…")
    try:
        base_market_id = await chain_service.create_market_base_sepolia(
            question=question,
            category=category,
            end_timestamp=end_ts,
            resolution_type=3,  # AI_DEBATE
        )
        results["base_market_id"] = base_market_id
        if base_market_id is not None:
            print(f"[GEN] ✅ Base Sepolia market ID: {base_market_id}")
        else:
            print("[GEN] ⚠️  Base Sepolia deploy returned no ID (check private key / factory)")
    except Exception as exc:
        print(f"[GEN] ❌ Base Sepolia deploy failed: {exc}")

    # 4. Register on GenLayer (AI resolution)
    print("[GEN] Registering on GenLayer Studionet…")
    try:
        gl_tx = await chain_service.create_market_onchain(
            question=question,
            deadline=deadline_iso,
            category=category,
        )
        results["gl_tx"] = gl_tx
        if gl_tx:
            print(f"[GEN] ✅ GenLayer tx: {gl_tx}")
        else:
            print("[GEN] ⚠️  GenLayer returned no tx hash (check CONTRACT_ADDRESS / RPC)")
    except Exception as exc:
        print(f"[GEN] ❌ GenLayer register failed: {exc}")

    print(f"[GEN] ✅ Market generation complete: '{question}'")
    return results


# ── Multi-category burst ──────────────────────────────────────────────────────

async def generate_initial_batch(count: int = 7) -> None:
    """
    Generate one market per category to seed the platform on first run.
    Waits a few seconds between deployments to avoid nonce collisions.
    """
    print(f"[GEN] Generating initial batch of {count} markets…")
    for i, category in enumerate(CATEGORIES[:count]):
        try:
            await generate_and_deploy(category=category)
        except Exception as exc:
            print(f"[GEN] Failed for {category}: {exc}")
        if i < count - 1:
            await asyncio.sleep(5)
    print("[GEN] Initial batch complete.")


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    category_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(generate_and_deploy(category=category_arg))
