require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config({ path: __dirname + "/../.env" });

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.22",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      viaIR: true,
    },
  },
  networks: {
    baseSepolia: {
      url: process.env.BASE_SEPOLIA_RPC_URL || "https://sepolia.base.org",
      accounts: (process.env.PRIVATE_KEY || process.env.OWNER_PRIVATE_KEY) ? [process.env.PRIVATE_KEY || process.env.OWNER_PRIVATE_KEY] : [],
      chainId: 84532,
    },
    base: {
      url: process.env.BASE_RPC_URL || "https://mainnet.base.org",
      accounts: (process.env.PRIVATE_KEY || process.env.OWNER_PRIVATE_KEY) ? [process.env.PRIVATE_KEY || process.env.OWNER_PRIVATE_KEY] : [],
      chainId: 8453,
    },
  },
  paths: {
    sources: "./solidity",
  },
  etherscan: {
    apiKey: {
      baseSepolia: process.env.BASESCAN_API_KEY || "",
      base: process.env.BASESCAN_API_KEY || "",
    },
  },
};
