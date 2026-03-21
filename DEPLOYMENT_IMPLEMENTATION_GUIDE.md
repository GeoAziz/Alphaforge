# 🚀 AlphaForge Backend Deployment Guide

## Overview

This guide covers the complete deployment process for AlphaForge, including:
- **Database Migration** - Automated migration runner for Phase 1 & Phase 2 schemas
- **Service Initialization** - Automatic service startup and health verification
- **Production Deployment** - Step-by-step instructions for going live

---

## Prerequisites

1. **Environment Setup**
   - Python 3.9+
   - PostgreSQL client (psycopg2)
   - All dependencies installed: `pip install -r requirements.txt`

2. **Environment Variables**
   ```bash
   # In backend/.env
   DATABASE_URL=postgresql://...  # Supabase connection string
   API_ENV=development            # or "production"
   NEXT_PUBLIC_API_URL=...        # Frontend API endpoint
   ```

3. **Database Access**
   - Supabase account with admin credentials
   - DATABASE_URL pointing to your Supabase PostgreSQL

---

## Part 1: Database Migration

### Option A: Automatic Migration (Recommended)

The backend automatically runs migrations on startup:

```bash
cd backend
python main.py
```

**What happens:**
1. ✅ Connects to database
2. ✅ Checks if Phase 1 tables exist (if not, runs migration)
3. ✅ Checks if Phase 2 tables exist (if not, runs migration)
4. ✅ Verifies all tables were created correctly
5. ✅ Initializes all services
6. 🚀 Backend is ready

**Output:**
```
🚀 Starting AlphaForge Backend API
🔗 Verifying database connection...
✅ Database connection verified
🔍 Checking migration status...
✅ Phase 1 migration verified
✅ Phase 2 migration verified
📦 Verifying Service Imports...
✅ All 15 required services verified
📋 Startup Summary
✅ Database: connected
✅ Migrations: complete
📦 Services: 15 verified
✅ Backend is ready to start!
```

### Option B: Manual Migration (For Production with caution)

Run migrations explicitly:

```bash
cd backend
python scripts/run_all_migrations.py
```

**What happens:**
- Phase 1: Creates core schema (users, signals, portfolios, etc.)
- Phase 2: Creates recommendation tables (signal_performance, etc.)
- Verifies all tables exist
- Provides detailed status report

**Verify Existing Schema:**
```bash
python scripts/run_all_migrations.py --verify
```

**Output:**
```
🚀 AlphaForge Database Migration
📍 Database: xouqexmepzkxlymihjuw

🔄 Running Phase 1: Core Schema
🔗 Connecting to Supabase...
✅ Connected to PostgreSQL
📖 Loaded supabase_phase1_init.sql (12543 bytes)
📝 Parsed 45 SQL statements
📊 Initial table count: 0
[phase_1] 45/45 statements executed ✅
📊 Final table count: 18 (+18)
✅ Phase 1: Core Schema completed successfully

🔄 Running Phase 2: Recommendations
...
📊 Final table count: 23 (+5)
✅ Phase 2: Recommendations completed successfully

📋 Migration Summary
✅ Phase 1: Core Schema: 45 statements, 18 tables
✅ Phase 2: Recommendations: 25 statements, 5 tables

✅ All migrations completed successfully!
```

---

## Part 2: Service Initialization

Services initialize automatically in the `lifespan` context manager of FastAPI:

### Initialization Order

1. **Database Connection & Verification**
   ```python
   orchestrator = get_orchestrator()
   startup_ok = await orchestrator.startup(auto_migrate=True)
   ```

2. **Redis/Cache Initialization**
   ```python
   redis_connected = await redis_manager.connect()
   ```

3. **Multi-Source Market Data Service**
   ```python
   market_data_service = MarketDataService()
   await market_data_service.initialize()
   ```

4. **Core Services** (in parallel where possible)
   - SignalAggregator
   - SignalProcessor
   - PaperTradingEngine
   - PortfolioService
   - RiskManager
   - ChatService
   - CreatorService
   - UserService
   - And 7 more...

