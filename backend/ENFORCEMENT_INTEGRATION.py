"""
ENFORCEMENT GATE INTEGRATION GUIDE
Complete endpoint implementations with all enforcement gates wired.
Add these endpoints to main.py to replace/enhance existing ones.

§7 Architecture: Non-negotiable enforcement before ANY live trade executes.
"""

from fastapi import HTTPException, Depends, Query, Body
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# INITIALIZATION (Add to app lifespan startup)
# ============================================================================

"""
In main.py lifespan startup, add:

from services import (
    RiskManager, ExecutionServiceComplete, PaperTradingEngineComplete,
    KYCServiceComplete, ComplianceServiceComplete, BillingService,
    AuditLogServiceComplete, EnforcementGate, LiveTradingExecutionFlow,
    SignalGenerator, EnsembleSignalPredictor, FeatureEngineer
)

# Initialize services
risk_manager = RiskManager(db)
execution_service = ExecutionServiceComplete(db, redis_client)
paper_trading_engine = PaperTradingEngineComplete(db)
kyc_service = KYCServiceComplete(db, redis_client)
audit_service = AuditLogServiceComplete(db)
compliance_service = ComplianceServiceComplete(db)
billing_service = BillingService(db)
creator_marketplace = CreatorMarketplaceServiceComplete(db)

# Initialize ML
feature_engineer = FeatureEngineer()
ensemble_predictor = EnsembleSignalPredictor()
ml_signal_gen = SignalGenerator(db, ensemble_predictor)

# Initialize master enforcement gate
enforcement_gate = EnforcementGate(
    db, risk_manager, kyc_service, compliance_service,
    billing_service, paper_trading_engine
)

live_execution_flow = LiveTradingExecutionFlow(
    db, enforcement_gate, execution_service
)
"""


# ============================================================================
# 1. KYC INITIATION ENDPOINT
# ============================================================================

