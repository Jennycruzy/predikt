#!/bin/bash

# PREDIKT.ai - Quick Setup Script
# Installs all dependencies and provides next steps

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       PREDIKT.ai - Complete Setup & Installation             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Please run this script from the predikt directory"
    exit 1
fi

echo "${BLUE}📦 Installing Python dependencies...${NC}"
cd backend
python3 -m pip install -q sqlalchemy psycopg2-binary openai anthropic google-generativeai
cd ..

echo "${GREEN}✅ Python dependencies installed${NC}"
echo ""

echo "${BLUE}📦 Installing Node dependencies...${NC}"
cd frontend
npm install -q
cd ..

echo "${GREEN}✅ Node dependencies installed${NC}"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating template .env file..."
    cat > .env.template << 'EOF'
# ═══════════════════════════════════════════════════════
# PREDIKT.ai Environment Variables
# ═══════════════════════════════════════════════════════

# ── Contract Deployment ──────────────────────────────
PRIVATE_KEY=
BASESCAN_API_KEY=
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org

# ── Contract Addresses ────────────────────────────────
NEXT_PUBLIC_MOCK_USDL_ADDRESS=
NEXT_PUBLIC_BET_FACTORY_ADDRESS=
NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS=0x9e1a258598b8a698c20d1a5621c86f1733a8e2e7fb069b230c191f2b28e4ba49

# ── Frontend ──────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_PRIVY_APP_ID=
NEXT_PUBLIC_PRIVY_CLIENT_ID=

# ── Backend ───────────────────────────────────────────
GENLAYER_RPC_URL=https://bradbury.genlayer.com/rpc
CONTRACT_ADDRESS=0x9e1a258598b8a698c20d1a5621c86f1733a8e2e7fb069b230c191f2b28e4ba49
OWNER_PRIVATE_KEY=

# ── Database (Optional - for persistence) ─────────────
DATABASE_URL=postgresql://user:password@localhost:5432/predikt_db

# ── LLM APIs (Choose at least one) ────────────────────
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
TOGETHER_API_KEY=

# ── Bridge Service ────────────────────────────────────
BET_FACTORY_ADDRESS=
EOF
    cp .env.template .env
    echo "${GREEN}✅ Created .env file${NC}"
else
    echo "${GREEN}✅ .env file already exists${NC}"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✅ Setup Complete!                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "1️⃣  Configure your .env file:"
echo "   • Add NEXT_PUBLIC_PRIVY_APP_ID & PRIVY_CLIENT_ID"
echo "   • Add at least one LLM API key (OPENAI_API_KEY, etc)"
echo "   • Update contract addresses"
echo ""

echo "2️⃣  (Optional) Setup PostgreSQL Database:"
echo "   • Follow DATABASE-SETUP.md"
echo "   • Run: python3 -c \"from backend.models.database import init_db; init_db()\""
echo ""

echo "3️⃣  Start Backend (Terminal 1):"
echo "   $ cd /Users/user/Downloads/predikt"
echo "   $ make backend"
echo ""

echo "4️⃣  Start Frontend (Terminal 2):"
echo "   $ cd /Users/user/Downloads/predikt"
echo "   $ make frontend"
echo ""

echo "5️⃣  Open Dashboard:"
echo "   $ open http://localhost:3000"
echo ""

echo "${BLUE}📚 Documentation:${NC}"
echo "   • IMPLEMENTATION-GUIDE.md - Complete feature guide"
echo "   • PRIVY-SETUP.md - Wallet integration"
echo "   • DATABASE-SETUP.md - PostgreSQL setup"
echo "   • LLM-SETUP.md - LLM APIs integration"
echo ""

echo "${GREEN}Ready to go! 🚀${NC}"
