/**
 * WalletConnect Component
 * UI for connecting/disconnecting wallet via RainbowKit
 */

"use client";

import { ConnectButton } from '@rainbow-me/rainbowkit';

export default function WalletConnect() {
  return <ConnectButton accountStatus="address" chainStatus="icon" />;
}
