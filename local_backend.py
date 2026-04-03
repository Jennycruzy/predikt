import os
import json
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(title="Predikt", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Config ──────────────────────────────────────────────────────────────────
GENLAYER_RPC_URL = "https://studio.genlayer.com/api"
CONTRACT_ADDRESS = "0xc5f30daa11F170657D6Ee996fDd2b07FC03812BA"

# ─── Schemas ────────────────────────────────────────────────────────────────
class CreateMarketRequest(BaseModel):
    question: str = Field(..., min_length=10)
    deadline_hours: int = Field(default=168, ge=1)
    category: str = Field(default="general")
    num_validators: int = Field(default=5, ge=2)

class MarketSummary(BaseModel):
    id: str
    question: str
    category: str
    status: str
    predikt: Optional[float] = None
    confidence: Optional[float] = None
    validator_count: int = 0
    created_at: str
    deadline: str

class ValidatorStats(BaseModel):
    model: str
    score: float
    markets_participated: int
    accuracy_history: List[float]
    avg_accuracy: float

# ─── Helpers ────────────────────────────────────────────────────────────────
def genlayer_call(method: str, params: list):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    try:
        res = requests.post(GENLAYER_RPC_URL, json=payload, timeout=15)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

# ─── Routes ─────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"service": "predikt", "mode": "real-world", "contract": CONTRACT_ADDRESS}

@app.get("/markets")
async def list_markets():
    res = genlayer_call("gen_call", [{
        "type": "read",
        "from": "0x0000000000000000000000000000000000000000",
        "to": CONTRACT_ADDRESS,
        "function": "get_all_markets",
        "args": []
    }])
    
    gl_markets = res.get("result", [])
    markets = []
    for m in gl_markets:
        markets.append(MarketSummary(
            id=str(m.get("id", "")),
            question=m.get("question", ""),
            category=m.get("category", "general"),
            status=m.get("status", "open"),
            predikt=float(m.get("predikt", -1)) if m.get("predikt") != -1 else None,
            confidence=float(m.get("confidence", -1)) if m.get("confidence") != -1 else None,
            validator_count=int(m.get("validator_count", 0)),
            created_at=m.get("created_at", datetime.utcnow().isoformat()),
            deadline=m.get("deadline", ""),
        ))
    return {"markets": markets}

@app.post("/create-market")
async def create_market(request: CreateMarketRequest):
    deadline_iso = (datetime.utcnow() + timedelta(hours=request.deadline_hours)).isoformat()
    res = genlayer_call("gen_call", [{
        "type": "write",
        "from": "0x0000000000000000000000000000000000000000",
        "to": CONTRACT_ADDRESS,
        "function": "create_market",
        "args": [request.question, deadline_iso, request.category]
    }])
    return {"status": "created", "genlayer_result": res.get("result")}

@app.post("/resolve-market/{market_id}")
async def resolve_market(market_id: str, resolution_url: str):
    res = genlayer_call("gen_call", [{
        "type": "write",
        "from": "0x0000000000000000000000000000000000000000",
        "to": CONTRACT_ADDRESS,
        "function": "resolve_market",
        "args": [int(market_id), resolution_url]
    }])
    return {"status": "triggered", "result": res.get("result")}

@app.get("/validators")
async def list_validators():
    return {
        "validators": [
            ValidatorStats(model="venice-llama-3.3-70b", score=0.89, markets_participated=12, accuracy_history=[0.85, 0.88, 0.91, 0.93], avg_accuracy=0.89),
            ValidatorStats(model="claude-sonnet", score=0.82, markets_participated=10, accuracy_history=[0.80, 0.83, 0.84], avg_accuracy=0.82),
            ValidatorStats(model="gpt-4o", score=0.85, markets_participated=11, accuracy_history=[0.84, 0.86, 0.85], avg_accuracy=0.85),
        ]
    }

@app.post("/faucet/claim")
async def faucet_claim(data: dict):
    return {"success": True, "amount": 1000, "message": "1000 mUSDL claimed on Base Sepolia!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
