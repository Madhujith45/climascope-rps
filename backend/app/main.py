"""
ClimaScope – Backend FastAPI Application
Multi-user AI platform with authentication, device management, and intelligent alerts
"""

import logging
import os
from dotenv import load_dotenv

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_BACKEND_ROOT, ".env"))
load_dotenv()

# ── Logging setup ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routes.data_routes import router as dr
from .routes.alert_routes import router as ar
from .routes.prediction_routes import router as pr
from .routes.device_routes import router as dvr
from .auth import auth_routes
from .db.mongo import init_db as init_mongo_db, close_db as close_mongo_db

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# CORS origins – allow Vercel-hosted frontend (and local dev)
# ─────────────────────────────────────────────────────────────────────
_RAW_ORIGINS = os.environ.get(
    "CLIMASCOPE_CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
)
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _RAW_ORIGINS.split(",") if o.strip()]
# Allow all origins when a wildcard is explicitly set (e.g. for public deployments)
if "*" in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["*"]

# ─────────────────────────────────────────────────────────────────────
# App factory
# ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ClimaScope API",
    description="Multi-user AI microclimate intelligence platform with device management and alerts.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup: create DB tables if they don't exist
@app.on_event("startup")
async def on_startup():
    await init_db()  # SQLite
    try:
        await init_mongo_db()  # MongoDB
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"MongoDB initialization skipped or failed: {e}")
    
    logger.info("ClimaScope backend ready – CORS origins: %s", ALLOWED_ORIGINS)
    logger.info("Multi-user AI platform initialized")

@app.on_event("shutdown")
async def on_shutdown():
    await close_mongo_db()

# ── Routers ───────────────────────────────────────────────────────────
# Core data routes (existing)
app.include_router(dr)

# Authentication routes (new)
app.include_router(auth_routes.router)

# Device management routes (new)
app.include_router(dvr)

# Alert system routes (new)
app.include_router(ar)

# Prediction routes (updated)
app.include_router(pr)

# AI ChatBot routes
from .routes.ai_chat_routes import router as ai_router
app.include_router(ai_router)
# Development Test Routes
from .routes.test_routes import router as test_router
app.include_router(test_router)
# ── Root health-check ─────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
async def health():
    return {
        "status": "ok", 
        "service": "ClimaScope Multi-User AI Platform",
        "version": "2.0.0",
        "features": [
            "JWT Authentication",
            "Device Management", 
            "Anomaly Detection",
            "Intelligent Alerts",
            "Multi-User Support"
        ]
    }
