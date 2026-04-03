"""
Off-Chain Reasoning Storage

Full reasoning text is stored off-chain (too large for on-chain).
Only the hash is stored on the smart contract.

In production, this would use:
  - IPFS for decentralized storage
  - PostgreSQL for queryable access
  - Redis for caching

For demo, we use an in-memory store.
"""

import hashlib
from typing import Optional, Dict
from datetime import datetime


class StorageService:
    """
    Manages off-chain storage of reasoning text, summaries,
    and reasoning trees.
    """

    def __init__(self):
        self._reasoning: Dict[str, Dict] = {}   # hash -> {text, model, timestamp}
        self._summaries: Dict[str, str] = {}     # market_id -> summary
        self._trees: Dict[str, Dict] = {}        # market_id -> tree

    def store_reasoning(self, text: str, model: str) -> str:
        """
        Store reasoning text and return its hash.

        Args:
            text: Full reasoning text
            model: Validator model name

        Returns:
            SHA-256 hash (first 16 chars) used as on-chain reference
        """
        full_hash = hashlib.sha256(text.encode()).hexdigest()
        short_hash = full_hash[:16]

        self._reasoning[short_hash] = {
            "text": text,
            "model": model,
            "full_hash": full_hash,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return short_hash

    def get_reasoning(self, reasoning_hash: str) -> Optional[str]:
        """Retrieve reasoning text by hash."""
        entry = self._reasoning.get(reasoning_hash)
        return entry["text"] if entry else None

    def store_summary(self, market_id: str, summary: str) -> str:
        """Store a market reasoning summary."""
        self._summaries[market_id] = summary
        return hashlib.sha256(summary.encode()).hexdigest()[:16]

    def get_summary(self, market_id: str) -> Optional[str]:
        """Retrieve a market reasoning summary."""
        return self._summaries.get(market_id)

    def store_tree(self, market_id: str, tree: Dict):
        """Store a reasoning tree for a market."""
        self._trees[market_id] = tree

    def get_tree(self, market_id: str) -> Optional[Dict]:
        """Retrieve a reasoning tree."""
        return self._trees.get(market_id)

    def get_stats(self) -> Dict:
        """Get storage statistics."""
        return {
            "reasoning_entries": len(self._reasoning),
            "summaries": len(self._summaries),
            "trees": len(self._trees),
        }


# Singleton
storage_service = StorageService()
