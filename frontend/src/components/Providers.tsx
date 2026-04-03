'use client';

import { getDefaultConfig, RainbowKitProvider, darkTheme } from '@rainbow-me/rainbowkit';
import { WagmiProvider, http } from 'wagmi';
import { baseSepolia } from 'wagmi/chains';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import type { ReactNode } from 'react';

// Use a placeholder or environment variable for WalletConnect/Reown App ID
const projectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || 'ad48a1d1faeaae8f45c43d04d79d3be2';

const config = getDefaultConfig({
    appName: 'PREDIKT',
    projectId,
    chains: [baseSepolia],
    transports: {
        [baseSepolia.id]: http('https://sepolia.base.org'),
    },
    ssr: true, // If Next.js App Router
});

const queryClient = new QueryClient();

export default function Providers({ children }: { children: ReactNode }) {
    return (
        <WagmiProvider config={config}>
            <QueryClientProvider client={queryClient}>
                <RainbowKitProvider theme={darkTheme({ accentColor: '#0ea5e9' })}>
                    {children}
                </RainbowKitProvider>
            </QueryClientProvider>
        </WagmiProvider>
    );
}
