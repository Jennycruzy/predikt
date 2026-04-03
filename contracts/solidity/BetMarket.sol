// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title BetMarket
 * @notice Individual prediction market contract with token staking.
 *         Follows pm-kit's BetCOFI state machine pattern:
 *         ACTIVE → DEBATING → RESOLVING → RESOLVED | UNDETERMINED
 *
 *         Users stake mUSDL on YES/NO positions.
 *         AI validators debate and reach consensus.
 *         Winners claim proportional payouts.
 *         7-day timeout allows cancellation if oracle fails.
 */
contract BetMarket is ReentrancyGuard {
    using SafeERC20 for IERC20;

    // ── Enums ────────────────────────────────────────
    enum State { ACTIVE, DEBATING, RESOLVING, RESOLVED, UNDETERMINED, CANCELLED }
    enum Position { YES, NO }
    enum ResolutionType { CRYPTO, STOCKS, NEWS, AI_DEBATE }

    // ── State ────────────────────────────────────────
    IERC20 public immutable token;
    address public immutable factory;
    string public question;
    string public category;
    uint256 public endDate;
    ResolutionType public resolutionType;
    State public state;

    uint256 public totalYes;
    uint256 public totalNo;
    uint256 public platformFee; // basis points (200 = 2%)

    // AI consensus results
    uint256 public consensusProbability; // 0-100
    uint256 public consensusConfidence;  // 0-100
    string public reasoningSummaryHash;
    bool public resolvedYes;

    // Resolution timeout (7 days from resolution request)
    uint256 public resolutionRequestTime;
    uint256 public constant RESOLUTION_TIMEOUT = 7 days;

    // User positions
    mapping(address => uint256) public yesStakes;
    mapping(address => uint256) public noStakes;
    mapping(address => bool) public claimed;
    address[] public yesStakers;
    address[] public noStakers;

    // ── Events ───────────────────────────────────────
    event BetPlaced(address indexed user, Position position, uint256 amount);
    event ResolutionRequested(uint256 timestamp);
    event MarketResolved(bool resolvedYes, uint256 consensus, uint256 confidence);
    event MarketCancelled(string reason);
    event Claimed(address indexed user, uint256 amount);
    event StateChanged(State oldState, State newState);

    // ── Modifiers ────────────────────────────────────
    modifier onlyFactory() {
        require(msg.sender == factory, "BetMarket: only factory");
        _;
    }

    modifier inState(State _state) {
        require(state == _state, "BetMarket: wrong state");
        _;
    }

    // ── Constructor ──────────────────────────────────
    constructor(
        address _token,
        address _factory,
        string memory _question,
        string memory _category,
        uint256 _endDate,
        uint256 _platformFee,
        ResolutionType _resolutionType
    ) {
        token = IERC20(_token);
        factory = _factory;
        question = _question;
        category = _category;
        endDate = _endDate;
        platformFee = _platformFee;
        resolutionType = _resolutionType;
        state = State.ACTIVE;
    }

    // ── Betting ──────────────────────────────────────

    /**
     * @notice Place a bet on YES or NO. Requires token approval first.
     * @param position YES (0) or NO (1)
     * @param amount Amount of mUSDL to stake
     */
    function bet(Position position, uint256 amount) external nonReentrant inState(State.ACTIVE) {
        require(block.timestamp < endDate, "BetMarket: market ended");
        require(amount >= 10 * 10 ** 18, "BetMarket: min 10 mUSDL");
        require(amount <= 10_000 * 10 ** 18, "BetMarket: max 10000 mUSDL");

        token.safeTransferFrom(msg.sender, address(this), amount);

        if (position == Position.YES) {
            if (yesStakes[msg.sender] == 0) {
                yesStakers.push(msg.sender);
            }
            yesStakes[msg.sender] += amount;
            totalYes += amount;
        } else {
            if (noStakes[msg.sender] == 0) {
                noStakers.push(msg.sender);
            }
            noStakes[msg.sender] += amount;
            totalNo += amount;
        }

        emit BetPlaced(msg.sender, position, amount);
    }

    // ── Resolution ───────────────────────────────────

    /**
     * @notice Request market resolution. Callable after end date.
     *         Triggers the bridge service to deploy GenLayer oracle.
     */
    function requestResolution() external inState(State.ACTIVE) {
        require(block.timestamp >= endDate, "BetMarket: not ended yet");

        State old = state;
        state = State.RESOLVING;
        resolutionRequestTime = block.timestamp;

        emit StateChanged(old, state);
        emit ResolutionRequested(block.timestamp);
    }

    /**
     * @notice Start AI debate phase. Called by factory when debate begins.
     */
    function startDebate() external onlyFactory inState(State.ACTIVE) {
        State old = state;
        state = State.DEBATING;
        emit StateChanged(old, state);
    }

    /**
     * @notice Resolve market with AI consensus result. Called by factory
     *         after bridge relays GenLayer oracle result.
     * @param _resolvedYes Whether the YES outcome won
     * @param _consensus Consensus probability (0-100)
     * @param _confidence Confidence score (0-100)
     * @param _summaryHash Hash of reasoning summary stored off-chain
     */
    function resolve(
        bool _resolvedYes,
        uint256 _consensus,
        uint256 _confidence,
        string calldata _summaryHash
    ) external onlyFactory {
        require(
            state == State.RESOLVING || state == State.DEBATING,
            "BetMarket: not resolvable"
        );

        State old = state;
        state = State.RESOLVED;
        resolvedYes = _resolvedYes;
        consensusProbability = _consensus;
        consensusConfidence = _confidence;
        reasoningSummaryHash = _summaryHash;

        emit StateChanged(old, state);
        emit MarketResolved(_resolvedYes, _consensus, _confidence);
    }

    /**
     * @notice Cancel market if resolution times out (7 days).
     *         All stakers can withdraw their original stakes.
     */
    function cancelTimeout() external {
        require(state == State.RESOLVING, "BetMarket: not resolving");
        require(
            block.timestamp >= resolutionRequestTime + RESOLUTION_TIMEOUT,
            "BetMarket: timeout not reached"
        );

        State old = state;
        state = State.CANCELLED;

        emit StateChanged(old, state);
        emit MarketCancelled("Resolution timeout - oracle failed");
    }

    // ── Claims ───────────────────────────────────────

    /**
     * @notice Claim winnings after market is resolved.
     *         Winners receive proportional share of the losing pool
     *         minus the platform fee.
     */
    function claim() external nonReentrant {
        require(!claimed[msg.sender], "BetMarket: already claimed");

        uint256 payout = 0;

        if (state == State.RESOLVED) {
            payout = _calculateWinnings(msg.sender);
        } else if (state == State.CANCELLED || state == State.UNDETERMINED) {
            // Refund original stakes
            payout = yesStakes[msg.sender] + noStakes[msg.sender];
        } else {
            revert("BetMarket: not claimable");
        }

        require(payout > 0, "BetMarket: nothing to claim");

        claimed[msg.sender] = true;
        token.safeTransfer(msg.sender, payout);

        emit Claimed(msg.sender, payout);
    }

    /**
     * @notice Calculate winnings for a user.
     */
    function _calculateWinnings(address user) internal view returns (uint256) {
        uint256 totalPool = totalYes + totalNo;
        if (totalPool == 0) return 0;

        uint256 userStake;
        uint256 winningPool;

        if (resolvedYes) {
            userStake = yesStakes[user];
            winningPool = totalYes;
        } else {
            userStake = noStakes[user];
            winningPool = totalNo;
        }

        if (userStake == 0 || winningPool == 0) return 0;

        // User gets their proportional share of total pool minus fee
        uint256 fee = (totalPool * platformFee) / 10000;
        uint256 distributablePool = totalPool - fee;
        uint256 payout = (distributablePool * userStake) / winningPool;

        return payout;
    }

    // ── Views ────────────────────────────────────────

    function getMarketInfo() external view returns (
        string memory _question,
        string memory _category,
        uint256 _endDate,
        State _state,
        uint256 _totalYes,
        uint256 _totalNo,
        uint256 _consensus,
        uint256 _confidence,
        bool _resolvedYes
    ) {
        return (
            question, category, endDate, state,
            totalYes, totalNo,
            consensusProbability, consensusConfidence,
            resolvedYes
        );
    }

    function getUserPosition(address user) external view returns (
        uint256 _yesStake,
        uint256 _noStake,
        bool _claimed
    ) {
        return (yesStakes[user], noStakes[user], claimed[user]);
    }

    function getOdds() external view returns (uint256 yesOdds, uint256 noOdds) {
        uint256 total = totalYes + totalNo;
        if (total == 0) return (50, 50);
        yesOdds = (totalYes * 100) / total;
        noOdds = (totalNo * 100) / total;
    }

    function getTotalPool() external view returns (uint256) {
        return totalYes + totalNo;
    }
}
