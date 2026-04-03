"""
Validator Reputation System

Tracks and evolves validator reputation scores over time based on:
  - Alignment with final predikt
  - Challenge history
  - Participation consistency

Score range: 1.0 – 10.0
"""

from typing import Dict
from copy import deepcopy

from backend.models.market import ValidatorPrediction
from backend.models.validator import DEFAULT_REPUTATION


# Reputation adjustment constants
CLOSE_BONUS = 0.2       # Within 10% of predikt
MODERATE_BONUS = 0.1     # Within 20% of predikt
FAR_PENALTY = -0.1       # Beyond 30% from predikt
MIN_SCORE = 1.0
MAX_SCORE = 10.0


class ReputationManager:
    """
    Manages the global validator reputation store.

    In production, this would be backed by a database.
    For demo, it uses an in-memory dict initialized from defaults.
    """

    def __init__(self):
        self.store: Dict[str, Dict] = deepcopy(DEFAULT_REPUTATION)

    def get(self, model: str) -> Dict:
        """Get reputation data for a model."""
        return self.store.get(model, {
            "score": 5.0,
            "markets_participated": 0,
            "accuracy_history": [],
        })

    def get_all(self) -> Dict[str, Dict]:
        """Get all validator reputations."""
        return self.store

    def update_after_predikt(
        self,
        predictions: list,
        predikt: float,
    ):
        """
        Update all validator reputations after a market is finalized.

        Args:
            predictions: List of ValidatorPrediction from the market
            predikt: Final predikt value (0–1)
        """
        for pred in predictions:
            model = pred.model
            if model not in self.store:
                self.store[model] = {
                    "score": 5.0,
                    "markets_participated": 0,
                    "accuracy_history": [],
                }

            distance = abs(pred.prediction - predikt)

            # Adjust score based on alignment
            if distance < 0.10:
                delta = CLOSE_BONUS
            elif distance < 0.20:
                delta = MODERATE_BONUS
            elif distance > 0.30:
                delta = FAR_PENALTY
            else:
                delta = 0.0

            self.store[model]["score"] = round(
                max(MIN_SCORE, min(MAX_SCORE, self.store[model]["score"] + delta)),
                2,
            )
            self.store[model]["markets_participated"] += 1
            self.store[model]["accuracy_history"].append(round(1 - distance, 2))

    def get_stats(self) -> list:
        """Get formatted stats for all validators."""
        results = []
        for model, data in self.store.items():
            history = data.get("accuracy_history", [])
            results.append({
                "model": model,
                "score": data["score"],
                "markets_participated": data["markets_participated"],
                "accuracy_history": history,
                "avg_accuracy": round(
                    sum(history) / len(history), 3
                ) if history else 0,
            })
        return results


# Singleton instance
reputation_manager = ReputationManager()
