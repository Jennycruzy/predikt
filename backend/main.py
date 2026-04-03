"""
predikt Backend
GenLayer AI Prediction Market — Reasoning-Driven Predikt Engine

FastAPI application entry point.
Registers all routers and configures middleware.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os, asyncio

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

from backend.routers import markets_router, debate_router, validators_router
from backend.routers.faucet import router as faucet_router

# Initialize database if using PostgreSQL
if os.getenv("DATABASE_URL"):
    try:
        from backend.models.database import init_db
        init_db()
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")

# ═══════════════════════════════════════════════════════
# App Configuration
# ═══════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm the markets cache so the first Vercel request doesn't cold-start
    async def _warm():
        try:
            from backend.routers.markets import list_markets
            await list_markets()
            print("[STARTUP] Markets cache warmed.")
        except Exception as e:
            print(f"[STARTUP] Cache warm failed (non-fatal): {e}")
    asyncio.create_task(_warm())
    yield

app = FastAPI(
    title="PREDIKT",
    lifespan=lifespan,
    description=(
        "AI-powered prediction market backend. "
        "Reasoning-driven predikt engine for GenLayer Studionet."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,https://predikt.vercel.app,https://*.netlify.app,https://*.pages.dev",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════
# Register Routers
# ═══════════════════════════════════════════════════════

app.include_router(markets_router)
app.include_router(debate_router)
app.include_router(validators_router)
app.include_router(faucet_router)

# ═══════════════════════════════════════════════════════
# Root
# ═══════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "service": "predikt",
        "version": "1.0.0",
        "chain": "GenLayer Studionet",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    from backend.services.chain import chain_service
    from backend.services.storage import storage_service

    return {
        "status": "healthy",
        "chain_mode": chain_service.status,
        "storage": storage_service.get_stats(),
    }


# ═══════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
