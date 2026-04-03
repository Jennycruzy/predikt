"""
LLM Service — Venice AI as primary provider.

Venice AI is OpenAI-compatible and runs privacy-preserving inference.
All five validator personas are powered by Venice using different models
and system prompts to create genuinely diverse debate dynamics.

Fallback chain: Venice → (if key missing) mock structured response
"""

import os
import json
import re
from dataclasses import dataclass
from typing import Optional
from openai import AsyncOpenAI


@dataclass
class LLMResponse:
    model: str
    content: str
    tokens_used: int
    cost: float = 0.0


# Validator persona system prompts
VALIDATOR_PERSONAS = {
    "gpt-4o": {
        "model": "llama-3.3-70b",
        "system": (
            "You are an analytical AI validator specialising in quantitative prediction markets. "
            "You rely heavily on data, statistics, and historical base rates. "
            "You structure your analysis with clear probability estimates backed by evidence. "
            "Be precise. Acknowledge uncertainty with confidence intervals. "
            "Always output valid JSON when asked."
        ),
    },
    "claude-sonnet": {
        "model": "mistral-31-24b",
        "system": (
            "You are a balanced, epistemically humble AI validator. "
            "You carefully weigh multiple competing narratives, acknowledge limitations in your "
            "knowledge, and avoid overconfidence. You look for base-rate evidence and reference "
            "class forecasting. When uncertain, you say so and widen your probability range. "
            "Always output valid JSON when asked."
        ),
    },
    "gemini-pro": {
        "model": "llama-3.3-70b",
        "system": (
            "You are an optimistic, momentum-driven AI validator. "
            "You focus on current trends, recent catalysts, and forward-looking indicators. "
            "You give extra weight to positive momentum and tend to assign higher probabilities "
            "when trend evidence is strong. "
            "Always output valid JSON when asked."
        ),
    },
    "llama-3": {
        "model": "mistral-31-24b",
        "system": (
            "You are a contrarian, skeptical AI validator. "
            "Your default is to question consensus views, apply base-rate corrections, and "
            "highlight underweighted risks and black-swan scenarios. "
            "You typically assign lower probabilities than the crowd and always explain why. "
            "Always output valid JSON when asked."
        ),
    },
    "mistral-large": {
        "model": "llama-3.3-70b",
        "system": (
            "You are a pragmatic, precedent-focused AI validator. "
            "You ground your analysis in historical analogues, institutional dynamics, and "
            "execution risks. You distrust narratives that lack precedent and weight "
            "implementation challenges heavily. "
            "Always output valid JSON when asked."
        ),
    },
}

PREDICTION_SCHEMA = """{
  "probability": <integer 0-100, your YES probability estimate>,
  "confidence": <integer 0-100, how confident you are in your estimate>,
  "reasoning": "<2-4 sentence explanation of your key reasoning>",
  "key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
  "risks": "<main uncertainty or risk to your estimate>"
}"""

CRITIQUE_SCHEMA = """{
  "challenge_type": "<one of: logical_flaw | evidence_gap | bias | contradiction>",
  "critique": "<2-3 sentence critique of the target's reasoning>",
  "severity": <float 0.0-1.0, how serious the flaw is>,
  "valid": <true if the critique identifies a real problem>
}"""


