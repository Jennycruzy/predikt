# Privy Wallet Integration Setup

## 1️⃣ Get Privy API Credentials

1. Visit [Privy Dashboard](https://dashboard.privy.io/)
2. Sign up or log in
3. Create a new project
4. Copy your **App ID** and **Client ID**

## 2️⃣ Install Privy SDK

```bash
npm install @privy-io/react-auth
```

## 3️⃣ Add Environment Variables

Update your `.env.local`:

```bash
NEXT_PUBLIC_PRIVY_APP_ID=your_app_id_here
NEXT_PUBLIC_PRIVY_CLIENT_ID=your_client_id_here
```

## 4️⃣ Wrap App with PrivyProvider

Update `frontend/src/app/layout.tsx`:

```tsx
import { PrivyProvider } from "@privy-io/react-auth";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <PrivyProvider
          appId={process.env.NEXT_PUBLIC_PRIVY_APP_ID!}
          clientId={process.env.NEXT_PUBLIC_PRIVY_CLIENT_ID!}
        >
          {children}
        </PrivyProvider>
      </body>
    </html>
  );
}
```

## 5️⃣ Use WalletConnect Component

In your dashboard or header:

```tsx
import { WalletConnect } from "@/components/WalletConnect";

export default function Dashboard() {
  return (
    <div>
      <header>
        <WalletConnect />
      </header>
      {/* Rest of dashboard */}
    </div>
  );
}
```

## 6️⃣ Configure Supported Chains

Privy will auto-detect Base Sepolia. You can customize in `privy-config.ts`:

```typescript
export const SUPPORTED_CHAINS = [
  {
    id: 84532,
    name: "Base Sepolia",
    rpcUrl: "https://sepolia.base.org",
  },
  {
    id: 4221,
    name: "GenLayer Studionet",
    rpcUrl: "https://bradbury.genlayer.com/rpc",
  },
];
```

## ✅ Testing

1. Run frontend: `make frontend`
2. Click "Connect Wallet"
3. Follow Privy login flow
4. See connected address in UI
5. Switch between Base Sepolia and GenLayer Studionet

## 📚 Resources

- [Privy Docs](https://docs.privy.io/)
- [React Auth SDK](https://docs.privy.io/guide/react/authentication)
- [Wallet Integration](https://docs.privy.io/guide/react/wallets)
