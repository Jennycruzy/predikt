# { "Depends": "py-genlayer:test" }

"""
PredictionMarket — GenLayer Intelligent Contract

Manages the full AI-powered prediction market lifecycle:
  1. Market creation (via daemon from real news)
  2. Validator predictions + debate (submitted by off-chain debate engine)
  3. AI resolution: fetches live web data → LLM consensus → finalize
  4. Reputation scoring for each AI validator

Staking (YES/NO mUSDL) is handled by Base Sepolia BetFactory/BetMarket.
The resolution result here is bridged to Base Sepolia by the daemon.
"""

import json
from dataclasses import dataclass, field
from genlayer import *


# ── Storage types ─────────────────────────────────────────────────────────────

@allow_storage
@dataclass
class Prediction:
    validator: Address
    model: str
    prediction: u256          # 0–100 probability (YES)
    reasoning_hash: str
    score: u256               # reasoning quality 0–100
    challenged: bool
    challenge_count: u256


@allow_storage
@dataclass
class Challenge:
    challenger: Address
    target: Address
    challenge_hash: str
    challenge_type: str       # logical_flaw | evidence_gap | bias | contradiction
    severity: u256            # 0–100, scaled from 0.0–1.0


@allow_storage
@dataclass
class Market:
    id: u256
    question: str
    deadline: str             # ISO-8601 UTC
    category: str
    creator: Address
    status: str               # "open" | "debating" | "finalized"
    predikt: i256             # -1 until finalized, then 0–100
    confidence: i256          # -1 until finalized, then 0–100
    resolved_yes: bool        # True if predikt >= 50
    summary_hash: str
    validator_count: u256
    debate_rounds: u256
    resolution_url: str       # URL used for AI resolution


# ── Contract ──────────────────────────────────────────────────────────────────

