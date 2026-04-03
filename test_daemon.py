import asyncio
from backend.market_daemon import run_automation, check_and_resolve_markets

async def test_cycle():
    print("🧪 [TEST] Starting one-time autonomous cycle...")
    
    # 1. Test Generation
    await run_automation()
    
    # 2. Test Resolution Check
    await check_and_resolve_markets()
    
    print("🧪 [TEST] Cycle complete.")

if __name__ == "__main__":
    asyncio.run(test_cycle())
