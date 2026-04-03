"""
Intelligence-Weighted Predikt Algorithm

Unlike traditional prediction markets that weight by capital,
this algorithm weights predictions by reasoning quality:
  - Higher reasoning score → more influence on predikt
  - Confidence reflects both agreement spread and average quality

Formula:
    predikt = Σ(prediction_i × score_i) / Σ(score_i)
    confidence = (1 - spread) × 0.6 + avg_score × 0.4
"""

from typing import List, Dict, Tuple, Optional

from backend.models.market import Market, ValidatorPrediction


def compute_predikt(predictions: List[ValidatorPrediction]) -> Tuple[float, float]:
    """
    Compute intelligence-weighted predikt from all predictions.

    Args:
        predictions: List of scored ValidatorPredictions

    Returns:
        Tuple of (predikt probability, confidence score)
        Both are floats in [0, 1]
    """
    if not predictions:
        return 0.5, 0.0

    # Intelligence-weighted average
    total_weight = sum(p.score for p in predictions)
    if total_weight == 0:
        total_weight = 1.0

    weighted_sum = sum(p.prediction * p.score for p in predictions)
    predikt = weighted_sum / total_weight

    # Confidence calculation
    pred_values = [p.prediction for p in predictions]
    spread = max(pred_values) - min(pred_values)
    agreement_factor = 1.0 - spread
    avg_score = total_weight / len(predictions)

    confidence = agreement_factor * 0.6 + avg_score * 0.4

    return round(predikt, 4), round(confidence, 4)


def build_reasoning_tree(market: Market) -> Dict:
    """
    Build a structured reasoning tree for frontend visualization.

    Structure:
        Root: question
        └── Validator branch (per model)
            └── Reasoning point (per line)
                └── Challenge node (if any)

    Args:
        market: Market with validators and debate rounds populated

    Returns:
        Nested dict tree structure
    """
    tree = {
        "id": "root",
        "label": market.question,
        "type": "question",
        "children": [],
    }

    for v in market.validators:
        validator_node = {
            "id": f"v_{v.model}",
            "label": v.model,
            "type": "validator",
            "prediction": v.prediction,
            "score": v.score,
            "reasoning": v.reasoning,
            "children": [],
        }

        # Break reasoning into individual points
        reasoning_points = [l.strip() for l in v.reasoning.split("\n") if l.strip()]
        for i, point in enumerate(reasoning_points):
            point_node = {
                "id": f"v_{v.model}_r{i}",
                "label": point,
                "type": "reasoning",
                "children": [],
            }

            # Attach challenges to their nearest reasoning point
            for rnd in market.debate_rounds:
                for critique in rnd.critiques:
                    if critique["target"] == v.model:
                        challenge_node = {
                            "id": f"c_{critique['challenger']}_{v.model}_{i}",
                            "label": critique["critique"],
                            "type": "challenge",
                            "challenge_type": critique["type"],
                            "severity": critique["severity"],
                            "valid": critique["valid"],
                            "children": [],
                        }
                        point_node["children"].append(challenge_node)
                        break  # One challenge per point for clarity

            validator_node["children"].append(point_node)

        tree["children"].append(validator_node)

    return tree


def generate_summary(market: Market) -> str:
    """
    Generate a human-readable reasoning summary.

    Args:
        market: Finalized market with predikt computed

    Returns:
        Markdown-formatted summary string
    """
    if not market.validators:
        return "No predictions submitted yet."

    lines = [
        f"## Predikt Analysis: {market.question}\n",
        f"**Final Predikt:** {market.predikt * 100:.1f}% probability",
        f"**Confidence Level:** {market.confidence * 100:.1f}%\n",
    ]

    sorted_validators = sorted(market.validators, key=lambda v: v.score, reverse=True)

    lines.append("### Validator Predictions (ranked by reasoning quality):\n")
    for v in sorted_validators:
        lines.append(f"**{v.model}** — {v.prediction * 100:.1f}% (score: {v.score:.2f})")
        first_line = v.reasoning.split("\n")[0] if v.reasoning else "No reasoning"
        lines.append(f"  _{first_line}_\n")

    if market.debate_rounds:
        lines.append("### Key Debate Points:\n")
        for rnd in market.debate_rounds:
            for critique in rnd.critiques:
                if critique.get("valid", False):
                    lines.append(f"- {critique['critique']}")

    return "\n".join(lines)
