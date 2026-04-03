# ⚡ PREDIKT: Complete Setup & Installation Guide

This guide walks you through setting up PREDIKT from zero to production-ready.

**Estimated Time:** 45-60 minutes

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Node.js & npm** (v18+) - Download from https://nodejs.org/
- [ ] **Python** (v3.10+) - Download from https://www.python.org/
- [ ] **PostgreSQL** (v14+) - Download from https://www.postgresql.org/
- [ ] **Git** - Download from https://git-scm.com/
- [ ] **macOS/Linux terminal** or **Windows PowerShell**
- [ ] **GenLayer Studionet contract address** - Have the contract address ready
- [ ] **Web browser** for registering API keys/accounts

---

## 🚀 Phase 1: Core Installation (10 minutes)

### 1.1 Backend Dependencies

Navigate to the backend directory and install Python dependencies:

```bash
cd /Users/user/Downloads/PREDIKT/backend
pip install -r requirements.txt
```

**What gets installed:**
- FastAPI + Uvicorn (REST API server)
- SQLAlchemy + psycopg2 (PostgreSQL ORM)
- openai, anthropic, google-generativeai, together (LLM SDKs)
- pydantic, python-dotenv (Config & validation)

**Verify installation:**
```bash
python -c "import fastapi, sqlalchemy, openai; print('✅ All dependencies installed')"
```

---

### 1.2 Frontend Dependencies

Navigate to the frontend directory and install npm dependencies:

```bash
cd /Users/user/Downloads/PREDIKT/frontend
npm install
```

**What gets installed:**
- Next.js 14 (React framework)
- ethers.js (Blockchain interaction)
- @privy-io/react-auth (Wallet connection)
- D3.js, Framer Motion (Visualizations)
- TailwindCSS (Styling)

**Verify installation:**
```bash
npm ls | head -20
```

---

## 🗄️ Phase 2: Database Setup (15 minutes)

### 2.1 Create PostgreSQL Database

Open a terminal and create the database:

```bash
# macOS with Homebrew
brew services start postgresql

# Or Linux
sudo systemctl start postgresql

# Create database
createdb predikt_db

# Verify
psql predikt_db -c "\dt"
```

**Expected output:** `Did not find any relations.` (empty database)

---

### 2.2 Update Environment Variables

Copy the template and add database connection:

```bash
cd /Users/user/Downloads/PREDIKT
cp .env.example .env
```

Edit `.env` and add:

```bash
# DATABASE
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/predikt_db
```

**Get your PostgreSQL username:**
```bash
whoami
```

---

### 2.3 Initialize Database Tables

Start the backend (it auto-creates tables):

```bash
cd backend
python3 -m uvicorn backend.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Database initialized with 7 tables
```

Let it run, then press `Ctrl+C` to stop.

---

## 🎮 Phase 3: Blockchain Configuration (10 minutes)

### 3.1 Add GenLayer Studionet Contract

Edit `.env` and add:

```bash
# GENLAYER BRADBURY
GENLAYER_RPC_URL=https://bradbury.genlayer.com/rpc
CONTRACT_ADDRESS=0x9e1a258598b8a698c20d1a5621c86f1733a8e2e7fb069b230c191f2b28e4ba49
GENLAYER_OWNER_PRIVATE_KEY=your_private_key_here

# BASE SEPOLIA (for token faucet)
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
MUSDL_TOKEN_ADDRESS=0x... # To be deployed or provided
FAUCET_ADDRESS=0x... # To be deployed or provided
```

**How to find your Studionet contract address:**
1. Go to https://bradbury-explorer.genlayer.com/
2. Search for your contract address
3. Verify it's `PredictionMarket` type

---

### 3.2 Frontend Blockchain Configuration

Edit `.env` and add:

```bash
# FRONTEND
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS=0x9e1a258598b8a698c20d1a5621c86f1733a8e2e7fb069b230c191f2b28e4ba49
NEXT_PUBLIC_BASE_SEPOLIA_RPC=https://sepolia.base.org
```

---

## 🔐 Phase 4: Privy Wallet Integration (5 minutes)

### 4.1 Register Privy Account

