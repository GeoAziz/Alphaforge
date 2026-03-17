# AlphaForge Backend - Complete Setup Guide

## Overview

This is the **production-ready backend** for the AlphaForge trading signal platform. Built with FastAPI, PostgreSQL (via Supabase), and microservices architecture.

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│  FastAPI Application (main.py)                      │
│  ├─ Signal Aggregator Service                       │
│  ├─ Signal Processor Service                        │
│  ├─ Paper Trading Engine                            │
│  ├─ Portfolio Service                               │
│  └─ Risk Manager                                    │
└─────────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────────┐
│  Supabase PostgreSQL Database                       │
│  ├─ Users & Profiles                                │
│  ├─ Signals                                         │
│  ├─ Paper Trades & Positions                        │
│  ├─ Portfolios                                      │
│  ├─ KYC/AML Records                                 │
│  └─ Audit Logs                                      │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start (5 Minutes)

### 1. Prerequisites
```bash
# Ensure you have Python 3.10+
python --version

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

**Required .env vars:**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_ANON_KEY=your-anon-key
ALPHA_VANTAGE_API_KEY=demo  # Get from alphavantage.co
```

### 4. Initialize Database
```bash
python scripts/init_db.py
# Follow on-screen instructions to manually run SQL migrations
```

### 5. Start Backend
```bash
# Development (hot reload)
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**API running at:** http://localhost:8000

**API Docs:** http://localhost:8000/docs (Swagger UI)

---

## Detailed Setup

### Supabase Configuration

1. **Create free Supabase account:** https://supabase.com

2. **Create new project** (follow setup wizard)

3. **Get your credentials** from Project Settings → API:
   - Copy `Project URL` → `SUPABASE_URL`
   - Copy `service_role key` → `SUPABASE_SERVICE_KEY`
   - Copy `anon key` → `SUPABASE_ANON_KEY`

4. **Create database schema:**
   - Go to SQL Editor in Supabase dashboard
   - Create new query
   - Paste entire SQL from `database/migrations.py`
   - Execute

5. **Verify tables created:**
   ```sql
   SELECT * FROM information_schema.tables WHERE table_schema = 'public';
   ```

### External API Keys

**Alpha Vantage** (market data):
- Free tier: 5 requests/min, 500/day
- Get key: https://www.alphavantage.co/api/
- Set `ALPHA_VANTAGE_API_KEY=your-key` in .env

**Polygon.io** (optional, for premium data):
- Free tier: $0
- Get key: https://polygon.io/
- Set `POLYGON_IO_API_KEY=your-key` in .env

**TradingView Webhooks** (optional):
- Set `TRADINGVIEW_WEBHOOK_SECRET=your-secret` in .env

---

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /status` - Detailed system status

### Users
- `POST /api/users/register` - Register new user
- `GET /api/users/{user_id}` - Get user profile
- `PUT /api/users/{user_id}` - Update user profile

### Signals
- `GET /api/signals` - Get top signals
- `POST /api/signals/process` - Trigger signal generation
- `POST /api/signals/{signal_id}/validate` - Validate signal for trading

### Paper Trading
- `POST /api/trades/paper` - Create paper trade
- `POST /api/trades/paper/{trade_id}/close` - Close paper trade
- `GET /api/trades/paper` - Get trade history

### Portfolio
- `GET /api/portfolio/{user_id}` - Get portfolio summary
- `GET /api/portfolio/{user_id}/metrics` - Get performance metrics
- `GET /api/positions/{user_id}` - Get open positions

### Webhooks
- `POST /webhooks/tradingview` - TradingView signal ingestion

---

## Environment Variables

**App Configuration:**
```
API_ENV=development          # development or production
API_HOST=0.0.0.0            # Listen on all interfaces (ngrok friendly)
API_PORT=8000               # Port to listen on
LOG_LEVEL=INFO              # Logging level
```

**Database:**
```
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
SUPABASE_ANON_KEY=...
```

**External APIs:**
```
ALPHA_VANTAGE_API_KEY=demo
POLYGON_IO_API_KEY=...
TRADINGVIEW_WEBHOOK_SECRET=...
```

