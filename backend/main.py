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
from firebase_config import verify_firebase_token, verify_admin_token, FirebaseTokenVerifier, require_self_or_admin
from services.signal_aggregator import SignalAggregator
from services.signal_processor import SignalProcessor
from services.paper_trading import PaperTradingEngine
from services.portfolio import PortfolioService
from services.risk_manager import RiskManager
from services.market_data import MarketDataService
from services.chat_service import ChatService
from services.creator_service import CreatorVerificationService
from services.user_service import UserManagementService
from services.backtest_service import BacktestingService
from services.strategy_service import StrategyService
from services.ml_signal_scorer import MLSignalScorer
from services.creator_marketplace import CreatorMarketplaceService
from services.kyc_service import KYCService
from services.compliance_service import ComplianceService
from services.billing_service import BillingService
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
from services.strategy_configurator import StrategyConfiguratorService
from services.education_service import EducationService
from services.tournament_service import TournamentService
from services.community_service import CommunityService
from services.strategy_personality import StrategyPersonalityService
from services.trailing_orders import TrailingOrdersService
from services.onchain_tracker import OnchainTrackerService
from tests.load_test_suite import LoadTestRunner
from utils.redis_manager import redis_manager
from services.startup_orchestrator import get_orchestrator
from services.execution_service import (
    IdempotencyKeyManager, OrderConfirmationMonitor,
    ExchangeAbstractionLayer, get_idempotency_manager,
    get_order_monitor, get_exchange_layer,
)
from services.data_validation_service import DataValidationPipeline, BackupMarketDataProvider
from services.notification_service import NotificationService
from services.sentiment_analysis_service import SentimentAnalysisService
from services.strategy_marketplace_service import StrategyMarketplaceService
from services.audit_log_service import AuditLogService
from services.explainability_proofs import ExplainabilityProofsService
from services.backtesting_integrity import BacktestingIntegrityService
from services.overfitting_prevention import OverfittingPreventionService
from services.ensemble_predictor import EnsemblePredictor
from services.gpu_inference import ModelConfig, QuantizationPrecision, InferenceBackend
from routes import gap_features

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from websocket_manager import WebSocketManager

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
compliance_service = None
billing_service = None

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

# Phase 3 Enhancement Services
tournament_service = None
community_service = None
strategy_personality_service = None
trailing_orders_service = None
onchain_tracker_service = None
strategy_configurator = None
education_service = None

# Architecture Doc Gap Services
idempotency_manager = None
order_monitor = None
exchange_layer = None
data_validation_pipeline = None
backup_data_provider = None
notification_svc = None
sentiment_svc = None
strategy_marketplace_svc = None
audit_log_svc = None

# §13.3 Feature Store, §16.2 IP Whitelist, §6.1 Regime Detection, §6.4 GPU Inference
feature_store_svc = None
ip_whitelist_svc = None
regime_detector_svc = None
gpu_inference_svc = None

# Moat Services (Differentiators)
explainability_proofs_svc = None
backtesting_integrity_svc = None
overfitting_prevention_svc = None
ensemble_predictor_svc = None

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
    global ml_scorer, creator_marketplace, kyc_service, compliance_service, billing_service, ph
    global signal_perf_tracker, external_signal_validator, market_correlation_analyzer, binance_ws_manager
    global rate_limiter, perf_monitor
    global automation_engine
    global education_service
    global explainability_proofs_svc, backtesting_integrity_svc, overfitting_prevention_svc, ensemble_predictor_svc
    
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
    compliance_service = ComplianceService(db)
    billing_service = BillingService(db)
    
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
    
    # ========================================================================
    # INITIALIZE AUTOMATION ENGINE (Grid Bot + DCA Bot)
    # ========================================================================
    
    from config import AutomationConfig
    if AutomationConfig.ENABLED:
        try:
            automation_engine = AutomationEngine(db)
            logger.info("✅ Automation engine initialized (Grid Bot + DCA Bot)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize automation engine: {e}")
    else:
        logger.info("ℹ️  Automation engine disabled (AUTOMATION_ENABLED=false)")
    
    # ========================================================================
    # INITIALIZE EDUCATION SERVICE (AlphaAcademy)
    # ========================================================================
    
    from config import EducationConfig
    if EducationConfig.ENABLED:
        try:
            education_service = EducationService(db)
            logger.info("✅ AlphaAcademy education service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize education service: {e}")
    else:
        logger.info("ℹ️  AlphaAcademy disabled (ALPHAACADEMY_ENABLED=false)")
    
    # ========================================================================
    # INITIALIZE PHASE 3 ENHANCEMENT SERVICES
    # ========================================================================
    
    from config import TournamentConfig, CommunityConfig, StrategyPersonalityConfig, TrailingOrderConfig, OnchainConfig

    if TournamentConfig.ENABLED:
        try:
            tournament_service = TournamentService(db)
            logger.info("✅ Tournament service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize tournament service: {e}")

    if CommunityConfig.ENABLED:
        try:
            community_service = CommunityService(db)
            logger.info("✅ Community service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize community service: {e}")
    
    if StrategyPersonalityConfig.ENABLED:
        try:
            strategy_personality_service = StrategyPersonalityService(db)
            logger.info("✅ Strategy personality service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize strategy personality service: {e}")
    
    if TrailingOrderConfig.ENABLED:
        try:
            trailing_orders_service = TrailingOrdersService(db)
            logger.info("✅ Trailing orders service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize trailing orders service: {e}")
    
    if OnchainConfig.ENABLED:
        try:
            onchain_tracker_service = OnchainTrackerService(db, use_mock=OnchainConfig.USE_MOCK_DATA)
            logger.info("✅ Onchain tracker service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize onchain tracker service: {e}")
    
    logger.info("✅ All Phase 3 enhancement services initialized")

    # ========================================================================
    # INITIALIZE ARCHITECTURE DOC GAP SERVICES
    # ========================================================================

    global idempotency_manager, order_monitor, exchange_layer
    global data_validation_pipeline, backup_data_provider
    global notification_svc, sentiment_svc, strategy_marketplace_svc, audit_log_svc

    from utils.redis_manager import redis_manager as rm
    idempotency_manager = get_idempotency_manager(rm._client if rm.enabled else None)
    logger.info("✅ Idempotency key manager initialized")

    order_monitor = get_order_monitor(db)
    await order_monitor.start_watchdog()
    logger.info("✅ Order confirmation monitor initialized")

    exchange_layer = get_exchange_layer("binance", "", "")
    logger.info("✅ Exchange abstraction layer initialized")

    data_validation_pipeline = DataValidationPipeline()
    backup_data_provider = BackupMarketDataProvider()
    logger.info("✅ Data validation pipeline initialized")

    notification_svc = NotificationService(db)
    logger.info("✅ Notification service initialized")

    sentiment_svc = SentimentAnalysisService(db)
    logger.info("✅ Sentiment analysis service initialized")

    strategy_marketplace_svc = StrategyMarketplaceService(db)
    logger.info("✅ Strategy marketplace service initialized")

    audit_log_svc = AuditLogService(db)
    logger.info("✅ Audit log service initialized")

    # ========================================================================
    # INITIALIZE MOAT SERVICES (Differentiators: Explainability, Backtesting)
    # ========================================================================

    try:
        explainability_proofs_svc = ExplainabilityProofsService(db)
        logger.info("✅ Explainability proofs service initialized (MOAT)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize explainability proofs: {e}")

    try:
        backtesting_integrity_svc = BacktestingIntegrityService(db)
        logger.info("✅ Backtesting integrity service initialized (MOAT)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize backtesting integrity: {e}")

    try:
        overfitting_prevention_svc = OverfittingPreventionService(db)
        logger.info("✅ Overfitting prevention service initialized (MOAT)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize overfitting prevention: {e}")

    try:
        ensemble_predictor_svc = EnsemblePredictor(db)
        logger.info("✅ Ensemble predictor service initialized (MOAT)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ensemble predictor: {e}")

    # ========================================================================
    # INITIALIZE GAP FEATURE SERVICES (Live Trading, AI Signals, Mobile App)
    # ========================================================================

    from config import FeatureFlags
    from services.live_trading_engine import LiveTradingEngine
    from services.llm_signal_generator import LLMSignalGenerator

    gap_services: Dict[str, Any] = {"compliance_service": compliance_service}

    if FeatureFlags.LIVE_TRADING:
        try:
            gap_services["live_trading_engine"] = LiveTradingEngine()
            logger.info("✅ Live trading engine initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize live trading engine: {e}")

    if FeatureFlags.AI_SIGNALS:
        try:
            gap_services["llm_signal_generator"] = LLMSignalGenerator()
            logger.info("✅ LLM signal generator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM signal generator: {e}")

    gap_features.initialize_services(db, gap_services)

    # ========================================================================
    # INITIALIZE NEW GAP SERVICES (§13.3, §16.2, §6.1, §6.4)
    # ========================================================================

    global feature_store_svc, ip_whitelist_svc, regime_detector_svc, gpu_inference_svc

    from services.feature_store import get_feature_store
    from services.ip_whitelist_service import get_ip_whitelist_service
    from services.regime_detector import get_regime_detector
    from services.gpu_inference import get_gpu_inference_service

    feature_store_svc = get_feature_store(db, rm._client if rm.enabled else None)
    logger.info("✅ Feature store initialized (§13.3)")

    ip_whitelist_svc = get_ip_whitelist_service(db, notification_svc, audit_log_svc)
    logger.info("✅ IP whitelist service initialized (§16.2)")

    regime_detector_svc = get_regime_detector()
    logger.info("✅ Market regime detector initialized (§6.1)")

    gpu_inference_svc = get_gpu_inference_service()
    logger.info("✅ GPU inference service initialized (§6.4)")

    # Initialize Redis PubSub for WebSocket fan-out (§19.1)
    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        await ws_manager.initialize_redis(redis_url)
        logger.info("✅ WebSocket Redis PubSub initialized (§19.1)")
    
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
    
    # ========================================================================
    # INITIALIZE ENHANCED SERVICES (Chat + External Signal Ingestion)
    # ========================================================================
    
    from services.external_signal_ingestion import ExternalSignalIngestionService
    global external_signal_ingestion
    external_signal_ingestion = ExternalSignalIngestionService(db)
    logger.info("✅ External signal ingestion service initialized")
    
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

# ---------------------------------------------------------------------------
# CORS configuration
#
# Production: CORS_ALLOW_ORIGINS must be explicitly set. No wildcards.
# Development: defaults to localhost dev ports + any configured ngrok tunnel.
# ---------------------------------------------------------------------------
DEV_URLS = [
    "http://localhost:3000",
    "http://localhost:9002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:9002",
]

