"""
GenLayer Chain Service — Real Studionet Integration
Uses GenLayer JSON-RPC API over async HTTP (httpx).

GenLayer Studionet RPC: https://studio.genlayer.com/api
Methods:
  gen_call          — read or write to an intelligent contract
  gen_deployIntelligentContract — deploy Python contract code
  gen_getTransactionByHash      — poll for tx receipt
"""

import os
import json
import hashlib
import asyncio
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime
from web3 import Web3
try:
    from web3.middleware import ExtraDataToPOAMiddleware
except ImportError:
    from web3.middleware import geth_poa_middleware as ExtraDataToPOAMiddleware  # web3 6.x

# ── Configuration ─────────────────────────────────────────────────────────────

GENLAYER_RPC_URL  = os.getenv("GENLAYER_RPC_URL",  "https://studio.genlayer.com/api")
CONTRACT_ADDRESS  = os.getenv("CONTRACT_ADDRESS",  "")
OWNER_ADDRESS     = os.getenv("OWNER_ADDRESS",     "")
OWNER_PRIVATE_KEY = os.getenv("OWNER_PRIVATE_KEY", "")

BASE_SEPOLIA_RPC  = os.getenv("BASE_SEPOLIA_RPC_URL",
                    os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org"))
FACTORY_ADDRESS   = (os.getenv("NEXT_PUBLIC_BET_FACTORY_ADDRESS")
                     or os.getenv("BET_FACTORY_ADDRESS", ""))
PRIVATE_KEY       = os.getenv("OWNER_PRIVATE_KEY", "")

# Derive sender address from private key if not set explicitly
if not OWNER_ADDRESS and OWNER_PRIVATE_KEY:
    try:
        from eth_account import Account as EthAccount
        OWNER_ADDRESS = EthAccount.from_key(OWNER_PRIVATE_KEY).address
    except Exception:
        pass

DEFAULT_SENDER = OWNER_ADDRESS or "0x0000000000000000000000000000000000000001"

# ── ABIs ──────────────────────────────────────────────────────────────────────

FACTORY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "internalType": "uint256", "name": "marketId",      "type": "uint256"},
            {"indexed": True,  "internalType": "address", "name": "marketAddress", "type": "address"},
            {"indexed": False, "internalType": "string",  "name": "question",      "type": "string"},
            {"indexed": False, "internalType": "string",  "name": "category",      "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "endDate",       "type": "uint256"},
        ],
        "name": "MarketCreated",
        "type": "event",
    },
    {
        "inputs": [
            {"internalType": "string",  "name": "question",       "type": "string"},
            {"internalType": "string",  "name": "category",       "type": "string"},
            {"internalType": "uint256", "name": "endDate",        "type": "uint256"},
            {"internalType": "uint8",   "name": "resolutionType", "type": "uint8"},
        ],
        "name": "createMarket",
        "outputs": [
            {"internalType": "uint256", "name": "marketId",      "type": "uint256"},
            {"internalType": "address", "name": "marketAddress", "type": "address"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "marketId",    "type": "uint256"},
            {"internalType": "bool",    "name": "resolvedYes", "type": "bool"},
            {"internalType": "uint256", "name": "consensus",   "type": "uint256"},
            {"internalType": "uint256", "name": "confidence",  "type": "uint256"},
            {"internalType": "string",  "name": "summaryHash", "type": "string"},
        ],
        "name": "processResolution",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "marketId", "type": "uint256"}],
        "name": "startDebate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getMarketCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "markets",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

