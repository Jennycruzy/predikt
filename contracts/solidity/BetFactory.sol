// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./BetMarket.sol";

/**
 * @title BetFactory
 * @notice Factory contract that deploys BetMarket instances and routes
 *         oracle resolution results. Follows pm-kit's BetFactoryCOFI pattern.
 *
 *         The bridge receiver calls processResolution() after GenLayer
 *         validators reach consensus, which forwards to the correct market.
 *
 * @dev Deploy on Base Sepolia with MockUSDL address as constructor arg.
 *      For production, use any ERC-20 token address.
 */
contract BetFactory is Ownable, ReentrancyGuard {
    // ── State ────────────────────────────────────────
    address public immutable bettingToken;
    address public bridgeReceiver; // LayerZero bridge endpoint

    uint256 public marketCount;
    uint256 public platformFee = 200; // 2% in basis points

    // Market registry
    mapping(uint256 => address) public markets;
    mapping(address => bool) public isMarket;

    // Fee collection
    uint256 public collectedFees;

    // ── Events ───────────────────────────────────────
    event MarketCreated(
        uint256 indexed marketId,
        address indexed marketAddress,
        string question,
        string category,
        uint256 endDate
    );
    event ResolutionProcessed(
        uint256 indexed marketId,
        bool resolvedYes,
        uint256 consensus,
        uint256 confidence
    );
    event BridgeReceiverSet(address indexed receiver);
    event PlatformFeeUpdated(uint256 newFee);
    event FeesWithdrawn(address indexed to, uint256 amount);

    // ── Constructor ──────────────────────────────────
    constructor(address _bettingToken) Ownable(msg.sender) {
        require(_bettingToken != address(0), "BetFactory: zero token");
        bettingToken = _bettingToken;
    }

    // ── Market Creation ──────────────────────────────

    /**
     * @notice Deploy a new prediction market.
     * @param question The prediction question
     * @param category Market category
     * @param endDate Unix timestamp when betting closes
     * @param resolutionType 0=CRYPTO, 1=STOCKS, 2=NEWS, 3=AI_DEBATE
     */
    function createMarket(
        string calldata question,
        string calldata category,
        uint256 endDate,
        BetMarket.ResolutionType resolutionType
    ) external returns (uint256 marketId, address marketAddress) {
        require(endDate > block.timestamp, "BetFactory: end date in past");
        require(bytes(question).length >= 10, "BetFactory: question too short");

        marketId = marketCount++;

        BetMarket market = new BetMarket(
            bettingToken,
            address(this),
            question,
            category,
            endDate,
            platformFee,
            resolutionType
        );

        marketAddress = address(market);
        markets[marketId] = marketAddress;
        isMarket[marketAddress] = true;

        emit MarketCreated(marketId, marketAddress, question, category, endDate);
    }

    // ── Resolution Processing ────────────────────────

    /**
     * @notice Process resolution result from the bridge.
     *         Called by bridgeReceiver after GenLayer validators reach consensus.
     * @param marketId Target market ID
     * @param resolvedYes Whether YES outcome won
     * @param consensus Consensus probability (0-100)
     * @param confidence Confidence score (0-100)
     * @param summaryHash Off-chain reasoning summary hash
     */
    function processResolution(
        uint256 marketId,
        bool resolvedYes,
        uint256 consensus,
        uint256 confidence,
        string calldata summaryHash
    ) external {
        require(
            msg.sender == bridgeReceiver || msg.sender == owner(),
            "BetFactory: unauthorized resolver"
        );
        require(markets[marketId] != address(0), "BetFactory: market not found");

        BetMarket market = BetMarket(markets[marketId]);
        market.resolve(resolvedYes, consensus, confidence, summaryHash);

        emit ResolutionProcessed(marketId, resolvedYes, consensus, confidence);
    }

    /**
     * @notice Start debate phase for a market.
     */
    function startDebate(uint256 marketId) external onlyOwner {
        require(markets[marketId] != address(0), "BetFactory: market not found");
        BetMarket(markets[marketId]).startDebate();
    }

    // ── Configuration ────────────────────────────────

    /**
     * @notice Set the bridge receiver address. Required for cross-chain resolution.
     */
    function setBridgeReceiver(address _receiver) external onlyOwner {
        require(_receiver != address(0), "BetFactory: zero address");
        bridgeReceiver = _receiver;
        emit BridgeReceiverSet(_receiver);
    }

    /**
     * @notice Update platform fee (in basis points, max 5%).
     */
    function setPlatformFee(uint256 _fee) external onlyOwner {
        require(_fee <= 500, "BetFactory: fee too high (max 5%)");
        platformFee = _fee;
        emit PlatformFeeUpdated(_fee);
    }

    /**
     * @notice Withdraw collected platform fees.
     */
    function withdrawFees(address to) external onlyOwner nonReentrant {
        uint256 amount = collectedFees;
        require(amount > 0, "BetFactory: no fees");
        collectedFees = 0;
        IERC20(bettingToken).transfer(to, amount);
        emit FeesWithdrawn(to, amount);
    }

    // ── Views ────────────────────────────────────────

    function getMarketAddress(uint256 marketId) external view returns (address) {
        return markets[marketId];
    }

    function getMarketCount() external view returns (uint256) {
        return marketCount;
    }
}
