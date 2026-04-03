"""
Validators Router — Reputation queries and live prediction API.
"""

from fastapi import APIRouter, HTTPException

from backend.models.schemas import PredictRequest
from backend.core.reputation import reputation_manager
from backend.core import debate_engine
from backend.core.predikt import compute_predikt, build_reasoning_tree, generate_summary
from backend.services.storage import storage_service
from backend.models.market import Market as MarketModel
from datetime import datetime, timezone, timedelta

router = APIRouter(tags=["validators"])


@router.get("/validators")
async def get_validators():
    """Get all validator reputation scores and accuracy history."""
    return {"validators": reputation_manager.get_stats()}


@router.post("/predict-with-reasoning")
async def predict_with_reasoning(request: PredictRequest):
    """
    One-shot prediction: run the full debate pipeline on any question
    without creating a permanent market. Useful for external integrations
    and testing the debate engine.
    """
    question = request.question
    category = request.category

    predictions = await debate_engine.generate_all_predictions(
        question=question,
        category=category,
    )
    if not predictions:
        raise HTTPException(status_code=500, detail="All validators failed")

    debate_rounds, all_critiques = await debate_engine.run_debate_rounds(
        predictions=predictions,
        question=question,
        num_rounds=2,
    )

    rep_store   = reputation_manager.get_all()
    predictions = await debate_engine.score_predictions(
        predictions=predictions,
        question=question,
        critiques=all_critiques,
        reputation_store=rep_store,
    )

    predikt_val, confidence_val = compute_predikt(predictions)

    mock_market = MarketModel(
        id="ephemeral",
        question=question,
        category=category,
        deadline=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        validators=predictions,
        debate_rounds=debate_rounds,
        predikt=predikt_val,
        confidence=confidence_val,
    )
    tree    = build_reasoning_tree(mock_market)
    summary = generate_summary(mock_market)

    return {
        "question":          question,
        "predikt":           predikt_val,
        "confidence":        confidence_val,
        "resolved_yes":      predikt_val >= 0.5,
        "validators": [
            {
                "model":             v.model,
                "prediction":        v.prediction,
                "score":             v.score,
                "challenged":        v.challenged,
                "reasoning_preview": v.reasoning[:300],
            }
            for v in sorted(predictions, key=lambda x: x.score, reverse=True)
        ],
        "debate_rounds":     len(debate_rounds),
        "total_challenges":  len(all_critiques),
        "reasoning_tree":    tree,
        "reasoning_summary": summary,
    }
