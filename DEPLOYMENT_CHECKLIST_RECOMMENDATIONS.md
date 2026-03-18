# 🚀 Deployment Checklist - Recommendations Implementation

**Date:** March 18, 2026  
**Status:** ✅ READY FOR DEPLOYMENT

---

## Phase 1: Pre-Deployment Verification

### ✅ Code Files Created/Modified

- [x] `/backend/services/signal_performance_tracker.py` - Signal outcome tracking
- [x] `/backend/services/external_signal_validator.py` - External source validation
- [x] `/backend/services/market_correlation_analyzer.py` - Correlation analysis
- [x] `/backend/services/binance_websocket.py` - Real-time WebSocket
- [x] `/backend/services/market_data_v2.py` - Updated with adaptive TTL
- [x] `/backend/services/cache/in_memory_cache.py` - Updated with user-specific cache
- [x] `/backend/main.py` - Service initialization + new endpoints
- [x] `/backend/.env` - Feature flags added
- [x] `/backend/database/recommendations_migration.sql` - Database schema
- [x] `/IMPLEMENTATION_COMPLETE.md` - Documentation

### ✅ Syntax Validation

```bash
# Run this to verify Python syntax
cd backend
python -m py_compile main.py
python -m py_compile services/signal_performance_tracker.py
python -m py_compile services/external_signal_validator.py
python -m py_compile services/market_correlation_analyzer.py
python -m py_compile services/binance_websocket.py
```

### ✅ Dependencies Check

All required packages already in `requirements.txt`:
- [x] `websockets` - WebSocket support
- [x] `numpy` - Correlation computations
- [x] `redis` - Caching (optional)
- [x] `sqlalchemy` - ORM operations
- [x] `fastapi` - Web framework
- [x] `pandas` - Data analysis (for correlations)

---

## Phase 2: Database Migration

### Step 1: Backup Database (RECOMMENDED)

```bash
# Export current database (optional but recommended)
pg_dump $DATABASE_URL > alphaforge_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Execute Migrations

**Option A: Using Supabase Dashboard (Easiest)**

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Select your project: **studio-1193676023-87512**
3. Navigate to: **SQL Editor**
4. Click **New Query**
5. Copy contents from `backend/database/recommendations_migration.sql`
6. Click **Run** (or CTRL+ENTER)
7. Verify: Check **Table Editor** for 5 new tables

**Option B: Using psql CLI**

```bash
# Set database URL
export DATABASE_URL="postgresql://postgres.xouqexmepzkxlymihjuw:Devmahn_FXDB1!.@aws-1-eu-west-1.pooler.supabase.com:6543/postgres"

# Run migration
psql $DATABASE_URL < backend/database/recommendations_migration.sql

# Verify
psql $DATABASE_URL -c "\dt" | grep -E "signal_performance|external_signal|market_correlation|user_cache|websocket"
```

**Option C: Using Migration Script**

```bash
cd backend
python scripts/run_migrations.py
```

### Step 3: Verify Migration Success

```sql
-- Run in Supabase SQL Editor

-- Check new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('signal_performance', 'external_signal_performance', 'market_correlations', 'user_cache_preferences', 'websocket_connections');