1. Go to https://dashboard.privy.io/
2. Click **Sign up** (or Sign in if you have account)
3. Create account with email/GitHub/Google
4. Create a new app:
   - App Name: `PREDIKT`
   - Select **Test environment**
   - Select chains: **Base Sepolia** + **Custom RPC** (GenLayer Studionet)

### 4.2 Get Privy App ID

After creating app:
1. Go to **Settings** → **API Keys**
2. Copy `Public API Key` (looks like `privy_public_...`)
3. Add to `.env`:

```bash
NEXT_PUBLIC_PRIVY_APP_ID=privy_public_xxxxxxxxxxxxx
```

---

## 🤖 Phase 5: LLM API Setup (10 minutes)

Choose one or more LLM providers:

### 5.1 OpenAI (GPT-4o) - $0.003-0.015 per 1K tokens

```bash
# 1. Go to https://platform.openai.com/account/api-keys
# 2. Create API key
# 3. Add to .env
OPENAI_API_KEY=sk-...
```

**Cost estimate:** ~$0.03 per full debate (2 rounds)

---

### 5.2 Anthropic (Claude-3) - $0.003-0.015 per 1K tokens

```bash
# 1. Go to https://console.anthropic.com/
# 2. Create API key
# 3. Add to .env
ANTHROPIC_API_KEY=sk-ant-...
```

**Cost estimate:** ~$0.02 per full debate

---

### 5.3 Google (Gemini-Pro) - FREE

```bash
# 1. Go to https://makersuite.google.com/app/apikey
# 2. Enable Generative AI API
# 3. Create API key
# 4. Add to .env
GOOGLE_API_KEY=...
```

**Cost:** Completely free tier available

---

### 5.4 Together AI (Open-source) - $0.001 per 1M tokens

```bash
# 1. Go to https://www.together.ai/
# 2. Create account
# 3. Get API key from https://www.together.ai/settings/api-keys
# 4. Add to .env
TOGETHER_API_KEY=...
```

**Models available:**
- Llama-3 8B: $0.0002 per 1M tokens
- Mistral 7B: $0.0002 per 1M tokens
- Mixtral 8x7B: $0.0006 per 1M tokens

**Recommended:** Use Google Gemini (free) for testing, Together AI for production (cheapest)

---

## 📱 Phase 6: Token Faucet Setup (Optional, 5 minutes)

If you want real mUSDL token faucet functionality:

### 6.1 Deploy MockUSDL to Base Sepolia

```bash
cd /Users/user/Downloads/PREDIKT/contracts

# Install contract dependencies
npm install

# Deploy using Hardhat
npx hardhat run scripts/deploy.js --network baseSepolia
```

**What this does:**
- Deploys MockUSDL ERC-20 token to Base Sepolia
- Outputs contract addresses to `deployment-baseSepolia.json`

### 6.2 Update Token Configuration

Add to `.env`:

```bash
MUSDL_TOKEN_ADDRESS=0x... # From deployment output
FAUCET_ADDRESS=0x... # From deployment output
```

---

## ✅ Phase 7: Verify All Systems (5 minutes)

### 7.1 Start Backend

```bash
cd /Users/user/Downloads/PREDIKT/backend
python3 -m uvicorn backend.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
✅ Connected to PostgreSQL
✅ Database initialized
INFO:     Application startup complete
```

---

### 7.2 Start Frontend (in new terminal)

```bash
cd /Users/user/Downloads/PREDIKT/frontend
npm run dev
```

**Expected output:**
```
✓ ready - started server on 0.0.0.0:3000, url: http://localhost:3000
✓ compiled client and server successfully
```

---

### 7.3 Test All Systems

#### Test Backend API
```bash
curl http://localhost:8000/docs
# Should return Swagger UI HTML
```

#### Test Frontend
```bash
open http://localhost:3000
# Should load PREDIKT dashboard
```

#### Test Database
```bash
psql predikt_db -c "SELECT COUNT(*) FROM validators;"
# Should return validator count
```

#### Test LLM (if API keys configured)
```bash
curl -X POST http://localhost:8000/run-debate \
  -H "Content-Type: application/json" \
  -d '{
    "market_id": 1,
    "validators": ["gpt-4o"],
    "rounds": 1,
    "use_real_llms": true
  }'
```