async def initiate_kyc(
    user_id: str = Query(...),
    email: str = Query(...),
    full_name: str = Query(...),
    date_of_birth: str = Query(...),  # YYYY-MM-DD
    country: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Initiate KYC verification via Onfido.
    Returns SDK token for frontend integration.
    """

    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Cannot initiate KYC for other users")

    try:
        result = await kyc_service.initiate_kyc(
            user_id=user_id,
            email=email,
            full_name=full_name,
            date_of_birth=date_of_birth,
            country=country
        )

        if result.get('success'):
            logger.info(f"✅ KYC initiated for {user_id}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))

    except Exception as e:
        logger.error(f"KYC initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2. KYC STATUS CHECK
# ============================================================================

async def get_kyc_status(
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Get KYC verification status."""

    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Cannot check KYC for other users")

    try:
        status = await kyc_service.get_kyc_status(user_id)
        return status
    except Exception as e:
        logger.error(f"KYC status fetch failed: {e}")
        return {'status': 'ERROR', 'approved': False, 'error': str(e)}


# ============================================================================
# 3. SUBSCRIPTION MANAGEMENT
# ============================================================================

async def create_subscription(
    user_id: str = Query(...),
    email: str = Query(...),
    plan: str = Query(default='basic'),
    firebase_uid: str = Depends(verify_firebase_token),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Create Stripe subscription for user."""

    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Cannot create subscription for other users")

    try:
        result = await billing_service.create_subscription(
            user_id=user_id,
            email=email,
            plan=plan,
            trial_days=7
        )

        if result.get('success'):
            logger.info(f"✅ Subscription created for {user_id}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))

    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_subscription_status(
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Get subscription status."""

    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Cannot check subscription for other users")

    try:
        status = await billing_service.get_subscription_status(user_id)
        return status
    except Exception as e:
        logger.error(f"Subscription fetch failed: {e}")
        return {'subscribed': False, 'error': str(e)}


# ============================================================================
# 4. DISCLAIMER ACKNOWLEDGMENT
# ============================================================================

async def acknowledge_disclaimer(
    user_id: str = Query(...),
    disclaimer_key: str = Query(...),
    ip_address: Optional[str] = Header(None),
    firebase_uid: str = Depends(verify_firebase_token),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """Track disclaimer acknowledgment."""

    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Cannot acknowledge disclaimers for other users")

    try:
        result = await compliance_service.track_disclaimer_acknowledgment(
            user_id=user_id,
            disclaimer_key=disclaimer_key,
            ip_address=ip_address,
            method='modal_popup'
        )

        if result.get('success'):
            return {'acknowledged': True}
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))

    except Exception as e:
        logger.error(f"Disclaimer acknowledgment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. PAPER TRADING WITH VALIDATION GATE
# ============================================================================

async def submit_to_paper_trading(
    signal_id: str = Query(...),
    signal: Dict[str, Any] = Body(...),
    backtest_sharpe: float = Query(...),
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Submit signal to paper trading.
    Internal signals automatically submitted; creator signals require proof.
    """

    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Cannot submit signals for other users")

    try:
        result = await paper_trading_engine.submit_signal_to_paper_trading(
            signal_id=signal_id,
            signal=signal,
            backtest_sharpe=backtest_sharpe
        )

        if result.get('success'):
            logger.info(f"✅ Signal submitted to paper trading: {signal_id}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))

    except Exception as e:
        logger.error(f"Paper trading submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def validate_paper_trading_gate(
    signal_id: str = Query(...),
    backtest_sharpe: float = Query(...),
    paper_trading_start: Optional[str] = Query(None),  # ISO datetime
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate if signal passes 4-week paper trading gate.
    Returns: {approved: bool, reason: str, gate_status: str}
    """

    try:
        from datetime import datetime
        paper_start = datetime.fromisoformat(paper_trading_start) if paper_trading_start else None

        gate_result = await paper_trading_engine.validate_signal_gate(
            signal_id=signal_id,
            backtest_sharpe=backtest_sharpe,
            paper_trading_started_at=paper_start
        )

        return gate_result

    except Exception as e:
        logger.error(f"Gate validation failed: {e}")
        return {
            'approved': False,
            'reason': str(e),
            'gate_status': 'ERROR'
        }


# ============================================================================
# 6. LIVE TRADE EXECUTION WITH FULL ENFORCEMENT
# ============================================================================

async def execute_live_trade(
    signal: Dict[str, Any] = Body(...),
    exchange: str = Query(default='binance'),
    user_id: str = Query(...),
    ip_address: Optional[str] = Header(None),
    firebase_uid: str = Depends(verify_firebase_token),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Execute live trade with ALL enforcement gates.

    Enforcement checks (§7 Architecture):
    1. KYC approved
    2. Subscription active
    3. Disclaimers acknowledged
    4. Risk validation passed
    5. Paper trading validated
    6. Age gate passed
    """

    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Cannot execute trades for other users")

    try:
        # Get account balance
        portfolio_response = db.supabase.table('portfolios').select('*').eq(
            'user_id', user_id
        ).execute()
        account_balance = portfolio_response.data[0]['current_balance'] if portfolio_response.data else 100000

        # Execute with FULL enforcement
        result = await live_execution_flow.execute_live_trade(
            user_id=user_id,
            signal=signal,
            exchange=exchange,
            account_balance=account_balance,
            ip_address=ip_address
        )

        if result.get('success'):
            logger.info(f"✅ LIVE TRADE EXECUTED: {user_id} - {signal.get('ticker')}")
            return result
        else:
            logger.warning(f"⛔ Trade BLOCKED: {result.get('error')}")
            raise HTTPException(
                status_code=403,
                detail=result.get('error')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 7. ML SIGNAL GENERATION
# ============================================================================

async def generate_ai_signal(
    ticker: str = Query(...),
    ohlcv_data: Dict[str, list] = Body(...),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate AI signal using ensemble ML models.
    Features: RSI, MACD, EMA, ATR, volatility.
    Confidence: model agreement + volatility.
    """

    try:
        signal = await ml_signal_gen.generate_signal(
            ticker=ticker,
            ohlcv_data=ohlcv_data
        )

        if signal.get('error'):
            raise HTTPException(status_code=400, detail=signal.get('error'))

        logger.info(f"✅ Signal generated: {ticker} {signal.get('signal_type')}")
        return signal

    except Exception as e:
        logger.error(f"Signal generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 8. AUDIT TRAIL ACCESS
# ============================================================================

async def get_audit_trail(
    user_id: str = Query(...),
    limit: int = Query(default=100),
    firebase_uid: str = Depends(verify_firebase_token),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get immutable audit trail for user.
    Hash-chained events, cryptographically verifiable.
    """

    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Cannot access audit trail for other users")

    try:
        trail = await audit_service.get_user_audit_trail(user_id, limit)
        return {
            'success': True,
            'total_events': len(trail),
            'events': trail
        }

    except Exception as e:
        logger.error(f"Audit trail fetch failed: {e}")
        return {'success': False, 'error': str(e)}


async def export_audit_trail(
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export complete audit trail for regulatory/tax purposes.
    """

    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Cannot export audit trail for other users")

    try:
        export_result = await audit_service.export_audit_trail(user_id)
        return export_result

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINT REGISTRATION SNIPPET
# Add these to main.py:
# ============================================================================

"""
# KYC Endpoints
@app.post("/api/kyc/initiate", tags=["Compliance"])
async def kyc_initiate(...): ...

@app.get("/api/kyc/status", tags=["Compliance"])
async def kyc_status_check(...): ...

# Subscription Endpoints
@app.post("/api/billing/subscribe", tags=["Billing"])
async def subscription_create(...): ...

@app.get("/api/billing/subscription", tags=["Billing"])
async def subscription_check(...): ...

# Compliance Endpoints
@app.post("/api/compliance/acknowledge-disclaimer", tags=["Compliance"])
async def disclaimer_ack(...): ...

# Paper Trading Endpoints
@app.post("/api/paper-trading/submit", tags=["Paper Trading"])
async def paper_trading_submit(...): ...

@app.post("/api/paper-trading/validate-gate", tags=["Paper Trading"])
async def paper_trading_validate(...): ...

# Live Trading Endpoints (ENFORCED)
@app.post("/api/trades/live/execute", tags=["Trading"])
async def live_trade_execute(...): ...

# Signal Generation Endpoints
@app.post("/api/signals/generate-ml", tags=["Signals"])
async def signal_generate(...): ...

# Audit Endpoints
@app.get("/api/audit/trail", tags=["Compliance"])
async def audit_get(...): ...

@app.get("/api/audit/export", tags=["Compliance"])
async def audit_export(...): ...
"""
