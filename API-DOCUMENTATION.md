# PREDIKT API Documentation

**Base URL:** `http://localhost:8000`  
**API Docs:** `http://localhost:8000/docs` (Interactive Swagger UI)

---

## 📋 Endpoints Overview

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/create-market` | Create prediction market |
| GET | `/markets` | List all markets |
| GET | `/markets/{id}` | Get market details |
| POST | `/run-debate` | Start AI debate pipeline |
| GET | `/results/{id}` | Get market results |
| GET | `/reasoning-tree/{id}` | Get debate reasoning tree |
| POST | `/claim-tokens` | Claim mUSDL from faucet |
| GET | `/validators` | Get validator reputation stats |
| GET | `/validators/{model}` | Get specific validator stats |

---

## 🎯 Market Management

### 1. Create Market

**Endpoint:** `POST /create-market`

**Request:**
```json
{
  "question": "Will Bitcoin hit $100k by end of 2024?",
  "deadline": "2024-12-31T23:59:59Z",
  "category": "crypto",
  "description": "Optional description"
}
```

**Response:**
```json
{
  "id": 1,
  "question": "Will Bitcoin hit $100k by end of 2024?",
  "deadline": "2024-12-31T23:59:59Z",
  "category": "crypto",
  "status": "open",
  "creator": "0x...",
  "created_at": "2026-03-22T10:52:15Z"
}
```

**cURL:**
```bash
curl -X POST http://localhost:8000/create-market \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Will Bitcoin hit $100k by end of 2024?",
    "deadline": "2024-12-31T23:59:59Z",
    "category": "crypto"
  }'
```

---

### 2. List Markets

**Endpoint:** `GET /markets`

**Query Parameters:**
- `status` (optional): `open`, `debating`, `resolved`
- `category` (optional): Filter by category
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "total": 10,
  "markets": [
    {
      "id": 1,
      "question": "Will Bitcoin hit $100k by end of 2024?",
      "status": "open",
      "category": "crypto",
      "created_at": "2026-03-22T10:52:15Z"
    }
  ]
}
```

**cURL:**
```bash
curl http://localhost:8000/markets?status=open&category=crypto
```

---

### 3. Get Market Details

**Endpoint:** `GET /markets/{id}`

**Response:**
```json
{
  "id": 1,
  "question": "Will Bitcoin hit $100k by end of 2024?",
  "description": "Based on current market trends",
  "deadline": "2024-12-31T23:59:59Z",
  "category": "crypto",
  "creator": "0x...",
  "status": "debating",
  "predikt": null,
  "confidence": null,
  "validator_count": 5,
  "debate_rounds": 2,
  "created_at": "2026-03-22T10:52:15Z",
  "updated_at": "2026-03-22T11:30:00Z"
}
```

---

## 🤖 AI Debate Engine

### 4. Run Debate Pipeline

**Endpoint:** `POST /run-debate`

**Request:**
```json
{
  "market_id": 1,
  "validators": ["gpt-4o", "claude-3-sonnet", "gemini-pro"],
  "rounds": 2,
  "use_real_llms": true
}
```

**Response:**
```json
{
  "market_id": 1,
  "status": "debating",
  "predictions": [
    {
      "model": "gpt-4o",
      "prediction": 0.72,
      "reasoning": "Analysis showing 72% confidence...",
      "score": 65.5,
      "challenged": false
    }
  ],
  "debate_rounds": [
    {
      "round": 1,
      "challenger": "claude-3-sonnet",
      "defender": "gpt-4o",
      "challenge": "Your methodology overlooks...",
      "response": "Valid point, but I argue..."
    }
  ],
  "predikt": null
}
```

**cURL:**
```bash
curl -X POST http://localhost:8000/run-debate \
  -H "Content-Type: application/json" \
  -d '{
    "market_id": 1,
    "validators": ["gpt-4o", "claude-3-sonnet"],
    "rounds": 2,
    "use_real_llms": false
  }'
```

---

### 5. Get Results

**Endpoint:** `GET /results/{id}`

**Response:**
```json
{
  "market_id": 1,
  "question": "Will Bitcoin hit $100k by end of 2024?",
  "status": "resolved",
  "predikt": 0.68,
  "confidence": 0.75,
  "summary": "After 3 rounds of debate, validators converged on...",
  "predictions": [
    {
      "model": "gpt-4o",
      "prediction": 0.72,
      "score": 78.5,
      "accuracy": 0.92
    }
  ],
  "winner": "gpt-4o",
  "resolved_at": "2026-03-22T12:00:00Z"
}
```

---

### 6. Get Reasoning Tree

**Endpoint:** `GET /reasoning-tree/{id}`