**Signal Processing:**
```
SIGNAL_PROCESSOR_INTERVAL=300   # seconds between runs
NUM_TOP_SIGNALS=50              # max signals to return
```

**Paper Trading:**
```
INITIAL_PAPER_BALANCE=100000    # starting balance
PAPER_TRADING_SLIPPAGE=0.001    # 0.1% slippage
```

**Risk Management:**
```
MAX_POSITION_SIZE_PCT=0.02      # 2% max per position
MAX_PORTFOLIO_EXPOSURE_PCT=0.20 # 20% per asset
MAX_LEVERAGE=5                  # max leverage
```

---

## Exposing via Ngrok

For public testing (integrate with frontend via ngrok URL):

```bash
# Install ngrok (free)
brew install ngrok  # macOS
# or download from https://ngrok.com/download

# Create free account and authenticate
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Start tunnel (in new terminal)
ngrok http 8000

# Output shows public URL, e.g.
# Forwarding  https://abc123def456.ngrok.io -> http://localhost:8000
```

**Use in frontend:**
```env
NEXT_PUBLIC_API_URL=https://abc123def456.ngrok.io
```

---

## Database Schema

### Core Tables

**users** - User accounts and profiles
- id (UUID)
- email (unique)
- display_name
- plan (free|basic|pro|enterprise)
- risk_tolerance (conservative|moderate|aggressive)
- kyc_status (NOT_STARTED|SUBMITTED|APPROVED|REJECTED)
- created_at, updated_at

**signals** - Trading signals from aggregation
- id (UUID)
- ticker (e.g., BTC, ETH)
- signal_type (BUY|SELL|HOLD)
- confidence (0.0-1.0)
- entry_price, stop_loss_price, take_profit_price
- rationale, drivers (JSON)
- created_by (FK: users)

**paper_trades** - Mock trades for validation
- id (UUID)
- user_id (FK)
- signal_id (FK)
- asset, direction (LONG|SHORT)
- entry_price, quantity, stop_loss, take_profit
- exit_price, status (OPEN|CLOSED|LIQUIDATED)
- pnl, pnl_percent
- opened_at, closed_at

**portfolios** - Per-user portfolio state
- id (UUID)
- user_id (FK, unique)
- starting_balance, current_balance
- total_pnl, total_pnl_percent
- total_trades, win_count, loss_count
- sharpe_ratio, max_drawdown

**positions** - Open positions (live trading)
- id (UUID)
- user_id (FK)
- ticker, direction (LONG|SHORT)
- entry_price, quantity, current_price
- unrealized_pnl, risk_exposure_pct
- signal_id (FK)
- opened_at

**kyc_verifications** - KYC/AML records
- id (UUID)
- user_id (FK, unique)
- status (SUBMITTED|APPROVED|REJECTED)
- onfido_applicant_id, onfido_check_id
- aml_status, aml_reason
- created_at, completed_at

**audit_logs** - Immutable audit trail
- id (UUID)
- user_id (FK)
- action, resource_type, resource_id
- changes (JSON)
- ip_address, user_agent
- timestamp

---

## Services Overview

### 1. Signal Aggregator Service
**File:** `services/signal_aggregator.py`

Fetches signals from external sources:
- ✅ Alpha Vantage (technical indicators)
- ✅ Polygon.io (market data)
- ✅ TradingView webhooks (manual alerts)

**Usage:**
```python
aggregator = SignalAggregator()
signals = await aggregator.fetch_all_signals(["BTC", "ETH"])
```

**Sample output:**
```json
{
  "ticker": "BTC",
  "signal_type": "BUY",
  "confidence": 0.85,
  "rationale": "RSI at 28 (Oversold)",
  "drivers": ["RSI"],
  "source": "alpha_vantage"
}
```

### 2. Signal Processor Service
**File:** `services/signal_processor.py`

Filters and ranks signals:
- Confidence threshold filtering
- Deduplication
- Strength-based ranking
- Per-ticker limiting

**Usage:**
```python
processor = SignalProcessor()
processed = processor.process_signals(raw_signals)
```

### 3. Paper Trading Engine
**File:** `services/paper_trading.py`

Simulates trading:
- Order execution with slippage
- PnL calculation
- Performance metrics (Sharpe, drawdown, win rate)
- Position tracking

