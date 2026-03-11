# AlphaForge — AI Trading Intelligence Platform
## Product Requirements Document (PRD)

Version: 2.0

---

# 1. Product Overview

AlphaForge is an AI-powered trading intelligence platform designed to deliver:

- AI-generated trading signals
- market analytics
- automated trade execution
- strategy performance verification
- portfolio risk management

The platform targets **crypto and forex traders** who want institutional-grade analytics and automated trading tools without the complexity or cost of professional hedge fund systems.

AlphaForge aims to become:

> **"The Bloomberg Terminal for Retail Traders."**

The system combines:

- AI trading signals
- automated copy trading
- transparent signal history
- institutional-level analytics
- strategy marketplaces

---

# 2. Product Vision

Build the **most trusted AI trading platform for retail traders**.

AlphaForge will provide three key pillars:

### Signals
High-probability AI-generated trading signals.

### Automation
Copy trading and automated execution through exchange APIs.

### Intelligence
Institution-level analytics normally reserved for hedge funds.

### Transparency
Every signal and trade result is fully visible and verifiable.

---

# 3. Product Goals

## Business Goals

### Year 1

Users: 10,000  
ARR: $1M

### Year 3

Users: 100,000  
ARR: $10M+

---

## Product Goals

Deliver:

- AI signals with measurable edge
- transparent performance metrics
- automated trade execution
- institutional analytics
- risk-managed strategies

---

# 4. Target Users

## Beginner Traders

Needs:

- simple signals
- entry and exit guidance
- risk protection

Pain Points:

- confusing markets
- analysis paralysis
- fear of losing money

---

## Intermediate Traders

Needs:

- confirmation signals
- market analytics
- strategy insights

Pain Points:

- conflicting indicators
- market noise
- inconsistent strategy performance

---

## Advanced Traders

Needs:

- API access
- customizable strategies
- backtesting engines
- deep analytics

Pain Points:

- expensive institutional platforms
- fragmented data tools

---

# 5. Core Product Features

## 5.1 AI Trading Signals

AI models generate signals from real-time market data.

Signal format example:

Asset: BTCUSDT  
Type: LONG  
Entry: 63,200  
Stop Loss: 62,100  
Take Profit: 65,200  

Confidence: 74%  
Strategy: Momentum Breakout  
Risk Level: Medium  

---

## 5.2 Signal Explainability (Trust Feature)

Every signal includes reasoning behind the prediction.

Example:

BTC LONG SIGNAL

Confidence: 72%

Signal Drivers:

✔ Momentum breakout detected  
✔ Rising open interest  
✔ Funding rates turning negative  
✔ RSI divergence detected  

This increases transparency and builds user trust.

---

## 5.3 Signal Performance Tracking

All signals are recorded.

Metrics include:

- total trades
- win rate
- average ROI
- max drawdown
- Sharpe ratio
- profit factor
- strategy breakdown

Users can verify complete signal history.

---

## 5.4 Copy Trading Automation

Users connect exchange accounts through secure APIs.

Supported exchanges:

- Binance
- Bybit
- OKX
- Kraken

Execution flow:

User connects exchange API  
↓  
AI generates signal  
↓  
Risk engine calculates position size  
↓  
Execution engine places trade  
↓  
Portfolio updated  
↓  
Performance tracked

---

## 5.5 Market Intelligence Dashboard

Advanced analytics include:

- market trend indicators
- liquidation heatmaps
- volatility metrics
- funding rates
- open interest analysis
- order book imbalance

---

## 5.6 Strategy Backtesting Engine

Users can test strategies using historical market data.

Inputs:

- indicators
- assets
- timeframes
- risk parameters

Outputs:

- win rate
- ROI
- drawdown
- Sharpe ratio
- Sortino ratio

---

## 5.7 Risk Management Tools

Built-in trading safety tools:

- position sizing calculator
- stop loss optimization
- portfolio risk scoring
- max exposure limits
- volatility-adjusted risk

---

## 5.8 Strategy Marketplace (Growth Feature)

Traders can publish strategies.

Other users can copy them.

Example leaderboard:

Top Strategies

Momentum Alpha  
ROI: +124%

Volatility Hunter  
ROI: +78%

Mean Reversion Pro  
ROI: +65%

Strategy creators earn revenue share.

This creates network effects.

---

## 5.9 Notifications System

Signals delivered through:

- Web dashboard
- mobile push notifications
- Telegram bot
- Discord alerts
- email alerts

Example:

🚨 BTC LONG SIGNAL

Entry: 63,200  
SL: 62,100  
TP: 65,000  

Confidence: 72%  
Strategy: Momentum Breakout

---

# 6. User Stories

Receive Signals

As a trader  
I want AI-generated signals  
So I can trade quickly.

Verify Performance

As a trader  
I want to see signal history  
So I can trust the system.

Automated Trading

As a user  
I want trades executed automatically  
So I never miss opportunities.

Strategy Testing

As an advanced trader  
I want backtesting tools  
So I can validate strategies.

---

# 7. Functional Requirements

## Market Data Collection

System collects:

- price data
- volume
- order book depth
- funding rates
- open interest
- liquidation data

Update frequency:

1 second to 1 minute.

---

## Signal Generation

System must:

- process engineered features
- run ML predictions
- generate signals
- assign confidence scores

Latency target:

< 2 seconds

---

## Trade Execution

Execution engine must:

- place trades via exchange APIs
- manage rate limits
- retry failed orders
- track order status
- record execution results

---

## Portfolio Accounting Engine

Tracks:

- user balances
- open positions
- unrealized PnL
- realized PnL
- portfolio exposure
- risk allocation

---

# 8. Non-Functional Requirements

## Performance

Signal latency: <2 seconds.

## Scalability

Support:

100,000+ concurrent users.

## Reliability

Target uptime:

99.9%.

## Security

- encrypted API keys
- secure key vault
- 2FA authentication
- role-based access control

---

# 9. System Architecture

High-level architecture:

Market Data Collectors  
↓  
Streaming Pipeline  
↓  
Feature Engineering  
↓  
AI Signal Engine  
↓  
Risk Engine  
↓  
Execution Engine  
↓  
API Gateway  
↓  
Frontend Applications

---

# 10. Infrastructure Architecture

## Market Data Layer

Exchange WebSocket feeds.

Collectors written in:

Python or Rust.

---

## Event Streaming

Event-driven pipeline.

Technology:

- Kafka or Redpanda

Pipeline:

Exchange feeds  
↓  
Market collectors  
↓  
Kafka streams  
↓  
Feature engineering workers  
↓  
Signal engine

---

## Data Storage

### Time-Series Database

Used for market data.

Recommended systems:

ClickHouse or TimescaleDB.

---

### Transaction Database

Stores:

- users
- trades
- signals
- strategies

Recommended:

PostgreSQL.

---

### Caching Layer

Redis used for:

- fast signal delivery
- active market data
- session management

---

# 11. AI Model Design

Goal:

Generate signals with **positive expected value**.

---

## Data Inputs

- OHLC price data
- volume
- RSI
- MACD
- EMA
- ATR
- funding rates
- open interest
- order book imbalance

---

## Feature Engineering

Derived features include:

- volatility metrics
- trend strength
- momentum indicators
- order flow imbalance
- funding rate changes

---

## Market Regime Detection

Markets classified into regimes:

- bull trend
- bear trend
- ranging market
- high volatility regime

Signals adapt depending on regime.

---

## Models

Initial models:

- Gradient Boosting
- Random Forest
- ensemble methods

Future models:

- LSTM
- Transformer architectures

---

## Ensemble Strategy

Combine predictions from:

- Gradient boosting
- Random forest
- deep learning models

Ensemble improves robustness.

---

## Confidence Score

Derived from:

- model agreement
- historical performance
- market volatility
- regime context

---

## Risk Filter

Signals pass filters before release:

- minimum reward-to-risk ratio
- drawdown limits
- volatility thresholds

Only high-quality signals are published.

---

# 12. Training Pipeline

Training workflow:

Historical data  
↓  
Feature engineering  
↓  
Model training  
↓  
Backtesting  
↓  
Performance evaluation  
↓  
Deployment

Retraining frequency:

Weekly.

---

# 13. Exchange Integration Layer

Unified exchange connector using standardized APIs.

Handles:

- authentication
- rate limits
- order placement
- account balances

---

# 14. Database Schema

## Users

id  
email  
password_hash  
subscription_plan  
created_at

---

## Signals

id  
asset  
signal_type  
entry_price  
stop_loss  
take_profit  
confidence  
strategy_id  
created_at

---

## Trades

