/**
 * Privy Wallet Integration
 * Setup for web3 wallet connection on Base Sepolia
 *
 * Installation:
 * npm install @privy-io/react-auth
 */

export const PRIVY_CONFIG = {
  appId: process.env.NEXT_PUBLIC_PRIVY_APP_ID || "",
  clientId: process.env.NEXT_PUBLIC_PRIVY_CLIENT_ID || "",
};

// Supported chains
export const SUPPORTED_CHAINS = [
  {
    id: 84532,
    name: "Base Sepolia",
    rpcUrl: "https://sepolia.base.org",
    blockExplorer: "https://sepolia.basescan.org",
  },
  {
    id: 4221,
    name: "GenLayer Studionet",
    rpcUrl: "https://bradbury.genlayer.com/rpc",
    blockExplorer: "http://explorer-bradbury.genlayer.com/",
  },
];

/**
 * Privy Client Hook Configuration
 * Add this to your app/_app.tsx or root layout
 */
export const getPrivyConfig = () => {
  if (!PRIVY_CONFIG.appId) {
    console.warn(
      "Privy App ID not set. Set NEXT_PUBLIC_PRIVY_APP_ID in .env.local"
    );
  }

  return {
    appId: PRIVY_CONFIG.appId,
    clientId: PRIVY_CONFIG.clientId,
    chains: SUPPORTED_CHAINS,
  };
};
