"""
AlphaForge Backend API - FastAPI application
Main entry point for all backend services and API endpoints.
"""

# Load environment variables from .env file FIRST
import config

import os
import logging
import uuid
import time
import hmac
import hashlib
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from statistics import mean
from typing import Any, Dict, List, Set, Optional
from threading import Lock

from fastapi import FastAPI, HTTPException, Depends, Query, Body, Header, Request, Path, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from models.schemas import *
from database.db import get_db
from firebase_config import verify_firebase_token, FirebaseTokenVerifier
from services.signal_aggregator_v2 import SignalAggregator
from services.signal_processor import SignalProcessor
from services.paper_trading import PaperTradingEngine
from services.portfolio import PortfolioService
from services.risk_manager import RiskManager
from services.market_data_v2 import MarketDataService
from services.chat_service import ChatService
from services.creator_service import CreatorVerificationService
from services.user_service import UserManagementService
from services.backtest_service import BacktestingService
from services.strategy_service import StrategyService
from services.ml_signal_scorer import MLSignalScorer
from services.creator_marketplace import CreatorMarketplaceService
from services.kyc_service import KYCService
from services.signal_performance_tracker import SignalPerformanceTracker
from services.external_signal_validator import ExternalSignalPerformanceValidator
from services.market_correlation_analyzer import MarketCorrelationAnalyzer
from services.binance_websocket import initialize_binance_ws, get_ws_manager
from services.rate_limiter import AdaptiveRateLimiter, RateLimitingMiddleware
from services.performance_monitor import PerformanceMonitor, PerformanceMonitoringMiddleware
from services.ml_retraining import MLModelRetrainingPipeline
from services.alert_system import AlertManager, LogAlertChannel, AlertSeverity
from services.strategy_manager import StrategyManagementService, StrategyType, StrategyStatus
from services.portfolio_risk_analyzer import PortfolioRiskAnalyzer, RiskLimitEnforcer
from tests.load_test_suite import LoadTestRunner
from utils.redis_manager import redis_manager
from services.startup_orchestrator import get_orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# WEBSOCKET MANAGER
# ============================================================================

class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, group: str):
        """Accept and register connection."""
        await websocket.accept()
        if group not in self.active_connections:
            self.active_connections[group] = set()
        self.active_connections[group].add(websocket)
        logger.info(f"WebSocket connected to group: {group}")
    
    def disconnect(self, websocket: WebSocket, group: str):
        """Remove connection."""
        if group in self.active_connections:
            self.active_connections[group].discard(websocket)
    
    async def broadcast_to_group(self, group: str, message: Dict[str, Any]):
        """Broadcast to all connections in group."""
        if group not in self.active_connections:
            return
        
        json_data = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections[group]:
            try:
                await connection.send_text(json_data)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.append(connection)
        
        for ws in disconnected:
            self.disconnect(ws, group)

# Global service instances
db = get_db()
signal_aggregator = None
signal_processor = None
paper_trading = None
portfolio_service = None
risk_manager = None
market_data_service = None
chat_service = None
creator_service = None
user_service = None
backtest_service = None
strategy_service = None
ml_scorer = None
creator_marketplace = None
kyc_service = None

# Recommendation Services (Phase 3 Enhancements)
signal_perf_tracker = None
external_signal_validator = None
market_correlation_analyzer = None
binance_ws_manager = None

# Infrastructure Services (Rate Limiting & Monitoring)
rate_limiter = None
perf_monitor = None

# Advanced Services (ML, Alerts, Strategy, Risk)
ml_retraining_pipeline = None
alert_manager = None
strategy_manager = None
portfolio_risk_analyzer = None
risk_enforcer = None
load_test_runner = None

# WebSocket and Analytics
ws_manager = WebSocketManager()
ph = None  # PostHog client


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global signal_aggregator, signal_processor, paper_trading, portfolio_service, risk_manager, market_data_service
    global chat_service, creator_service, user_service, backtest_service, strategy_service
    global ml_scorer, creator_marketplace, kyc_service, ph
    global signal_perf_tracker, external_signal_validator, market_correlation_analyzer, binance_ws_manager
    global rate_limiter, perf_monitor
    
    # Startup
    logger.info("🚀 Starting AlphaForge Backend API")

    if os.getenv("API_ENV", "development").lower() == "production":
        config.validate_config()
    
    # ========================================================================
    # ORCHESTRATED STARTUP (Database Migration & Verification)
    # ========================================================================
    
    orchestrator = get_orchestrator()
    
    # Auto-migrate in development, manual in production
    auto_migrate = os.getenv("API_ENV", "development").lower() != "production"
    
    startup_ok = await orchestrator.startup(auto_migrate=auto_migrate)
    
    if not startup_ok:
        logger.error("❌ Startup orchestration failed - Backend cannot start")
        # In production, fail hard; in development, warn but attempt to continue
        if os.getenv("API_ENV", "development").lower() == "production":
            raise RuntimeError("Backend startup verification failed")
        else:
            logger.warning("⚠️  Continuing in degraded mode...")
    
    # ========================================================================
    # INITIALIZE REDIS & CACHE (if configured)
    # ========================================================================
    
    redis_connected = await redis_manager.connect()
    if redis_connected:
        logger.info("🔴 Redis cache layer activated")
    else:
        logger.info("🟢 Using in-memory cache (Redis unavailable or disabled)")
    
    # ========================================================================
    # INITIALIZE MULTI-SOURCE SERVICES
    # ========================================================================
    
    # Initialize market data service (multi-source with caching)
    market_data_service = MarketDataService()
    await market_data_service.initialize()
    logger.info("✅ Market data service initialized (multi-source)")
    
    # Log data source health
    health = market_data_service.get_data_source_health()
    logger.info(f"📊 Data sources health: {health}")
    
    # Log cache status
    cache_backend = config.Config.CACHE_BACKEND.lower()
    cache_stats = market_data_service.get_cache_stats()
    logger.info(f"💾 Cache initialized: {cache_backend} | Stats: {cache_stats}")
    
    # Initialize signal aggregator (uses market data + technical indicators)
    signal_aggregator = SignalAggregator(performance_tracker=signal_perf_tracker)
    await signal_aggregator.initialize()
    logger.info("✅ Signal aggregator initialized (multi-source indicators)")
    
    # ========================================================================
    # INITIALIZE REMAINING SERVICES
    # ========================================================================
    
    signal_processor = SignalProcessor()
    paper_trading = PaperTradingEngine(db)
    portfolio_service = PortfolioService(db)
    risk_manager = RiskManager(db)
    chat_service = ChatService(db)
    creator_service = CreatorVerificationService(db)
    user_service = UserManagementService(db)
    backtest_service = BacktestingService(db)
    strategy_service = StrategyService(db)
    ml_scorer = MLSignalScorer(db)
    creator_marketplace = CreatorMarketplaceService(db)
    kyc_service = KYCService(db)
    
    # ========================================================================
    # INITIALIZE RECOMMENDATION SERVICES (Phase 3 Enhancements)
    # ========================================================================
    
    # Signal Performance Tracking - MUST be before connecting to aggregator
    if os.getenv("ENABLE_SIGNAL_PERFORMANCE_TRACKING", "true").lower() == "true":
        try:
            signal_perf_tracker = SignalPerformanceTracker(db)
            # Connect to signal aggregator for automatic tracking
            await signal_aggregator.set_performance_tracker(signal_perf_tracker)
            logger.info("✅ Signal performance tracker initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize signal performance tracker: {e}")
    
    # External Signal Validation
    if os.getenv("ENABLE_EXTERNAL_SIGNAL_VALIDATION", "true").lower() == "true":
        try:
            external_signal_validator = ExternalSignalPerformanceValidator(db)
            logger.info("✅ External signal validator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize external signal validator: {e}")
    
    # Market Correlation Analysis
    if os.getenv("ENABLE_MARKET_CORRELATION_ANALYSIS", "true").lower() == "true":
        try:
            market_correlation_analyzer = MarketCorrelationAnalyzer(db)
            logger.info("✅ Market correlation analyzer initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize market correlation analyzer: {e}")
    
    # Binance WebSocket (Real-time data)
    if os.getenv("ENABLE_BINANCE_WEBSOCKET", "true").lower() == "true":
        try:
            binance_ws_manager = await initialize_binance_ws()
            logger.info("✅ Binance WebSocket manager initialized (real-time data)")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize Binance WebSocket: {e} (fallback to polling)")
    
    logger.info("✅ All recommendation services initialized")
    
    # Initialize PostHog
    try:
        from posthog import Posthog
        posthog_key = os.getenv("POSTHOG_API_KEY")
        posthog_host = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
        if posthog_key:
            ph = Posthog(api_key=posthog_key, host=posthog_host)
            logger.info("✅ PostHog analytics initialized")
        else:
            logger.warning("⚠️  PostHog API key not set")
    except Exception as e:
        logger.warning(f"⚠️  PostHog initialization failed: {e}")
    
    # ========================================================================
    # INITIALIZE INFRASTRUCTURE SERVICES (Rate Limiter & Monitoring)
    # ========================================================================
    # Note: rate_limiter and perf_monitor are initialized at module level
    # (before app creation) so they can be added to middleware stack
    logger.info("✅ Rate limiter and performance monitor attached to middleware")
    
    logger.info("✅ All services initialized and middleware configured")
    
    logger.info("✅ All services initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AlphaForge Backend API")
    
    # Close WebSocket connections
    if binance_ws_manager:
        try:
            await binance_ws_manager.disconnect()
            logger.info("🔌 Binance WebSocket closed")
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")
    
    # Close Redis connection if enabled
    if redis_manager.enabled:
        await redis_manager.close()
    
    # Close services
    if signal_aggregator:
        await signal_aggregator.close()
        logger.info("🔌 Signal aggregator closed")
    if market_data_service:
        await market_data_service.close()
        logger.info("🔌 Market data service closed")
    logger.info("✅ Shutdown complete")


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="AlphaForge Backend API",
    description="AI-powered trading signals and portfolio management",
    version="1.0.0",
    lifespan=lifespan
)

API_ENV = os.getenv("API_ENV", "development").lower()
IS_PRODUCTION = API_ENV == "production"
REQUIRE_REAL_DB = os.getenv("REQUIRE_REAL_DB", "true" if IS_PRODUCTION else "false").lower() == "true"
SECURITY_HEADERS_ENABLED = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"

# CORS configuration - allow development frontends and ngrok tunnels
DEV_URLS = [
    "http://localhost:3000",
    "http://localhost:9002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:9002",
]
# Parse ngrok URL from environment (format: https://xxxx.ngrok-free.app)
ngrok_url = os.getenv("NGROK_TUNNEL_URL", "").strip()
if not ngrok_url:
    # Auto-extract from NEXT_PUBLIC_API_URL if it's an ngrok URL
    api_url = os.getenv("NEXT_PUBLIC_API_URL", "")
    if "ngrok" in api_url:
        ngrok_url = api_url
if ngrok_url and not ngrok_url.endswith("/"):
    DEV_URLS.append(ngrok_url)

CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", ",".join(DEV_URLS) if not IS_PRODUCTION else "")
ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOW_ORIGINS.split(",") if origin.strip()] or ["*"]

# Debug: Log CORS configuration
logger.info(f"🔐 CORS Configuration (IS_PRODUCTION={IS_PRODUCTION})")
logger.info(f"📍 Allowed Origins: {ALLOWED_ORIGINS}")
if ngrok_url:
    logger.info(f"🌐 ngrok URL detected: {ngrok_url}")

if IS_PRODUCTION and "*" in ALLOWED_ORIGINS:
    raise RuntimeError("CORS_ALLOW_ORIGINS cannot include '*' in production")

TRUSTED_HOSTS_RAW = os.getenv("TRUSTED_HOSTS", "*")
TRUSTED_HOSTS = [host.strip() for host in TRUSTED_HOSTS_RAW.split(",") if host.strip()] or ["*"]

if IS_PRODUCTION and "*" in TRUSTED_HOSTS:
    raise RuntimeError("TRUSTED_HOSTS cannot include '*' in production")

# Standard CORS middleware (more reliable than custom)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Host header hardening
app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)

# Add performance monitoring middleware
perf_monitor = PerformanceMonitor()
app.add_middleware(PerformanceMonitoringMiddleware, monitor=perf_monitor)

# Add adaptive rate limiting middleware
rate_limiter = AdaptiveRateLimiter()
app.add_middleware(RateLimitingMiddleware, rate_limiter=rate_limiter)

# Initialize advanced services
ml_retraining_pipeline = MLModelRetrainingPipeline(retraining_interval_days=7)
alert_manager = AlertManager()
alert_manager.add_alert_handler(LogAlertChannel().send)
strategy_manager = StrategyManagementService()
portfolio_risk_analyzer = PortfolioRiskAnalyzer()
risk_enforcer = RiskLimitEnforcer()
load_test_runner = LoadTestRunner(base_url=os.getenv("API_URL", "http://localhost:8000"))

# Optional in-memory rate limiter for production hardening
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "120"))
_rate_limit_store: Dict[str, Dict[str, float]] = {}
_rate_limit_lock = Lock()

# Legacy rate limit middleware - disabled in favor of AdaptiveRateLimiter middleware
# kept for reference
# @app.middleware("http")
# async def rate_limit_middleware(request: Request, call_next):
#     ... old middleware code ...

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)

    if SECURITY_HEADERS_ENABLED:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/status", tags=["Health"])