class PredictionMarket(gl.Contract):
    owner: Address
    market_count: u256

    markets:     TreeMap[u256, Market]
    predictions: TreeMap[u256, DynArray[Prediction]]
    challenges:  TreeMap[u256, DynArray[Challenge]]
    scores:      TreeMap[Address, u256]   # cumulative reputation per validator

    def __init__(self) -> None:
        self.owner        = gl.message.sender_address
        self.market_count = u256(0)

    # ── Write: market lifecycle ───────────────────────────────────────────────

    @gl.public.write
    def create_market(
        self,
        question: str,
        deadline: str,
        category: str,
    ) -> None:
        """Register a new prediction market. Called by the daemon after news-based generation."""
        mid = self.market_count
        self.market_count = u256(int(mid) + 1)

        market = Market(
            id=mid,
            question=question,
            deadline=deadline,
            category=category,
            creator=gl.message.sender_address,
            status="open",
            predikt=i256(-1),
            confidence=i256(-1),
            resolved_yes=False,
            summary_hash="",
            validator_count=u256(0),
            debate_rounds=u256(0),
            resolution_url="",
        )
        self.markets[mid]     = market
        self.predictions[mid] = DynArray[Prediction]()
        self.challenges[mid]  = DynArray[Challenge]()

    @gl.public.write
    def submit_prediction(
        self,
        market_id: u256,
        prediction: int,       # 0–100
        reasoning_hash: str,
        model_name: str,
    ) -> None:
        """AI validator submits its prediction for a market."""
        assert market_id < self.market_count, "Market does not exist"
        market = self.markets[market_id]
        assert market.status in ("open", "debating"), "Market not accepting predictions"
        assert 0 <= prediction <= 100, "Prediction must be 0–100"

        sender = gl.message.sender_address
        pred   = Prediction(
            validator=sender,
            model=model_name,
            prediction=u256(prediction),
            reasoning_hash=reasoning_hash,
            score=u256(50),
            challenged=False,
            challenge_count=u256(0),
        )
        self.predictions[market_id].append(pred)

        market.validator_count = u256(int(market.validator_count) + 1)
        if market.status == "open":
            market.status = "debating"
        self.markets[market_id] = market

        if sender not in self.scores:
            self.scores[sender] = u256(500)

    @gl.public.write
    def submit_challenge(
        self,
        market_id: u256,
        target_validator: Address,
        challenge_hash: str,
        challenge_type: str,
        severity: int = 50,    # 0–100
    ) -> None:
        """AI challenger submits a logical critique against another validator."""
        assert market_id < self.market_count, "Market does not exist"
        market = self.markets[market_id]
        assert market.status == "debating", "Not in debate phase"
        assert challenge_type in (
            "logical_flaw", "evidence_gap", "bias", "contradiction"
        ), "Invalid challenge type"

        challenge = Challenge(
            challenger=gl.message.sender_address,
            target=target_validator,
            challenge_hash=challenge_hash,
            challenge_type=challenge_type,
            severity=u256(max(0, min(100, severity))),
        )
        self.challenges[market_id].append(challenge)

        preds = self.predictions[market_id]
        for pred in preds:
            if pred.validator == target_validator:
                pred.challenged       = True
                pred.challenge_count  = u256(int(pred.challenge_count) + 1)

        market.debate_rounds = u256(int(market.debate_rounds) + 1)
        self.markets[market_id] = market

    @gl.public.write
    def resolve_market(self, market_id: u256, resolution_url: str) -> None:
        """
        AI-powered resolution using GenLayer's non-deterministic execution.

        The contract:
          1. Fetches live data from resolution_url (web render)
          2. Runs an LLM prompt to determine probability
          3. Uses strict equality consensus across validators
          4. Finalizes the market with the agreed result

        Only callable by the contract owner (daemon).
        """
        assert gl.message.sender_address == self.owner, "Only owner"
        assert market_id < self.market_count, "Market does not exist"
        market = self.markets[market_id]
        assert market.status in ("open", "debating"), "Market not resolvable in current state"

        question = market.question

        def get_resolution() -> str:
            web_data = gl.nondet.web.render(resolution_url, mode="text")

            # Truncate to avoid token limit
            if len(web_data) > 3000:
                web_data = web_data[:3000] + "…[truncated]"

            task = f"""You are a prediction market resolution oracle.

Market question: {question}

Live web data fetched from {resolution_url}:
{web_data}

Based on this evidence, determine the probability (0–100) that the event
described in the question has occurred or will occur as stated.

Be precise. If data is unavailable or ambiguous, use 50 as your estimate.

Respond in JSON ONLY — no extra text:
{{
    "probability": <integer 0-100>,
    "confidence": <integer 0-100>,
    "resolved_yes": <true if probability >= 50, else false>,
    "summary": "<one sentence explaining your decision>"
}}"""

            result = gl.nondet.exec_prompt(task, response_format="json")
            return json.dumps(result, sort_keys=True)

        # All GenLayer validators must agree on this result (strict equality)
        result_raw  = gl.eq_principle.strict_eq(get_resolution)
        result_json = json.loads(result_raw)

        predikt_val  = max(0, min(100, int(result_json.get("probability", 50))))
        conf_val     = max(0, min(100, int(result_json.get("confidence",  50))))
        summary      = str(result_json.get("summary", ""))
        resolved_yes = bool(result_json.get("resolved_yes", predikt_val >= 50))

        # Store resolution URL
        market.resolution_url = resolution_url
        self.markets[market_id] = market

        self._finalize(
            market_id,
            i256(predikt_val),
            i256(conf_val),
            summary,
            resolved_yes,
        )

    @gl.public.write
    def finalize_predikt(
        self,
        market_id: u256,
        predikt: int,
        confidence: int,
        summary_hash: str,
    ) -> None:
        """
        Manual finalization by the owner after off-chain debate.
        Used when resolution_url is not yet available or as a pre-step.
        """
        assert gl.message.sender_address == self.owner, "Only owner"
        assert market_id < self.market_count, "Market does not exist"
        assert 0 <= predikt    <= 100, "Predikt must be 0–100"
        assert 0 <= confidence <= 100, "Confidence must be 0–100"

        self._finalize(
            market_id,
            i256(predikt),
            i256(confidence),
            summary_hash,
            predikt >= 50,
        )

    @gl.public.write
    def update_validator_score(
        self,
        market_id: u256,
        validator: Address,
        new_score: int,
    ) -> None:
        """Owner updates a validator's reasoning score post-debate."""
        assert gl.message.sender_address == self.owner, "Only owner"
        assert market_id < self.market_count, "Market does not exist"
        assert 0 <= new_score <= 100, "Score must be 0–100"

        preds = self.predictions[market_id]
        for pred in preds:
            if pred.validator == validator:
                pred.score = u256(new_score)

    # ── Read: views ───────────────────────────────────────────────────────────

    @gl.public.view
    def get_market(self, market_id: u256) -> dict:
        assert market_id < self.market_count, "Market does not exist"
        m = self.markets[market_id]
        return {
            "id":              int(m.id),
            "question":        m.question,
            "deadline":        m.deadline,
            "category":        m.category,
            "creator":         m.creator.as_hex,
            "status":          m.status,
            "predikt":         int(m.predikt),
            "confidence":      int(m.confidence),
            "resolved_yes":    m.resolved_yes,
            "summary_hash":    m.summary_hash,
            "validator_count": int(m.validator_count),
            "debate_rounds":   int(m.debate_rounds),
            "resolution_url":  m.resolution_url,
        }

    @gl.public.view
    def get_predictions(self, market_id: u256) -> list:
        assert market_id < self.market_count, "Market does not exist"
        return [
            {
                "validator":       p.validator.as_hex,
                "model":           p.model,
                "prediction":      int(p.prediction),
                "reasoning_hash":  p.reasoning_hash,
                "score":           int(p.score),
                "challenged":      p.challenged,
                "challenge_count": int(p.challenge_count),
            }
            for p in self.predictions[market_id]
        ]

    @gl.public.view
    def get_challenges(self, market_id: u256) -> list:
        assert market_id < self.market_count, "Market does not exist"
        return [
            {
                "challenger":      c.challenger.as_hex,
                "target":          c.target.as_hex,
                "challenge_hash":  c.challenge_hash,
                "challenge_type":  c.challenge_type,
                "severity":        int(c.severity),
            }
            for c in self.challenges[market_id]
        ]

    @gl.public.view
    def get_validator_reputation(self, validator: Address) -> int:
        return int(self.scores.get(validator, u256(500)))

    @gl.public.view
    def get_market_count(self) -> int:
        return int(self.market_count)

    @gl.public.view
    def get_all_markets(self) -> list:
        result = []
        for i in range(int(self.market_count)):
            m = self.markets[u256(i)]
            result.append({
                "id":              int(m.id),
                "question":        m.question,
                "deadline":        m.deadline,
                "category":        m.category,
                "creator":         m.creator.as_hex,
                "status":          m.status,
                "predikt":         int(m.predikt),
                "confidence":      int(m.confidence),
                "resolved_yes":    m.resolved_yes,
                "summary_hash":    m.summary_hash,
                "validator_count": int(m.validator_count),
                "debate_rounds":   int(m.debate_rounds),
            })
        return result

    # ── Internal ──────────────────────────────────────────────────────────────

    def _finalize(
        self,
        market_id: u256,
        predikt_val: i256,
        confidence_val: i256,
        summary_hash: str,
        resolved_yes: bool,
    ) -> None:
        market              = self.markets[market_id]
        market.status       = "finalized"
        market.predikt      = predikt_val
        market.confidence   = confidence_val
        market.summary_hash = summary_hash
        market.resolved_yes = resolved_yes
        self.markets[market_id] = market

        # Update validator reputation scores
        preds = self.predictions[market_id]
        for pred in preds:
            addr     = pred.validator
            current  = int(self.scores.get(addr, u256(500)))
            distance = abs(int(pred.prediction) - int(predikt_val))

            if distance <= 5:
                new_score = min(1000, current + 50)
            elif distance <= 15:
                new_score = min(1000, current + 20)
            elif distance <= 30:
                new_score = current
            else:
                new_score = max(100, current - 30)

            # Challenge penalty
            if pred.challenged and int(pred.challenge_count) > 1:
                new_score = max(100, new_score - 20)

            # Update individual prediction score based on accuracy
            pred.score      = u256(max(10, 100 - distance))
            self.scores[addr] = u256(new_score)
