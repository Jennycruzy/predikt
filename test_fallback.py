import asyncio
from backend.services.chain import chain_service

async def test():
    print("Testing Base Sepolia Fallback...")
    markets = await chain_service.get_all_markets_base_sepolia()
    print(f"Final Count: {len(markets)}")
    for m in markets:
        print(f" - {m['id']}: {m['question']}")

if __name__ == "__main__":
    asyncio.run(test())
