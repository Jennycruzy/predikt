/**
 * Faucet Modal Component
 * 
 * Allows connected users to claim mock USDL directly on Base Sepolia
 */

'use client';

import { useContract } from "../hooks/useContract";
import { useAccount } from "wagmi";

interface FaucetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function FaucetModal({ isOpen, onClose }: FaucetModalProps) {
  const { claimFaucet, txPending, wallet } = useContract();
  const { isConnected, address } = useAccount();

  if (!isOpen) return null;

  const handleClaim = async () => {
    if (!isConnected) {
      alert("Please connect your wallet first.");
      return;
    }
    const result = await claimFaucet();
    if (result) {
      setTimeout(() => {
        onClose();
      }, 2000);
    }
  };

  const isCooldownActive = wallet.faucetCooldown > 0;
  const cooldownHours = Math.floor(wallet.faucetCooldown / 3600);
  const cooldownMinutes = Math.floor((wallet.faucetCooldown % 3600) / 60);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-lg p-8 max-w-md w-full mx-4 border border-cyan-500/30">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Mock USDL Faucet</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">×</button>
        </div>

        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 mb-6">
          <p className="text-sm text-gray-300">
            <span className="text-blue-400">💡 Tip:</span> Use mock USDL tokens to stake on Base Sepolia markets.
            <strong> 1000 mUSDL per claim</strong>, max <strong>1 claim per 24 hours</strong>.
          </p>
        </div>

        {isConnected ? (
          <div className="mb-6">
            <p className="text-sm text-gray-300 mb-2">Connected Account:</p>
            <p className="font-mono text-cyan-400 bg-gray-800 p-2 rounded truncate">{address}</p>
            <p className="text-sm text-gray-400 mt-2">Current Balance: <span className="text-white">{wallet.balance} mUSDL</span></p>
          </div>
        ) : (
          <div className="mb-6 bg-red-900/20 border border-red-500/30 rounded p-4">
            <p className="text-sm text-red-400">You must connect your wallet before claiming.</p>
          </div>
        )}

        <div className="flex gap-3 mt-8">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleClaim}
            disabled={txPending || !isConnected || isCooldownActive}
            className="flex-1 px-4 py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
          >
            {txPending ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Claiming...
              </>
            ) : isCooldownActive ? (
              `Wait ${cooldownHours}h ${cooldownMinutes}m`
            ) : (
              '💰 Claim 1,000 mUSDL'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
