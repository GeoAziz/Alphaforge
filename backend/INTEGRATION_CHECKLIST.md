# AlphaForge Integration Checklist

Quick reference for wiring all enforcement gates and complete services into main.py.

---

## STEP 1: Import Complete Services

**Add to main.py imports section:**

```python
from services import (
    RiskManager,
    ExecutionServiceComplete,
    PaperTradingEngineComplete,
    KYCServiceComplete,
    ComplianceServiceComplete,
    BillingService,
    AuditLogServiceComplete,
    CreatorMarketplaceServiceComplete,
    FeatureEngineer,
    EnsembleSignalPredictor,
    SignalGenerator,
    EnforcementGate,
    LiveTradingExecutionFlow,
)
from services.execution_service import ExchangeAbstractionLayer
```

---

## STEP 2: Initialize in App Startup

**Add to `@app.lifespan` startup event:**

```python
# Risk & Execution
risk_manager = RiskManager(db)
execution_service = ExecutionServiceComplete(db, redis_client)
paper_trading_engine = PaperTradingEngineComplete(db)

# Compliance & KYC
kyc_service = KYCServiceComplete(db, redis_client)
compliance_service = ComplianceServiceComplete(db)
billing_service = BillingService(db)
audit_service = AuditLogServiceComplete(db)

# Marketplace
creator_marketplace = CreatorMarketplaceServiceComplete(db)

# ML Signal Generation
feature_engineer = FeatureEngineer()
ensemble_predictor = EnsembleSignalPredictor()
ml_signal_gen = SignalGenerator(db, ensemble_predictor)

# Master Enforcement Gate
enforcement_gate = EnforcementGate(
    db, risk_manager, kyc_service, compliance_service,
    billing_service, paper_trading_engine
)
live_execution_flow = LiveTradingExecutionFlow(
    db, enforcement_gate, execution_service
)

logger.info("✅ All enforcement gates initialized")
```

---

## STEP 3: Add/Replace Endpoints

### KYC Endpoints

```python
@app.post("/api/kyc/initiate", tags=["Compliance"])
async def kyc_initiate(
    user_id: str = Query(...),
    email: str = Query(...),
    full_name: str = Query(...),
    date_of_birth: str = Query(...),
    country: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
) -> Dict[str, Any]:
    """Initiate KYC via Onfido."""
    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    result = await kyc_service.initiate_kyc(
        user_id, email, full_name, date_of_birth, country
    )
    if result.get('success'):
        return result
    raise HTTPException(status_code=400, detail=result.get('error'))


@app.get("/api/kyc/status", tags=["Compliance"])
async def kyc_status(
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
) -> Dict[str, Any]:
    """Get KYC status."""
    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return await kyc_service.get_kyc_status(user_id)
```

### Subscription Endpoints

```python
@app.post("/api/billing/subscribe", tags=["Billing"])
async def create_sub(
    user_id: str = Query(...),
    email: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
) -> Dict[str, Any]:
    """Create Stripe subscription."""
    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    result = await billing_service.create_subscription(user_id, email)
    if result.get('success'):
        return result
    raise HTTPException(status_code=400, detail=result.get('error'))


@app.get("/api/billing/subscription", tags=["Billing"])
async def sub_status(
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
) -> Dict[str, Any]:
    """Get subscription status."""
    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return await billing_service.get_subscription_status(user_id)
```

### Disclaimer Endpoint

```python
@app.post("/api/compliance/acknowledge-disclaimer", tags=["Compliance"])
async def ack_disclaimer(
    user_id: str = Query(...),
    disclaimer_key: str = Query(...),
    ip_address: Optional[str] = Header(None),
    firebase_uid: str = Depends(verify_firebase_token),
) -> Dict[str, Any]:
    """Track disclaimer acknowledgment."""
    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    result = await compliance_service.track_disclaimer_acknowledgment(
        user_id, disclaimer_key, ip_address, method='modal_popup'
    )
    if result.get('success'):
        return {'acknowledged': True}
    raise HTTPException(status_code=400, detail=result.get('error'))
```

### Paper Trading Endpoints

```python
@app.post("/api/paper-trading/submit", tags=["Paper Trading"])
async def submit_paper_trade(
    signal_id: str = Query(...),
    signal: Dict[str, Any] = Body(...),
    backtest_sharpe: float = Query(...),
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
) -> Dict[str, Any]:
    """Submit signal to paper trading."""
    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    result = await paper_trading_engine.submit_signal_to_paper_trading(
        signal_id, signal, backtest_sharpe
    )
    if result.get('success'):
        return result
    raise HTTPException(status_code=400, detail=result.get('error'))


@app.post("/api/paper-trading/validate-gate", tags=["Paper Trading"])
async def validate_gate(
    signal_id: str = Query(...),
    backtest_sharpe: float = Query(...),
    paper_trading_start: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Validate 4-week paper trading gate."""
    from datetime import datetime
    
    paper_start = None
    if paper_trading_start:
        paper_start = datetime.fromisoformat(paper_trading_start)
    
    return await paper_trading_engine.validate_signal_gate(
        signal_id, backtest_sharpe, paper_start
    )
```

### CRITICAL: Live Trade Execution Endpoint (WITH ENFORCEMENT)

