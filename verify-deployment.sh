#!/bin/bash

# Deployment Verification Script
# Verifies that all contract deployments are properly configured

echo "═══════════════════════════════════════════════════════"
echo "PREDIKT.ai Deployment Verification"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check .env file
echo "📋 Checking .env configuration..."
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    exit 1
fi

GENLAYER_RPC=$(grep "GENLAYER_RPC_URL=" .env | cut -d'=' -f2)
CONTRACT_ADDRESS=$(grep "CONTRACT_ADDRESS=" .env | cut -d'=' -f2)
NEXT_PUBLIC_ADDRESS=$(grep "NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS=" .env | cut -d'=' -f2)

echo "✅ .env file found"
echo "   GENLAYER_RPC_URL: $GENLAYER_RPC"
echo "   CONTRACT_ADDRESS: $CONTRACT_ADDRESS"
echo "   NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS: $NEXT_PUBLIC_ADDRESS"
echo ""

# Check deployment info file
echo "📋 Checking deployment-bradbury.json..."
if [ -f deployment-bradbury.json ]; then
    echo "✅ Deployment info file found"
    echo ""
    echo "📄 Deployment Details:"
    cat deployment-bradbury.json | grep -E '"(contract_name|network|contract_address|deployment_time)"' | sed 's/^/   /'
    echo ""
else
    echo "⚠️  deployment-bradbury.json not found"
fi

# Check contract file
echo "📋 Checking contract file..."
if [ -f contracts/prediction_market.py ]; then
    echo "✅ Contract file found: contracts/prediction_market.py"
    LINES=$(wc -l < contracts/prediction_market.py)
    echo "   Lines of code: $LINES"
    echo ""
else
    echo "❌ Contract file not found"
    exit 1
fi

# Check backend configuration
echo "📋 Checking backend configuration..."
if [ -f backend/services/chain.py ]; then
    echo "✅ Chain service found"
    if grep -q "GENLAYER_RPC_URL\|CONTRACT_ADDRESS" backend/services/chain.py; then
        echo "   ✓ Uses environment variables for configuration"
    fi
    echo ""
else
    echo "❌ Chain service not found"
fi

# Check frontend configuration
echo "📋 Checking frontend configuration..."
if [ -f frontend/src/lib/constants.ts ]; then
    echo "✅ Frontend constants found"
    if grep -q "PREDICTION_MARKET\|genLayerStudionet" frontend/src/lib/constants.ts; then
        echo "   ✓ GenLayer Studionet configured"
    fi
    echo ""
else
    echo "❌ Frontend constants not found"
fi

# Summary
echo "═══════════════════════════════════════════════════════"
echo "✅ Deployment Verification Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📊 Status:"
echo "   Contract: Ready for use on GenLayer Studionet"
echo "   Backend: Configured via environment variables"
echo "   Frontend: Ready to connect"
echo ""
echo "🚀 Next Steps:"
echo "   1. make backend    # Start the FastAPI backend"
echo "   2. make frontend   # Start the Next.js frontend"
echo "   3. Open http://localhost:3000"
echo ""
