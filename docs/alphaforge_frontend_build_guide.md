# AlphaForge — Frontend Build Guide

Version: 1.0
Stack: Next.js 14+ (App Router) · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion
Hosting: Vercel
Backend: Mock data layer (real API integration deferred)

---

This document is the single source of truth for building the AlphaForge frontend. It covers every page, every component, every animation, every mock data shape, and every edge case. There is no design file — this is the design file. Build exactly what is described here. If something is not described here, it does not exist yet.

---

# 1. Project Setup

## 1.1 Initialize

```bash
npx create-next-app@latest alphaforge --typescript --tailwind --eslint --app --src-dir
```

## 1.2 Install Dependencies

```bash
# UI primitives
npx shadcn@latest init

# Core shadcn components needed
npx shadcn@latest add button card dialog dropdown-menu input label select separator sheet skeleton tabs toast tooltip badge command popover scroll-area table avatar switch slider progress

# Motion
npm install framer-motion

# Charts
npm install lightweight-charts recharts

# Icons
npm install lucide-react

# Utilities
npm install clsx tailwind-merge class-variance-authority
npm install date-fns numeral
```

## 1.3 Fonts

Load via `next/font`:

```typescript
import { Inter, JetBrains_Mono } from 'next/font/google'
import localFont from 'next/font/local'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

// Inter Tight — used for hero/display stats only
const interTight = localFont({
  src: './fonts/InterTight-Variable.woff2',
  variable: '--font-display',
  display: 'swap',
})
```

If Inter Tight is not available as a Google font at build time, use Inter weight 900 with letter-spacing -0.05em as fallback for hero stats.

## 1.4 Project Structure

```
src/
├── app/
│   ├── layout.tsx                    # Root layout — fonts, providers, sidebar, noise
│   ├── page.tsx                      # Dashboard
│   ├── signals/
│   │   └── page.tsx                  # Signals feed
│   ├── market-intelligence/
│   │   └── page.tsx                  # Market analytics
│   ├── portfolio/
│   │   └── page.tsx                  # Portfolio overview
│   ├── strategies/
│   │   └── page.tsx                  # Strategy cards
│   ├── backtesting/
│   │   └── page.tsx                  # Backtesting interface
│   ├── marketplace/
│   │   └── page.tsx                  # Strategy marketplace
│   ├── analytics/
│   │   └── page.tsx                  # Performance analytics
│   ├── settings/
│   │   └── page.tsx                  # Settings page
│   └── onboarding/
│       └── page.tsx                  # Onboarding flow
│
├── components/
│   ├── layout/
│   │   ├── sidebar.tsx               # Collapsible sidebar
│   │   ├── topbar.tsx                # Top bar with search + notifications
│   │   ├── mobile-nav.tsx            # Bottom tab bar (mobile)
│   │   ├── command-palette.tsx       # ⌘K command palette
│   │   ├── scroll-progress.tsx       # Scroll-linked progress bar
│   │   └── page-wrapper.tsx          # Shared page animation wrapper
│   │
│   ├── dashboard/
│   │   ├── hero-stats.tsx            # Hero composition — win rate + supporting stats
│   │   ├── bento-grid.tsx            # Bento grid layout container
│   │   ├── market-overview.tsx       # BTC/ETH prices, volatility, funding
│   │   ├── active-signals-panel.tsx  # Compact signal cards
│   │   ├── performance-summary.tsx   # Win rate, ROI, profit factor, drawdown
│   │   ├── market-heatmap.tsx        # Volume/liquidation heatmap
│   │   └── recent-signals.tsx        # Latest signal list
│   │
│   ├── signals/
│   │   ├── signal-feed.tsx           # Real-time signal feed
│   │   ├── signal-card.tsx           # Individual signal card
│   │   ├── signal-detail-panel.tsx   # Right slide-in panel
│   │   ├── signal-filters.tsx        # Filter toolbar
│   │   └── confidence-pill.tsx       # Color-coded confidence badge
│   │
│   ├── portfolio/
│   │   ├── portfolio-overview.tsx    # Equity, PnL summary
│   │   ├── active-positions.tsx      # Open positions table
│   │   ├── trade-history.tsx         # Historical trades table
│   │   └── position-row.tsx          # Single position row with flash
│   │
│   ├── market/
│   │   ├── trend-dashboard.tsx       # Trend indicators
│   │   ├── liquidation-heatmap.tsx   # Liquidation clusters
│   │   ├── funding-rate-monitor.tsx  # Funding rates
│   │   ├── open-interest.tsx         # OI dashboard
│   │   ├── sentiment-breakdown.tsx   # Per-asset NLP sentiment (FinBERT/VADER) panel
│   │   └── onchain-dashboard.tsx     # Whale movements, exchange inflows/outflows panel
│   │
│   ├── strategies/
│   │   ├── strategy-card.tsx         # Strategy card with spotlight
│   │   └── strategy-detail.tsx       # Strategy performance detail
│   │
│   ├── backtesting/
│   │   ├── backtest-form.tsx         # Input form
│   │   ├── backtest-results.tsx      # Results display
│   │   └── equity-curve.tsx          # Animated equity curve with terminal glow
│   │
│   ├── marketplace/
│   │   ├── marketplace-grid.tsx      # Strategy marketplace grid
│   │   ├── marketplace-card.tsx      # Marketplace strategy card
│   │   ├── verification-badge.tsx    # 5-stage verification process badge
│   │   ├── paper-trade-gate.tsx      # Mandatory paper trade result before copy CTA
│   │   └── marketplace-disclaimer.tsx # Risk/past-performance disclaimer modal
│   │
│   ├── analytics/
│   │   ├── performance-charts.tsx    # Accuracy, profit factor, drawdown charts
│   │   └── timeframe-selector.tsx    # 7D / 30D / 90D / All Time toggle
│   │
│   ├── settings/
│   │   ├── exchange-connection.tsx   # API key connection flow
│   │   ├── risk-settings.tsx         # Risk preferences
│   │   ├── notification-settings.tsx # Alert preferences
│   │   ├── security-settings.tsx     # 2FA, password, active sessions
│   │   ├── audit-log-panel.tsx       # Read-only user audit trail with filters
│   │   ├── data-privacy-settings.tsx # GDPR/CCPA consent, data export, deletion
│   │   └── regulatory-settings.tsx   # Jurisdiction selector, investment disclaimers
│   │
│   ├── onboarding/
│   │   ├── onboarding-stepper.tsx    # Step progress indicator (now 6 steps)
│   │   ├── step-account.tsx          # Step 1
│   │   ├── step-exchange.tsx         # Step 2 — updated with idempotency explanation
│   │   ├── step-risk.tsx             # Step 3 — updated with regulatory disclaimer card
│   │   ├── step-notifications.tsx    # Step 4
│   │   ├── step-walkthrough.tsx      # Step 5 — updated with audit trail callout
│   │   └── step-regulatory-consent.tsx # Step 6 — GDPR/CCPA consent, cannot be skipped
│   │
│   ├── shared/
│   │   ├── animated-counter.tsx      # Count-up animation for stats
│   │   ├── price-ticker.tsx          # Price with green/red flash
│   │   ├── empty-state.tsx           # Illustrated empty state
│   │   ├── error-state.tsx           # Error with retry
│   │   ├── spotlight-card.tsx        # Reusable cursor spotlight wrapper
│   │   ├── glass-panel.tsx           # Glassmorphism wrapper
│   │   ├── gradient-border.tsx       # Animated gradient border wrapper
│   │   ├── noise-overlay.tsx         # Noise texture pseudo-element
│   │   ├── stat-card.tsx             # Metric stat card
│   │   ├── skeleton-card.tsx         # Skeleton loading card
│   │   ├── notification-toast.tsx    # Glass toast component
│   │   ├── data-quality-indicator.tsx # Feed validation status badge per ticker
│   │   ├── audit-trail.tsx           # Read-only append-only action log viewer
│   │   ├── paper-trade-badge.tsx     # Paper trading gate result badge on strategy cards
│   │   └── reputation-score.tsx      # Creator reputation panel with sub-metrics
│   │
│   └── charts/
│       ├── candlestick-chart.tsx     # TradingView Lightweight Charts wrapper
│       ├── area-chart.tsx            # Recharts area chart wrapper
│       ├── bar-chart.tsx             # Recharts bar chart wrapper
│       └── heatmap-chart.tsx         # Custom heatmap renderer
│
├── data/
│   ├── mock-signals.ts              # Mock signal data
│   ├── mock-portfolio.ts            # Mock positions and trades
│   ├── mock-market.ts               # Mock market data
│   ├── mock-strategies.ts           # Mock strategy data
│   ├── mock-analytics.ts            # Mock analytics data
│   ├── mock-notifications.ts        # Mock notifications
│   ├── mock-sentiment-detail.ts     # Per-asset NLP sentiment scores breakdown
│   ├── mock-onchain.ts              # Whale movements, exchange inflows/outflows
│   ├── mock-audit-log.ts            # Sample user action audit log entries
│   └── mock-marketplace.ts          # Expanded marketplace data (reputation, verification, paper trade)
│
├── lib/
│   ├── api.ts                       # Data layer — returns mock data now, API calls later
│   ├── utils.ts                     # cn(), formatCurrency(), formatPercent()
│   ├── constants.ts                 # App-wide constants
│   └── types.ts                     # All TypeScript interfaces
│
├── hooks/
│   ├── use-spotlight.ts             # Mouse tracking for spotlight effect
│   ├── use-animated-counter.ts      # Count-up hook
│   ├── use-scroll-progress.ts       # Scroll progress tracker
│   ├── use-mock-realtime.ts         # Simulates real-time data updates
│   ├── use-command-palette.ts       # ⌘K keyboard shortcut
│   ├── use-media-query.ts           # Responsive breakpoint hook
│   ├── use-data-quality.ts          # Polls data validation status, surfaces anomaly warnings
│   ├── use-paper-trade.ts           # Manages paper trade simulation state for a strategy
│   └── use-audit-log.ts             # Fetches and paginates user audit log entries
│
└── styles/
    └── globals.css                  # Tokens, mesh bg, noise, base styles
```

---

# 2. Design Tokens (globals.css)

This is the exact CSS that must go in `globals.css`. Do not deviate from these values.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    color-scheme: dark;

    /* Backgrounds */
    --bg: #030712;
    --surface: #0f1629;
    --elevated: #1a2342;
    --overlay: #1e2d4a;
    --inset: #080f1f;

    /* Borders */
    --border: #1e3a5f;
    --border-subtle: #132035;

    /* Brand */
    --primary: #60a5fa;
    --primary-rgb: 96, 165, 250;
    --accent: #c084fc;
    --accent-rgb: 192, 132, 252;

    /* Semantic */
    --green: #34d399;
    --red: #f87171;
    --amber: #fbbf24;

    /* Text */
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #475569;

    /* Typography scale */
    --text-xs:   clamp(0.694rem, 0.66rem + 0.17vw, 0.8rem);
    --text-sm:   clamp(0.833rem, 0.78rem + 0.27vw, 1rem);
    --text-base: clamp(1rem, 0.93rem + 0.36vw, 1.25rem);
    --text-lg:   clamp(1.2rem, 1.1rem + 0.5vw, 1.563rem);
    --text-xl:   clamp(1.44rem, 1.3rem + 0.7vw, 1.953rem);
    --text-2xl:  clamp(1.728rem, 1.54rem + 0.94vw, 2.441rem);
    --text-3xl:  clamp(2.074rem, 1.81rem + 1.32vw, 3.052rem);
    --text-hero: clamp(3rem, 2.4rem + 3vw, 6rem);

    /* Easing */
    --ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
    --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
    --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  }

  body {
    background-color: var(--bg);
    background-image:
      radial-gradient(ellipse at 20% 50%, rgba(96, 165, 250, 0.06) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 20%, rgba(192, 132, 252, 0.05) 0%, transparent 50%),
      radial-gradient(ellipse at 50% 80%, rgba(52, 211, 153, 0.04) 0%, transparent 50%);
    color: var(--text-primary);
    font-family: var(--font-inter), system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    min-height: 100dvh;
  }

  /* Noise texture — apply .noise-surface class where needed */
  .noise-surface {
    position: relative;
  }
  .noise-surface::after {
    content: '';
    position: absolute;
    inset: 0;
    background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    mix-blend-mode: overlay;
    opacity: 0.35;
    border-radius: inherit;
    z-index: 0;
  }

  /* Reduced noise for cards */
  .noise-surface--subtle::after {
    opacity: 0.25;
  }
  .noise-surface--faint::after {
    opacity: 0.2;
  }
}

/* Skeleton shimmer */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
.skeleton {
  background: linear-gradient(90deg,
    rgba(255,255,255,0.04) 0%,
    rgba(255,255,255,0.08) 50%,
    rgba(255,255,255,0.04) 100%);
  background-size: 800px 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}