5. **Recommendation Services** (Phase 3)
   - SignalPerformanceTracker
   - ExternalSignalPerformanceValidator
   - MarketCorrelationAnalyzer
   - BinanceWebSocketManager

6. **Analytics & Monitoring**
   - PostHog
   - Performance Monitor
   - Rate Limiter

### Service Configuration

Control service initialization via environment variables in `.env`:

```bash
# Enable/disable recommendation services
ENABLE_SIGNAL_PERFORMANCE_TRACKING=true
ENABLE_EXTERNAL_SIGNAL_VALIDATION=true
ENABLE_MARKET_CORRELATION_ANALYSIS=true
ENABLE_BINANCE_WEBSOCKET=true
ENABLE_USER_SPECIFIC_CACHING=true

# Feature flags
FEATURE_BACKTESTING=false
FEATURE_LIVE_TRADING=false
FEATURE_KYC=false

# Cache configuration
CACHE_BACKEND=memory  # or "redis"
REDIS_HOST=localhost
REDIS_PORT=6379

# Rate limiting
RATE_LIMIT_ENABLED=true
```

### Graceful Degradation

If a service fails to initialize:
- ✅ Development mode: Logs warning, continues with other services
- ✅ Production mode: Logs warning, continues (services have fallbacks)
- ✅ Only database migration failures cause hard stop

---

## Part 3: Production Deployment

### 1. Pre-Deployment Checklist

```bash
# 1. Test database connection
python scripts/run_all_migrations.py --verify

# 2. Check all services can import
python -c "from main import app"

# 3. Run health check endpoint
curl http://localhost:8000/health
curl http://localhost:8000/ready

# 4. Run integration tests
pytest -v backend/tests/
```

### 2. Environment Setup

Create `.env` for production:

```bash
# Database (Supabase)
DATABASE_URL=postgresql://postgres.xxxxx:password@...

# API Configuration
API_ENV=production
API_PORT=8000
REQUIRE_REAL_DB=true

# Frontend
NEXT_PUBLIC_API_URL=https://your-domain.com/api

# Security
SECURITY_HEADERS_ENABLED=true
CORS_ALLOW_ORIGINS=https://your-domain.com

# Cache
CACHE_BACKEND=redis  # Use Redis in production
REDIS_HOST=your-redis-host
REDIS_PORT=6379

# Analytics
POSTHOG_API_KEY=your-key
POSTHOG_HOST=https://us.i.posthog.com

# Feature flags
FEATURE_BACKTESTING=true
FEATURE_LIVE_TRADING=true
FEATURE_KYC=true

# Services (all enabled in production)
ENABLE_SIGNAL_PERFORMANCE_TRACKING=true
ENABLE_EXTERNAL_SIGNAL_VALIDATION=true
ENABLE_MARKET_CORRELATION_ANALYSIS=true
ENABLE_BINANCE_WEBSOCKET=true
```

### 3. Deployment Steps (Render/Railway)

**For Render.com:**

1. Connect your repository
2. Create new Web Service
3. Set environment variables from `.env` above
4. Build command: `pip install -r requirements.txt`
5. Start command: `python main.py`
6. Port: 8000

**For Railway.app:**

1. Connect GitHub repository
2. Set environment variables
3. Add PostgreSQL plugin
4. Deploy

### 4. Post-Deployment Verification

```bash
# 1. Check logs
journalctl -u alphaforge -f
# or cloud provider logs dashboard

# 2. Test health endpoint
curl https://your-domain.com/api/health

# 3. Check database
curl https://your-domain.com/api/signals/top

# 4. Monitor analytics
# Check PostHog dashboard

# 5. Load test (optional)
python backend/scripts/load_testing_suite.py
```

---

## Common Issues & Fixes

### Issue 1: "DATABASE_URL not set"
```bash
# Solution: Add to .env in backend/ directory
DATABASE_URL=postgresql://postgres.xxxxx:password@...
```

