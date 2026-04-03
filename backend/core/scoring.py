"""
Reasoning Quality Scoring System

Scores each validator's reasoning based on:
  - Evidence usage (depth and structure of reasoning)
  - Peer agreement (distance from median prediction)
  - Historical reputation
  - Challenge outcomes (penalty for valid challenges)

This is the core differentiator from traditional prediction markets:
predictions are weighted by reasoning quality, NOT by capital.
"""

from typing import List, Dict

from backend.models.market import ValidatorPrediction
from backend.models.validator import DEFAULT_REPUTATION


# Weight configuration for scoring components
WEIGHTS = {
    "evidence": 0.25,      # How deep and structured is the reasoning?
    "agreement": 0.30,     # How close to the group median?
    "reputation": 0.25,    # Historical accuracy track record
    "challenge": 0.20,     # Penalty for valid challenges received
}

# Thresholds
EVIDENCE_CHAR_CAP = 500    # Reasoning length normalization cap
CHALLENGE_PENALTY = 0.10   # Per valid challenge received
MIN_SCORE = 0.10
MAX_SCORE = 1.00


def score_evidence_usage(reasoning: str) -> float:
    """
    Score based on reasoning depth and structure.
    Longer, more structured reasoning scores higher (up to cap).
    """
    length = len(reasoning)
    # Number of distinct reasoning points (lines)
    num_points = len([l for l in reasoning.split("\n") if l.strip()])

    length_score = min(1.0, length / EVIDENCE_CHAR_CAP)
    structure_score = min(1.0, num_points / 6)  # Expect ~6 points

    return (length_score * 0.6 + structure_score * 0.4)


def score_peer_agreement(
    prediction: float,
    all_predictions: List[float],
) -> float:
    """
    Score based on proximity to the median prediction.
    Closer to median = higher agreement score.
    """
    sorted_preds = sorted(all_predictions)
    median = sorted_preds[len(sorted_preds) // 2]
    distance = abs(prediction - median)
    return max(0.0, 1.0 - distance * 2)


def score_reputation(model: str, reputation_store: Dict) -> float:
    """
    Score based on historical reputation.
    Normalized to 0–1 from the 1–10 reputation scale.
    """
    rep = reputation_store.get(model, DEFAULT_REPUTATION.get(model, {}))
    raw_score = rep.get("score", 5.0)
    return raw_score / 10.0


def score_challenge_outcomes(
    model: str,
    challenges: List[Dict],
) -> float:
    """
    Calculate penalty from valid challenges.
    Each valid challenge against this model reduces the score.
    """
    valid_challenges = [
        c for c in challenges
        if c["target"] == model and c.get("valid", False)
    ]
    penalty = len(valid_challenges) * CHALLENGE_PENALTY
    return max(0.0, 1.0 - penalty)


def score_reasoning(
    prediction: ValidatorPrediction,
    all_predictions: List[ValidatorPrediction],
    challenges: List[Dict],
    reputation_store: Dict,
) -> float:
    """
    Compute the composite reasoning quality score for a validator.

    Args:
        prediction: The validator's prediction to score
        all_predictions: All predictions in this market
        challenges: All challenges from all debate rounds
        reputation_store: Current reputation data for all validators

    Returns:
        Float score between MIN_SCORE and MAX_SCORE
    """
    all_pred_values = [p.prediction for p in all_predictions]

    evidence = score_evidence_usage(prediction.reasoning)
    agreement = score_peer_agreement(prediction.prediction, all_pred_values)
    reputation = score_reputation(prediction.model, reputation_store)
    challenge = score_challenge_outcomes(prediction.model, challenges)

    composite = (
        evidence * WEIGHTS["evidence"]
        + agreement * WEIGHTS["agreement"]
        + reputation * WEIGHTS["reputation"]
        + challenge * WEIGHTS["challenge"]
    )

    return round(max(MIN_SCORE, min(MAX_SCORE, composite)), 4)
