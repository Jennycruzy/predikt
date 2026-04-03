// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MockUSDL
 * @notice Testnet ERC-20 betting token with rate-limited faucet.
 *         Inspired by courtofinternet/pm-kit's MockUSDL pattern.
 *         Users claim tokens via the faucet to stake on prediction markets.
 *
 * @dev Deploy on Base Sepolia. For production, replace with any ERC-20
 *      by passing its address to the BetFactory constructor.
 */
contract MockUSDL is ERC20, Ownable {
    uint256 public constant FAUCET_AMOUNT = 1_000 * 10 ** 18;    // 1000 mUSDL per claim
    uint256 public constant FAUCET_COOLDOWN = 24 hours;
    uint256 public constant MAX_SUPPLY = 100_000_000 * 10 ** 18; // 100M cap

    mapping(address => uint256) public lastFaucetClaim;

    event FaucetClaimed(address indexed user, uint256 amount);
    event TokensMinted(address indexed to, uint256 amount);

    constructor() ERC20("Mock USDL", "mUSDL") Ownable(msg.sender) {
        // Mint initial supply to deployer for liquidity seeding
        _mint(msg.sender, 1_000_000 * 10 ** 18);
    }

    /**
     * @notice Claim free testnet tokens. Rate-limited to once per 24 hours.
     */
    function faucet() external {
        require(
            block.timestamp >= lastFaucetClaim[msg.sender] + FAUCET_COOLDOWN,
            "MockUSDL: faucet cooldown active"
        );
        require(
            totalSupply() + FAUCET_AMOUNT <= MAX_SUPPLY,
            "MockUSDL: max supply reached"
        );

        lastFaucetClaim[msg.sender] = block.timestamp;
        _mint(msg.sender, FAUCET_AMOUNT);

        emit FaucetClaimed(msg.sender, FAUCET_AMOUNT);
    }

    /**
     * @notice Check remaining cooldown for an address.
     * @return Seconds until next claim is available (0 = ready)
     */
    function faucetCooldownRemaining(address user) external view returns (uint256) {
        uint256 nextClaim = lastFaucetClaim[user] + FAUCET_COOLDOWN;
        if (block.timestamp >= nextClaim) return 0;
        return nextClaim - block.timestamp;
    }

    /**
     * @notice Owner can mint tokens to any address (for airdrops, rewards).
     */
    function mint(address to, uint256 amount) external onlyOwner {
        require(totalSupply() + amount <= MAX_SUPPLY, "MockUSDL: max supply reached");
        _mint(to, amount);
        emit TokensMinted(to, amount);
    }
}
