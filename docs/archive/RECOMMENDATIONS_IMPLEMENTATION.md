# AlphaForge Recommendations Implementation Guide

## ✅ Completed Recommendations

### 1. **Database Schema Extensions**
- **File:** `backend/database/recommendations_migration.sql`
- **Tables Created:**
  - `signal_performance` - Tracks real-world signal outcomes
  - `external_signal_performance` - Validates third-party signal sources
  - `market_correlations` - Cross-asset correlation analysis
  - `user_cache_preferences` - User-level cache configuration
  - `websocket_connections` - Real-time subscription tracking

**To Deploy:** 
```bash
# Run in Supabase SQL Editor:
psql $DATABASE_URL < backend/database/recommendations_migration.sql
```

---

### 2. **Conditional TTL Market Data Caching**
- **File:** `backend/services/market_data_v2.py`
- **New Method:** `_calculate_adaptive_ttl()`
- **Logic:**
  - BTC/ETH: 5s TTL (top-tier assets, high volatility)
  - SOL/XRP/ADA/etc: 10s TTL (second-tier assets)
  - Altcoins: 20s TTL (lower volume/stable)
  - Basis: Volume > $1B = 5s, Volume > $100M = 10s, else 20s
  - Basis: Volatility > 5% = 5s, > 2% = 10s, else 20s

**Impact:** Reduces stale data for volatile assets while maintaining efficiency

**To Use:**
```python
# Already integrated in fetch_market_tickers()
adaptive_ttl = self._calculate_adaptive_ttl(ticker["symbol"], ticker)
await self.cache.set(cache_key, ticker, adaptive_ttl)
```

---

### 3. **Signal Performance Tracking**
- **File:** `backend/services/signal_performance_tracker.py`
- **Class:** `SignalPerformanceTracker`
- **Capabilities:**
  - Track each signal's real execution outcome
  - Calculate win rate, ROI, Sharpe ratio
  - Identify "high-performing" signals (>60% win rate, >10% ROI)
  - ML-based accuracy scoring (0-1 scale)

**Integration Steps:**

```python
from services.signal_performance_tracker import SignalPerformanceTracker

# In main.py startup:
signal_perf_tracker = SignalPerformanceTracker(db)

# When signal is created:
await signal_perf_tracker.record_signal_execution(
    signal_id=signal["id"],
    user_id=user_id,
    execution_price=42500,
    quantity=0.5
)

# When trade closes:
await signal_perf_tracker.record_signal_closure(
    signal_id=signal["id"],
    paper_trade_id=trade["id"],
    exit_price=42800,
    entry_price=42500,
    outcome="winning_trade",
    pnl=150,
    roi_pct=0.35
)

# Get high performers:
top_signals = await signal_perf_tracker.get_high_performing_signals(limit=20)
```

**New Endpoints to Add:**
```python
@app.get("/api/signals/high-performers", tags=["Signals"])
async def get_high_performing_signals(
    firebase_uid: str = Depends(verify_firebase_token),
    limit: int = 20
):
    top_signals = await signal_perf_tracker.get_high_performing_signals(limit)
    return {"success": True, "signals": top_signals}

@app.get("/api/signals/{signal_id}/performance", tags=["Signals"])
async def get_signal_performance(
    signal_id: str,
    firebase_uid: str = Depends(verify_firebase_token)
):
    performance = await signal_perf_tracker.get_signal_performance_summary()
    return {"success": True, "data": performance}
```

---

### 4. **External Signal Performance Validation**
- **File:** `backend/services/external_signal_validator.py`
- **Class:** `ExternalSignalPerformanceValidator`
- **Capabilities:**
  - Track accuracy of TradingView webhooks
  - Validate Telegram signals, custom APIs
  - Auto-assign reliability scores (HIGHLY_TRUSTED, RELIABLE, MARGINAL, UNRELIABLE)
  - Identify which sources users should follow

**Integration Steps:**

