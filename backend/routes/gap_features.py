"""
API routes for remaining gap features:
- Live Trading
- Advanced Signals
- Community & Social
- Compliance
- Mobile App
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, Dict, Any, List
import logging

from config import FeatureFlags
from services import (
    LiveTradingEngine,
    LLMSignalGenerator,
    AdvancedSignalsService,
    ComplianceService,
    MobileAppService,
)
from firebase_config import verify_firebase_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["gap-features"])

# Service instances (initialized in main.py)
live_trading_engine: Optional[LiveTradingEngine] = None
llm_signal_gen: Optional[LLMSignalGenerator] = None
advanced_signals_svc: Optional[AdvancedSignalsService] = None
compliance_svc: Optional[ComplianceService] = None
mobile_app_svc: Optional[MobileAppService] = None


# ============================================================================
# LIVE TRADING ENDPOINTS
# ============================================================================

@router.post("/trading/execute")
async def execute_trading_signal(
    signal: Dict[str, Any],
    exchange: str = "binance",
    user_id: str = Depends(verify_firebase_token),
):
    """Execute a trading signal on live exchange."""
    if not FeatureFlags.LIVE_TRADING:
        raise HTTPException(status_code=503, detail="Live trading not enabled")

    if not live_trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")

    try:
        result = await live_trading_engine.execute_signal(user_id, signal, exchange)
        return result
    except Exception as e:
        logger.error(f"❌ Trading execution failed: {e}")
        raise HTTPException(status_code=500, detail="Execution failed")


@router.get("/trading/balance")
async def get_exchange_balance(
    exchange: str = "binance",
    asset: str = "USDT",
    user_id: str = Depends(verify_firebase_token),
):
    """Get account balance from exchange."""
    if not live_trading_engine:
        raise HTTPException(status_code=503, detail="Trading engine not initialized")

    try:
        balance = await live_trading_engine.get_balance(exchange, asset)
        return balance
    except Exception as e:
        logger.error(f"❌ Balance fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Balance fetch failed")


# ============================================================================
# ADVANCED SIGNALS ENDPOINTS
# ============================================================================

@router.post("/signals/ai-generated")
async def generate_ai_signal(
    ticker: str,
    market_data: Dict[str, Any],
    technical_indicators: Dict[str, Any],
    sentiment_data: Optional[Dict[str, Any]] = None,
    user_id: str = Depends(verify_firebase_token),
):
    """Generate AI-powered trading signal using LLM."""
    if not FeatureFlags.AI_SIGNALS:
        raise HTTPException(status_code=503, detail="AI signals not enabled")

    if not llm_signal_gen:
        raise HTTPException(status_code=503, detail="LLM not initialized")

    try:
        signal = await llm_signal_gen.generate_signal(
            ticker, market_data, technical_indicators, sentiment_data
        )
        return {"success": bool(signal), "signal": signal}
    except Exception as e:
        logger.error(f"❌ AI signal generation failed: {e}")
        raise HTTPException(status_code=500, detail="Signal generation failed")


@router.post("/signals/multi-timeframe")
async def get_multi_timeframe_signal(
    ticker: str,
    indicators_1h: Dict[str, Any],
    indicators_4h: Dict[str, Any],
    indicators_1d: Dict[str, Any],
    user_id: str = Depends(verify_firebase_token),
):
    """Generate multi-timeframe confirmation signal."""
    if not advanced_signals_svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        signal = await advanced_signals_svc.generate_multi_timeframe_signal(
            ticker, indicators_1h, indicators_4h, indicators_1d
        )
        return {"success": bool(signal), "signal": signal}
    except Exception as e:
        logger.error(f"❌ Multi-timeframe signal failed: {e}")
        raise HTTPException(status_code=500, detail="Signal generation failed")


@router.post("/signals/sentiment")
async def get_sentiment_signal(
    ticker: str, sentiment_data: Dict[str, Any], user_id: str = Depends(verify_firebase_token)
):
    """Generate sentiment-based trading signal."""
    if not advanced_signals_svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        signal = await advanced_signals_svc.generate_sentiment_signal(ticker, sentiment_data)
        return {"success": bool(signal), "signal": signal}
    except Exception as e:
        logger.error(f"❌ Sentiment signal failed: {e}")
        raise HTTPException(status_code=500, detail="Signal generation failed")


# NOTE: community profile/follow/leaderboard endpoints already live in
# main.py under the same /api/community/* paths, so they are not duplicated
# here to avoid shadowed, unreachable routes.

# ============================================================================
# COMPLIANCE ENDPOINTS
# ============================================================================

@router.post("/compliance/kyc/submit")
async def submit_kyc(
    full_name: str,
    date_of_birth: str,
    address: str,
    country: str,
    id_document_url: str,
    proof_of_address_url: str,
    user_id: str = Depends(verify_firebase_token),
):
    """Submit KYC documents."""
    if not compliance_svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = await compliance_svc.submit_kyc(
            user_id, full_name, date_of_birth, address, country, id_document_url, proof_of_address_url
        )
        return result
    except Exception as e:
        logger.error(f"❌ KYC submission failed: {e}")
        raise HTTPException(status_code=500, detail="Submission failed")


@router.get("/compliance/kyc/status")
async def get_kyc_status(user_id: str = Depends(verify_firebase_token)):
    """Get KYC verification status."""
    if not compliance_svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        status = await compliance_svc.get_kyc_status(user_id)
        return status
    except Exception as e:
        logger.error(f"❌ KYC status fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Fetch failed")


@router.post("/compliance/disclaimer/accept")
async def accept_disclaimer(version: Optional[str] = None, user_id: str = Depends(verify_firebase_token)):
    """Accept platform disclaimer."""
    if not compliance_svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = await compliance_svc.accept_disclaimer(user_id, version)
        return result
    except Exception as e:
        logger.error(f"❌ Disclaimer acceptance failed: {e}")
        raise HTTPException(status_code=500, detail="Acceptance failed")


@router.get("/compliance/audit-trail")
async def get_audit_trail(limit: int = 100, user_id: str = Depends(verify_firebase_token)):
    """Get user audit trail."""
    if not compliance_svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = await compliance_svc.get_audit_trail(user_id, limit)
        return result
    except Exception as e:
        logger.error(f"❌ Audit trail fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Fetch failed")


# ============================================================================
# MOBILE APP ENDPOINTS
# ============================================================================

@router.get("/mobile/config")
async def get_mobile_config():
    """Get mobile app configuration."""
    if not mobile_app_svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        config = mobile_app_svc.get_app_config()
        return config
    except Exception as e:
        logger.error(f"❌ Config fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Fetch failed")


@router.post("/mobile/device-register")
async def register_device(
    device_token: str,
    platform: str,
    device_model: str,
    user_id: str = Depends(verify_firebase_token),
):
    """Register mobile device for push notifications."""
    if not mobile_app_svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = await mobile_app_svc.register_device_token(user_id, device_token, platform, device_model)
        return result
    except Exception as e:
        logger.error(f"❌ Device registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.get("/mobile/update-check")
async def check_app_update(current_version: str, platform: str):
    """Check if app update is available."""
    if not mobile_app_svc:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        update_info = mobile_app_svc.check_app_update(current_version, platform)
        return update_info
    except Exception as e:
        logger.error(f"❌ Update check failed: {e}")
        raise HTTPException(status_code=500, detail="Check failed")


def initialize_services(db, services_dict: Dict[str, Any]):
    """Initialize gap feature services."""
    global live_trading_engine, llm_signal_gen, advanced_signals_svc, compliance_svc, mobile_app_svc

    if FeatureFlags.LIVE_TRADING:
        live_trading_engine = services_dict.get("live_trading_engine")

    if FeatureFlags.AI_SIGNALS:
        llm_signal_gen = services_dict.get("llm_signal_generator")

    advanced_signals_svc = AdvancedSignalsService(db)
    compliance_svc = services_dict.get("compliance_service") or ComplianceService(db)
    mobile_app_svc = MobileAppService()

    logger.info("✅ Gap feature services initialized")