**Usage:**
```python
engine = PaperTradingEngine(db)
result = await engine.execute_paper_trade(user_id, signal_id, "BTC", "LONG", 63000, 1.0)
metrics = await engine.get_portfolio_metrics(user_id)
```

### 4. Portfolio Service
**File:** `services/portfolio.py`

Manages open positions:
- Open position tracking
- Portfolio summary computation
- Position size validation
- Risk exposure calculation

**Usage:**
```python
portfolio = PortfolioService(db)
summary = await portfolio.get_portfolio_summary(user_id)
positions = await portfolio.get_open_positions(user_id)
```

### 5. Risk Manager
**File:** `services/risk_manager.py`

Validates trades against constraints:
- Position sizing
- Portfolio exposure limits
- Leverage checks
- Correlation analysis
- Risk scoring

**Usage:**
```python
risk_mgr = RiskManager(db)
validation = await risk_mgr.validate_trade(user_id, signal, portfolio_balance)
```

---

## Testing

### Test Endpoints with curl

```bash
# Health check
curl http://localhost:8000/health

# Get signals
curl http://localhost:8000/api/signals?limit=10

# Process signals
curl -X POST http://localhost:8000/api/signals/process

# Register user
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","display_name":"Test User"}'

# Create paper trade
curl -X POST http://localhost:8000/api/trades/paper \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"user123",
    "signal_id":"sig123",
    "asset":"BTC",
    "direction":"LONG",
    "entry_price":63000,
    "quantity":1.0
  }'

# Get portfolio
curl http://localhost:8000/api/portfolio/user123
```

### Interactive Testing

Open Swagger UI: http://localhost:8000/docs

All endpoints documented with try-it-out functionality.

---

## Deployment

### Option 1: Render.com (Recommended for free tier)

1. Push code to GitHub
2. Connect GitHub repo to Render
3. Set environment variables in Render dashboard
4. Deploy

**URL:** https://alphaforge-backend-abc123.onrender.com

### Option 2: Railway.app

1. Push to GitHub
2. Connect GitHub
3. Auto-deploys on push

### Option 3: DigitalOcean App Platform

Similar setup to above platforms.

---

## Monitoring & Logging

### View Logs

```bash
# Development (console output)
python main.py

# Production (via hosting platform dashboard)
# Render: https://dashboard.render.com/logs
# Railway: https://railway.app/project/logs
```

### Key Log Messages

```
✅ - Success/completion
❌ - Error
⚠️  - Warning
ℹ️  - Info
📊 - Data metrics
💾 - Database operation
🔄 - Processing
```

---

## Troubleshooting

### "Supabase connection failed"
- Check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
- Ensure Supabase project is active
- Test with curl: `curl $SUPABASE_URL/rest/v1/users -H "apikey: $SUPABASE_ANON_KEY"`

### "Signal aggregation returning empty"
- Check API keys (Alpha Vantage, Polygon)
- Verify API rate limits not exceeded
- Check network connectivity

### "Paper trade creation fails"
- Ensure user exists in database
- Verify portfolio record exists
- Check signal exists

### Ngrok URL keeps changing
- Use paid ngrok tier for static URL
- Or update frontend env var each time
- Or use ngrok authtoken for reserved URL (paid)

---

## Performance Optimization

### Database
- ✅ Indexed all foreign keys
- ✅ Indexed ticker and created_at for fast queries
- ✅ Row-level security enabled

### API
- Connection pooling enabled
- Request validation
- Async/await throughout

### Caching
- In-memory signal cache (future)
- Redis integration (optional)

---

## Next Steps

1. ✅ Start backend: `python main.py`
2. ✅ Verify health: `curl http://localhost:8000/health`
3. ✅ Create sample user via `/api/users/register`
4. ✅ Trigger signal generation: `POST /api/signals/process`
5. ✅ Create paper trade: `POST /api/trades/paper`
6. ✅ Check portfolio: `GET /api/portfolio/{user_id}`
7. 🔗 Connect frontend to API via ngrok URL

---

## Support

- API Docs: http://localhost:8000/docs
- GitHub: (link to repo)
- Issues: File on GitHub

---

**Status:** ✅ Production Ready (MVP v1.0)
