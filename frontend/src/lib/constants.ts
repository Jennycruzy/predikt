/**
 * predikt — Constants & Configuration
 *
 * Chain config, contract addresses, validator definitions,
 * and token configuration.
 */

// ═══════════════════════════════════════════════════════
// Chain Configuration
// ═══════════════════════════════════════════════════════

export const CHAINS = {
  baseSepolia: {
    id: 84532,
    name: "Base Sepolia",
    rpcUrl: "https://sepolia.base.org",
    blockExplorer: "https://sepolia.basescan.org",
  },
  genLayerStudionet: {
    name: "GenLayer Studionet",
    rpcUrl: "https://studio.genlayer.com/api",
    studioUrl: "https://studio.genlayer.com",
  },
};

// ═══════════════════════════════════════════════════════
// Contract Addresses (set after deployment)
// ═══════════════════════════════════════════════════════

export const CONTRACTS = {
  MOCK_USDL: process.env.NEXT_PUBLIC_MOCK_USDL_ADDRESS || "",
  BET_FACTORY: process.env.NEXT_PUBLIC_BET_FACTORY_ADDRESS || "",
  PREDICTION_MARKET: process.env.NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS || "0x9e1a258598b8a698c20d1a5621c86f1733a8e2e7fb069b230c191f2b28e4ba49",
};

// ═══════════════════════════════════════════════════════
// Mock Token Config
// ═══════════════════════════════════════════════════════

export const TOKEN_CONFIG = {
  name: "Mock USDL",
  symbol: "mUSDL",
  decimals: 18,
  faucetAmount: 1000,          // Tokens per faucet claim
  faucetCooldown: 86400,       // 24 hours between claims
  initialBalance: 10000,       // Starting balance for new users (demo)
};

// ═══════════════════════════════════════════════════════
// AI Validator Definitions
// ═══════════════════════════════════════════════════════

export const VALIDATORS = [
  {
    model: "gpt-4o",
    color: "#00D4AA",
    icon: "◆",
    style: "Analytical",
    description: "Quantitative, data-driven approach with statistical emphasis",
  },
  {
    model: "claude-sonnet",
    color: "#FF6B35",
    icon: "●",
    style: "Nuanced",
    description: "Balanced analysis with epistemic humility and caveats",
  },
  {
    model: "gemini-pro",
    color: "#4ECDC4",
    icon: "▲",
    style: "Optimistic",
    description: "Momentum-driven, trend-following forward outlook",
  },
  {
    model: "llama-3",
    color: "#FF3366",
    icon: "■",
    style: "Contrarian",
    description: "Skeptical, base-rate focused with historical corrections",
  },
  {
    model: "mistral-large",
    color: "#A855F7",
    icon: "◈",
    style: "Pragmatic",
    description: "Precedent-based institutional dynamics analysis",
  },
];

// ═══════════════════════════════════════════════════════
// Market Categories
// ═══════════════════════════════════════════════════════

export const CATEGORIES = [
  { id: "technology", label: "Technology", icon: "⚡" },
  { id: "finance", label: "Finance", icon: "◊" },
  { id: "science", label: "Science", icon: "◎" },
  { id: "politics", label: "Politics", icon: "☆" },
  { id: "crypto", label: "Crypto", icon: "₿" },
  { id: "sports", label: "Sports", icon: "◉" },
  { id: "general", label: "General", icon: "○" },
];

// ═══════════════════════════════════════════════════════
// Market Resolution Types (from pm-kit pattern)
// ═══════════════════════════════════════════════════════

export const RESOLUTION_TYPES = {
  CRYPTO: 0,    // Price-based (CoinMarketCap)
  STOCKS: 1,    // Stock price (Yahoo Finance)
  NEWS: 2,      // Event-based (AI validator predikt)
  AI_DEBATE: 3, // Our custom type: AI reasoning predikt
};

// ═══════════════════════════════════════════════════════
// Market States (from pm-kit BetCOFI pattern)
// ═══════════════════════════════════════════════════════

export const MARKET_STATES = {
  ACTIVE: "active",
  DEBATING: "debating",
  RESOLVING: "resolving",
  RESOLVED: "resolved",
  UNDETERMINED: "undetermined",
  CANCELLED: "cancelled",
};

// ═══════════════════════════════════════════════════════
// Staking Config
// ═══════════════════════════════════════════════════════

export const STAKING_CONFIG = {
  minStake: 10,                // Minimum mUSDL to stake on a position
  maxStake: 10000,             // Maximum per position
  platformFee: 2,              // 2% platform fee on winnings
  resolutionTimeout: 604800,   // 7 days — allows cancellation if oracle fails
};

// ═══════════════════════════════════════════════════════
// UI Constants
// ═══════════════════════════════════════════════════════

export const STATUS_COLORS = {
  active: "#00D4AA",
  open: "#00D4AA",
  debating: "#FFB800",
  resolving: "#FF6B35",
  resolved: "#A855F7",
  finalized: "#A855F7",
  undetermined: "#666",
  cancelled: "#FF3366",
};

// API calls go through Next.js rewrite proxy at /api/* — see next.config.js
export const API_BASE_URL = "/api";
