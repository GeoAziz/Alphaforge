# AlphaForge

AI-powered trading intelligence platform for crypto and forex traders. Institutional-grade analytics, automated trading signals, and strategy performance verification — built for retail traders.

## Tech Stack

- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI (Python), Supabase PostgreSQL, Redis
- **AI/ML:** Google Genkit, custom signal generation
- **Deploy:** Vercel (frontend), Render/Railway (backend), Supabase (database)

## Getting Started

### Frontend

```bash
npm install
npm run dev
```

Opens at `http://localhost:9002`.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Environment Variables

Copy `.env.example` to `.env.local` and fill in:

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=
DATABASE_URL=
```

## Project Structure

```
alphaforge/
├── src/                    # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # UI components (shadcn/ui)
│   ├── hooks/             # React hooks
│   └── lib/               # Utilities, API client
├── backend/               # FastAPI backend
│   ├── main.py           # API entry point (62+ endpoints)
│   ├── services/         # Business logic (10+ services)
│   ├── data_sources/     # Market data integrations
│   └── database/         # Migration scripts
└── docs/                  # Documentation
    ├── alphaforge.md     # Product requirements
    └── archive/          # Historical docs
```

## Key Features

- **Trading Signals:** AI-generated entry/exit signals with confidence scores
- **Paper Trading:** Risk-free strategy testing with simulated execution
- **Market Analytics:** Real-time price data, correlations, technical indicators
- **Strategy Marketplace:** Browse, subscribe, and copy proven strategies
- **Portfolio Management:** Position tracking, P&L analysis, risk metrics
- **Backtesting:** Historical strategy validation with performance metrics

## API Reference

See `backend/API_INTEGRATION_GUIDE.md` for complete endpoint documentation.

Key endpoints:
- `GET /api/signals/top` — Top trading signals
- `GET /api/paper-trades` — Paper trade history
- `GET /api/portfolio/summary` — Portfolio overview
- `GET /api/analytics/correlation` — Asset correlations
- `GET /api/health` — Backend health check

## Documentation

- [Quick Start](QUICK_START.md) — Local development setup
- [Deployment Guide](DEPLOYMENT_GUIDE.md) — Production deployment
- [API Integration](backend/API_INTEGRATION_GUIDE.md) — Backend API reference
- [Frontend Integration](FRONTEND_INTEGRATION_GUIDE.md) — Frontend API integration
- [Product Requirements](docs/alphaforge.md) — Full PRD
- [System Design](docs/alphaforge_system_design.md) — Architecture overview
