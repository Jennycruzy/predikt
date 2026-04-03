/**
 * ERC-20 Token Service
 * Handles balance queries and transfers for MockUSDL on Base Sepolia
 */

import { ethers } from "ethers";

// ABI for MockUSDL
const MOCK_USDL_ABI = [
  "function balanceOf(address account) view returns (uint256)",
  "function decimals() view returns (uint8)",
  "function name() view returns (string)",
  "function symbol() view returns (string)",
  "function totalSupply() view returns (uint256)",
  "function transfer(address to, uint256 amount) returns (bool)",
  "function faucet()",
  "function faucetCooldownRemaining(address user) view returns (uint256)",
  "function FAUCET_AMOUNT() view returns (uint256)"
];

const BASE_SEPOLIA_RPC = "https://sepolia.base.org";
const MOCK_USDL_ADDRESS = process.env.NEXT_PUBLIC_MOCK_USDL_ADDRESS || "";

export class TokenService {
  private provider: ethers.JsonRpcProvider;
  private tokenContract: ethers.Contract | null = null;

  constructor() {
    this.provider = new ethers.JsonRpcProvider(BASE_SEPOLIA_RPC);
    if (MOCK_USDL_ADDRESS) {
      this.tokenContract = new ethers.Contract(
        MOCK_USDL_ADDRESS,
        MOCK_USDL_ABI,
        this.provider
      );
    }
  }

  async getBalance(address: string): Promise<string> {
    if (!this.tokenContract) return "0";
    try {
      const balance = await this.tokenContract.balanceOf(address);
      return ethers.formatUnits(balance, 18); // hardcoded for 18 decimals
    } catch (error) {
      console.error("Error fetching balance:", error);
      return "0";
    }
  }

  async canClaim(address: string): Promise<boolean> {
    if (!this.tokenContract) return false;
    try {
      const cooldown = await this.tokenContract.faucetCooldownRemaining(address);
      return cooldown === 0n;
    } catch (error) {
      console.error("Error checking claim eligibility:", error);
      return false;
    }
  }

  async claimFromFaucet(signer: ethers.Signer): Promise<string> {
    if (!this.tokenContract) throw new Error("Contract not connected");
    const contractWithSigner = this.tokenContract.connect(signer);
    const tx = await contractWithSigner.faucet();
    const receipt = await tx.wait();
    return receipt.hash;
  }
}

export const tokenService = new TokenService();