id  
user_id  
signal_id  
entry_price  
exit_price  
pnl  
status  
executed_at

---

## Strategies

id  
name  
parameters  
win_rate  
avg_roi  
max_drawdown  
sharpe_ratio

---

## Market Data

asset  
timestamp  
open  
high  
low  
close  
volume

---

## Feature Store

timestamp  
asset  
rsi  
macd  
ema  
volatility  
orderbook_imbalance

---

# 15. Security Architecture

API keys stored in secure vault.

Security practices:

- encrypted storage
- role-based access
- key rotation
- read + trade permissions only

Withdrawal permissions strictly disabled.

---

## Audit Logs

All user and system actions are logged to an immutable audit trail.

Captured events include:

- user logins and session events
- API key creation, rotation, and deletion
- trade placement, modification, and cancellation
- subscription changes and billing events
- admin actions and permission changes

Audit logs are:

- write-once (append-only)
- retained for minimum 2 years
- accessible to users for their own activity
- exportable for regulatory or tax purposes

---

## Data Anonymisation

Personally identifiable information (PII) is minimised throughout the platform.

Practices:

- user IDs are UUID-based, not sequential
- PII fields are encrypted at rest with envelope encryption
- analytics pipelines operate on anonymised datasets
- data exports exclude raw PII unless explicitly requested by the user
- data deletion requests are honoured within 30 days (right to erasure)

---

# 16. Monetization & Business Model

## Board Decision Required: Primary Monetisation Path

Before Phase 1 infrastructure build, the following decision must be approved by board + CFO:

### Option A: Subscription-First (RECOMMENDED)

**Structure:**
- **MVP Tier (Phase 1)**: $39/month — 4-6 signals/week, 2 exchanges (Binance + Bybit spot & perps), paper trading unlimited
- **Pro Tier (Phase 2)**: $99/month — 8+ signals/week, 4 exchanges (add Bitget + OKX), priority support, advanced risk controls
- **VIP Tier (Phase 3)**: $199/month — unlimited signals, all exchanges, profit-share option unlock, API access

**Advantages:**
- Predictable recurring revenue: enabling fundraising and 24-month burn planning
- High customer loyalty: switching friction once users have multiple subscriptions
- Regulatory simplicity: signals are information services, not managed accounts; no SEC/CFTC registration needed at MVP
- Faster MVP launch: simpler billing and compliance compared to profit-share model
- Works for both beginner and advanced users

**Disadvantages:**
- Price resistance from users who don't want subscriptions (competitor: eToro copy trading)
- Churn risk if signal quality weak (<60% win rate)
- Limits upside on high-frequency traders (would prefer profit-share)

**Financial Model:**
- Year 1 target: $1M ARR (≈2,150 Basic tier users at 40% churn)
- Gross margin: 75% (after data costs + infrastructure + payment processing)
- Data costs: $400/month MVP phase, $2,500/month Phase 3
- Breakeven: ≈1,800 paying users ($500/month overhead)

---

### Option B: Profit-Share Primary (High Risk)

**Structure:**
- $0 subscription
- 30% of profits taken when user profits (only if account grows >10% from initial balance)
- Minimum account size: $1,000
- Scaled payout: AlphaForge takes 30% only after user profitability threshold is met

**Advantages:**
- Zero friction for user signup: appeals to price-sensitive retail traders
- Aligned incentives: AlphaForge profits only when users profit
- Regulatory novelty: potentially creates new market category

**Disadvantages:**
- Revenue concentration risk: if signals lose edge, platform earns $0 (vs $39/month from subscription base)
- Regulatory complexity: may trigger investment adviser registration in US, MiFID II suitability in EU
- Requires 2-3 additional compliance hires + legal counsel ($100K+ legal fees for regulatory opinions)
- No predictable MRR: impossible to forecast for investor meetings or hiring plans
- High churn: users who don't profit immediately (~60% of retail traders) abandon platform
- Profitability incentive conflict: incentivizes high-risk signals vs sustainable edge

**Financial Model (Pessimistic):**
- Year 1: $0-100K revenue (depends entirely on signal quality + user capital)
- Requires $500K-$1M seed for 12+ month runway with no revenue
- Only viable if seed raises $2M+ to cover uncertainty

**Verdict:** Only pursue if (a) lead investor specifically requires it, (b) signal alpha definitively proven in backtests, (c) $1M+ funding committed.

---

### Option C: Hybrid Tiered (Complex)

**Structure:**
- Users choose subscription OR profit-share at signup
- Subscription: $29/month (reduced price tier due to profit-share option)
- Profit-share: $0 subscription + 30% of profits (same as Option B)

**Advantages:**
- Encompasses both models: appeals to different user psychographics
- Hedges regulatory risk: if profit-share is restricted, subscription users anchor revenue

**Disadvantages:**
- Operational complexity: split billing, invoicing, tax reporting for hybrid model
- User confusion: marketing has to explain choice, increases CAC (customer acquisition cost)
- Cannibalization: profit-share users are lower ARPU, higher churn (profit-share users expect 100% edge reliability)
- Requires 2x accounting complexity (2 revenue streams, 2 reporting narratives for investors)
- Only justified if you can't decide between A and B

**Financial Model:**
- Assume 60% choose subscription, 40% choose profit-share
- Year 1 revenue: $400-600K (below subscription-only)
- Breakeven: 2,500+ paying users (higher due to ARPU split)

**Verdict:** Not recommended for MVP. Consider in Phase 3 if subscription is stable and profit-share demand exists.

---

## DECISION: Recommend Option A (Subscription-First)

**Rationale:**
1. Predictable revenue for fundraising and hiring
2. Regulatory simplicity: information services model, not managed accounts
3. Works globally without jurisdiction-specific customization
4. Faster 4-month MVP launch vs 8-month legal/compliance build-out for profit-share

**Implementation Timeline:**
- Week 1: Board approves Option A
- Weeks 2-3: Build Stripe billing + subscription management
- Week 4: QA subscription flow (upgrade/downgrade/cancellation)
- Week 5+: Integrate into MVP infrastructure

---

## Copy Trading Economics

When users enable copy trading:
- User retains 100% of P&L and losses
- AlphaForge collects subscription fee only (no execution fees, no profit fees at MVP)
- Example: User copies $10K into BTC LONG signal, makes $1,000 profit
  - User nets: $1,000 profit
  - AlphaForge earns: $39/month subscription (unchanged)
  - Exchange costs: $0 (Binance/Bybit charge user taker fees, paid to exchange not AlphaForge)