MARKET_ABI = [
    {
        "inputs": [],
        "name": "getMarketInfo",
        "outputs": [
            {"internalType": "string",  "name": "_question",   "type": "string"},
            {"internalType": "string",  "name": "_category",   "type": "string"},
            {"internalType": "uint256", "name": "_endDate",    "type": "uint256"},
            {"internalType": "uint8",   "name": "_state",      "type": "uint8"},
            {"internalType": "uint256", "name": "_totalYes",   "type": "uint256"},
            {"internalType": "uint256", "name": "_totalNo",    "type": "uint256"},
            {"internalType": "uint256", "name": "_consensus",  "type": "uint256"},
            {"internalType": "uint256", "name": "_confidence", "type": "uint256"},
            {"internalType": "bool",    "name": "_resolvedYes","type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "state",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ── GenLayer Client ───────────────────────────────────────────────────────────

class GenLayerClient:
    """
    Async client for GenLayer Studionet JSON-RPC API.
    Wraps the low-level RPC into typed methods that mirror the
    PredictionMarket intelligent contract interface.
    """

    def __init__(self, rpc_url: str, sender: str):
        self.rpc_url = rpc_url
        self.sender  = sender
        self._req_id = 0

    # ── Internal RPC helpers ──────────────────────────────────────────────────

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    async def _rpc(
        self,
        method: str,
        params: List[Any],
        timeout: int = 45,
    ) -> Any:
        import base64
        payload = {
            "jsonrpc": "2.0",
            "method":  method,
            "params":  params,
            "id":      self._next_id(),
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as http:
                resp = await http.post(
                    self.rpc_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    err = data["error"]
                    # GenLayer wraps execution errors in error.data.receipt
                    err_data = err.get("data", {})
                    if isinstance(err_data, dict) and "receipt" in err_data:
                        receipt = err_data["receipt"]
                        if receipt.get("execution_result") == "ERROR":
                            raw = receipt.get("result", "")
                            try:
                                msg = base64.b64decode(raw + "==").decode(errors="replace")
                            except Exception:
                                msg = raw
                            raise RuntimeError(f"GenLayer execution failed: {msg}")
                    raise RuntimeError(f"GenLayer RPC error: {err}")
                return data.get("result")
        except httpx.TimeoutException:
            raise TimeoutError(f"GenLayer RPC timed out ({method})")
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"GenLayer HTTP {exc.response.status_code}: {exc.response.text[:200]}")

    # ── Read (view) call ──────────────────────────────────────────────────────

    async def call_read(
        self,
        contract: str,
        function: str,
        args: List = [],
    ) -> Any:
        """Call a @gl.public.view function — no gas, immediate result."""
        import base64
        data_hex = "0x" + json.dumps({"function": function, "args": args}).encode().hex()
        result = await self._rpc("gen_call", [{
            "type": "read",
            "from": self.sender,
            "to":   contract,
            "data": data_hex,
        }])
        # Unwrap receipt envelope and base64-decode the return value
        if isinstance(result, dict):
            receipt = result.get("receipt", result)
            encoded = receipt.get("result", "")
            if encoded:
                try:
                    decoded_bytes = base64.b64decode(encoded + "==")
                    try:
                        return json.loads(decoded_bytes)
                    except (json.JSONDecodeError, ValueError):
                        return decoded_bytes.decode(errors="replace")
                except Exception:
                    pass
        return result

    # ── Write (transaction) ───────────────────────────────────────────────────

    async def send_transaction(
        self,
        contract: str,
        function: str,
        args: List = [],
        wait: bool = True,
        max_wait: int = 60,
    ) -> Optional[str]:
        """
        Submit a @gl.public.write transaction.
        Returns the tx hash; optionally polls until FINALIZED/ACCEPTED.
        """
        data_hex = "0x" + json.dumps({"function": function, "args": args}).encode().hex()
        result = await self._rpc("gen_call", [{
            "type": "write",
            "from": self.sender,
            "to":   contract,
            "data": data_hex,
        }], timeout=max_wait)

        # Extract tx hash — result may be a dict with "id" or a bare hash string
        if isinstance(result, dict):
            tx_hash = result.get("id") or result.get("hash") or result.get("tx_hash")
        else:
            tx_hash = str(result) if result else None

        if wait and tx_hash:
            await self._wait_for_receipt(tx_hash)
        return tx_hash

    async def _wait_for_receipt(
        self,
        tx_hash: str,
        max_attempts: int = 20,
        delay: float = 3.0,
    ) -> Optional[Dict]:
        """Poll gen_getTransactionByHash until the tx is settled."""
        for _ in range(max_attempts):
            try:
                receipt = await self._rpc("gen_getTransactionByHash", [tx_hash])
                if receipt:
                    status = receipt.get("status", "")
                    if status in ("FINALIZED", "ACCEPTED", "PENDING_FINALIZATION"):
                        return receipt
            except Exception:
                pass
            await asyncio.sleep(delay)
        return None

    # ── Contract deployment ───────────────────────────────────────────────────

    async def deploy_contract(
        self,
        code: str,
        args: List = [],
    ) -> Optional[str]:
        """
        Deploy an intelligent contract and return its address.
        Uses gen_call with type=deploy (Studionet format).
        """
        data_hex = "0x" + json.dumps({"code": code, "args": args}).encode().hex()
        result = await self._rpc("gen_call", [{
            "type": "deploy",
            "from": self.sender,
            "data": data_hex,
        }], timeout=120)
        if isinstance(result, dict):
            addr = (result.get("contract_address")
                    or result.get("to")
                    or result.get("address"))
            return str(addr) if addr else None
        return str(result) if result else None


# ── Chain Service ─────────────────────────────────────────────────────────────

class ChainService:
    """
    High-level service combining:
      - GenLayer Studionet (intelligent contract / AI resolution)
      - Base Sepolia (staking / payouts via BetFactory)
    """

    def __init__(self):
        self.rpc_url          = GENLAYER_RPC_URL
        self.contract_address = CONTRACT_ADDRESS
        self.gl               = GenLayerClient(GENLAYER_RPC_URL, DEFAULT_SENDER)
        self.is_live          = bool(CONTRACT_ADDRESS)

        # Base Sepolia Web3
        self.w3 = Web3(Web3.HTTPProvider(BASE_SEPOLIA_RPC))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.factory_address = FACTORY_ADDRESS
        self._base_account   = None
        if PRIVATE_KEY:
            try:
                self._base_account = self.w3.eth.account.from_key(PRIVATE_KEY)
            except Exception:
                pass

    @property
    def status(self) -> str:
        return "live" if self.is_live else "demo"

    # ── GenLayer: market lifecycle ────────────────────────────────────────────

    async def get_market_count_onchain(self) -> int:
        if not self.is_live:
            return 0
        try:
            result = await self.gl.call_read(self.contract_address, "get_market_count")
            return int(result) if result is not None else 0
        except Exception as exc:
            print(f"[GL] get_market_count failed: {exc}")
            return 0

    async def get_market_onchain(self, market_id: int) -> Optional[Dict]:
        if not self.is_live:
            return None
        try:
            result = await self.gl.call_read(
                self.contract_address, "get_market", [market_id]
            )
            return result if isinstance(result, dict) else None
        except Exception as exc:
            print(f"[GL] get_market({market_id}) failed: {exc}")
            return None

    async def get_all_markets_onchain(self) -> List[Dict]:
        if not self.is_live:
            return []
        count = await self.get_market_count_onchain()
        if count == 0:
            return []
        tasks = [self.get_market_onchain(i) for i in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict)]

    async def create_market_onchain(
        self,
        question: str,
        deadline: str,
        category: str,
    ) -> Optional[str]:
        """Register a new market on the GenLayer intelligent contract."""
        if not self.is_live:
            print(f"[GL:DEMO] create_market({question[:50]}…)")
            return None
        try:
            tx_hash = await self.gl.send_transaction(
                self.contract_address,
                "create_market",
                [question, deadline, category],
            )
            print(f"[GL] create_market tx: {tx_hash}")
            return tx_hash
        except Exception as exc:
            print(f"[GL] create_market failed: {exc}")
            return None

    async def submit_prediction_onchain(
        self,
        market_id: int,
        prediction: int,       # 0–100
        reasoning_hash: str,
        model_name: str,
    ) -> Optional[str]:
        if not self.is_live:
            return None
        try:
            tx_hash = await self.gl.send_transaction(
                self.contract_address,
                "submit_prediction",
                [market_id, prediction, reasoning_hash, model_name],
                wait=False,   # fire-and-forget during debate
            )
            print(f"[GL] submit_prediction({market_id}, {model_name}, {prediction}%) tx: {tx_hash}")
            return tx_hash
        except Exception as exc:
            print(f"[GL] submit_prediction failed: {exc}")
            return None

    async def submit_challenge_onchain(
        self,
        market_id: int,
        target_validator: str,
        challenge_hash: str,
        challenge_type: str,
    ) -> Optional[str]:
        if not self.is_live:
            return None
        try:
            tx_hash = await self.gl.send_transaction(
                self.contract_address,
                "submit_challenge",
                [market_id, target_validator, challenge_hash, challenge_type],
                wait=False,
            )
            return tx_hash
        except Exception as exc:
            print(f"[GL] submit_challenge failed: {exc}")
            return None

    async def resolve_market_onchain(
        self,
        market_id: int,
        resolution_url: str,
    ) -> Optional[str]:
        """
        Trigger the intelligent contract's AI resolution.
        The contract fetches live web data and runs LLM inference on-chain.
        """
        if not self.is_live:
            return None
        try:
            tx_hash = await self.gl.send_transaction(
                self.contract_address,
                "resolve_market",
                [market_id, resolution_url],
                wait=True,
                max_wait=120,  # AI resolution takes longer
            )
            print(f"[GL] resolve_market({market_id}) tx: {tx_hash}")
            return tx_hash
        except Exception as exc:
            print(f"[GL] resolve_market failed: {exc}")
            return None

    async def finalize_onchain(
        self,
        market_id: int,
        predikt: int,       # 0–100
        confidence: int,    # 0–100
        summary_hash: str,
    ) -> Optional[str]:
        """Manually finalize a market with the debate-computed predikt."""
        if not self.is_live:
            return None
        try:
            tx_hash = await self.gl.send_transaction(
                self.contract_address,
                "finalize_predikt",
                [market_id, predikt, confidence, summary_hash],
            )
            print(f"[GL] finalize_predikt({market_id}, {predikt}%) tx: {tx_hash}")
            return tx_hash
        except Exception as exc:
            print(f"[GL] finalize failed: {exc}")
            return None

    async def get_predictions_onchain(self, market_id: int) -> List[Dict]:
        if not self.is_live:
            return []
        try:
            result = await self.gl.call_read(
                self.contract_address, "get_predictions", [market_id]
            )
            return result if isinstance(result, list) else []
        except Exception as exc:
            print(f"[GL] get_predictions({market_id}) failed: {exc}")
            return []

    # ── Base Sepolia: staking contracts ───────────────────────────────────────

    async def get_all_markets_base_sepolia(self) -> List[Dict]:
        """Fetch markets from Base Sepolia BetFactory as fallback / stake data."""
        if not self.factory_address:
            return []
        print(f"[BASE] Fetching from BetFactory {self.factory_address}…")
        try:
            factory = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.factory_address),
                abi=FACTORY_ABI,
            )
            count = factory.functions.getMarketCount().call()
            print(f"[BASE] Found {count} markets on Base Sepolia.")

            markets = []
            for i in range(count - 1, -1, -1):
                try:
                    market_addr = factory.functions.markets(i).call()
                    market_contract = self.w3.eth.contract(
                        address=market_addr, abi=MARKET_ABI
                    )
                    info = market_contract.functions.getMarketInfo().call()
                    status_map = {0: "open", 1: "debating", 2: "resolving", 3: "finalized", 4: "undetermined", 5: "cancelled"}
                    status = status_map.get(info[3], "open")
                    markets.append({
                        "id":              i,
                        "question":        info[0],
                        "category":        info[1],
                        "deadline":        datetime.fromtimestamp(info[2]).isoformat(),
                        "status":          status,
                        "total_yes":       float(self.w3.from_wei(info[4], "ether")),
                        "total_no":        float(self.w3.from_wei(info[5], "ether")),
                        "predikt":         int(info[6]) if info[3] == 3 else -1,
                        "confidence":      int(info[7]) if info[3] == 3 else -1,
                        "resolved_yes":    info[8],
                        "validator_count": 5,
                        "source":          "base_sepolia",
                    })
                except Exception as exc:
                    print(f"[BASE] Market {i} read error: {exc}")
            return markets
        except Exception as exc:
            print(f"[BASE] Factory read failed: {exc}")
            return []

    async def create_market_base_sepolia(
        self,
        question: str,
        category: str,
        end_timestamp: int,
        resolution_type: int = 3,   # 3 = AI_DEBATE
    ) -> Optional[int]:
        """Deploy a new BetMarket on Base Sepolia and return its marketId."""
        if not self._base_account or not self.factory_address:
            print("[BASE] No account or factory — skipping Base Sepolia deploy.")
            return None
        try:
            factory = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.factory_address),
                abi=FACTORY_ABI,
            )
            tx = factory.functions.createMarket(
                question, category, end_timestamp, resolution_type
            ).build_transaction({
                "from":     self._base_account.address,
                "nonce":    self.w3.eth.get_transaction_count(self._base_account.address, "pending"),
                "gasPrice": int(self.w3.eth.gas_price * 1.2),
            })
            signed  = self.w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None))
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            # Parse MarketCreated event to get marketId
            for log in receipt.logs:
                try:
                    decoded = factory.events.MarketCreated().process_log(log)
                    market_id = decoded["args"]["marketId"]
                    print(f"[BASE] Market {market_id} deployed: {tx_hash.hex()}")
                    return int(market_id)
                except Exception:
                    continue
            print(f"[BASE] Market deployed (tx: {tx_hash.hex()}), could not parse ID")
            return None
        except Exception as exc:
            print(f"[BASE] create_market_base_sepolia failed: {exc}")
            return None

    async def resolve_on_base_sepolia(
        self,
        market_id: int,
        resolved_yes: bool,
        consensus: int,
        confidence: int,
        summary_hash: str = "",
    ) -> bool:
        """Bridge GenLayer resolution result to Base Sepolia BetFactory."""
        if not self._base_account or not self.factory_address:
            print("[BASE] No account — skipping resolution bridge.")
            return False
        try:
            factory = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.factory_address),
                abi=FACTORY_ABI,
            )
            # Check market state to avoid double-resolution
            market_addr = factory.functions.markets(market_id).call()
            market_contract = self.w3.eth.contract(address=market_addr, abi=MARKET_ABI)
            state = market_contract.functions.state().call()
            if state >= 3:
                print(f"[BASE] Market {market_id} already resolved.")
                return True

            tx = factory.functions.processResolution(
                market_id,
                resolved_yes,
                consensus,
                confidence,
                summary_hash or "predikt://summary",
            ).build_transaction({
                "from":     self._base_account.address,
                "nonce":    self.w3.eth.get_transaction_count(self._base_account.address, "pending"),
                "gasPrice": int(self.w3.eth.gas_price * 1.2),
            })
            signed  = self.w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None))
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"[BASE] Resolution bridged — Market {market_id}, YES={resolved_yes}, tx: {tx_hash.hex()}")
            return True
        except Exception as exc:
            print(f"[BASE] resolve_on_base_sepolia({market_id}) failed: {exc}")
            return False

    async def start_debate_base_sepolia(self, market_id: int) -> bool:
        """Transition market to DEBATING state on Base Sepolia."""
        if not self._base_account or not self.factory_address:
            return False
        try:
            factory = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.factory_address),
                abi=FACTORY_ABI,
            )
            tx = factory.functions.startDebate(market_id).build_transaction({
                "from":     self._base_account.address,
                "nonce":    self.w3.eth.get_transaction_count(self._base_account.address, "pending"),
                "gasPrice": int(self.w3.eth.gas_price * 1.2),
            })
            signed  = self.w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None))
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"[BASE] Debate started for market {market_id}")
            return True
        except Exception as exc:
            print(f"[BASE] startDebate({market_id}) failed: {exc}")
            return False


# ── Utilities ─────────────────────────────────────────────────────────────────

def hash_reasoning(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:32]


# ── Singleton ─────────────────────────────────────────────────────────────────

chain_service = ChainService()