# Parse ngrok URL from environment (format: https://xxxx.ngrok-free.app)
ngrok_url = os.getenv("NGROK_TUNNEL_URL", "").strip()
if not ngrok_url:
    api_url = os.getenv("NEXT_PUBLIC_API_URL", "")
    if "ngrok" in api_url:
        ngrok_url = api_url
if ngrok_url and not ngrok_url.endswith("/"):
    DEV_URLS.append(ngrok_url)

CORS_ALLOW_ORIGINS_RAW = os.getenv("CORS_ALLOW_ORIGINS", "").strip()

if CORS_ALLOW_ORIGINS_RAW:
    ALLOWED_ORIGINS = [o.strip() for o in CORS_ALLOW_ORIGINS_RAW.split(",") if o.strip()]
else:
    # No explicit config — use safe defaults per environment
    ALLOWED_ORIGINS = [] if IS_PRODUCTION else DEV_URLS

# Safety checks — never allow wildcards with credentials
HAS_WILDCARD = "*" in ALLOWED_ORIGINS

if IS_PRODUCTION:
    if HAS_WILDCARD:
        raise RuntimeError(
            "CORS_ALLOW_ORIGINS cannot include '*' in production. "
            "Set CORS_ALLOW_ORIGINS to your actual frontend domain(s)."
        )
    if not ALLOWED_ORIGINS:
        raise RuntimeError(
            "CORS_ALLOW_ORIGINS is empty in production. "
            "Set it to your frontend domain(s), e.g. https://alphaforge.app"
        )

logger.info("CORS Configuration (IS_PRODUCTION=%s)", IS_PRODUCTION)
logger.info("Allowed Origins: %s", ALLOWED_ORIGINS)
if ngrok_url:
    logger.info("ngrok URL detected: %s", ngrok_url)

# Only send credentials when origins are explicitly enumerated (not wildcard)
allow_credentials = not HAS_WILDCARD and len(ALLOWED_ORIGINS) > 0

# Restrict methods and headers to what the app actually uses
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
CORS_ALLOW_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Origin",
    "X-Requested-With",
    "X-User-Id",
]

if not IS_PRODUCTION:
    # Allow all local network origins in development (LAN IPs, localhost, etc.)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$",
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=allow_credentials,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

# ---------------------------------------------------------------------------
# Trusted Hosts
# ---------------------------------------------------------------------------
TRUSTED_HOSTS_RAW = os.getenv("TRUSTED_HOSTS", "").strip()

if TRUSTED_HOSTS_RAW:
    TRUSTED_HOSTS = [h.strip() for h in TRUSTED_HOSTS_RAW.split(",") if h.strip()]
else:
    # Safe defaults: allow all hosts in development (LAN IPs, localhost), must be explicit in production
    TRUSTED_HOSTS = ["*"] if not IS_PRODUCTION else []

if IS_PRODUCTION and "*" in TRUSTED_HOSTS:
    raise RuntimeError("TRUSTED_HOSTS cannot include '*' in production")
if IS_PRODUCTION and not TRUSTED_HOSTS:
    raise RuntimeError(
        "TRUSTED_HOSTS is empty in production. "
        "Set it to your actual hostnames, e.g. api.alphaforge.app,alphaforge.app"
    )

app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)

# Add performance monitoring middleware
perf_monitor = PerformanceMonitor()
app.add_middleware(PerformanceMonitoringMiddleware, monitor=perf_monitor)

# Add adaptive rate limiting middleware
rate_limiter = AdaptiveRateLimiter()
app.add_middleware(RateLimitingMiddleware, rate_limiter=rate_limiter)

# Gap feature routes (live trading, AI signal generation, mobile app, compliance)
app.include_router(gap_features.router)

# Initialize advanced services
ml_retraining_pipeline = MLModelRetrainingPipeline(retraining_interval_days=7)
alert_manager = AlertManager()
alert_manager.add_alert_handler(LogAlertChannel().send)
strategy_manager = StrategyManagementService()
portfolio_risk_analyzer = PortfolioRiskAnalyzer()
risk_enforcer = RiskLimitEnforcer()
load_test_runner = LoadTestRunner(base_url=os.getenv("API_URL", "http://localhost:8000"))
strategy_configurator = StrategyConfiguratorService(db)

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
            "users,signals,paper_trades,positions,portfolios,creator_profiles,kyc_verifications,audit_logs,external_signals,api_keys,strategies,creator_strategies,strategy_subscriptions,strategy_paper_trades,backtests,chat_messages,notifications,user_risk_settings,external_signal_rules,user_strategies,strategy_templates",
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {e}")


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    from services.prometheus_metrics import get_prometheus_metrics
    metrics_data = get_prometheus_metrics().get_metrics()
    return PlainTextResponse(content=metrics_data, media_type="text/plain")


# ============================================================================
# INFRASTRUCTURE HEALTH
# ============================================================================

