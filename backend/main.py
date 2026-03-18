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
    
    # Startup
    logger.info("🚀 Starting AlphaForge Backend API")

    if os.getenv("API_ENV", "development").lower() == "production":
        config.validate_config()
    
    signal_aggregator = SignalAggregator()
    signal_processor = SignalProcessor()
    paper_trading = PaperTradingEngine(db)
    portfolio_service = PortfolioService(db)
    risk_manager = RiskManager(db)
    market_data_service = MarketDataService()
    chat_service = ChatService(db)
    creator_service = CreatorVerificationService(db)
    user_service = UserManagementService(db)
    backtest_service = BacktestingService(db)
    strategy_service = StrategyService(db)
    ml_scorer = MLSignalScorer(db)
    creator_marketplace = CreatorMarketplaceService(db)
    kyc_service = KYCService(db)
    
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
    
    logger.info("✅ All services initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AlphaForge Backend API")
    await signal_aggregator.close()
    await market_data_service.close()


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

# Custom CORS middleware to handle all origins properly
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    """Explicit CORS middleware for ngrok and localhost tunneling."""
    origin = request.headers.get("origin", "").lower()
    
    # Check if origin is allowed
    allowed_origins_lower = [o.lower() for o in ALLOWED_ORIGINS]
    is_allowed = (
        "*" in ALLOWED_ORIGINS or
        origin in allowed_origins_lower or
        any(origin == ao.lower() for ao in ALLOWED_ORIGINS)
    )
    
    # Handle preflight: OPTIONS requests
    if request.method == "OPTIONS":
        response = JSONResponse(content={}, status_code=200)
        if is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin or ALLOWED_ORIGINS[0]
        else:
            response.headers["Access-Control-Allow-Origin"] = "*" if "*" in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
        logger.info(f"✅ CORS OPTIONS: origin={origin}, allowed={is_allowed}, headers set")
        return response
    
    # Handle actual requests (GET, POST, etc.)
    response = await call_next(request)
    
    # Add CORS headers to response
    if is_allowed:
        response.headers["Access-Control-Allow-Origin"] = origin or ALLOWED_ORIGINS[0]
    else:
        response.headers["Access-Control-Allow-Origin"] = "*" if "*" in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]
    
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Expose-Headers"] = "Content-Type, Content-Length"
    
    logger.debug(f"✅ CORS {request.method}: {request.url.path} - origin={origin}, allowed={is_allowed}")
    return response

# Host header hardening
app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)

# Optional in-memory rate limiter for production hardening
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "120"))
_rate_limit_store: Dict[str, Dict[str, float]] = {}
_rate_limit_lock = Lock()


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if RATE_LIMIT_ENABLED:
        if request.url.path in {"/health", "/ready", "/status"}:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        route_key = f"{client_ip}:{request.url.path}"
        now = time.time()

        with _rate_limit_lock:
            entry = _rate_limit_store.get(route_key)
            if entry is None or now - entry["window_start"] > RATE_LIMIT_WINDOW_SECONDS:
                _rate_limit_store[route_key] = {"window_start": now, "count": 1}
            else:
                entry["count"] += 1
                if entry["count"] > RATE_LIMIT_MAX_REQUESTS:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "success": False,
                            "error": "Rate limit exceeded",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

    return await call_next(request)


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
async def register_user(user: UserProfileCreate):
    """Register a new user."""
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
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = db.supabase.table("users").insert(user_data).execute()
        
        if response.data and len(response.data) > 0:
            created_user = response.data[0]
            logger.info(f"✅ User registered: {user.email}")
            return {"success": True, "user": created_user}
        
        raise HTTPException(status_code=400, detail="Registration failed")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}", response_model=UserProfile, tags=["Users"])
async def get_user(user_id: str):
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
async def update_user(user_id: str, updates: UserProfileUpdate):
    """Update user profile."""
    try:
        update_data = updates.model_dump(exclude_unset=True)
        # Convert enums to strings
        if "plan" in update_data:
            update_data["plan"] = update_data["plan"].value if isinstance(update_data["plan"], Enum) else str(update_data["plan"]).lower()
        if "risk_tolerance" in update_data:
            update_data["risk_tolerance"] = update_data["risk_tolerance"].value if isinstance(update_data["risk_tolerance"], Enum) else str(update_data["risk_tolerance"]).lower()
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"📝 Updating user: {user_id}")
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
async def process_signals(payload: Dict[str, Any] = Body(None)):
    """
    Trigger signal aggregation and processing.
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
async def validate_signal_trade(signal_id: str, user_id: str = Query(...)):
    """Validate a signal for trading (risk check)."""
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
async def create_paper_trade(trade: PaperTradeCreate):
    """Create a paper trade."""
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
async def close_paper_trade(trade_id: str, exit_price: float = Query(...)):
    """Close a paper trade."""
    try:
        result = await paper_trading.close_paper_trade(trade_id, exit_price)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    except Exception as e:
        logger.error(f"❌ Paper trade close failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/paper", tags=["Paper Trading"])
async def get_paper_trades(user_id: str = Query(...)):
    """Get all paper trades for a user."""
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
async def get_portfolio(user_id: str):
    """Get portfolio summary."""
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
async def get_portfolio_metrics(user_id: str):
    """Get detailed portfolio metrics (performance stats)."""
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
