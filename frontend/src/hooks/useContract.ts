/**
 * useContract Hook
 * Read calls: viem publicClient (HTTP)
 * Write calls: window.ethereum eth_sendTransaction directly
 *   — avoids ethers.js/viem tx-builder quirks with Rabby on custom networks
 */

import { useState, useCallback } from "react";
import { createPublicClient, http, parseUnits, formatUnits, encodeFunctionData } from "viem";
import { baseSepolia } from "viem/chains";
import { useAccount } from "wagmi";

const MOCK_USDL_ADDRESS = (process.env.NEXT_PUBLIC_MOCK_USDL_ADDRESS || "0x8f693B55dF716FE43A219b65BACE1027Fb09AFF0") as `0x${string}`;
const FACTORY_ADDRESS   = (process.env.NEXT_PUBLIC_BET_FACTORY_ADDRESS  || "0x62A51185770F0545Bde0e0B10f5d6ed36dD8DD85") as `0x${string}`;
const BASE_SEPOLIA_HEX  = "0x14A34";

const TOKEN_ABI = [
  { name: "balanceOf",  type: "function", stateMutability: "view",       inputs: [{ name: "owner",   type: "address" }],                                       outputs: [{ type: "uint256" }] },
  { name: "approve",    type: "function", stateMutability: "nonpayable",  inputs: [{ name: "spender", type: "address" }, { name: "amount", type: "uint256" }], outputs: [{ type: "bool"    }] },
] as const;

const FACTORY_ABI = [
  { name: "markets", type: "function", stateMutability: "view", inputs: [{ name: "id", type: "uint256" }], outputs: [{ type: "address" }] },
] as const;

const MARKET_ABI = [
  { name: "bet",             type: "function", stateMutability: "nonpayable", inputs: [{ name: "position", type: "uint8"    }, { name: "amount", type: "uint256" }], outputs: [] },
  { name: "claim",           type: "function", stateMutability: "nonpayable", inputs: [],                                                                            outputs: [] },
  { name: "getUserPosition", type: "function", stateMutability: "view",       inputs: [{ name: "user",     type: "address"  }],                                      outputs: [{ name: "_yesStake", type: "uint256" }, { name: "_noStake", type: "uint256" }, { name: "_claimed", type: "bool" }] },
] as const;

export interface UserPosition { yesStake: number; noStake: number; claimed: boolean; }

function getEth() {
  const eth = (window as any).ethereum;
  if (!eth) throw new Error("No wallet detected. Please install MetaMask or Rabby.");
  return eth;
}

function pc() {
  return createPublicClient({ chain: baseSepolia, transport: http("https://sepolia.base.org") });
}

async function ensureBaseSepolia() {
  const eth = getEth();
  const current: string = await eth.request({ method: "eth_chainId" });
  if (current.toLowerCase() === BASE_SEPOLIA_HEX.toLowerCase()) return;
  try {
    await eth.request({ method: "wallet_switchEthereumChain", params: [{ chainId: BASE_SEPOLIA_HEX }] });
  } catch (err: any) {
    if (err.code === 4902) {
      await eth.request({
        method: "wallet_addEthereumChain",
        params: [{ chainId: BASE_SEPOLIA_HEX, chainName: "Base Sepolia", nativeCurrency: { name: "ETH", symbol: "ETH", decimals: 18 }, rpcUrls: ["https://sepolia.base.org"], blockExplorerUrls: ["https://sepolia-explorer.base.org"] }],
      });
    } else throw err;
  }
}

/** Send a raw transaction via window.ethereum and wait for it to mine. */
async function sendAndWait(eth: any, from: string, to: string, data: string, gasHex: string): Promise<`0x${string}`> {
  const client = pc();
  // Get nonce and gas price from our HTTP RPC — not from Rabby's custom-network handler
  const [nonce, gasPrice] = await Promise.all([
    client.getTransactionCount({ address: from as `0x${string}`, blockTag: "pending" }),
    client.getGasPrice(),
  ]);

  const hash: `0x${string}` = await eth.request({
    method: "eth_sendTransaction",
    params: [{
      from,
      to,
      data,
      gas:      gasHex,
      gasPrice: "0x" + gasPrice.toString(16),
      nonce:    "0x" + nonce.toString(16),
    }],
  });

  // Poll for receipt
  for (let i = 0; i < 120; i++) {
    const receipt = await client.getTransactionReceipt({ hash }).catch(() => null);
    if (receipt) {
      if (receipt.status === "reverted") throw new Error("Transaction reverted on-chain");
      return hash;
    }
    await new Promise(r => setTimeout(r, 2500));
  }
  throw new Error("Transaction not mined after 5 min");
}