-- Expected output: 5 rows
```

---

## Phase 3: Service Initialization

### Step 1: Verify Service Imports

```bash
# Check imports are in main.py (lines ~35-40)
grep -n "SignalPerformanceTracker\|ExternalSignalPerformanceValidator\|MarketCorrelationAnalyzer\|initialize_binance_ws" backend/main.py
```

### Step 2: Verify Global Declarations

```bash
# Check global service variables added (lines ~117-120)
grep -n "signal_perf_tracker\|external_signal_validator\|market_correlation_analyzer\|binance_ws_manager" backend/main.py | head -10
```

### Step 3: Verify Lifespan Registration

```bash
# Check services initialized in startup (lines ~179-210)
grep -A 20 "INITIALIZE RECOMMENDATION SERVICES" backend/main.py
```

---

## Phase 4: Feature Flags Configuration

### Verify .env Settings

```bash
# Check feature flags in .env
grep "ENABLE_" backend/.env
```

**Expected Output:**
```
ENABLE_SIGNAL_PERFORMANCE_TRACKING=true
ENABLE_EXTERNAL_SIGNAL_VALIDATION=true
ENABLE_MARKET_CORRELATION_ANALYSIS=true
ENABLE_BINANCE_WEBSOCKET=true
ENABLE_USER_SPECIFIC_CACHING=true
```

### Toggle Features (Optional)

To disable any feature temporarily:

```bash
# Edit .env
ENABLE_BINANCE_WEBSOCKET=false  # Use polling fallback if WebSocket issues
```

---

## Phase 5: Deploy to Staging

### Step 1: Start Backend with New Services

```bash
cd backend

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start backend
python main.py
```

**Expected Startup Log:**

```
✅ Market data service initialized (multi-source)
✅ Signal aggregator initialized (multi-source indicators)
✅ Signal performance tracker initialized
✅ External signal validator initialized
✅ Market correlation analyzer initialized
✅ Binance WebSocket manager initialized (real-time data)
✅ All recommendation services initialized
```

### Step 2: Test New Endpoints

```bash
# Set auth token (replace with real Firebase token)
TOKEN="<your-firebase-token>"

# Test high-performing signals endpoint
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/signals/high-performers?limit=10"

# Test external sources endpoint
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/external-signals/sources"

# Test market correlations endpoint
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/market/correlations?time_window=30d"

# Test WebSocket status
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/websocket/status"

# Test cache stats
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/cache/stats"
```

### Step 3: Check Logs for Errors

```bash
# Monitor logs for any errors
tail -f backend.log | grep "ERROR\|❌"
```

---

## Phase 6: Performance Testing

### Test 1: Signal Performance Tracking

```python
# Test that signals are being tracked
import requests
response = requests.get(
    "http://localhost:8000/api/signals/high-performers",
    headers={"Authorization": f"Bearer {TOKEN}"}
)
print(response.json())
# Should show: {"success": true, "count": N, "high_performers": [...]}
```

### Test 2: WebSocket Connection

```python
# Test WebSocket is connected
import asyncio
import websockets
import json

async def test_websocket():
    uri = "wss://localhost:8000/ws/market-updates"
    async with websockets.connect(uri) as websocket:
        # Should receive real-time updates
        data = await websocket.recv()
        print(f"Received: {data}")

asyncio.run(test_websocket())
```

### Test 3: Cache Performance

```bash
# Monitor cache hit rate
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/cache/stats" | jq '.cache_stats'
```

---

## Phase 7: Production Deployment

### Step 1: Review Environment Variables

```bash
# Verify production settings in .env
grep "API_ENV\|CACHE_BACKEND\|ENABLE_" backend/.env
```

**For Production, Should Be:**
```
API_ENV=production
CACHE_BACKEND=redis  # Switch from memory to redis
ENABLE_SIGNAL_PERFORMANCE_TRACKING=true
ENABLE_MARKET_CORRELATION_ANALYSIS=true
ENABLE_BINANCE_WEBSOCKET=true
```

### Step 2: Deploy to Production

```bash
# Using your deployment platform (Render, Railway, etc.)
# Push changes to main branch or deploy via CLI

# Example for Render:
render deploy --service alphaforge-backend

# Example for Railway:
railway up
```

### Step 3: Monitor Production Logs

```bash
# Check for any initialization errors
journalctl -u alphaforge-backend -f

# Or via your platform's logs dashboard
```

---

## Phase 8: Post-Deployment Verification

### ✅ Health Checks

```bash
# Check backend health
curl -s http://api.alphaforge.com/health | jq '.'

