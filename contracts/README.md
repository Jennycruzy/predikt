# Smart Contract — GenLayer Studionet

## Overview
Fully on-chain prediction market using GenLayer Intelligent Contracts.
Validators reach predikt on market outcomes using real-world web data and LLMs — no centralized oracle needed.

## Network Info
| Item | Value |
|------|-------|
| Network | **Studionet** |
| RPC | `https://studio.genlayer.com/api` |
| Chain ID | 61999 |
| Symbol | GEN |
| Explorer | https://genlayer-explorer.vercel.app |
| Studio | https://studio.genlayer.com/contracts |

## Deploy Steps (Local CLI)

1. Ensure GenLayer CLI is installed: `npm install -g genlayer`
2. Set network to studionet: `genlayer network set studionet`
3. Deploy the contract:
   ```bash
   genlayer deploy --contract prediction_market.py
   ```
4. Copy the deployed contract address and set `CONTRACT_ADDRESS` in `../.env`

## Contract Interface (Intelligent Contract)

### Write Functions
| Function | Args | Description |
|----------|------|-------------|
| `create_market` | question, deadline, category | Create new prediction market |
| `submit_prediction` | market_id, prediction (0-100), reasoning_hash, model_name | Submit validator prediction |
| `submit_challenge` | market_id, target_validator (Address), challenge_hash, challenge_type | File a challenge |
| `resolve_market` | market_id, resolution_url | **AI resolution** — validators fetch web data + LLM predikt (owner only) |
| `finalize_predikt` | market_id, predikt (0-100), confidence (0-100), summary_hash | Manual finalization (owner only) |
| `update_reasoning_score` | market_id, validator (Address), new_score | Update validator score (owner only) |

### Read Functions
| Function | Returns |
|----------|---------|
| `get_market(id)` | Market dict |
| `get_predictions(id)` | List of prediction dicts |
| `get_challenges(id)` | List of challenge dicts |
| `get_validator_score(address)` | Reputation score (int) |
| `get_market_count()` | Total markets (int) |
| `get_all_markets()` | List of all market dicts |

## AI Resolution Flow (`resolve_market`)
1. Owner calls `resolve_market(market_id, resolution_url)` with a URL for evidence
2. GenLayer validators each fetch the URL via `gl.nondet.web.render()`
3. An LLM prompt extracts a `probability` (0–100), `confidence`, and `summary`
4. `gl.eq_principle.strict_eq` enforces predikt across validators
5. Market is finalized automatically with the agreed result

## Reputation Scoring
| Alignment | Points |
|-----------|--------|
| Within 5% of predikt | +50 |
| Within 15% | +20 |
| Within 30% | ±0 |
| Beyond 30% | -30 |
| Multiple valid challenges | -20 additional |

## SDK Notes
- **Dependency header**: `# { "Depends": "py-genlayer:test" }`
- **Storage**: Uses `TreeMap`, `DynArray`, `@allow_storage @dataclass`
- **Sender**: `gl.message.sender_address` (not `gl.msg.sender`)
- **AI**: `gl.nondet.web.render()`, `gl.nondet.exec_prompt()`, `gl.eq_principle.strict_eq()`