/* Gradient text utility */
.gradient-text {
  background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Glassmorphism */
.glass {
  background: rgba(26, 35, 66, 0.75);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* Tabular numbers for all mono text */
.font-mono {
  font-variant-numeric: tabular-nums;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 150ms !important;
  }
}
```

## 2.1 Tailwind Config Extensions

Add these to `tailwind.config.ts`:

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        elevated: 'var(--elevated)',
        overlay: 'var(--overlay)',
        inset: 'var(--inset)',
        border: 'var(--border)',
        'border-subtle': 'var(--border-subtle)',
        primary: 'var(--primary)',
        accent: 'var(--accent)',
        green: 'var(--green)',
        red: 'var(--red)',
        amber: 'var(--amber)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
        display: ['var(--font-display)', 'var(--font-inter)', 'system-ui'],
      },
      fontSize: {
        xs: 'var(--text-xs)',
        sm: 'var(--text-sm)',
        base: 'var(--text-base)',
        lg: 'var(--text-lg)',
        xl: 'var(--text-xl)',
        '2xl': 'var(--text-2xl)',
        '3xl': 'var(--text-3xl)',
        hero: 'var(--text-hero)',
      },
      borderRadius: {
        DEFAULT: '8px',
        lg: '12px',
        xl: '16px',
      },
      transitionTimingFunction: {
        'ease-out-custom': 'var(--ease-out)',
        spring: 'var(--ease-spring)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
```

---

# 3. TypeScript Types

File: `src/lib/types.ts`

These types define every data shape in the application. The mock data layer must produce objects matching these types exactly. When the real backend is connected later, the API responses must match these types — or adapters must be written to transform them.

```typescript
// ── Signals ──

export type SignalDirection = 'LONG' | 'SHORT'
export type SignalStatus = 'active' | 'closed' | 'expired' | 'cancelled'

export interface Signal {
  id: string
  asset: string                     // e.g. "BTCUSDT"
  direction: SignalDirection
  entryPrice: number
  stopLoss: number
  takeProfit: number
  confidence: number                // 0-100
  strategy: string                  // e.g. "Momentum Breakout"
  strategyId: string
  status: SignalStatus
  riskRewardRatio: number
  createdAt: string                 // ISO 8601
  closedAt: string | null
  pnlPercent: number | null         // null if still active
  drivers: SignalDriver[]
  modelVersion: ModelVersion        // cryptographic model version at time of signal
  auditHash: string                 // SHA-256 hash of this signal's immutable record
}

export interface SignalDriver {
  label: string                     // e.g. "Momentum breakout detected"
  weight: number                    // 0-1, visual weight bar
  active: boolean                   // true = contributing factor
}

// ── Portfolio ──

export interface PortfolioSummary {
  totalEquity: number
  unrealizedPnl: number
  realizedPnl: number
  totalTrades: number
  openPositions: number
  marginUsed: number
}

export interface Position {
  id: string
  asset: string
  direction: SignalDirection
  entryPrice: number
  currentPrice: number
  quantity: number
  unrealizedPnl: number
  unrealizedPnlPercent: number
  riskExposure: number              // percentage of portfolio
  signalId: string
  openedAt: string
  tradingMode: 'spot' | 'perp'      // NEW: spot or perpetuals
  liquidationPrice?: number          // NEW: only for perps, null for spot
}

export interface Trade {
  id: string
  asset: string
  direction: SignalDirection
  entryPrice: number
  exitPrice: number
  pnl: number
  pnlPercent: number
  status: 'win' | 'loss'
  strategy: string
  signalId: string
  executedAt: string
  closedAt: string
}

// ── Market Data ──

export interface MarketTicker {
  asset: string
  price: number
  change24h: number                 // percentage
  change24hAbs: number              // absolute
  volume24h: number
  high24h: number
  low24h: number
}

export interface FundingRate {
  asset: string
  exchange: string
  rate: number                      // percentage
  nextFundingTime: string
}

export interface OpenInterest {
  asset: string
  value: number
  change24h: number                 // percentage
}

export interface LiquidationCluster {
  priceLevel: number
  volume: number
  side: 'long' | 'short'
}

export interface MarketSentiment {
  score: number                     // 0-100
  label: 'Extreme Fear' | 'Fear' | 'Neutral' | 'Greed' | 'Extreme Greed'
}

export interface SentimentSource {
  source: 'twitter' | 'reddit' | 'telegram' | 'news'
  score: number                     // 0-100
  label: 'Bearish' | 'Neutral' | 'Bullish'
  finbert: 'bearish' | 'neutral' | 'bullish'   // FinBERT classification
  vader: number                     // -1 to +1 VADER compound score
  volume: number                    // message/mention count in window
  window: '1h' | '4h' | '24h'
}

export interface MarketSentimentDetail {
  asset: string
  aggregateScore: number            // 0-100 composite
  aggregateLabel: 'Extreme Fear' | 'Fear' | 'Neutral' | 'Greed' | 'Extreme Greed'
  sources: SentimentSource[]
  trendingTopics: string[]          // top 3 organic topics
  updatedAt: string
}

// ── Strategies ──

export interface Strategy {
  id: string
  name: string
  description: string
  winRate: number
  avgRoi: number
  maxDrawdown: number
  sharpeRatio: number
  totalTrades: number
  profitFactor: number
  riskLevel: 'Low' | 'Medium' | 'High'
  isActive: boolean
}

// ── Analytics ──

export interface PerformancePoint {
  date: string
  equity: number
  drawdown: number
  cumulativePnl: number
}

export interface StrategyPerformance {
  strategyId: string
  strategyName: string
  winRate: number
  roi: number
  trades: number
  profitFactor: number
}

// ── Notifications ──

export interface Notification {
  id: string
  type: 'signal' | 'trade' | 'risk' | 'system'
  title: string
  message: string
  read: boolean
  critical: boolean
  createdAt: string
}

// ── Backtesting ──

export interface BacktestConfig {
  asset: string
  strategy: string
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d'
  startDate: string
  endDate: string
  initialCapital: number
  riskPerTrade: number              // percentage
}

export interface BacktestResult {
  winRate: number
  totalTrades: number
  roi: number
  maxDrawdown: number
  sharpeRatio: number
  sortinoRatio: number
  profitFactor: number
  equityCurve: PerformancePoint[]
}

// ── Marketplace ──

export interface ReputationScore {
  overall: number                   // 0-100
  longevity: number                 // months strategy has been live
  maxDrawdownRecord: number         // worst drawdown % ever recorded live
  communityRating: number           // 0-5 stars
  ratingCount: number
}

export type VerificationStage =
  | 'submitted'
  | 'backtest_verified'
  | 'paper_trade_gate'
  | 'compliance_review'
  | 'verified'

export interface PaperTradeResult {
  strategyId: string
  duration: number                  // days
  signalCount: number
  winRate: number
  roi: number
  maxDrawdown: number
  vsBacktestDelta: number           // win rate deviation from backtest claim
  passed: boolean
  completedAt: string
}

export interface MarketplaceStrategy {
  id: string
  name: string
  creator: string
  creatorId: string
  description: string
  winRate: number
  roi: number
  maxDrawdown: number
  subscribers: number
  riskLevel: 'Low' | 'Medium' | 'High'
  monthlyPrice: number              // 0 if profit-share model
  profitSharePercent: number | null // null if subscription model
  isVerified: boolean
  verificationStage: VerificationStage
  reputationScore: ReputationScore
  paperTradeResult: PaperTradeResult | null  // null = gate not yet complete
  sharpeRatio: number
  totalTrades: number
  tradingMode: 'spot' | 'perp'       // NEW: spot or perpetuals
  leverageTier?: number              // NEW: 3x, 5x, 10x, 20x (for perps only)
}

// ── Data Quality ──

export type DataQualityStatus = 'ok' | 'gap' | 'anomaly' | 'stale' | 'backup_feed'

export interface DataValidationStatus {
  asset: string
  exchange: string
  status: DataQualityStatus
  lastValidAt: string
  details: string | null            // human-readable description if not 'ok'
}

// ── Audit Log ──

export type AuditEventCategory =
  | 'auth'
  | 'api_key'
  | 'trading'
  | 'account'
  | 'risk_settings'
  | 'billing'

export interface AuditLogEntry {
  id: string
  userId: string
  category: AuditEventCategory
  action: string                    // e.g. "API key created", "Copy trading enabled"
  detail: string | null             // additional context
  ipAddress: string
  userAgent: string
  createdAt: string
}

// ── Model Version ──

export interface ModelVersion {
  hash: string                      // SHA-256 of model weights
  version: string                   // e.g. "v2.4.1"
  deployedAt: string
  paperTradeDuration: number        // days in paper trading gate before this deployed
  paperTradeWinRate: number         // win rate during paper trading gate
}

// ── On-Chain ──

export interface OnChainMetric {
  asset: string
  exchangeInflow: number            // USD value flowing into exchanges
  exchangeOutflow: number           // USD value flowing out of exchanges
  netFlow: number                   // negative = net withdrawal (bullish)
  whaleMovements: WhaleEvent[]
  stablecoinSupply: number          // on-chain stablecoin balance (dry powder)
  sopr: number | null               // Spent Output Profit Ratio (BTC/ETH only)
  mvrvZScore: number | null         // Market Value to Realised Value Z-Score
  updatedAt: string
}

export interface WhaleEvent {
  wallet: string                    // truncated address
  direction: 'inflow' | 'outflow'
  value: number                     // USD
  timestamp: string
}

// ── User ──

export interface UserProfile {
  id: string
  name: string
  email: string
  plan: 'free' | 'basic' | 'pro' | 'vip'
  riskTolerance: 'conservative' | 'balanced' | 'aggressive'
  connectedExchanges: ConnectedExchange[]
  onboardingComplete: boolean
}

// ── User ──

export interface UserProfile {
  id: string
  name: string
  email: string
  plan: 'free' | 'basic' | 'pro' | 'vip'
  riskTolerance: 'conservative' | 'balanced' | 'aggressive'
  connectedExchanges: ConnectedExchange[]
  onboardingComplete: boolean
  kycStatus?: KycStatus               // NEW: KYC/AML verification status
  riskScoreData?: PortfolioRiskScore  // NEW: portfolio risk calculation
}

// ── KYC / AML ──

export type KycStatus = 'not_started' | 'pending' | 'verified' | 'rejected'

export interface KycVerification {
  status: KycStatus
  verifiedName?: string
  verifiedCountry?: string
  verifiedAt?: string
  rejectionReason?: string
  appealAvailable?: boolean
}

// ── Risk Scoring ──

export interface PortfolioRiskScore {
  totalScore: number              // 0-10 scale
  positionRisk: number
  correlationRisk: number
  volatilityRisk: number
  breakdown: string               // human-readable summary
  updatedAt: string
}

// ── Paper Trading ──

export interface PaperTradeResult {
  strategyId: string
  duration: number                  // days
  signalCount: number
  winRate: number
  roi: number
  maxDrawdown: number
  sharpeRatio: number              // NEW: actual Sharpe achieved
  vsBacktestDelta: number           // win rate deviation from backtest claim
  passed: boolean
  completedAt: string
}

// ── Marketplace Pricing ──

export interface MarketplacePricing {
  subscriptionPrice?: number        // null if profit-share only
  profitSharePercent?: number       // null if subscription only
  selectedModel: 'subscription' | 'profit_share'  // user's active choice
}

// ── Proof / Audit ──

export interface SignalProof {
  signalId: string
  signal: Signal
  hypothesis: string                // locked pre-registered hypothesis
  backtestResults: BacktestResult
  paperTradeResults: PaperTradeResult
  blockchainProof?: {               // NEW: immutable proof
    txHash: string
    timestamp: string
  }
  status: 'live' | 'retired' | 'underperforming'
}

// ── Model Performance Tracking ──

export interface ModelPerformanceComparison {
  modelVersion: string
  backtestMetrics: {
    sharpe: number
    winRate: number
    maxDD: number
    profitFactor: number
  }
  liveMetrics: {
    sharpe: number
    winRate: number
    maxDD: number
    thisWeekData: true
  }
  weeklyDelta: number               // % difference (live vs backtest)
  status: 'performing' | 'underperforming' | 'new'
}

// ── Creator Verification ──

export interface CreatorVerificationStatus {
  creatorId: string
  strategies: {
    strategyId: string
    stage: VerificationStage
    stageName: string
    progress: number
    lastUpdated: string
    failureReason?: string
    appealAvailable: boolean
  }[]
}

export interface ConnectedExchange {
  exchange: 'binance' | 'bybit' | 'okx' | 'kraken'
  connected: boolean
  connectedAt: string | null
  permissions: string[]
}
```

---

# 4. Mock Data Layer

File: `src/lib/api.ts`

This is the data abstraction layer. Every component fetches data through these functions. Right now they return mock data. When the Python backend on Render is ready, replace the mock returns with `fetch()` calls. Nothing else changes.

```typescript
import { mockSignals, mockActiveSignals } from '@/data/mock-signals'
import { mockPortfolio, mockPositions, mockTrades } from '@/data/mock-portfolio'
import { mockTickers, mockFundingRates, mockOpenInterest, mockSentiment } from '@/data/mock-market'
import { mockStrategies } from '@/data/mock-strategies'
import { mockPerformance, mockStrategyPerformance } from '@/data/mock-analytics'
import { mockNotifications } from '@/data/mock-notifications'
import { mockSentimentDetail } from '@/data/mock-sentiment-detail'
import { mockOnChainMetrics } from '@/data/mock-onchain'
import { mockAuditLog } from '@/data/mock-audit-log'
import { mockMarketplaceStrategies } from '@/data/mock-marketplace'
import type * as T from './types'

// Simulate network delay (remove when connecting real API)
const delay = (ms: number) => new Promise(r => setTimeout(r, ms))

// ── Signals ──
export async function getActiveSignals(): Promise<T.Signal[]> {
  await delay(600)
  return mockActiveSignals
}

export async function getAllSignals(): Promise<T.Signal[]> {
  await delay(800)
  return mockSignals
}

export async function getSignalById(id: string): Promise<T.Signal | null> {
  await delay(400)
  return mockSignals.find(s => s.id === id) ?? null
}

// ── Portfolio ──
export async function getPortfolioSummary(): Promise<T.PortfolioSummary> {
  await delay(500)
  return mockPortfolio
}

export async function getActivePositions(): Promise<T.Position[]> {
  await delay(600)
  return mockPositions
}

export async function getTradeHistory(): Promise<T.Trade[]> {
  await delay(700)
  return mockTrades
}

// ── Market ──
export async function getMarketTickers(): Promise<T.MarketTicker[]> {
  await delay(400)
  return mockTickers
}

export async function getFundingRates(): Promise<T.FundingRate[]> {
  await delay(500)
  return mockFundingRates
}

export async function getOpenInterest(): Promise<T.OpenInterest[]> {
  await delay(500)
  return mockOpenInterest
}

export async function getMarketSentiment(): Promise<T.MarketSentiment> {
  await delay(300)
  return mockSentiment
}

// ── Strategies ──
export async function getStrategies(): Promise<T.Strategy[]> {
  await delay(600)
  return mockStrategies
}

// ── Analytics ──
export async function getPerformanceData(): Promise<T.PerformancePoint[]> {
  await delay(800)
  return mockPerformance
}

export async function getStrategyPerformance(): Promise<T.StrategyPerformance[]> {
  await delay(700)
  return mockStrategyPerformance
}

// ── Notifications ──
export async function getNotifications(): Promise<T.Notification[]> {
  await delay(400)
  return mockNotifications
}

// ── Backtesting ──
export async function runBacktest(config: T.BacktestConfig): Promise<T.BacktestResult> {
  await delay(2000) // simulate computation
  // Return hardcoded result shaped like a real one
  return {
    winRate: 67.3,
    totalTrades: 142,
    roi: 34.7,
    maxDrawdown: -12.4,
    sharpeRatio: 1.82,
    sortinoRatio: 2.14,
    profitFactor: 1.94,
    equityCurve: mockPerformance,
  }
}

// ── Sentinel: Data Quality ──
export async function getMarketDataQuality(): Promise<T.DataValidationStatus[]> {
  await delay(400)
  // Returns validation status per asset feed. 'ok' for most, one 'anomaly', one 'stale'.
  return mockTickers.map((t, i) => ({
    asset: t.asset,
    exchange: 'binance',
    status: i === 2 ? 'anomaly' : i === 5 ? 'stale' : 'ok',
    lastValidAt: new Date(Date.now() - (i === 5 ? 90000 : 2000)).toISOString(),
    details: i === 2 ? 'Price spike: 4.1 std deviations above rolling mean' : i === 5 ? 'No data received for >60s' : null,
  } as T.DataValidationStatus))
}

// ── Sentiment Breakdown ──
export async function getSentimentBreakdown(): Promise<T.MarketSentimentDetail[]> {
  await delay(600)
  return mockSentimentDetail
}

// ── On-Chain ──
export async function getOnChainMetrics(): Promise<T.OnChainMetric[]> {
  await delay(700)
  return mockOnChainMetrics
}

// ── Audit Log ──
export async function getAuditLog(page = 0, pageSize = 20): Promise<T.AuditLogEntry[]> {
  await delay(500)
  return mockAuditLog.slice(page * pageSize, page * pageSize + pageSize)
}

// ── Marketplace (expanded) ──
export async function getMarketplaceStrategies(): Promise<T.MarketplaceStrategy[]> {
  await delay(700)
  return mockMarketplaceStrategies
}

export async function getCreatorReputation(creatorId: string): Promise<T.ReputationScore | null> {
  await delay(400)
  const strategy = mockMarketplaceStrategies.find(s => s.creatorId === creatorId)
  return strategy?.reputationScore ?? null
}

export async function paperTradeStrategy(strategyId: string): Promise<T.PaperTradeResult> {
  await delay(1500) // simulate paper trade gate check
  const strategy = mockMarketplaceStrategies.find(s => s.id === strategyId)
  if (strategy?.paperTradeResult) return strategy.paperTradeResult
  // Return a mock in-progress result if no result yet
  return {
    strategyId,
    duration: 0,
    signalCount: 0,
    winRate: 0,
    roi: 0,
    maxDrawdown: 0,
    sharpeRatio: 0,
    vsBacktestDelta: 0,
    passed: false,
    completedAt: '',
  }
}

// ── KYC / AML (NEW) ──
export async function getKycStatus(): Promise<T.KycVerification> {
  await delay(400)
  return {
    status: 'verified',
    verifiedName: 'Alice Johnson',
    verifiedCountry: 'UK',
    verifiedAt: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days ago
  }
}

// ── Risk Scoring (NEW) ──
export async function calculatePortfolioRiskScore(): Promise<T.PortfolioRiskScore> {
  await delay(300)
  return {
    totalScore: 6.8,
    positionRisk: 4,
    correlationRisk: 2,
    volatilityRisk: 0.8,
    breakdown: 'Position risk: 4/10 | Correlation risk: 2/10 | Volatility risk: 0.8/10 | Total: 6.8/10 (Medium-High)',
    updatedAt: new Date().toISOString(),
  }
}

// ── Model Performance (NEW) ──
export async function getModelPerformanceComparison(modelVersion: string): Promise<T.ModelPerformanceComparison> {
  await delay(400)
  return {
    modelVersion,
    backtestMetrics: { sharpe: 1.47, winRate: 0.623, maxDD: 0.18, profitFactor: 1.8 },
    liveMetrics: { sharpe: 1.36, winRate: 0.612, maxDD: 0.21, thisWeekData: true },
    weeklyDelta: -7.5,
    status: 'performing',
  }
}

// ── Signal Proof (NEW) ──
export async function getSignalProof(signalId: string): Promise<T.SignalProof> {
  await delay(500)
  const signal = mockSignals.find(s => s.id === signalId)
  if (!signal) throw new Error('Signal not found')
  return {
    signalId,
    signal,
    hypothesis: 'If open interest rises while funding rates become negative, a short squeeze is likely.',
    backtestResults: {
      winRate: 0.623,
      totalTrades: 142,
      roi: 34.7,
      maxDrawdown: -12.4,
      sharpeRatio: 1.82,
      sortinoRatio: 2.14,
      profitFactor: 1.94,
      equityCurve: [],
    },
    paperTradeResults: {
      strategyId: signal.strategyId,
      duration: 28,
      signalCount: 18,
      winRate: 0.611,
      roi: 30.2,
      maxDrawdown: -11.8,
      sharpeRatio: 1.48,
      vsBacktestDelta: -2.4,
      passed: true,
      completedAt: new Date().toISOString(),
    },
    blockchainProof: {
      txHash: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6',
      timestamp: new Date().toISOString(),
    },
    status: signal.status === 'active' ? 'live' : 'retired',
  }
}

// ── Creator Verification (NEW) ──
export async function getCreatorVerificationStatus(creatorId: string): Promise<T.CreatorVerificationStatus> {
  await delay(400)
  return {
    creatorId,
    strategies: [
      {
        strategyId: 'strat-001',
        stage: 'verified',
        stageName: 'Verified',
        progress: 100,
        lastUpdated: new Date().toISOString(),
        appealAvailable: false,
      },
      {
        strategyId: 'strat-002',
        stage: 'paper_trade_gate',
        stageName: 'Paper Trade Gate',
        progress: 65,
        lastUpdated: new Date().toISOString(),
        appealAvailable: false,
      },
    ],
  }
}
```

## 4.1 Mock Data Files

Each file in `src/data/` exports realistic arrays and objects matching the types. Here are the specifications for what the data must contain. The actual values should look plausible — not random garbage.

### mock-signals.ts

Generate 20-30 signals. Mix of:
- 60% active, 20% closed (win), 15% closed (loss), 5% expired
- Assets: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, AVAXUSDT, DOGEUSDT, LINKUSDT
- Confidence range: 55-95
- Strategies: "Momentum Breakout", "Mean Reversion", "Volatility Expansion", "Order Flow", "Trend Following"
- Entry prices should be realistic for the asset (BTC ~60000-70000, ETH ~3000-4000, SOL ~100-200, etc.)
- Stop loss: 1.5-3% below entry for longs, above for shorts
- Take profit: 2-5% above entry for longs, below for shorts
- Each signal must have 3-5 drivers with realistic labels and weights
- Timestamps: spread across the last 7 days, with active signals in the last 4 hours

Export both `mockSignals` (all) and `mockActiveSignals` (status === 'active' only).

### mock-portfolio.ts

Portfolio summary:
- totalEquity: 127,450.00
- unrealizedPnl: +4,230.50
- realizedPnl: +18,670.25
- totalTrades: 342
- openPositions: 5
- marginUsed: 42,300.00

Generate 5 open positions and 30 historical trades. Trades should have a ~65% win rate consistent with signal performance claims.

### mock-market.ts

Market tickers for: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, AVAXUSDT, DOGEUSDT, LINKUSDT.
Use realistic prices. Mix of positive and negative 24h changes.

8 funding rates across Binance and Bybit. Some normal (0.01%), some elevated (0.05%+), one negative.

Open interest for top 6 assets. Mix of rising and falling.

Market sentiment: { score: 62, label: 'Greed' }.

### mock-strategies.ts

Generate 5 strategies:
1. Momentum Breakout — winRate: 68.3, avgRoi: 4.2, sharpe: 1.92, risk: Medium
2. Mean Reversion — winRate: 72.1, avgRoi: 2.8, sharpe: 2.1, risk: Low
3. Volatility Expansion — winRate: 58.7, avgRoi: 6.1, sharpe: 1.54, risk: High
4. Order Flow — winRate: 65.4, avgRoi: 3.5, sharpe: 1.78, risk: Medium
5. Trend Following — winRate: 61.2, avgRoi: 5.3, sharpe: 1.65, risk: Medium

### mock-analytics.ts

Generate 90 days (3 months) of daily performance points. Equity curve should trend upward overall with realistic drawdowns (2-3 pullbacks of 5-12%). Starting equity: 100,000.

Strategy performance: one entry per strategy with metrics matching the strategy data.

### mock-notifications.ts

Generate 15 notifications. Mix of:
- signal notifications (new BTC LONG signal, etc.)
- trade notifications (trade executed, position closed)
- risk alerts (portfolio exposure high, drawdown warning)
- system notifications (exchange connected, model retrained)

2-3 should be unread. 1 should be critical (risk alert — `critical: true`).

---

### mock-sentiment-detail.ts

Generate `MarketSentimentDetail` objects for 5 assets: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT.

Each must include:
- `aggregateScore` and `aggregateLabel` that is internally consistent (e.g., score 72 = 'Greed')
- 4 `SentimentSource` entries per asset: twitter, reddit, telegram, news
- Each source has a plausible `finbert` label, `vader` score, and `volume` count
- Twitter typically highest volume, Telegram often highest sentiment variance
- `trendingTopics`: 3 organic topic strings per asset (e.g., "ETF approval", "whale accumulation", "support level held")
- `updatedAt`: within the last 5 minutes

Export as `mockSentimentDetail: MarketSentimentDetail[]`.

---

### mock-onchain.ts

Generate `OnChainMetric` objects for BTC and ETH only (on-chain data meaningful at this resolution).

For BTC:
- `exchangeInflow`: ~250M USD (moderate inflows, neutral signal)
- `exchangeOutflow`: ~320M USD (outflows > inflows — accumulation signal)
- `netFlow`: -70M (negative = net withdrawal = bullish)
- 3 whale events: mix of inflows and outflows, realistic wallet addresses (truncated), values >1M USD
- `stablecoinSupply`: ~18B
- `sopr`: 1.04 (holders in slight profit, not yet distribution zone)
- `mvrvZScore`: 1.2 (moderate, not overheated)

For ETH:
- Similar structure. Slightly different values.
- `mvrvZScore`: 0.8 (undervalued relative to historical)

`updatedAt` within the last 1 hour.

Export as `mockOnChainMetrics: OnChainMetric[]`.

---

### mock-audit-log.ts

Generate 40 `AuditLogEntry` objects spread across the last 30 days.

Event distribution:
- 10 `auth` events (logins, one failed attempt, one 2FA verification)
- 8 `api_key` events (2 creates, 1 rotation, key used from new IP alert)
- 12 `trading` events (copy trading enabled/disabled, signal subscriptions activated)
- 6 `risk_settings` events (max risk per trade changed, exposure limit updated)
- 4 `billing` events (plan upgraded, payment processed)

Each entry should have a plausible `ipAddress` (two different IPs — desktop and mobile sessions), a realistic `userAgent`, and a logical `action` string.

Sort descending by `createdAt` (newest first).

Export as `mockAuditLog: AuditLogEntry[]`.

---

### mock-marketplace.ts

Generate 8 `MarketplaceStrategy` objects.

Distribution:
- 3 fully `verified` strategies (all 5 verification stages passed, `paperTradeResult.passed: true`)
- 2 at `paper_trade_gate` stage (gate in progress, `paperTradeResult: null`)
- 1 at `backtest_verified` stage
- 1 at `compliance_review` stage
- 1 at `submitted` stage

Verified strategies should have:
- `reputationScore.overall` between 75-92
- `reputationScore.longevity` at least 6 months
- `paperTradeResult.passed: true` with `vsBacktestDelta` within ±4%

Pricing mix:
- 4 subscription-only strategies (`profitSharePercent: null`, `monthlyPrice`: $29–$149)
- 2 profit-share only (`monthlyPrice: 0`, `profitSharePercent`: 20–30)
- 2 hybrid (both `monthlyPrice` > 0 and `profitSharePercent` > 0 — user chooses)

Export as `mockMarketplaceStrategies: MarketplaceStrategy[]`.

---

# 5. Hooks

## 5.1 Data Simulation Hook

To make the prototype feel alive, simulate real-time updates. This hook randomly updates prices and signals on an interval.

File: `src/hooks/use-mock-realtime.ts`

Behavior:
- Every 3-5 seconds, randomly pick 2-3 market tickers and nudge their prices by -0.5% to +0.5%.
- Every 30-60 seconds, generate a "new" signal (move one from the mock pool to appear as new).
- Every 5 seconds, nudge currentPrice on open positions by a small amount and recalculate unrealizedPnl.
- Use `useState` + `useEffect` with `setInterval`. Cleanup on unmount.

This creates the illusion of a live platform without any backend. It is good enough for a demo. Keep the update logic simple — the goal is visual movement, not financial accuracy.

## 5.2 Data Quality Hook

File: `src/hooks/use-data-quality.ts`

Polls `getMarketDataQuality()` at a configurable interval (default: 30 seconds) and returns the current `DataValidationStatus[]` array plus a derived `degradedCount` number.

```typescript
// Return shape
{
  statuses: DataValidationStatus[]
  degradedCount: number             // count of statuses that are not 'ok'
  isLoading: boolean
  lastChecked: Date | null
}
```

Components consuming this hook:
- Market Overview bento cell (dashboard) — shows indicator per ticker
- Data Quality Monitor panel (Market Intelligence) — shows full table
- Market Data Service status badge in the header (future)

Behavior:
- Initial fetch on mount
- Refetch every 30 seconds
- If `degradedCount > 0`, the hook exposes `hasIssues: true` for quick conditional rendering
- Uses `useEffect` cleanup to clear interval on unmount

## 5.3 Paper Trade Hook

File: `src/hooks/use-paper-trade.ts`

Manages the paper trading gate result state for a strategy in the marketplace.

```typescript
// State shape per strategyId
{
  result: PaperTradeResult | null
  isLoading: boolean
  isComplete: boolean
  hasPassed: boolean
  initiate: () => void               // calls paperTradeStrategy() and shows loading state
}
```

Usage: consumed by `marketplace-card.tsx` and `paper-trade-gate.tsx` to drive the CTA button logic.

When `initiate()` is called:
1. Sets `isLoading: true`
2. Calls `paperTradeStrategy(strategyId)` from api.ts
3. On resolve: sets `result`, `isComplete: true`, `hasPassed: result.passed`
4. On error: sets an error state and shows an error toast

## 5.4 Audit Log Hook

File: `src/hooks/use-audit-log.ts`

Fetches and paginates audit log entries from `getAuditLog()`.

```typescript
// Return shape
{
  entries: AuditLogEntry[]
  isLoading: boolean
  page: number
  hasMore: boolean
  loadMore: () => void              // increments page and appends results
  filter: AuditEventCategory | 'all'
  setFilter: (f: AuditEventCategory | 'all') => void
}
```

When `setFilter` changes, page resets to 0 and entries are refetched.
`loadMore` appends the next page to `entries` without replacing (infinite scroll pattern).
Used exclusively by `audit-log-panel.tsx` in settings.

---

# 6. Root Layout

File: `src/app/layout.tsx`

The root layout renders:
1. Font class names on `<html>`
2. The sidebar (always rendered, collapsible)
3. The top bar (always rendered)
4. The main content area (children)
5. The command palette (always rendered, hidden until ⌘K)
6. The toast provider
7. The noise overlay on body

Layout structure:

```
<html class={fonts}>
  <body class="noise-surface">
    <div class="flex h-dvh">
      <Sidebar />
      <div class="flex-1 flex flex-col overflow-hidden">
        <Topbar />
        <main class="flex-1 overflow-y-auto">
          <PageWrapper>{children}</PageWrapper>
        </main>
      </div>
    </div>
    <CommandPalette />
    <Toaster />
  </body>
</html>
```

---

# 7. Component Specifications

## 7.1 Sidebar

Width: 260px expanded, 64px collapsed.
Background: `var(--surface)`.
Border: `1px solid var(--border-subtle)` on the right edge.
Position: fixed height, does not scroll with content.

Contents (top to bottom):
1. Logo mark + "AlphaForge" text (text hidden when collapsed)
2. Navigation items each with: icon (lucide-react), label, active indicator
3. Divider
4. "Settings" at the bottom

Navigation items:
- Dashboard (LayoutDashboard icon)
- Signals (Zap icon)
- Market Intelligence (BarChart3 icon)
- Portfolio (Wallet icon)
- Strategies (Target icon)
- Backtesting (FlaskConical icon)
- Marketplace (Store icon)
- Analytics (TrendingUp icon)

Active state: `var(--primary)` text + left border accent (2px).
Hover state: `var(--elevated)` background.
Collapse trigger: button at bottom of sidebar (ChevronLeft/ChevronRight icon).
Auto-collapse: at viewport < 1280px.
Transition: width 280ms ease-out. Labels fade independently at 150ms.
Collapsed tooltips: show label on hover using shadcn Tooltip.

## 7.2 Top Bar

Height: 56px.
Background: `var(--surface)` with `border-bottom: 1px solid var(--border-subtle)`.

Contents (left to right):
1. Page title (current route name, weight 700, size lg)
2. Spacer
3. Search trigger (magnifying glass icon + "⌘K" badge — opens command palette)
4. Notification bell icon with unread count badge
5. User avatar dropdown (placeholder avatar)

Notification badge: small red dot or count pill when unread notifications exist.
Clicking bell opens notification dropdown (glass panel, max 5 recent notifications, "View all" link).

## 7.3 Command Palette

Trigger: `⌘K` (Mac) / `Ctrl+K` (Windows).
Appearance: centered overlay, glassmorphism (see glass spec in Section 2).
Width: 560px max, centered horizontally and offset 20% from top.
Border-radius: 16px.
Shadow: `0 0 0 1px rgba(96, 165, 250, 0.1), 0 24px 80px rgba(0, 0, 0, 0.6), 0 8px 24px rgba(0, 0, 0, 0.4)`.

Backdrop: `rgba(3, 7, 18, 0.7)` with blur.
Entrance: scale 0.96 → 1 + opacity 0 → 1, 250ms spring.
Exit: scale 1 → 0.96 + opacity 1 → 0, 180ms ease-in.
Close on: Escape, click outside.

Built on shadcn `Command` component (which uses cmdk under the hood).

Groups:
- **Navigation** — Dashboard, Signals, Market Intelligence, Portfolio, Strategies, Backtesting, Marketplace, Analytics, Settings
- **Actions** — Connect Exchange, Create Alert, Toggle Notifications
- **Recent Signals** — Show last 3 signals as searchable items

Mobile (< 768px): render as full-screen bottom sheet, slides up from bottom at 320ms spring.

## 7.4 Scroll Progress Bar

Position: fixed, top: 0, left: 0, height: 2px, full width.
Background: `linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)`.
Transform: `scaleX(var(--scroll-progress))` with transform-origin: left.
z-index: 9999.

Active on: Signals, Analytics, Portfolio (trade history), any page with vertical scroll.
Not active on: Dashboard (if content fits viewport).

Hook `useScrollProgress` listens to scroll events on the main scroll container and updates a CSS variable or state value (0 to 1).

## 7.5 Page Wrapper

Wraps every page's content with entrance animation.
Animation: opacity 0 → 1 + translateY 8px → 0, 200ms ease-out.
Use Framer Motion `<motion.div>` with `initial`, `animate`, `exit` props.

```typescript
<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
>
  {children}
</motion.div>
```

## 7.6 Mobile Navigation

Rendered only at viewport < 768px. Replaces sidebar entirely.
Position: fixed bottom. Height: ~64px + safe area inset.
Background: `var(--surface)` with top border.

Tabs:
- Dashboard (LayoutDashboard)
- Signals (Zap)
- Portfolio (Wallet)
- Alerts (Bell)
- More (Menu) — opens bottom sheet with remaining nav items

Active tab: `var(--primary)` icon color.
Respect `env(safe-area-inset-bottom)` for notched devices.

---

# 8. Shared Components

## 8.1 Spotlight Card

Reusable wrapper that adds cursor spotlight to any card.

Props:
- `children` — card content
- `variant` — `'primary'` (blue glow) | `'accent'` (purple glow)
- `className` — additional classes

Implementation:
- Track mouse position relative to card using `onMouseMove`
- Set `--mouse-x` and `--mouse-y` CSS variables on the element
- `::before` pseudo-element renders the radial gradient
- Opacity 0 by default, 1 on hover
- Transition: opacity 300ms ease-out

This component wraps signal cards, strategy cards, marketplace cards, and dashboard bento cells.

## 8.2 Animated Counter

Animates a number from 0 to its target value on mount.

Props:
- `value` — target number
- `duration` — ms (default 1200)
- `prefix` — string (e.g. "$", "+")
- `suffix` — string (e.g. "%")
- `decimals` — number of decimal places

Respects `prefers-reduced-motion` — shows final value immediately.
Use `useEffect` + `requestAnimationFrame` for smooth interpolation with ease-out curve.

## 8.3 Price Ticker

Displays a price that flashes green or red when it changes.

Props:
- `value` — current price
- `previousValue` — previous price (for comparison)

When value > previousValue: background flashes `rgba(52, 211, 153, 0.15)` for 600ms then fades.
When value < previousValue: background flashes `rgba(248, 113, 113, 0.15)` for 600ms then fades.
Font: JetBrains Mono, tabular-nums.

## 8.4 Confidence Pill (Enhanced)

Displays confidence score as a color-coded badge.

Rules:
- ≥80%: green background (`rgba(52, 211, 153, 0.15)`), green text, subtle green glow shadow
- 60-79%: amber background, amber text
- <60%: red background, red text

Font: JetBrains Mono, weight 600, tabular-nums.

**On Hover Animation** (NEW):
- Micro-animation: slight glow expansion + scale 1.05 (300ms spring)
- Shows enhanced tooltip with 4 information rows
- Pointer cursor changes to indicate interactivity

**Enhanced Model Version Tooltip** (NEW):
Hovering the confidence pill shows a shadcn Tooltip containing:
- Model version string (e.g. `v2.4.1`) + deployment date (e.g. `Deployed Mar 14, 2026`)
- Paper trading gate duration (e.g. `Gate duration: 28 days`)
- Paper trading result (e.g. `Gate win rate: 72.1%`)
- **Live performance (NEW)** — "Live performance this week: 72.3% WR (83% of baseline)" in amber text if degraded, green if healthy
- Truncated model hash (first 8 chars of SHA-256) at bottom

Tooltip uses glass treatment. Pointer cursor on hover.

**Clicking the pill** (NEW):
- Copies model hash to clipboard
- Shows toast: "Model hash copied"

## 8.5 Data Quality Indicator (NEW Component)

Purpose: Show the health status of market data feeds for each asset.

Props:
- `asset` — string (e.g. "BTC")
- `status` — DataQualityStatus ('ok' | 'gap' | 'anomaly' | 'stale' | 'backup_feed')
- `details` — string | null (explanation if status != 'ok')

Display: Colored dot badge next to asset name (5px diameter).

Status colors:
- `ok`: green dot (steady)
- `gap`: amber dot (pulsing — see animations table)
- `anomaly`: red dot (pulsing)
- `stale`: amber dot (pulsing)
- `backup_feed`: blue dot (steady)

**On Hover Popover** (NEW):
Shows detailed status information in a glass panel:
- Feed name: "Binance WebSocket" (primary or secondary)
- Status: "Last update: 2.1 seconds ago"
- If anomaly: "Price moved 4.2σ from mean. Typical: ±2σ. Backup feed active."
- If stale: "No data for 67s (threshold 60s). Switching to Polygon.io..."
- If backup_feed: "Primary offline. Backup (Polygon) active (6.2s latency)."

Tooltip note: "Data quality affects signal confidence. Lower quality = lower confidence."

## 8.6 Empty State

Props:
- `icon` — React node (SVG illustration or lucide icon)
- `message` — string
- `action` — optional { label: string, onClick: () => void }

Centered vertically in its container.
Entrance: fade in + translateY 8px → 0, 400ms ease-out, 200ms delay.
Icon: 80px height, uses `var(--primary)` or `var(--accent)` color.
Message: text-sm, `var(--text-secondary)`.
Action: standard primary button.

## 8.7 Error State

Same layout as empty state but with:
- Amber icon for recoverable, red for critical
- Retry button if applicable
- Error message in plain english — no stack traces

## 8.8 Stat Card

A single metric display card used across dashboard, analytics, and portfolio.

Props:
- `label` — string (card label, uppercase, text-xs, --text-muted)
- `value` — string or number
- `change` — optional number (percentage change, colored green/red)
- `isHero` — boolean (if true, uses gradient text + noise overlay)
- `loading` — boolean (if true, shows skeleton)

Background: `var(--surface)`.
Border: `1px solid var(--border)`.
Border-radius: 12px.
Padding: 20px 24px.

If `isHero`, add `.noise-surface--subtle` class and render value with `.gradient-text` class at weight 900.

## 8.9 Glass Panel

Wrapper that applies glassmorphism styles. Used for command palette, toasts, chart tooltips, and floating toolbars.

```
background: rgba(26, 35, 66, 0.75)
backdrop-filter: blur(20px) saturate(180%)
border: 1px solid rgba(255, 255, 255, 0.08)
border-radius: 14px
```

Props:
- `icon` — React node (SVG illustration or lucide icon)
- `message` — string
- `action` — optional { label: string, onClick: () => void }

Centered vertically in its container.
Entrance: fade in + translateY 8px → 0, 400ms ease-out, 200ms delay.
Icon: 80px height, uses `var(--primary)` or `var(--accent)` color.
Message: text-sm, `var(--text-secondary)`.
Action: standard primary button.

## 8.6 Error State

Same layout as empty state but with:
- Amber icon for recoverable, red for critical
- Retry button if applicable
- Error message in plain english — no stack traces

## 8.7 Stat Card

A single metric display card used across dashboard, analytics, and portfolio.

Props:
- `label` — string (card label, uppercase, text-xs, --text-muted)
- `value` — string or number
- `change` — optional number (percentage change, colored green/red)
- `isHero` — boolean (if true, uses gradient text + noise overlay)
- `loading` — boolean (if true, shows skeleton)

Background: `var(--surface)`.
Border: `1px solid var(--border)`.
Border-radius: 12px.
Padding: 20px 24px.

If `isHero`, add `.noise-surface--subtle` class and render value with `.gradient-text` class at weight 900.

## 8.8 Glass Panel

Wrapper that applies glassmorphism styles. Used for command palette, toasts, chart tooltips, and floating toolbars.

```
background: rgba(26, 35, 66, 0.75)
backdrop-filter: blur(20px) saturate(180%)
border: 1px solid rgba(255, 255, 255, 0.08)
border-radius: 14px
```

## 8.9 Gradient Border

Wrapper that adds the rotating conic gradient border to its child.

Props:
- `active` — boolean (only renders the border when true)
- `children`

Uses `@property --angle` with `conic-gradient` animation rotating over 4s. See the CSS from the UI/UX spec Section 9.4. Only used on signal cards with confidence ≥ 85% and featured marketplace listings.

## 8.10 Notification Toast

Uses shadcn's toast system.
Glass background (see 8.8).
Slides in from top-right at 350ms spring.
Auto-dismiss after 5 seconds.
Critical toasts (risk alerts): do not auto-dismiss, show red left border, require manual dismiss.

Signal toast content:
```
🚨 BTC LONG SIGNAL
Entry: $63,200 | Confidence: 74%
Strategy: Momentum Breakout
```

---

# 9. Page-by-Page Specifications

## 9.1 Dashboard Page

Route: `/`

This is the first thing users see. It must be the most polished page.

### Hero Section (above the fold)

The top area contains:
- **Win Rate** — the dominant stat. Font: display, weight 900, size hero. Apply `.gradient-text`. Animate from 0 to 67.3% using animated counter (1200ms, 600ms delay after mount).
- **Total Signals** — supporting stat to the right. Normal stat card style. "1,247 signals" with animated counter.
- **Profit Factor** — supporting stat. "1.94" with animated counter.
- **Average ROI** — supporting stat. "+4.2%" in green with animated counter.

Background: use the mesh gradient from body. Add hero spotlight behind win rate:
```css
radial-gradient(ellipse at 50% 50%, rgba(96, 165, 250, 0.08) 0%, transparent 60%)
```

Entrance: hero stats stagger in — win rate first (600ms delay), supporting metrics at 200ms intervals after.

### Bento Grid (below hero)

12-column grid with mixed cell sizes. Each cell is a surface card with border.

Layout:
```
Row 1: [Market Overview — 4 col] [Active Signals — 4 col] [Market Sentiment — 4 col]
Row 2: [Performance Summary — 8 col]                       [Quick Alerts — 4 col]
Row 3: [Market Heatmap — 6 col]   [Recent Signals — 6 col]
```

Each bento cell gets the spotlight effect (wrap in SpotlightCard).

#### Market Overview Cell
Shows: BTC price, ETH price, market volatility index, top funding rate.
Prices use PriceTicker component. Update via mock realtime hook.
Each asset price row includes a `DataQualityIndicator` badge (status dot) to the right of the asset name. If status is `anomaly` or `stale`, the dot pulses amber.
`useDataQuality()` hook provides status. Tooltip on badge shows feed detail.

#### Active Signals Cell
Shows: 3 most recent active signals in compact card form.
Each mini-card: asset, direction (LONG/SHORT badge), confidence pill, age.
"View all →" link to /signals.

#### Market Sentiment Cell
Shows: Fear & Greed gauge (62 — Greed).
Render as a semicircular gauge or a large colored number with label.

#### Performance Summary Cell
Shows: Win Rate, Total Trades, Profit Factor, Max Drawdown.
Each as a stat card with animated counter. Win Rate uses green color.

#### Quick Alerts Cell
Shows: 3 most recent notifications.
Each: type icon, title, relative timestamp.
"View all →" link.

#### Market Heatmap Cell
Shows: placeholder heatmap visual of asset performance.
Can be a simple colored grid showing 24h performance for top 8 assets.
Green for positive, red for negative, opacity = magnitude.

#### Recent Signals Cell
Shows: 5 most recent signals in a compact list.
Each row: asset, direction badge, confidence pill, time ago.
Click opens signal detail.

Loading state: every cell shows skeleton matching its dimensions.

## 9.2 Signals Page

Route: `/signals`

This is the core product page. The scroll progress bar is active here.

### Filter Toolbar
Horizontal bar above the feed. Compact pill-style toggles.
Filters:
- Asset: multi-select dropdown (All, BTC, ETH, SOL, etc.)
- Strategy: multi-select dropdown
- Confidence: range (All, 60+, 70+, 80+, 90+)
- Status: Active / Closed / All
- Timeframe: 1H, 4H, 1D, 1W

Active filters highlight with `var(--primary)` pill background. A "Clear all" button appears when any filter is active.

### Signal Feed
Vertical feed of signal cards, most recent first.

Each Signal Card:
- Background: `var(--surface)`, border: `var(--border)`, border-radius: 12px
- Spotlight effect (SpotlightCard wrapper)
- If confidence ≥ 85: animated gradient border
- Layout:
  ```
  [Direction badge: LONG/SHORT]  [Asset pair]  [Strategy label]  [Time ago]
  [Entry: $XX,XXX]  [SL: $XX,XXX]  [TP: $XX,XXX]  [R:R ratio]
  [Confidence pill]  [Signal age indicator]
  ```
- Direction badge: green bg for LONG, red bg for SHORT
- All prices in JetBrains Mono, tabular-nums
- Age indicator: full opacity < 5min, 90% at 5-15min, 75% + amber tag at > 15min, greyed at > 1hr

New signal animation: when a new signal appears (via mock realtime), it slides in from the top with a green border flash. 400ms spring.

Click on a signal card → opens the right detail panel.

### Signal Detail Panel
Width: 360px. Slides in from right (translateX 360px → 0 + opacity, 320ms ease-out). Pushes main content left.

Contents:
1. Asset + direction + status
2. Entry / SL / TP levels with visual price ladder or level indicators
3. Confidence score (large) + breakdown:
   - Each driver as a row: label + weight bar (visual progress bar, 0-1 width)
   - Active drivers marked with green checkmark
4. Strategy name + link to strategy detail
5. Risk/Reward ratio
6. Timestamp
7. If closed: PnL result (green/red)
8. **Model Integrity footer** (new) — collapsible section at the bottom:
   - Model version chip: `v2.4.1` with copy-to-clipboard on click
   - Signal audit hash: first 16 chars of SHA-256, monospace, copy-to-clipboard
   - Label: "Signal cryptographically logged" with a lock icon
   - Tooltip on hash: "This signal’s record is immutable and independently verifiable."
   - Style: inset panel (`var(--inset)` bg), `text-xs`, `--text-muted` for labels, `--text-secondary` for values

Close button (X) in top-right corner. Close on Escape.

**Model Integrity footer - Enhanced Details**:
   - **Blockchain proof badge** (NEW): displays `SignalProof.blockchainProof?.transactionHash` — "Tx: 0x7a3f..." (truncated) with copy button
     - Tooltip: "Proof timestamp: [ISO date] UTC. View on block explorer."
   - **View public proof link** (NEW): "View Full Proof" button in teal → links to `/proofs/{signal_id}` page (public route, no auth required)
   - **Paper trading results** (if signal is in paper trading phase): shows green badge "In Paper Trading" with stats: "28/30 days, 87.3% Sharpe"
   - **Performance comparison** (NEW): if signal has live + backtest data, show micro card:
     - "Backtest Sharpe: 1.23 | Live Sharpe: 1.15 (93%)" — color coded (green if >80%, amber if 60-80%, red if <60%)

Empty state (filtered, no results): show empty state with funnel icon + "No signals match your current filters." + "Clear Filters" button.

## 9.3 Market Intelligence Page

Route: `/market-intelligence`

Uses bento grid layout. Seven main content areas (four original + three new).

### Bento Layout

```
Row 1: [Trend Dashboard — 8 col]                   [Funding Rate Monitor — 4 col]
Row 2: [Liquidation Heatmap — 6 col]  [Open Interest Dashboard — 6 col]
Row 3: [Social Sentiment Panel — 8 col]             [Data Quality Monitor — 4 col]
Row 4: [On-Chain Metrics Panel — 12 col — full width]
```

### Trend Dashboard (dominant cell — 8 col)
Table or card grid showing trend indicators for top assets.
Per asset: MA trend (up/down/flat arrow), trend strength (1-10 bar), breakout detection (yes/no badge).
Loading: skeleton rows.

### Liquidation Heatmap (6 col)
Visual representation of liquidation clusters.
For MVP mock: use a gradient-colored bar chart showing liquidation volume at different price levels. Long liquidations in green, short in red.
Loading: skeleton block.

### Funding Rate Monitor (4 col)
Table: Asset | Exchange | Rate | Next Funding.
Extreme rates (> 0.03% or < -0.01%) highlighted in red/green.
Loading: skeleton rows.

### Open Interest Dashboard (6 col)
Per asset: OI value + 24h change. Positive changes in green, negative in red.
Optional: small sparkline per asset showing OI trend.
Loading: skeleton cards.

### Social Sentiment Panel (8 col) — NEW

Displays per-asset NLP sentiment scores from `getSentimentBreakdown()`.

Layout:
- Asset selector tabs at the top (BTC | ETH | SOL | BNB | XRP)
- Selected asset shows:
  - **Aggregate score** displayed as a large semicircular gauge (same style as dashboard sentiment cell), `aggregateLabel` below
  - **Source breakdown table**: Source icon | Sentiment label (colored chip) | FinBERT tag | VADER score (numeric) | Volume (message count)
  - **Trending topics**: 3 pill badges in `var(--elevated)` showing the `trendingTopics` for the selected asset
  - Last updated timestamp in `text-xs --text-muted`

Source row colors:
- `bullish` / `Bullish`: `var(--green)` chip
- `neutral` / `Neutral`: `var(--text-muted)` chip
- `bearish` / `Bearish`: `var(--red)` chip

Switching asset tab transitions the content with a 200ms opacity fade.
Loading: skeleton rows + skeleton gauge.

### Data Quality Monitor (4 col) — NEW

Displays `DataValidationStatus` for each active asset feed from `getMarketDataQuality()`.

Layout: compact list, one row per asset.
Per row: asset name | exchange | status badge | last valid timestamp.

Status badge colors:
- `ok`: `var(--green)` small dot
- `gap`: amber dot + label
- `anomaly`: red dot + label + detail tooltip on hover
- `stale`: amber dot + "stale" label
- `backup_feed`: blue dot + "Backup feed" label

Top of panel: "Data Quality" label + a summary chip — "All feeds healthy" (green) or "X feeds degraded" (amber) depending on statuses.

Anomaly rows pulse amber (see animation table — new entry).
Auto-refreshes every 30 seconds via `useDataQuality()` hook.
Loading: skeleton rows.

### On-Chain Metrics Panel (12 col — full width) — NEW

Displays `OnChainMetric` data from `getOnChainMetrics()` for BTC and ETH.

Layout: two side-by-side columns (BTC on left, ETH on right), each containing:

**Exchange Flow section**
- Inflow amount (red if high, neutral otherwise)
- Outflow amount (green if high)
- Net flow badge: "+$70M net outflow → Accumulation signal" or "−$40M net inflow → Distribution signal"
- Net flow colored: green for net outflow, red for net inflow

**On-Chain Ratios section** (BTC/ETH only)
- SOPR displayed as a number with contextual label:
  - > 1.05: "Holders selling at profit — watch for distribution" (amber)
  - 0.95-1.05: "Neutral" (muted)
  - < 0.95: "Holders selling at loss — potential bottom" (green)
- MVRV Z-Score with contextual label:
  - > 7: "Overheated" (red)
  - 2-7: "Growth phase" (green)
  - 0-2: "Fair value" (muted)
  - < 0: "Undervalued" (green + bold)

**Recent Whale Events** (last 3)
- Direction icon (arrow up = inflow, arrow down = outflow)
- Truncated wallet address in `font-mono`
- Value in USD
- Time ago

Refreshes every 60 seconds.
Loading: skeleton blocks.
Note at bottom of panel: "On-chain data via Glassnode API · Updated every 1 hour" in `text-xs --text-muted`.

## 9.4 Portfolio Page

Route: `/portfolio`

### Portfolio Overview (top section)
4 stat cards in a row:
- Total Equity: $127,450.00 (animated counter)
- Unrealized PnL: +$4,230.50 (green, animated counter)
- Realized PnL: +$18,670.25 (green, animated counter)
- Open Positions: 5

All money values in JetBrains Mono.

Empty state (no exchange connected): illustrated empty state with unlinked chain icon + "Connect an exchange to see your portfolio." + "Connect Exchange" button that opens settings.

### Active Positions (table)
Columns: Asset | Direction | Entry | Current | Size | PnL | PnL% | Risk
- PnL colored green/red
- Current price uses PriceTicker component (flashes on change)
- Direction: colored badge (green LONG / red SHORT)
- Risk: percentage of portfolio as a subtle progress bar

Empty state: "No open positions." + "View Signals" link.
Loading: skeleton rows.

### Trade History (below positions)
Tabbed or scrollable section.
Columns: Asset | Direction | Entry | Exit | PnL | PnL% | Strategy | Date
- Winning trades: green left border accent (3px)
- Losing trades: red left border accent (3px)
- Table row hover: background → `var(--elevated)` + spotlight glow (see trade-row CSS spec)

Filterable by: date range, strategy, asset.
The scroll progress bar is active when scrolling through trade history.

Loading: skeleton rows.
Empty state: "No trades in this date range." + "Change Range" button.

## 9.5 Strategies Page

Route: `/strategies`

Grid of strategy cards (3-column on desktop, 2 on tablet, 1 on mobile).

Each Strategy Card:
- SpotlightCard wrapper
- Background: `var(--surface)`, border: `var(--border)`
- Content:
  ```
  [Strategy name — weight 700, text-lg]
  [Description — text-sm, --text-secondary, 2 lines max]
  [Divider]
  [Win Rate: XX.X%]  [Avg ROI: +X.X%]
  [Sharpe: X.XX]     [Max DD: -X.X%]
  [Risk level badge]  [Active/Inactive status]
  ```
- Win rate uses confidence pill coloring rules
- Risk level: Low (green), Medium (amber), High (red)

Click → opens right detail panel with full performance history (similar pattern to signal detail).

Loading: 6 skeleton cards.

## 9.6 Backtesting Page

Route: `/backtesting`

Two-panel layout: form on the left (or top on mobile), results on the right (or bottom).

### Backtest Form
Fields:
- Asset: select dropdown (BTCUSDT, ETHUSDT, etc.)
- Strategy: select dropdown
- Timeframe: select (1m, 5m, 15m, 1h, 4h, 1d)
- Date Range: start date + end date pickers
- Initial Capital: number input ($)
- Risk Per Trade: slider (0.5% to 5%, step 0.5%)

"Run Backtest" button — primary CTA with gradient background.
On submit: show loading state (skeleton results + loading spinner on button) for 2 seconds (simulated), then show results.

### Backtest Results

Stat cards row:
- Win Rate: 67.3%
- Total Trades: 142
- ROI: +34.7% (green)
- Max Drawdown: -12.4% (red)
- Sharpe Ratio: 1.82
- Sortino Ratio: 2.14
- Profit Factor: 1.94

Each stat uses animated counter on mount.

### Equity Curve Chart
Below the stats. Full-width area chart.
Draws from left to right over 800ms on mount.
Color: `var(--green)` for profitable curve, `var(--red)` if final equity < initial.

**Terminal glow**: when the draw animation completes, a bright pulse fires at the rightmost point:
- 12px circle, background: `var(--green)`, box-shadow: `0 0 12px 4px rgba(52, 211, 153, 0.6)`
- Animation: scale 0.8 → 1.4 → 2.0, opacity 0.9 → 1 → 0, over 600ms ease-out
- Then stays as a subtle static dot

Empty state (before first run): "Configure a strategy and run a backtest to see results." No fancy illustration needed — just text + the form.

## 9.7 Strategy Marketplace Page

Route: `/marketplace`

Grid of marketplace strategy cards (same 3-column / 2-column / 1-column responsive grid as strategies page).

### Page Header

Above the grid:
- Title: "Strategy Marketplace"
- Subtitle: "All published strategies are backtested, audited, and paper-traded before going live."
- Filter bar: Risk level (All / Low / Medium / High) | Pricing (All / Subscription / Profit-Share) | Sort (ROI / Sharpe / Win Rate / Subscribers)

### Each Marketplace Card

- SpotlightCard wrapper
- Fully verified strategies get animated gradient border
- Content layout:
  ```
  [Strategy name — weight 700]
  [Creator name — text-xs, --text-muted] + [Verification stage badge]
  [Reputation score: stars or numeric]
  [Description — 2 lines max]
  [Divider]
  [ROI: +XX%]  [Win Rate: XX%]  [Sharpe: X.XX]  [Max DD: -XX%]
  [Risk badge]  [Subscribers count]
  [Divider]
  [Paper Trade Result badge OR "Gate in progress" indicator]
  [Pricing row: $XX/mo OR XX% profit share OR both with toggle]
  [CTA button — see logic below]
  ```

**Verification Stage Badge**

Small chip next to creator name. Values and colors:
- `submitted`: gray — "Submitted"
- `backtest_verified`: amber — "Backtest Verified"
- `paper_trade_gate`: amber — "Paper Trade Gate"
- `compliance_review`: blue — "Compliance Review"
- `verified`: green with checkmark icon — "Verified"

Tooltip on hover explains each stage in one sentence.

**Reputation Score Display**

Shown on cards for strategies that have reached at least `backtest_verified` stage.

Layout: `ReputationScore` overall out of 100 as a numeric badge + star rating for `communityRating`.
Hovering expands a small popover showing sub-metrics:
- Longevity: "Live for X months"
- Max drawdown record: "Worst: -XX%"
- Community rating: "X.X stars (N ratings)"

**Paper Trade Result Badge**

For verified strategies: show a compact summary badge:
- `paper_trade_result.passed: true`: green pill — "Gate Passed • XX.X% WR • XX days"
- Delta: "Within 2.1% of backtest" in `text-xs --text-muted` below the pill

For strategies in gate: amber pulsing pill — "Paper Trade Gate in Progress"

For strategies before gate: gray pill — "Paper Trading Not Yet Started"

**Pricing Row**

Three cases:

1. Subscription only (`profitSharePercent: null`):
   - Display: `$XX / month`

2. Profit-share only (`monthlyPrice: 0`):
   - Display: `XX% profit share • No monthly fee`

3. Hybrid (both set):
   - Display: pill toggle — "Subscription" | "Profit Share"
   - Switching the pill updates the price shown below it
   - Selected pricing model is passed to the CTA

**CTA Button Logic**

- Strategy not verified (`verificationStage` ≠ `verified`): button is disabled — label "Not Yet Verified", cursor not-allowed, tooltip explaining what stage is pending
- Strategy verified, `paperTradeResult: null`: button label "Paper Trade First" — triggers `paperTradeStrategy()` and shows a loading state
- Strategy verified, `paperTradeResult.passed: false`: button label "Gate Failed" — disabled, explanation tooltip
- Strategy verified, `paperTradeResult.passed: true`, user has not acknowledged disclaimer: button label "Subscribe" — opens disclaimer modal before proceeding
- Strategy verified, disclaimer acknowledged: button label "Subscribe" or "Copy Strategy" — navigates to subscription/copy flow

**Disclaimer Modal**

Triggered before any copy/subscribe action for verified strategies.

Cannot be dismissed by clicking outside the modal (intentional friction — see animation table).
Must be dismissed via "I Understand" CTA or Escape/close button.

Contents:
- "Past performance does not guarantee future results."
- "Trading involves significant risk of loss. Only trade with capital you can afford to lose."
- AlphaForge platform risk disclaimer (1 short paragraph)
- "This strategy was backtested and paper-traded under controlled conditions. Real market performance may differ."
- "I understand the risks" confirmation checkbox
- "I Understand — Proceed" primary button (disabled until checkbox is ticked)
- "Cancel" secondary button

Loading state for grid: 6 skeleton cards with matching dimensions.

Empty state (all filtered out): empty state component with funnel icon + "No strategies match your filters." + "Clear Filters" button.

## 9.8 Analytics Page

Route: `/analytics`

Scroll progress bar active on this page.

### Timeframe Selector
Horizontal pill toggle at the top: 7D | 30D | 90D | All Time
Active pill: `var(--primary)` background.
Switching timeframe re-filters the data (mock: just slice the array).

### Equity Curve (full-width chart)
Area chart showing portfolio equity over time.
Hover: crosshair + tooltip (glass treatment) showing date + equity value + drawdown.
Same terminal glow animation as backtesting curve on mount.

### Performance Metrics (2x2 grid of charts)
1. **Win Rate by Strategy** — horizontal bar chart. One bar per strategy.
2. **Profit Factor Trend** — line chart over time.
3. **Drawdown History** — inverted area chart (drawdown is negative, chart goes down from 0).
4. **Signal Accuracy Over Time** — line chart showing rolling 30-day accuracy.

All charts animate on mount (fade in + slight scale). Hover states show tooltips.

Loading: skeleton chart placeholders for each chart area.

## 9.9 Settings Page

Route: `/settings`

Tabs or vertical nav for sections:

### Exchange Connections
List of supported exchanges: Binance, Bybit, OKX, Kraken.
Each shows: exchange logo, name, connection status (Connected/Not Connected).
Connected: green status dot + "Connected on [date]" + Disconnect button.
Not connected: "Connect" button → opens connection modal.

#### Exchange Connection Modal
Stepped flow (3 steps):
1. Select exchange → shows exchange-specific instructions
2. Enter API Key + API Secret → input fields (inset background)
3. Confirm permissions — shows what the key can do (Read ✓, Trade ✓, Withdraw ✗ with explanation)

Success: green glow confirmation + exchange logo.
Error: amber/red message with troubleshooting steps.

For the mock prototype: simulate a successful connection after 1.5s delay on submit. Store connected state in local state or localStorage.

### Notification Preferences
Toggle switches for:
- Email alerts (on/off)
- Push notifications (on/off)
- Telegram alerts (on/off) + bot connection flow (mock: show QR placeholder + instructions, simulate connection after 2s)
- Discord alerts (on/off) + webhook URL field (validate URL format, mock: green confirmation after save)

Each channel: independent toggle.

### Risk Settings

Display of current **portfolio risk score** (NEW):
- Top of the Risk Settings tab: large stat display showing current portfolio risk (0-10 scale color-coded: 0-3 green, 4-6 amber, 7-10 red)
- Breakdown card showing: position concentration, correlation risk, volatility risk, leverage risk (for perps)
- "Recalculate" link refreshes from mock data (calls `calculatePortfolioRiskScore()`)

Risk tolerance settings:
- Radio group (Conservative / Balanced / Aggressive)
- Max risk per trade: slider (0.5% to 5%)
- Max portfolio exposure: slider (10% to 100%)
- Stop loss preference: auto (AI) / manual + input for manual SL percentage

**Perpetuals leverage limits** (NEW):
- Dropdown: select max leverage tier (1x / 5x / 10x / 20x) — defaults to 5x
- Shows liquidation buffer warning: "At 5x leverage, liquidation occurs at 20% below entry. Proceed with caution."
- Warning color changes based on tier: 5x = green, 10x = amber, 20x = red

### Security
- Change password fields
- 2FA toggle (simulate setup flow with QR code placeholder)
- Active sessions list (mock: 2 sessions — current browser + mobile)

### Audit Log (NEW tab)

A read-only, paginated view of the user's `AuditLogEntry` records from `getAuditLog()`.

Layout:
- Filter row at top: Category filter dropdown (All / Auth / API Keys / Trading / Risk Settings / Billing) + date range selector
- Table with columns: Timestamp | Category chip | Action | Detail | IP Address
- 20 entries per page, with pagination controls
- Category chips use distinct colors (auth = blue, trading = green, api_key = amber, risk_settings = purple, billing = teal)
- Rows are read-only. No actions, no delete, no edit.
- "Export CSV" button at top right (mock: downloads a blank CSV with headers — real export deferred)

Empty state: "No activity recorded yet."
Loading: skeleton rows.

### Data Privacy (NEW tab)

GDPR / CCPA consent management and data subject rights.

Sections:

**Consent Management**
- 4 toggle rows with `consent: boolean` state stored in localStorage for the prototype:
  - "Analytics & Usage Data" — help improve the platform (default: on)
  - "Marketing Communications" — emails about new features (default: off)
  - "Third-Party Analytics" — anonymised usage data sharing (default: off)
  - "Push Notifications" — signal and portfolio alerts (default: on)
- Each toggle shows when consent was last updated in `text-xs --text-muted`

**Your Data**
- "Export My Data" button — mock: shows a toast "Your data export has been requested. You will receive it by email within 24 hours."
- "Delete My Account" button — red/destructive styling → opens confirmation dialog:
  - "This action is permanent and irreversible."
  - "All your data will be deleted within 30 days per GDPR Article 17."
  - Type your email to confirm
  - "Permanently Delete Account" button (destructive) / "Cancel"
  - Mock: shows toast "Account deletion requested. You will receive a confirmation email."

**Privacy Policy link** — plaintext link to a placeholder `#` route.

### Regulatory (NEW tab)

Jurisdiction and compliance notices for the user.

Sections:

**Your Jurisdiction**
- Dropdown to select country/region (mock: 10 options — UK, USA, EU, Australia, Canada, UAE, Singapore, Nigeria, India, Other)
- Selecting a jurisdiction shows a contextual compliance notice banner below:
  - UK: "AlphaForge may require FCA registration to provide investment signals in the UK. This platform operates as a technology tool, not an investment adviser. Consult a regulated adviser before making investment decisions."
  - USA: "AlphaForge does not provide investment advice. Automated trade execution features may be subject to SEC or CFTC regulation if you are a US person. Consult a licensed investment adviser."
  - EU: "This platform is subject to GDPR. Your data rights are reflected in the Data Privacy tab."
  - All others: generic disclaimer.
- Notice uses amber `Alert` component with an info icon.

**Investment Risk Acknowledgement**
- If not yet acknowledged by the user (localStorage flag): show a prominent card with the full risk disclaimer and a "I acknowledge the risks" button.
- If already acknowledged: show green confirmation chip — "Risk acknowledged on [date]" with a "Re-read disclaimer" link.

**Disclaimer** (always visible at bottom of tab):
> "AlphaForge provides trading signals and analytics for informational purposes only. Nothing on this platform constitutes investment advice. Past performance of any strategy or signal does not guarantee future results. Trading cryptocurrency involves substantial risk of loss. Only trade with capital you can afford to lose entirely."

### Verification (NEW tab)

KYC/AML verification status and appeals management.

Sections:

**KYC Verification Status Card**:
Displays the result of `getKycStatus()`:

If `status === 'verified'`:
- Green checkmark icon + "Verified on [date]"
- Full name + country displayed
- Re-verify link (re-submits current documents, simulates 1s delay)

If `status === 'pending'`:
- Clock icon (amber) + "Verification in progress"
- "Your documents are being reviewed. This usually takes 1-2 business days."
- Shows which documents are pending (Passport, Proof of Address, etc.)
- "View submission details" link (expands to show submitted document types and timestamps)
- No trading live signals until approved (paper trading remains available)

If `status === 'rejected'`:
- Red X icon + "Verification declined"
- **Reason card** (amber alert):
  > "Your submission did not meet our verification requirements."
  > 
  > **Reason:** [taxonomy reason — e.g., "Document is expired", "Photo is blurry", "Country is restricted", "PEP list match detected"]
  > 
  > **Why this matters:** [explanation specific to the reason]
- **Next steps** (2 options):
  - [Resubmit Documents] → opens KYC flow modal (Onfido mock, 3-step: select documents → upload → confirm)
    - On successful resubmit: show "Resubmitted on [time]. Manual review required (5 business days)."
  - [Appeal Decision] → opens appeal form modal:
    - Text area: "Explain why you believe the decision was incorrect"
    - Submit button → shows "Appeal submitted on [time]. Compliance team will review within 2 weeks. You'll be notified via email."
- "View previous submission" link → shows modal with previous document details

**Marketplace Creator Verification** (if user has created a strategy):
- Card showing creator status (Unverified / Pending / Verified / Suspended)
- If Verified: shows green check + "Your strategies are live on the marketplace"
- If Pending: shows clock + "Your creator profile is under review (1-3 business days). Strategies cannot be published until approved."
- If Suspended: shows red X + reason (e.g., "Performance below minimum threshold") + appeal pathway

**Connected Exchanges**:
- Shows currently connected exchanges with trade permissions (Read + Trade)
- Revoke access buttons (simulated, local state)

**Account Activity**:
- "Last login:" timestamp
- "Last password change:" timestamp
- "Last KYC update:" timestamp (from `getKycStatus().verifiedDate`)

## 9.10 Onboarding Flow

Route: `/onboarding`

Full-screen flow. No sidebar. No top bar. Clean, focused experience.

### Progress Indicator
Top of screen: "Step X of 7" + horizontal progress bar (7 total steps including paper trading gate and regulatory consent).

### Step Transitions
Forward: current step exits left (translateX -40px, opacity 0), new step enters from right (translateX 40px → 0, opacity 1). 350ms spring.
Backward: current step exits right, new step enters from left. Same timing.

### Step 1 — Account Setup
Fields: Name, Email, Password, Confirm Password.
Skip option: small text link "Skip for now" with tooltip explaining what you'll miss.

### Step 2 — Exchange Connection
Same as the exchange connection modal from settings, but inline.
Shows Binance, Bybit, OKX, Kraken as selectable cards.
"Skip — browse in demo mode" option prominently shown.

**Idempotency explanation callout (new)**:
Small info card below the API key input fields:
> “AlphaForge assigns a unique order ID to every trade. If a connection hiccup occurs, your trade will never be placed twice.”
Style: inset panel, `text-sm`, lock icon on the left.

### Step 3 — Risk Preferences
3 selectable cards:
- **Conservative**: "Lower risk, smaller positions. Best for beginners." (Green accent)
- **Balanced**: "Moderate risk, balanced approach. Recommended." (Blue accent, pre-selected)
- **Aggressive**: "Higher risk, larger positions. For experienced traders." (Red accent)

Visual example for each showing hypothetical position sizing on a $10K portfolio.

**Regulatory disclaimer card (new)**:
Below the 3 risk cards, show an amber `Alert` component:
> “AlphaForge is a technology tool, not a regulated investment adviser. Your risk settings control position sizing only. They do not constitute financial advice. Please consult a licensed adviser before trading with real capital.”

### Step 4 — Notification Setup
Toggles for: Email, Push, Telegram, Discord.
Recommended defaults pre-selected (Email on, Push on).

### Step 5 — First Signal Walkthrough
Show a mock signal card with interactive tooltip callouts:
1. "This is the confidence score — higher means stronger signal."
2. "Entry, Stop Loss, and Take Profit — your key levels."
3. "Click any signal to see the full reasoning behind it."
4. **New callout**: Point to the Model Integrity footer on the mock signal card — "Every signal is cryptographically logged and independently verifiable. No results are ever altered."

"Next" button → advances to Step 5A.

### Step 5A — Paper Trading Gate (NEW — mandatory before live trading)

This step educates users on the 4-week paper trading requirement. No skip option.

Layout: single-focus screen, educational tone.

Heading: "Every signal starts in sandbox mode."

**Purpose card** (Glass panel with gradient border):
> "Before you trade real money, all AlphaForge signals run on paper trading for 4 weeks. This ensures every signal meets our quality standards and your risk profile is set correctly."

**Timeline visualization** (Horizontal timeline component):
- Stage 1: "Week 1-2: Initial Validation" (checkmark icon)
- Stage 2: "Week 3-4: Performance Confirmation" (checkmark icon)
- Stage 3: "Day 29: Automatic Review" (clock icon)
- Stage 4: "Day 30: Live Trading Unlocked" (unlock icon, highlighted in green)

**Mock progress tracker** (for demo purposes):
Show "Your paper trading started 3 days ago" with estimated unlock date displayed prominently in green.

**Conversion metrics display** (Stat cards):
- "100" — signals in paper
- "85%" — converted to live (success rate statistic)
- "87.3%" — current Sharpe ratio (must maintain ≥80% backtest to convert)

**Checkpoint explanation** (Amber alert):
> "Once paper trading completes, live signals will automatically begin executing on your connected exchange. You'll see execution confirmations in the dashboard. To disable live trading, visit Settings → Risk Engine."

"I understand, proceed" button → advances to Step 6.

### Step 6 — Regulatory Consent (Mandatory — cannot be skipped)

This step is mandatory. There is no skip option. The progress bar shows 7/7.

Layout: single-focus screen with no distractions. Auto-scroll to bottom on checkbox completion.

Top label: "Final step — understand your rights and risks."

**Tabs for jurisdiction-specific information** (Tab component):
- **Your Jurisdiction** (auto-selected based on KYC or IP location)
- **General Terms** (always visible)
- **Risk Acknowledgement** (always visible)

**Tab 1 — Your Jurisdiction**:
Displays jurisdiction-specific compliance notice (same content as Settings → Regulatory tab):
- UK: "AlphaForge is not FCA-regulated. Your trades are not covered by FSCS. [Learn more] link."
- EU: "AlphaForge is not ESMA-regulated. MiFID II protections do not apply. [Learn more] link."
- US: "AlphaForge is not SEC-registered. Accredited investor status not required, but trading via registered broker IS required. [Learn more] link."
- Asia: "AlphaForge is not regulated in your jurisdiction. Trading is at your own risk. Check local law before proceeding. [Learn more] link."

**Tab 2 — General Terms**:

**Data Processing & Privacy**:
- [□] **I consent to AlphaForge processing my data to provide the service** (required)
  - Tooltip: "We store your exchange API keys (encrypted), trading history, risk preferences, and KYC/AML information."
- [□] **I consent to receiving service-related emails and notifications** (required)
  - Tooltip: "Order confirmations, risk alerts, account security notices, and end-of-life signal notices."
- [□] **I consent to anonymised analytics to improve the platform** (optional)
  - Tooltip: "We analyze aggregated trading patterns to improve our models. Your data is anonymised and never sold."

**GDPR/CCPA-specific callout** (if EU or CA selected):
> "You have rights under [GDPR/CCPA]: access, correction, deletion, and portability. Visit Settings → Data Privacy to exercise these rights. Requests processed within 30 days."

**Tab 3 — Risk Acknowledgement**:

**Investment Risk Disclaimer** (Critical section, styled in red accent):
> **"CRITICAL RISK DISCLOSURE"**
> 
> Trading cryptocurrency involves substantial risk of loss. You may lose all invested capital. AlphaForge is a technology tool, not a regulated investment adviser. This platform does not provide personalized investment advice.
> 
> - All trades are based on algorithmic signals. Models can fail without warning.
> - Paper trading performance does not guarantee live trading results.
> - Exchange failures, network outages, and market flash crashes can cause unexpected losses.
> - Perpetuals trading can result in liquidation and total account loss.
> - AlphaForge assumes no liability for trading outcomes, exchange failures, or data loss.

**Required acknowledgement checkboxes**:
- [□] **I have read and understand the risk disclaimer above** (required)
  - Grayed out until user scrolls to see full disclaimer
  - Tooltip reveals full disclaimer text
- [□] **I will only trade with capital I can afford to lose** (required)
- [□] **I understand AlphaForge is not a regulated investment adviser** (required)
- [□] **I am responsible for all taxes and regulatory reporting on my trades** (required)

**Completion button**:
Button text: "I Accept All Terms — Unlock Trading" (styled as primary CTA)
Button state: disabled until all checkboxes checked
On click: Creates user.paper_trading_start_date (now), sets onboarding_complete to true, redirects to dashboard

**Post-completion pathway for KYC rejections** (conditional, only shown if previous KYC submission failed):

If `user.kycStatus === 'rejected'`:
Show collapsible alert above the tabs:
> "Your KYC submission was declined. Reason: [specific taxonomy reason]"
> 
> **Why?** [Explanation of rejection reason linked to specific document/check]
> 
> **Next steps:**
> - [Resubmit Documents] — Upload corrected documents for manual review (5 business days)
> - [Appeal Decision] — Dispute the rejection (2-week review by compliance team)
> - [Learn More] — See FAQ for common rejection reasons
> 
> Until KYC is approved, you cannot trade live signals. Paper trading remains available.

Risk disclaimer text block (not a checkbox — just read-only):
> "AlphaForge signals are generated by AI models for informational purposes only. Past performance does not guarantee future results. You are solely responsible for your trading decisions."

"Get Started" primary button:
- **Disabled** until all required checkboxes are ticked
- Clicking stores consent record in localStorage (timestamp, version) and sets `onboardingComplete: true`
- Redirects to Dashboard

Modal dismissal behavior: this step cannot be dismissed by clicking outside, pressing Escape, or using the browser back button. User must complete the checkboxes or explicitly close the app. This is intentional friction — see animation table.

### Onboarding State
Store `onboardingComplete: boolean` in localStorage.
If false, redirect to /onboarding on app load.
Dashboard shows a dismissible "Complete your setup" banner if onboarding was skipped.

---

# 10. Notification Center

Accessed via bell icon in top bar.

Click → dropdown (glass panel, max height 400px, scrollable).
Shows 10 most recent notifications.
Each notification row:
- Type icon (signal: Zap, trade: ArrowRightLeft, risk: AlertTriangle, system: Info)
- Title (weight 600)
- Message (text-sm, --text-secondary, 1-2 lines)
- Relative timestamp (text-xs, --text-muted)
- Unread: subtle blue dot on the left

Critical notifications: red left border accent.
"Mark all as read" link at top.
"View all notifications" link at bottom → could open a full page or just be a placeholder.

---

# 11. Responsive Breakpoints

| Breakpoint | Width | Behavior |
|---|---|---|
| Desktop | ≥1280px | Full sidebar + all columns |
| Laptop | 1024-1279px | Collapsed sidebar (auto) + signal detail as overlay |
| Tablet | 768-1023px | No sidebar, top nav + bottom tabs. 2-column grids. |
| Mobile | <768px | Bottom tab bar. Single column. Bottom sheets replace modals. |

### Key Mobile Adaptations

- Sidebar → hidden, replaced by bottom tab bar
- Command palette → full-screen bottom sheet, slides up
- Signal detail panel → full-screen overlay, slides up from bottom
- Bento grid → single column, all cells full-width
- Tables → horizontal scroll or card-based list view
- Charts → full-width, reduced height
- Modals → bottom sheets
- Min touch target: 44×44px
- Use `dvh` not `vh`
- Respect `env(safe-area-inset-*)` on all edge elements

---

# 12. Charts Implementation

## 12.1 Candlestick Charts (Market Intelligence, Backtesting)

Use TradingView Lightweight Charts (`lightweight-charts` npm package).

Create a reusable wrapper component:
- Props: `data` (array of { time, open, high, low, close }), `height`, `width` or responsive
- Styling: dark theme matching AlphaForge colors
  - Background: `var(--bg)` (#030712)
  - Grid lines: `var(--border-subtle)` (#132035)
  - Up candle: `var(--green)` (#34d399)
  - Down candle: `var(--red)` (#f87171)
  - Crosshair: `var(--text-muted)` (#475569)
  - Text: `var(--text-secondary)` (#94a3b8)
- Include volume bars below (same up/down coloring at 30% opacity)
- Crosshair hover shows OHLCV tooltip (glass treatment)

## 12.2 Area / Line Charts (Analytics, Portfolio, Backtesting equity)

Use Recharts.

Standard config:
- Background: transparent (card provides the surface)
- Line color: `var(--primary)` or `var(--green)` depending on context
- Area fill: same color at 10% opacity
- Grid: `var(--border-subtle)`
- Axis text: `var(--text-muted)`, JetBrains Mono
- Tooltip: glass treatment (custom tooltip component)
- Animate on mount

## 12.3 Bar Charts (Analytics, Win Rate by Strategy)

Use Recharts.
Same styling config as area charts.
Bar color: `var(--primary)` for default, `var(--green)` for positive, `var(--red)` for negative.

## 12.4 Heatmap (Dashboard, Market Intelligence)

Custom component — no library needed for a simple one.
Render a grid of colored cells.
Color scale: red (negative) → neutral → green (positive).
Opacity = magnitude relative to max value.
Each cell shows: asset name + percentage change.
On hover: tooltip with exact value.

---

# 13. Animation Specifications Summary

Every animation in one table. Build these exactly.

| Element | Trigger | Animation | Duration | Easing |
|---|---|---|---|---|
| Page content | Route change | Fade in + translateY(8px→0) | 200ms | ease-out |
| Hero stats | Page mount | Staggered counter (0→value) | 1200ms per stat, 200ms stagger | ease-out |
| Stat card mount | Page mount | Counter from 0 | 1200ms | ease-out |
| Bento cell | Page mount | Fade in + scale(0.97→1), staggered | 300ms, 50ms stagger | spring |
| New signal | Arrives (mock timer) | Slide from top + green border flash | 400ms | spring |
| Price tick up | Value increases | Cell bg flashes green → fades | 600ms | ease-out |
| Price tick down | Value decreases | Cell bg flashes red → fades | 600ms | ease-out |
| Signal card click → expand | User click | Height expand + body fade | 350ms | spring |
| Detail panel open | Signal click | TranslateX(360→0) + opacity | 320ms | ease-out |
| Detail panel close | Close/Escape | TranslateX(0→360) + opacity | 250ms | ease-in |
| Sidebar expand | Toggle | Width 64→260 + label fade | 280ms | ease-out |
| Sidebar collapse | Toggle | Width 260→64 + label fade | 280ms | ease-out |
| Command palette open | ⌘K | Scale(0.96→1) + opacity | 250ms | spring |
| Command palette close | Escape | Scale(1→0.96) + opacity | 180ms | ease-in |
| Modal open | User action | Scale(0.96→1) + opacity | 250ms | spring |
| Button press | Click | Scale(1→0.97→1) | 120ms | ease-out |
| Toast appear | Notification | Slide from top-right | 350ms | spring |
| Toast dismiss | Auto/manual | Fade out | 200ms | ease-out |
| Equity curve draw | Chart mount | Stroke draws left to right | 800ms | ease-out |
| Terminal glow | Curve draw complete | Scale pulse + fade | 600ms | ease-out |
| Table row hover | Mouse enter | BG color + spotlight | 150ms | ease-out |
| Onboarding step forward | Next | Exit left + enter from right | 350ms | spring |
| Onboarding step back | Back | Exit right + enter from left | 350ms | spring |
| Skeleton shimmer | Loading | Gradient slide | 1500ms | linear, infinite |
| Gradient border rotate | Continuous | Conic gradient rotation | 4000ms | linear, infinite |
| Empty state entrance | Mount | Fade + translateY(8→0) | 400ms, 200ms delay | ease-out |
| Mobile command palette | ⌘K on mobile | Bottom sheet slides up | 320ms | spring |
| Scroll progress bar | Scroll | scaleX tracks scroll position | Real-time | — |
| Spotlight glow | Mouse move | Follows cursor on hover | 300ms opacity transition | ease-out |
| Data quality flag (anomaly/stale) | Status = anomaly or stale | Amber dot pulsing repeat | 2000ms | ease-in-out, infinite |
| Paper trade result reveal | Simulation complete | Stat cards counter sequence (same as backtest results) | 1200ms, 200ms stagger | ease-out |
| Reputation score bars | Card mount | Staggered horizontal bar fill from 0% to value | 800ms, 100ms stagger | spring |
| Audit log new entry | New action logged | Slide in from top (same as notification toast) | 350ms | spring |
| Regulatory consent modal | First visit to Step 6 | Cannot be dismissed by clicking outside — background overlay does NOT close | — | intentional friction |

---

# 14. Accessibility Requirements

These are not optional. Build them from the start or they never get added.

1. **Reduced motion**: `prefers-reduced-motion: reduce` — all animations collapse to opacity fades at 150ms max. Counters show final value immediately.

2. **Keyboard navigation**: all interactive elements reachable via Tab. Command palette via ⌘K. Escape closes modals/panels/palette. Enter selects.

3. **Focus indicators**: visible focus ring on all interactive elements. Use `ring-2 ring-primary ring-offset-2 ring-offset-bg` pattern.

4. **ARIA**: 
   - Signal cards: `role="article"`, descriptive `aria-label`
   - Confidence pill: `aria-label="Confidence 74 percent"`
   - Live price tickers: `aria-live="polite"` on the price container
   - Navigation: `role="navigation"`, `aria-current="page"` on active link
   - Command palette: `role="dialog"`, `aria-modal="true"`
   - Toast notifications: `role="alert"`

5. **Color contrast**: all text on `var(--surface)` or `var(--bg)` must pass WCAG AA. The token values in Section 2 are designed to meet this — do not lighten muted text further.

6. **Minimum font size**: 14px on all viewports. No exceptions.

7. **Touch targets**: 44×44px minimum on all interactive elements on mobile.

---

# 15. Performance Requirements

1. **First Contentful Paint**: < 1.5s on Vercel
2. **Largest Contentful Paint**: < 2.5s
3. **Bundle size**: monitor with `next/bundle-analyzer`. Keep initial JS under 200KB.
4. **Images**: use `next/image` for all static images. SVG for icons and illustrations.
5. **Fonts**: preload Inter and JetBrains Mono. Use `display: swap`.
6. **Code splitting**: each page is automatically code-split by Next.js App Router. Lazy load chart components with `next/dynamic` + loading skeleton.
7. **Skeleton screens**: every data panel shows a skeleton before data loads. No blank states, no spinners.

---

# 16. What to Skip

These features exist in the full product vision but are NOT built in the frontend prototype. Do not waste time on them.

- Real authentication (use mock user state / localStorage)
- Real exchange API connections (simulate with delay + local state)
- Real payment/billing flows (show the UI, wire nothing)
- WebSocket connections to any backend
- Real ML model inference
- Real trade execution
- Data persistence (localStorage is fine for demo state)
- PDF export / report generation
- Admin panel
- Multi-language support
- Real-time collaboration features
- Push notification registration

**Note on Telegram/Discord**: Do NOT skip the Telegram and Discord notification UI. Both channels are Phase 1 MVP features and must be demoed. Build the full toggle UI and a mock connection flow:
- Telegram: show QR code placeholder + "Scan with Telegram" instruction, simulate "Bot Connected" after 2 seconds with a green confirmation state.
- Discord: show webhook URL input field, validate URL format, simulate "Webhook Verified" after 1.5 seconds save delay.

Skip only the actual webhook/bot API calls — never the UI.

---

# 17. What to Build Well

These are the things that make the prototype look and feel like a real product:

1. **The cursor spotlight effect** — on every card it's specified for. This single interaction makes the UI feel premium.
2. **Animated counters on stat cards** — counting up from zero on mount sells the "live data" illusion.
3. **Price ticker flashes** — green/red flash on value change makes the portfolio feel real-time.
4. **Skeleton loading states** — on every panel, matching the content dimensions. No blank screens.
5. **The equity curve terminal glow** — small detail, huge impact.
6. **Signal card confidence treatment** — color-coded pills, animated gradient borders on ≥85% signals.
7. **Smooth page transitions** — the 200ms fade + translate on route changes.
8. **The command palette** — ⌘K is the fastest way to show this is a power-user tool.
9. **Empty states** — for every panel. They prove you've thought about every scenario.
10. **The bento grid on the dashboard** — asymmetric cells with mixed sizes, not a boring uniform grid.
11. **Mock real-time updates** — ticking prices and arriving signals sell the demo.
12. **The noise texture** — subtle but it prevents the flat screen look.
13. **Glassmorphism on overlays** — command palette, toasts, tooltips. Consistent glass treatment.
14. **Responsive mobile layout** — bottom tabs, bottom sheets, proper touch targets.

---

# 18. Build Order

This is the recommended order. Each step produces a demoable increment.

1. **Project setup** — Next.js, Tailwind, shadcn, fonts, globals.css tokens, layout.tsx
2. **Shell** — Sidebar + top bar + mobile nav + page wrapper with transitions
3. **Shared components** — SpotlightCard, AnimatedCounter, PriceTicker, ConfidencePill, StatCard, EmptyState, Skeleton, GlassPanel, DataQualityIndicator, PaperTradeBadge, ReputationScore
4. **Mock data** — all files in src/data/ including mock-sentiment-detail, mock-onchain, mock-audit-log, mock-marketplace
5. **Data layer** — api.ts functions returning mock data (all functions including new sentiment, on-chain, audit, marketplace, data-quality)
6. **Dashboard** — hero composition + bento grid + all cells (include DataQualityIndicator on Market Overview cell)
7. **Signals page** — filter bar + signal feed + signal cards + detail panel (including Model Integrity footer)
8. **Portfolio page** — overview stats + positions table + trade history
9. **Market Intelligence** — bento grid with trend, liquidation, funding, OI panels + Social Sentiment panel + On-Chain Metrics panel + Data Quality Monitor
10. **Strategies page** — strategy cards + detail panel
11. **Analytics page** — timeframe selector + equity curve + performance charts
12. **Backtesting page** — form + results + equity curve with terminal glow
13. **Settings page** — exchange connection + notifications (Telegram/Discord mock flows) + risk + security + Audit Log tab + Data Privacy tab + Regulatory tab
14. **Command palette** — ⌘K with all groups and search
15. **Notification system** — bell dropdown + toasts
16. **Onboarding flow** — all 5 content steps with transitions + Step 6 Regulatory Consent (mandatory, non-dismissible)
17. **Marketplace page** — full grid with verification badges, paper trade results, reputation scores, pricing toggle, disclaimer modal, CTA logic
18. **Mock realtime hook** — wire up live-feeling price/signal updates + useDataQuality polling
19. **Mobile polish** — test every page on mobile, fix touch targets, bottom sheets
20. **Performance audit** — bundle size, lighthouse, skeleton coverage, reduced motion

---

# 19. Deployment

Deploy to Vercel. Connect the GitHub repo. Vercel auto-deploys on push to main.

Environment variables (set in Vercel dashboard for future API integration):
```
NEXT_PUBLIC_API_URL=         # empty for now, will point to Render backend later
NEXT_PUBLIC_APP_NAME=AlphaForge
```

Custom domain: configure when ready.

Preview deployments: Vercel gives a unique URL per branch/PR — use these for team review.

---

# 20. Backend Integration Plan (Future)

When the Python FastAPI backend is deployed on Render:

1. Set `NEXT_PUBLIC_API_URL` in Vercel to the Render service URL (e.g. `https://alphaforge-api.onrender.com`)
2. Update `src/lib/api.ts` — replace mock returns with `fetch()` calls:
   ```typescript
   export async function getActiveSignals(): Promise<Signal[]> {
     const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/signals?status=active`)
     if (!res.ok) throw new Error('Failed to fetch signals')
     return res.json()
   }
   ```
3. Add error handling + retry logic in a shared fetch wrapper
4. Replace `use-mock-realtime` hook with a WebSocket connection to the backend
5. Replace localStorage auth with Firebase Auth + token passing to the API

The component layer does not change. The data layer is the only thing that gets rewritten. This is why the abstraction exists.

---

End of document. Build this.
