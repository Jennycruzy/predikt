"""
Debate Router — Async AI validator debates with background jobs.

POST /run-debate      → starts job, returns {job_id} immediately
GET  /debate-job/{id} → poll for status/results (no proxy timeout)
"""

import asyncio
import uuid
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks

from backend.models.schemas import RunDebateRequest, DebateResponse, ValidatorResult
from backend.models.validator import VALIDATOR_PROFILES
from backend.core import debate_engine
from backend.core.predikt import compute_predikt, build_reasoning_tree, generate_summary
from backend.core.reputation import reputation_manager
from backend.services.chain import chain_service, hash_reasoning
from backend.services.storage import storage_service
from backend.models.market import Market as MarketModel, MarketStatus

router = APIRouter(tags=["debate"])

# In-memory job store (acceptable for single-server testnet)
_jobs: Dict[str, Dict[str, Any]] = {}


async def _get_market_any_source(mid: int) -> dict | None:
    """Try GenLayer first, fall back to Base Sepolia."""
    market_data = await chain_service.get_market_onchain(mid)
    if market_data:
        return market_data
    try:
        bs_markets = await chain_service.get_all_markets_base_sepolia()
        for m in bs_markets:
            if int(m.get("id", -1)) == mid:
                return m
    except Exception:
        pass
    return None


async def _run_debate_job(job_id: str, mid: int, num_rounds: int, context: str | None):
    """
    AI debate pipeline — INFORMATIONAL ONLY.

    This shows users what the AI validators predict and how they critique each other.
    It does NOT change market state, does NOT finalize, does NOT resolve on-chain.
    Market finalization happens exclusively via the daemon after the deadline passes.
    """
    try:
        market_data = await _get_market_any_source(mid)
        if not market_data:
            _jobs[job_id] = {"status": "failed", "error": f"Market {mid} not found"}
            return

        question = market_data["question"]
        category = market_data.get("category", "general")
        # Preserve the current on-chain status — we never change it here
        market_status = market_data.get("status", "open")

        _jobs[job_id]["step"] = "Generating validator predictions..."

        predictions = await debate_engine.generate_all_predictions(
            question=question,
            category=category,
            context=context,
        )
        if not predictions:
            _jobs[job_id] = {"status": "failed", "error": "All validators failed"}
            return

        # Submit predictions to GenLayer contract (best-effort, does not block)
        for pred in predictions:
            try:
                await chain_service.submit_prediction_onchain(
                    market_id=mid,
                    prediction=int(pred.prediction * 100),
                    reasoning_hash=pred.reasoning_hash,
                    model_name=pred.model,
                )
            except Exception:
                pass
            storage_service.store_reasoning(pred.reasoning, pred.model)

        _jobs[job_id]["step"] = "Running debate rounds..."

        debate_rounds, all_critiques = await debate_engine.run_debate_rounds(
            predictions=predictions,
            question=question,
            num_rounds=num_rounds,
        )

        # Submit challenges to GenLayer (best-effort, does not block)
        for critique in all_critiques:
            if critique.get("valid"):
                try:
                    await chain_service.submit_challenge_onchain(
                        market_id=mid,
                        target_validator=critique["target"],
                        challenge_hash=hash_reasoning(critique["critique"]),
                        challenge_type=critique["type"],
                    )
                except Exception:
                    pass

        _jobs[job_id]["step"] = "Scoring reasoning quality..."

        rep_store   = reputation_manager.get_all()
        predictions = await debate_engine.score_predictions(
            predictions=predictions,
            question=question,
            critiques=all_critiques,
            reputation_store=rep_store,
        )

        predikt_val, confidence_val = compute_predikt(predictions)

        mock_market = MarketModel(
            id=str(mid),
            question=question,
            category=category,
            deadline=market_data.get("deadline", ""),
            validators=predictions,
            debate_rounds=debate_rounds,
            predikt=predikt_val,
            confidence=confidence_val,
        )
        reasoning_tree = build_reasoning_tree(mock_market)
        summary        = generate_summary(mock_market)
        summary_hash   = storage_service.store_summary(str(mid), summary)
        storage_service.store_tree(str(mid), reasoning_tree)

        # Update reputation scores (local, no chain changes)
        reputation_manager.update_after_predikt(predictions, predikt_val)

        # ── NO finalize_onchain, NO resolve_on_base_sepolia ──────────────────
        # Finalization is the daemon's job, triggered only after deadline.

        sorted_preds = sorted(predictions, key=lambda x: x.score, reverse=True)

        rounds_data = [
            {
                "round": dr.round_num,
                "critiques": [
                    {
                        "challenger": c.get("challenger", ""),
                        "target":     c.get("target", ""),
                        "critique":   c.get("critique", ""),
                        "type":       c.get("type") or "factual_challenge",
                        "valid":      bool(c.get("valid", False)),
                        "severity":   int(c.get("severity", 5)),
                    }
                    for c in dr.critiques
                ],
            }
            for dr in debate_rounds
        ]

        _jobs[job_id] = {
            "status": "completed",
            "step": "Done",
            "result": {
                "market_id":       str(mid),
                "predikt":         predikt_val,
                "confidence":      confidence_val,
                "validators": [
                    {
                        "model":             v.model,
                        "prediction":        v.prediction,
                        "score":             v.score,
                        "challenged":        v.challenged,
                        "reasoning_preview": v.reasoning[:300],
                        "reasoning":         v.reasoning,
                    }
                    for v in sorted_preds
                ],
                "debate_rounds":    len(debate_rounds),
                "total_challenges": len(all_critiques),
                "status":           market_status,  # unchanged — market not finalized
                "rounds_data":      rounds_data,
            }
        }

    except Exception as exc:
        import traceback
        _jobs[job_id] = {"status": "failed", "error": str(exc), "tb": traceback.format_exc()}


@router.post("/run-debate")
async def run_debate(request: RunDebateRequest, background_tasks: BackgroundTasks):
    """Start an AI debate as a background job. Returns job_id immediately."""
    try:
        mid = int(request.market_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="market_id must be an integer")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "step": "Starting..."}

    background_tasks.add_task(
        _run_debate_job, job_id, mid, request.num_rounds, request.additional_context
    )

    return {"job_id": job_id, "status": "pending"}


@router.get("/debate-job/{job_id}")
async def get_debate_job(job_id: str):
    """Poll for debate job status and results."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/debate/{market_id}/summary")
async def get_debate_summary(market_id: str):
    summary = storage_service.get_summary(market_id)
    tree    = storage_service.get_tree(market_id)
    if not summary:
        raise HTTPException(status_code=404, detail="No debate summary found")
    return {"market_id": market_id, "summary": summary, "reasoning_tree": tree}