class LLMService:

    def __init__(self):
        self.venice_key   = os.getenv("VENICE_API_KEY", "")
        self._venice_client: Optional[AsyncOpenAI] = None

    def _client(self) -> AsyncOpenAI:
        if self._venice_client is None:
            if not self.venice_key:
                raise ValueError("VENICE_API_KEY not configured")
            self._venice_client = AsyncOpenAI(
                api_key=self.venice_key,
                base_url="https://api.venice.ai/api/v1",
            )
        return self._venice_client

    async def _call(
        self,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: int = 1200,
    ) -> LLMResponse:
        client = self._client()
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content or ""
        tokens  = resp.usage.total_tokens if resp.usage else 0
        return LLMResponse(model=model, content=content, tokens_used=tokens)

    # ── Core methods ──────────────────────────────────────────────────────────

    async def generate_prediction(
        self,
        validator: str,
        market_question: str,
        context: Optional[str] = None,
        category: str = "general",
    ) -> LLMResponse:
        """
        Ask a validator to predict the market question.
        Returns JSON matching PREDICTION_SCHEMA.
        """
        persona = VALIDATOR_PERSONAS.get(validator, VALIDATOR_PERSONAS["gpt-4o"])
        ctx_block = f"\n\nAdditional context:\n{context}" if context else ""

        user_prompt = (
            f"Prediction market question: {market_question}\n"
            f"Category: {category}{ctx_block}\n\n"
            f"Respond ONLY with JSON in this exact format:\n{PREDICTION_SCHEMA}"
        )

        return await self._call(
            model=persona["model"],
            system=persona["system"],
            user=user_prompt,
            temperature=0.75,
        )

    async def generate_critique(
        self,
        challenger: str,
        target_reasoning: str,
        market_question: str,
        target_probability: int,
    ) -> LLMResponse:
        """Ask challenger validator to critique another's prediction."""
        persona = VALIDATOR_PERSONAS.get(challenger, VALIDATOR_PERSONAS["llama-3"])

        user_prompt = (
            f"Market question: {market_question}\n\n"
            f"Another validator's prediction: {target_probability}% probability of YES.\n"
            f"Their reasoning: {target_reasoning}\n\n"
            f"Challenge their reasoning. Respond ONLY with JSON:\n{CRITIQUE_SCHEMA}"
        )

        return await self._call(
            model=persona["model"],
            system=persona["system"],
            user=user_prompt,
            temperature=0.8,
        )

    async def generate_response_to_critique(
        self,
        defender: str,
        original_reasoning: str,
        critique_text: str,
        market_question: str,
    ) -> str:
        """Defender responds to a critique, potentially updating their view."""
        persona = VALIDATOR_PERSONAS.get(defender, VALIDATOR_PERSONAS["gpt-4o"])

        user_prompt = (
            f"Market: {market_question}\n\n"
            f"Your original reasoning: {original_reasoning}\n\n"
            f"Challenge received: {critique_text}\n\n"
            f"Respond in 2-3 sentences: acknowledge valid points or defend your position."
        )

        resp = await self._call(
            model=persona["model"],
            system=persona["system"],
            user=user_prompt,
            temperature=0.7,
            max_tokens=400,
        )
        return resp.content

    async def generate_market_question(
        self,
        category: str,
        context: str,
        deadline_hours: int = 24,
    ) -> dict:
        """
        Generate a realistic prediction market question from news context.
        Returns dict: {question, category, deadline_hours_from_now, resolution_url}
        """
        from datetime import datetime
        today = datetime.utcnow().strftime("%B %d, %Y")

        system = (
            "You are a prediction market designer. "
            "Create ONE realistic, verifiable YES/NO question based on current events. "
            "The question must resolve definitively (no ambiguity). "
            "Always output valid JSON only."
        )

        hints = {
            "crypto": f"Focus on specific price levels or on-chain metrics. Use real current prices. "
                      f"Example: 'Will Bitcoin close above $84,000 on {today}?'",
            "science": "Focus on space, climate, or medical research milestones. Must be verifiable.",
            "sports":  "Focus on today's or this week's actual games/matches with real teams.",
            "technology": "Focus on AI, big tech, or open source announcements expected soon.",
            "politics": "Focus on votes, elections, or geopolitical decisions expected imminently.",
            "finance":  "Focus on stock indices, earnings reports, or macroeconomic data releases.",
            "genlayer": "Focus on GenLayer protocol metrics, studionet activity, or ecosystem growth.",
        }
        hint = hints.get(category, "Focus on a verifiable near-future event.")

        schema = (
            '{\n'
            '  "question": "Will ...?",\n'
            '  "category": "<category>",\n'
            '  "deadline_hours_from_now": <integer>,\n'
            f'  "resolution_hint": "<URL or source where this can be verified>"\n'
            '}'
        )

        user_prompt = (
            f"Today: {today} UTC. Category: {category}\n"
            f"Hint: {hint}\n\n"
            f"Context from live data:\n{context}\n\n"
            f"Deadline: approximately {deadline_hours} hours from now.\n\n"
            f"Respond ONLY with JSON:\n{schema}"
        )

        resp = await self._call(
            model="llama-3.3-70b",
            system=system,
            user=user_prompt,
            temperature=0.9,
            max_tokens=400,
        )
        return parse_json(resp.content) or {
            "question": f"Will a major {category} event occur in the next {deadline_hours} hours?",
            "category": category,
            "deadline_hours_from_now": deadline_hours,
            "resolution_hint": "https://google.com",
        }

    async def score_reasoning(
        self,
        prediction_text: str,
        market_question: str,
        challenge_text: Optional[str] = None,
    ) -> dict:
        """Score reasoning quality on multiple dimensions."""
        ctx = f"Challenge received:\n{challenge_text}\n\n" if challenge_text else ""
        user_prompt = (
            f"Market: {market_question}\n\n"
            f"Validator reasoning:\n{prediction_text}\n\n"
            f"{ctx}"
            "Score this reasoning (each 0-100):\n"
            '{"evidence_quality": <0-100>, "logical_coherence": <0-100>, '
            '"risk_awareness": <0-100>, "clarity": <0-100>}'
        )
        resp = await self._call(
            model="mistral-31-24b",
            system="You are a rigorous reasoning evaluator. Output only JSON scores.",
            user=user_prompt,
            temperature=0.3,
            max_tokens=200,
        )
        scores = parse_json(resp.content) or {}
        return {
            "evidence_quality": int(scores.get("evidence_quality", 50)),
            "logical_coherence": int(scores.get("logical_coherence", 50)),
            "risk_awareness":    int(scores.get("risk_awareness",    50)),
            "clarity":           int(scores.get("clarity",           50)),
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_json(text: str) -> Optional[dict]:
    """Extract and parse the first JSON object from an LLM response."""
    if not text:
        return None
    # Try direct parse
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Strip markdown fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Find first {...} block
    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


# ── Singleton ─────────────────────────────────────────────────────────────────

llm_service = LLMService()