---

## 🎯 Phase 8: Feature Testing Checklist

Now that everything is running, test each feature:

### ✅ Markets & Debate

- [ ] Create market via dashboard
- [ ] Market appears in "All Markets" list
- [ ] Click market shows debate timeline
- [ ] Run AI debate button works
- [ ] See predictions from validators
- [ ] See reasoning tree visualization
- [ ] See results with predikt %

### ✅ Wallet Connection (if Privy configured)

- [ ] Click "Connect Wallet" button
- [ ] Privy login modal appears
- [ ] Select wallet (MetaMask, Phantom, etc.)
- [ ] Wallet connects and shows address
- [ ] Disconnect button works

### ✅ Token Faucet (if MockUSDL deployed)

- [ ] See balance of mUSDL
- [ ] Click "Claim Tokens" button
- [ ] Transaction submits to Base Sepolia
- [ ] Balance updates after 24h cooldown
- [ ] See cooldown timer

### ✅ Validators & Reputation

- [ ] See all validators in sidebar
- [ ] Each validator has accuracy %
- [ ] Each validator has reputation score
- [ ] Click validator shows detailed stats
- [ ] Accuracy increases with correct predictions

### ✅ API Documentation

- [ ] Visit http://localhost:8000/docs
- [ ] Try "Create Market" endpoint
- [ ] Try "Run Debate" endpoint
- [ ] See response schemas

---

## 🐛 Troubleshooting

### Problem: `Database connection failed`

**Solution:**
```bash
# Check PostgreSQL is running
psql -U $USER -d predikt_db

# If fails, restart PostgreSQL
brew services restart postgresql  # macOS
sudo systemctl restart postgresql  # Linux
```

---

### Problem: `Port 8000 already in use`

**Solution:**
```bash
# Kill process using port 8000
lsof -i :8000
kill -9 <PID>
```

---

### Problem: `OPENAI_API_KEY not found`

**Solution:**
```bash
# Check .env file exists
cat /Users/user/Downloads/PREDIKT/.env | grep OPENAI

# If missing, add it:
echo "OPENAI_API_KEY=sk-..." >> /Users/user/Downloads/PREDIKT/.env

# Restart backend
```

---

### Problem: `Privy login not working`

**Solution:**
1. Verify `NEXT_PUBLIC_PRIVY_APP_ID` in `.env`
2. Check Privy dashboard for correct app ID
3. Ensure Base Sepolia is enabled in Privy settings
4. Clear browser cache (Cmd+Shift+Delete)

---

### Problem: `Token balance showing 0`

**Solution:**
```bash
# Check MockUSDL deployed to Base Sepolia
echo $MUSDL_TOKEN_ADDRESS  # Should not be empty

# Verify address is valid
curl https://sepolia.base.org \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["0x...","latest"],"id":1}'
```

---

## 📊 Next Steps

Now that your system is running:

1. **Create test markets** with various predictions
2. **Run debates** and watch AI validators compete
3. **Monitor the reasoning tree** visualization
4. **Check validator accuracy** over multiple debates
5. **Deploy to production** following [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 🆘 Need Help?

### Logs to Check

**Backend logs:**
```bash
# Terminal 1: Check FastAPI startup
python /Users/user/Downloads/PREDIKT/backend/main.py

# Check database logs
tail -f /usr/local/var/log/postgresql.log  # macOS
tail -f /var/log/postgresql/postgresql.log  # Linux
```

**Frontend logs:**
```bash
# Terminal 2: Check Next.js build
npm run dev 2>&1 | tee frontend.log
```

**Database logs:**
```bash
psql predikt_db -c "SELECT * FROM markets LIMIT 5;"
```

---

## ✨ Congratulations!

You now have a fully functional AI prediction market with:

✅ GenLayer Studionet intelligent contracts  
✅ AI validators (GPT-4o, Claude, Gemini, Llama-3)  
✅ PostgreSQL persistence  
✅ Real blockchain wallet connection (Privy)  
✅ Token faucet with Base Sepolia integration  
✅ AI debate with multi-round challenges  
✅ Validator reputation tracking  

**Start creating markets and watch AI debate!** 🚀
