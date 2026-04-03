import asyncio
import os
from dotenv import load_dotenv

# Load environment variables FIRST before importing services
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from services.llm import llm_service
from services.chain import chain_service

async def verify():
    print("🚀 Verifying Venice and GenLayer Integration...\n")
    
    # 1. Verify Venice
    print("📡 Testing Venice API...")
    try:
        response = await llm_service.generate_prediction(
            model="venice:llama-3.3-70b", 
            market_question="Will Bitcoin hit $100k in 2024?"
        )
        print(f"✅ Venice Response: {response.content[:100]}...\n")
    except Exception as e:
        print(f"❌ Venice API Error: {e}\n")

    # 2. Verify GenLayer
    print("📡 Testing GenLayer SDK...")
    print(f"RPC URL: {os.getenv('GENLAYER_RPC_URL')}")
    print(f"Contract: {os.getenv('CONTRACT_ADDRESS')}")
    
    try:
        # Test a read call
        market_count = await chain_service.get_market_onchain(0)
        print(f"✅ GenLayer Connection: Success (Market 0 status: {market_count})")
    except Exception as e:
        print(f"❌ GenLayer Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
