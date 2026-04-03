"""
Faucet Router — Gasless mUSDL faucet.

The backend owner wallet calls MockUSDL.mint() so users pay zero gas.
Rate-limited per address (24h cooldown, stored in memory).
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from web3 import Web3
from web3.middleware import geth_poa_middleware

router = APIRouter(prefix="/faucet", tags=["faucet"])

# ── Config ────────────────────────────────────────────────────────────────────

FAUCET_AMOUNT   = 1_000   # mUSDL tokens (human units)
FAUCET_COOLDOWN = 86_400  # 24 h in seconds
ETH_DRIP_WEI    = 5_000_000_000_000_000  # 0.005 ETH — covers ~100 txs on Base Sepolia

MUSDL_ADDRESS   = os.getenv("NEXT_PUBLIC_MOCK_USDL_ADDRESS", "")
PRIVATE_KEY     = os.getenv("OWNER_PRIVATE_KEY", "")
BASE_RPC        = os.getenv("BASE_SEPOLIA_RPC_URL",
                    os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org"))

# Minimal ABI — only what we need
MUSDL_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "to",     "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "mint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs":  [{"internalType": "address", "name": "account", "type": "address"}],
        "name":    "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs":  [{"internalType": "address", "name": "user", "type": "address"}],
        "name":    "faucetCooldownRemaining",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# In-memory cooldown store (resets on restart — acceptable for testnet)
_claim_history: Dict[str, float] = {}


def _w3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(BASE_RPC))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3


# ── Models ────────────────────────────────────────────────────────────────────

class ClaimRequest(BaseModel):
    wallet_address: str
    amount: float = FAUCET_AMOUNT


class ClaimResponse(BaseModel):
    status: str
    wallet_address: str
    amount: float
    transaction_hash: str
    timestamp: str
    next_claim_available: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/claim", response_model=ClaimResponse)
async def claim_tokens(request: ClaimRequest):
    """
    Gasless faucet: backend owner wallet mints mUSDL directly to the user.
    User pays no gas. Rate-limited to once per 24 h per wallet.
    """
    if not request.wallet_address or not request.wallet_address.startswith("0x"):
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    wallet = request.wallet_address.lower()
    now    = time.time()

    # Cooldown check
    since = now - _claim_history.get(wallet, 0)
    if since < FAUCET_COOLDOWN:
        remaining = int(FAUCET_COOLDOWN - since)
        raise HTTPException(
            status_code=429,
            detail=f"Cooldown active. Next claim in {remaining // 3600}h {(remaining % 3600) // 60}m",
        )

    if not PRIVATE_KEY or not MUSDL_ADDRESS:
        # Fallback: return mock success so UI doesn't break during dev
        _claim_history[wallet] = now
        next_claim = datetime.utcnow() + timedelta(seconds=FAUCET_COOLDOWN)
        return ClaimResponse(
            status="success_mock",
            wallet_address=wallet,
            amount=FAUCET_AMOUNT,
            transaction_hash="0x" + "0" * 64,
            timestamp=datetime.utcnow().isoformat(),
            next_claim_available=next_claim.isoformat(),
        )

    try:
        w3      = _w3()
        account = w3.eth.account.from_key(PRIVATE_KEY)
        token   = w3.eth.contract(
            address=w3.to_checksum_address(MUSDL_ADDRESS),
            abi=MUSDL_ABI,
        )
        amount_wei = w3.to_wei(int(request.amount), "ether")  # 18 decimals

        # Use "pending" nonce to account for any queued txs from the same wallet
        nonce = w3.eth.get_transaction_count(account.address, "pending")
        # 20% gas premium to avoid "replacement transaction underpriced"
        gas_price = int(w3.eth.gas_price * 1.2)

        # ── Tx 1: Mint mUSDL ──────────────────────────────────────────────────
        tx = token.functions.mint(
            w3.to_checksum_address(request.wallet_address),
            amount_wei,
        ).build_transaction({
            "from":     account.address,
            "nonce":    nonce,
            "gasPrice": gas_price,
        })

        signed   = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        raw_tx   = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None)
        tx_hash  = w3.eth.send_raw_transaction(raw_tx)
        w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        # ── Tx 2: Drip ETH for gas (best-effort) ─────────────────────────────
        # Users need ETH to pay for approve + bet transactions.
        # Only drip if owner still has a comfortable balance.
        try:
            owner_eth = w3.eth.get_balance(account.address)
            if owner_eth > w3.to_wei(0.05, "ether"):
                eth_tx = {
                    "from":     account.address,
                    "to":       w3.to_checksum_address(request.wallet_address),
                    "value":    ETH_DRIP_WEI,
                    "gas":      21_000,
                    "gasPrice": gas_price,
                    "nonce":    nonce + 1,
                    "chainId":  84532,
                }
                signed_eth = w3.eth.account.sign_transaction(eth_tx, private_key=PRIVATE_KEY)
                raw_eth    = getattr(signed_eth, "rawTransaction", None) or getattr(signed_eth, "raw_transaction", None)
                w3.eth.send_raw_transaction(raw_eth)
                # fire-and-forget — don't block the response
        except Exception as eth_exc:
            print(f"[FAUCET] ETH drip failed (non-fatal): {eth_exc}")

        _claim_history[wallet] = now
        next_claim = datetime.utcnow() + timedelta(seconds=FAUCET_COOLDOWN)

        return ClaimResponse(
            status="success",
            wallet_address=wallet,
            amount=int(request.amount),
            transaction_hash=tx_hash.hex(),
            timestamp=datetime.utcnow().isoformat(),
            next_claim_available=next_claim.isoformat(),
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Mint failed: {str(exc)}")


@router.get("/status/{wallet_address}")
async def faucet_status(wallet_address: str):
    wallet = wallet_address.lower()
    since  = time.time() - _claim_history.get(wallet, 0)

    if since >= FAUCET_COOLDOWN:
        return {"can_claim": True, "next_claim_in_seconds": 0, "amount": FAUCET_AMOUNT}

    remaining = int(FAUCET_COOLDOWN - since)
    return {
        "can_claim": False,
        "next_claim_in_seconds": remaining,
        "next_claim_in_hours": round(remaining / 3600, 1),
    }


@router.get("/balance/{wallet_address}")
async def token_balance(wallet_address: str):
    """Return mUSDL balance for a wallet."""
    if not MUSDL_ADDRESS:
        return {"balance": 0, "symbol": "mUSDL"}
    try:
        w3    = _w3()
        token = w3.eth.contract(
            address=w3.to_checksum_address(MUSDL_ADDRESS),
            abi=MUSDL_ABI,
        )
        raw = token.functions.balanceOf(
            w3.to_checksum_address(wallet_address)
        ).call()
        return {"balance": float(w3.from_wei(raw, "ether")), "symbol": "mUSDL"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/info")
async def faucet_info():
    return {
        "token":          "mUSDL",
        "network":        "Base Sepolia",
        "chain_id":       84532,
        "amount":         FAUCET_AMOUNT,
        "cooldown_hours": 24,
        "token_address":  MUSDL_ADDRESS or "not configured",
        "gasless":        bool(PRIVATE_KEY and MUSDL_ADDRESS),
    }