### Issue 2: "Connection refused"
```bash
# Solution: Verify connection string
psql $DATABASE_URL -c "SELECT 1"
```

### Issue 3: "Migration failed: relation 'users' already exists"
```bash
# Solution: This is OK! Migrations are idempotent (safe to re-run)
# Just continue - new tables will be created
```

### Issue 4: "Service failed to initialize"
```bash
# Solution: Check service logs
# Services have graceful fallbacks - check logs for details
tail -f backend/logs/app.log
```

### Issue 5: "Redis connection failed"
```bash
# Solution: Redis is optional, will fallback to in-memory cache
# To use Redis, ensure REDIS_HOST and REDIS_PORT are set correctly
```

---

## Database Schema Overview

### Phase 1 Tables (18)
**Users & Auth:**
- `users` - User accounts and profiles
- `api_keys` - API authentication keys
- `kyc_verifications` - KYC verification records

**Signals & Trading:**
- `signals` - Trading signals
- `paper_trades` - Paper trading transactions
- `positions` - Open trading positions
- `portfolios` - User portfolios
- `strategies` - User strategies
- `backtests` - Backtest results

**Creators & Marketplace:**
- `creator_profiles` - Creator profiles
- `creator_strategies` - Creator strategies
- `strategy_subscriptions` - Signal subscriptions
- `external_signals` - External signal sources
- `external_signal_rules` - Signal routing rules

**Other:**
- `chat_messages` - Chat message history
- `notifications` - User notifications
- `audit_logs` - Audit trail
- `user_risk_settings` - Risk management settings

### Phase 2 Tables (5)
**Recommendations:**
- `signal_performance` - Signal performance tracking
- `external_signal_performance` - External signal validation
- `market_correlations` - Market correlation data
- `user_cache_preferences` - User cache settings
- `websocket_connections` - WebSocket connection tracking

---

## Monitoring & Logging

### Log Levels
Development: `LOG_LEVEL=INFO`
Production: `LOG_LEVEL=WARNING`

### Key Endpoints

**Health Checks:**
- `GET /health` - Basic health check
- `GET /ready` - Readiness probe (checks all systems)

**Metrics:**
- `GET /metrics` - Prometheus metrics
- Performance monitor dashboard in PostHog

### Key Metrics

- Database query time
- Signal generation latency
- API response times
- WebSocket connection count
- Cache hit rate

---

## Rollback Procedure

### If Migrations Fail

1. **Check logs for specific error**
   ```bash
   grep "❌" backend/logs/migration.log
   ```

2. **Verify database state**
   ```bash
   # In Supabase SQL Editor
   SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;
   ```

3. **In development: Restart and re-run**
   ```bash
   python scripts/run_all_migrations.py
   ```

4. **In production: Contact support**
   - Migrations are idempotent - safe to retry
   - Won't duplicate tables

---

## Support & Troubleshooting

### Quick Diagnostic Script

```bash
# backend/scripts/diagnose.sh
#!/bin/bash
echo "🔍 AlphaForge Diagnostics"
echo "=========================="

echo "1. Database Connection"
python -c "from database.db import get_db; db = get_db(); print('✅ Database OK')" || echo "❌ Database Failed"

echo ""
echo "2. Migration Status"
python scripts/run_all_migrations.py --verify

echo ""
echo "3. Service Imports"
python -c "from main import app; print('✅ All services importable')" || echo "❌ Import Failed"

echo ""
echo "4. Network Check"
curl -s http://localhost:8000/health && echo "✅ Backend responding" || echo "❌ Backend offline"
```

---

## Next Steps

1. ✅ **Complete database migration** - Run `python scripts/run_all_migrations.py`
2. ✅ **Start backend** - Run `python main.py`
3. ✅ **Test endpoints** - Run integration tests
4. ✅ **Deploy frontend** - Point to backend API
5. ✅ **Monitor production** - Watch logs and metrics

---

**Questions?** Check the main README.md or contact the development team.
