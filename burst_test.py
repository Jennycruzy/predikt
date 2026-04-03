import asyncio
from backend.market_daemon import generate_market_data, deploy_to_base_sepolia, deploy_to_genlayer

async def burst():
    initial_categories = ["crypto", "genlayer", "finance"]
    print(f"🧪 [TEST] Starting burst of {len(initial_categories)} markets...")
    for cat in initial_categories:
        try:
            print(f"🧪 [TEST] Burst: Generating {cat} market...")
            data = generate_market_data(category=cat)
            deploy_to_base_sepolia(data)
            deploy_to_genlayer(data)
        except Exception as e:
            print(f"❌ [TEST] Burst failed for {cat}: {e}")
        await asyncio.sleep(2)
    print("🧪 [TEST] Burst complete.")

if __name__ == "__main__":
    asyncio.run(burst())
