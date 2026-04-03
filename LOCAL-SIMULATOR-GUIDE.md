# 🛠️ Faucet-Free Deployment Guide

If the GenLayer Studionet faucet is down or rate-limited, use the **GenLayer Studio Simulator** (Studionet) for development.

## 🚀 Using GenLayer Studio Simulator

### 1. Connect to Studio
Open [GenLayer Studio](https://studio.genlayer.com/contracts).

### 2. Get Simulator Funds
Unlike the public testnet, the Simulator (Studionet) has an internal funding mechanism:
1. Ensure the network (top right) is set to **"Simulator"**.
2. Go to the **"Simulator"** or **"Accounts"** tab.
3. Click the **"Get Funds"** button for any account. You will receive 100 GEN instantly.

### 3. Deploy via CLI
You can also deploy to the Studio Simulator using the CLI:

```bash
# 1. Set network to studionet
genlayer network set studionet

# 2. Deploy the contract
genlayer deploy --contract contracts/prediction_market.py
```

### 4. Update .env
Once deployed, use the Studio RPC and your new contract address:

```env
GENLAYER_RPC_URL=https://studio.genlayer.com/api
CONTRACT_ADDRESS=<YOUR_NEW_ADDRESS>
```

## 🏡 Running Localnet
If you have a local GenLayer node running at `http://localhost:4000/api`:

```bash
genlayer network set localnet
genlayer deploy --contract contracts/prediction_market.py
```