```python
@app.post("/api/trades/live", tags=["Trading"])
async def execute_live_trade_enforced(
    signal: Dict[str, Any] = Body(...),
    exchange: str = Query(default='binance'),
    user_id: str = Query(...),
    ip_address: Optional[str] = Header(None),
    firebase_uid: str = Depends(verify_firebase_token),
) -> Dict[str, Any]:
    """
    Execute live trade with FULL enforcement gates.
    
    Checks before execution:
    1. KYC approved
    2. Subscription active
    3. Disclaimers acknowledged
    4. Risk validation passed
    5. Paper trading validated
    6. Age gate passed
    """
    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        # Get account balance
        portfolio_response = db.supabase.table('portfolios').select('*').eq(
            'user_id', user_id
        ).execute()
        account_balance = (
            portfolio_response.data[0]['current_balance'] 
            if portfolio_response.data else 100000
        )
        
        # Execute with ENFORCEMENT
        result = await live_execution_flow.execute_live_trade(
            user_id=user_id,
            signal=signal,
            exchange=exchange,
            account_balance=account_balance,
            ip_address=ip_address
        )
        
        if result.get('success'):
            logger.info(f"✅ LIVE TRADE: {user_id} - {signal.get('ticker')}")
            return result
        else:
            logger.warning(f"⛔ BLOCKED: {result.get('error')}")
            raise HTTPException(status_code=403, detail=result.get('error'))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### ML Signal Generation

```python
@app.post("/api/signals/generate-ml", tags=["Signals"])
async def generate_signal_ml(
    ticker: str = Query(...),
    ohlcv_data: Dict[str, list] = Body(...),
) -> Dict[str, Any]:
    """Generate AI signal using ensemble ML."""
    try:
        signal = await ml_signal_gen.generate_signal(ticker, ohlcv_data)
        
        if signal.get('error'):
            raise HTTPException(status_code=400, detail=signal.get('error'))
        
        return signal
    
    except Exception as e:
        logger.error(f"Signal generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Audit Trail Endpoints

```python
@app.get("/api/audit/trail", tags=["Compliance"])
async def get_audit(
    user_id: str = Query(...),
    limit: int = Query(default=100),
    firebase_uid: str = Depends(verify_firebase_token),
) -> Dict[str, Any]:
    """Get immutable audit trail."""
    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    trail = await audit_service.get_user_audit_trail(user_id, limit)
    return {
        'success': True,
        'total_events': len(trail),
        'events': trail
    }


@app.get("/api/audit/export", tags=["Compliance"])
async def export_audit(
    user_id: str = Query(...),
    firebase_uid: str = Depends(verify_firebase_token),
) -> Dict[str, Any]:
    """Export audit trail for compliance."""
    if firebase_uid != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return await audit_service.export_audit_trail(user_id)
```

---

## STEP 4: Verify Integration

### Check 1: All Services Initialized
```bash
grep -n "enforcement_gate = EnforcementGate" backend/main.py
# Should output line number
```

### Check 2: Live Trade Endpoint Has Enforcement
```bash
grep -A 5 "execute_live_trade_enforced" backend/main.py
# Should show live_execution_flow.execute_live_trade
```

### Check 3: All Database Tables Migrated
```bash
python backend/database/migration_manager.py run_migrations
# Should show all 7 new tables created
```

---

## STEP 5: Test Enforcement

### Manual Test: Verify KYC Gate Blocks Trade

```bash
# 1. Try live trade without KYC
curl -X POST http://localhost:8000/api/trades/live \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ticker":"BTC","entry_price":45000}'

# Expected: 403 Forbidden - "Live trading requires KYC approval"

# 2. Initiate KYC
curl -X POST http://localhost:8000/api/kyc/initiate \
  -H "Authorization: Bearer $TOKEN" \
  -d "user_id=..&email=..&full_name=..&dob=..&country=.."

# 3. Simulate webhook callback (in test)
# (Onfido would call your webhook on verification)

# 4. Try live trade again
# Expected: 200 OK - trade executed (if other gates pass)
```

---

## STEP 6: Deploy & Monitor

### Pre-Deploy Checks

```bash
# Verify all imports work
python -c "from services import EnforcementGate; print('✅ Imports OK')"

# Run integration tests
pytest backend/tests/test_enforcement_gates.py -v

# Check enforcement gate logic
pytest backend/tests/test_live_execution_flow.py -v
```

### Post-Deploy Monitoring

```bash
# Monitor KYC blocks
grep "KYC:" backend/logs/app.log | tail -20

# Monitor risk rejects
grep "Risk:" backend/logs/app.log | tail -20

# Monitor live trades executed
grep "LIVE TRADE EXECUTED" backend/logs/app.log | tail -20

# Verify audit logs are hash-chained
curl -X GET http://localhost:8000/api/audit/trail?user_id=$USER_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✅ Integration Complete Checklist

- [ ] All services imported
- [ ] Services initialized in startup
- [ ] KYC endpoints added
- [ ] Subscription endpoints added
- [ ] Disclaimer endpoint added
- [ ] Paper trading endpoints added
- [ ] **Live trade endpoint ENFORCED**
- [ ] ML signal generation endpoint added
- [ ] Audit trail endpoints added
- [ ] Database migrations run
- [ ] Import test passes
- [ ] Integration tests pass
- [ ] Enforcement gates verified working
- [ ] Monitoring in place

---

## Endpoints Summary

| Endpoint | Method | Enforcement | Status |
|----------|--------|---|--------|
| /api/kyc/initiate | POST | - | ✅ New |
| /api/kyc/status | GET | - | ✅ New |
| /api/billing/subscribe | POST | - | ✅ New |
| /api/billing/subscription | GET | - | ✅ New |
| /api/compliance/acknowledge-disclaimer | POST | - | ✅ New |
| /api/paper-trading/submit | POST | - | ✅ New |
| /api/paper-trading/validate-gate | POST | - | ✅ New |
| **`/api/trades/live`** | **POST** | **✅ FULL** | **✅ CRITICAL** |
| /api/signals/generate-ml | POST | - | ✅ New |
| /api/audit/trail | GET | - | ✅ New |
| /api/audit/export | GET | - | ✅ New |

---

**All enforcement gates are ready. Follow this checklist to integrate into main.py and verify enforcement works.**
