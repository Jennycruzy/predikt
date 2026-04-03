# PREDIKT

**A private prediction market powered by Venice AI inference, GenLayer intelligent contracts, and Base Sepolia staking.**

PREDIKT lets users stake on real-world outcomes. AI validators debate each question privately using Venice AI, GenLayer records the logic on-chain, and Base Sepolia handles all staking and payouts — with no centralised intermediary at any layer.

---

## Why PREDIKT

Most prediction platforms expose user behaviour and AI reasoning to centralised servers. PREDIKT is built differently:

| Layer | What Runs There | Privacy |
|-------|----------------|---------|
| AI Inference | Venice AI | Prompts never logged, never trained on |
| Market Logic | GenLayer Studionet | On-chain, auditable, tamper-proof |
| Staking & Payouts | Base Sepolia (BetFactory) | Fully on-chain, self-custodial |
| Wallet | RainbowKit | Non-custodial, no identity required |

---

## Venice AI — Privacy Stack

All AI inference runs exclusively through **[Venice AI](https://venice.ai/)** — a decentralised, privacy-preserving LLM platform.

- **No logging** — prompts and completions are never stored
- **No training** — your data never fine-tunes any model
- **No censorship** — models reason freely on financial, political, and sensitive market topics
- **Decentralised** — no centralised AI provider can surveil staking behaviour or validator reasoning

**Validator personas (all via Venice):**

| Persona | Model | Style |
|---------|-------|-------|
| Analytical | `llama-3.3-70b` | Quantitative, data-driven |
| Nuanced | `mistral-31-24b` | Balanced, epistemic humility |
| Optimistic | `llama-3.3-70b` | Momentum, trend-following |
| Contrarian | `mistral-31-24b` | Skeptical, base-rate focused |
| Pragmatic | `llama-3.3-70b` | Precedent, institutional dynamics |

Resolution (factual outcome determination after deadline) also runs through Venice at `temperature: 0.1` for deterministic, grounded answers.

---

## GenLayer — Intelligent Contracts

Market state is managed by a Python intelligent contract on **GenLayer Studionet**. GenLayer contracts can execute AI inference and fetch live web data natively on-chain — meaning resolution logic is verifiable, not a black-box backend call.

Lifecycle: `OPEN → DEBATING → RESOLVING → FINALIZED`

The daemon bridges the finalized result to Base Sepolia via `processResolution`.

---

## Base Sepolia — Staking & Payouts

All staking runs on **Base Sepolia** through the `BetFactory` contract pattern:

- One `BetMarket` contract is deployed per market
- Users stake mUSDL (ERC-20) on YES or NO
- After resolution, winners call `claimWinnings` to receive their proportional share of the pool (minus 2% platform fee)
- No funds are ever held by a backend — only by the contract

**Token:** MockUSDL (mUSDL) · **Faucet:** 1,000 mUSDL per claim, 24h cooldown

---

## How a Market Works

1. **Creation** — The daemon generates markets from news across crypto, science, technology, politics, finance, and sports. Markets are deployed autonomously every few hours.
2. **Staking** — Users connect a wallet and stake mUSDL on YES or NO. Earlier stakers get better odds.
3. **Deadline** — When the market deadline passes, the daemon picks it up within 2 minutes.
4. **Debate** — Five Venice AI validators independently predict the outcome, then critique each other across multiple rounds. Reasoning quality — not validator count — determines weight.
5. **Resolution** — Venice AI is asked factually: *"Did this event actually happen?"* at low temperature. The result is written on-chain to GenLayer and bridged to Base Sepolia.
6. **Payout** — Winning stakers call `claimWinnings`. The losing pool is distributed proportionally to the winning side.

---

## Technology Stack

### AI
- **Venice AI** — privacy-preserving, uncensored, zero data retention
- Models: `llama-3.3-70b`, `mistral-31-24b`

### Backend
- **FastAPI** + Uvicorn
- **PostgreSQL** + SQLAlchemy
- **Market Daemon** — autonomous lifecycle manager, checks every 2 minutes

### Frontend
- **Next.js 14** + React 18
- **TailwindCSS**
- **D3.js** + Framer Motion (visualisations)
- **RainbowKit** + Wagmi + Viem (wallet)

### Blockchain
- **GenLayer Studionet** — intelligent contracts (Python)
- **Base Sepolia** — BetFactory staking contracts (Solidity)
- **MockUSDL** — ERC-20 staking token

---

## Market Categories

Crypto · Technology · Science · Politics · Finance · Sports · General

---

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in VENICE_API_KEY, OWNER_PRIVATE_KEY, BET_FACTORY_ADDRESS
python3 -m uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Open
open http://localhost:3000
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VENICE_API_KEY` | Venice AI key — all LLM inference |
| `OWNER_PRIVATE_KEY` | Wallet private key for signing on-chain transactions |
| `NEXT_PUBLIC_BET_FACTORY_ADDRESS` | BetFactory contract on Base Sepolia |
| `NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS` | GenLayer intelligent contract address |
| `NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID` | WalletConnect project ID |
| `DATABASE_URL` | PostgreSQL connection string |
| `BASE_SEPOLIA_RPC_URL` | Base Sepolia RPC endpoint |

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/markets` | All markets with status and stakes |
| `GET` | `/markets/{id}` | Single market with on-chain predictions |
| `POST` | `/run-debate` | Trigger AI validator debate |
| `GET` | `/debate-job/{id}` | Poll debate job status |
| `GET` | `/validators` | Validator reputation stats |
| `POST` | `/claim-tokens` | Claim mUSDL from faucet |
| `GET` | `/docs` | Interactive API docs |

---

## Roadmap

**Token Layer**
- User-deployed ERC-20 tokens as staking currency (not just mUSDL)
- Token-gated markets for community-specific pools

**Multi-Chain**
- Ethereum Mainnet — high-stakes markets
- Arbitrum & Optimism — low-fee staking
- Polygon — broad ecosystem access
- Cross-chain resolution via LayerZero (architecture already bridge-ready)

**Platform**
- Chainlink price feed oracles for crypto and finance markets
- Third-party validator marketplace — AI validators earn fees for accuracy
- Staker-proposed markets for mUSDL holders

---

## License

MIT

---

## Credits

- Intelligent contracts — [GenLayer Studionet](https://genlayer.com/)
- Privacy-preserving AI — [Venice AI](https://venice.ai/)
- Staking contract pattern — [courtofinternet/pm-kit](https://github.com/courtofinternet/pm-kit)