This model eliminates conflicts of interest (AlphaForge doesn't profit from user losses or high churn).

---

## Performance Fee (Phase 3 Alternative)

If board elects Option C or wants performance upside in Phase 3:

- VIP users can elect performance fee model: $99/month + 15% of profits above 8% annual return
- Example: User gains $2,000 in a month ($16K annual equivalent, 8% on $200K account)
  - Performance fee trigger: $2,000 - (8% * $200K / 12 months) = $2,000 - $1,333 = $667
  - AlphaForge takes 15% of $667 = **$100.05** performance fee
  - User nets: $2,000 - $100.05 = $1,899.95
- Only applies when user outperforms 8% annual hurdle
- Regulatory risk: may require investment adviser registration; consult counsel in each jurisdiction

---

## Data Monetization (Phase 4+)

Optional future revenue stream (not for MVP):
- Anonymous aggregated trading insights (e.g., "70% of users are holding BTC long")
- Anonymised signal performance dataset sold to quant researchers
- **Policy:** PII never shared; data is aggregated and anonymised before sale
- **Governance:** User can opt-out via settings checkbox

---

# 17. MVP Scope

Launch timeline:

3–4 months.

MVP features:

- AI signals
- signal dashboard
- signal history
- Telegram alerts
- subscription billing
- performance tracking

Excluded initially:

- copy trading
- backtesting
- strategy marketplace
- advanced analytics

---

# 18. Product Roadmap

## CRITICAL PATH: Pre-Launch Board Decisions

**BLOCKERS to Phase 1 Infrastructure Build (Weeks 1-4 Parallel Track):**

1. ✅ **Monetisation Model Decision** — Option A (Subscription-First) or alternative approved by board
2. ✅ **Launch Jurisdiction Decision** — UK/EU-first (recommended) or alternative + legal opinion obtained
3. ✅ **Copy Trading Legal Framing** — User-directed execution (recommended) or alternative approved by legal counsel
4. ✅ **Signal Alpha Proof-of-Concept** — Backtest ≥2 candidate signals (Sharpe ≥1.0, profit factor ≥1.5), 4-week paper trading gate passed
5. ✅ **FCA Legal Opinion** (UK/EU launch) — Is investment adviser registration required? Signals classified as information services?

**If any blocker is not complete by Week 4, Phase 1 infrastructure build is delayed.**

---

## Phase 1: MVP (Weeks 5-16 after prerequisites cleared)

**Launch Target: Week 16-20 (Month 4-5) pending legal clearances**

### Core Platform MVP Features

**Dashboard & Portfolio**
- User dashboard with portfolio overview
- Holdings summary (per exchange)
- PnL metrics (daily, weekly, monthly, all-time)
- Win rate, Sharpe ratio, max drawdown

**AI Signal Generation** (2-3 validated signals at launch)
- Every signal must have:
  1. 2-year historical backtest (Sharpe ≥1.0, max drawdown ≤25%, profit factor ≥1.5, min 100 trades)
  2. Pre-registration hypothesis committed to audit log (timestamp, signal logic, expected edge)
  3. 4-week live paper trading on real market data (must achieve ≥80% of backtest Sharpe)
  4. Public "Proof" tab showing backtest chart + paper trading performance
- Example Phase 1 signals:
  - Signal A: Momentum breakout + RSI divergence (BTC/ETH)
  - Signal B: Funding rate arbitrage (perps only)
  - Signal C: One additional validated signal (to be determined by quant team)

**Paper Trading (Unlimited)**
- Simulated portfolio mirror trading (no real exchange orders)
- Tracks: PnL, win rate, drawdown, Sharpe ratio (same metrics as live)
- Unlimited duration (no time gate)
- No account minimum
- Users see side-by-side: paper vs live (when live trading enabled)

**Risk Engine (Non-Negotiable Enforcement)**
- Max position size: 2% per trade
- Portfolio exposure limit: 20% per asset
- Perpetuals-specific limits: Max 5x leverage (Phase 1)
- Stop loss enforcement: System prevents trades without defined stop loss
- Risk-adjusted position sizing: Formula: Position Size = (Account * 2%) / (Entry - Stop) 
- Users cannot override risk limits (structural constraint, not optional setting)

**Copy Trading (2 Exchanges Minimum)**
- Binance (spot + perpetuals)
- Bybit (perpetuals)
- User connects via API key (read-only + trade permissions, withdrawal disabled)
- User can enable/disable signals individually (checkbox per signal)
- 24-hour cancellation window before first trade on new signal
- Execution: System routes orders to exchange via REST API
- Paper → Live conversion: Soft prompts at Day 14, 21, 28 of paper trading + 30% first-month discount

**Subscription Billing**
- Stripe integration
- $39/month Basic tier (only tier at MVP, separate Pro/VIP come in Phase 2)
- Monthly billing cycle
- Cancel anytime (no lock-in)
- Free trial: 7 days paper trading only (no live execution)

**Signal Dashboard & History**
- Real-time signal feed (latest 4 signals)
- Signal cards show: asset, direction, entry, SL, TP, confidence, driver breakdown
- Full signal history (searchable, filterable by asset/date)
- Immutable audit trail: All signals hash-chained + cryptographically signed

**Regulatory Compliance**
- KYC/AML: Basic at signup (name, email, DOB, country) → Enhanced KYC (government ID + proof of address) before first live trade
- GDPR/CCPA: Consent management platform active; privacy policy compliant
- Disclaimers: Financial promotion, past performance, leverage risk (modals before first trade)
- Regulatory opinion letter on file (FCA confirmation that signals are information services, not managed accounts)

---

### Phase 1 Constraints & Non-Features

**NOT included in MVP (deferred to Phase 2+):**
- Strategy marketplace (complexity deferred)
- Advanced analytics dashboard (simplified version only)
- Mobile app (web-responsive only)
- Backtesting lab (internal use only)
- Alternative exchanges (only 2 supported)
- Profit-share model (subscription-only)
- Advanced risk controls (only basic limits)
- TradingView integration (Phase 3)
- User-built strategies (deferred decision)

---

## Phase 2 (Weeks 17-30)

**Market Intelligence Suite**
- Liquidation heatmap (showing liquidation clusters by exchange)
- Funding rate monitor (perpetuals funding rates per exchange + historical trend)
- Trend dashboard (momentum, strength metrics over time)
- Sentiment breakdown (aggregated market sentiment per asset)
- On-chain dashboard (whale movements, exchange flows, active addresses)
- All components visualised in Recharts with real-time updates

**Performance Analytics**
- Win rate tracking (per strategy, per asset, custom date range)
- Sharpe ratio calculation (monthly, quarterly, yearly)
- Drawdown analysis (running max, max consecutive loss days)
- Monthly P&L breakdown (fees, slippage impact)
- ROI and CAGR calculations
- Comparison to benchmark (BTC hodl returns)

**Pro Tier Launch** ($99/month)
- 8+ signals per week (vs 4-6 for Basic)
- 4 exchanges (add Bitget + OKX to Binance + Bybit)
- Advanced risk controls: configurable leverage limits, correlation risk filtering
- Priority email support
- Early access to new features

**Advanced Risk Controls**
- Leverage limit per asset (user-configurable: 1x-5x)
- Correlation risk: System prevents opening similar directional positions across correlated assets
- Portfolio heat map: Visual showing overall portfolio concentration risk
- Volatility-adjusted sizing: Position size scales down in high volatility regimes

**PWA Capability**
- Progressive Web App manifest (installable to home screen)
- Push notifications via Web Push API
- Offline signal caching (read-only, no trades when offline)
- Mobile-responsive UI (Tailwind breakpoints tested)
- Android Web App install prompt (iOS 15+ support TBD)

**Backtesting Lab** (User-Facing)
- Users upload CSV strategy data (entry/exit prices, timeframe)
- System backtests against historical OHLC data (Polygon.io)
- Output: Win rate, Sharpe ratio, max drawdown, profit factor
- Does NOT execute real trades (research-only tool)
- Comparison mode: Compare 2+ strategies side-by-side

**Education Layer**
- Glossary: 50+ crypto/forex terms (RSI, Sharpe ratio, liquidation, etc.)
- Contextual tooltips: Hover over any metric to see explanation
- Signal driver explainer: "What is RSI divergence?" → video + interactive chart
- Risk explainer: Interactive leverage simulator ("If you lose X%, your account is liquidated at Y leverage")
- Blog integration: 5-10 educational articles linked from UI

**Tax Integration**
- "Tax Summary" dashboard showing:
  - Gross P&L (all trades)
  - Fees paid (exchange fees + AlphaForge subscription)
  - Estimated capital gains (short-term vs long-term)
  - Export for accountant (CSV format)
- **Note:** No withholding or tax filing; users responsible for local tax reporting
- Privacy: Tax data stored locally in browser; never sent to AlphaForge servers

---

## Phase 2.5 (Weeks 28-35): Strategy Marketplace Soft Launch

**Marketplace Beta: Invite-Only**
- Limited to 50 creator submissions (target 5-10 approved at launch)
- All creators must pass same verification gate as internal signals:
  1. 2-year backtest (Sharpe ≥1.0, PF ≥1.5, max DD ≤25%, min 100 trades)
  2. Pre-registration hypothesis committed to audit log with timestamp
  3. 4-week live paper trading on real market data (must match ≥80% backtest Sharpe)

**Marketplace Governance Policy Published**
- Review Committee: 2 internal (Head of Product + Head of Risk) + 1 external independent expert
- Approval criteria: Sharpe ≥1.0, max drawdown ≤25%, profit factor ≥1.5
- Live performance monitoring: Monthly review
  - Sharpe <60% of backtest for 1 month: warning badge
  - Sharpe <50% for 2 consecutive months: automatic delisting
  - Max drawdown >backtest + 10%: automatic delisting
- Appeals process: Creator can appeal rejection once; external arbitrator makes final decision
- Creator code of conduct: No false marketing claims, no coordinated trading, max 8x leverage
- Liability: AlphaForge not liable for strategy losses, but liable for verification process breaches

**Marketplace Revenue**
- Creator pays $99/month listing fee to marketplace
- AlphaForge takes 10% of subscription revenue from users who copy creator strategy
- Example: Creator's strategy earns $1,000/month from 25 users
  - Creator nets: $900/month (after 10% revenue share)
  - AlphaForge takes: $100/month from strategy subscriptions

**Beta Visibility**
- Visible to 30% of user base (A/B testing group)
- Separate "Creator Strategies" tab in UI
- Creator profile page showing backtest proof + live track record

---

## Phase 3 (Weeks 31-48)

**Full Marketplace Launch**
- Remove invite-only gate; accept all creator submissions that pass verification
- Target: 50-100 approved creator strategies on platform by end of Phase 3
- Creator marketplace dashboard: stats, subscriber count, revenue tracking

**VIP Tier Launch** ($199/month)
- Unlimited signals per week
- All exchanges (6+: Binance, Bybit, Bitget, OKX, MEXC, Gate.io)
- Profit-share model unlock (optional): 0 subscription + 30% of profits (for VIP users only, application-gated, max 100 seats)
- Advanced API access: Programmatic signal access, webhook delivery
- Dedicated account manager (for top 50 VIP users)

**Profit-Share Model Availability** (VIP Only)
- Eligibility: VIP $199/month users, application-approved
- Terms: 0 subscription + 30% of profits
- Activation gate: User must complete 4-week paper trading first
- Economics: 30% taken only when user account grows ≥10% from starting balance
- Maturity filtering: Only 100 seats available globally (capacity cap)

**Mobile Experience Expansion**
- Option A: Full mobile-first responsive redesign (CSS media queries, touch-optimized UI)
- Option B: Native iOS beta (evaluate demand, resource cost vs PWA + responsive web)
- Recommendation: Start with Option A (responsive redesign), defer native apps to Phase 4

**TradingView Webhook Integration** (Advanced Users)
- Users can POST webhooks from TradingView alerts into AlphaForge
- AlphaForge converts webhook into trade execution (subject to risk engine validation)
- Example: User has custom TradingView script → on signal, POST to AlphaForge → execution routed to exchange
- Webhook format: JSON with entry, SL, TP, asset, side
- Use case: Advanced traders bring custom strategies into AlphaForge execution engine

**Exchange Expansion**
- Add MEXC (altcoin audience)
- Add Gate.io (Asia-focused traders)
- Total supported: 6 exchanges (Binance, Bybit, Bitget, OKX, MEXC, Gate.io)
- Deprioritized: Kraken (lower trading volume for alts), Coinbase (native app better for US audience)

**Signal Expansion**
- Scale to 15-20 daily signals across assets:
  - BTC (3-4 signals)
  - ETH (3-4 signals)
  - SOL (2 signals)
  - Major alts (LINK, ARB, AVAX, etc.) (6-8 signals)
  - Forex pairs (optional, depending on team capacity)
- Signal driver diversity:
  - Momentum divergence
  - Funding rate arbitrage
  - Liquidation cluster reversal
  - Volatility regime detection
  - On-chain whale accumulation
  - Order book imbalance
  - Sentiment-driven signals (social media trends)
  - Correlation-based pair trading

**User-Built Strategies Decision Point**
- DECISION REQUIRED: Allow users to build their own strategies in AlphaForge engine?
- Option A: No (keep signals AI-only, simpler product, better QC)
- Option B: Yes (TradingView webhook + custom script support, appeals to advanced traders, more complex QC)
- **Recommendation:** Defer to Phase 4; start MVP with AI signals only. Adds complexity for limited TAM (only top 5% of traders build custom strategies).

---

## Phase 4 (Weeks 49-60+): International & Institutional Expansion

**Native Mobile Apps**
- iOS app (native SwiftUI, distribute via App Store)
- Android app (native Kotlin/Jetpack Compose, distribute via Google Play)
- Feature parity with web (all trading, all analytics)
- Push notifications for signals + trades
- Biometric auth (Face ID / Touch ID / fingerprint)

**US Market Expansion**
- **Gate**: Only if SEC/CFTC legal opinion confirms no investment adviser registration required
- **Alternative**: Register as Registered Investment Adviser (RIA) with SEC if copy trading requires it
  - Cost: $15-30K registration + $5-10K annual compliance
  - Timeline: 8-16 weeks for SEC approval
  - Scope expansion: Must provide suitability documentation before copy trading
- **Recommendation:** Defer to Phase 4; start with UK/EU-first MVP

**International Expansion**
- Singapore/Hong Kong expansion (SFC/ASI regulated)
- Malaysia, Thailand, Indonesia (once compliance templates proven)
- Deprecation: Avoid US sub-prime lending-style aggressive compliance; stick to transparent jurisdiction ops

**Institutional Tier**
- API access for hedge funds / prop trading firms
- Bulk signal delivery (daily digest, not real-time)
- Custom integrations (Slack, Discord, proprietary order routing)
- SLA guarantees: 99.95% uptime, <100ms signal delivery latency
- Pricing: $2,000-5,000/month custom
- Dedicated technical support

**OTC Settlement Layer** (Conditional)
- Only build if demand from institutions validates
- Allows institutional users to settle at custom prices vs exchange fills
- Adds regulatory complexity (settlement risk, custody); defer until Phase 4+

**Advanced Order Types**
- Iceberg orders (hide order size in small chunks)
- TWAP: Time-weighted average price execution
- VWAP: Volume-weighted average price execution
- Useful for large institutional trades; less relevant for retail MVP

**White-Label Option**
- AlphaForge backend available as white-label to brokers / community platforms
- Pricing: $X per trade or $X per user per month
- Use case: Bitget, OKX, other exchanges integrate AlphaForge signals into their CMS

---

## Signal Quality Standards (All Phases)

**Signal Launch Gate (Non-Negotiable for Any Signal):**

1. **Backtest Validation**
   - Minimum: 2 years of historical data
   - Sharpe ratio: ≥1.0 (risk-adjusted return metric)
   - Maximum drawdown: ≤25% of account equity
   - Profit factor: ≥1.5 (total wins / total losses)
   - Minimum trades: 100 (statistical significance)
   - Win rate: Not specified (can be <50% if PF >1.5, i.e., winners larger than losers)

2. **Pre-Registration Hypothesis (Audit Trail)**
   - Before paper trading, creator submits hypothesis to immutable audit log
   - Recorded: Exact timestamp, signal logic description, expected edge, assumptions
   - Purpose: Prevent p-hacking / result-fitting post hoc
   - Blockchain timestamp or append-only database proof

3. **Paper Trading Validation (4 Weeks Minimum)**
   - Live market data, simulated execution
   - Must achieve: ≥80% of backtest Sharpe ratio
   - Example: Backtest Sharpe 1.5 → Paper trading must achieve ≥1.2 Sharpe
   - Purpose: Confirm backtest not over-fit to historical data

4. **Public Proof Tab**
   - Every signal displays:
     - 2-year backtest chart (equity curve + drawdown)
     - Win rate, Sharpe ratio, max drawdown, profit factor
     - Paper trading performance (last 4 weeks)
     - Pre-registration hypothesis commitment (with timestamp)
   - Transparent to all users; no cherry-picking results

**Signal Retirement (Live Performance Monitoring)**
- Monthly review: Compare live performance to backtest baseline
- If live Sharpe <60% of backtest Sharpe: Warning badge displayed to users
- If live Sharpe <50% of backtest for 2 consecutive months: Automatic delisting
- If max drawdown >backtest + 10%: Automatic delisting
- User notification: 2-week notice before retirement; unfollows automatic
- Retired signal track record remains public in audit trail (transparency)

---

# 19. Competitive Advantage

AlphaForge differentiates through four pillars.

## Transparency

Full signal history with verifiable results. Every signal result is recorded, publicly queryable, and cryptographically auditable — no cherry-picking, no survivorship bias.

## Explainability

Every signal includes a human-readable breakdown of its drivers. Traders understand *why* a signal was generated, not just what it says. This is the primary trust differentiator vs. black-box competitors.

## Automation

Integrated AI copy trading with enforced risk limits. Users cannot accidentally over-leverage — the risk engine is non-negotiable.

## Intelligence

Institution-level analytics for retail traders: liquidation heatmaps, funding rate extremes, open interest trends, on-chain data, and sentiment analytics. These are tools normally reserved for professional desks.

---

# 20. Growth Strategy

Primary growth channel:

Telegram trading communities.

Growth loop:

Free signals  
↓  
Build trust  
↓  
Paid subscriptions  
↓  
Automation features

---

# 21. Product Potential

If executed successfully:

AlphaForge could scale into a:

$10M+ ARR trading intelligence platform.

---

# 22. Regulatory & Legal Decisions Framework

**CRITICAL**: All decisions in this section require board + legal counsel approval before Phase 1 infrastructure build. These decisions will determine compliance scope, timeline, and cost structure.

---

## Decision 1: Primary Launch Jurisdiction

### Option A: UK/EU Launch First (RECOMMENDED)

**Why UK/EU First:**
- Regulatory clarity: FCA has published guidance on algorithmic trading signals (DP16/6)
- Legal precedent: Copy trading exists in UK (e.g., eToro UK subsidiary) with established precedent
- Fast legal opinion: 4 weeks typical (vs 12 weeks for US)
- GDPR expertise: Legal market has deep GDPR expertise; easier to find counsel
- Market size: 450M+ potential users (UK + EU + EEA)
- Timing: Launch simultaneously in UK + EU post-FCA opinion

**Implementation Roadmap:**
- **Weeks 1-2**: Engage UK fintech counsel (recommend: Linklaters, Allen & Co, or CMS)
- **Weeks 2-3**: Provide counsel with documentation:
  - Technical architecture (how signals are generated, no discretionary account management)
  - Terms of Service (showing user retains control, can cancel signals anytime)
  - API documentation (showing encrypted keys, withdrawal disabled)
- **Weeks 3-4**: Obtain FCA Legal Opinion Letter addressing:
  1. Are AI signals investment advice under MiFID II?
  2. Is copy trading (user-directed execution) discretionary account management?
  3. Is investment adviser registration required for AlphaForge?
  4. What disclaimers are required?
- **Expected Outcome**: "AI signals are market commentary (information services). Copy trading with user-initiated execution is not discretionary account management. No FCA registration required."
- **Cost**: £10-15K (~$12-18K)
- **Timeline to Phase 1 Launch**: +4 weeks legal + 0 weeks registration (if no registration required) = 4 weeks.

**Regulatory Obligations (if legal opinion confirms no registration needed):**
- GDPR compliance: Privacy policy, DPA with vendors, right to erasure
- Age verification: 18+ only
- Disclaimers: Financial promotion, past performance, leverage risk (see Section 23 disclaimers)
- AML/KYC: Enhanced KYC before live trading (government ID + proof of address)
- Data retention: 24-month audit trail + anonymisation of deleted users

---

### Option B: US-First Launch (HIGH RISK)

**Why NOT Recommended for MVP:**
- Regulatory uncertainty: SEC's position on AI trading signals unclear
- Copy trading legal framing: May trigger Registered Investment Adviser (RIA) registration requirement
- Timeline: 8-16 weeks for legal opinion (vs 4 weeks UK)
- Cost: $30-50K legal fees (vs $12-18K UK)
- State-level complexity: Additional requirements in NY (BitLicense), CA, other states
- Likelihood: 70% chance registration IS required → adds 4-8 months compliance build-out
- Marketing constraint: If registration required, cannot claim "AI" as black-box; must show full explainability

**If Board Insists on US Launch:**
1. Engage SEC/CFTC counsel (recommend: Davis Polk, Cooley, Skadden)
2. Provide same documentation as UK process
3. Obtain opinion on:
   - Do signals trigger investment advice registration?
   - Is copy trading a security? Commodity? Forex?
   - What state-level compliance is required?
4. Budget $40-60K legal + $15-30K registration (if required) + $200K/year compliance staff
5. Timeline: 12-20 weeks before first US user can trade
6. Alternative: Register as RIA immediately (skips legal opinion, costs $20-30K setup)

**Verdict**: Only pursue if (a) Series A investor requires US market first, (b) willing to budget $50-100K for legal/compliance, (c) 4-6 month delay to Phase 1 launch acceptable.

---

### Option C: Asia-First (DEFERRAL STRATEGY)

**Singapore / Hong Kong as Phase 2 Backup:**
- Timeline: 6-8 weeks for SFC/MAS opinion (vs 4 weeks UK)
- Cost: $15-25K legal fees
- Regulatory clarity: SFC has explicit AI trading guidance (RA 19-59)
- Market: Growing crypto adoption in Singapore; strong fintech ecosystem
- Use case: If UK/EU launch delayed by legal challenges, pivot to Singapore Phase 2

**Verdict**: Keep as Phase 2 fallback if UK launch constrained by GDPR enforcement actions or regulatory delays.

---

## 🔒 DECISION: Jurisdiction = UK/EU Launch First (4-Week Legal Opinion)

**Action Items:**
- Week 1: Board approves UK/EU-first jurisdiction
- Week 1: CEO + Legal engage fintech counsel (Linklaters or CMS)
- Week 2: Provide technical + legal documentation to counsel
- Week 4: Receive FCA opinion letter
- Week 5+: Begin Phase 1 infrastructure build

---

## Decision 2: Copy Trading Legal Framework

### Option A: User-Directed Execution (Information Services Model) — RECOMMENDED

**What This Means Operationally:**

1. **Signal Delivery**: AlphaForge provides AI signals (market commentary, recommendations)
2. **User Explicit Opt-In**: User sees signal card with entry/SL/TP, clicks "Enable" checkbox per signal
3. **Pre-Trade Approval**: User reviews order details on order preview screen before execution
4. **24-Hour Cancellation**: User can cancel enabled signals up to 24 hours before first trade
5. **User Control**: User can modify stop loss / take profit on exchange UI (AlphaForge cannot force prices)
6. **Execution**: User-initiated instruction to exchange (not managed by AlphaForge algorithm)

**Why This Framing:**
- **Legal precedent**: eToro UK, Bitget, OKX all use this model with regulators accepting it
- **Regulatory simplicity**: Information services, not discretionary account management (no investment adviser registration needed)
- **Clear liability boundary**: AlphaForge liable for signal generation accuracy, user liable for trading decisions
- **Global replicability**: Same framework works in UK, EU, Singapore, Asia

**Example T&S Language:**
> "AlphaForge provides AI-generated trading signals as market commentary only. When you enable a signal, YOU authorize AlphaForge to submit a trade instruction to your connected exchange. You retain full control: you can modify prices, cancel trades, or disable signals at any time. AlphaForge is not a discretionary manager and does not have power of attorney over your account."

**Regulatory Disclaimers Required:**
1. Financial promotion warning: "This is market commentary, not investment advice"
2. Past performance: "Past signal performance does not guarantee future results"
3. Leverage risk: "Trading with leverage can result in liquidation and total account loss"
4. Execution risk: "Trades may execute at different prices than preview due to market slippage"
5. Technology risk: "System failures may prevent trade execution"
6. Model risk: "AI signals can be wrong; no guarantee of profitability"

**Advantages:**
- ✅ No SEC/FCA registration required
- ✅ No MiFID II suitability assessments (market commentary exception)
- ✅ Works globally with minimal customization
- ✅ Establishes user liability (reduces AlphaForge defensive litigation risk)
- ✅ Faster compliance sign-off (4-week legal opinion)

**Disadvantages:**
- ❌ Users feel less "passive" (must explicitly enable signals, not automatic)
- ❌ Competitor narrative: "eToro's copy trading is fully automatic" (need marketing differentiator)
- ❌ Slightly lower conversion rate (extra friction = fewer users enabling copy trading)

---

### Option B: Discretionary Account Management (Phase 3+)

**What This Means Operationally:**

1. **User Grant Power of Attorney**: User signs legal document authorizing AlphaForge to trade on their behalf
2. **Automatic Execution**: When signal fires, AlphaForge automatically places trade without user pre-approval
3. **AlphaForge Discretion**: AlphaForge chooses execution price, timing, modifications (not user)
4. **Account Management**: AlphaForge manages position sizing, risk limits, profit-taking (full account control)
5. **Professional Accountability**: AlphaForge liable if trades underperform market standards

**Why Deferred to Phase 3:**
- Requires investment adviser registration (SEC/FCA/SFC)
- Legal opinion not clear until after Phase 1 market testing
- Complex compliance: Suitability letters, financial disclosures, ongoing suitability reviews
- Higher liability insurance costs ($20-30K/year vs $8-15K)
- Not necessary for MVP (user-directed execution sufficient for product launch)

**Advantages:**
- ✅ Fully passive user experience (signals execute automatically)
- ✅ No user friction (no checkboxes; just subscribe and profit)
- ✅ Appeals to lazy/busy traders (core retail demographic)

**Disadvantages:**
- ❌ Requires investment adviser registration ($15-30K legal, $5-10K annual compliance)
- ❌ Must provide suitability assessments before trading (slow customer onboarding)
- ❌ Higher regulatory scrutiny and audit risk
- ❌ Longer legal opinion timeline (8-12 weeks)

**Verdict for MVP**: Do NOT pursue Option B for Phase 1. Confirm with FCA that user-directed execution (Option A) is acceptable; defer discretionary management to Phase 3 if demand validates.

---

## 🔒 DECISION: Copy Trading Legal Framework = User-Directed Execution (Option A)

**T&S Implementation:**
- User must click "Enable" per signal (explicit opt-in)
- 24-hour cancellation window before first trade
- Order preview screen shows execution details before sending to exchange
- User retains ability to modify SL/TP on exchange UI

**Action Items:**
- Week 2: Legal counsel reviews T&S copy trading language for FCA compliance
- Week 3: Draft signal disclaimers with counsel + integrate into UI
- Week 4: QA all disclaimer triggers + user consent flows

---

## Decision 3: Marketplace Governance & Operational Policy

**Required BEFORE marketplace launches (Phase 2.5).**

### Marketplace Verification Gate

Every creator strategy must pass identical verification as internal signals:

**Verification Requirements:**
1. **2-Year Historical Backtest**
   - Minimum: 100 winning + losing trades
   - Sharpe ratio: ≥1.0
   - Max drawdown: ≤25%
   - Profit factor: ≥1.5 (total wins / total losses)
   - Out-of-sample validation preferred (hold-out test set)

2. **Pre-Registration Hypothesis Commitment** (Immutable Audit Trail)
   - Creator submits: Date, signal logic description, expected edge, key assumptions
   - Recorded to blockchain or append-only database with cryptographic timestamp
   - Purpose: Prevent p-hacking / overfitting after results are known
   - Public on creator profile: "Strategy registered for paper trading on [DATE]"

3. **4-Week Live Paper Trading** (Minimum)
   - Execution: AlphaForge shadow-mirrors creator strategy using live market data
   - No real money; simulated fills at actual market prices
   - Performance measurement: Track Sharpe ratio vs backtest baseline
   - Pass criterion: Live Sharpe ≥80% of backtest Sharpe
   - Example: Backtest Sharpe 1.5 → must achieve ≥1.2 in paper trading to approve

4. **Creator Profile Requirements**
   - Background verification (optional but encouraged): Trading credentials, prior track record
   - Professional photo + bio (authenticity filter)
   - Conflict of interest disclosure (if creator benefits from specific price moves external to strategy)
   - Prohibited: Fake credentials, deleted strategies post-failure, recycled strategies under new names

---

### Review Committee & Appeals

**Review Committee Composition:**
- 2 internal: Head of Product, Head of Risk
- 1 external: Independent fintech/trading advisor (monthly rotating)
- Quorum: Unanimous approval required (all 3 must recommend approval)

**Approval Timeline:**
- Submission → Initial review: 5 business days
- Questions/revisions: 10 business days (back-and-forth)
- Final decision: 2 business days
- Total: 2-3 weeks typical

**Appeals Process:**
- Creator can appeal rejection ONCE
- Escalates to external arbitrator (fintech counsel on retainer)
- Arbitrator reviews verification data independently
- Decision is final (no further appeal)

---

### Live Performance Monitoring & Delisting

**Monthly Review Cycle:**
- Performance measured against backtest baseline
- Automated alerts if thresholds breached

**Delisting Triggers (Automatic):**
1. **Performance Degradation**: Live Sharpe <50% of backtest Sharpe for 2 consecutive months → Automatic delisting
   - Example: Backtest 1.5 Sharpe → actual 0.75 Sharpe for 2 months → delisted
   - User notification: "Strategy needs to be revalidated; we're temporarily delisting"
2. **Drawdown Breach**: Max drawdown >backtest baseline + 10% → Automatic delisting
   - Example: Backtest max DD 20% → actual 31% → delisted
3. **Data Quality**: >5% of signals missing execution data (system failures) → Warning badge, manual review

**Warning Threshold (Non-Automatic):**
- Live Sharpe <60% of backtest for 1 month → Warning badge displayed to users
  - "This strategy is underperforming its backtest; invest carefully"
  - Subscribers notified via email
  - No automatic delisting yet; 1-month probation

**Creator Notification:**
- Automatic alert sent 48 hours after trigger
- Creator has 5 business days to respond with explanation (e.g., "Market regime changed")
- If no response: Proceed with delisting
- If response provided: Committee reviews separately (may reinstate if compelling reason)

**Users Affected by Delisting:**
- All active subscribers notified 2 weeks before delisting
- Subscriptions automatically unfollowed (users not charged)
- Historical performance remains public (no deletion for transparency)
- Users can re-enable if strategy later re-approved

---

### Marketplace Revenue & Creator Economics

**Listing Fee:**
- $99/month per strategy to be marketplace-eligible
- Creators pay directly (transaction fee, not per subscription)
- If strategy delisted: Refund prorated remainder of month

**Revenue Share:**
- AlphaForge takes 10% of subscription revenue from strategy subscribers
- Creator retains 90%
- Example: 50 users subscribe to creator strategy at $39/month = $1,950/month revenue
  - AlphaForge takes: 10% = $195/month
  - Creator earns: 90% = $1,755/month

**Payout Schedule:**
- Payouts monthly via Stripe Connect
- Minimum payout threshold: $100 (lower balances held until threshold met)
- Tax responsibility: Creators responsible for 1099 reporting (if US) or local tax
- Withholding: AlphaForge withholds 30% for US creators (IRS requirement); non-US creators can provide W-8BEN

---

### Creator Code of Conduct

**Mandatory Policies:**

1. **No False Marketing**
   - All performance claims must reference backtested proof on creator profile
   - Prohibited: "100% guaranteed returns," "never loses," "proprietary AI" (vague)
   - Enforcement: Marketing team reviews creator bio + signal description for compliance

2. **No Coordinated Trading**
   - Creator cannot coordinate with other creators to artificially pump signals
   - Creator cannot use personal capital to front-run own strategy (conflict of interest)
   - Prohibited: "My buddies will all go long BTC on Tuesday" (market manipulation)

3. **Leverage Limits**
   - Max leverage on any strategy: 8x (prevent rekt liquidations damaging platform reputation)
   - Applies to: All derivatives strategies, not applicable to spot trading
   - Technical enforcement: UI prevents strategy creation with >8x leverage configured

4. **Conflict of Interest Disclosure**
   - If creator benefits from specific price moves (e.g., owns 1,000 BTC, strategy is BTC long)
   - Must disclose in creator bio: "I have personal long bias toward BTC"
   - Transparency: Allows users to evaluate conflict impact

5. **Signal Delay Disclosure** (if applicable)
   - If strategy execution delayed by >1 hour after signal generation (e.g., webhook latency)
   - Must note in description: "Typical execution delay: 5-10 minutes"
   - Sets user expectations accurately

**Enforcement:**
- Violations flagged by AlphaForge compliance team
- First violation: Formal warning + 48-hour fix deadline
- Second violation: 30-day suspension
- Third violation: Permanent delisting + marketplace ban

---

### Liability Terms for Marketplace

**AlphaForge Liable For:**
- Breach of verification process (accepted strategy later found fraudulent or over-fit)
- System failures preventing signal delivery (creator can claim damages)
- Data misrepresentation (backtest data manipulated by AlphaForge team)
- Liability cap: $5M (or insurance policy limit)

**AlphaForge NOT Liable For:**
- Strategy underperformance (even if <backtest Sharpe)
- Market losses or liquidations when following strategy
- Slippage or execution price differences
- Creator's personal statements (creator responsible for own words)

---

## 🔒 DECISION: Marketplace Governance Policy = Permanent

**Implement BEFORE Phase 2.5 (Week 28):**
- Review Committee structure operationalized
- Delisting triggers coded into monitoring system
- Creator code of conduct published + terms updated
- Creator payout system tested with pilot creators

**Action Items:**
- Week 20: Publish marketplace governance documentation publicly
- Week 24: Set up creator review committee meeting cadence
- Week 26: Build monitoring dashboards (Sharpe ratio tracking, delisting alerts)
- Week 28: Beta launch with 10-20 pilot creators

---

## Decision 4: Player Trading Requirement & Economics

### Timeline Decision: Paper Trading as Phase 1 vs Phase 2

**Recommendation: Paper Trading in Phase 1 (Before Live Execution)**

**Why Phase 1:**
- ✅ Reduces wash-out rate: Traders who can't profit in paper won't profit live
- ✅ Confidence building: Users who paper trade successfully are 3x more likely to convert to paid live
- ✅ Signal validation: 4-week paper trading is gate for internal signals; sets consistency

**User Experience:**
- Free 7-day trial: Paper trading only (no exchange connection required)
- Unlimited paper trading duration: No time gate, no upgrade pressure
- Conversion prompts at Day 14, 21, 28: "Ready to trade live? Get 30% off first month"
- Live toggle: Simple switch in settings to convert paper account → live

**Conversion Economics:**
- 30% off Month 1: $39/month → $27 first month for converter
- Expected conversion rate: 5-10% of paper traders → $ paid subscribers
- Gross margin: Still 75% after discount (data + infra + payment processing)

**Implementation:**
- Week 10: Build paper trading simulation engine (shadow mirror live prices)
- Week 12: Integrate conversion UI + discount code system
- Week 13: QA paper → live transition flow (API key connection, risk confirmation)

---

## Decision 5: AML/KYC Compliance Scope

### Option A: Basic KYC at Signup + Enhanced KYC Before Live Trading (RECOMMENDED)

**Phase 1 (Paper Trading Only):**
- Name, email, date of birth, country
- Paper trading enabled immediately
- NO government ID verification required
- NO AML screening required
- Purpose: Low friction for people curious about platform

**Phase 1 → Phase 2 (Before First Live Trade):**
- Triggered automatically when user tries to connect exchange API
- Enhanced KYC required:
  1. Government-issued ID (passport, driver's license, national ID)
  2. Proof of address (utility bill, bank statement dated <3 months)
  3. Selfie with ID verification (Onfido, IDology, or Complytix)
- AML screening: OFAC + PEP list check (automatic)
- Turnaround: Instant (AI) or 24 hours (human review)
- Third-party vendor: **Onfido** recommended (cost $0.50-1.50 per verification, enterprise API)

**Vendor Recommendation: Onfido**
- Cost: $0.50-1.50 per verification
- Turnaround: Instant-24h
- Coverage: 195+ countries
- Available in EU, US, UK, Singapore
- API integration: REST API, easy to integrate into signup flow
- Drawback: Requires customer support contact for disputes (not instant resolution)

**Alternative Vendors:**
- **IDology** (US-focused, ~$1 per verification, established fintech vendor)
- **Complytix** (EU-focused, GDPR-optimized, ~$1.50 per verification)
- **Docusign Identity** (expensive but highest accuracy, $2-3 per verification)

**Rejection Handling:**
- If verification fails: User receives clear reason (e.g., "Selfie illegible, please retake")
- Retry limit: 3 attempts, then escalate to human support
- Appeal: User can request manual review by AlphaForge compliance team (48-hour turnaround)

**Advantages:**
- ✅ Low friction for signup (paper trading demo doesn't require ID)
- ✅ Compliance meets UK FCA guidance (verifying users before money touch)
- ✅ Reduces fraud/account takeover risk
- ✅ Scalable (automated verification reduces compliance headcount)

**Disadvantages:**
- ❌ Some users abandon at ID verification step (~10-15% drop-off typical)
- ❌ Privacy concerns: Storing ID images (requires encryption, strong data governance)
- ❌ False positives: Legitimate users rejected (need manual review process)

---

### Option B: No KYC, Anonymous Paper Trading Only (Not Recommended)

**Structure:**
- Email only needed (no name, no ID)
- Paper trading unlimited
- Live trading: **Completely disabled**
- Users cannot connect exchange APIs

**Advantages:**
- ✅ Maximum privacy / anonymous access
- ✅ Fastest onboarding (1 click)

**Disadvantages:**
- ❌ Revenue model breaks (users can't trade live, can't pay subscription)
- ❌ Useless product (signals only valuable if executed)
- ❌ Regulatory risk: May trigger FCA/regulatory concerns about market manipulation (unidentifiable users)

**Verdict:** Don't pursue. Paper trading only (no live) is demo, not product.

---

## 🔒 DECISION: KYC Scope = Enhanced KYC Before Live Trading (Onfido Integration)

**Implementation Timeline:**
- Week 5: Negotiate Onfido enterprise contract (volume discounts)
- Week 8: Integrate Onfido API into signup flow (test environment)
- Week 11: QA verification flow + rejection handling
- Week 13: Deploy to production with manual appeal process

**Cost Impact:**
- Onfido verification: $0.50-1.50 per user per verification (~3,000 users Year 1 = $1,500-4,500)
- Internal compliance: 0.5 FTE for appeals + dispute handling
- Insurance impact: E&O insurance may require KYC verification (premium reduction likely)

---

## Decision 6: Insurance & Liability Cap

### E&O (Errors & Omissions) Insurance Requirement

**Coverage Needed: $5M E&O Policy**
- Covers: Execution errors, API security breaches, signal generation errors, system failures
- Deductible: $1M recommended (lower deductible = higher premium)
- Policy period: 12 months (annual renewal)
- Retroactive coverage: Required (covers issues pre-dating policy binding date)

**Procurement Timeline:**
- Week 5: CFO engages fintech insurance broker
- Week 7: Underwriter audits infrastructure (encryption, penetration testing, incident response plan)
- Week 10: Policy binding (premium due)
- Week 13: Policy active before MVP launch

**Cost Estimate:**
- Annual premium: $8-15K (depending on audit findings, company size, claims history)
- Underwriter audit: Sometimes free, sometimes $2-5K
- Broker commission: Usually paid by insurer (no additional cost to AlphaForge)

**Underwriter Likely Questions:**
1. "What encryption standard do you use for API keys?" (Answer: AES-256 envelope encryption)
2. "What's your incident response time for security breaches?" (Answer: <15 minutes detection, <1 hour customer notification)
3. "Do you have penetration testing?" (Answer: Annual third-party audit + ongoing bug bounty program)
4. "What's your data retention policy?" (Answer: 24-month immutable audit trail + anonymisation on deletion)

**Liability Cap in T&S:**
> "AlphaForge's maximum liability to user is limited to the lesser of: (a) user's account balance, (b) 12 months of subscription fees paid, or (c) $5M (insurance policy limit). AlphaForge is not liable for market losses or strategy underperformance."

---

### Selective Liability Examples

**AlphaForge IS Liable For:**
- ❌ Exchange API key stolen due to unencrypted storage on AlphaForge servers
- ❌ User trade executed at 50% extreme slippage due to AlphaForge routing error
- ❌ System outage preventing stop loss execution (liquidation occurs)
- ❌ Signal duplicated, causing user to double-execute same trade

**AlphaForge IS NOT Liable For:**
- ✅ Market loss ($10K account → $5K due to BTC crash)
- ✅ Strategy underperformance (backtest 2.0 Sharpe, live 0.8 Sharpe)
- ✅ Slippage from exchange latency (normal trading friction)
- ✅ Liquidation when user chooses extreme leverage (user's choice, risk engine warned)

---

## 🔒 DECISION: Insurance & Liability = $5M E&O Policy, $1M Deductible

**Action Items:**
- Week 5: CFO engages broker
- Week 10: Policy placed
- Week 11: Add liability cap language to T&S with legal counsel review
- Week 13: Deploy with insurance proof on About page

---

## Decision 7: Regulatory Disclaimers & Contextual Messaging

### 7-Point Disclaimer System

**Goal**: All required disclaimers acknowledged within 10 minutes across signup + first trade (not a 20-minute legal gauntlet).

| When | What | Format | User Action | Notes |
|------|------|--------|-------------|-------|
| **Signup (Homepage)** | Financial promotion — "This is not investment advice" | 1-sentence banner + expand link | Read + checkbox | Before account creation |
| **Signal Card** | AI model risk — "Signals may be wrong" | Tooltip on confidence % | Hover to expand | Every signal view |
| **Proof Tab** | Past performance — "Does not guarantee future results" | Text above backtest chart | Read, mandatory acknowledge | Before first trade |
| **API Connection (Futures)** | Leverage & liquidation risk | Modal popup × 5 second delay | Checkbox + 5-digit code | When connecting to perps exchange |
| **Order Preview** | Execution risk — "May fill at different price due to slippage" | Text on order confirm screen | Acknowledge + submit | Before each live trade |
| **Settings → Risk** | Model versioning — "Signals may change when AI retrains" | FAQ link + explanation | Read optional | In risk settings tab |
| **Weekly Email** | Technology risk — "System updates may affect delivery" | Bullet point in signal digest | Read optional | On every email |

---

### Disclaimer Language (Legal Review Required)

**Financial Promotion Warning** (Homepage)
```
⚠️ AlphaForge provides AI-generated trading signals as market commentary only. 
This is NOT investment advice. 
Past performance does NOT guarantee future results.
Crypto trading carries substantial risk of loss. 
Understand the risks before trading.
```

**Model Risk** (Signal Card Tooltip)
```
This signal is generated by AI. 
AI models can be wrong. 
No guarantee of accuracy or profitability.
This is recommendation, not advice.
```

**Leverage Risk** (Futures Connection Modal)
```
⚠️ LEVERAGE WARNING

Trading with leverage can result in liquidation and total loss of your account.
Example: At 5x leverage, a 20% price move liquidates your account.
Only use leverage if you understand liquidation mechanics.

Do you understand liquidation risk? [YES / NO]
```

**Execution Risk** (Order Preview)
```
Order Preview (Subject to Change)
- Entry price shown is estimated; actual execution may differ
- Slippage may occur due to market volatility
- Execution is not guaranteed; order may partially fill
- You are responsible for all market losses
```

---

## 🔒 DECISION: Disclaimers = 7-Point Contextual System

**Implementation:**
- Week 9: Draft disclaimer language with legal counsel
- Week 10: Integrate banners + tooltips + modals into UI
- Week 11: QA all flows (can't proceed without acknowledging)
- Week 12: Deploy with analytics tracking (which disclaimers convert vs abandon)

---

## Jurisdiction-Specific Compliance

### UK/EU (Primary Launch)

**GDPR Obligations:**
- Privacy policy: Describe data collection, retention, third-party sharing
- Consent: Explicit opt-in for marketing emails
- Data Subject Rights: Users can request export (30 days), deletion (30 days)
- Data Protection Officer: Not required unless "large-scale systematic monitoring"
- Data Breach Notification: Notify FCA + users within 72 hours if breach occurs
- GDPR Representative: Not required (US-based company can operate with EU contact point)

**FCA Obligations (Post-Legal Opinion):**
- If no registration required (expected outcome): Publish disclaimers + maintain audit trail
- Presumed-marketing restrictions on targeted ads (no "guaranteed returns" claims)

**Consumer Credit Directive:**
- Only applies if offering credit (e.g., leveraging user capital for trading)
- Likely NOT applicable to AlphaForge (users provide own capital)

---

### United States (Phase 4+)

**IF Investment Adviser Registration Required:**
- SEC Form ADV filing: $550 application fee + annual updates
- Form ADV Part 2 (brochure) published to clients: Disclose fees, conflicts, strategies
- Quarterly reporting on AUM + fee income
- Annual audit: 3-5 years, then every 2 years
- Chief Compliance Officer: Hire if ≥80 employees (can be part-time initially)
- Compliance calendar: File by 4/30 each year

**Restrictions if Registered:**
- Cannot misrepresent performance (SEC staff alerts on this)
- Cannot advertise past performance without benchmarks
- Must implement written compliance policies (written policies, approval for advertising)
- Must maintain records for 6 years

**IF Registered as Commodity Trading Adviser (CFTC):**
- NFA registration: $1,500 + annual renewal
- Tighter restrictions on performance claims (specific rules)
- If managing >$20M: Registered Futures Commission Merchant (RCM) may be required (higher complexity)

---

### Deferred: Asia Expansion (Phase 4+)

**Singapore (SFC Regulation):**
- MAS guidelines on algo trading: Published
- Likely: Same information-services framing works
- ID requirement: Stricter than UK (must verify address)

**Hong Kong (SFC Regulation):**
- Securities and Futures Commission: Similar to UK FCA structure
- License requirements: Likely similar to UK

---

## 22. Summary: Regulatory Framework Checklist

**Pre-Phase 1 Launch (Weeks 1-4):**
- ✅ Choose jurisdiction: UK/EU-first (recommended)
- ✅ Obtain FCA legal opinion: Clarify no registration required
- ✅ Choose copy trading framing: User-directed execution
- ✅ Decide monetisation: Subscription-first
- ✅ Finalize disclaimers: 7-point contextual system
- ✅ Arrange E&O insurance: $5M policy placed
- ✅ KYC vendor: Onfido contract signed

**Pre-MVP Launch (Weeks 5-13):**
- ✅ KYC/AML integration: Onfido API working
- ✅ Disclaimer modals: All flows QA'd
- ✅ Age verification: System blocks <18
- ✅ Data encryption: API keys,personal data encrypted at rest
- ✅ Audit trail: Append-only logging working
- ✅ T&S + Privacy Policy: Legal counsel reviewed
- ✅ Compliance training: All team members trained on restrictions

**Post-MVP (Phase 2):**
- 🔄 Marketplace governance: Policy published before beta
- 🔄 GDPR data exports: Automated export tool built
- 🔄 Tax reporting: 1099 + annual P&L export for users

**Phase 4+ (International Expansion):**
- 🔄 SEC/CFTC opinion (if US expansion): Engage counsel Q1 Year 2
- 🔄 Singapore SFC registration: Engage counsel Q3 Year 2

---

# 23. Competitive Landscape

AlphaForge positions itself against several categories of competitor.

---

## 23.1 Competitor Analysis Matrix

| Platform | Core Offering | Key Weakness | AlphaForge Opportunity |
|---|---|---|---|
| **dbtraders.com** | Deriv-specific bot builder, no-code automation, community strategies | Single exchange (Deriv only), no AI signals, no multi-exchange, basic UI | Multi-exchange, multi-asset with AI signals and full ecosystem. Directly superior scope. |
| **Bitget** | Copy trading, UEX (stocks/gold), AI assistant, futures, spot | Copy trading is from human traders, not AI-driven; AI assistant is superficial | AI-generated signals with explainability and transparent backtested track records |
| **Binance** | Massive asset selection, advanced charts, futures, options, staking | Overwhelming for beginners, no built-in AI signals, copy trading limited | Curated high-confidence signals with risk management and a simplified UX |
| **OKX** | Advanced trading, Web3 wallet, P2P — similar to Binance breadth | No transparent AI signals, no explainability, fragmented experience | Explainable AI + unified ecosystem (signals + backtesting + automation + community) |
| **eToro** | Social copy trading, multi-asset (stocks, crypto, ETFs), paper trading | Copy trading based on humans (risky followers), no AI-generated signals | AI-driven signals with rigorous backtesting and automated risk controls |
| **Pepperstone** | Forex/CFDs, tight spreads, MT4/5, cTrader, strong regulation | No crypto signals, no AI, no automation for retail | Add crypto and AI-generated signals to traditional asset base |
| **ThinkMarkets** | Forex/CFDs, proprietary ThinkTrader, tight spreads, fast execution | No AI signals, no crypto focus, no automation | Same opportunity as Pepperstone: AI + crypto focus |
| **Cryptohopper** | Automated bot creation, marketplace, backtesting, paper trading | Steep learning curve, signals are basic (not AI), dated UI, no explainability | More intuitive UX with explainability and institutional-grade analytics |

---

## 23.2 Common Market Gaps AlphaForge Addresses

No transparent, explainable AI signals  
Most platforms use human copy trading or basic technical alerts. Traders do not trust black-box signals.

No institutional-grade analytics for retail  
Platforms like Binance have data but it is not curated into actionable intelligence.

Risk management as afterthought  
Users blow up accounts because platforms lack built-in position sizing or drawdown controls.

Fragmented experience  
Traders need TradingView + Cryptohopper + exchange + signal service just to replicate what AlphaForge provides in one platform.

Poor mobile experience  
Most platforms have clunky mobile apps. Retail traders want a seamless mobile-first experience.

No unified marketplace with verifiable track records  
eToro has copy trading but it is not based on backtested, audited strategies.

---

## 23.3 AlphaForge Differentiation Summary

Key differentiators that are difficult to replicate quickly:

1. **Explainable AI signals** — reasoning shown per signal, not black box
2. **Cryptographically auditable signal history** — no result manipulation possible
3. **Risk engine before execution** — automated protection is enforced, not optional
4. **Unified ecosystem** — signals, backtesting, automation, community in one platform
5. **Institutional analytics for retail** — liquidation heatmaps, OI trends, funding extremes
6. **Verified strategy marketplace** — audited, not just claimed performance

---

# 24. Data Privacy & User Protection

---

## 24.1 Data Minimisation

AlphaForge collects only the data necessary for platform functionality.

Not collected:

- full bank account details (payment processors handle this)
- government IDs (unless required for KYC in regulated jurisdictions)

Collected:

- email
- exchange API keys (encrypted at rest, never logged in plaintext)
- trading activity (for portfolio tracking and signal performance)
- user preferences

---

## 24.2 Exchange API Key Security

API keys are the most sensitive data the platform handles.

Protection layers:

- stored in a dedicated secret vault (e.g., HashiCorp Vault or AWS Secrets Manager)
- encrypted with envelope encryption (unique data encryption key per user)
- never returned to the frontend after initial entry
- restricted to read + trade permissions — withdrawal disabled at exchange level
- key rotation notifications sent to users regularly
- keys invalidated immediately upon account deletion or user request

---

## 24.3 Third-Party Data Sharing

User data is not sold to third parties.

Data shared with third parties only to operate the platform:

- payment processor (billing only, no trading data shared)
- cloud infrastructure providers (data processed under DPA agreements)
- analytics providers (anonymised event data only)

All third-party processors must sign Data Processing Agreements (DPAs) before integration.
