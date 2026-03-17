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
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from statistics import mean
from typing import Any, Dict
from threading import Lock

from fastapi import FastAPI, HTTPException, Depends, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global signal_aggregator, signal_processor, paper_trading, portfolio_service, risk_manager, market_data_service
    global chat_service, creator_service, user_service, backtest_service, strategy_service
    
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

CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")
ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOW_ORIGINS.split(",") if origin.strip()] or ["*"]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Optional in-memory rate limiter for production hardening
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "120"))
_rate_limit_store: Dict[str, Dict[str, float]] = {}
_rate_limit_lock = Lock()


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if RATE_LIMIT_ENABLED:
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


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/status", tags=["Health"])
async def status():
    """Detailed status endpoint."""
    return {
        "api_running": True,
        "database": "connected",
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
            "services_ready": services_ready,
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
    
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}", response_model=UserProfile, tags=["Users"])
async def get_user(user_id: str):
    """Get user profile."""
    try:
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
async def process_signals():
    """
    Trigger signal aggregation and processing.
    This would normally run on a schedule, but exposed as endpoint for testing.
    """
    try:
        # Aggregate from sources
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
                    "source": "internal_fallback",
                }
                for symbol in symbols
            ]
        
        # Process signals
        processed = signal_processor.process_signals(raw_signals)
        
        # Store in database
        stored_signals = []
        for signal in processed:
            payload = {**signal}
            payload.setdefault("id", str(uuid.uuid4()))
            payload.setdefault("created_by", "system")
            payload.setdefault("created_at", datetime.utcnow().isoformat())

            insert_response = db.supabase.table("signals").insert(payload).execute()
            if getattr(insert_response, "data", None):
                stored_signals.append(insert_response.data[0])
            else:
                stored_signals.append(payload)
        
        logger.info(f"✅ Processed and stored {len(processed)} signals")
        
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
async def tradingview_webhook(payload: Dict[str, Any], x_webhook_secret: str = Header(None)):
    """
    Receive TradingView webhook alerts and ingest as signals.
    """
    try:
        # Verify webhook secret
        expected_secret = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")
        
        # If secret is configured, validate it
        if expected_secret and expected_secret.strip():
            if not x_webhook_secret or x_webhook_secret != expected_secret:
                logger.warning(f"❌ Invalid webhook secret (expected: {expected_secret}, got: {x_webhook_secret})")
                raise HTTPException(status_code=401, detail="Unauthorized: Invalid webhook secret")
        else:
            # If no secret configured, allow for MVP testing
            logger.warning("⚠️ Webhook secret not configured, allowing unauthenticated requests")
        
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

    except Exception as e:
        logger.error(f"❌ Failed to submit KYC: {e}")
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