export function useContract() {
  const { address, isConnected } = useAccount();
  const [wallet,        setWallet      ] = useState({ balance: 0, faucetCooldown: 0 });
  const [userPosition,  setUserPosition] = useState<UserPosition | null>(null);
  const [txPending,     setTxPending   ] = useState(false);
  const [txHash,        setTxHash      ] = useState<string | null>(null);

  const refreshData = useCallback(async (marketId?: string | number) => {
    if (!isConnected || !address) return;
    try {
      const client = pc();
      const bal = await client.readContract({ address: MOCK_USDL_ADDRESS, abi: TOKEN_ABI, functionName: "balanceOf", args: [address as `0x${string}`] });
      setWallet(prev => ({ ...prev, balance: Math.floor(Number(formatUnits(bal as bigint, 18))) }));

      if (marketId !== undefined) {
        const mAddr = await client.readContract({ address: FACTORY_ADDRESS, abi: FACTORY_ABI, functionName: "markets", args: [BigInt(marketId)] }) as `0x${string}`;
        if (mAddr && mAddr !== "0x0000000000000000000000000000000000000000") {
          const pos = await client.readContract({ address: mAddr, abi: MARKET_ABI, functionName: "getUserPosition", args: [address as `0x${string}`] }) as [bigint, bigint, boolean];
          setUserPosition({ yesStake: Math.floor(Number(formatUnits(pos[0], 18))), noStake: Math.floor(Number(formatUnits(pos[1], 18))), claimed: pos[2] });
        }
      }
    } catch (err) { console.error("Data refresh error:", err); }
  }, [isConnected, address]);

  const claimFaucet = useCallback(async () => {
    if (!address) { alert("Connect your wallet first."); return false; }
    setTxPending(true);
    try {
      const res  = await fetch("/api/faucet/claim", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ wallet_address: address }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Faucet failed");
      setTxHash(data.transaction_hash);
      await refreshData();
      return true;
    } catch (err: any) { alert(`Faucet failed: ${err.message}`); return false; }
    finally { setTxPending(false); }
  }, [address, refreshData]);

  const placeBet = useCallback(async (mid: string | number, pos: "YES" | "NO", amt: number) => {
    if (!amt || amt <= 0) { alert("Enter a valid amount."); return false; }
    setTxPending(true);
    try {
      await ensureBaseSepolia();
      const eth    = getEth();
      const client = pc();

      const accounts: string[] = await eth.request({ method: "eth_accounts" });
      const from = accounts[0];
      if (!from) throw new Error("No wallet account found");

      const mAddr = await client.readContract({ address: FACTORY_ADDRESS, abi: FACTORY_ABI, functionName: "markets", args: [BigInt(mid)] }) as `0x${string}`;
      if (!mAddr || mAddr === "0x0000000000000000000000000000000000000000") {
        throw new Error(`Market ${mid} not found on Base Sepolia`);
      }

      const pAmt = parseUnits(amt.toString(), 18);

      // Step 1: Approve
      const approveData = encodeFunctionData({ abi: TOKEN_ABI, functionName: "approve", args: [mAddr, pAmt] });
      await sendAndWait(eth, from, MOCK_USDL_ADDRESS, approveData, "0x13880"); // 80 000

      // Step 2: Bet (0 = YES, 1 = NO)
      const betData = encodeFunctionData({ abi: MARKET_ABI, functionName: "bet", args: [pos === "YES" ? 0 : 1, pAmt] });
      const betHash = await sendAndWait(eth, from, mAddr, betData, "0x30D40"); // 200 000

      setTxHash(betHash);
      await refreshData(mid);
      return true;
    } catch (err: any) {
      alert(`Stake failed: ${err.message}`);
      return false;
    } finally { setTxPending(false); }
  }, [refreshData]);

  const claimWinnings = useCallback(async (mid: string | number) => {
    setTxPending(true);
    try {
      await ensureBaseSepolia();
      const eth    = getEth();
      const client = pc();

      const accounts: string[] = await eth.request({ method: "eth_accounts" });
      const from = accounts[0];
      if (!from) throw new Error("No wallet account found");

      const mAddr  = await client.readContract({ address: FACTORY_ADDRESS, abi: FACTORY_ABI, functionName: "markets", args: [BigInt(mid)] }) as `0x${string}`;
      const data   = encodeFunctionData({ abi: MARKET_ABI, functionName: "claim", args: [] });
      const hash   = await sendAndWait(eth, from, mAddr, data, "0x30D40");
      setTxHash(hash);
      await refreshData(mid);
      return true;
    } catch (err: any) { alert(`Claim failed: ${err.message}`); return false; }
    finally { setTxPending(false); }
  }, [refreshData]);

  return { wallet, userPosition, txPending, txHash, claimFaucet, placeBet, claimWinnings, refreshData };
}

export default useContract;