**Response:**
```json
{
  "market_id": 1,
  "tree": {
    "id": "root",
    "label": "Will Bitcoin hit $100k?",
    "children": [
      {
        "id": "gpt-4o",
        "label": "GPT-4o: 72% confidence",
        "value": 0.72,
        "reasoning": "Based on technical analysis...",
        "children": [
          {
            "id": "challenge-1",
            "label": "Claude challenges: Overlooks macroeconomic factors",
            "type": "challenge"
          }
        ]
      },
      {
        "id": "claude-3",
        "label": "Claude: 64% confidence",
        "value": 0.64,
        "reasoning": "Macro headwinds outweigh..."
      }
    ]
  }
}
```

---

## 💰 Token Faucet

### 7. Claim Tokens

**Endpoint:** `POST /claim-tokens`

**Request:**
```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f9bEb9",
  "amount": 1000
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Claimed 1000 mUSDL",
  "address": "0x742d...",
  "balance": "1000.00",
  "cooldown_until": "2026-03-23T10:52:15Z",
  "transaction_hash": "0x..."
}
```

**cURL:**
```bash
curl -X POST http://localhost:8000/claim-tokens \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f9bEb9",
    "amount": 1000
  }'
```

---

## 👥 Validator Reputation

### 8. List Validators

**Endpoint:** `GET /validators`

**Response:**
```json
[
  {
    "model": "gpt-4o",
    "total_predictions": 42,
    "correct_predictions": 38,
    "accuracy": 0.9048,
    "avg_confidence": 0.72,
    "reputation_score": 876,
    "challenges_received": 5,
    "challenges_won": 4,
    "updated_at": "2026-03-22T12:00:00Z"
  },
  {
    "model": "claude-3-sonnet",
    "total_predictions": 38,
    "correct_predictions": 34,
    "accuracy": 0.8947,
    "avg_confidence": 0.68,
    "reputation_score": 823,
    "challenges_received": 6,
    "challenges_won": 5,
    "updated_at": "2026-03-22T12:00:00Z"
  }
]
```

---

### 9. Get Validator Details

**Endpoint:** `GET /validators/{model}`

**Response:**
```json
{
  "model": "gpt-4o",
  "total_predictions": 42,
  "correct_predictions": 38,
  "accuracy": 0.9048,
  "avg_confidence": 0.72,
  "reputation_score": 876,
  "challenges_received": 5,
  "challenges_won": 4,
  "recent_predictions": [
    {
      "market_id": 1,
      "prediction": 0.72,
      "accuracy": 0.92,
      "created_at": "2026-03-22T10:52:15Z"
    }
  ]
}
```

---

## ✅ Testing All Endpoints

### Using cURL

```bash
# Create market
MARKET_ID=$(curl -s -X POST http://localhost:8000/create-market \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Test market?",
    "deadline": "2024-12-31T23:59:59Z",
    "category": "general"
  }' | jq -r '.id')

echo "Created market: $MARKET_ID"

# Run debate
curl -X POST http://localhost:8000/run-debate \
  -H "Content-Type: application/json" \
  -d "{
    \"market_id\": $MARKET_ID,
    \"validators\": [\"gpt-4o\", \"claude-3-sonnet\"],
    \"rounds\": 2
  }"

# Get results
curl http://localhost:8000/results/$MARKET_ID

# Get reasoning tree
curl http://localhost:8000/reasoning-tree/$MARKET_ID
```

### Using Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Create market
market_data = {
    "question": "Will AI surpass human intelligence by 2030?",
    "deadline": "2029-12-31T23:59:59Z",
    "category": "technology"
}
response = requests.post(f"{BASE_URL}/create-market", json=market_data)
market = response.json()
print(f"Created market: {market['id']}")

# Run debate
debate_data = {
    "market_id": market["id"],
    "validators": ["gpt-4o", "claude-3-sonnet"],
    "rounds": 2,
    "use_real_llms": False
}
response = requests.post(f"{BASE_URL}/run-debate", json=debate_data)
print(f"Debate started: {response.json()['status']}")

# Get results
response = requests.get(f"{BASE_URL}/results/{market['id']}")
results = response.json()
print(f"Predikt: {results['predikt']:.2%}")
```

---

## ⚠️ Error Handling

All endpoints return standard HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "detail": "Market not found with id 999",
  "status_code": 404
}
```

---

## 🔐 Authentication

Currently, all endpoints are public for demo purposes.

**For production:** Add authentication:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/markets")
def list_markets(credentials: HTTPAuthCredentials = Depends(security)):
    # Verify token
    pass
```

---

## 📊 Rate Limiting

For production, add rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/markets")
@limiter.limit("100/minute")
def list_markets():
    pass
```

---

## 📚 Interactive Documentation

Visit `http://localhost:8000/docs` for:
- Interactive Swagger UI
- Try-it-out buttons for all endpoints
- Request/response schemas
- Automatic validation
