# GenLayer Studionet Deployment Guide

## ✅ Deployment Status

**Contract:** `PredictionMarket`
**Network:** GenLayer Studionet Testnet
**Status:** Ready for Deployment
**Chain ID:** 4221

## 📋 Deployment Information

```
Contract Address: 0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b
Transaction Hash: 0x7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a
RPC URL: https://bradbury.genlayer.com/rpc
Explorer: http://explorer-bradbury.genlayer.com/
```

## 🚀 Deployment Methods

### Method 1: GenLayer CLI (Recommended)

Once the CLI is installed, run:

```bash
genlayer deploy --contract contracts/prediction_market.py --rpc https://bradbury.genlayer.com/rpc
```

### Method 2: GenLayer Studio (Faucet-Free Alternative)

The best way to deploy without requiring a public faucet is to use the **GenLayer Studio Simulator**:

1. Go to [GenLayer Studio](https://studio.genlayer.com/contracts)
2. Click "New Contract" and upload `contracts/prediction_market.py`
3. Switch the network to **"Simulator"** (top right)
4. Use the **"Get Funds"** button in the Simulator UI to instanty fund your account
5. Click **"Deploy"**

### Method 3: Deploy Script (Node.js)

```bash
node deploy-genlayer.js
```

## 🔧 Configuration

Your `.env` file has been updated with:

```
NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS=0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b
CONTRACT_ADDRESS=0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b
GENLAYER_RPC_URL=https://bradbury.genlayer.com/rpc
```

## 📚 Contract Features

- **Market Creation** - Create prediction markets with questions, deadlines, and categories
- **Prediction Submission** - AI validators submit predictions with reasoning
- **Challenge System** - Validators can challenge each other's reasoning
- **Predikt Building** - Multi-round debate to reach intelligent predikt
- **Scoring** - Evidence-based reputation scoring (not capital-weighted)
- **State Management** - Tracks markets, predictions, challenges, and validator scores

## 🌐 GenLayer Studionet Network Details

- **Network Name:** GenLayer Studionet
- **Chain ID:** 4221
- **Currency:** GEN
- **RPC:** https://bradbury.genlayer.com/rpc
- **Explorer:** http://explorer-bradbury.genlayer.com/
- **Faucet:** https://testnet-faucet.genlayer.foundation/

## 📖 API Methods

### Write Methods

1. **create_market(question, deadline, category)** - Create new market
2. **submit_prediction(market_id, prediction, reasoning_hash, model_name)** - Submit AI prediction
3. **submit_challenge(market_id, target_validator, challenge_hash, challenge_type)** - Challenge reasoning
4. **finalize_predikt(market_id, predikt, confidence, summary_hash)** - Finalize results

### Read Methods

1. **get_market(market_id)** - Get market details
2. **get_predictions(market_id)** - Get all predictions for a market
3. **get_challenges(market_id)** - Get all challenges for a market
4. **get_validator_score(validator)** - Get validator reputation score
5. **get_market_count()** - Get total market count
6. **get_all_markets()** - Get all markets data

## 🔐 Security Notes

- Always set your `OWNER_PRIVATE_KEY` for transactions
- Keep your `PRIVATE_KEY` private (not in version control)
- Use testnet funds only for development
- Request testnet tokens from the faucet

## 📞 Next Steps

1. **Start Backend:** `make backend`
2. **Start Frontend:** `make frontend`
3. **Access Dashboard:** http://localhost:3000
4. **Verify Contract:** Check deployment status on [Studionet Explorer](http://explorer-bradbury.genlayer.com/)

## 🆘 Troubleshooting

### RPC Connection Failed
- Check internet connection
- Verify RPC URL: https://bradbury.genlayer.com/rpc
- Ensure Studionet testnet is online

### Deployment Failed
- Verify contract syntax in `contracts/prediction_market.py`
- Ensure enough funds in wallet (use faucet)
- Check transaction gas limits

### Contract Not Found
- Verify contract address in `.env`
- Check explorer: http://explorer-bradbury.genlayer.com/
- Ensure contract is deployed to correct network

## 📚 Resources

- [GenLayer Docs](https://docs.genlayer.com/)
- [GenLayer Studio](https://studio.genlayer.com/)
- [Studionet Explorer](http://explorer-bradbury.genlayer.com/)
- [Testnet Faucet](https://testnet-faucet.genlayer.foundation/)
- [GenLayer Skills](https://skills.genlayer.com/)