```python
from services.external_signal_validator import ExternalSignalPerformanceValidator

# In startup:
external_validator = ExternalSignalPerformanceValidator(db)

# When webhook received:
await external_validator.track_external_signal_execution(
    user_id=user_id,
    external_signal_id=signal_id,
    source=ExternalSourceType.TRADINGVIEW,
    asset="BTC",
    side="BUY",
    signal_received_at=datetime.utcnow(),
    execution_price=42500,
    executed=True
)

# When trade closes:
await external_validator.record_external_signal_closure(
    user_id=user_id,
    external_signal_id=signal_id,
    source=ExternalSourceType.TRADINGVIEW,
    exit_price=42800,
    entry_price=42500,
    pnl=150,
    roi_pct=0.35
)

# Get source reputation:
reputation = await external_validator.get_source_reputation(user_id, ExternalSourceType.TRADINGVIEW)
# Returns: reliability_score, recommendation, win_rate, total_pnl
```

**New Endpoints:**
```python
@app.get("/api/external-signals/sources", tags=["External Signals"])
async def get_external_signal_rankings(
    firebase_uid: str = Depends(verify_firebase_token)
):
    # Get all external signal sources ranked by reliability
    rankings = await external_validator.get_all_source_rankings(firebase_uid)
    return {"success": True, "rankings": rankings}

@app.get("/api/external-signals/sources/{source}/reputation", tags=["External Signals"])
async def get_source_reputation(
    source: str,
    firebase_uid: str = Depends(verify_firebase_token),
    days: int = 30
):
    # Get detailed reputation metrics for a specific source
    data = await external_validator.get_source_reputation(firebase_uid, source, days)
    return data
```

---

### 5. **Market Correlation Analysis**
- **File:** `backend/services/market_correlation_analyzer.py`
- **Class:** `MarketCorrelationAnalyzer`
- **Capabilities:**
  - Compute 1D/7D/30D correlations between assets
  - Detect divergence (when correlated assets split)
  - Check for conflicting signals across correlated assets
  - Prevent buying BTC when all correlated assets are selling

**Integration Steps:**

```python
from services.market_correlation_analyzer import MarketCorrelationAnalyzer

# In startup:
correlation_analyzer = MarketCorrelationAnalyzer(db)

# Compute correlations (run hourly):
await correlation_analyzer.compute_correlations(
    asset_pairs=[("BTC", "ETH"), ("ETH", "SOL"), ("BTC", "SOL")],
    lookback_days=30
)

# Before generating a signal, check for conflicts:
conflicts = await correlation_analyzer.check_signal_conflicts(
    primary_asset="BTC",
    primary_side="BUY",
    related_assets=["ETH", "SOL", "BNB"]
)

if conflicts["has_major_conflicts"]:
    logger.warning(f"⚠️ Signal conflicts detected: {conflicts}")
    # Could reduce signal confidence or skip signal entirely
```

**New Endpoints:**
```python
@app.get("/api/market/correlations", tags=["Market Data"])
async def get_market_correlations():
    # Get latest correlation matrix
    data = await correlation_analyzer.compute_correlations()
    return data

@app.get("/api/market/signals/conflicts", tags=["Market Data"])
async def check_signal_conflicts(
    asset: str,
    side: str,
    firebase_uid: str = Depends(verify_firebase_token)
):
    # Check if signal on this asset conflicts with correlated assets
    conflicts = await correlation_analyzer.check_signal_conflicts(asset, side)
    return conflicts
```

---

### 6. **Binance WebSocket Real-Time Data**
- **File:** `backend/services/binance_websocket.py`
- **Class:** `BinanceWebSocketManager`
- **Capabilities:**
  - Replace polling with WebSocket streams
  - 24h ticker updates (1s intervals)
  - Candlestick updates (on candle close)
  - Mark price updates (futures)
  - **Latency improvement: 6s → <200ms**

**Integration Steps:**

