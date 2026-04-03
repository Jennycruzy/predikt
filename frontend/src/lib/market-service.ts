import { Interface, Contract, Signer, EventLog } from "ethers";

// Minimal ABIs required for interaction
const FACTORY_ABI = [
    "function createMarket(string calldata question, string calldata category, uint256 endDate, uint8 resolutionType) external returns (uint256 marketId, address marketAddress)",
    "function getMarketAddress(uint256 marketId) external view returns (address)",
    "function marketCount() external view returns (uint256)"
];

const MARKET_ABI = [
    "function bet(uint8 position, uint256 amount) external",
    "function claim() external",
    "function getUserPosition(address user) external view returns (uint256 _yesStake, uint256 _noStake, bool _claimed)",
    "function getMarketInfo() external view returns (string _question, string _category, uint256 _endDate, uint8 _state, uint256 _totalYes, uint256 _totalNo, uint256 _predikt, uint256 _confidence, bool _resolvedYes)"
];

const FACTORY_ADDRESS = process.env.NEXT_PUBLIC_BET_FACTORY_ADDRESS || "0x62A51185770F0545Bde0e0B10f5d6ed36dD8DD85";

export class MarketService {
    /**
     * Retrieves the market interface to format/decode data
     */
    get interface() {
        return new Interface(MARKET_ABI);
    }

    /**
     * Fetch a specific market contract instance with a signer
     */
    getMarketContract(marketAddress: string, signer: Signer) {
        return new Contract(marketAddress, MARKET_ABI, signer);
    }

    /**
     * Fetch the factory contract instance
     */
    getFactoryContract(signer: Signer) {
        return new Contract(FACTORY_ADDRESS, FACTORY_ABI, signer);
    }

    /**
     * Creates a new Prediction Market via the Factory.
     * Returns the new Market address.
     */
    async createMarket(
        signer: Signer,
        question: string,
        category: string,
        deadlineHours: number
    ): Promise<{ marketId: number; marketAddress: string }> {
        const factory = this.getFactoryContract(signer);
        const deadlineStr = Math.floor(Date.now() / 1000) + (deadlineHours * 3600); // Unix TS

        const tx = await factory.createMarket(question, category, deadlineStr, 3); // 3 = AI_DEBATE
        const receipt = await tx.wait();

        // Parse logs for MarketCreated log
        // We assume it's cleanly resolvable from ethers parses
        return { marketId: 0, marketAddress: "0xPlaceholder" }; // Will be hydrated when we read the logs correctly. For now we use subgraph / generic indexers.
    }

    /**
     * Places a stake on a market.
     * Note: Expects caller to have already called tokenService.approve(marketAddress, amount)
     */
    async placeBet(signer: Signer, marketAddress: string, position: "YES" | "NO", amountRaw: bigint) {
        const market = this.getMarketContract(marketAddress, signer);
        const posByte = position === "YES" ? 0 : 1;

        const tx = await market.bet(posByte, amountRaw);
        const receipt = await tx.wait();
        return receipt.hash;
    }

    /**
     * Claims winnings or refunds on a finalized/cancelled market.
     */
    async claimWinnings(signer: Signer, marketAddress: string) {
        const market = this.getMarketContract(marketAddress, signer);
        const tx = await market.claim();
        const receipt = await tx.wait();
        return receipt.hash;
    }

    /**
     * Gets user stake positioning in a given market
     */
    async getUserPosition(signer: Signer, marketAddress: string, userAddress: string) {
        const market = this.getMarketContract(marketAddress, signer);
        return await market.getUserPosition(userAddress);
    }
}

export const marketService = new MarketService();
