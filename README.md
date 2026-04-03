# 🤖 PREDIKT

**Reasoning-driven prediction markets powered by AI validators debating on GenLayer Studionet.**

AI validators compete through intelligent debate to predict outcomes with confidence. Instead of capital-weighted voting, PREDIKT uses multi-round challenges and reasoning quality scoring to compute intelligence-weighted predikt.

---

## 🎯 What is PREDIKT?

A **decentralized prediction market** where:

✅ **Create Markets** - Ask any question: "Will Bitcoin hit $100k?" "Will AI surpass humans?"  
✅ **AI Debate** - Multiple LLM validators (GPT-4o, Claude, Gemini) submit predictions with reasoning  
✅ **Challenge Rounds** - Validators critique each other's logic through structured debate  
✅ **Predikt Scoring** - Quality of reasoning drives final prediction (not capital)  
✅ **Stake & Win** - Users stake mUSDL tokens on outcomes, winners claim proportional payouts  
✅ **Real Blockchain** - Smart contracts on GenLayer Studionet + token faucet on Base Sepolia  

---

## 🏗️ Architecture Overview

```
FRONTEND (Next.js 14)
    ↓
┌─────────────────────────────────────┐
│  User Dashboard                      │
│  • Create Markets                    │
│  • View Debates (Reasoning Tree)     │
│  • Stake Tokens (Wallet Connect)     │
│  • Monitor Reputation                │
└─────────────────────────────────────┘
    ↓                    ↓
Backend (FastAPI)    GenLayer Studionet
    ↓               (Intelligent Contract)
┌─────────────────────────────────────┐
│  API Endpoints                       │
│  • /create-market                    │
│  • /run-debate                       │
│  • /results/{id}                     │
│  • /validators                       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  LLM Orchestration                   │
│  • OpenAI (GPT-4o)                   │
│  • Anthropic (Claude-3)              │
│  • Google (Gemini)                   │
│  • Together AI (Llama, Mistral)      │
└─────────────────────────────────────┘
    ↓
PostgreSQL (Persistence)
    ↓
Base Sepolia (Token Faucet)
```

---

## � Quick Start (5 minutes)

**Just want to run it?** See [QUICK-START.md](./QUICK-START.md)

```bash
# Terminal 1: Backend
cd backend && pip install -r requirements.txt && python3 -m uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm install && npm run dev

# Open browser
open http://localhost:3000
```

---

## 📚 Documentation

| Document | Purpose | Time |
|----------|---------|------|
| **[QUICK-START.md](./QUICK-START.md)** | Get running in 5 minutes | 5 min |
| **[SETUP-GUIDE.md](./SETUP-GUIDE.md)** | Complete installation with database + API keys | 45 min |
| **[API-DOCUMENTATION.md](./API-DOCUMENTATION.md)** | All endpoints with cURL examples | Reference |
| **[DEPLOYMENT-CHECKLIST.md](./DEPLOYMENT-CHECKLIST.md)** | Production deployment guide | Reference |
| **[CONTRIBUTION-GUIDE.md](./CONTRIBUTION-GUIDE.md)** | How to contribute + roadmap | Reference |

---

## 🎯 Key Features

### 1. Market Creation
Create prediction markets on any topic:
- Question (10-500 characters)
- Deadline (future date)
- Category (crypto, weather, politics, etc)

### 2. AI Debate Engine
Multiple LLM validators submit predictions:
- **Initial predictions** - Each validator commits confidence + reasoning
- **Challenge rounds** - Validators critique each other's logic
- **Scoring** - Reasoning quality determines weight
- **Predikt** - Final prediction computed from debate

### 3. Validator Reputation
Track accuracy of each AI model:
- Total predictions made
- Prediction accuracy
- Average confidence
- Challenges won/lost
- Reputation score (0-1000)

### 4. User Staking
Stake mUSDL tokens on market outcomes:
- YES/NO positions
- Proportional payouts
- 24-hour claim window after resolution

### 5. Token Faucet
Claim free mUSDL tokens:
- 1000 mUSDL per claim
- 24-hour cooldown
- Real ERC-20 token on Base Sepolia

### 6. Wallet Integration
Connect with RainbowKit:
- MetaMask, WalletConnect, and injected wallets
- Base Sepolia + GenLayer Studionet support
- Balance tracking
- Transaction signing via Wagmi + Viem

---

## 🏆 How AI Predikt Works

### Step 1: Prediction Submission
```
Multiple validators independently generate predictions:
- GPT-4o: "75% confidence - technical analysis shows..."
- Claude: "62% confidence - macro factors suggest..."
- Gemini: "68% confidence - considering both perspectives..."
```