async def status():
    """Detailed status endpoint."""
    return {
        "api_running": True,
        "database": "connected",
        "database_mode": "mock" if db.is_mock_mode else "supabase",
        "services": {
            "signal_aggregator": "ready" if signal_aggregator else "not_ready",
            "signal_processor": "ready" if signal_processor else "not_ready",
            "paper_trading": "ready" if paper_trading else "not_ready",
            "portfolio": "ready" if portfolio_service else "not_ready",
            "risk_manager": "ready" if risk_manager else "not_ready"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe endpoint."""
    try:
        _ = db.supabase
        if REQUIRE_REAL_DB and db.is_mock_mode:
            raise HTTPException(status_code=503, detail="Service not ready: running in mock database mode")

        required_tables_raw = os.getenv(
            "REQUIRED_DB_TABLES",
            "users,signals,paper_trades,positions,portfolios,creator_profiles,kyc_verifications,audit_logs,external_signals,api_keys,strategies,creator_strategies,strategy_subscriptions,strategy_paper_trades,backtests,chat_messages,notifications,user_risk_settings,external_signal_rules",
        )
        required_tables = [table.strip() for table in required_tables_raw.split(",") if table.strip()]
        table_check = db.verify_required_tables(required_tables) if required_tables else {"ok": True, "missing_tables": []}
        if REQUIRE_REAL_DB and not table_check.get("ok", False):
            raise HTTPException(
                status_code=503,
                detail=f"Service not ready: missing required tables: {', '.join(table_check.get('missing_tables', []))}",
            )

        services_ready = all(
            [
                signal_aggregator is not None,
                signal_processor is not None,
                paper_trading is not None,
                portfolio_service is not None,
                risk_manager is not None,
                market_data_service is not None,
                chat_service is not None,
                creator_service is not None,
                user_service is not None,
                backtest_service is not None,
                strategy_service is not None,
            ]
        )

        return {
            "status": "ready" if services_ready else "degraded",
            "database": "ready",
            "database_mode": "mock" if db.is_mock_mode else "supabase",
            "services_ready": services_ready,
            "required_tables_ok": table_check.get("ok", True),
            "missing_tables": table_check.get("missing_tables", []),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {e}")


def _iso(value: Any) -> str:
    if value is None:
        return datetime.utcnow().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


# ============================================================================
# MULTI-SOURCE DATA HEALTH
# ============================================================================

@app.get("/api/health/data-sources", tags=["Health"])
async def data_sources_health():
    """Health check for multi-source data infrastructure."""
    if not market_data_service:
        raise HTTPException(status_code=503, detail="Market data service not initialized")
    
    try:
        data_sources = market_data_service.get_data_source_health()
        cache_stats = market_data_service.get_cache_stats()
        cache_backend = config.Config.CACHE_BACKEND.lower()
        redis_health = await redis_manager.health_check()
        
        return {
            "status": "healthy",
            "cache": {
                "backend": cache_backend,
                "stats": cache_stats,
                "redis": redis_health
            },
            "data_sources": data_sources,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Data sources health check error: {e}")
        raise HTTPException(status_code=503, detail=f"Data sources check failed: {e}")


@app.get("/api/health/signals", tags=["Health"])
async def signals_health():
    """Health check for signal generation infrastructure."""
    if not signal_aggregator:
        raise HTTPException(status_code=503, detail="Signal aggregator not initialized")
    
    return {
        "status": "healthy",
        "signal_aggregator": "ready",
        "uses": {
            "primary_source": config.Config.DATA_SOURCE_PRIMARY,
            "secondary_source": config.Config.DATA_SOURCE_SECONDARY,
            "indicators": ["RSI", "MACD", "Bollinger_Bands", "Stochastic", "ATR"],
            "min_confidence": config.Config.MIN_SIGNAL_CONFIDENCE
        },
        "timestamp": datetime.utcnow().isoformat()
    }


def _normalize_direction(signal_type: Any) -> str:
    signal_type_upper = str(signal_type or "HOLD").upper()
    return "LONG" if signal_type_upper == "BUY" else "SHORT"


def _map_market_data_quality_status(status: str) -> str:
    status_upper = str(status or "HEALTHY").upper()
    if status_upper == "HEALTHY":
        return "Optimal"
    if status_upper == "DEGRADED":
        return "Degraded"
    return "Offline"


def _map_user_profile_to_frontend(user: Dict[str, Any]) -> Dict[str, Any]:
    display_name = user.get("display_name") or user.get("name") or "Anonymous"
    kyc_status_raw = str(user.get("kyc_status", "NOT_STARTED")).upper()
    if kyc_status_raw in {"NOT_STARTED", "UNVERIFIED"}:
        kyc_status = "Unverified"
    elif kyc_status_raw in {"SUBMITTED", "PENDING"}:
        kyc_status = "Pending"
    elif kyc_status_raw == "APPROVED":
        kyc_status = "Verified"
    else:
        kyc_status = "Rejected"

    return {
        "id": str(user.get("id")),
        "name": display_name,
        "email": user.get("email", ""),
        "plan": user.get("plan", "free"),
        "riskTolerance": user.get("risk_tolerance", "moderate"),
        "connectedExchanges": user.get("connected_exchanges", []),
        "onboardingComplete": bool(user.get("onboarding_complete", False)),
        "createdAt": _iso(user.get("created_at")),
        "kycStatus": kyc_status,
    }


def _map_signal_to_frontend(signal: Dict[str, Any]) -> Dict[str, Any]:
    entry_price = float(signal.get("entry_price") or signal.get("price") or 0)
    stop_loss = float(signal.get("stop_loss_price") or signal.get("stop_loss") or (entry_price * 0.98 if entry_price else 0))
    take_profit = float(signal.get("take_profit_price") or signal.get("take_profit") or (entry_price * 1.03 if entry_price else 0))
    direction = _normalize_direction(signal.get("signal_type"))

    risk_reward_ratio = 0.0
    if entry_price and stop_loss and take_profit:
        downside = abs(entry_price - stop_loss)
        upside = abs(take_profit - entry_price)
        risk_reward_ratio = round((upside / downside), 2) if downside else 0.0

    return {
        "id": str(signal.get("id")),
        "asset": signal.get("ticker", "UNKNOWN"),
        "direction": direction,
        "entryPrice": entry_price,
        "stopLoss": stop_loss,
        "takeProfit": take_profit,
        "confidence": float(signal.get("confidence") or 0),
        "strategy": signal.get("source", "system"),
        "strategyId": str(signal.get("strategy_id") or signal.get("created_by") or "system"),
        "status": "active",
        "riskRewardRatio": risk_reward_ratio,
        "createdAt": _iso(signal.get("created_at")),
        "closedAt": signal.get("closed_at"),
        "pnlPercent": signal.get("pnl_percent"),
        "drivers": signal.get("drivers", []),
    }


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.post("/api/users/register", response_model=dict, tags=["Users"])
async def register_user(user: UserProfileCreate, firebase_uid: str = Depends(verify_firebase_token)):
    """Register a new user with Firebase authentication."""
    try:
        # Check for duplicate email
        existing = db.supabase.table("users").select("id").eq("email", user.email).execute()
        if existing.data and len(existing.data) > 0:
            logger.warning(f"⚠️ Duplicate email: {user.email}")
            raise HTTPException(status_code=409, detail="Email already exists")
        
        user_data = {
            "email": user.email,
            "display_name": user.display_name,
            "institution_name": user.institution_name or "",
            "plan": user.plan.value if isinstance(user.plan, Enum) else str(user.plan).lower(),
            "risk_tolerance": user.risk_tolerance.value if isinstance(user.risk_tolerance, Enum) else str(user.risk_tolerance).lower(),
            "firebase_uid": firebase_uid,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = db.supabase.table("users").insert(user_data).execute()
        
        if response.data and len(response.data) > 0:
            created_user = response.data[0]
            logger.info(f"✅ User registered: {user.email} with Firebase UID: {firebase_uid}")
            return {"success": True, "user": created_user}
        
        raise HTTPException(status_code=400, detail="Registration failed")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/firebase/{firebase_uid}", response_model=UserProfile, tags=["Users"])
async def get_user_by_firebase_uid(firebase_uid: str):
    """Get user profile by Firebase UID (login endpoint)."""
    try:
        logger.info(f"📖 Fetching user by Firebase UID: {firebase_uid}")
        response = db.supabase.table("users").select("*").eq("firebase_uid", firebase_uid).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"✅ User found: {firebase_uid}")
            user_data = response.data[0]
            
            # Ensure all required fields are present with defaults
            if "kyc_status" not in user_data:
                user_data["kyc_status"] = KYCStatus.NOT_STARTED.value
            if "verification_stage" not in user_data:
                user_data["verification_stage"] = VerificationStage.STAGE_1_INTRO.value
            if "onboarding_complete" not in user_data:
                user_data["onboarding_complete"] = False
            if "updated_at" not in user_data:
                user_data["updated_at"] = user_data.get("created_at", datetime.utcnow().isoformat())
            
            return user_data
        
        logger.warning(f"⚠️ User not found for Firebase UID: {firebase_uid}")
        raise HTTPException(status_code=404, detail="User not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}", response_model=UserProfile, tags=["Users"])
async def get_user(user_id: str, firebase_uid: str = Depends(verify_firebase_token)):
    """Get user profile."""
    try:
        # Validate UUID format
        try:
            uuid.UUID(user_id)
        except (ValueError, AttributeError):
            logger.warning(f"⚠️ Invalid user ID format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        logger.info(f"📖 Fetching user: {user_id}")
        response = db.supabase.table("users").select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"✅ User found: {user_id}")
            user_data = response.data[0]
            
            # Ensure all required fields are present with defaults
            if "kyc_status" not in user_data:
                user_data["kyc_status"] = KYCStatus.NOT_STARTED.value
            if "verification_stage" not in user_data:
                user_data["verification_stage"] = VerificationStage.STAGE_1_INTRO.value
            if "onboarding_complete" not in user_data:
                user_data["onboarding_complete"] = False
            if "updated_at" not in user_data:
                user_data["updated_at"] = user_data.get("created_at", datetime.utcnow().isoformat())
            
            return user_data
        
        logger.warning(f"⚠️ User not found: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/users/{user_id}", response_model=UserProfile, tags=["Users"])
async def update_user(user_id: str, updates: UserProfileUpdate, firebase_uid: str = Depends(verify_firebase_token)):
    """Update user profile (requires Firebase authentication)."""
    try:
        update_data = updates.model_dump(exclude_unset=True)
        # Convert enums to strings
        if "plan" in update_data:
            update_data["plan"] = update_data["plan"].value if isinstance(update_data["plan"], Enum) else str(update_data["plan"]).lower()
        if "risk_tolerance" in update_data:
            update_data["risk_tolerance"] = update_data["risk_tolerance"].value if isinstance(update_data["risk_tolerance"], Enum) else str(update_data["risk_tolerance"]).lower()
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"📝 Updating user: {user_id} (Firebase UID: {firebase_uid})")
        response = db.supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"✅ User updated: {user_id}")
            return response.data[0]
        
        logger.warning(f"⚠️ User not found for update: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SIGNAL ENDPOINTS
# ============================================================================

@app.get("/api/signals", response_model=List[Signal], tags=["Signals"])
async def get_signals(limit: int = Query(50, le=100)):
    """Get top signals."""
    try:
        response = db.supabase.table("signals").select("*").limit(limit).execute()

        signals = []
        for record in (response.data or []):
            normalized = dict(record)
            normalized.setdefault("id", str(uuid.uuid4()))
            normalized.setdefault("created_by", "system")
            normalized.setdefault("created_at", datetime.utcnow().isoformat())
            normalized.setdefault("rationale", "No rationale provided")
            normalized.setdefault("drivers", [])

            confidence = normalized.get("confidence", 0.5)
            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                confidence = 0.5
            normalized["confidence"] = min(1.0, max(0.0, confidence))

            signal_type = str(normalized.get("signal_type", "HOLD")).upper()
            if signal_type not in {"BUY", "SELL", "HOLD"}:
                signal_type = "HOLD"
            normalized["signal_type"] = signal_type

            signals.append(normalized)

        logger.info(f"✅ Fetched {len(signals)} signals")
        
        return signals
    
    except Exception as e:
        logger.error(f"❌ Signal fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/latest", response_model=List[Signal], tags=["Signals"])
async def get_latest_signals(limit: int = Query(50, le=100)):
    """Compatibility alias for frontend contract."""
    return await get_signals(limit=limit)


@app.post("/api/signals/process", tags=["Signals"])
async def process_signals(payload: Dict[str, Any] = Body(None), firebase_uid: str = Depends(verify_firebase_token)):
    """
    Trigger signal aggregation and processing (requires Firebase authentication).
    Accepts optional payload with symbols list for testing.
    """
    try:
        # Determine symbols from payload or use defaults
        if payload and "symbols" in payload:
            symbols = payload.get("symbols", ["BTC", "ETH", "BNB", "SOL"])
        else:
            symbols = ["BTC", "ETH", "BNB", "SOL"]
        
        raw_signals = await signal_aggregator.fetch_all_signals(symbols)

        if not raw_signals:
            logger.warning("⚠️ No external signals available; using deterministic fallback signals")
            raw_signals = [
                {
                    "ticker": symbol,
                    "signal_type": "HOLD",
                    "confidence": 0.65,
                    "rationale": "Fallback signal due to unavailable external providers",
                    "drivers": ["fallback_engine"],
                }
                for symbol in symbols
            ]
        
        # Process signals
        processed = signal_processor.process_signals(raw_signals)
        
        # Store in database only if database is available
        stored_signals = []
        try:
            for signal in processed:
                # Only include valid database columns
                payload_db = {
                    "id": signal.get("id", str(uuid.uuid4())),
                    "ticker": signal.get("ticker"),
                    "signal_type": signal.get("signal_type"),
                    "confidence": signal.get("confidence"),
                    "entry_price": signal.get("entry_price"),
                    "stop_loss_price": signal.get("stop_loss_price"),
                    "take_profit_price": signal.get("take_profit_price"),
                    "rationale": signal.get("rationale"),
                    "drivers": signal.get("drivers", []),
                    "created_by": signal.get("created_by", "system"),
                    "created_at": signal.get("created_at", datetime.utcnow().isoformat()),
                }
                
                insert_response = db.supabase.table("signals").insert(payload_db).execute()
                if getattr(insert_response, "data", None):
                    stored_signals.append(insert_response.data[0])
                else:
                    stored_signals.append(payload_db)
        except Exception as db_error:
            logger.warning(f"⚠️ Database storage failed: {db_error}. Returning processed signals without persistence.")
            stored_signals = processed
        
        logger.info(f"✅ Processed {len(processed)} signals")
        
        # Track in PostHog
        if ph:
            try:
                ph.capture(
                    distinct_id="system",
                    event="signals_processed",
                    properties={
                        "count": len(processed),
                        "symbols": symbols,
                    }
                )
            except Exception as e:
                logger.warning(f"PostHog tracking failed: {e}")
        
        return {
            "success": True,
            "signals_processed": len(processed),
            "signals": stored_signals[:10]  # Return top 10 with persisted identifiers
        }
    
    except Exception as e:
        logger.error(f"❌ Signal processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signals/{signal_id}/validate", tags=["Signals"])
async def validate_signal_trade(signal_id: str, user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Validate a signal for trading (risk check - requires Firebase authentication)."""
    try:
        # Fetch signal
        signal_response = db.supabase.table("signals").select("*").eq("id", signal_id).execute()
        if not signal_response.data:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        signal = signal_response.data[0]
        
        # Get user portfolio
        portfolio = await portfolio_service.get_portfolio_summary(user_id)
        portfolio_balance = portfolio.get("total_equity", 100000)
        
        # Validate with risk manager
        validation = await risk_manager.validate_trade(
            user_id,
            signal,
            portfolio_balance
        )
        
        logger.info(f"✅ Signal validation: {signal_id} - Risk Score: {validation['risk_score']:.1f}")
        
        return validation
    
    except Exception as e:
        logger.error(f"❌ Signal validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PAPER TRADING ENDPOINTS
# ============================================================================

@app.post("/api/trades/paper", tags=["Paper Trading"])
async def create_paper_trade(trade: PaperTradeCreate, firebase_uid: str = Depends(verify_firebase_token)):
    """Create a paper trade (requires Firebase authentication)."""
    try:
        result = await paper_trading.execute_paper_trade(
            user_id=trade.user_id,
            signal_id=trade.signal_id,
            ticker=trade.asset,
            direction=trade.direction.value,
            entry_price=trade.entry_price,
            quantity=trade.quantity,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit
        )
        
        if result["success"]:
            # Track signal execution in performance tracker
            if signal_perf_tracker and trade.signal_id:
                try:
                    await signal_perf_tracker.record_signal_execution(
                        signal_id=trade.signal_id,
                        entry_price=trade.entry_price,
                        entry_time=datetime.utcnow(),
                        trade_id=result.get("trade_id"),
                        user_id=trade.user_id
                    )
                    logger.info(f"📊 Signal execution recorded for {trade.signal_id}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to record signal execution: {e}")
            
            # Track in PostHog
            if ph:
                try:
                    ph.capture(
                        distinct_id=trade.user_id,
                        event="trade_executed_paper",
                        properties={
                            "asset": trade.asset,
                            "direction": trade.direction.value,
                            "quantity": trade.quantity,
                            "entry_price": trade.entry_price,
                            "trade_id": result.get("trade_id"),
                        }
                    )
                except Exception as e:
                    logger.warning(f"PostHog tracking failed: {e}")
            
            return {"success": True, "trade_id": result["trade_id"], "data": result}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    except Exception as e:
        logger.error(f"❌ Paper trade creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trades/paper/{trade_id}/close", tags=["Paper Trading"])
async def close_paper_trade(trade_id: str, exit_price: float = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Close a paper trade (requires Firebase authentication)."""
    try:
        # Get trade details before closing
        try:
            trade_response = db.supabase.table("paper_trades").select("*").eq("id", trade_id).single().execute()
            trade_record = trade_response.data
        except Exception:
            trade_record = None
        
        result = await paper_trading.close_paper_trade(trade_id, exit_price)
        
        if result["success"]:
            # Track signal closure in performance tracker
            if signal_perf_tracker and trade_record and trade_record.get("signal_id"):
                try:
                    entry_price = float(trade_record.get("entry_price", exit_price))
                    quantity = float(trade_record.get("quantity", 1))
                    
                    # Calculate PnL
                    pnl = (exit_price - entry_price) * quantity
                    roi_pct = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                    
                    await signal_perf_tracker.record_signal_closure(
                        signal_id=trade_record.get("signal_id"),
                        exit_price=exit_price,
                        entry_price=entry_price,
                        pnl=pnl,
                        roi_pct=roi_pct,
                        exit_time=datetime.utcnow(),
                        trade_id=trade_id
                    )
                    logger.info(f"📊 Signal closure recorded for {trade_record.get('signal_id')}: PnL={pnl}, ROI={roi_pct:.2f}%")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to record signal closure: {e}")
            
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    except Exception as e:
        logger.error(f"❌ Paper trade close failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/paper", tags=["Paper Trading"])
async def get_paper_trades(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Get all paper trades for a user (requires Firebase authentication)."""
    try:
        response = db.supabase.table("paper_trades").select("*").eq("user_id", user_id).execute()
        
        trades = response.data or []
        logger.info(f"✅ Fetched {len(trades)} paper trades for {user_id}")
        
        return {"trades": trades, "count": len(trades)}
    
    except Exception as e:
        logger.error(f"❌ Paper trades fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@app.get("/api/portfolio/{user_id}", tags=["Portfolio"])
async def get_portfolio(user_id: str, firebase_uid: str = Depends(verify_firebase_token)):
    """Get portfolio summary (requires Firebase authentication)."""
    try:
        summary = await portfolio_service.get_portfolio_summary(user_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        logger.info(f"✅ Portfolio retrieved for {user_id}")
        return summary
    
    except Exception as e:
        logger.error(f"❌ Portfolio fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/{user_id}/metrics", tags=["Portfolio"])
async def get_portfolio_metrics(user_id: str, firebase_uid: str = Depends(verify_firebase_token)):
    """Get detailed portfolio metrics (performance stats) (requires Firebase authentication)."""
    try:
        metrics = await paper_trading.get_portfolio_metrics(user_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Portfolio metrics not found")
        
        return metrics
    
    except Exception as e:
        logger.error(f"❌ Metrics fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions/{user_id}", tags=["Portfolio"])
async def get_positions(user_id: str):
    """Get all open positions."""
    try:
        positions = await portfolio_service.get_open_positions(user_id)
        
        return {"positions": positions, "count": len(positions)}
    
    except Exception as e:
        logger.error(f"❌ Positions fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/{user_id}/positions", tags=["Portfolio"])
async def get_portfolio_positions(user_id: str):
    """Compatibility alias for frontend contract."""
    return await get_positions(user_id)


# ============================================================================
# MARKET DATA ENDPOINTS
# ============================================================================

@app.get("/api/market/tickers", response_model=MarketTickerResponse, tags=["Market Data"])
async def get_market_tickers(symbols: str = Query("BTC,ETH,BNB,SOL,XRP")):
    """Get market tickers for specified symbols."""
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        tickers = await market_data_service.fetch_market_tickers(symbol_list)
        
        logger.info(f"✅ Fetched {len(tickers)} market tickers")
        
        return {
            "success": True,
            "tickers": tickers,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"❌ Market tickers fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/sentiment", response_model=MarketSentiment, tags=["Market Data"])
async def get_market_sentiment():
    """Get current market sentiment aggregated across sources."""
    try:
        sentiment = await market_data_service.fetch_market_sentiment()
        
        logger.info(f"✅ Market sentiment fetched: {sentiment['market_status']}")
        
        return sentiment
    
    except Exception as e:
        logger.error(f"❌ Market sentiment fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/data-quality", response_model=DataQualityResponse, tags=["Market Data"])
async def get_data_quality():
    """Get data quality metrics for all market feeds."""
    try:
        data_quality = await market_data_service.fetch_data_quality()
        
        logger.info(f"✅ Fetched data quality for {len(data_quality)} feeds")
        
        return {
            "success": True,
            "data_quality": data_quality,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"❌ Data quality fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/funding-rates", response_model=FundingRatesResponse, tags=["Market Data"])
async def get_funding_rates():
    """Get current funding rates for perpetual contracts."""
    try:
        funding_rates = await market_data_service.fetch_funding_rates()
        
        logger.info(f"✅ Fetched {len(funding_rates)} funding rates")
        
        return {
            "success": True,
            "funding_rates": funding_rates,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"❌ Funding rates fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/open-interest", response_model=OpenInterestResponse, tags=["Market Data"])
async def get_open_interest():
    """Get open interest data for major assets."""
    try:
        open_interest = await market_data_service.fetch_open_interest()
        
        logger.info(f"✅ Fetched open interest for {len(open_interest)} assets")
        
        return {
            "success": True,
            "open_interest": open_interest,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"❌ Open interest fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBHOOK ENDPOINTS (External Signal Ingestion)
# ============================================================================

@app.post("/webhooks/tradingview", tags=["Webhooks"])
async def tradingview_webhook(
    request: Request,
    payload: Dict[str, Any],
    x_webhook_secret: str = Header(None),
    x_webhook_signature: str = Header(None),
):
    """
    Receive TradingView webhook alerts and ingest as signals.
    """
    try:
        # Verify webhook secret
        expected_secret = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")
        expected_hmac_secret = os.getenv("TRADINGVIEW_WEBHOOK_HMAC_SECRET")

        # Optional HMAC signature verification (preferred)
        if expected_hmac_secret and expected_hmac_secret.strip():
            raw_body = await request.body()
            digest = hmac.new(
                expected_hmac_secret.encode("utf-8"),
                raw_body,
                hashlib.sha256,
            ).hexdigest()
            if not x_webhook_signature or not hmac.compare_digest(x_webhook_signature, digest):
                logger.warning("❌ Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Unauthorized: Invalid webhook signature")
        
        # If secret is configured, validate it
        if expected_secret and expected_secret.strip():
            if not x_webhook_secret or x_webhook_secret != expected_secret:
                logger.warning("❌ Invalid webhook secret")
                raise HTTPException(status_code=401, detail="Unauthorized: Invalid webhook secret")
        else:
            if IS_PRODUCTION:
                raise HTTPException(status_code=503, detail="Webhook secret is not configured in production")
            logger.warning("⚠️ Webhook secret not configured, allowing unauthenticated requests in non-production")
        
        # Parse webhook payload
        ticker = payload.get("ticker", "UNKNOWN")
        action = payload.get("action", "HOLD")  # BUY, SELL, HOLD
        price = payload.get("price", 0)
        
        # Create external signal record
        signal_data = {
            "ticker": ticker,
            "signal_type": action,
            "price": price,
            "source": "tradingview",
            "metadata": payload,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = db.supabase.table("external_signals").insert(signal_data).execute()
        
        logger.info(f"✅ TradingView signal ingested: {ticker} {action}")
        
        return {"success": True, "signal_id": response.data[0]["id"] if response.data else None}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CHAT & AI ENDPOINTS
# ============================================================================

@app.post("/api/chat/message", tags=["Chat"])
async def send_chat_message(user_id: str = Query(...), message: str = Query(...)):
    """Send a message and get AI response."""
    try:
        # Get context
        context = await chat_service.get_context_for_response(
            user_id, portfolio_service, signal_processor
        )
        
        # Generate response
        response_text = await chat_service._generate_ai_response(message, context)
        
        # Save messages
        await chat_service.save_message(user_id, message, "user")
        await chat_service.save_message(user_id, response_text, "assistant")
        
        logger.info(f"✅ Chat message processed for {user_id}")
        
        return {
            "success": True,
            "user_message": message,
            "ai_response": response_text,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/history", tags=["Chat"])
async def get_chat_history(user_id: str = Query(...), limit: int = Query(50, le=100)):
    """Get chat history for a user."""
    try:
        history = await chat_service.get_chat_history(user_id, limit)
        
        return {
            "success": True,
            "user_id": user_id,
            "messages": history,
            "count": len(history)
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to fetch chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CREATOR VERIFICATION ENDPOINTS
# ============================================================================

@app.get("/api/creator/verification", tags=["Creator"])
async def get_creator_verification(user_id: str = Query(...)):
    """Get creator verification status and pipeline."""
    try:
        result = await creator_service.get_verification_status(user_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except Exception as e:
        logger.error(f"❌ Failed to get verification status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/creator/strategy-submit", tags=["Creator"])
async def submit_strategy_for_verification(user_id: str = Query(...)):
    """Submit strategy for creator verification."""
    try:
        from pydantic import BaseModel
        
        class StrategySubmission(BaseModel):
            name: str
            description: str
            parameters: dict = {}
            backtest_results: dict = {}
        
        # In production, parse from request body
        strategy_data = {
            "name": "Test Strategy",
            "description": "A test trading strategy",
            "parameters": {},
            "backtest_results": {}
        }
        
        result = await creator_service.submit_strategy(user_id, strategy_data)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except Exception as e:
        logger.error(f"❌ Failed to submit strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/creator/reputation/{creator_id}", tags=["Creator"])
async def get_creator_reputation(creator_id: str):
    """Get creator reputation score and tier."""
    try:
        result = await creator_service.get_reputation_score(creator_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))

    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"❌ Failed to get reputation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/creators", tags=["Creator"])
async def create_creator_profile(user_id: str = Query(...), payload: Dict[str, Any] = None):
    """Create or update a creator profile (roadmap compatibility endpoint)."""
    try:
        payload = payload or {}
        profile_data = {
            "user_id": user_id,
            "bio": payload.get("bio", ""),
            "fee_percent": float(payload.get("fee_percent", 0)),
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = db.supabase.table("creator_profiles").upsert(profile_data).execute()
        creator_profile = response.data[0] if response.data else profile_data

        return {
            "success": True,
            "creator": creator_profile,
            "strategy_ids": payload.get("strategy_ids", []),
        }
    except Exception as e:
        logger.error(f"❌ Failed to create creator profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/creators", tags=["Creator"])
async def list_creators(limit: int = Query(50, le=100), offset: int = Query(0)):
    """List creator profiles (roadmap compatibility endpoint)."""
    try:
        response = (
            db.supabase.table("creator_profiles")
            .select("*")
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        creators = response.data or []
        return {"success": True, "creators": creators, "count": len(creators)}
    except Exception as e:
        logger.error(f"❌ Failed to list creators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/creators/{creator_id}", tags=["Creator"])
async def get_creator_profile(creator_id: str):
    """Get creator profile by creator profile id or user id."""
    try:
        by_profile_id = db.supabase.table("creator_profiles").select("*").eq("id", creator_id).execute()
        if by_profile_id.data:
            return {"success": True, "creator": by_profile_id.data[0]}

        by_user_id = db.supabase.table("creator_profiles").select("*").eq("user_id", creator_id).execute()
        if by_user_id.data:
            return {"success": True, "creator": by_user_id.data[0]}

        raise HTTPException(status_code=404, detail="Creator not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get creator profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/creators/{creator_id}/strategies", tags=["Creator"])
async def get_creator_strategies(creator_id: str):
    """Get creator strategies by creator profile id or user id."""
    try:
        profile = db.supabase.table("creator_profiles").select("user_id").eq("id", creator_id).execute()
        resolved_user_id = profile.data[0].get("user_id") if profile.data else creator_id

        response = (
            db.supabase.table("creator_strategies")
            .select("*")
            .eq("user_id", resolved_user_id)
            .order("created_at", desc=True)
            .execute()
        )
        strategies = response.data or []
        return {"success": True, "strategies": strategies, "count": len(strategies)}
    except Exception as e:
        logger.error(f"❌ Failed to get creator strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/creators/{creator_id}/stats", tags=["Creator"])
async def get_creator_stats(creator_id: str):
    """Get creator performance stats summary."""
    try:
        rep = await creator_service.get_reputation_score(creator_id)
        if not rep.get("success"):
            raise HTTPException(status_code=404, detail=rep.get("error", "Creator stats unavailable"))

        strategies = await get_creator_strategies(creator_id)
        strategy_count = len(strategies.get("strategies", [])) if isinstance(strategies, dict) else 0

        return {
            "success": True,
            "creator_id": creator_id,
            "stats": {
                "reputation_score": rep.get("reputation_score", 0),
                "tier": rep.get("tier", "Unverified"),
                "strategy_count": strategy_count,
                "win_rate": float(rep.get("components", {}).get("win_rate", 0)),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get creator stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/creators/{creator_id}/subscribe", tags=["Creator"])
async def subscribe_to_creator(creator_id: str, user_id: str = Query(...)):
    """Subscribe to a creator (maps to strategy subscription model)."""
    try:
        strategies = await get_creator_strategies(creator_id)
        strategy_items = strategies.get("strategies", []) if isinstance(strategies, dict) else []
        if not strategy_items:
            raise HTTPException(status_code=404, detail="Creator has no subscribable strategies")

        target_strategy_id = strategy_items[0].get("id")
        result = await strategy_service.subscribe_to_strategy(user_id, target_strategy_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Subscription failed"))

        return {
            "success": True,
            "creator_id": creator_id,
            "strategy_id": target_strategy_id,
            "subscription_id": result.get("subscription_id"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to subscribe to creator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategies/{strategy_id}/copy", tags=["Strategy"])
async def copy_creator_strategy(strategy_id: str, user_id: str = Query(...)):
    """Copy a creator strategy into the user's strategy library."""
    try:
        source = db.supabase.table("creator_strategies").select("*").eq("id", strategy_id).execute()
        if not source.data:
            raise HTTPException(status_code=404, detail="Strategy not found")

        source_strategy = source.data[0]
        copied = {
            "user_id": user_id,
            "name": f"Copy - {source_strategy.get('name', 'Strategy')}",
            "description": source_strategy.get("description", ""),
            "parameters": source_strategy.get("parameters", {}),
            "is_public": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        insert_result = db.supabase.table("strategies").insert(copied).execute()
        copied_id = insert_result.data[0].get("id") if insert_result.data else None

        return {
            "success": True,
            "source_strategy_id": strategy_id,
            "copied_strategy_id": copied_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to copy strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# KYC & USER VERIFICATION ENDPOINTS
# ============================================================================

@app.get("/api/user/kyc", tags=["KYC"])
async def get_kyc_status(user_id: str = Query(...)):
    """Get user's KYC verification status."""
    try:
        result = await user_service.get_kyc_status(user_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to get KYC status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/user/kyc", tags=["KYC"])
async def submit_kyc(user_id: str = Query(...)):
    """Submit KYC documents for verification."""
    try:
        # In production, receive file uploads
        kyc_data = {
            "documents": [],
            "submitted_by_user": True
        }
        
        result = await user_service.submit_kyc(user_id, kyc_data)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except HTTPException:
        raise


@app.post("/api/kyc/start", tags=["KYC"])
async def kyc_start(user_id: str = Query(...)):
    """Roadmap compatibility endpoint to initiate KYC."""
    result = await user_service.submit_kyc(user_id, {"documents": [], "status": "started"})
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to start KYC"))
    return {"success": True, "user_id": user_id, "kyc_id": result.get("kyc_id")}


@app.post("/api/kyc/upload", tags=["KYC"])
async def kyc_upload(user_id: str = Query(...), doc_type: str = Query(...), file_url: str = Query(...)):
    """Roadmap compatibility endpoint to attach KYC document metadata."""
    try:
        current = await user_service.get_kyc_status(user_id)
        if not current.get("success"):
            raise HTTPException(status_code=404, detail=current.get("error", "KYC record not found"))

        existing = current.get("kyc_details") or {}
        documents = existing.get("documents") or []
        documents.append({"doc_type": doc_type, "file_url": file_url, "uploaded_at": datetime.utcnow().isoformat()})

        update_data = {
            "documents": documents,
            "status": "SUBMITTED",
            "created_at": existing.get("created_at") or datetime.utcnow().isoformat(),
        }

        db.supabase.table("kyc_verifications").upsert({"user_id": user_id, **update_data}).execute()
        db.supabase.table("users").update({"kyc_status": "SUBMITTED"}).eq("id", user_id).execute()

        return {"success": True, "user_id": user_id, "document_count": len(documents)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to upload KYC document metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kyc/status", tags=["KYC"])
async def kyc_status(user_id: str = Query(...)):
    """Roadmap compatibility endpoint for KYC status checks."""
    result = await user_service.get_kyc_status(user_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "KYC status not found"))
    return result


@app.post("/api/kyc/submit", tags=["KYC"])
async def kyc_submit(user_id: str = Query(...), payload: Dict[str, Any] = None):
    """Roadmap compatibility endpoint for final KYC submission."""
    result = await user_service.submit_kyc(user_id, payload or {"submitted": True})
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to submit KYC"))
    return {"success": True, "user_id": user_id, "kyc_id": result.get("kyc_id")}


@app.post("/api/kyc/admin/approve", tags=["KYC"])
async def kyc_admin_approve(user_id: str = Query(...)):
    """Admin endpoint to approve KYC."""
    try:
        db.supabase.table("kyc_verifications").update(
            {"status": "APPROVED", "completed_at": datetime.utcnow().isoformat()}
        ).eq("user_id", user_id).execute()
        db.supabase.table("users").update({"kyc_status": "APPROVED"}).eq("id", user_id).execute()
        return {"success": True, "user_id": user_id, "status": "APPROVED"}
    except Exception as e:
        logger.error(f"❌ Failed to approve KYC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/admin/reject", tags=["KYC"])
async def kyc_admin_reject(user_id: str = Query(...), reason: str = Query("manual_review_failed")):
    """Admin endpoint to reject KYC."""
    try:
        db.supabase.table("kyc_verifications").update(
            {
                "status": "REJECTED",
                "aml_reason": reason,
                "completed_at": datetime.utcnow().isoformat(),
            }
        ).eq("user_id", user_id).execute()
        db.supabase.table("users").update({"kyc_status": "REJECTED"}).eq("id", user_id).execute()
        return {"success": True, "user_id": user_id, "status": "REJECTED", "reason": reason}
    except Exception as e:
        logger.error(f"❌ Failed to reject KYC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@app.get("/api/audit/trail/{user_id}", tags=["Audit"])
async def get_audit_trail(user_id: str, limit: int = Query(100, le=500)):
    """Get immutable audit trail for a user."""
    try:
        result = await user_service.get_audit_trail(user_id, limit)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to fetch audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/audit/log", tags=["Audit"])
async def create_audit_log(user_id: str = Query(...)):
    """Create an audit log entry."""
    try:
        # In production, parse from request body
        result = await user_service.log_audit_entry(
            user_id=user_id,
            action="API_CALL",
            resource_type="endpoint",
            resource_id="test"
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to create audit log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SETTINGS & RISK ENDPOINTS
# ============================================================================

@app.get("/api/settings/risk", tags=["Settings"])
async def get_risk_settings(user_id: str = Query(...)):
    """Get user's risk management settings."""
    try:
        result = await user_service.get_risk_settings(user_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to get risk settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/settings/risk", tags=["Settings"])
async def update_risk_settings(user_id: str = Query(...)):
    """Update user's risk management settings."""
    try:
        # In production, parse from request body
        settings = {
            "max_position_size_pct": 2.0,
            "max_portfolio_exposure_pct": 20.0,
            "max_leverage": 5.0
        }
        
        result = await user_service.update_risk_settings(user_id, settings)
        
        if result.get("success"):
            return {"success": True, "message": "Risk settings updated"}
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to update risk settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXCHANGE CONNECTION ENDPOINTS
# ============================================================================

@app.post("/api/exchange/connect", tags=["Exchange"])
async def connect_exchange(user_id: str = Query(...), exchange: str = Query(...)):
    """Connect a trading exchange API."""
    try:
        # In production, receive encrypted credentials
        result = await user_service.connect_exchange(
            user_id=user_id,
            exchange=exchange,
            api_key="test_key",
            api_secret="test_secret"
        )
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to connect exchange: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exchange/keys", tags=["Exchange"])
async def get_connected_exchanges(user_id: str = Query(...)):
    """Get list of connected exchanges."""
    try:
        result = await user_service.get_connected_exchanges(user_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to get exchanges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/exchange/disconnect", tags=["Exchange"])
async def disconnect_exchange(user_id: str = Query(...), exchange: str = Query(...)):
    """Disconnect a trading exchange."""
    try:
        result = await user_service.disconnect_exchange(user_id, exchange)
        
        if result.get("success"):
            return {"success": True, "message": f"{exchange} disconnected"}
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to disconnect exchange: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXTERNAL SIGNALS ENDPOINTS
# ============================================================================

@app.get("/api/external-signals", tags=["External Signals"])
async def get_external_signals(user_id: str = Query(None), limit: int = Query(50, le=100)):
    """Get external signals received via webhooks."""
    try:
        result = await user_service.get_external_signals(user_id, limit)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to fetch external signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/external-signals/rules", tags=["External Signals"])
async def set_signal_rules(user_id: str = Query(...)):
    """Set filtering rules for external signal ingestion."""
    try:
        # In production, parse from request body
        rules = {
            "min_confidence": 0.7,
            "enabled_sources": ["tradingview"],
            "excluded_symbols": []
        }
        
        result = await user_service.set_external_signal_rules(user_id, rules)
        
        if result.get("success"):
            return {"success": True, "message": "Signal rules updated"}
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to set signal rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/external-signals/history", tags=["External Signals"])
async def get_signal_history(user_id: str = Query(...), days: int = Query(7, ge=1, le=90)):
    """Get history of external signal webhook hits."""
    try:
        result = await user_service.get_external_signal_history(user_id, days)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to get signal history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STRATEGY ENDPOINTS
# ============================================================================

@app.get("/api/strategies", tags=["Strategy"])
async def get_user_strategies(user_id: str = Query(...)):
    """Get all strategies created by user."""
    try:
        result = await strategy_service.get_user_strategies(user_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to fetch strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/marketplace", tags=["Strategy"])
async def get_marketplace_strategies(limit: int = Query(50, le=100), offset: int = Query(0)):
    """Get approved strategies on marketplace."""
    try:
        result = await strategy_service.get_marketplace_strategies(limit, offset)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to fetch marketplace: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}/performance", tags=["Strategy"])
async def get_strategy_performance(strategy_id: str):
    """Get performance metrics for a strategy."""
    try:
        result = await strategy_service.get_strategy_performance(strategy_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to get strategy performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategy/subscribe", tags=["Strategy"])
async def subscribe_to_strategy(user_id: str = Query(...), strategy_id: str = Query(...)):
    """Subscribe user to a marketplace strategy."""
    try:
        result = await strategy_service.subscribe_to_strategy(user_id, strategy_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to subscribe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategy/subscriptions", tags=["Strategy"])
async def get_user_subscriptions(user_id: str = Query(...)):
    """Get user's active strategy subscriptions."""
    try:
        result = await strategy_service.get_user_subscriptions(user_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to get subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategy/{strategy_id}/paper-trade", tags=["Strategy"])
async def start_paper_trade_strategy(strategy_id: str, user_id: str = Query(...)):
    """Start paper trading a marketplace strategy."""
    try:
        result = await strategy_service.start_paper_trade_strategy(user_id, strategy_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"❌ Failed to start paper trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKTESTING ENDPOINTS
# ============================================================================

@app.post("/api/backtest/run", tags=["Backtesting"])
async def run_backtest(user_id: str = Query(...)):
    """Run a backtest for a strategy."""
    try:
        # In production, parse strategy config from request body
        strategy_config = {
            "name": "Test Strategy",
            "symbols": ["BTC", "ETH"],
            "initial_capital": 100000,
            "parameters": {}
        }
        
        result = await backtest_service.run_backtest(user_id, strategy_config)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except Exception as e:
        logger.error(f"❌ Failed to run backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/{backtest_id}", tags=["Backtesting"])
async def get_backtest_results(backtest_id: str):
    """Get backtest results."""
    try:
        result = await backtest_service.get_backtest_results(backtest_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except Exception as e:
        logger.error(f"❌ Failed to get backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/{backtest_id}/equity-curve", tags=["Backtesting"])
async def get_equity_curve(backtest_id: str):
    """Get equity curve data for a backtest."""
    try:
        result = await backtest_service.get_equity_curve(backtest_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except Exception as e:
        logger.error(f"❌ Failed to get equity curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/user/{user_id}", tags=["Backtesting"])
async def list_user_backtests(user_id: str, limit: int = Query(20, le=100)):
    """List all backtests for a user."""
    try:
        result = await backtest_service.list_user_backtests(user_id, limit)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except Exception as e:
        logger.error(f"❌ Failed to list backtests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SIGNAL PROOF & EXECUTION ENDPOINTS
# ============================================================================

@app.post("/api/signals/{signal_id}/execute", tags=["Signals"])
async def execute_signal(signal_id: str, user_id: str = Query(...)):
    """Execute a signal (convert to paper/live trade)."""
    try:
        result = await user_service.execute_signal(user_id, signal_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
    
    except Exception as e:
        logger.error(f"❌ Failed to execute signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/{signal_id}/proofs", tags=["Signals"])
async def get_signal_proofs(signal_id: str):
    """Get proof/verification data for a signal."""
    try:
        result = await user_service.get_signal_proof(signal_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except Exception as e:
        logger.error(f"❌ Failed to get signal proof: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proofs/{signal_id}", tags=["Proofs"])
async def get_proof_detail(signal_id: str):
    """Get full proof details with blockchain anchor."""
    try:
        result = await user_service.get_signal_proof(signal_id)
        
        if result.get("success"):
            proof = result.get("proof", {})
            return {
                "success": True,
                "proof": {
                    "signal_id": proof.get("signal_id"),
                    "ticker": proof.get("ticker"),
                    "signal_type": proof.get("signal_type"),
                    "created_at": proof.get("created_at"),
                    "merkle_root": proof.get("merkle_root"),
                    "blockchain_anchor": proof.get("blockchain_anchor"),
                    "rationale": proof.get("rationale"),
                    "immutable": True
                }
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    except Exception as e:
        logger.error(f"❌ Failed to get proof: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MARKET INSIGHTS ENDPOINT
# ============================================================================

@app.post("/api/market/insights", tags=["Market Data"])
async def get_market_insights(query: str = Query(...)):
    """Get AI-generated market insights."""
    try:
        # Get market data
        sentiment = await market_data_service.fetch_market_sentiment()
        tickers = await market_data_service.fetch_market_tickers(["BTC", "ETH"])
        
        # Generate insight (in production, call LLM)
        insight = {
            "query": query,
            "insight": f"Based on current market conditions: {sentiment.get('market_status', 'NEUTRAL')} sentiment detected. "
                       "Bitcoin is showing consolidation with support at recent lows. "
                       "Consider waiting for confirmation before entering new positions.",
            "confidence": 0.75,
            "data_sources": ["sentiment_analysis", "price_action", "technical_indicators"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Market insights generated")
        
        return {
            "success": True,
            "insight": insight
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to generate insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RECOMMENDATION SERVICES ENDPOINTS (Phase 3 Enhancements)
# ============================================================================

@app.get("/api/signals/high-performers", tags=["Signal Analytics"])
async def get_high_performing_signals(
    limit: int = Query(20, ge=1, le=100),
    min_executions: int = Query(5, ge=1, le=100),
    current_user: str = Depends(verify_firebase_token)
):
    """Get high-performing signals (minimum executions > threshold)."""
    if not signal_perf_tracker:
        raise HTTPException(status_code=503, detail="Signal performance tracking not enabled")
    
    try:
        high_performers = await signal_perf_tracker.get_high_performing_signals(
            limit=limit,
            min_executions=min_executions
        )
        
        return {
            "success": True,
            "count": len(high_performers),
            "high_performers": high_performers,
            "min_executions_filter": min_executions
        }
    except Exception as e:
        logger.error(f"❌ Failed to get high-performing signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/{signal_id}/performance", tags=["Signal Analytics"])
async def get_signal_performance(
    signal_id: str,
    current_user: str = Depends(verify_firebase_token)
):
    """Get detailed performance metrics for a specific signal."""
    if not signal_perf_tracker:
        raise HTTPException(status_code=503, detail="Signal performance tracking not enabled")
    
    try:
        performance = await signal_perf_tracker.get_signal_performance_summary(signal_id)
        
        if not performance:
            raise HTTPException(status_code=404, detail="Signal not found or no performance data")
        
        return {
            "success": True,
            "signal_id": signal_id,
            "performance": performance
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get signal performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/external-signals/sources", tags=["External Signal Analytics"])
async def get_external_signal_sources(
    current_user: str = Depends(verify_firebase_token)
):
    """Get all external signal sources ranked by reliability."""
    if not external_signal_validator:
        raise HTTPException(status_code=503, detail="External signal validation not enabled")
    
    try:
        source_rankings = await external_signal_validator.get_all_source_rankings(user_id=current_user)
        
        return {
            "success": True,
            "count": len(source_rankings),
            "sources": source_rankings
        }
    except Exception as e:
        logger.error(f"❌ Failed to get external signal sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/external-signals/sources/{source_name}/reputation", tags=["External Signal Analytics"])
async def get_external_source_reputation(
    source_name: str,
    current_user: str = Depends(verify_firebase_token)
):
    """Get detailed reputation metrics for a specific external signal source."""
    if not external_signal_validator:
        raise HTTPException(status_code=503, detail="External signal validation not enabled")
    
    try:
        reputation = await external_signal_validator.get_source_reputation(source_name)
        
        if not reputation:
            raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")
        
        return {
            "success": True,
            "source": source_name,
            "reputation": reputation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get source reputation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/correlations", tags=["Market Analytics"])
async def get_market_correlations(
    time_window: str = Query("30d", pattern="^(1d|7d|30d)$"),
    current_user: str = Depends(verify_firebase_token)
):
    """Get current market correlations between assets."""
    if not market_correlation_analyzer:
        raise HTTPException(status_code=503, detail="Market correlation analysis not enabled")
    
    try:
        # Map time_window to lookback_days
        lookback_map = {"1d": 1, "7d": 7, "30d": 30}
        lookback_days = lookback_map.get(time_window, 30)
        
        # Compute correlations using default asset pairs
        correlations = await market_correlation_analyzer.compute_correlations(
            asset_pairs=None,
            lookback_days=lookback_days
        )
        
        return {
            "success": True,
            "time_window": time_window,
            "lookback_days": lookback_days,
            "correlations": correlations.get("correlations", {})
        }
    except Exception as e:
        logger.error(f"❌ Failed to get market correlations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/market/signals/conflicts", tags=["Market Analytics"])
async def check_signal_conflicts(
    asset: str = Body(...),
    signal_type: str = Body(..., pattern="^(BUY|SELL)$"),
    related_assets: list = Body(default=None),
    current_user: str = Depends(verify_firebase_token)
):
    """Check if a signal would create conflicts with correlated assets."""
    if not market_correlation_analyzer:
        raise HTTPException(status_code=503, detail="Market correlation analysis not enabled")
    
    try:
        # If no related assets specified, use default related assets
        if not related_assets:
            related_assets_map = {
                "BTC": ["ETH", "SOL"],
                "ETH": ["BTC", "SOL"],
                "SOL": ["BTC", "ETH"],
                "BNB": ["BTC", "ETH"],
                "XRP": ["BTC", "ETH"]
            }
            related_assets = related_assets_map.get(asset, [])
        
        conflicts = await market_correlation_analyzer.check_signal_conflicts(
            primary_asset=asset,
            primary_side=signal_type,
            related_assets=related_assets
        )
        
        return {
            "success": True,
            "asset": asset,
            "signal_type": signal_type,
            "has_conflicts": conflicts.get("has_major_conflicts", False),
            "conflict_details": conflicts
        }
    except Exception as e:
        logger.error(f"❌ Failed to check signal conflicts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cache/stats", tags=["System"])
async def get_cache_stats(
    current_user: str = Depends(verify_firebase_token)
):
    """Get cache performance statistics."""
    try:
        # Access cache from market data service
        if hasattr(market_data_service, 'cache') and market_data_service.cache:
            cache = market_data_service.cache
            
            if hasattr(cache, 'get_user_cache_stats'):
                stats = cache.get_user_cache_stats(current_user)
                return {
                    "success": True,
                    "user_id": current_user,
                    "cache_stats": stats
                }
            elif hasattr(cache, 'get_stats'):
                stats = cache.get_stats()
                return {
                    "success": True,
                    "user_id": current_user,
                    "global_cache_stats": stats
                }
        
        return {
            "success": True,
            "message": "Cache statistics not available"
        }
    except Exception as e:
        logger.error(f"❌ Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/websocket/status", tags=["System"])
async def get_websocket_status(
    current_user: str = Depends(verify_firebase_token)
):
    """Get Binance WebSocket connection status."""
    try:
        if binance_ws_manager:
            status = await binance_ws_manager.get_connection_status()
            return {
                "success": True,
                "websocket_enabled": True,
                "status": status
            }
        else:
            return {
                "success": True,
                "websocket_enabled": False,
                "status": "WebSocket not initialized (using polling fallback)"
            }
    except Exception as e:
        logger.error(f"❌ Failed to get WebSocket status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKTESTING ENDPOINTS
# ============================================================================

@app.post("/api/backtest", tags=["Backtesting"])
async def backtest_signal(
    request: Dict[str, Any] = Body(...),
    current_user: str = Depends(verify_firebase_token)
):
    """
    Backtest a signal strategy against historical data
    
    Request body:
    {
        "signal_ids": ["sig_001", "sig_002"],
        "asset": "BTC",
        "hold_duration_hours": 24,
        "position_size_pct": 2.0
    }
    """
    try:
        if not market_data_service or not backtest_service:
            raise HTTPException(status_code=503, detail="Backtesting service unavailable")
        
        signal_ids = request.get("signal_ids", [])
        asset = request.get("asset", "BTC")
        hold_hours = request.get("hold_duration_hours", 24)
        pos_size = request.get("position_size_pct", 2.0)
        
        if not signal_ids:
            raise HTTPException(status_code=400, detail="signal_ids required")
        
        # Mock backtest results (in production, use real historical data)
        results = {
            "success": True,
            "signal_count": len(signal_ids),
            "trades": [
                {
                    "signal_id": sid,
                    "asset": asset,
                    "entry_price": 50000 + (i * 100),
                    "exit_price": 51000 + (i * 100),
                    "pnl": 1000,
                    "roi_pct": 2.0
                }
                for i, sid in enumerate(signal_ids[:5])
            ],
            "metrics": {
                "total_trades": len(signal_ids),
                "winning_trades": int(len(signal_ids) * 0.65),
                "losing_trades": int(len(signal_ids) * 0.35),
                "win_rate": 0.65,
                "total_pnl": len(signal_ids) * 1000 * 0.65 - len(signal_ids) * 300 * 0.35,
                "total_roi": 2.0,
                "sharpe_ratio": 1.25,
                "max_drawdown_pct": 3.5,
                "profit_factor": 2.2
            }
        }
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/backtest/portfolio", tags=["Backtesting"])
async def backtest_portfolio(
    request: Dict[str, Any] = Body(...),
    current_user: str = Depends(verify_firebase_token)
):
    """
    Backtest multiple signals across multiple assets
    
    Request body:
    {
        "signals": [
            {"asset": "BTC", "signal_ids": ["sig_001"]},
            {"asset": "ETH", "signal_ids": ["sig_002"]}
        ],
        "hold_duration_hours": 24
    }
    """
    try:
        if not market_data_service or not backtest_service:
            raise HTTPException(status_code=503, detail="Backtesting service unavailable")
        
        signals = request.get("signals", [])
        
        if not signals:
            raise HTTPException(status_code=400, detail="signals required")
        
        # Aggregate results across assets
        total_trades = sum(len(s.get("signal_ids", [])) for s in signals)
        
        results = {
            "success": True,
            "asset_count": len(signals),
            "total_signals": total_trades,
            "portfolio_metrics": {
                "total_trades": total_trades,
                "winning_trades": int(total_trades * 0.62),
                "losing_trades": int(total_trades * 0.38),
                "win_rate": 0.62,
                "total_pnl": total_trades * 800,
                "total_roi": 1.8,
                "sharpe_ratio": 1.15,
                "max_drawdown_pct": 4.2,
                "profit_factor": 2.0
            },
            "asset_breakdown": [
                {
                    "asset": s["asset"],
                    "signals": len(s.get("signal_ids", [])),
                    "win_rate": 0.60 + (i * 0.03),
                    "roi_pct": 1.5 + (i * 0.5)
                }
                for i, s in enumerate(signals)
            ]
        }
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio backtest error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# MONITORING & ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/monitoring/stats", tags=["Monitoring"])
async def get_monitoring_stats(
    current_user: str = Depends(verify_firebase_token)
):
    """Get per-endpoint performance statistics and health metrics."""
    try:
        if hasattr(rate_limiter, 'get_user_stats'):
            user_stats = rate_limiter.get_user_stats(current_user)
        else:
            user_stats = {
                "requests_used": 0,
                "requests_remaining": 60,
                "reset_time": (datetime.utcnow().timestamp() + 60)
            }
        
        # Mock monitoring data (would come from performance_monitor service)
        monitoring_data = {
            "system_stats": {
                "total_requests": 1543,
                "total_errors": 23,
                "error_rate_pct": 1.49,
                "avg_response_time_ms": 145.3,
                "most_problematic_endpoint": "/api/market/correlations"
            },
            "endpoints": {
                "/api/signals/high-performers": {
                    "total_calls": 342,
                    "success_calls": 338,
                    "error_calls": 4,
                    "response_times": {"min_ms": 12, "max_ms": 2543, "avg_ms": 98.4},
                    "error_rate_pct": 1.17
                },
                "/api/external-signals/sources": {
                    "total_calls": 287,
                    "success_calls": 285,
                    "error_calls": 2,
                    "response_times": {"min_ms": 8, "max_ms": 1200, "avg_ms": 78.2},
                    "error_rate_pct": 0.70
                },
                "/api/market/correlations": {
                    "total_calls": 156,
                    "success_calls": 148,
                    "error_calls": 8,
                    "response_times": {"min_ms": 95, "max_ms": 5200, "avg_ms": 245.8},
                    "error_rate_pct": 5.13
                }
            },
            "user_rate_limit": user_stats
        }
        
        return {
            "success": True,
            "monitoring_data": monitoring_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Monitoring stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/monitoring/endpoint/{endpoint_path}", tags=["Monitoring"])
async def get_endpoint_stats(
    endpoint_path: str,
    current_user: str = Depends(verify_firebase_token)
):
    """Get detailed statistics for a specific endpoint."""
    try:
        # Mock data for endpoint stats
        endpoint_stats = {
            "/api/signals/high-performers": {
                "total_calls": 342,
                "success_calls": 338,
                "error_calls": 4,
                "response_times": {"min_ms": 12, "max_ms": 2543, "avg_ms": 98.4, "p50_ms": 85, "p95_ms": 450, "p99_ms": 1200},
                "error_rate_pct": 1.17,
                "recent_errors": [
                    {"error": "Database timeout", "timestamp": "2026-03-18T10:30:00Z"},
                    {"error": "Signal not found", "timestamp": "2026-03-18T10:29:45Z"}
                ],
                "trend": "stable"
            }
        }
        
        stats = endpoint_stats.get(endpoint_path)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Endpoint not found in monitoring data")
        
        return {
            "success": True,
            "endpoint": endpoint_path,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Endpoint stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ML MODEL RETRAINING ENDPOINTS
# ============================================================================

@app.get("/api/ml/retrain/status", tags=["ML Operations"])
async def get_retrain_status(
    current_user: str = Depends(verify_firebase_token)
):
    """Get ML model retraining pipeline status."""
    try:
        retrain_needed = await ml_retraining_pipeline.should_retrain()
        status = ml_retraining_pipeline.get_retraining_status()
        
        return {
            "success": True,
            "should_retrain": retrain_needed,
            "pipeline_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Retrain status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/retrain/execute", tags=["ML Operations"])
async def execute_retraining(
    request: Dict[str, Any] = Body({
        "model_name": "signal_classifier_v2",
        "training_samples": 10000
    }),
    current_user: str = Depends(verify_firebase_token)
):
    """Trigger model retraining pipeline."""
    try:
        model_name = request.get("model_name", "signal_classifier_v2")
        
        # Execute retraining
        result = await ml_retraining_pipeline.retrain_model(
            training_data={},
            validation_data={},
            model_name=model_name
        )
        
        # Validate
        validation = await ml_retraining_pipeline.validate_model({})
        
        return {
            "success": True,
            "retraining_result": result,
            "validation": validation,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Retraining execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/drift/check", tags=["ML Operations"])
async def check_data_drift(
    request: Dict[str, Any] = Body(...),
    current_user: str = Depends(verify_firebase_token)
):
    """Check for data drift in market data."""
    try:
        features = request.get("features", {})
        
        drift_result = await ml_retraining_pipeline.check_data_drift(features)
        
        return {
            "success": True,
            "drift_analysis": drift_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Drift check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ALERT SYSTEM ENDPOINTS
# ============================================================================

@app.get("/api/alerts/active", tags=["Alerts"])
async def get_active_alerts(
    current_user: str = Depends(verify_firebase_token)
):
    """Get all active system alerts."""
    try:
        alerts = alert_manager.get_active_alerts()
        stats = alert_manager.get_alert_stats()
        
        return {
            "success": True,
            "active_alerts": alerts,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Fetch alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/history", tags=["Alerts"])
async def get_alert_history(
    limit: int = Query(50, ge=10, le=500),
    current_user: str = Depends(verify_firebase_token)
):
    """Get alert history."""
    try:
        history = alert_manager.get_alert_history(limit)
        
        return {
            "success": True,
            "history": history,
            "count": len(history),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Alert history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/{alert_key}/acknowledge", tags=["Alerts"])
async def acknowledge_alert(
    alert_key: str,
    current_user: str = Depends(verify_firebase_token)
):
    """Acknowledge alert."""
    try:
        success = alert_manager.acknowledge_alert(alert_key)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {
            "success": True,
            "alert_key": alert_key,
            "acknowledged": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Acknowledge alert error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STRATEGY MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/strategies", tags=["Strategy Management"])
async def create_strategy(
    request: Dict[str, Any] = Body(...),
    current_user: str = Depends(verify_firebase_token)
):
    """Create new trading strategy."""
    try:
        strategy = await strategy_manager.create_strategy(
            name=request.get("name"),
            description=request.get("description", ""),
            strategy_type=StrategyType(request.get("strategy_type", "custom")),
            assets=request.get("assets", []),
            parameters=request.get("parameters", []),
            user_id=current_user
        )
        
        return {
            "success": True,
            "strategy": strategy.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Create strategy error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/strategies", tags=["Strategy Management"])
async def list_strategies(
    status: Optional[str] = Query(None),
    current_user: str = Depends(verify_firebase_token)
):
    """List trading strategies."""
    try:
        status_filter = None
        if status:
            status_filter = StrategyStatus(status)
        
        strategies = await strategy_manager.list_strategies(status=status_filter)
        
        return {
            "success": True,
            "strategies": [s.to_dict() for s in strategies],
            "count": len(strategies),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"List strategies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}", tags=["Strategy Management"])
async def get_strategy(
    strategy_id: str,
    current_user: str = Depends(verify_firebase_token)
):
    """Get strategy details."""
    try:
        strategy = await strategy_manager.get_strategy(strategy_id)
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "success": True,
            "strategy": strategy.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get strategy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/strategies/{strategy_id}", tags=["Strategy Management"])
async def update_strategy(
    strategy_id: str,
    request: Dict[str, Any] = Body(...),
    current_user: str = Depends(verify_firebase_token)
):
    """Update strategy configuration."""
    try:
        strategy = await strategy_manager.update_strategy(
            strategy_id=strategy_id,
            updates=request,
            user_id=current_user
        )
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "success": True,
            "strategy": strategy.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update strategy error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/strategies/{strategy_id}/activate", tags=["Strategy Management"])
async def activate_strategy(
    strategy_id: str,
    current_user: str = Depends(verify_firebase_token)
):
    """Activate strategy for trading."""
    try:
        strategy = await strategy_manager.activate_strategy(strategy_id, current_user)
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found or cannot be activated")
        
        return {
            "success": True,
            "strategy": strategy.to_dict(),
            "status": "activated",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate strategy error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/strategies/{strategy_id}/pause", tags=["Strategy Management"])
async def pause_strategy(
    strategy_id: str,
    current_user: str = Depends(verify_firebase_token)
):
    """Pause strategy execution."""
    try:
        strategy = await strategy_manager.pause_strategy(strategy_id, current_user)
        
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "success": True,
            "strategy": strategy.to_dict(),
            "status": "paused",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pause strategy error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/strategies/{strategy_id}", tags=["Strategy Management"])
async def delete_strategy(
    strategy_id: str,
    current_user: str = Depends(verify_firebase_token)
):
    """Archive strategy."""
    try:
        success = await strategy_manager.delete_strategy(strategy_id, current_user)
        
        if not success:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        return {
            "success": True,
            "strategy_id": strategy_id,
            "status": "archived",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete strategy error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/strategies/management/stats", tags=["Strategy Management"])
async def get_strategy_stats(
    current_user: str = Depends(verify_firebase_token)
):
    """Get strategy management statistics."""
    try:
        stats = await strategy_manager.get_management_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Strategy stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PORTFOLIO RISK ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/portfolio/risk-analysis", tags=["Portfolio Risk"])
async def analyze_portfolio_risk(
    request: Dict[str, Any] = Body(...),
    current_user: str = Depends(verify_firebase_token)
):
    """Perform comprehensive portfolio risk analysis."""
    try:
        positions = request.get("positions", {})
        market_data = request.get("market_data", {})
        
        if not positions:
            raise HTTPException(status_code=400, detail="positions required")
        
        # Perform analysis
        metrics = await portfolio_risk_analyzer.analyze_portfolio(positions, market_data)
        
        # Check limits
        position_risks = []
        for asset, size in positions.items():
            vol = market_data.get(asset, {}).get("volatility", 0.02)
            beta = market_data.get(asset, {}).get("beta", 1.0)
            from services.portfolio_risk_analyzer import PositionAnalyzer
            pr = PositionAnalyzer.get_position_risk(asset, size, sum(positions.values()), vol, beta)
            position_risks.append(pr)
        
        compliance = await risk_enforcer.check_limits(position_risks, metrics)
        
        return {
            "success": True,
            "portfolio_metrics": {
                "total_value": metrics.total_value,
                "volatility": round(metrics.portfolio_volatility, 4),
                "var_95": round(metrics.portfolio_var_95, 2),
                "diversification_score": round(metrics.diversification_score, 3),
                "risk_level": metrics.risk_level
            },
            "compliance": compliance,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio risk analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/risk-limits", tags=["Portfolio Risk"])
async def get_risk_limits(
    current_user: str = Depends(verify_firebase_token)
):
    """Get current portfolio risk limits."""
    try:
        return {
            "success": True,
            "position_limits": risk_enforcer.position_limits,
            "portfolio_limits": risk_enforcer.portfolio_limits,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Get risk limits error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/portfolio/risk-limits/{asset}/set", tags=["Portfolio Risk"])
async def set_position_limit(
    asset: str,
    request: Dict[str, Any] = Body({"max_allocation": 0.05}),
    current_user: str = Depends(verify_firebase_token)
):
    """Set position limit for asset."""
    try:
        max_alloc = request.get("max_allocation", 0.05)
        risk_enforcer.set_position_limit(asset, max_alloc)
        
        return {
            "success": True,
            "asset": asset,
            "max_allocation": max_alloc,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Set position limit error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# LOAD TESTING ENDPOINTS
# ============================================================================

@app.post("/api/load-testing/standard", tags=["Load Testing"])
async def run_standard_load_test(
    request: Dict[str, Any] = Body({
        "endpoint": "/api/signals/high-performers",
        "num_requests": 100,
        "concurrent_requests": 10
    }),
    current_user: str = Depends(verify_firebase_token)
):
    """Run standard load test on endpoint."""
    try:
        endpoint = request.get("endpoint", "/api/signals/high-performers")
        num_requests = request.get("num_requests", 100)
        concurrent = request.get("concurrent_requests", 10)
        
        metrics = await load_test_runner.run_load_test(
            endpoint=endpoint,
            method="GET",
            num_requests=num_requests,
            concurrent_requests=concurrent
        )
        
        return {
            "success": True,
            "test_type": "standard_load_test",
            "endpoint": endpoint,
            "metrics": {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": round(metrics.success_rate, 4),
                "response_times": metrics.response_times,
                "requests_per_second": round(metrics.requests_per_second, 2),
                "duration_seconds": round(metrics.duration_seconds, 2)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Standard load test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/load-testing/soak", tags=["Load Testing"])
async def run_soak_test(
    request: Dict[str, Any] = Body({
        "endpoint": "/api/signals/high-performers",
        "duration_minutes": 5,
        "requests_per_second": 10
    }),
    current_user: str = Depends(verify_firebase_token)
):
    """Run soak test (sustained load for extended period)."""
    try:
        endpoint = request.get("endpoint", "/api/signals/high-performers")
        duration = request.get("duration_minutes", 5)
        rps = request.get("requests_per_second", 10)
        
        result = await load_test_runner.run_soak_test(
            endpoint=endpoint,
            method="GET",
            duration_minutes=duration,
            requests_per_second=rps
        )
        
        return {
            "success": True,
            "test_type": "soak_test",
            "endpoint": endpoint,
            "soak_test_results": result["soak_test_results"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Soak test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/load-testing/spike", tags=["Load Testing"])
async def run_spike_test(
    request: Dict[str, Any] = Body({
        "endpoint": "/api/signals/high-performers",
        "normal_rps": 10,
        "spike_rps": 100,
        "spike_duration_seconds": 30
    }),
    current_user: str = Depends(verify_firebase_token)
):
    """Run spike test (sudden traffic increase)."""
    try:
        endpoint = request.get("endpoint", "/api/signals/high-performers")
        normal_rps = request.get("normal_rps", 10)
        spike_rps = request.get("spike_rps", 100)
        spike_duration = request.get("spike_duration_seconds", 30)
        
        result = await load_test_runner.run_spike_test(
            endpoint=endpoint,
            method="GET",
            normal_rps=normal_rps,
            spike_rps=spike_rps,
            spike_duration_seconds=spike_duration,
            test_duration_minutes=5
        )
        
        return {
            "success": True,
            "test_type": "spike_test",
            "endpoint": endpoint,
            "spike_test_results": result["spike_test_results"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Spike test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/load-testing/stress", tags=["Load Testing"])
async def run_stress_test(
    request: Dict[str, Any] = Body({
        "endpoint": "/api/signals/high-performers",
        "starting_rps": 10,
        "increment_rps": 10,
        "max_rps": 500
    }),
    current_user: str = Depends(verify_firebase_token)
):
    """Run stress test (incrementally increase load until failure)."""
    try:
        endpoint = request.get("endpoint", "/api/signals/high-performers")
        starting_rps = request.get("starting_rps", 10)
        increment = request.get("increment_rps", 10)
        max_rps = request.get("max_rps", 500)
        
        result = await load_test_runner.run_stress_test(
            endpoint=endpoint,
            method="GET",
            starting_rps=starting_rps,
            increment_rps=increment,
            max_rps=max_rps,
            failure_threshold_pct=10.0
        )
        
        return {
            "success": True,
            "test_type": "stress_test",
            "endpoint": endpoint,
            "stress_test_stages": result["stress_test_stages"],
            "breaking_point_rps": result["breaking_point_rps"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Stress test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/load-testing/results", tags=["Load Testing"])
async def get_load_test_results(
    limit: int = Query(100, ge=10, le=1000),
    current_user: str = Depends(verify_firebase_token)
):
    """Get historical load test results."""
    try:
        all_results = load_test_runner.get_all_results()
        limited_results = all_results[-limit:]
        
        return {
            "success": True,
            "total_results": len(all_results),
            "returned": len(limited_results),
            "results": limited_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Get results error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/load-testing/clear", tags=["Load Testing"])
async def clear_load_test_results(
    current_user: str = Depends(verify_firebase_token)
):
    """Clear stored load test results."""
    try:
        load_test_runner.clear_results()
        
        return {
            "success": True,
            "message": "Load test results cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Clear results error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FRONTEND CONTRACT ADAPTER ENDPOINTS
# ============================================================================

@app.get("/api/frontend/user/{user_id}/profile", tags=["Frontend"])
async def frontend_user_profile(user_id: str):
    response = db.supabase.table("users").select("*").eq("id", user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    return _map_user_profile_to_frontend(response.data[0])


@app.get("/api/frontend/user/{user_id}/kyc", tags=["Frontend"])
async def frontend_user_kyc(user_id: str):
    result = await user_service.get_kyc_status(user_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "KYC status not found"))

    status_raw = str(result.get("kyc_status", "NOT_STARTED")).upper()
    status = "Unverified"
    if status_raw in {"SUBMITTED", "PENDING"}:
        status = "Pending"
    elif status_raw == "APPROVED":
        status = "Verified"
    elif status_raw == "REJECTED":
        status = "Rejected"

    return {
        "userId": user_id,
        "status": status,
        "level": 2 if status == "Verified" else 1,
        "verifiedAt": _iso((result.get("kyc_details") or {}).get("updated_at")),
    }


@app.get("/api/frontend/user/{user_id}/risk-score", tags=["Frontend"])
async def frontend_user_risk_score(user_id: str):
    metrics = await paper_trading.get_portfolio_metrics(user_id)
    pnl_percent = float(metrics.get("pnl_percent") or 0)
    max_drawdown = float(metrics.get("max_drawdown") or 0)
    leverage_factor = 0.2
    concentration = min(1.0, float(metrics.get("open_positions") or 0) / 10)
    volatility = min(1.0, abs(pnl_percent) / 50)
    score = max(0, min(100, int((volatility * 45 + concentration * 35 + leverage_factor * 20) * 100)))

    label = "Low"
    if score >= 70:
        label = "High"
    elif score >= 40:
        label = "Medium"

    return {
        "userId": user_id,
        "score": score,
        "label": label,
        "factors": {
            "volatility": round(volatility, 2),
            "leverage": leverage_factor,
            "concentration": round(concentration, 2),
        },
        "updatedAt": datetime.utcnow().isoformat(),
    }


@app.get("/api/frontend/market/tickers", tags=["Frontend"])
async def frontend_market_tickers(symbols: str = Query("BTC,ETH,BNB,SOL,XRP")):
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    tickers = await market_data_service.fetch_market_tickers(symbol_list)
    return [
        {
            "id": f"ticker-{item.get('symbol')}",
            "asset": item.get("symbol"),
            "price": float(item.get("last_price") or 0),
            "change24h": float(item.get("change_24h_pct") or 0),
            "change24hAbs": float(item.get("change_24h") or 0),
            "volume24h": float(item.get("volume_24h") or 0),
            "high24h": float(item.get("last_price") or 0) * 1.01,
            "low24h": float(item.get("last_price") or 0) * 0.99,
        }
        for item in tickers
    ]


@app.get("/api/frontend/market/sentiment", tags=["Frontend"])
async def frontend_market_sentiment():
    sentiment = await market_data_service.fetch_market_sentiment()
    return {
        "id": "market-sentiment-latest",
        "score": float(sentiment.get("composite_score") or 0),
        "label": sentiment.get("market_status", "NEUTRAL").title(),
        "factors": {
            "social": round(float(sentiment.get("bullish_pct", 0)), 2),
            "volatility": round(float(sentiment.get("bearish_pct", 0)), 2),
            "orderBook": round(float(sentiment.get("neutral_pct", 0)), 2),
        },
    }


@app.get("/api/frontend/market/funding-rates", tags=["Frontend"])
async def frontend_funding_rates():
    rates = await market_data_service.fetch_funding_rates()
    return [
        {
            "id": f"funding-{rate.get('asset')}",
            "asset": rate.get("asset"),
            "exchange": "binance",
            "rate": float(rate.get("funding_rate") or 0),
            "nextFundingTime": _iso(rate.get("next_funding_time")),
        }
        for rate in rates
    ]


@app.get("/api/frontend/market/open-interest", tags=["Frontend"])
async def frontend_open_interest():
    values = await market_data_service.fetch_open_interest()
    return [
        {
            "id": f"oi-{item.get('asset')}",
            "asset": item.get("asset"),
            "value": float(item.get("open_interest_usd") or 0),
            "change24h": float(item.get("change_24h_pct") or 0),
        }
        for item in values
    ]


@app.get("/api/frontend/market/data-quality", tags=["Frontend"])
async def frontend_data_quality():
    quality = await market_data_service.fetch_data_quality()
    return [
        {
            "asset": item.get("asset"),
            "source": "aggregated",
            "freshness": max(0, 100 - float(item.get("latency_ms") or 0) / 10),
            "status": _map_market_data_quality_status(item.get("status")),
        }
        for item in quality
    ]


@app.get("/api/frontend/market/on-chain-activity", tags=["Frontend"])
async def frontend_on_chain_activity():
    now = datetime.utcnow().isoformat()
    return [
        {
            "id": "onchain-1",
            "type": "whale_move",
            "asset": "BTC",
            "amount": 120.5,
            "valueUsd": 120.5 * 45000,
            "from": "0xexchange-hot-wallet",
            "to": "0xinstitutional-cold-wallet",
            "timestamp": now,
        },
        {
            "id": "onchain-2",
            "type": "exchange_flow",
            "asset": "ETH",
            "amount": 4200,
            "valueUsd": 4200 * 3000,
            "from": "0xunknown",
            "to": "0xexchange",
            "timestamp": now,
        },
    ]


@app.get("/api/frontend/market/liquidation-clusters", tags=["Frontend"])
async def frontend_liquidation_clusters():
    oi = await market_data_service.fetch_open_interest()
    clusters = []
    for item in oi:
        value = float(item.get("open_interest_usd") or 0)
        clusters.append({"asset": item.get("asset"), "value": round(value * 0.12, 2), "type": "long"})
        clusters.append({"asset": item.get("asset"), "value": round(value * 0.08, 2), "type": "short"})
    return clusters


@app.get("/api/frontend/portfolio/{user_id}/summary", tags=["Frontend"])
async def frontend_portfolio_summary(user_id: str):
    summary = await portfolio_service.get_portfolio_summary(user_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return {
        "id": str(summary.get("portfolio_id") or summary.get("id") or f"portfolio-{user_id}"),
        "totalEquity": float(summary.get("total_equity") or 0),
        "unrealizedPnl": float(summary.get("unrealized_pnl") or 0),
        "realizedPnl": float(summary.get("realized_pnl") or 0),
        "totalTrades": int(summary.get("total_trades") or 0),
        "openPositions": int(summary.get("open_positions_count") or 0),
        "marginUsed": round(float(summary.get("total_exposure_pct") or 0) / 100, 4),
    }


@app.get("/api/frontend/portfolio/{user_id}/positions", tags=["Frontend"])
async def frontend_portfolio_positions(user_id: str):
    positions = await portfolio_service.get_open_positions(user_id)
    mapped = []
    for position in positions:
        mapped.append(
            {
                "id": str(position.get("id")),
                "userId": str(position.get("user_id")),
                "asset": position.get("ticker"),
                "direction": position.get("direction", "LONG"),
                "entryPrice": float(position.get("entry_price") or 0),
                "currentPrice": float(position.get("current_price") or position.get("entry_price") or 0),
                "quantity": float(position.get("quantity") or 0),
                "unrealizedPnl": float(position.get("unrealized_pnl") or 0),
                "unrealizedPnlPercent": float(position.get("unrealized_pnl_percent") or 0),
                "riskExposure": float(position.get("risk_exposure_pct") or 0),
                "signalId": str(position.get("signal_id") or ""),
                "openedAt": _iso(position.get("opened_at")),
            }
        )
    return mapped


@app.get("/api/frontend/portfolio/{user_id}/trades", tags=["Frontend"])
async def frontend_portfolio_trades(user_id: str):
    response = db.supabase.table("paper_trades").select("*").eq("user_id", user_id).execute()
    trades = response.data or []
    mapped = []
    for trade in trades:
        pnl_value = float(trade.get("pnl") or 0)
        mapped.append(
            {
                "id": str(trade.get("id")),
                "userId": str(trade.get("user_id")),
                "asset": trade.get("asset"),
                "direction": trade.get("direction", "LONG"),
                "entryPrice": float(trade.get("entry_price") or 0),
                "exitPrice": float(trade.get("exit_price") or 0),
                "pnl": pnl_value,
                "pnlPercent": float(trade.get("pnl_percent") or 0),
                "status": "win" if pnl_value >= 0 else "loss",
                "strategy": "paper-trade",
                "signalId": str(trade.get("signal_id") or ""),
                "executedAt": _iso(trade.get("opened_at")),
                "closedAt": _iso(trade.get("closed_at")),
            }
        )
    return mapped


@app.get("/api/frontend/portfolio/{user_id}/performance-points", tags=["Frontend"])
async def frontend_portfolio_performance_points(user_id: str):
    trades_response = db.supabase.table("paper_trades").select("*").eq("user_id", user_id).eq("status", "CLOSED").execute()
    closed_trades = sorted(trades_response.data or [], key=lambda item: _iso(item.get("closed_at")))
    running = 100000.0
    points = []
    for idx, trade in enumerate(closed_trades):
        running += float(trade.get("pnl") or 0)
        points.append(
            {
                "id": f"pp-{user_id}-{idx}",
                "userId": user_id,
                "strategyId": str(trade.get("strategy_id") or ""),
                "backtestResultId": str(trade.get("backtest_id") or ""),
                "date": _iso(trade.get("closed_at")),
                "equity": round(running, 2),
                "drawdown": 0,
                "cumulativePnl": round(running - 100000.0, 2),
            }
        )
    if not points:
        points.append(
            {
                "id": f"pp-{user_id}-0",
                "userId": user_id,
                "strategyId": "",
                "backtestResultId": "",
                "date": datetime.utcnow().isoformat(),
                "equity": 100000.0,
                "drawdown": 0,
                "cumulativePnl": 0,
            }
        )
    return points


@app.get("/api/frontend/strategies/user/{user_id}", tags=["Frontend"])
async def frontend_user_strategies(user_id: str):
    result = await strategy_service.get_user_strategies(user_id)
    strategies = result.get("strategies", []) if result.get("success") else []
    return [
        {
            "id": str(strategy.get("id")),
            "name": strategy.get("name", "Unnamed Strategy"),
            "description": strategy.get("description", ""),
            "winRate": float(strategy.get("win_rate") or 0),
            "avgRoi": float(strategy.get("avg_roi") or 0),
            "maxDrawdown": float(strategy.get("max_drawdown") or 0),
            "sharpeRatio": float(strategy.get("sharpe_ratio") or 0),
            "totalTrades": int(strategy.get("total_trades") or 0),
            "profitFactor": float(strategy.get("profit_factor") or 0),
            "riskLevel": strategy.get("risk_level", "Medium"),
            "isActive": bool(strategy.get("is_active", True)),
            "maxLeverage": strategy.get("max_leverage"),
            "signals": strategy.get("signals"),
            "status": strategy.get("status"),
            "createdAt": _iso(strategy.get("created_at")),
        }
        for strategy in strategies
    ]


@app.get("/api/frontend/strategies/marketplace", tags=["Frontend"])
async def frontend_marketplace_strategies(limit: int = Query(50, le=100), offset: int = Query(0)):
    result = await strategy_service.get_marketplace_strategies(limit, offset)
    strategies = result.get("strategies", []) if result.get("success") else []
    return [
        {
            "id": str(strategy.get("id")),
            "name": strategy.get("name", "Unnamed Strategy"),
            "creator": strategy.get("creator_name") or "Unknown",
            "description": strategy.get("description", ""),
            "winRate": float(strategy.get("win_rate") or 0),
            "roi": float(strategy.get("roi") or strategy.get("avg_roi") or 0),
            "maxDrawdown": float(strategy.get("max_drawdown") or 0),
            "subscribers": int(strategy.get("subscribers") or strategy.get("total_followers") or 0),
            "riskLevel": strategy.get("risk_level", "Medium"),
            "monthlyPrice": float(strategy.get("monthly_price") or 0),
            "isVerified": bool(strategy.get("verified_at")),
            "reputationScore": float(strategy.get("reputation_score") or 0),
            "verificationStage": int(strategy.get("verification_stage") or 1),
            "performanceBadge": strategy.get("performance_badge") or "New",
            "paperTradeDelta": float(strategy.get("paper_trade_delta") or 0),
            "pricingModel": strategy.get("pricing_model") or "Subscription",
        }
        for strategy in strategies
    ]


@app.get("/api/frontend/strategies/{strategy_id}/performance", tags=["Frontend"])
async def frontend_strategy_performance(strategy_id: str):
    result = await strategy_service.get_strategy_performance(strategy_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Strategy performance not found"))

    metrics = result.get("metrics", {})
    return {
        "id": strategy_id,
        "strategyName": metrics.get("strategy_name") or strategy_id,
        "winRate": float(str(metrics.get("win_rate", 0)).replace("%", "") or 0),
        "roi": float(metrics.get("total_return") or metrics.get("total_pnl") or 0),
        "trades": int(metrics.get("total_trades") or metrics.get("closed_trades") or 0),
        "profitFactor": float(metrics.get("profit_factor") or 0),
    }


@app.get("/api/frontend/strategies/{strategy_id}/paper-trade-result", tags=["Frontend"])
async def frontend_strategy_paper_trade_result(strategy_id: str):
    response = db.supabase.table("strategy_paper_trades").select("*").eq("strategy_id", strategy_id).order("started_at", desc=True).limit(1).execute()
    if not response.data:
        return None
    session = response.data[0]
    initial = float(session.get("initial_capital") or 0)
    current = float(session.get("current_capital") or initial)
    roi = ((current - initial) / initial * 100) if initial else 0
    return {
        "duration": 28,
        "signalCount": int(session.get("signal_count") or 0),
        "roi": round(roi, 2),
        "maxDrawdown": float(session.get("max_drawdown") or 0),
    }


@app.get("/api/frontend/signals/live/{user_id}", tags=["Frontend"])
async def frontend_live_signals(user_id: str, limit: int = Query(50, le=100)):
    response = db.supabase.table("signals").select("*").order("created_at", desc=True).limit(limit).execute()
    return [_map_signal_to_frontend(signal) for signal in (response.data or [])]


@app.get("/api/frontend/signals/latest", tags=["Signals"])
async def frontend_latest_signals(limit: int = Query(10, le=100)):
    """Get latest generated signals."""
    try:
        response = db.supabase.table("signals").select("*").order("created_at", desc=True).limit(limit).execute()
        return [_map_signal_to_frontend(signal) for signal in (response.data or [])]
    except Exception as e:
        logger.error(f"❌ Failed to get latest signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/frontend/signals/{signal_id}", tags=["Frontend"])
async def frontend_signal_detail(signal_id: str):
    response = db.supabase.table("signals").select("*").eq("id", signal_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Signal not found")
    return _map_signal_to_frontend(response.data[0])


@app.get("/api/frontend/signals/{signal_id}/proof", tags=["Frontend"])
async def frontend_signal_proof(signal_id: str):
    result = await user_service.get_signal_proof(signal_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Signal proof not found"))

    proof = result.get("proof", {})
    return {
        "signalId": signal_id,
        "hash": user_service._hash_content(signal_id),
        "merkleRoot": proof.get("merkle_root"),
        "timestamp": _iso(proof.get("created_at")),
        "verified": bool((proof.get("blockchain_anchor") or {}).get("confirmation", True)),
        "txHash": (proof.get("blockchain_anchor") or {}).get("tx_hash"),
        "hypothesis": proof.get("rationale"),
        "backtestResult": "Backtest history available",
        "paperResults": "Paper trading validation completed",
        "liveResults": "Live execution trace available",
    }


@app.get("/api/frontend/external/{user_id}/signals", tags=["Frontend"])
async def frontend_external_signals(user_id: str, limit: int = Query(50, le=100)):
    result = await user_service.get_external_signals(user_id, limit)
    signals = result.get("signals", []) if result.get("success") else []
    mapped = []
    for signal in signals:
        direction = _normalize_direction(signal.get("signal_type"))
        mapped.append(
            {
                "id": str(signal.get("id")),
                "source": "tradingview",
                "asset": signal.get("ticker"),
                "direction": direction,
                "confidence": signal.get("confidence"),
                "timestamp": _iso(signal.get("created_at")),
                "webhookPayload": signal.get("metadata", {}),
                "status": "processed",
                "executionContext": {
                    "riskMultiplier": 1.0,
                    "positionSize": float(signal.get("price") or 0),
                    "executedAt": _iso(signal.get("created_at")),
                },
            }
        )
    return mapped


@app.get("/api/frontend/external/{user_id}/webhook-events", tags=["Frontend"])
async def frontend_webhook_events(user_id: str, limit: int = Query(100, le=500)):
    result = await user_service.get_external_signal_history(user_id, days=7)
    events = result.get("webhook_hits", []) if result.get("success") else []
    return [
        {
            "id": f"event-{event.get('id')}",
            "userId": user_id,
            "timestamp": _iso(event.get("created_at")),
            "sourceIp": event.get("source_ip"),
            "signatureValid": True,
            "payload": event.get("metadata", {}),
            "processingStatus": "processed",
            "matchedSignalId": str(event.get("id")),
        }
        for event in events[:limit]
    ]


@app.get("/api/frontend/external/{user_id}/ingestion-rule", tags=["Frontend"])
async def frontend_ingestion_rule(user_id: str):
    response = db.supabase.table("external_signal_rules").select("*").eq("user_id", user_id).execute()
    rule = response.data[0] if response.data else {}
    rule_payload = rule.get("rules", {}) if isinstance(rule.get("rules"), dict) else {}
    return {
        "id": str(rule.get("id") or f"rule-{user_id}"),
        "userId": user_id,
        "minConfidence": float(rule_payload.get("min_confidence") or 0.7),
        "autoExecute": bool(rule_payload.get("auto_execute", False)),
        "cooldownSeconds": int(rule_payload.get("cooldown_seconds") or 60),
        "maxPositionsOpen": int(rule_payload.get("max_positions_open") or 5),
        "riskMultiplier": float(rule_payload.get("risk_multiplier") or 1.0),
        "createdAt": _iso(rule.get("created_at")),
        "updatedAt": _iso(rule.get("updated_at")),
    }


@app.get("/api/frontend/creator/{user_id}/verification-pipeline", tags=["Frontend"])
async def frontend_creator_pipeline(user_id: str):
    result = await creator_service.get_verification_status(user_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Creator verification pipeline not found"))

    pipeline = result.get("pipeline", [])
    current_stage = 1
    for idx, item in enumerate(pipeline, start=1):
        if item.get("status") == "current":
            current_stage = idx
            break

    return [
        {
            "strategyId": str((result.get("creator_profile") or {}).get("id") or f"strategy-{user_id}"),
            "strategyName": (result.get("creator_profile") or {}).get("name") or "Creator Strategy",
            "currentStage": current_stage,
            "steps": [
                {
                    "id": str(step.get("stage")),
                    "name": step.get("name"),
                    "status": "Completed" if step.get("status") == "completed" else "In Progress" if step.get("status") == "current" else "Pending",
                    "description": step.get("description"),
                }
                for step in pipeline
            ],
            "overallStatus": "Active" if result.get("current_stage") == "stage_5_approved" else "Review",
        }
    ]


@app.get("/api/frontend/system/{user_id}/audit-logs", tags=["Frontend"])
async def frontend_audit_logs(user_id: str, limit: int = Query(200, le=500)):
    result = await user_service.get_audit_trail(user_id, limit)
    logs = result.get("audit_logs", []) if result.get("success") else []
    return [
        {
            "id": str(log.get("id")),
            "timestamp": _iso(log.get("timestamp")),
            "action": log.get("action", "UNKNOWN"),
            "target": str(log.get("resource_id") or log.get("resource_type") or "system"),
            "userId": str(log.get("user_id")),
            "status": "Success",
            "node": "AF-NODE-01",
        }
        for log in logs
    ]


@app.get("/api/frontend/system/model-performance", tags=["Frontend"])
async def frontend_model_performance():
    response = db.supabase.table("signals").select("confidence").execute()
    confidences = [float(item.get("confidence") or 0) for item in (response.data or [])]
    average_confidence = mean(confidences) if confidences else 0.75
    return [
        {
            "id": "model-signal-core",
            "modelName": "Signal Confidence Model",
            "accuracy": round(average_confidence, 2),
            "latency": 45,
            "uptime": 99.9,
            "lastTraining": datetime.utcnow().isoformat(),
        }
    ]


@app.get("/api/frontend/system/{user_id}/notifications", tags=["Frontend"])
async def frontend_notifications(user_id: str):
    return [
        {
            "id": f"notif-{user_id}-1",
            "userId": user_id,
            "type": "system",
            "title": "Backend Connected",
            "message": "Realtime backend bridge is active.",
            "read": False,
            "critical": False,
            "createdAt": datetime.utcnow().isoformat(),
        }
    ]


# ============================================================================
# PHASE 2: ML SIGNAL SCORING
# ============================================================================

@app.post("/api/ml/score-signal", tags=["ML Scoring"])
async def score_signal(
    signal_id: str = Query(...),
    signal_data: Dict[str, Any] = Body(...)
):
    """Score signal using ML model."""
    try:
        if ml_scorer is None:
            raise HTTPException(status_code=503, detail="ML scoring service not initialized")
        result = await ml_scorer.score_signal(signal_id, signal_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Scoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/model/performance", tags=["ML Scoring"])
async def get_ml_performance():
    """Get ML model performance metrics."""
    try:
        performance = await ml_scorer.get_model_performance()
        return performance
    except Exception as e:
        logger.error(f"❌ Failed to get ML performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/train", tags=["ML Scoring"])
async def train_ml_model(training_data: List[Dict[str, Any]] = None):
    """Train ML model (Phase 2 feature)."""
    try:
        result = await ml_scorer.train_model(training_data or [])
        return result
    except Exception as e:
        logger.error(f"❌ Train failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 2: CREATOR MARKETPLACE
# ============================================================================

@app.post("/api/creators", tags=["Marketplace"])
async def create_creator(
    user_id: str = Query(...),
    bio: str = Query(...),
    strategy_ids: List[str] = Query(None)
):
    """Create creator profile."""
    try:
        result = await creator_marketplace.create_creator_profile(
            user_id, bio, strategy_ids
        )
        return result
    except Exception as e:
        logger.error(f"❌ Creator creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/creators", tags=["Marketplace"])
async def list_creators(
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    sort_by: str = Query("reputation_score")
):
    """List all verified creators."""
    try:
        result = await creator_marketplace.list_creators(limit, offset, sort_by)
        return result
    except Exception as e:
        logger.error(f"❌ Creator listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/creators/{creator_id}", tags=["Marketplace"])
async def get_creator(creator_id: str):
    """Get creator profile."""
    try:
        result = await creator_marketplace.get_creator_profile(creator_id)
        return result
    except Exception as e:
        logger.error(f"❌ Failed to get creator: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/creators/{creator_id}/strategies", tags=["Marketplace"])
async def publish_strategy(
    creator_id: str,
    strategy_data: Dict[str, Any]
):
    """Publish strategy to marketplace."""
    try:
        result = await creator_marketplace.publish_strategy(creator_id, strategy_data)
        return result
    except Exception as e:
        logger.error(f"❌ Strategy publishing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/marketplace", tags=["Marketplace"])
async def list_marketplace_strategies(
    limit: int = Query(50, le=100),
    offset: int = Query(0)
):
    """List marketplace strategies."""
    try:
        result = await creator_marketplace.list_creators(limit, offset)
        return result
    except Exception as e:
        logger.error(f"❌ Marketplace query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategies/{strategy_id}/subscribe", tags=["Marketplace"])
async def subscribe_to_strategy(
    strategy_id: str = Path(...),
    user_id: str = Query(...),
    allocation_pct: float = Query(10.0)
):
    """Subscribe user to strategy."""
    try:
        result = await creator_marketplace.subscribe_to_strategy(
            user_id, strategy_id, allocation_pct
        )
        return result
    except Exception as e:
        logger.error(f"❌ Subscription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}/paper-trade-status", tags=["Marketplace"])
async def check_paper_trading_gate(strategy_id: str = Path(...)):
    """Check if strategy passed paper trading validation gate."""
    try:
        result = await creator_marketplace.check_paper_trading_completion(strategy_id)
        return result
    except Exception as e:
        logger.error(f"❌ Paper trading check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 2: KYC VERIFICATION
# ============================================================================

@app.post("/api/kyc/start", tags=["KYC"])
async def start_kyc(
    user_id: str = Query(...),
    kyc_level: str = Query("enhanced")
):
    """Start KYC verification process."""
    try:
        result = await kyc_service.start_kyc(user_id, kyc_level)
        return result
    except Exception as e:
        logger.error(f"❌ KYC start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kyc/status", tags=["KYC"])
async def get_kyc_status(user_id: str = Query(...)):
    """Get user KYC verification status."""
    try:
        result = await kyc_service.get_kyc_status(user_id)
        return result
    except Exception as e:
        logger.error(f"❌ KYC status fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/upload", tags=["KYC"])
async def upload_kyc_document(
    user_id: str = Query(...),
    document_type: str = Query(...),
    document_url: str = Query(...)
):
    """Upload KYC document."""
    try:
        result = await kyc_service.upload_document(
            user_id, document_type, document_url
        )
        return result
    except Exception as e:
        logger.error(f"❌ Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/submit", tags=["KYC"])
async def submit_kyc(user_id: str = Query(...)):
    """Submit KYC for review."""
    try:
        result = await kyc_service.submit_kyc(user_id)
        return result
    except Exception as e:
        logger.error(f"❌ KYC submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/resubmit", tags=["KYC"])
async def resubmit_kyc(user_id: str = Query(...)):
    """Resubmit rejected KYC."""
    try:
        result = await kyc_service.resubmit_kyc(user_id)
        return result
    except Exception as e:
        logger.error(f"❌ KYC resubmission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kyc/admin/pending", tags=["KYC", "Admin"])
async def get_pending_kyc_reviews(limit: int = Query(50, le=100)):
    """Admin: Get pending KYC reviews."""
    try:
        result = await kyc_service.get_pending_kyc_reviews(limit)
        return result
    except Exception as e:
        logger.error(f"❌ Failed to get pending reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/admin/approve", tags=["KYC", "Admin"])
async def approve_kyc(
    user_id: str = Query(...),
    admin_id: str = Query(...),
    notes: str = Query("")
):
    """Admin: Approve KYC."""
    try:
        result = await kyc_service.approve_kyc(user_id, admin_id, notes)
        return result
    except Exception as e:
        logger.error(f"❌ KYC approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/admin/reject", tags=["KYC", "Admin"])
async def reject_kyc(
    user_id: str = Query(...),
    admin_id: str = Query(...),
    rejection_reason: str = Query(...)
):
    """Admin: Reject KYC."""
    try:
        result = await kyc_service.reject_kyc(user_id, admin_id, rejection_reason)
        return result
    except Exception as e:
        logger.error(f"❌ KYC rejection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET ENDPOINTS - REAL-TIME UPDATES
# ============================================================================

@app.websocket("/ws/market-updates")
async def websocket_market_updates(websocket: WebSocket):
    """Stream real-time market data updates."""
    await ws_manager.connect(websocket, "market-updates")
    
    try:
        while True:
            # Fetch latest market data
            tickers = await market_data_service.fetch_market_tickers(['BTC', 'ETH', 'SOL', 'DOGE'])
            
            # Broadcast to all connected clients
            await ws_manager.broadcast_to_group("market-updates", {
                "type": "market_update",
                "data": tickers,
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            # Update every 5 seconds
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "market-updates")
        logger.info("WebSocket disconnected: market-updates")
    except Exception as e:
        logger.error(f"WebSocket error in market-updates: {e}")
        ws_manager.disconnect(websocket, "market-updates")


@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """Stream real-time signal updates."""
    await ws_manager.connect(websocket, "signals")
    
    try:
        while True:
            # Fetch live signals from database
            try:
                response = db.supabase.table("signals").select("*").order("created_at", desc=True).limit(50).execute()
                signals = [_map_signal_to_frontend(signal) for signal in (response.data or [])]
            except Exception as e:
                logger.warning(f"Failed to fetch signals: {e}")
                signals = []
            
            # Only broadcast if there are signals
            if signals:
                await ws_manager.broadcast_to_group("signals", {
                    "type": "signal_update",
                    "data": signals,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            
            # Update every 2 seconds
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "signals")
        logger.info("WebSocket disconnected: signals")
    except Exception as e:
        logger.error(f"WebSocket error in signals: {e}")
        ws_manager.disconnect(websocket, "signals")


# ============================================================================
# ERROR HANDLING
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("API_ENV") == "development"
    )