# Check signal performance tracking
curl -s -H "Authorization: Bearer $TOKEN" \
  http://api.alphaforge.com/api/signals/high-performers | jq '.count'

# Check WebSocket status
curl -s -H "Authorization: Bearer $TOKEN" \
  http://api.alphaforge.com/api/websocket/status | jq '.status'
```

### ✅ Database Verification

```sql
-- Check data is being written to new tables
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name LIKE '%signal_performance%';

-- Should show the new tables exist
```

### ✅ Performance Metrics

Monitor these metrics over 24 hours:

- **Signal Latency:** Target <1s (was 6s)
- **Cache Hit Rate:** Target >70% for user data
- **WebSocket Connections:** Should show active connections
- **External Signal Accuracy:** Track source reliability

---

## Rollback Plan (If Needed)

### Quick Rollback

```bash
# Stop the backend
systemctl stop alphaforge-backend

# Revert to previous version
git checkout HEAD~1 backend/main.py

# Restart
systemctl start alphaforge-backend

# Disable features in .env if needed
ENABLE_BINANCE_WEBSOCKET=false
```

### Full Rollback (Database)

```sql
-- Drop new tables (careful - this deletes data!)
DROP TABLE IF EXISTS signal_performance CASCADE;
DROP TABLE IF EXISTS external_signal_performance CASCADE;
DROP TABLE IF EXISTS market_correlations CASCADE;
DROP TABLE IF EXISTS user_cache_preferences CASCADE;
DROP TABLE IF EXISTS websocket_connections CASCADE;
```

---

## Troubleshooting

### Issue: "Service not initialized" Error

```
Error: Signal performance tracking not enabled
```

**Solution:**
```bash
# Check .env has feature flag
grep "ENABLE_SIGNAL_PERFORMANCE_TRACKING" backend/.env

# Should output: ENABLE_SIGNAL_PERFORMANCE_TRACKING=true

# If not, add it and restart backend
```

### Issue: WebSocket Connection Failed

```
Warning: Failed to initialize Binance WebSocket: Connection refused
```

**Solution:**
```bash
# Check Binance server is reachable
curl -s https://stream.binance.com/health | jq '.'

# If fails, backend will automatically use polling fallback
# Set fallback in .env:
ENABLE_BINANCE_WEBSOCKET=false
```

### Issue: Database Migration Failed

```
Error: relation "signal_performance" already exists
```

**Solution:**
```sql
-- This is OK - migrations use IF NOT EXISTS
-- Just confirm tables exist:
SELECT * FROM information_schema.tables 
WHERE table_name IN ('signal_performance', 'external_signal_performance');

-- Should return 5 rows for the 5 new tables
```

### Issue: Authentication Fails on New Endpoints

```
401 Unauthorized
```

**Solution:**
```bash
# Verify Firebase token is valid
# Make sure Authorization header format is correct:
Authorization: Bearer <firebase_token>

# Not:
Authorization: <firebase_token>
```

---

## Success Indicators

You'll know everything is working when:

✅ Backend starts without errors  
✅ All 6 new endpoints respond with 200 OK  
✅ Signal performance tracker logs signal executions  
✅ External signals show source reliability scores  
✅ Market correlations compute without errors  
✅ WebSocket connection shows as "connected"  
✅ Cache stats show >70% hit rate for frequently accessed data  
✅ Signal latency drops from 6s to <1s  

---

## Support

For issues during deployment:

1. **Check logs first:** `journalctl -u alphaforge-backend -f`
2. **Review implementation guide:** `RECOMMENDATIONS_IMPLEMENTATION.md`
3. **Verify feature flags:** `grep ENABLE_ backend/.env`
4. **Test individual services:** Run endpoint tests from Phase 5
5. **Check database:** Verify migrations ran with SQL queries above

---

**Last Updated:** March 18, 2026  
**Version:** 1.0.0  
**Status:** ✅ Ready for Deployment