### Step 2: Challenge Round
```
Validators challenge each other:
- Claude challenges GPT: "You overlooked regulatory risk"
- GPT responds: "Valid point, revising to 70%"
- Validators score challenge quality
```

### Step 3: Predikt Computation
```
Intelligence-weighted predikt:
1. Score quality of reasoning (evidence, logic, uncertainty)
2. Weight by validator accuracy (from history)
3. Compute final prediction = weighted average
4. Confidence = agreement level of validators
```

### Step 4: Resolution
```
When market deadline passes:
1. Actual outcome determined
2. Check if AI prediction matched
3. Update validator accuracy scores
4. Adjust reputation ratings
5. Distribute payouts to winning stakers
```

---

## 🏗️ Technology Stack

### AI — Venice Privacy Stack
PREDIKT uses **[Venice AI](https://venice.ai/)** as its primary LLM provider for all validator inference, debate rounds, and market resolution.

Venice is a privacy-preserving AI platform — prompts and responses are **never logged, stored, or used for training**. This matters for a prediction market because:

- **Validator reasoning stays private** — debate logic and staking signals are not exposed to third parties
- **No data retention** — Venice processes and immediately discards all inference requests
- **Uncensored models** — validators can reason freely about financial, political, and sensitive market topics without content filtering interfering with predictions
- **Decentralisation alignment** — Venice's architecture matches PREDIKT's ethos: no central authority controlling the AI layer

**Models in use (via Venice):**
| Validator Persona | Venice Model | Style |
|-------------------|-------------|-------|
| gpt-4o (analytical) | `llama-3.3-70b` | Quantitative, data-driven |
| claude-sonnet (nuanced) | `mistral-31-24b` | Balanced, epistemic humility |
| gemini-pro (optimistic) | `llama-3.3-70b` | Momentum, trend-following |
| llama-3 (contrarian) | `mistral-31-24b` | Skeptical, base-rate focused |
| mistral-large (pragmatic) | `llama-3.3-70b` | Precedent, institutional dynamics |

Resolution calls (determining actual real-world outcomes) also run through Venice at low temperature (0.1) for factual accuracy.

---

### Backend
- **API:** FastAPI + Uvicorn
- **Database:** PostgreSQL + SQLAlchemy ORM
- **Smart Contracts:** GenLayer Studionet (Python)
- **LLM / AI:** Venice AI (privacy-preserving, uncensored inference)
- **Validation:** Pydantic

**7 Database Models:**
- `User` - User profiles + token balance
- `Market` - Prediction markets
- `Prediction` - Individual validator predictions
- `Debate` - Multi-round challenge records
- `Challenge` - Individual challenge + response
- `Stake` - User token stakes
- `ValidatorReputation` - Model accuracy tracking

### Frontend
- **Framework:** Next.js 14 + React 18
- **Styling:** TailwindCSS
- **Visualization:** D3.js + Framer Motion
- **Blockchain:** ethers.js
- **Wallet:** RainbowKit + Wagmi + Viem
- **HTTP:** React Query + fetch

### Blockchain
- **Intelligent Contracts:** GenLayer Studionet (Python)
- **Token:** ERC-20 on Base Sepolia (MockUSDL)
- **RPC Endpoints:**
  - GenLayer: `https://bradbury.genlayer.com/rpc`
  - Base Sepolia: `https://sepolia.base.org`

---

## 📊 API Endpoints

**See full documentation:** [API-DOCUMENTATION.md](./API-DOCUMENTATION.md)

```bash
# Create market
POST /create-market

# Run AI debate
POST /run-debate

# Get market results
GET /results/{id}

# List validators
GET /validators

# Claim tokens
POST /claim-tokens

# Interactive docs
GET /docs
```

---

## 🔧 Environment Setup

**Before running, create `.env` file:**

```bash
cp .env.example .env
```

**Then add:**

1. **GenLayer Studionet** - Contract address
2. **Base Sepolia** - RPC endpoint
3. **LLM APIs** - OpenAI, Anthropic, Google, or Together AI key
4. **WalletConnect** - Project ID (from cloud.walletconnect.com)
5. **Database** - PostgreSQL connection string

See [SETUP-GUIDE.md](./SETUP-GUIDE.md) for detailed instructions.

---

## 🐳 Docker Deployment

Run everything in Docker:

```bash
docker-compose up -d
```

Opens:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Database: PostgreSQL on :5432

---

## 🔮 Roadmap

What's coming next for PREDIKT:

### Token & Asset Layer
- **Custom Token Creation** — Users will be able to deploy and stake with their own ERC-20 tokens, not just mUSDL. Create a market, define your staking token, and let the community participate with assets they already hold.
- **Token-Gated Markets** — Restrict market participation to holders of a specific token for community-specific prediction pools.

### Multi-Chain Expansion
- **Ethereum Mainnet** — Full deployment on mainnet for high-stakes markets with real economic weight.
- **Arbitrum & Optimism** — L2 deployments for low-fee, high-throughput staking.
- **Polygon** — Broad accessibility for users across the ecosystem.
- **Cross-Chain Resolution** — Markets created on one chain resolved by oracles and AI validators across chains via LayerZero (architecture already bridge-ready).

### Platform
- **Market Categories & Tagging** — Richer categorisation and search across Crypto, Science, Technology, Politics, and more.
- **On-Chain Resolution Oracles** — Automated resolution via price feeds and verified news sources, reducing reliance on manual settlement.
- **Validator Marketplace** — Third-party AI validators that can register, stake reputation, and earn fees for accurate predictions.

---

## 🤝 Contributing

See [CONTRIBUTION-GUIDE.md](./CONTRIBUTION-GUIDE.md) for:
- Development setup
- Code standards
- Testing requirements
- PR process
- Good first issues

---

## 📜 License

MIT License - See LICENSE file for details.

---

## 🙏 Credits

- Built with [GenLayer Studionet](https://genlayer.com/) intelligent contracts
- Inspired by [courtofinternet/pm-kit](https://github.com/courtofinternet/pm-kit) architecture
- AI validators and market resolution powered by [Venice AI](https://venice.ai/) — private, uncensored, decentralised inference

---

## 📞 Support

- **Questions?** Check the docs above
- **Found a bug?** Open a GitHub Issue
- **Want to contribute?** See CONTRIBUTION-GUIDE.md
- **Need help?** See SETUP-GUIDE.md troubleshooting section

---

**Ready to predict with AI predikt? 🚀**

Start with [QUICK-START.md](./QUICK-START.md) or [SETUP-GUIDE.md](./SETUP-GUIDE.md)
│   │   │   ├── PredictionDistribution.tsx
│   │   │   ├── ReputationChart.tsx
│   │   │   ├── MarketCard.tsx
│   │   │   ├── ValidatorCard.tsx
│   │   │   └── CreateMarketModal.tsx
│   │   ├── hooks/
│   │   │   ├── useMarkets.ts
│   │   │   ├── useDebate.ts
│   │   │   └── useContract.ts
│   │   ├── lib/
│   │   │   ├── api.ts                 # Backend API client
│   │   │   ├── contract.ts            # ABI + read/write helpers
│   │   │   └── constants.ts           # Config, validators, chain
│   │   └── styles/theme.ts
│   ├── tailwind.config.js
│   └── next.config.js
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Quick Start

```bash
# 1. Install everything
make install

# 2. Start backend
make backend

# 3. Start frontend (new terminal)
make frontend

# 4. Open http://localhost:3000
```

### Deploy Contracts

```bash
# Copy env and set PRIVATE_KEY
cp .env.example .env

# Deploy MockUSDL + BetFactory to Base Sepolia
make deploy-token

# Deploy intelligent contract to GenLayer Studionet
make deploy-genlayer
```

---

## Key Features

### From pm-kit
- **MockUSDL token** with rate-limited faucet (1000 mUSDL / 24hr)
- **BetFactory pattern** for deploying individual market contracts
- **BetMarket state machine**: ACTIVE → DEBATING → RESOLVING → RESOLVED
- **7-day resolution timeout** with automatic cancellation + refund
- **Platform fee** (2%) on winning payouts
- **LayerZero bridge ready** architecture for cross-chain resolution

### Original
- **AI Debate Engine** with 5 validator profiles (GPT-4o, Claude, Gemini, Llama, Mistral)
- **Multi-round cross-examination** between validators
- **Intelligence-weighted predikt** (not equal weights)
- **Reasoning quality scoring** based on evidence depth, peer agreement, historical reputation, challenge outcomes
- **D3.js reasoning tree** visualization
- **Validator reputation system** evolving over time

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/create-market` | Create prediction market |
| POST | `/run-debate` | Execute AI debate pipeline |
| GET | `/results/{id}` | Full market results |
| GET | `/reasoning-tree/{id}` | Reasoning tree JSON |
| GET | `/validators` | Reputation stats |
| GET | `/markets` | List all markets |
| POST | `/predict-with-reasoning` | One-call external API |

---

## License

MIT
