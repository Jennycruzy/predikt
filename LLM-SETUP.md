# Real LLM APIs Integration Guide

## 🤖 Supported Models

| Model | Provider | Cost | Speed | Quality |
|-------|----------|------|-------|---------|
| **gpt-4o** | OpenAI | $0.015-0.06/K tokens | ⚡⚡⚡ | 🌟🌟🌟🌟🌟 |
| **claude-3-opus** | Anthropic | $0.015-0.075/K tokens | ⚡⚡ | 🌟🌟🌟🌟🌟 |
| **claude-3-sonnet** | Anthropic | $0.003-0.015/K tokens | ⚡⚡⚡ | 🌟🌟🌟🌟 |
| **gemini-pro** | Google | Free/Paid | ⚡⚡⚡ | 🌟🌟🌟🌟 |
| **llama-3-70b** | Together AI | $0.0007/K tokens | ⚡⚡⚡ | 🌟🌟🌟 |
| **mistral-large** | Mistral | $0.003/K tokens | ⚡⚡⚡ | 🌟🌟🌟🌟 |

---

## 1️⃣ OpenAI (GPT-4o)

### Setup

1. Create account: https://platform.openai.com/
2. Generate API key: https://platform.openai.com/api/keys
3. Add to `.env`:

```bash
OPENAI_API_KEY=sk_live_xxxxxxxxxxxx
```

4. Install SDK:

```bash
pip install openai
```

### Usage

```python
from backend.services.llm import llm_service

# In debate engine
response = await llm_service.generate_prediction(
    model="gpt-4o",
    market_question="Will Bitcoin hit $100k by end of 2024?",
    context="Current price is $95k..."
)
print(response.content)
print(f"Cost: ${response.cost:.4f}")
```

### Pricing

- Input: $0.000015 per token
- Output: $0.000060 per token
- ~1000 tokens = $0.08

---

## 2️⃣ Anthropic (Claude)

### Setup

1. Create account: https://console.anthropic.com/
2. Generate API key
3. Add to `.env`:

```bash
ANTHROPIC_API_KEY=sk_ant_xxxxxxxxxxxx
```

4. Install SDK:

```bash
pip install anthropic
```

### Usage

```python
response = await llm_service.generate_prediction(
    model="claude-3-opus",
    market_question="...",
)
```

### Pricing

**Claude 3 Opus** (Best quality):
- Input: $0.000015 per token
- Output: $0.000075 per token

**Claude 3 Sonnet** (Fast):
- Input: $0.000003 per token
- Output: $0.000015 per token

**Claude 3 Haiku** (Cheapest):
- Input: $0.00000025 per token
- Output: $0.00000125 per token

---

## 3️⃣ Google Generative AI (Gemini)

### Setup

1. Create account: https://ai.google.dev/
2. Generate API key: https://ai.google.dev/tutorials/setup
3. Add to `.env`:

```bash
GOOGLE_API_KEY=AIzaSy_xxxxxxxxxxxx
```

4. Install SDK:

```bash
pip install google-generativeai
```

### Usage

```python
response = await llm_service.generate_prediction(
    model="gemini-pro",
    market_question="...",
)
```

### Pricing

- **Free tier**: 60 requests/min
- **Paid**: ~$0.00375/million tokens

---

## 4️⃣ Together AI (Open-Source Models)

For Llama-3, Mistral, and other open-source models.

### Setup

1. Create account: https://api.together.xyz/
2. Generate API key
3. Add to `.env`:

```bash
TOGETHER_API_KEY=xxxxxxxxxxxx
```

4. Install SDK:

```bash
pip install together
```

### Usage

```python
response = await llm_service.generate_prediction(
    model="meta-llama/Llama-2-70b-chat-hf",
    market_question="...",
)
```

### Pricing

- Llama-3-70b: $0.0007 per 1K tokens
- Mistral-large: $0.003 per 1K tokens
- Generally cheapest option

---

## 🚀 Quick Start (Minimum Setup)

### Option A: Budget ($1-2/month)

Use **Anthropic Claude 3 Haiku** (cheapest quality model):

```bash
# Install
pip install anthropic

# .env
ANTHROPIC_API_KEY=sk_ant_xxxxxxxxxxxx

# Code
response = await llm_service.generate_prediction(
    model="claude-3-haiku",
    market_question="Will Bitcoin hit $100k?",
)
```

### Option B: Best Quality ($5-10/month)

Use **OpenAI GPT-4o** (best reasoning):

```bash
# Install
pip install openai

# .env
OPENAI_API_KEY=sk_live_xxxxxxxxxxxx

# Code
response = await llm_service.generate_prediction(
    model="gpt-4o",
    market_question="Will Bitcoin hit $100k?",
)
```

### Option C: Hybrid (3-5/month)

Use multiple models for diversity:

```bash
models = ["gpt-4o", "claude-3-sonnet", "gemini-pro"]
predictions = []

for model in models:
    response = await llm_service.generate_prediction(
        model=model,
        market_question=question,
    )
    predictions.append(response)

# Get predikt from multiple models
```

---

## 🔧 Integration in Debate Engine

Update `backend/core/debate_engine.py`:

```python
# Enable real LLMs
USE_REAL_LLMS = True  # Set this based on API availability

def generate_prediction(model, question, category, context=None):
    if USE_REAL_LLMS:
        try:
            response = asyncio.run(
                llm_service.generate_prediction(model, question, context)
            )
            return ValidatorPrediction(
                model=model,
                prediction=extract_prediction(response.content),
                reasoning=response.content,
                reasoning_hash=hash_content(response.content),
                score=0.5,
            )
        except Exception as e:
            print(f"LLM failed: {e}, using simulation")
    
    # Fallback to simulation...
```

---

## 📊 Monitor API Costs

Track spending per request:

```python
total_cost = 0

for market in markets:
    for validator in validators:
        response = await llm_service.generate_prediction(...)
        total_cost += response.cost
        print(f"Prediction cost: ${response.cost:.4f}")

print(f"Total cost: ${total_cost:.2f}")
```

---

## ❌ Troubleshooting

### API Key Not Found

```bash
# Check .env is loaded
python3 -c "import os; print(os.getenv('OPENAI_API_KEY'))"

# Make sure .env is in project root
ls -la .env
```

### Rate Limiting

```python
import asyncio
import time

async def generate_with_retry(model, question, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await llm_service.generate_prediction(model, question)
        except RateLimitError:
            wait_time = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

### High Costs

1. Use cheaper models (Haiku, Sonnet, Llama-3)
2. Reduce token count (shorter prompts)
3. Cache responses for similar questions
4. Use batch processing during off-peak

---

## ✅ Verify Setup

Test each provider:

```bash
python3 << 'EOF'
from backend.services.llm import llm_service
import asyncio

async def test():
    try:
        response = await llm_service.generate_prediction(
            model="gpt-4o",
            market_question="Test question?",
        )
        print(f"✅ OpenAI working: {response.content[:50]}...")
    except Exception as e:
        print(f"❌ OpenAI failed: {e}")

asyncio.run(test())
EOF
```

---

## 📚 Resources

- [OpenAI Docs](https://platform.openai.com/docs)
- [Anthropic Docs](https://docs.anthropic.com/)
- [Google AI Docs](https://ai.google.dev/docs)
- [Together AI Docs](https://docs.together.ai/)
- [Token Counter](https://platform.openai.com/tokenizer)

