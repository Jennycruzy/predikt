"""
Data models for markets, predictions, and debate rounds.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum


class MarketStatus(str, Enum):
    OPEN = "open"
    DEBATING = "debating"
    FINALIZING = "finalizing"
    FINALIZED = "finalized"


class ChallengeType(str, Enum):
    LOGICAL_FLAW = "logical_flaw"
    EVIDENCE_GAP = "evidence_gap"
    BIAS = "bias"
    CONTRADICTION = "contradiction"


@dataclass
class ValidatorPrediction:
    """A single validator's prediction with reasoning."""
    model: str
    prediction: float              # 0.0–1.0 probability
    reasoning: str                 # Full reasoning text
    reasoning_hash: str            # SHA-256 hash for on-chain storage
    score: float = 0.5             # Reasoning quality score (0–1)
    challenged: bool = False
    challenges_received: List[Dict] = field(default_factory=list)


@dataclass
class DebateRound:
    """A single round of debate containing critiques."""
    round_num: int
    critiques: List[Dict] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class Market:
    """Complete prediction market with all state."""
    id: str
    question: str
    category: str
    deadline: str
    status: MarketStatus = MarketStatus.OPEN
    created_at: str = ""
    validators: List[ValidatorPrediction] = field(default_factory=list)
    debate_rounds: List[DebateRound] = field(default_factory=list)
    predikt: Optional[float] = None
    confidence: Optional[float] = None
    reasoning_tree: Optional[Dict] = None
    reasoning_summary: Optional[str] = None

    def to_summary(self) -> Dict:
        """Return a lightweight summary for list views."""
        return {
            "id": self.id,
            "question": self.question,
            "category": self.category,
            "status": self.status.value,
            "predikt": self.predikt,
            "confidence": self.confidence,
            "validator_count": len(self.validators),
            "created_at": self.created_at,
            "deadline": self.deadline,
        }

    def to_full(self) -> Dict:
        """Return the complete market payload."""
        return {
            "market_id": self.id,
            "question": self.question,
            "category": self.category,
            "status": self.status.value,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "predikt": self.predikt,
            "confidence": self.confidence,
            "validators": [
                {
                    "model": v.model,
                    "prediction": v.prediction,
                    "score": v.score,
                    "reasoning": v.reasoning,
                    "reasoning_hash": v.reasoning_hash,
                    "challenged": v.challenged,
                }
                for v in self.validators
            ],
            "debate_rounds": [
                {
                    "round": r.round_num,
                    "critiques": r.critiques,
                    "timestamp": r.timestamp,
                }
                for r in self.debate_rounds
            ],
            "reasoning_summary": self.reasoning_summary,
        }
