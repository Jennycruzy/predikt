"""
AI Debate Engine — Real async AI debate via Venice API.

Flow per market:
  1. All 5 validators independently generate predictions (async, parallel)
  2. N debate rounds: each validator critiques at least one other
  3. Defenders respond to critiques
  4. Scoring: evidence quality, peer agreement, reputation, challenge penalty
  5. Intelligence-weighted predikt computed
  6. Results submitted to GenLayer intelligent contract
"""

import asyncio
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from backend.models.market import ValidatorPrediction, DebateRound
from backend.models.validator import VALIDATOR_PROFILES
from backend.services.llm import llm_service, parse_json


# ── Prediction generation ─────────────────────────────────────────────────────

async def generate_prediction(
    model: str,
    question: str,
    category: str,
    context: Optional[str] = None,
) -> ValidatorPrediction:
    """
    Ask a validator LLM to predict a market question.
    Falls back to a structured estimate if the LLM call fails.
    """
    try:
        resp   = await llm_service.generate_prediction(
            validator=model,
            market_question=question,
            context=context,
            category=category,
        )
        parsed = parse_json(resp.content)
        if parsed and "probability" in parsed:
            prob      = max(1, min(99, int(parsed["probability"])))
            reasoning = (
                f"{parsed.get('reasoning', '')}\n"
                f"Key factors: {', '.join(parsed.get('key_factors', []))}\n"
                f"Risks: {parsed.get('risks', '')}"
            ).strip()
            reasoning_hash = _hash(reasoning)
            return ValidatorPrediction(
                model=model,
                prediction=prob / 100.0,
                reasoning=reasoning,
                reasoning_hash=reasoning_hash,
                score=0.5,
            )
    except Exception as exc:
        print(f"[DEBATE] {model} prediction failed: {exc}")

    # Structured fallback using persona profile
    profile    = VALIDATOR_PROFILES.get(model, VALIDATOR_PROFILES["gpt-4o"])
    low, high  = profile["confidence_range"]
    import random
    prob       = int((low + high) / 2 * 100 + random.uniform(-5, 5))
    prob       = max(5, min(95, prob))
    reasoning  = (
        f"[{model}] Analysis of '{question}': Based on {profile['bias_toward']} approach, "
        f"estimated probability is {prob}%. {profile['description']}."
    )
    return ValidatorPrediction(
        model=model,
        prediction=prob / 100.0,
        reasoning=reasoning,
        reasoning_hash=_hash(reasoning),
        score=0.5,
    )