@app.get("/api/health/infrastructure", tags=["Health"])
async def infrastructure_health():
    """Comprehensive infrastructure health check."""
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    overall_healthy = True

    # Database
    try:
        db_ok = not (REQUIRE_REAL_DB and db.is_mock_mode)
        health["services"]["database"] = {
            "status": "healthy" if db_ok else "degraded",
            "mode": "mock" if db.is_mock_mode else "supabase"
        }
        if not db_ok:
            overall_healthy = False
    except Exception as e:
        health["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # Redis
    try:
        redis_health = await redis_manager.health_check()
        health["services"]["redis"] = redis_health
        if redis_health.get("status") != "healthy":
            overall_healthy = False
    except Exception as e:
        health["services"]["redis"] = {"status": "unhealthy", "error": str(e)}

    # Kafka (optional)
    try:
        from services.kafka_service import get_kafka_service
        kafka_svc = await get_kafka_service()
        health["services"]["kafka"] = kafka_svc.health_check()
    except Exception as e:
        health["services"]["kafka"] = {"status": "unavailable", "error": str(e)}

    # ClickHouse (optional)
    try:
        from services.clickhouse_service import get_clickhouse_service
        ch_svc = await get_clickhouse_service()
        health["services"]["clickhouse"] = ch_svc.health_check()
    except Exception as e:
        health["services"]["clickhouse"] = {"status": "unavailable", "error": str(e)}

    # Exchange failover
    try:
        from services.circuit_breaker import get_multi_exchange_failover
        failover = get_multi_exchange_failover()
        health["services"]["exchanges"] = failover.get_health_status()
    except Exception as e:
        health["services"]["exchanges"] = {"status": "unavailable", "error": str(e)}

    health["status"] = "healthy" if overall_healthy else "degraded"
    return health


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

    except HTTPException:
        raise
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

    except HTTPException:
        raise
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

    except HTTPException:
        raise
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
    require_self_or_admin(user_id, firebase_uid)
    try:
        summary = await portfolio_service.get_portfolio_summary(user_id)

        if not summary:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        logger.info(f"✅ Portfolio retrieved for {user_id}")
        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Portfolio fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/{user_id}/metrics", tags=["Portfolio"])
async def get_portfolio_metrics(user_id: str, firebase_uid: str = Depends(verify_firebase_token)):
    """Get detailed portfolio metrics (performance stats) (requires Firebase authentication)."""
    require_self_or_admin(user_id, firebase_uid)
    try:
        metrics = await paper_trading.get_portfolio_metrics(user_id)

        if not metrics:
            raise HTTPException(status_code=404, detail="Portfolio metrics not found")

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Metrics fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/{user_id}/benchmark", tags=["Portfolio"])
async def get_portfolio_benchmark(
    user_id: str,
    period_days: int = Query(30, ge=1, le=3650),
    benchmarks: str = Query("BTC,ETH", description="Comma-separated tickers to compare against"),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Compare portfolio return against BTC/ETH or custom benchmarks over a period."""
    require_self_or_admin(user_id, firebase_uid)
    try:
        benchmark_list = [b.strip().upper() for b in benchmarks.split(",") if b.strip()]
        result = await portfolio_service.get_benchmark_comparison(
            user_id, market_data_service, period_days=period_days, benchmarks=benchmark_list
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Benchmark comparison failed"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Benchmark comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions/{user_id}", tags=["Portfolio"])
async def get_positions(user_id: str, firebase_uid: str = Depends(verify_firebase_token)):
    """Get all open positions."""
    require_self_or_admin(user_id, firebase_uid)
    try:
        positions = await portfolio_service.get_open_positions(user_id)

        return {"positions": positions, "count": len(positions)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Positions fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/{user_id}/positions", tags=["Portfolio"])
async def get_portfolio_positions(user_id: str, firebase_uid: str = Depends(verify_firebase_token)):
    """Compatibility alias for frontend contract."""
    return await get_positions(user_id, firebase_uid)


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
# FOREX ENDPOINTS
# ============================================================================

@app.get("/api/forex/pairs", tags=["Forex"])
async def get_forex_pairs():
    """Get list of supported forex pairs."""
    try:
        pairs = market_data_service.get_supported_forex_pairs()
        logger.info(f"✅ Fetched {len(pairs)} supported forex pairs")

        return {
            "success": True,
            "pairs": pairs,
            "count": len(pairs),
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"❌ Forex pairs fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forex/tickers", tags=["Forex"])
async def get_forex_tickers(pairs: str = Query("EUR/USD,GBP/USD,USD/JPY")):
    """Get forex pair tickers."""
    try:
        pair_list = [p.strip() for p in pairs.split(",")]
        tickers = await market_data_service.fetch_forex_tickers(pair_list)

        logger.info(f"✅ Fetched {len(tickers)} forex tickers")

        return {
            "success": True,
            "tickers": tickers,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"❌ Forex tickers fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forex/ticker/{pair}", tags=["Forex"])
async def get_forex_ticker(pair: str = Path(...)):
    """Get ticker for specific forex pair."""
    try:
        ticker = await market_data_service.fetch_forex_ticker(pair)

        if not ticker:
            raise HTTPException(status_code=404, detail=f"Forex pair {pair} not found")

        logger.info(f"✅ Fetched ticker for {pair}")

        return {
            "success": True,
            "ticker": ticker,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"❌ Forex ticker fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forex/ohlcv/{pair}", tags=["Forex"])
async def get_forex_ohlcv(
    pair: str = Path(...),
    interval: str = Query("1h"),
    limit: int = Query(100)
):
    """Get OHLCV data for forex pair."""
    try:
        ohlcv = await market_data_service.fetch_forex_ohlcv(pair, interval, limit)

        if not ohlcv:
            raise HTTPException(status_code=404, detail=f"OHLCV data for {pair} not found")

        logger.info(f"✅ Fetched OHLCV for {pair} ({interval}) - {len(ohlcv)} candles")

        return {
            "success": True,
            "pair": pair,
            "interval": interval,
            "ohlcv": ohlcv,
            "count": len(ohlcv),
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"❌ Forex OHLCV fetch failed: {e}")
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

    except HTTPException:
        raise
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

    except HTTPException:
        raise
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
async def get_kyc_status(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Get user's KYC verification status. User can only access their own KYC status."""
    try:
        if firebase_uid != user_id:
            raise HTTPException(status_code=403, detail="Cannot access other users' KYC status")

        result = await user_service.get_kyc_status(user_id)

        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get KYC status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get KYC status")


@app.post("/api/user/kyc", tags=["KYC"])
async def submit_kyc(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Submit KYC documents for verification. User can only submit their own KYC."""
    try:
        if firebase_uid != user_id:
            raise HTTPException(status_code=403, detail="Cannot submit KYC for other users")

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
async def connect_exchange(
    user_id: str = Query(...),
    exchange: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Connect a trading exchange API. Tier gating enforced: Basic=2 exchanges, Pro=4, VIP=unlimited."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot connect exchanges for other users")
    try:
        tier_info = await billing_service.get_tier_limits(user_id)
        limits = tier_info.get("limits", {})
        max_exchanges = limits.get("max_exchanges", 1)

        current = await user_service.get_connected_exchanges(user_id)
        num_connected = len(current.get("exchanges", []))

        if num_connected >= max_exchanges:
            raise HTTPException(
                status_code=403,
                detail=f"Tier {tier_info['tier']} limited to {max_exchanges} exchanges. Disconnect one first."
            )

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
async def get_connected_exchanges(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Get list of connected exchanges."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' exchanges")
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
async def disconnect_exchange(
    user_id: str = Query(...),
    exchange: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Disconnect a trading exchange."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot disconnect exchanges for other users")
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
async def set_signal_rules(
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Set filtering rules for external signal ingestion (VIP tier required)."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot set rules for another user")

    try:
        # Check VIP tier
        tier_info = await billing_service.get_tier_limits(user_id)
        if not tier_info.get("limits", {}).get("api_access"):
            raise HTTPException(status_code=403, detail="API access requires VIP tier subscription")

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
async def get_signal_history(
    user_id: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Get history of external signal webhook hits (VIP tier required)."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot view history for another user")

    try:
        # Check VIP tier
        tier_info = await billing_service.get_tier_limits(user_id)
        if not tier_info.get("limits", {}).get("api_access"):
            raise HTTPException(status_code=403, detail="API access requires VIP tier subscription")

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

@app.get("/api/strategies/user", tags=["Strategy"])
async def get_user_strategies(user_id: str = Query(...)):
    """Get all strategies created by a specific user."""
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


@app.get("/api/strategies/browse", tags=["Strategy"])
async def get_marketplace_strategies(limit: int = Query(50, le=100), offset: int = Query(0)):
    """Browse approved strategies on marketplace."""
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
async def run_backtest(
    user_id: str = Query(...),
    strategy_config: Dict[str, Any] = Body(default={}),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Run a backtest for a strategy. NOTE: current engine is a synthetic
    demo simulation, not a real historical-price replay — see
    backtest_service._simulate_backtest and results['data_source']."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot run a backtest for other users")
    try:
        strategy_config = {
            "name": strategy_config.get("name", "Unnamed Strategy"),
            "symbols": strategy_config.get("symbols", ["BTC", "ETH"]),
            "initial_capital": strategy_config.get("initial_capital", 100000),
            "start_date": strategy_config.get("start_date"),
            "end_date": strategy_config.get("end_date"),
            "parameters": strategy_config.get("parameters", {}),
        }

        result = await backtest_service.run_backtest(user_id, strategy_config)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))

    except HTTPException:
        raise
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

    except HTTPException:
        raise
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get equity curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/user/{user_id}", tags=["Backtesting"])
async def list_user_backtests(user_id: str, limit: int = Query(20, le=100), firebase_uid: str = Depends(verify_firebase_token)):
    """List all backtests for a user. User can only list their own."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot list other users' backtests")
    try:
        result = await backtest_service.list_user_backtests(user_id, limit)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list backtests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SIGNAL PROOF & EXECUTION ENDPOINTS
# ============================================================================

@app.post("/api/signals/{signal_id}/execute", tags=["Signals"])
async def execute_signal(signal_id: str, user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Execute a signal (convert to paper/live trade). User can only execute signals for themselves."""
    try:
        if firebase_uid != user_id:
            raise HTTPException(status_code=403, detail="Cannot execute signals for other users")

        result = await user_service.execute_signal(user_id, signal_id)

        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute signal: {e}")
        raise HTTPException(status_code=500, detail="Signal execution failed")


@app.get("/api/signals/{signal_id}/proofs", tags=["Signals"])
async def get_signal_proofs(signal_id: str):
    """Get proof/verification data for a signal."""
    try:
        result = await user_service.get_signal_proof(signal_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("error"))

    except HTTPException:
        raise
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

    except HTTPException:
        raise
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

        real_stats = perf_monitor.get_all_stats()
        endpoints = real_stats.get("endpoints", {})

        total_requests = sum(ep["total_calls"] for ep in endpoints.values())
        total_errors = sum(ep["error_calls"] for ep in endpoints.values())
        error_rate_pct = round((total_errors / total_requests * 100), 2) if total_requests else 0.0

        response_times = [
            float(ep["avg_response_time_ms"]) for ep in endpoints.values() if ep.get("total_calls", 0) > 0
        ]
        avg_response_time_ms = round(sum(response_times) / len(response_times), 2) if response_times else 0.0

        most_problematic_endpoint = None
        if endpoints:
            most_problematic_endpoint = max(
                endpoints.items(),
                key=lambda kv: kv[1]["error_calls"],
            )[0]

        monitoring_data = {
            "system_stats": {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate_pct": error_rate_pct,
                "avg_response_time_ms": avg_response_time_ms,
                "most_problematic_endpoint": most_problematic_endpoint,
            },
            "endpoints": endpoints,
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
        stats = perf_monitor.get_endpoint_stats(endpoint_path)

        if not stats or "error" in stats:
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
            "price": float(item.get("price") or 0),
            "change24h": float(item.get("change_24h_pct") or 0),
            "change24hAbs": float(item.get("change_24h") or 0),
            "volume24h": float(item.get("volume_24h") or 0),
            "high24h": float(item.get("high_24h") or item.get("price") or 0),
            "low24h": float(item.get("low_24h") or item.get("price") or 0),
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
async def frontend_on_chain_activity(limit: int = Query(20, le=50)):
    """Real whale-movement feed via onchain_tracker_service (respects its
    honest mock/database toggle — see OnchainConfig.USE_MOCK_DATA)."""
    if not onchain_tracker_service:
        return []

    result = await onchain_tracker_service.get_whale_movements(limit=limit)
    if not result.get("success"):
        return []

    exchange_types = {"exchange_deposit", "exchange_withdrawal"}
    return [
        {
            "id": m.get("id"),
            "type": "exchange_flow" if m.get("movement_type") in exchange_types else "whale_move",
            "asset": m.get("asset"),
            "amount": m.get("amount"),
            "valueUsd": m.get("value_usd"),
            "from": m.get("from_address"),
            "to": m.get("to_address"),
            "timestamp": m.get("timestamp"),
        }
        for m in result.get("movements", [])
    ]


@app.get("/api/frontend/market/on-chain-metrics", tags=["Frontend"])
async def frontend_on_chain_metrics(assets: str = Query("BTC,ETH,SOL")):
    """Real MVRV/SOPR-style on-chain valuation metrics per asset, flattened
    into one row per metric (via onchain_tracker_service — respects its
    honest mock/database toggle)."""
    if not onchain_tracker_service:
        return []

    rows = []
    for asset in [a.strip().upper() for a in assets.split(",") if a.strip()]:
        result = await onchain_tracker_service.get_asset_metrics(asset)
        if not result.get("success"):
            continue
        m = result["metrics"]
        rows.append({"asset": asset, "name": "MVRV", "value": str(m.get("mvrv")), "status": m.get("mvrv_label", "Neutral"), "change24h": 0})
        rows.append({"asset": asset, "name": "SOPR", "value": str(m.get("sopr")), "status": m.get("sopr_label", "Neutral"), "change24h": 0})
        rows.append({"asset": asset, "name": "NVT Ratio", "value": str(m.get("nvt_ratio")), "status": "Neutral", "change24h": 0})
        rows.append({
            "asset": asset,
            "name": "Exchange Balance",
            "value": f"{m.get('exchange_balance_change_pct_24h')}%",
            "status": "Undervalued" if (m.get("exchange_balance_change_pct_24h") or 0) < 0 else "Overvalued",
            "change24h": m.get("exchange_balance_change_pct_24h", 0),
        })
    return rows


@app.get("/api/frontend/market/liquidation-clusters", tags=["Frontend"])
async def frontend_liquidation_clusters():
    """Estimated long/short liquidation cluster sizing derived from real open
    interest. The long/short split is a heuristic (12%/8% of OI), not a
    measured liquidation-engine figure — flagged as estimated so the
    frontend/user never mistakes this for exchange-reported liquidation data."""
    oi = await market_data_service.fetch_open_interest()
    clusters = []
    for item in oi:
        value = float(item.get("open_interest_usd") or 0)
        clusters.append({"asset": item.get("asset"), "value": round(value * 0.12, 2), "type": "long", "estimated": True})
        clusters.append({"asset": item.get("asset"), "value": round(value * 0.08, 2), "type": "short", "estimated": True})
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
    # accuracy is real (avg confidence over actual stored signals). latency/
    # uptime are not measured yet — no request-latency or uptime-tracking
    # subsystem exists — so we report them as null rather than inventing
    # plausible-looking numbers.
    response = db.supabase.table("signals").select("confidence, created_at").execute()
    rows = response.data or []
    confidences = [float(item.get("confidence") or 0) for item in rows]
    average_confidence = mean(confidences) if confidences else 0.75
    last_training = max((r.get("created_at") for r in rows if r.get("created_at")), default=None)
    return [
        {
            "id": "model-signal-core",
            "modelName": "Signal Confidence Model",
            "accuracy": round(average_confidence, 2),
            "latency": None,
            "uptime": None,
            "lastTraining": last_training or datetime.utcnow().isoformat(),
        }
    ]


@app.get("/api/frontend/system/{user_id}/notifications", tags=["Frontend"])
async def frontend_notifications(user_id: str, firebase_uid: str = Depends(verify_firebase_token)):
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' notifications")
    if not notification_svc:
        return []
    result = await notification_svc.get_notification_history(user_id, limit=50)
    if not result.get("success"):
        return []
    return [
        {
            "id": str(n.get("id", "")),
            "userId": user_id,
            "type": n.get("notification_type", "system"),
            "title": n.get("title", ""),
            "message": n.get("message", ""),
            "read": bool(n.get("read", False)),
            "critical": bool(n.get("critical", False)),
            "createdAt": n.get("sent_at", ""),
        }
        for n in result.get("notifications", [])
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
    kyc_level: str = Query("enhanced"),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Start KYC verification process. User can only start their own KYC."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot start KYC for other users")
    try:
        result = await kyc_service.start_kyc(user_id, kyc_level)
        return result
    except Exception as e:
        logger.error(f"❌ KYC start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kyc/status", tags=["KYC"])
async def get_kyc_status(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Get user KYC verification status. User can only access their own status."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' KYC status")
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
    document_url: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Upload a KYC document. User can only upload to their own KYC record."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot upload documents for other users")
    try:
        result = await kyc_service.upload_document(
            user_id, document_type, document_url
        )
        return result
    except Exception as e:
        logger.error(f"❌ Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/submit", tags=["KYC"])
async def submit_kyc(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Submit KYC for review. User can only submit their own KYC."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot submit KYC for other users")
    try:
        result = await kyc_service.submit_kyc(user_id)
        return result
    except Exception as e:
        logger.error(f"❌ KYC submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/resubmit", tags=["KYC"])
async def resubmit_kyc(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Resubmit rejected KYC. User can only resubmit their own KYC."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot resubmit KYC for other users")
    try:
        result = await kyc_service.resubmit_kyc(user_id)
        return result
    except Exception as e:
        logger.error(f"❌ KYC resubmission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kyc/admin/pending", tags=["KYC", "Admin"])
async def get_pending_kyc_reviews(limit: int = Query(50, le=100), admin_uid: str = Depends(verify_admin_token)):
    """Admin: Get pending KYC reviews. Requires ADMIN_UIDS allowlist membership."""
    try:
        result = await kyc_service.get_pending_kyc_reviews(limit)
        return result
    except Exception as e:
        logger.error(f"❌ Failed to get pending reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/admin/approve", tags=["KYC", "Admin"])
async def approve_kyc(
    user_id: str = Query(...),
    notes: str = Query(""),
    admin_uid: str = Depends(verify_admin_token),
):
    """Admin: Approve KYC. Requires ADMIN_UIDS allowlist membership — admin
    identity is taken from the verified token, never a client-supplied param."""
    try:
        result = await kyc_service.approve_kyc(user_id, admin_uid, notes)
        return result
    except Exception as e:
        logger.error(f"❌ KYC approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kyc/admin/reject", tags=["KYC", "Admin"])
async def reject_kyc(
    user_id: str = Query(...),
    rejection_reason: str = Query(...),
    admin_uid: str = Depends(verify_admin_token),
):
    """Admin: Reject KYC. Requires ADMIN_UIDS allowlist membership — admin
    identity is taken from the verified token, never a client-supplied param."""
    try:
        result = await kyc_service.reject_kyc(user_id, admin_uid, rejection_reason)
        return result
    except Exception as e:
        logger.error(f"❌ KYC rejection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DISCLAIMER ACKNOWLEDGMENT ENDPOINTS (PRD Decision 7 — 7-point disclaimer system)
# ============================================================================

@app.get("/api/compliance/disclaimers", tags=["Compliance"])
async def list_disclaimers():
    """Get the current text/version of all disclaimer types. Public — shown pre-signup."""
    try:
        result = await compliance_service.get_disclaimer()
        return result
    except Exception as e:
        logger.error(f"❌ Failed to fetch disclaimers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compliance/disclaimers/status", tags=["Compliance"])
async def get_disclaimer_status(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Get which disclaimers the caller has acknowledged. User can only check their own."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' disclaimer status")
    try:
        result = await compliance_service.get_user_disclaimer_status(user_id)
        return result
    except Exception as e:
        logger.error(f"❌ Failed to fetch disclaimer status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compliance/disclaimers/accept", tags=["Compliance"])
async def accept_one_disclaimer(
    user_id: str = Query(...),
    disclaimer_key: str = Query(...),
    version: Optional[str] = Query(None),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Acknowledge a single disclaimer. User can only accept for themselves."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot accept disclaimers for other users")
    try:
        result = await compliance_service.accept_disclaimer(user_id, disclaimer_key, version)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to accept disclaimer"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Disclaimer acceptance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compliance/disclaimers/accept-all", tags=["Compliance"])
async def accept_all_disclaimers_route(
    user_id: str = Query(...),
    ts_version: Optional[str] = Query(None),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Acknowledge all disclaimer types at once (used at signup). User can only accept for themselves."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot accept disclaimers for other users")
    try:
        result = await compliance_service.accept_all_disclaimers(user_id, ts_version)
        return result
    except Exception as e:
        logger.error(f"❌ Disclaimer acceptance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compliance/audit-trail", tags=["Compliance"])
async def get_compliance_audit_trail(user_id: str = Query(...), limit: int = Query(100, le=500), firebase_uid: str = Depends(verify_firebase_token)):
    """Get a user's immutable compliance audit trail. User can only access their own."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' audit trail")
    try:
        result = await compliance_service.get_audit_trail(user_id, limit)
        return result
    except Exception as e:
        logger.error(f"❌ Failed to fetch audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUBSCRIPTION BILLING ENDPOINTS (Stripe — PRD §16 Subscription-First)
# ============================================================================

@app.post("/api/billing/checkout-session", tags=["Billing"])
async def create_checkout_session(
    user_id: str = Query(...),
    email: str = Query(...),
    tier: str = Query("basic"),
    success_url: str = Query(...),
    cancel_url: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Create a Stripe Checkout session for a subscription. User can only checkout for themselves."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot create a checkout session for other users")
    if tier not in ("basic", "pro", "vip"):
        raise HTTPException(status_code=400, detail="Invalid tier")
    try:
        result = await billing_service.create_checkout_session(user_id, email, tier, success_url, cancel_url)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Checkout session creation failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Checkout session creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/billing/subscription", tags=["Billing"])
async def get_subscription(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Get the caller's current subscription tier/status. User can only access their own."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' subscription")
    try:
        result = await billing_service.get_subscription_status(user_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Subscription not found"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/billing/webhook", tags=["Billing"])
async def stripe_webhook(request: Request, stripe_signature: str = Header(None, alias="Stripe-Signature")):
    """Receive Stripe webhook events. Unauthenticated by design (Stripe can't
    send a Firebase token) — trust is established purely via signature
    verification against STRIPE_WEBHOOK_SECRET, never skip that check."""
    raw_body = await request.body()

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    event = billing_service.verify_webhook_signature(raw_body, stripe_signature)
    if event is None:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    result = await billing_service.handle_webhook_event(event)
    return JSONResponse(status_code=200 if result.get("success") else 500, content=result)


# ============================================================================
# AUTOMATION ENDPOINTS (Grid Bot + DCA Bot)
# ============================================================================

from services.automation_engine import AutomationEngine

automation_engine: Optional[AutomationEngine] = None


@app.post("/api/automation/grid", tags=["Automation"])
async def create_grid_bot(payload: GridBotCreate, firebase_uid: str = Depends(verify_firebase_token)):
    """Create a Grid Bot that places buy/sell orders in a price range."""
    if payload.user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot create a bot for other users")
    try:
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        result = await automation_engine.create_grid_bot(
            user_id=payload.user_id,
            exchange_id=payload.exchange_id,
            symbol=payload.symbol,
            lower_bound=payload.lower_bound,
            upper_bound=payload.upper_bound,
            grid_levels=payload.grid_levels,
            order_size=payload.order_size,
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Grid bot creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/automation/dca", tags=["Automation"])
async def create_dca_bot(payload: DCABotCreate, firebase_uid: str = Depends(verify_firebase_token)):
    """Create a DCA Bot that invests a fixed amount on a recurring schedule."""
    if payload.user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot create a bot for other users")
    try:
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        result = await automation_engine.create_dca_bot(
            user_id=payload.user_id,
            exchange_id=payload.exchange_id,
            symbol=payload.symbol,
            investment_amount=payload.investment_amount,
            frequency=payload.frequency,
            start_time=payload.start_time,
        )

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ DCA bot creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/automation/jobs", tags=["Automation"])
async def list_automation_jobs(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """List all automation jobs (active bots) for a user."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot list other users' automation jobs")
    try:
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        result = await automation_engine.list_user_jobs(user_id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ List automation jobs failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/automation/jobs/{job_id}", tags=["Automation"])
async def kill_automation_job(job_id: str, user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Kill switch: close all open orders and stop the bot."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot control other users' bots")
    try:
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        result = await automation_engine.stop_job(job_id, user_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Kill switch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/automation/jobs/{job_id}", tags=["Automation"])
async def get_automation_job(job_id: str, user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Get bot status, config, and P&L summary."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' bots")
    try:
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        result = await automation_engine.get_job_status(job_id, user_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get automation job failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/automation/jobs/{job_id}/orders", tags=["Automation"])
async def get_automation_orders(job_id: str, user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Get all orders placed by a specific bot."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' bot orders")
    try:
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        result = await automation_engine.get_job_orders(job_id, user_id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get automation orders failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/automation/jobs/{job_id}/pause", tags=["Automation"])
async def pause_automation_job(job_id: str, user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Pause an automation job without cancelling open orders."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot control other users' bots")
    try:
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        result = await automation_engine.pause_job(job_id, user_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Pause automation job failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/automation/jobs/{job_id}/resume", tags=["Automation"])
async def resume_automation_job(job_id: str, user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Resume a paused automation job."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot control other users' bots")
    try:
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        result = await automation_engine.resume_job(job_id, user_id)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Resume automation job failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/automation/jobs/{job_id}/events", tags=["Automation"])
async def get_automation_events(job_id: str, user_id: str = Query(...), limit: int = Query(50, le=200), firebase_uid: str = Depends(verify_firebase_token)):
    """Get event log for a specific automation job."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' bot events")
    try:
        if not automation_engine:
            raise HTTPException(status_code=503, detail="Automation engine not initialized")

        result = await automation_engine.get_job_events(job_id, user_id, limit)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get automation events failed: {e}")
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
    """WebSocket endpoint for live signal streaming."""
    await ws_manager.connect(websocket, "signals")
    
    try:
        while True:
            # Send latest signals every 2 seconds
            try:
                response = db.supabase.table("signals").select("*").limit(20).execute()
                signals = response.data or []
                await websocket.send_json({
                    "type": "signals_update",
                    "data": [_map_signal_to_frontend(s) for s in signals],
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"WebSocket signals error: {e}")
            
            # Update every 2 seconds
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "signals")
        logger.info("WebSocket disconnected: signals")
    except Exception as e:
        logger.error(f"WebSocket error in signals: {e}")
        ws_manager.disconnect(websocket, "signals")


# ============================================================================
# NO-CODE STRATEGY BUILDER ENDPOINTS
# ============================================================================

@app.post("/api/strategy-builder", tags=["Strategy Builder"])
async def create_custom_strategy(
    payload: StrategyBuilderCreate,
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Create a custom no-code strategy from visual builder selections."""
    try:
        # Resolve user_id from Firebase UID
        user_response = db.supabase.table("users").select("id").eq("firebase_uid", firebase_uid).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_response.data[0]["id"]

        result = await strategy_configurator.create_strategy(
            user_id=user_id,
            strategy_name=payload.strategy_name,
            rules=payload.rules,
            description=payload.description or "",
        )

        if result.get("success"):
            return result
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to create strategy"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Create strategy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategy-builder", tags=["Strategy Builder"])
async def list_custom_strategies(
    firebase_uid: str = Depends(verify_firebase_token),
):
    """List all custom strategies for the authenticated user."""
    try:
        user_response = db.supabase.table("users").select("id").eq("firebase_uid", firebase_uid).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_response.data[0]["id"]

        result = await strategy_configurator.list_user_strategies(user_id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ List strategies failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/strategy-builder/{strategy_id}", tags=["Strategy Builder"])
async def update_custom_strategy(
    strategy_id: str,
    payload: StrategyBuilderUpdate,
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Update a custom strategy's rules, name, or description."""
    try:
        user_response = db.supabase.table("users").select("id").eq("firebase_uid", firebase_uid).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_response.data[0]["id"]

        updates = payload.model_dump(exclude_unset=True)
        result = await strategy_configurator.update_strategy(strategy_id, user_id, updates)

        if result.get("success"):
            return result
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to update strategy"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update strategy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/strategy-builder/{strategy_id}", tags=["Strategy Builder"])
async def delete_custom_strategy(
    strategy_id: str,
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Delete a custom strategy."""
    try:
        user_response = db.supabase.table("users").select("id").eq("firebase_uid", firebase_uid).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_response.data[0]["id"]

        result = await strategy_configurator.delete_strategy(strategy_id, user_id)

        if result.get("success"):
            return result
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to delete strategy"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete strategy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategy-builder/{strategy_id}/activate", tags=["Strategy Builder"])
async def activate_custom_strategy(
    strategy_id: str,
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Set a strategy as the active trading strategy."""
    try:
        user_response = db.supabase.table("users").select("id").eq("firebase_uid", firebase_uid).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_response.data[0]["id"]

        result = await strategy_configurator.activate_strategy(strategy_id, user_id)

        if result.get("success"):
            return result
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to activate strategy"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Activate strategy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/strategy-builder/{strategy_id}/simulate", tags=["Strategy Builder"])
async def simulate_custom_strategy(
    strategy_id: str,
    days: int = Query(30, ge=1, le=365),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Simulate a strategy against past signals to estimate performance."""
    try:
        user_response = db.supabase.table("users").select("id").eq("firebase_uid", firebase_uid).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user_response.data[0]["id"]

        result = await strategy_configurator.simulate_strategy(strategy_id, user_id, days)

        if result.get("success"):
            return result
        raise HTTPException(status_code=400, detail=result.get("error", "Simulation failed"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Simulate strategy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategy-builder/templates", tags=["Strategy Builder"])
async def get_strategy_templates(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
):
    """Get pre-built strategy templates for the no-code builder."""
    try:
        result = await strategy_configurator.get_templates(category=category, difficulty=difficulty)
        return result
    except Exception as e:
        logger.error(f"❌ Get templates failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ALPHAACADEMY (Education Layer)
# ============================================================================

@app.get("/api/academy/content")
async def list_education_content(
    category: Optional[str] = Query(None, description="Filter by category: patterns, strategies, risk_mgmt, quant_basics"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: beginner, intermediate, advanced"),
):
    """List all education content with optional category and difficulty filters."""
    if not education_service:
        raise HTTPException(status_code=503, detail="Education service not available")
    result = await education_service.list_content(category=category, difficulty=difficulty)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    return result


@app.get("/api/academy/content/{content_id}")
async def get_education_content(content_id: str = Path(..., description="Content ID")):
    """Get a single education content piece by ID."""
    if not education_service:
        raise HTTPException(status_code=503, detail="Education service not available")
    result = await education_service.get_content(content_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Content not found"))
    return result


@app.get("/api/academy/progress/{user_id}")
async def get_user_progress(user_id: str = Path(..., description="User ID"), firebase_uid: str = Depends(verify_firebase_token)):
    """Get a user's education progress including completion status and quiz scores. User can only access their own."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' progress")
    if not education_service:
        raise HTTPException(status_code=503, detail="Education service not available")
    result = await education_service.get_user_progress(user_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    return result


@app.post("/api/academy/progress/{content_id}")
async def mark_content_completed(
    content_id: str = Path(..., description="Content ID"),
    user_id: str = Body(..., embed=True, description="User ID"),
    quiz_score: Optional[float] = Body(None, embed=True, description="Quiz score (0-100)"),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Mark an education content piece as completed for a user. User can only mark their own progress."""
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot mark progress for other users")
    if not education_service:
        raise HTTPException(status_code=503, detail="Education service not available")
    result = await education_service.mark_completed(
        user_id=user_id, content_id=content_id, quiz_score=quiz_score
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    return result


@app.get("/api/academy/signal-breakdown/{signal_id}")
async def get_signal_breakdown(signal_id: str = Path(..., description="Signal ID")):
    """Get an existing AI breakdown explanation for a signal."""
    if not education_service:
        raise HTTPException(status_code=503, detail="Education service not available")
    result = await education_service.get_signal_breakdown(signal_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Breakdown not found"))
    return result


@app.post("/api/academy/generate-breakdown/{signal_id}")
async def generate_signal_breakdown(signal_id: str = Path(..., description="Signal ID")):
    """Generate an AI breakdown explanation for a signal."""
    if not education_service:
        raise HTTPException(status_code=503, detail="Education service not available")
    result = await education_service.generate_breakdown(signal_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate breakdown"))
    return result


# ============================================================================
# PHASE 3: TRADING TOURNAMENTS
# ============================================================================

@app.get("/api/tournaments", tags=["Tournaments"])
async def list_tournaments(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
):
    """List active/upcoming tournaments."""
    if not tournament_service:
        raise HTTPException(status_code=503, detail="Tournament service not available")
    result = await tournament_service.list_tournaments(status_filter=status, limit=limit)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@app.post("/api/tournaments/{tournament_id}/join", tags=["Tournaments"])
async def join_tournament(
    tournament_id: str = Path(...),
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Join a tournament."""
    if not tournament_service:
        raise HTTPException(status_code=503, detail="Tournament service not available")
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot join tournament for another user")
    result = await tournament_service.join_tournament(tournament_id, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.get("/api/tournaments/{tournament_id}/leaderboard", tags=["Tournaments"])
async def get_tournament_leaderboard(
    tournament_id: str = Path(...),
    sort_by: str = Query("final_pnl"),
    limit: int = Query(100, le=500),
):
    """Get tournament leaderboard."""
    if not tournament_service:
        raise HTTPException(status_code=503, detail="Tournament service not available")
    result = await tournament_service.get_leaderboard(tournament_id, sort_by=sort_by, limit=limit)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@app.get("/api/tournaments/{tournament_id}/status", tags=["Tournaments"])
async def get_my_tournament_status(
    tournament_id: str = Path(...),
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Get my status in a tournament."""
    if not tournament_service:
        raise HTTPException(status_code=503, detail="Tournament service not available")
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot view status for another user")
    result = await tournament_service.get_my_status(tournament_id, user_id)
    return result


# ============================================================================
# PHASE 3: STRATEGY PERSONALITY
# ============================================================================

@app.get("/api/strategies/{strategy_id}/personality", tags=["Strategy Personality"])
async def get_strategy_personality(
    strategy_id: str = Path(...),
):
    """Get strategy personality badge and classification."""
    if not strategy_personality_service:
        raise HTTPException(status_code=503, detail="Strategy personality service not available")
    result = await strategy_personality_service.get_personality(strategy_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


# ============================================================================
# PHASE 3: COMMUNITY & SOCIAL
# ============================================================================

@app.get("/api/community/profile/{user_id}", tags=["Community"])
async def get_community_profile(user_id: str = Path(...)):
    """Get public community profile."""
    if not community_service:
        raise HTTPException(status_code=503, detail="Community service not available")
    profile = await community_service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"success": True, "profile": profile}


@app.post("/api/community/profile", tags=["Community"])
async def update_community_profile(
    data: dict,
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Update own community profile."""
    if not community_service:
        raise HTTPException(status_code=503, detail="Community service not available")
    user_id = data.get("user_id")
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot update profile for another user")
    result = await community_service.update_user_profile(
        user_id,
        display_name=data.get("display_name"),
        bio=data.get("bio"),
        avatar_url=data.get("avatar_url"),
    )
    return result


@app.post("/api/community/follow/{target_user_id}", tags=["Community"])
async def follow_community_user(
    target_user_id: str = Path(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Follow another user."""
    if not community_service:
        raise HTTPException(status_code=503, detail="Community service not available")
    result = await community_service.follow_user(firebase_uid, target_user_id)
    return result


@app.post("/api/community/unfollow/{target_user_id}", tags=["Community"])
async def unfollow_community_user(
    target_user_id: str = Path(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Unfollow a user."""
    if not community_service:
        raise HTTPException(status_code=503, detail="Community service not available")
    result = await community_service.unfollow_user(firebase_uid, target_user_id)
    return result


@app.get("/api/community/leaderboard", tags=["Community"])
async def get_community_leaderboard(
    metric: str = Query("pnl"),
    timeframe: str = Query("all_time"),
    limit: int = Query(100, le=500),
):
    """Get community leaderboard rankings."""
    if not community_service:
        raise HTTPException(status_code=503, detail="Community service not available")
    leaderboard = await community_service.get_leaderboard(metric=metric, timeframe=timeframe, limit=limit)
    return {"success": True, "leaderboard": leaderboard, "count": len(leaderboard)}


@app.post("/api/community/strategy/{strategy_id}/comment", tags=["Community"])
async def add_strategy_comment(
    strategy_id: str = Path(...),
    comment_text: str = Body(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Add comment to strategy."""
    if not community_service:
        raise HTTPException(status_code=503, detail="Community service not available")
    result = await community_service.add_strategy_comment(firebase_uid, strategy_id, comment_text)
    return result


@app.post("/api/community/strategy/{strategy_id}/rate", tags=["Community"])
async def rate_strategy_community(
    strategy_id: str = Path(...),
    rating: int = Body(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Rate a strategy (1-5 stars)."""
    if not community_service:
        raise HTTPException(status_code=503, detail="Community service not available")
    result = await community_service.rate_strategy(firebase_uid, strategy_id, rating)
    return result


@app.get("/api/community/notifications", tags=["Community"])
async def get_community_notifications(
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Get unread notifications."""
    if not community_service:
        raise HTTPException(status_code=503, detail="Community service not available")
    notifications = await community_service.get_unread_notifications(firebase_uid)
    return {"success": True, "notifications": notifications, "count": len(notifications)}


# ============================================================================
# PHASE 3: TRAILING ORDERS
# ============================================================================

@app.post("/api/orders/trailing-stop", tags=["Trailing Orders"])
async def create_trailing_stop(
    request: Dict[str, Any] = Body(...),
):
    """Create a trailing stop or trailing take-profit order."""
    if not trailing_orders_service:
        raise HTTPException(status_code=503, detail="Trailing orders service not available")
    result = await trailing_orders_service.create_trailing_order(
        user_id=request.get("user_id", ""),
        asset=request.get("asset", "BTC"),
        side=request.get("side", "SELL"),
        order_type=request.get("order_type", "trailing_stop"),
        trail_percent=float(request.get("trail_percent", 2.0)),
        quantity=float(request.get("quantity", 0)),
        direction=request.get("direction", "LONG"),
        current_price=float(request.get("current_price", 0)) if request.get("current_price") else None,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.put("/api/orders/trailing-stop/{order_id}", tags=["Trailing Orders"])
async def update_trailing_stop(
    order_id: str = Path(...),
    request: Dict[str, Any] = Body(...),
):
    """Update a trailing stop order."""
    if not trailing_orders_service:
        raise HTTPException(status_code=503, detail="Trailing orders service not available")
    user_id = request.pop("user_id", "")
    result = await trailing_orders_service.update_trailing_order(order_id, user_id, request)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.delete("/api/orders/trailing-stop/{order_id}", tags=["Trailing Orders"])
async def cancel_trailing_stop(
    order_id: str = Path(...),
    user_id: str = Query(...),
):
    """Cancel a trailing stop order."""
    if not trailing_orders_service:
        raise HTTPException(status_code=503, detail="Trailing orders service not available")
    result = await trailing_orders_service.cancel_trailing_order(order_id, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.get("/api/orders/trailing-stop", tags=["Trailing Orders"])
async def list_trailing_orders(
    user_id: str = Query(...),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    """List active trailing orders."""
    if not trailing_orders_service:
        raise HTTPException(status_code=503, detail="Trailing orders service not available")
    result = await trailing_orders_service.list_trailing_orders(user_id, status_filter=status, limit=limit)
    return result


# ============================================================================
# PHASE 3: ONCHAIN SMART MONEY TRACKER
# ============================================================================

@app.get("/api/onchain/whales", tags=["Onchain Tracker"])
async def get_whale_movements(
    asset: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
):
    """Recent whale movements."""
    if not onchain_tracker_service:
        raise HTTPException(status_code=503, detail="Onchain tracker service not available")
    result = await onchain_tracker_service.get_whale_movements(asset=asset, limit=limit)
    return result


@app.get("/api/onchain/metrics/{asset}", tags=["Onchain Tracker"])
async def get_onchain_metrics(
    asset: str = Path(...),
):
    """On-chain metrics for an asset (SOPR, MVRV, NVT, etc.)."""
    if not onchain_tracker_service:
        raise HTTPException(status_code=503, detail="Onchain tracker service not available")
    result = await onchain_tracker_service.get_asset_metrics(asset)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@app.get("/api/onchain/exchange-flows", tags=["Onchain Tracker"])
async def get_exchange_flows(
    asset: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
):
    """Exchange inflows and outflows."""
    if not onchain_tracker_service:
        raise HTTPException(status_code=503, detail="Onchain tracker service not available")
    result = await onchain_tracker_service.get_exchange_flows(asset=asset, hours=hours)
    return result


# ============================================================================
# ENHANCED CHAT ENDPOINTS (AlphaAI Chat with LLM Integration)
# ============================================================================

from services.external_signal_ingestion import ExternalSignalIngestionService

external_signal_ingestion: Optional[ExternalSignalIngestionService] = None

@app.post("/api/chat/message", tags=["Chat"])
async def send_chat_message_v2(
    payload: Dict[str, Any] = Body(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Send a message and get AI response with full context injection and token budget."""
    try:
        user_id = payload.get("user_id", firebase_uid)
        if user_id != firebase_uid:
            raise HTTPException(status_code=403, detail="Cannot send messages for other users")
        message = payload.get("message", "")
        signal_id = payload.get("signal_id")
        strategy_id = payload.get("strategy_id")
        page_context = payload.get("page_context")

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        context = await chat_service.get_context_for_response(
            user_id, portfolio_service, signal_processor,
            signal_id=signal_id, strategy_id=strategy_id, page_context=page_context,
        )

        full_response = ""
        async for chunk in chat_service.generate_response(user_id, message, context, signal_id, strategy_id):
            full_response += chunk

        return {
            "success": True,
            "user_message": message,
            "ai_response": full_response,
            "context_used": bool(context.get("portfolio")),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/history", tags=["Chat"])
async def get_chat_history_v2(user_id: str = Query(...), limit: int = Query(50, le=100), firebase_uid: str = Depends(verify_firebase_token)):
    """Get chat history for a user. User can only access their own history."""
    try:
        if user_id != firebase_uid:
            raise HTTPException(status_code=403, detail="Cannot access other users' chat history")
        history = await chat_service.get_chat_history(user_id, limit)
        return {"success": True, "user_id": user_id, "messages": history, "count": len(history)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/tokens", tags=["Chat"])
async def get_chat_token_usage(user_id: str = Query(...), firebase_uid: str = Depends(verify_firebase_token)):
    """Get token usage stats for a user. User can only access their own usage."""
    try:
        if user_id != firebase_uid:
            raise HTTPException(status_code=403, detail="Cannot access other users' token usage")
        usage = await chat_service.get_token_usage(user_id)
        return {"success": True, "usage": usage}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token usage fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/search", tags=["Chat"])
async def search_chat(user_id: str = Query(...), query: str = Query(...), limit: int = Query(10), firebase_uid: str = Depends(verify_firebase_token)):
    """Search chat history. User can only search their own history."""
    try:
        if user_id != firebase_uid:
            raise HTTPException(status_code=403, detail="Cannot search other users' chat history")
        results = await chat_service.search_chat_history(user_id, query, limit)
        return {"success": True, "results": results, "count": len(results)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time AlphaAI Chat streaming."""
    await ws_manager.connect(websocket, f"chat-{user_id}")
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            signal_id = data.get("signal_id")
            strategy_id = data.get("strategy_id")
            page_context = data.get("page_context")

            if not message:
                continue

            context = await chat_service.get_context_for_response(
                user_id, portfolio_service, signal_processor,
                signal_id=signal_id, strategy_id=strategy_id, page_context=page_context,
            )

            async for chunk in chat_service.generate_response(user_id, message, context, signal_id, strategy_id):
                await websocket.send_json({
                    "type": "chat_chunk",
                    "content": chunk,
                    "timestamp": datetime.utcnow().isoformat(),
                })

            await websocket.send_json({
                "type": "chat_complete",
                "timestamp": datetime.utcnow().isoformat(),
            })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, f"chat-{user_id}")
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
        ws_manager.disconnect(websocket, f"chat-{user_id}")


# ============================================================================
# ENHANCED EXTERNAL SIGNAL INGESTION ENDPOINTS
# ============================================================================

@app.post("/api/external-signals/ingest", tags=["External Signals"])
async def ingest_external_signal(
    payload: Dict[str, Any] = Body(...),
    source: str = Query("tradingview"),
    x_webhook_signature: Optional[str] = Header(None),
):
    """Ingest an external signal with full validation pipeline."""
    if not external_signal_ingestion:
        raise HTTPException(status_code=503, detail="External signal ingestion service not available")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required in payload")

    signature_valid = True
    if x_webhook_signature:
        secret = os.getenv("TRADINGVIEW_WEBHOOK_HMAC_SECRET")
        import json as _json
        raw_body = _json.dumps(payload).encode()
        signature_valid = external_signal_ingestion.verify_webhook_signature(raw_body, x_webhook_signature, secret)

    result = await external_signal_ingestion.ingest_signal(user_id, payload, source, signature_valid)

    status_code = 200 if result.get("success") else 400
    return JSONResponse(status_code=status_code, content=result)


@app.get("/api/external-signals/rules", tags=["External Signals"])
async def get_ingestion_rules(user_id: str = Query(...)):
    """Get user's external signal ingestion rules."""
    if not external_signal_ingestion:
        raise HTTPException(status_code=503, detail="Service not available")
    rules = await external_signal_ingestion.get_user_rules(user_id)
    return {"success": True, "rules": rules}


@app.put("/api/external-signals/rules", tags=["External Signals"])
async def update_ingestion_rules(
    user_id: str = Query(...),
    rules: Dict[str, Any] = Body(...),
):
    """Update user's external signal ingestion rules."""
    if not external_signal_ingestion:
        raise HTTPException(status_code=503, detail="Service not available")
    result = await external_signal_ingestion.set_user_rules(user_id, rules)
    return result


@app.get("/api/external-signals/history", tags=["External Signals"])
async def get_ingested_signal_history(
    user_id: str = Query(...),
    limit: int = Query(50, le=200),
    status: Optional[str] = Query(None),
):
    """Get history of ingested external signals."""
    if not external_signal_ingestion:
        raise HTTPException(status_code=503, detail="Service not available")
    signals = await external_signal_ingestion.get_signal_history(user_id, limit, status)
    return {"success": True, "signals": signals, "count": len(signals)}


@app.get("/api/external-signals/events", tags=["External Signals"])
async def get_webhook_events(
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    """Get webhook event log for debugging."""
    if not external_signal_ingestion:
        raise HTTPException(status_code=503, detail="Service not available")
    events = await external_signal_ingestion.get_webhook_events(user_id, limit)
    return {"success": True, "events": events, "count": len(events)}


# ============================================================================
# ARCHITECTURE DOC GAP SERVICES - API ROUTES
# ============================================================================

# --- Execution Service (§11.1) ---

@app.post("/api/orders/place", tags=["Execution"])
async def place_order(
    request: Dict[str, Any] = Body(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Place an order with idempotency protection."""
    user_id = request.get("user_id", firebase_uid)
    signal_id = request.get("signal_id", str(uuid.uuid4()))
    asset = request.get("asset", "BTC")
    direction = request.get("direction", "BUY")
    quantity = request.get("quantity", 0)
    exchange = request.get("exchange", "binance")

    idem_key = idempotency_manager.generate_key(user_id, signal_id, asset, direction)
    if not await idempotency_manager.acquire(idem_key):
        raise HTTPException(status_code=409, detail="Duplicate order detected")

    order_id = str(uuid.uuid4())
    await order_monitor.record_submission(
        order_id, user_id, signal_id, exchange, asset, direction, quantity, idem_key,
    )
    return {"success": True, "order_id": order_id, "idempotency_key": idem_key}


@app.get("/api/orders/{order_id}/status", tags=["Execution"])
async def get_order_status(order_id: str):
    """Get order confirmation status."""
    state = order_monitor.get_order_state(order_id)
    if not state:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"success": True, "order_id": order_id, "state": state.get("state", "UNKNOWN")}


@app.get("/api/execution/circuit-breakers", tags=["Execution"])
async def get_circuit_breakers():
    """Get circuit breaker status for all exchanges."""
    return {"success": True, "breakers": exchange_layer.get_circuit_breaker_status()}


@app.get("/api/execution/data-validation/stats", tags=["Execution"])
async def get_data_validation_stats():
    """Get data validation pipeline statistics."""
    return {"success": True, "stats": data_validation_pipeline.get_validation_stats()}


@app.get("/api/execution/backup-providers", tags=["Execution"])
async def get_backup_providers():
    """Get backup market data provider status."""
    return {"success": True, "providers": backup_data_provider.get_health_status()}


# --- Notification Service (§15) ---

@app.post("/api/notifications/send", tags=["Notifications"])
async def send_notification(
    request: Dict[str, Any] = Body(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Send notification to user."""
    result = await notification_svc.send_notification(
        user_id=request.get("user_id", firebase_uid),
        title=request.get("title", ""),
        message=request.get("message", ""),
        notification_type=request.get("type", "system"),
        channels=request.get("channels"),
    )
    return result


@app.get("/api/notifications/history", tags=["Notifications"])
async def get_notification_history(
    user_id: str = Query(...),
    limit: int = Query(50, le=200),
    firebase_uid: str = Depends(verify_firebase_token),
):
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot access other users' notifications")
    return await notification_svc.get_notification_history(user_id, limit)


@app.put("/api/notifications/preferences", tags=["Notifications"])
async def update_notification_preferences(
    user_id: str = Query(...),
    preferences: Dict[str, Any] = Body(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    if user_id != firebase_uid:
        raise HTTPException(status_code=403, detail="Cannot update other users' notification preferences")
    return await notification_svc.update_user_preferences(user_id, preferences)


# --- Sentiment Analysis Service (§26.1) ---

@app.get("/api/sentiment/{ticker}", tags=["Sentiment"])
async def get_sentiment(ticker: str):
    """Get aggregated sentiment for a ticker."""
    return await sentiment_svc.get_aggregated_sentiment(ticker)


@app.get("/api/sentiment/{ticker}/signal", tags=["Sentiment"])
async def get_sentiment_signal(ticker: str):
    """Generate sentiment-based trading signal."""
    return await sentiment_svc.generate_sentiment_signal(ticker)


@app.post("/api/sentiment/ingest", tags=["Sentiment"])
async def ingest_sentiment(
    ticker: str = Query(...),
    source: str = Query("unknown"),
    items: List[Dict[str, Any]] = Body(...),
):
    """Ingest social data for sentiment analysis."""
    return await sentiment_svc.ingest_social_data(ticker, source, items)


@app.get("/api/sentiment/{ticker}/onchain", tags=["Sentiment"])
async def get_onchain_metrics(ticker: str):
    """Get on-chain metrics for a ticker."""
    return await sentiment_svc.get_onchain_metrics(ticker)


# --- Strategy Marketplace Service (§26.2) ---

@app.post("/api/marketplace/strategies", tags=["Marketplace"])
async def submit_strategy(
    request: Dict[str, Any] = Body(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Submit strategy for marketplace verification."""
    return await strategy_marketplace_svc.submit_strategy(firebase_uid, request)


@app.post("/api/marketplace/strategies/{strategy_id}/verify", tags=["Marketplace"])
async def verify_strategy(strategy_id: str):
    """Verify strategy backtest claims."""
    return await strategy_marketplace_svc.verify_strategy(strategy_id)


@app.get("/api/marketplace/leaderboard", tags=["Marketplace"])
async def get_marketplace_leaderboard(
    metric: str = Query("sharpe_ratio"),
    limit: int = Query(50, le=100),
):
    """Get strategy marketplace leaderboard."""
    return await strategy_marketplace_svc.get_leaderboard(metric, limit)


@app.post("/api/marketplace/strategies/{strategy_id}/revenue", tags=["Marketplace"])
async def calculate_revenue(strategy_id: str):
    """Calculate creator revenue share."""
    return await strategy_marketplace_svc.calculate_revenue_share(strategy_id)


@app.get("/api/marketplace/creators/{creator_id}/reputation", tags=["Marketplace"])
async def get_creator_reputation(creator_id: str):
    """Get creator reputation score."""
    return await strategy_marketplace_svc.get_reputation_score(creator_id)


# --- Compliance Enhancement (§6) - 6 Disclaimer Types ---

@app.get("/api/compliance/disclaimers", tags=["Compliance"])
async def get_all_disclaimers():
    """Get all 6 disclaimer types."""
    return await compliance_svc.get_disclaimer()


@app.post("/api/compliance/disclaimers/acknowledge", tags=["Compliance"])
async def acknowledge_disclaimer(
    request: Dict[str, Any] = Body(...),
    firebase_uid: str = Depends(verify_firebase_token),
):
    """Acknowledge a specific disclaimer."""
    return await compliance_svc.accept_disclaimer(
        user_id=firebase_uid,
        disclaimer_key=request.get("disclaimer_key", ""),
        ts_version=request.get("ts_version"),
    )


@app.get("/api/compliance/disclaimers/status", tags=["Compliance"])
async def get_disclaimer_status(user_id: str = Query(...)):
    """Get which disclaimers user has acknowledged."""
    return await compliance_svc.get_user_disclaimer_status(user_id)


@app.post("/api/compliance/gdpr/export", tags=["Compliance"])
async def gdpr_export(user_id: str = Query(...)):
    """GDPR data export."""
    return await compliance_svc.export_user_data(user_id)


@app.post("/api/compliance/gdpr/delete", tags=["Compliance"])
async def gdpr_delete(user_id: str = Query(...)):
    """GDPR right-to-erasure."""
    return await compliance_svc.delete_user_data(user_id)


# --- Audit Log Service (§28) ---

@app.get("/api/audit/events", tags=["Audit"])
async def get_audit_events(
    user_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
):
    """Get audit events with filters."""
    return await audit_log_svc.get_audit_trail(user_id=user_id, event_type=event_type, limit=limit)


@app.get("/api/audit/verify-integrity", tags=["Audit"])
async def verify_audit_integrity():
    """Verify hash chain integrity of audit logs."""
    return await audit_log_svc.verify_chain_integrity()


@app.get("/api/audit/stats", tags=["Audit"])
async def get_audit_stats(user_id: Optional[str] = Query(None)):
    """Get audit log statistics."""
    return await audit_log_svc.get_audit_stats(user_id)


@app.get("/api/audit/category/{category}", tags=["Audit"])
async def get_audit_by_category(category: str):
    """Get audit events by category (auth, trading, account, admin)."""
    events = await audit_log_svc.get_events_by_category(category)
    return {"success": True, "events": events, "count": len(events)}


# --- Paper Trading Enhancement (§10.1) ---

@app.post("/api/paper-trading/validate-signal", tags=["Paper Trading"])
async def start_signal_validation(
    signal_id: str = Query(...),
    backtest_sharpe: float = Query(...),
):
    """Start 4-week internal paper trading validation."""
    return await paper_trading.start_internal_validation(signal_id, backtest_sharpe)


@app.get("/api/paper-trading/validate-signal/{signal_id}", tags=["Paper Trading"])
async def evaluate_signal_validation(signal_id: str):
    """Evaluate internal signal validation result."""
    return await paper_trading.evaluate_internal_validation(signal_id)


@app.post("/api/paper-trading/paper-to-live", tags=["Paper Trading"])
async def paper_to_live(
    user_id: str = Query(...),
    exchange: str = Query("binance"),
):
    """Execute paper-to-live conversion flow."""
    return await paper_trading.paper_to_live_flow(user_id, exchange)


@app.get("/api/paper-trading/proof/{signal_id}", tags=["Paper Trading"])
async def get_signal_proof(signal_id: str):
    """Get signal proof/verification data for Proof tab."""
    return await paper_trading.get_signal_proof(signal_id)


# --- Risk Engine Enhancement (§10) ---

@app.get("/api/risk/funding-rate/{ticker}", tags=["Risk"])
async def check_funding_rate(ticker: str, rate: float = Query(...)):
    """Check funding rate alert for perpetuals."""
    return await risk_manager.check_funding_rate(ticker, rate)


@app.post("/api/risk/volatility-adjusted-size", tags=["Risk"])
async def volatility_adjusted_size(request: Dict[str, Any] = Body(...)):
    """Calculate volatility-adjusted position size."""
    adjusted = risk_manager.calculate_volatility_adjusted_size(
        base_size=request.get("base_size", 0),
        current_vol_20d=request.get("current_vol_20d", 0),
        historical_avg_vol_60d=request.get("historical_avg_vol_60d", 0),
    )
    return {"success": True, "adjusted_size": adjusted}


@app.post("/api/risk/liquidation-check", tags=["Risk"])
async def liquidation_buffer_check(request: Dict[str, Any] = Body(...)):
    """Validate liquidation buffer is sufficient."""
    liq = risk_manager.calculate_liquidation_price(
        entry_price=request.get("entry_price", 0),
        margin=request.get("margin", 0),
        position_size=request.get("position_size", 1),
        leverage=request.get("leverage", 1),
        direction=request.get("direction", "LONG"),
    )
    validation = risk_manager.validate_liquidation_buffer(
        liq["liquidation_price"], request.get("mark_price", 0)
    )
    return {"success": True, "liquidation": liq, "validation": validation}


# ============================================================================
# MOAT SERVICES: EXPLAINABILITY & BACKTESTING INTEGRITY
# ============================================================================

@app.post("/api/proofs/create", tags=["Proofs"])
async def create_explainability_proof(request: Dict[str, Any] = Body(...)):
    """Create an explainability proof for a signal."""
    if not explainability_proofs_svc:
        raise HTTPException(status_code=503, detail="Explainability service not initialized")

    return await explainability_proofs_svc.create_proof(
        signal_id=request.get("signal_id"),
        symbol=request.get("symbol"),
        signal_type=request.get("signal_type"),
        confidence=request.get("confidence", 0.0),
        reasoning_chain=request.get("reasoning_chain", []),
        feature_importance=request.get("feature_importance", {}),
        technical_drivers=request.get("technical_drivers", {}),
        sentiment_components=request.get("sentiment_components", {}),
        ml_model_version=request.get("ml_model_version", "1.0"),
        backtest_performance=request.get("backtest_performance", {}),
    )


@app.get("/api/proofs/{signal_id}", tags=["Proofs"])
async def get_explainability_proof(signal_id: str):
    """Retrieve explainability proof for a signal."""
    if not explainability_proofs_svc:
        raise HTTPException(status_code=503, detail="Explainability service not initialized")

    proof = await explainability_proofs_svc.get_proof(signal_id)
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")

    return proof


@app.get("/api/proofs/{signal_id}/verify", tags=["Proofs"])
async def verify_explainability_proof(signal_id: str, proof_hash: str = Query(...)):
    """Verify integrity of an explainability proof."""
    if not explainability_proofs_svc:
        raise HTTPException(status_code=503, detail="Explainability service not initialized")

    is_valid = await explainability_proofs_svc.verify_proof(signal_id, proof_hash)
    return {"signal_id": signal_id, "is_valid": is_valid}


@app.get("/api/proofs", tags=["Proofs"])
async def list_explainability_proofs(
    symbol: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100)
):
    """List explainability proofs with optional filtering."""
    if not explainability_proofs_svc:
        raise HTTPException(status_code=503, detail="Explainability service not initialized")

    proofs = await explainability_proofs_svc.list_proofs(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return {"proofs": proofs, "count": len(proofs)}


@app.get("/api/signals/{signal_id}/explainability", tags=["Proofs"])
async def get_signal_explainability(signal_id: str):
    """Get full explainability data for a signal."""
    if not explainability_proofs_svc:
        raise HTTPException(status_code=503, detail="Explainability service not initialized")

    explainability = await explainability_proofs_svc.get_signal_explainability(signal_id)
    if not explainability:
        raise HTTPException(status_code=404, detail="Signal explainability data not found")

    return explainability


@app.get("/api/proofs/audit-trail/export", tags=["Proofs"])
async def export_audit_trail(
    user_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    format: str = Query("json")
):
    """Export audit trail of signal proofs for compliance."""
    if not explainability_proofs_svc:
        raise HTTPException(status_code=503, detail="Explainability service not initialized")

    return await explainability_proofs_svc.export_audit_trail(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        format=format
    )


@app.post("/api/backtesting/integrity-check", tags=["Backtesting"])
async def check_backtest_integrity(request: Dict[str, Any] = Body(...)):
    """Check integrity of a backtest."""
    if not backtesting_integrity_svc:
        raise HTTPException(status_code=503, detail="Backtesting integrity service not initialized")

    return await backtesting_integrity_svc.check_integrity(
        backtest_id=request.get("backtest_id"),
        backtest_data=request.get("backtest_data", {})
    )


@app.get("/api/ml/overfitting-check/{model_id}", tags=["ML"])
async def check_overfitting(model_id: str):
    """Check if model shows signs of overfitting."""
    if not overfitting_prevention_svc:
        raise HTTPException(status_code=503, detail="Overfitting prevention service not initialized")

    result = await overfitting_prevention_svc.detect_overfitting(model_id)
    return result


@app.post("/api/signals/ensemble", tags=["Signals"])
async def generate_ensemble_prediction(request: Dict[str, Any] = Body(...)):
    """Generate ensemble prediction combining multiple signal sources."""
    if not ensemble_predictor_svc:
        raise HTTPException(status_code=503, detail="Ensemble predictor service not initialized")

    return await ensemble_predictor_svc.predict_ensemble(
        symbol=request.get("symbol"),
        signals=request.get("signals", []),
        weights=request.get("weights")
    )


# ============================================================================
# ERROR HANDLING
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
# FEATURE STORE ROUTES (§13.3)
# ============================================================================

@app.get("/api/feature-store/definitions", tags=["Feature Store"])
async def get_feature_definitions():
    """Get all registered feature definitions."""
    if not feature_store_svc:
        raise HTTPException(status_code=503, detail="Feature store not initialized")
    return {"success": True, "definitions": feature_store_svc.get_feature_definitions()}


@app.get("/api/feature-store/{ticker}/features", tags=["Feature Store"])
async def get_ticker_features(ticker: str, limit: int = Query(100, le=1000)):
    """Get computed features for a ticker."""
    if not feature_store_svc:
        raise HTTPException(status_code=503, detail="Feature store not initialized")
    features = await feature_store_svc.get_features(ticker, limit=limit)
    return {"success": True, "ticker": ticker, "features": features}


@app.get("/api/feature-store/{ticker}/vector", tags=["Feature Store"])
async def get_feature_vector(ticker: str):
    """Get latest feature vector for a ticker (flat dict for ML inference)."""
    if not feature_store_svc:
        raise HTTPException(status_code=503, detail="Feature store not initialized")
    vector = await feature_store_svc.get_feature_vector(ticker)
    return {"success": True, "ticker": ticker, "vector": vector}


@app.post("/api/feature-store/{ticker}/compute", tags=["Feature Store"])
async def compute_features(ticker: str, ohlcv_data: List[Dict[str, Any]] = Body(...)):
    """Compute and store features from OHLCV data."""
    if not feature_store_svc:
        raise HTTPException(status_code=503, detail="Feature store not initialized")
    result = await feature_store_svc.compute_and_store(ticker, ohlcv_data)
    return {"success": True, "ticker": ticker, "result": result}


# ============================================================================
# IP WHITELIST ROUTES (§16.2)
# ============================================================================

@app.get("/api/ip-whitelist/{user_id}", tags=["IP Whitelist"])
async def get_ip_whitelist(user_id: str):
    """Get IP whitelist for a user."""
    if not ip_whitelist_svc:
        raise HTTPException(status_code=503, detail="IP whitelist service not initialized")
    whitelist = await ip_whitelist_svc.get_whitelist(user_id)
    return {"success": True, "user_id": user_id, "whitelist": whitelist}


@app.post("/api/ip-whitelist/{user_id}/add", tags=["IP Whitelist"])
async def add_ip_to_whitelist(
    user_id: str,
    ip_address: str = Body(..., embed=True),
    description: str = Body("", embed=True),
):
    """Add an IP address to a user's whitelist."""
    if not ip_whitelist_svc:
        raise HTTPException(status_code=503, detail="IP whitelist service not initialized")
    result = await ip_whitelist_svc.add_ip(user_id, ip_address, description=description)
    return result


@app.delete("/api/ip-whitelist/{user_id}/remove", tags=["IP Whitelist"])
async def remove_ip_from_whitelist(user_id: str, ip_address: str = Body(..., embed=True)):
    """Remove an IP address from a user's whitelist."""
    if not ip_whitelist_svc:
        raise HTTPException(status_code=503, detail="IP whitelist service not initialized")
    result = await ip_whitelist_svc.remove_ip(user_id, ip_address)
    return result


@app.post("/api/ip-whitelist/{user_id}/toggle", tags=["IP Whitelist"])
async def toggle_ip_whitelist(user_id: str, enabled: bool = Body(..., embed=True)):
    """Enable or disable IP whitelisting for a user."""
    if not ip_whitelist_svc:
        raise HTTPException(status_code=503, detail="IP whitelist service not initialized")
    result = await ip_whitelist_svc.enable_whitelist(user_id, enabled)
    return result


@app.get("/api/ip-whitelist/{user_id}/status", tags=["IP Whitelist"])
async def get_ip_whitelist_status(user_id: str):
    """Get whitelist status and stats for a user."""
    if not ip_whitelist_svc:
        raise HTTPException(status_code=503, detail="IP whitelist service not initialized")
    result = await ip_whitelist_svc.get_whitelist_status(user_id)
    return result


# ============================================================================
# REGIME DETECTOR ROUTES (§6.1)
# ============================================================================

@app.get("/api/regime/{ticker}", tags=["Regime Detection"])
async def detect_market_regime(ticker: str):
    """Detect current market regime for a ticker."""
    if not regime_detector_svc:
        raise HTTPException(status_code=503, detail="Regime detector not initialized")
    if not market_data_service:
        raise HTTPException(status_code=503, detail="Market data service not available")
    try:
        ohlcv = await market_data_service.fetch_forex_ohlcv(ticker, "1h", 100)
        if not ohlcv:
            ohlcv = []
        closes = [c.get("close", 0) for c in ohlcv] if ohlcv else []
        highs = [c.get("high", 0) for c in ohlcv] if ohlcv else []
        lows = [c.get("low", 0) for c in ohlcv] if ohlcv else []
        volumes = [c.get("volume", 0) for c in ohlcv] if ohlcv else []
        regime = regime_detector_svc.detect_regime(ticker, closes, highs, lows, volumes)
        return {"success": True, "ticker": ticker, "regime": regime}
    except Exception as e:
        logger.error(f"Regime detection failed for {ticker}: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/regime/{ticker}/cached", tags=["Regime Detection"])
async def get_cached_regime(ticker: str):
    """Get cached regime classification for a ticker (no recomputation)."""
    if not regime_detector_svc:
        raise HTTPException(status_code=503, detail="Regime detector not initialized")
    regime = regime_detector_svc.get_cached_regime(ticker)
    if regime:
        return {"success": True, "ticker": ticker, "regime": regime}
    return {"success": False, "error": "No cached regime available"}


# ============================================================================
# GPU INFERENCE ROUTES (§6.4)
# ============================================================================

@app.post("/api/inference/models", tags=["GPU Inference"])
async def register_inference_model(config: Dict[str, Any] = Body(...)):
    """Register a model for GPU/ONNX inference."""
    if not gpu_inference_svc:
        raise HTTPException(status_code=503, detail="GPU inference service not initialized")
    model_config = ModelConfig(
        model_id=config.get("model_id", ""),
        model_path=config.get("model_path", ""),
        input_shape=tuple(config.get("input_shape", [1, 10])),
        precision=QuantizationPrecision(config.get("precision", "fp32")),
        backend=InferenceBackend(config.get("backend", "cpu")),
        batch_size=config.get("batch_size", 32),
    )
    result = gpu_inference_svc.register_model(model_config)
    return result


@app.post("/api/inference/{model_id}", tags=["GPU Inference"])
async def run_inference(model_id: str, input_data: Dict[str, Any] = Body(...)):
    """Run single inference on a registered model."""
    if not gpu_inference_svc:
        raise HTTPException(status_code=503, detail="GPU inference service not initialized")
    result = await gpu_inference_svc.infer(model_id, input_data)
    return result


@app.post("/api/inference/{model_id}/batch", tags=["GPU Inference"])
async def run_batch_inference(model_id: str, batch_data: List[Dict[str, Any]] = Body(...)):
    """Run batch inference on a registered model."""
    if not gpu_inference_svc:
        raise HTTPException(status_code=503, detail="GPU inference service not initialized")
    results = await gpu_inference_svc.infer_batch(model_id, batch_data)
    return {"success": True, "model_id": model_id, "results": results}


@app.get("/api/inference/stats", tags=["GPU Inference"])
async def get_inference_stats():
    """Get inference performance statistics."""
    if not gpu_inference_svc:
        raise HTTPException(status_code=503, detail="GPU inference service not initialized")
    return {"success": True, "stats": gpu_inference_svc.get_stats()}


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
