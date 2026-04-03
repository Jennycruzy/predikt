# ⚡ PREDIKT: Quick Start (5 minutes)

**Goal:** Get PREDIKT running locally in 5 minutes.

---

## 🚀 Start Both Services

### Terminal 1: Backend
```bash
# Start from /Users/user/Downloads/Predikt
python3 -m uvicorn backend.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Frontend
```bash
cd /Users/user/Downloads/PREDIKT/frontend
npm install
npm run dev
```

**Expected output:**
```
✓ ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

---

## 🌐 Access the App

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **API Base:** http://localhost:8000

---

## 🎯 Try These Actions

### 1. Create a Market
```bash
curl -X POST http://localhost:8000/create-market \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Will it rain tomorrow?",
    "deadline": "2024-12-31T23:59:59Z",
    "category": "weather"
  }'
```

**Response:**
```json
{
  "id": 1,
  "question": "Will it rain tomorrow?",
  "status": "open"
}
```

---

### 2. Run AI Debate
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

**Response:**
```json
{
  "market_id": 1,
  "status": "debating",
  "predictions": [
    {
      "model": "gpt-4o",
      "prediction": 0.72,
      "reasoning": "..."
    }
  ]
}
```

---

### 3. View Results
```bash
curl http://localhost:8000/results/1
```

---

### 4. See Validator Reputation
```bash
curl http://localhost:8000/validators
```

---

## 🔧 Configuration (Optional)

Add API keys to `.env` for real AI predictions:

```bash
# OpenAI (free trial includes $5)
echo "OPENAI_API_KEY=sk-..." >> .env

# Or use Google Gemini (completely free)
echo "GOOGLE_API_KEY=..." >> .env

# Restart backend
# Both terminals: Ctrl+C
# Then run: python3 -m uvicorn backend.main:app --reload --port 8000 (backend)
```

---

## ❓ Troubleshooting

**Port 8000/3000 already in use?**
```bash
lsof -i :8000
kill -9 <PID>
```

**Database connection error?**
```bash
# Create database
createdb predikt_db

# Or install PostgreSQL
brew install postgresql
brew services start postgresql
```

**Missing dependencies?**
```bash
# Backend
pip install fastapi uvicorn sqlalchemy

# Frontend
npm install
```

---

## 📚 Next Steps

- Read [SETUP-GUIDE.md](./SETUP-GUIDE.md) for full setup
- Read [API-DOCUMENTATION.md](./API-DOCUMENTATION.md) for all endpoints
- Explore [DEPLOYMENT-CHECKLIST.md](./DEPLOYMENT-CHECKLIST.md) for production
- See [CONTRIBUTION-GUIDE.md](./CONTRIBUTION-GUIDE.md) to contribute

---

## 🆘 Help

- **API Issues?** Check `http://localhost:8000/docs`
- **Frontend Issues?** Open browser DevTools (F12)
- **Database Issues?** Check logs with `psql predikt_db`
- **General Help?** Read the main [README.md](./README.md)

---

**You're all set! 🎉 Start creating prediction markets with AI validators!**