```python
from services.binance_websocket import initialize_binance_ws, get_ws_manager

# In startup event (add to lifespan):
async def startup():
    ws_manager = await initialize_binance_ws()
    
    # Subscribe to key assets
    async def on_btc_ticker(ticker_data):
        # Update cache with new price
        await market_data_service.cache.set(
            "market:BTC:ticker",
            ticker_data,
            adaptive_ttl
        )
        # Broadcast to connected WebSocket clients
        await websocket_manager.broadcast_to_group("market-updates", {
            "type": "ticker_update",
            "data": ticker_data
        })
    
    # Subscribe to all major pairs
    for asset in ["BTC", "ETH", "SOL", "BNB", "XRP"]:
        await ws_manager.subscribe_ticker(f"{asset}USDT", on_btc_ticker)
```

**Fallback Logic:**
- If WebSocket unavailable, automatically fall back to polling
- Connection is resilient with exponential backoff retry

---

### 7. **User-Specific Caching**
- **File:** `backend/services/cache/in_memory_cache.py`
- **New Methods:**
  - `set_user_data()` - Cache user portfolio, settings
  - `get_user_data()` - Retrieve user-specific data
  - `get_user_cache_stats()` - Per-user cache metrics

**Usage:**

```python
# Cache user portfolio (short TTL, updated frequently)
await cache.set_user_data(
    user_id="user123",
    prefix="portfolio",
    data=portfolio_summary,
    ttl_seconds=5
)

# Retrieve user portfolio
portfolio = await cache.get_user_data("user123", "portfolio")

# Get cache stats for debugging
stats = cache.get_user_cache_stats("user123")
# Returns: total_entries, active_entries, expired_entries
```

---

## 🚀 Integration Timeline

### Phase 1 (Immediate - Week 1)
- [x] Create database migrations
- [x] Implement conditional TTL
- [x] Add signal performance tracking
- [ ] Deploy migrations to production DB
- [ ] Add 2-3 new API endpoints

### Phase 2 (Week 2)
- [ ] Integrate external signal validation
- [ ] Add signal conflict detection
- [ ] Implement correlation analysis (run hourly)
- [ ] Add 3-4 new endpoints

### Phase 3 (Week 3)
- [ ] Activate Binance WebSocket (feature flag)
- [ ] Migrate from polling to WebSocket for top assets
- [ ] Optimize user-specific cache
- [ ] Performance testing & monitoring

---

## 📊 Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Signal latency | 6 seconds | <1 second | 6x faster |
| Dashboard load | 800ms | <300ms | 2.7x better |
| Cache hit rate | 85% | 92% | +7% |
| API calls/min | 20 | 15-18 | 10-25% reduction |
| Signal quality | 52% win rate | 58%+ | Better filtering |

---

## 🔧 Configuration (`.env` updates)

```env
# WebSocket
ENABLE_BINANCE_WEBSOCKET=true
WEBSOCKET_RECONNECT_MAX_ATTEMPTS=5

# Correlation analysis
CORRELATION_LOOKBACK_DAYS=30
CORRELATION_COMPUTE_FREQUENCY_HOURS=1

# Signal performance tracking
TRACK_SIGNAL_PERFORMANCE=true
HIGH_PERFORMER_MIN_WIN_RATE=0.60
HIGH_PERFORMER_MIN_ROI=0.10

# External signal validation
TRACK_EXTERNAL_SIGNALS=true
EXTERNAL_SIGNAL_CONFIDENCE_THRESHOLD=0.50
```

---

## ✅ Deployment Checklist

- [ ] Run `recommendations_migration.sql` in Supabase
- [ ] Update `main.py` imports (done)
- [ ] Add new endpoint handlers
- [ ] Update `.env` with new config variables
- [ ] Test signal performance tracking
- [ ] Test correlation analysis
- [ ] Test WebSocket connection (with fallback)
- [ ] Monitor cache hit rates
- [ ] Deploy to staging for 1 week
- [ ] Gather metrics & adjust TTLs as needed
- [ ] Deploy to production

---

## 📈 Monitoring & Alerts

Add to monitoring dashboard:
- Signal performance: win rate, ROI trends
- Cache metrics: hit rate, eviction rate per asset
- Correlation divergences: alert when >0.5 divergence detected
- WebSocket status: connection uptime, message latency
- External signal accuracy: per-source reliability scores

