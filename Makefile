.PHONY: help install dev backend frontend contracts test deploy

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	cd contracts && npm install
	cd frontend && npm install
	cd backend && pip install -r requirements.txt

dev: ## Start backend + frontend (docker)
	docker-compose up --build

backend: ## Start backend only
	python3 -m uvicorn backend.main:app --reload --port 8000

frontend: ## Start frontend only
	cd frontend && npm run dev

contracts-compile: ## Compile Solidity contracts
	cd contracts && npx hardhat compile

contracts-test: ## Run contract tests
	cd contracts && npx hardhat test

deploy-token: ## Deploy MockUSDL to Base Sepolia
	cd contracts && npx hardhat run scripts/deploy.js --network baseSepolia

deploy-genlayer: ## Deploy intelligent contract to GenLayer Studionet
	@echo "Open GenLayer Studio: https://studio.genlayer.com"
	@echo "Upload: contracts/prediction_market.py"
	@echo "Deploy to Studionet testnet"

clean: ## Clean build artifacts
	cd contracts && npx hardhat clean
	cd frontend && rm -rf .next
	find . -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
