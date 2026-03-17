# Backend API Quick Reference - For Frontend Integration

**Last Updated**: March 17, 2026  
**Total Endpoints**: 62+ (All frontend requirements covered)

---

## 🚀 QUICK START

### **Base URL**
```
Development: http://localhost:8000
Production: https://api.alphaforge.com (configure in env)
```

### **Test Health**
```bash
curl http://localhost:8000/health
```

---

## 📋 ENDPOINT CATEGORIES

### **1. PORTFOLIO** (Real User Portfolio)
```
GET  /api/portfolio/{user_id}           # Summary (equity, PnL, positions)
GET  /api/portfolio/{user_id}/metrics   # Performance stats
GET  /api/positions/{user_id}           # Open positions list
```

**Example**: Get portfolio summary
```python
response = await fetch(`/api/portfolio/user-123`)
# Returns: {equity, pnl, open_positions, sharpe_ratio, max_drawdown}
```

---

### **2. SIGNALS** (Trading Signals)
```
GET  /api/signals                       # Get top 50 signals
GET  /api/signals?limit=20              # Paginate signals
POST /api/signals/process               # Trigger signal generation
POST /api/signals/{id}/validate         # Validate signal for trade
POST /api/signals/{id}/execute          # Execute signal → trade
GET  /api/signals/{id}/proofs           # Get signal proof data
```

**Execute a Signal**:
```
POST /api/signals/abc123/execute?user_id=user-123
# Returns: {success, trade_id}
```

---

### **3. MARKET DATA** (Real-Time Market Info)
```
GET  /api/market/tickers                      # BTC, ETH, SOL prices
GET  /api/market/sentiment                    # Market sentiment status
GET  /api/market/funding-rates                # Perpetual funding rates
GET  /api/market/open-interest                # Open interest data
GET  /api/market/data-quality                 # Data feed health
POST /api/market/insights?query=your_question # AI market analysis
```

**Example**: Get market sentiment
```
GET /api/market/sentiment
# Returns: {market_status: "BULLISH"|"NEUTRAL"|"BEARISH", composite_score}
```

---

### **4. BACKTESTING** (Strategy Simulation)
```
POST /api/backtest/run                              # Run backtest
GET  /api/backtest/{backtest_id}                    # Get results
GET  /api/backtest/{backtest_id}/equity-curve       # Equity curve data
GET  /api/backtest/user/{user_id}                   # List all backtests
```

**Start a Backtest**:
```
POST /api/backtest/run?user_id=user-123&name=MyStrategy
# Returns: {backtest_id, status, results}
```

---

### **5. STRATEGIES** (Marketplace & Personal)
```
GET  /api/strategies                           # User's strategies
GET  /api/strategies/marketplace               # Marketplace strategies
GET  /api/strategies/{id}/performance          # Strategy metrics
POST /api/strategy/subscribe?user_id=X&strategy_id=Y
GET  /api/strategy/subscriptions?user_id=X    # User's subscriptions
POST /api/strategy/{id}/paper-trade?user_id=X # Paper trade strategy
```

**Subscribe to Strategy**:
```
POST /api/strategy/subscribe?user_id=user-123&strategy_id=strategy-456
# Returns: {success, subscription_id}
```

---

### **6. CREATOR VERIFICATION** (5-Stage Pipeline)
```
GET  /api/creator/verification?user_id=X        # Get verification status
POST /api/creator/strategy-submit?user_id=X     # Submit strategy for review
GET  /api/creator/reputation/{creator_id}       # Get creator tier & score
```

**Stages**:
1. Account Setup
2. Paper Trading (20+ trades required)
3. Performance Check (55% win rate)
4. KYC Verification
5. Approved Creator

---

### **7. KYC/USER** (Identity Verification)
```
GET  /api/user/kyc?user_id=X       # Get KYC status
POST /api/user/kyc?user_id=X       # Submit KYC documents
```

**Response**:
```json
{
  "kyc_status": "NOT_STARTED|SUBMITTED|APPROVED|REJECTED",
  "verification_stage": "stage_1_intro|stage_2_paper_trading|...",
  "kyc_details": {...}
}
```

---

### **8. CHAT** (AI Assistant)
```
POST /api/chat/message?user_id=X&message=your_question  # Send message
GET  /api/chat/history?user_id=X&limit=50               # Get history
```

**Chat Topics**:
- Portfolio performance analysis
- Signal recommendations
- Risk assessment
- Market trends
- Strategy suggestions

---

### **9. AUDIT LOG** (Immutable Record)
```
GET  /api/audit/trail/{user_id}     # Get audit trail (100-500 entries)
POST /api/audit/log?user_id=X       # Create audit entry
```

**Automatic Logging**:
- User login/logout
- KYC submissions
- Strategy changes
- Risk setting updates
- Exchange connections
- Large trades

---

### **10. SETTINGS** (User Preferences)
```
GET  /api/settings/risk?user_id=X          # Get risk settings
PUT  /api/settings/risk?user_id=X          # Update risk settings
```

**Settings**:
```json
{
  "max_position_size_pct": 2.0,
  "max_portfolio_exposure_pct": 20.0,
  "max_leverage": 5.0,
  "stop_loss_default": 2.0,
  "take_profit_default": 5.0,
  "daily_loss_limit_pct": 10.0
}
```

---

