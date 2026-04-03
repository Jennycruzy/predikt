"""
Pydantic models for API request/response validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────

class CreateMarketRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)
    deadline_hours: int = Field(default=168, ge=1, le=8760)  # 1h to 1yr
    category: str = Field(default="general")
    num_validators: int = Field(default=5, ge=2, le=10)
    debate_rounds: int = Field(default=2, ge=1, le=5)


class RunDebateRequest(BaseModel):
    market_id: str
    additional_context: Optional[str] = None
    num_rounds: int = Field(default=2, ge=1, le=5)


class PredictRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)
    category: str = Field(default="general")


# ── Responses ─────────────────────────────────────────

class ValidatorResult(BaseModel):
    model: str
    prediction: float
    score: float
    challenged: bool = False
    reasoning_preview: str = ""
    reasoning: str = ""  # full reasoning for UI display


class CreateMarketResponse(BaseModel):
    market_id: str
    question: str
    category: str
    deadline: str
    status: str
    message: str


class DebateResponse(BaseModel):
    market_id: str
    predikt: float
    confidence: float
    validators: List[ValidatorResult]
    debate_rounds: int
    total_challenges: int
    status: str
    rounds_data: List[Dict[str, Any]] = []  # structured round data for UI


class MarketSummary(BaseModel):
    id: str
    question: str
    category: str
    status: str
    predikt: Optional[float] = None
    confidence: Optional[float] = None
    validator_count: int
    total_yes: float = 0.0
    total_no: float = 0.0
    created_at: str
    deadline: str


class ValidatorStats(BaseModel):
    model: str
    score: float
    markets_participated: int
    accuracy_history: List[float]
    avg_accuracy: float


class MarketListResponse(BaseModel):
    markets: List[MarketSummary]


class ValidatorListResponse(BaseModel):
    validators: List[ValidatorStats]
