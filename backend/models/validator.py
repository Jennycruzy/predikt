"""
AI Validator profiles, configurations, and reasoning templates.
Each validator has a distinct analytical style and bias profile.
"""

from typing import Dict, List, Tuple


VALIDATOR_PROFILES: Dict[str, Dict] = {
    "gpt-4o": {
        "style": "analytical",
        "bias_toward": "data-driven",
        "confidence_range": (0.65, 0.90),
        "reasoning_depth": "deep",
        "description": "Quantitative, statistical approach with strong data emphasis",
    },
    "claude-sonnet": {
        "style": "nuanced",
        "bias_toward": "balanced",
        "confidence_range": (0.60, 0.85),
        "reasoning_depth": "thorough",
        "description": "Careful, epistemic-humility-driven analysis with caveats",
    },
    "gemini-pro": {
        "style": "optimistic",
        "bias_toward": "trend-following",
        "confidence_range": (0.70, 0.95),
        "reasoning_depth": "moderate",
        "description": "Momentum-driven, forward-looking with trend emphasis",
    },
    "llama-3": {
        "style": "contrarian",
        "bias_toward": "skeptical",
        "confidence_range": (0.40, 0.75),
        "reasoning_depth": "moderate",
        "description": "Skeptical, base-rate-focused with historical analogies",
    },
    "mistral-large": {
        "style": "pragmatic",
        "bias_toward": "historical-precedent",
        "confidence_range": (0.55, 0.80),
        "reasoning_depth": "deep",
        "description": "Precedent-based, institutional-dynamics focused analysis",
    },
}


REASONING_TEMPLATES: Dict[str, List[str]] = {
    "gpt-4o": [
        "Analyzing '{question}' through quantitative lens.",
        "Historical data patterns suggest a {pred}% probability.",
        "Key factors: market indicators show strong directional signals.",
        "Statistical models converge on this estimate with moderate variance.",
        "Cross-referencing multiple data sources confirms this assessment.",
        "Risk assessment: {risk} uncertainty range.",
    ],
    "claude-sonnet": [
        "Evaluating '{question}' with emphasis on nuance and uncertainty.",
        "Multiple competing narratives exist in the evidence base.",
        "Weighing factors for and against, I arrive at {pred}% confidence.",
        "Important caveat: this estimate carries significant epistemic uncertainty.",
        "The strongest evidence points toward this conclusion, but counterarguments have merit.",
        "Base rate analysis and reference class forecasting support this range.",
    ],
    "gemini-pro": [
        "Rapid assessment of '{question}' using trend analysis.",
        "Current trajectory and momentum strongly favor this outcome.",
        "My estimate of {pred}% reflects recent positive indicators.",
        "Market sentiment and expert predikt align with this direction.",
        "Technological and structural tailwinds support this projection.",
        "Near-term catalysts could push this probability higher.",
    ],
    "llama-3": [
        "Critical examination of '{question}' from a skeptical perspective.",
        "Common assumptions about this topic may be overconfident.",
        "Adjusting for typical forecasting biases, I estimate {pred}%.",
        "Historical precedents suggest outcomes are less predictable than assumed.",
        "Key risks and black swan scenarios remain underweighted by predikt.",
        "Contrarian indicators suggest the market may be mispricing this event.",
    ],
    "mistral-large": [
        "Pragmatic analysis of '{question}' grounded in historical precedent.",
        "Comparing to analogous past events reveals instructive patterns.",
        "Based on base rates and adjustments, probability is approximately {pred}%.",
        "Structural factors and institutional dynamics play a key role.",
        "Implementation challenges and execution risk are material considerations.",
        "The path dependency of outcomes suggests we should track leading indicators.",
    ],
}


CRITIQUE_TEMPLATES: Dict[str, str] = {
    "logical_flaw": (
        "{challenger} identifies a logical gap in {target}'s reasoning: "
        "the causal chain from evidence to conclusion has unstated assumptions "
        "that may not hold."
    ),
    "evidence_gap": (
        "{challenger} notes that {target} omits key evidence that could "
        "significantly alter the prediction. The analysis appears incomplete."
    ),
    "bias": (
        "{challenger} flags potential {bias_type} bias in {target}'s analysis, "
        "which may skew the prediction by {skew}%."
    ),
    "contradiction": (
        "{challenger} points out an internal contradiction: {target}'s stated "
        "confidence level doesn't align with the uncertainty acknowledged "
        "in the reasoning."
    ),
}


# Default reputation state for new deployments
DEFAULT_REPUTATION: Dict[str, Dict] = {
    "gpt-4o": {
        "score": 7.2,
        "markets_participated": 12,
        "accuracy_history": [0.78, 0.82, 0.69, 0.91, 0.85],
    },
    "claude-sonnet": {
        "score": 7.8,
        "markets_participated": 15,
        "accuracy_history": [0.81, 0.76, 0.88, 0.92, 0.79],
    },
    "gemini-pro": {
        "score": 6.9,
        "markets_participated": 10,
        "accuracy_history": [0.72, 0.68, 0.84, 0.77, 0.81],
    },
    "llama-3": {
        "score": 6.5,
        "markets_participated": 8,
        "accuracy_history": [0.65, 0.71, 0.78, 0.69, 0.74],
    },
    "mistral-large": {
        "score": 7.0,
        "markets_participated": 9,
        "accuracy_history": [0.74, 0.79, 0.71, 0.82, 0.68],
    },
}