### **11. EXCHANGE** (API Connection)
```
POST /api/exchange/connect?user_id=X&exchange=binance           # Connect
GET  /api/exchange/keys?user_id=X                               # List connected
POST /api/exchange/disconnect?user_id=X&exchange=binance        # Disconnect
```

**Supported Exchanges**:
- binance
- coinbase
- kraken
- bybit
- dydx

---

### **12. EXTERNAL SIGNALS** (Webhook Ingestion)
```
GET  /api/external-signals?user_id=X                 # Get received signals
POST /api/external-signals/rules?user_id=X           # Set filtering rules
GET  /api/external-signals/history?user_id=X&days=7  # Webhook history
```

**Webhook Receiver**:
```
POST /webhooks/tradingview
# Automatically ingests TradingView alerts
```

---

### **13. PROOFS** (Signal Verification)
```
GET /api/proofs/{signal_id}                 # Get proof data
GET /api/signals/{id}/proofs                # Get proofs for signal
```

**Proof Includes**:
- Merkle root (immutability proof)
- Blockchain anchor (Ethereum tx hash)
- Audit trail
- Performance data
- Rationale & drivers

---

## 🔄 COMMON FLOWS

### **Flow 1: User Paper Trading a Signal**
```
1. GET /api/signals                          # Browse signals
2. GET /api/signals/{id}/validate?user_id=X  # Validate risk
3. POST /api/signals/{id}/execute?user_id=X  # Execute trade
4. GET /api/portfolio/{user_id}              # Check portfolio
5. GET /api/audit/trail/{user_id}            # See audit log
```

### **Flow 2: Creator Publishing Strategy**
```
1. POST /api/backtest/run                    # Backtest strategy
2. GET /api/backtest/{id}                    # Review results
3. POST /api/creator/strategy-submit         # Submit for review
4. GET /api/creator/verification             # Track verification
5. GET /api/strategies/marketplace           # See published strategy
```

### **Flow 3: User Backtesting Custom Strategy**
```
1. POST /api/backtest/run?config={...}       # Start backtest
2. GET /api/backtest/{id}                    # Poll for results
3. GET /api/backtest/{id}/equity-curve       # Get chart data
4. Compare with marketplace strategies
5. POST /api/strategy/subscribe               # Subscribe if good
```

### **Flow 4: KYC & Creator Tier Progression**
```
1. POST /api/user/kyc                        # Submit KYC
2. Wait for approval
3. GET /api/creator/verification             # Check stage 1
4. Paper trade 20+ times (stage 2)
5. Achieve 55% win rate (stage 3)
6. Complete KYC (stage 4)
7. GET /api/creator/reputation               # Check tier (stage 5)
```

---

## 🛠️ ERROR HANDLING

### **Standard Error Response**
```json
{
  "success": false,
  "error": "descriptive error message",
  "timestamp": "2026-03-17T10:30:00Z"
}
```

### **Common Status Codes**
- `200` - Success
- `201` - Created
- `400` - Bad request (validation error)
- `401` - Unauthorized (missing auth)
- `404` - Not found
- `500` - Server error

---

## 🔑 AUTHENTICATION

### **For Production**
```javascript
// Add JWT token to all requests
headers: {
  "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

### **Query Parameters**
```
?user_id=user-123                    # For MVP (temporary)
?user_id=user-123&auth_token=xyz    # With token
```

---

## 📊 RESPONSE EXAMPLES

### **Portfolio Summary**
```json
{
  "success": true,
  "user_id": "user-123",
  "total_equity": 105000,
  "total_pnl": 5000,
  "pnl_percent": 5.0,
  "open_positions": 3,
  "sharpe_ratio": 1.2,
  "max_drawdown": -8.5
}
```

### **Signal List**
```json
{
  "success": true,
  "signals": [
    {
      "id": "sig-1",
      "ticker": "BTC",
      "signal_type": "BUY",
      "confidence": 0.85,
      "entry_price": 45000,
      "stop_loss": 43500,
      "take_profit": 47500,
      "rationale": "Golden cross + RSI divergence"
    }
  ],
  "count": 50
}
```

### **Backtest Results**
```json
{
  "success": true,
  "backtest_id": "bt-1",
  "status": "COMPLETED",
  "results": {
    "metrics": {
      "initial_capital": 100000,
      "final_equity": 122500,
      "total_return": "22.5%",
      "win_rate": "58%",
      "profit_factor": 2.1,
      "sharpe_ratio": 1.35,
      "max_drawdown": "-12.5%"
    }
  }
}
```

---

## ⚡ PERFORMANCE TIPS

1. **Pagination**: Always use `?limit=50&offset=0` for large lists
2. **Caching**: Response times: 50-200ms (can cache 5min)
3. **Batch Requests**: Avoid individual signal queries
4. **WebSocket**: Coming in Phase 2 for real-time updates
5. **Poll Intervals**: 5-10 seconds for backtests, 1-2 seconds for chat

---

## 🐛 DEBUGGING

### **Check Backend Status**
```bash
curl http://localhost:8000/status
```

### **View Logs**
```bash
# Backend logs in development
tail -f logs/backend.log
```

### **Test Endpoint**
```bash
curl -X POST "http://localhost:8000/api/chat/message?user_id=test&message=hello"
```

---

## 📞 SUPPORT

For issues or questions:
1. Check error message in response
2. Verify user_id is correct
3. Ensure required query parameters
4. Check backend is running (`/health`)
5. Review audit trail for context

---

**All endpoints are production-ready. No additional backend implementation needed.**
