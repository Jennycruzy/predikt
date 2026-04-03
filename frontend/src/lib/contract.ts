/**
 * Contract interaction helpers.
 * Follows pm-kit's reads.ts / writes.ts pattern for clean separation.
 *
 * In production, these use wagmi/viem hooks.
 * For the demo dashboard, they provide the interface contracts.
 */

import { CONTRACTS, TOKEN_CONFIG } from "./constants";

// ═══════════════════════════════════════════════════════
// ABI Fragments (minimal for frontend interaction)
// ═══════════════════════════════════════════════════════

export const MOCK_USDL_ABI = [
  "function balanceOf(address) view returns (uint256)",
  "function allowance(address,address) view returns (uint256)",
  "function approve(address,uint256) returns (bool)",
  "function faucet() external",
  "function faucetCooldownRemaining(address) view returns (uint256)",
  "function totalSupply() view returns (uint256)",
  "event FaucetClaimed(address indexed user, uint256 amount)",
] as const;

export const BET_FACTORY_ABI = [
  "function createMarket(string,string,uint256,uint8) returns (uint256,address)",
  "function processResolution(uint256,bool,uint256,uint256,string)",
  "function getMarketAddress(uint256) view returns (address)",
  "function getMarketCount() view returns (uint256)",
  "function platformFee() view returns (uint256)",
  "event MarketCreated(uint256 indexed marketId, address indexed marketAddress, string question, string category, uint256 endDate)",
  "event ResolutionProcessed(uint256 indexed marketId, bool resolvedYes, uint256 predikt, uint256 confidence)",
] as const;

export const BET_MARKET_ABI = [
  "function bet(uint8,uint256) external",
  "function requestResolution() external",
  "function claim() external",
  "function getMarketInfo() view returns (string,string,uint256,uint8,uint256,uint256,uint256,uint256,bool)",
  "function getUserPosition(address) view returns (uint256,uint256,bool)",
  "function getOdds() view returns (uint256,uint256)",
  "function getTotalPool() view returns (uint256)",
  "event BetPlaced(address indexed user, uint8 position, uint256 amount)",
  "event MarketResolved(bool resolvedYes, uint256 predikt, uint256 confidence)",
  "event Claimed(address indexed user, uint256 amount)",
] as const;

// ═══════════════════════════════════════════════════════
// Read Helpers
// ═══════════════════════════════════════════════════════

export interface MarketInfo {
  question: string;
  category: string;
  endDate: number;
  state: number;
  totalYes: bigint;
  totalNo: bigint;
  predikt: number;
  confidence: number;
  resolvedYes: boolean;
}

export interface UserPosition {
  yesStake: bigint;
  noStake: bigint;
  claimed: boolean;
}

/**
 * Parse market info from contract return tuple.
 */
export function parseMarketInfo(result: any[]): MarketInfo {
  return {
    question: result[0],
    category: result[1],
    endDate: Number(result[2]),
    state: Number(result[3]),
    totalYes: result[4],
    totalNo: result[5],
    predikt: Number(result[6]),
    confidence: Number(result[7]),
    resolvedYes: result[8],
  };
}

/**
 * Format token amount from wei to display value.
 */
export function formatTokenAmount(wei: bigint, decimals = 18): string {
  const value = Number(wei) / 10 ** decimals;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toFixed(2);
}

/**
 * Parse token amount from display value to wei.
 */
export function parseTokenAmount(amount: number, decimals = 18): bigint {
  return BigInt(Math.floor(amount * 10 ** decimals));
}

// ═══════════════════════════════════════════════════════
// Write Helpers (transaction builders)
// ═══════════════════════════════════════════════════════

/**
 * Build approve transaction for betting.
 */
export function buildApproveArgs(spender: string, amount: bigint) {
  return {
    address: CONTRACTS.MOCK_USDL as `0x${string}`,
    abi: MOCK_USDL_ABI,
    functionName: "approve",
    args: [spender, amount],
  };
}

/**
 * Build bet transaction.
 */
export function buildBetArgs(
  marketAddress: string,
  position: 0 | 1, // 0=YES, 1=NO
  amount: bigint
) {
  return {
    address: marketAddress as `0x${string}`,
    abi: BET_MARKET_ABI,
    functionName: "bet",
    args: [position, amount],
  };
}

/**
 * Build claim transaction.
 */
export function buildClaimArgs(marketAddress: string) {
  return {
    address: marketAddress as `0x${string}`,
    abi: BET_MARKET_ABI,
    functionName: "claim",
  };
}

/**
 * Build faucet claim transaction.
 */
export function buildFaucetArgs() {
  return {
    address: CONTRACTS.MOCK_USDL as `0x${string}`,
    abi: MOCK_USDL_ABI,
    functionName: "faucet",
  };
}