async def generate_all_predictions(
    question: str,
    category: str,
    context: Optional[str] = None,
    models: Optional[List[str]] = None,
) -> List[ValidatorPrediction]:
    """Run all validator predictions in parallel."""
    if models is None:
        models = list(VALIDATOR_PROFILES.keys())
    tasks = [
        generate_prediction(model, question, category, context)
        for model in models
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    preds = []
    for model, r in zip(models, results):
        if isinstance(r, ValidatorPrediction):
            preds.append(r)
        else:
            print(f"[DEBATE] {model} returned exception: {r}")
    return preds


# ── Debate rounds ─────────────────────────────────────────────────────────────

async def run_debate_rounds(
    predictions: List[ValidatorPrediction],
    question: str,
    num_rounds: int = 2,
) -> Tuple[List[DebateRound], List[Dict]]:
    """
    Each round: every validator critiques one other validator.
    Defenders respond to valid critiques.
    Returns (debate_rounds list, flat critiques list).
    """
    debate_rounds: List[DebateRound] = []
    all_critiques: List[Dict] = []

    for round_num in range(1, num_rounds + 1):
        round_critiques: List[Dict] = []
        critique_tasks = []

        # Each validator challenges the one with the most different probability
        for pred in predictions:
            others = [p for p in predictions if p.model != pred.model]
            if not others:
                continue
            # Target the validator with the most different view
            target = max(others, key=lambda p: abs(p.prediction - pred.prediction))
            critique_tasks.append(
                _run_single_critique(pred, target, question)
            )

        results = await asyncio.gather(*critique_tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict):
                round_critiques.append(r)
                all_critiques.append(r)
                # Mark target as challenged
                if r.get("valid") and r.get("severity", 0) > 0.45:
                    for p in predictions:
                        if p.model == r["target"]:
                            p.challenged = True

        # Defenders respond to valid critiques in round 1 only
        if round_num == 1:
            await _run_defences(predictions, round_critiques, question)

        debate_rounds.append(DebateRound(
            round_num=round_num,
            critiques=round_critiques,
            timestamp=datetime.utcnow().isoformat(),
        ))

    return debate_rounds, all_critiques


async def _run_single_critique(
    challenger_pred: ValidatorPrediction,
    target_pred: ValidatorPrediction,
    question: str,
) -> Dict:
    """One validator critiques another asynchronously."""
    try:
        resp   = await llm_service.generate_critique(
            challenger=challenger_pred.model,
            target_reasoning=target_pred.reasoning[:600],
            market_question=question,
            target_probability=int(target_pred.prediction * 100),
        )
        parsed = parse_json(resp.content)
        if parsed and "critique" in parsed:
            return {
                "challenger":      challenger_pred.model,
                "target":          target_pred.model,
                "type":            parsed.get("challenge_type", "logical_flaw"),
                "critique":        parsed["critique"],
                "severity":        float(parsed.get("severity", 0.5)),
                "valid":           bool(parsed.get("valid", True)),
            }
    except Exception as exc:
        print(f"[DEBATE] critique {challenger_pred.model}→{target_pred.model} failed: {exc}")

    # Fallback minimal critique
    return {
        "challenger": challenger_pred.model,
        "target":     target_pred.model,
        "type":       "evidence_gap",
        "critique":   (
            f"{challenger_pred.model} notes that {target_pred.model}'s "
            f"{int(target_pred.prediction*100)}% estimate may underweight key evidence."
        ),
        "severity":   0.4,
        "valid":      False,
    }


async def _run_defences(
    predictions: List[ValidatorPrediction],
    critiques: List[Dict],
    question: str,
) -> None:
    """Defenders respond to valid critiques; stores response in reasoning."""
    valid_critiques = [c for c in critiques if c.get("valid")]
    if not valid_critiques:
        return

    tasks = []
    mapping = []
    for critique in valid_critiques:
        target = next((p for p in predictions if p.model == critique["target"]), None)
        if target:
            tasks.append(
                llm_service.generate_response_to_critique(
                    defender=target.model,
                    original_reasoning=target.reasoning[:400],
                    critique_text=critique["critique"],
                    market_question=question,
                )
            )
            mapping.append(target)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for pred, result in zip(mapping, results):
        if isinstance(result, str) and result:
            pred.reasoning += f"\n\n[Defence]: {result}"


# ── Scoring ───────────────────────────────────────────────────────────────────

async def score_predictions(
    predictions: List[ValidatorPrediction],
    question: str,
    critiques: List[Dict],
    reputation_store: Dict,
) -> List[ValidatorPrediction]:
    """
    Async scoring: calls LLM for evidence quality, then combines with
    peer-agreement, reputation, and challenge penalties.
    """
    probabilities = [p.prediction for p in predictions]
    import statistics
    median_prob = statistics.median(probabilities) if probabilities else 0.5

    score_tasks = [
        _score_single(pred, question, critiques, median_prob, reputation_store)
        for pred in predictions
    ]
    scored = await asyncio.gather(*score_tasks, return_exceptions=True)
    for pred, score in zip(predictions, scored):
        if isinstance(score, float):
            pred.score = score
    return predictions


async def _score_single(
    pred: ValidatorPrediction,
    question: str,
    critiques: List[Dict],
    median_prob: float,
    reputation_store: Dict,
) -> float:
    # 1. LLM evidence quality (0-100 → 0-1)
    try:
        challenge_text = next(
            (c["critique"] for c in critiques if c["target"] == pred.model and c.get("valid")),
            None,
        )
        scores = await llm_service.score_reasoning(
            prediction_text=pred.reasoning,
            market_question=question,
            challenge_text=challenge_text,
        )
        evidence = (
            scores.get("evidence_quality", 50) * 0.30
            + scores.get("logical_coherence", 50) * 0.30
            + scores.get("risk_awareness",    50) * 0.20
            + scores.get("clarity",           50) * 0.20
        ) / 100.0
    except Exception:
        evidence = 0.5

    # 2. Peer agreement (proximity to median)
    dist          = abs(pred.prediction - median_prob)
    peer_score    = max(0.0, 1.0 - dist * 2)

    # 3. Reputation
    rep           = reputation_store.get(pred.model, {}).get("score", 7.0)
    rep_score     = min(1.0, rep / 10.0)

    # 4. Challenge penalty
    n_valid_challenges = sum(
        1 for c in critiques
        if c["target"] == pred.model and c.get("valid") and c.get("severity", 0) > 0.5
    )
    challenge_penalty = min(0.3, n_valid_challenges * 0.08)

    # Weighted composite
    composite = (
        evidence   * 0.35
        + peer_score * 0.30
        + rep_score  * 0.20
    ) - challenge_penalty

    return round(max(0.05, min(1.0, composite)), 4)


# ── Utilities ─────────────────────────────────────────────────────────────────

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]
