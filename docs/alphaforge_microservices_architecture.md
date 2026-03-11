# AlphaForge — Microservices Architecture

Version: 1.0

---

# 1. Document Overview

This document describes the **microservices architecture** of the AlphaForge platform.

The system is designed as a **distributed event-driven platform** that processes market data, generates AI trading signals, manages risk, executes trades, and serves analytics to users.

The architecture emphasizes:

- scalability
- fault tolerance
- real-time processing
- modular development
- independent service deployment

This architecture enables AlphaForge to support **100,000+ concurrent users** while processing large volumes of financial data.

---

# 2. Microservices Architecture Philosophy

AlphaForge follows a **service-oriented architecture** where each service handles a specific responsibility.

Benefits include:

Independent scaling  
Fault isolation  
Faster development cycles  
Clear service ownership  
Better maintainability

Services communicate using:

REST APIs  
Event streams  
Message queues

---

# 3. High-Level System Layout

The platform consists of several service layers.

Market Data Layer  
↓  
Streaming & Data Processing Layer  
↓  
AI Signal Generation Layer  
↓  
Trading Execution Layer  
↓  
API Gateway Layer  
↓  
Frontend Applications

Each layer contains multiple microservices.

---

# 4. Core Microservices

The AlphaForge backend consists of the following core services.

**Core Trading Services**
- User Service / Authentication Service
- Market Data Service
- Feature Engineering Service
- Signal Engine Service
- Risk Engine Service
- Paper Trading Simulator Service
- Execution Service
- Portfolio Service

**Support Services**
- Strategy Service
- Analytics Service
- Notification Service
- Billing Service

**Compliance & Governance (Phase 1+)**
- Compliance Service (KYC/AML, audit logging)
- Marketplace Governance Service (Phase 2.5+)

**Infrastructure**
- API Gateway
- Event Streaming (Kafka/Redpanda)
- Multi-Database Infrastructure

Each service is deployed independently via Kubernetes.

---

# 5. User Service

The User Service manages all user-related data.

Responsibilities:

- User registration
- Profile management
- Subscription plans  
- User preferences
- Settings (risk configuration, exchange connections)

Database tables include:

- Users
- Profiles
- Subscriptions
- User Preferences
- Settings

---

# 6. Complance Service (NEW — Phase 1)

**Purpose**: Centralized handling of KYC/AML verification, audit logging, and regulatory compliance.

**Responsibilities**:

1. **KYC/AML Verification** – Integrate with Onfido (or similar vendor) for identity verification
   - Triggered when user attempts to enable live trading
   - Captures: Government ID photograph + proof of address
   - OFAC/PEP list screening automatic
   - Stores verification status + results in immutable audit table
   - Streams event to other services when verification complete

2. **Audit Log Management** – Write-once append-only event store
   - All authentication events (logins, 2FA, password changes, API key rotation)
   - All trading events (signal subscriptions, copy trading toggles, trade placements)
   - All account events (subscription changes, billing, email changes)
   - All admin actions (staff modifying user accounts)
   - Chain-of-custody verification (hash(previous_entry) in each new entry)

3. **Disclaimer Tracking** – Record which disclaimers user acknowledged + when
   - Financial promotion warning
   - Past performance disclaimer
   - Leverage/liquidation risk
   - Execution risk (slippage)
   - Model risk (AI can be wrong)
   - Technology risk (system updates)
   - Archives version of T&S user acknowledged

4. **Regulatory Reporting** – Support GDPR/CCPA requests
   - Data export API (user requests own data)
   - Anonymisation pipeline (user deletion → anonymise PII in audit trail)
   - Right-to-erasure implementation (30-day deletion cycle)

**Data Store**:
```
kyc_verifications table:
  user_id (FK)
  onfido_applicant_id
  onfido_check_id
  status (SUBMITTED, APPROVED, REJECTED)
  result_details (JSON)
  aml_status (CLEAR, BLOCKED, UNDER_REVIEW)
  created_at, completed_at

audit_log table:
  id (PK)
  user_id (optional FK)
  event_type (LOGIN, TRADE_PLACED, API_KEY_CREATED, etc.)
  actor (user or admin)
  timestamp
  ipv4_address
  useragent
  details (JSON: action details)
  previous_entry_hash (chain integrity)
  
disclaimer_acknowledgments:
  user_id (FK)
  disclaimer_key
  acknowledged_at
  ts_version
```

**API Endpoints**:
- `POST /kyc/verify` – Initiate KYC with Onfido
- `GET /kyc/status/{user_id}`
- `POST /audit/log` – Write to immutable audit
- `GET /audit/trail/{user_id}` – Export user's audit trail
- `POST /disclaimers/acknowledge` – Record disclaimer acknowledgment

**Events Subscribed To**:
- `user.created` → Check if live trading intended
- `trade.placed` → Log to audit trail  
- `api_key.rotated` → Log to audit trail
- `signal.subscribed` → Record disclaimer timestamp

---

  
Subscriptions  
Settings  

---

# 6. Authentication Service

Handles platform security.

Responsibilities:

Login and authentication  
JWT token issuance  
Two-factor authentication  
Session validation  

Security features include:

Password hashing  
Token expiration  
Rate limiting

---

# 7. Market Data Service

This service collects and processes real-time market data from exchanges.

Responsibilities:

Exchange WebSocket connections  
Market feed aggregation  
Data normalization  
Streaming data to Kafka topics

Data sources include:

Price feeds  
Order books  
Funding rates  
Open interest  

The service must be highly optimized for low latency.

---

## 7.1 Backup Market Data Providers

Exchange feeds are supplemented or replaced by institutional-grade data providers during downtime or data quality failures.

Integrated backup providers:

**Polygon.io** — crypto and equities, normalised and deduplicated feeds  
**CoinAPI** — unified API across 300+ exchanges with historical backfill  
**Kaiko** — institutional tick data and order book analytics

Failover logic:

- primary exchange feed monitored by the Data Validation Service
- if anomalies exceed threshold, the Market Data Service switches to backup provider automatically
- failover events are logged and alerted to operations team
- automatic switchback to primary feed once data quality is restored

---

## 7.2 Data Validation Service (Embedded)

The Market Data Service includes an embedded validation pipeline that runs before any data is published to Kafka.

Validation steps executed per message:

1. **Deduplication** — events are deduplicated using exchange sequence IDs and timestamps; duplicate events within a 60-second window are dropped and logged
2. **Gap detection** — missing candles or timestamp gaps above a configured threshold trigger a gap event on a dedicated Kafka topic
3. **Outlier detection** — price values that deviate more than 5 standard deviations from the rolling 100-period mean are quarantined and not forwarded to the feature engineering pipeline
4. **Clock skew check** — exchange timestamps must be within ±500ms of server UTC; events outside this window are flagged
5. **Cross-venue consistency** — for multi-exchange assets, price divergence exceeding 0.5% is logged as a data quality alert

Output topics:

`market.data.validated` — clean, validated data for downstream consumption  
`market.data.anomalies` — quarantined events for retrospective analysis  
`market.data.gaps` — gap events for monitoring and alerting

---

# 8. Feature Engineering Service

Transforms raw market data into machine learning features.

Responsibilities:

Compute technical indicators  
Generate volatility metrics  
Create order flow indicators  
Store features in feature store  

Examples of generated features:

RSI  
MACD  
EMA  
ATR  
order book imbalance  
volatility metrics  

These features feed into the AI signal engine.

---

# 9. Signal Engine Service

This service runs the machine learning models that generate trading signals.

Responsibilities:

Load ML models  
Process feature vectors  
Generate signals  
Assign confidence scores  

Output example:

Asset: BTCUSDT  
Signal: LONG  
Entry: 63,200  
Stop Loss: 62,100  
Take Profit: 65,200  
Confidence: 74%

Signals are then passed to the Risk Engine.

---

# 10. Risk Engine Service

Ensures trades meet defined risk limits before execution (non-negotiable enforcement).

**Core Responsibilities**:

- Position sizing calculation (2% max per trade)
- Portfolio exposure checks (20% max per asset)
- Leverage limits (5x max for perps Phase 1, 10x Phase 2)
- Stop loss enforcement (required on all orders)
- Liquidation buffer validation (20% cushion for perpetuals)
- Risk scoring algorithm
- Volatility-adjusted position sizing

**Risk Rules (Phase 1)**:

**Spot Trading**:
- Max position size: 2% of account balance
- Portfolio exposure limit: 20% per asset
- Stop loss: Required (system rejects without SL)

**Perpetuals Trading** (Important: Explicit perpetuals scope added):
- Max leverage: 5x (Phase 1)
- Max position margin: 2% of account
- Liquidation buffer: Price moves >20% would trigger liquidation → reject
- Liquidation price calculation: 
  - Formula: Liquidation Price = (Entry Price - (Margin * Entry Price / Position Size)) * Leverage
  - System checks: If (Liquidation Price - Mark Price) < (Mark Price * 0.20) → Reject
- Funding rate alert: Warn if >1% daily
- Auto-close on extreme: Optional user setting (close all if daily loss >X%)

**Algorithm**:
```
Risk Score =
  (Position Size % × Leverage × Vol Index × (1 - Sharpe Ratio)) +
  Correlation Risk +
  Liquidity Risk

Score > 8.0 → REJECT
Score 6-8 → WARN user
Score < 6 → APPROVE
```

**Volatility Adjustment**:
```
adjusted_size = base_size × (20-day_vol / 60-day_avg_vol)
```

If current IV is 3× historical, position reduced to 33%.

**Data Flow**:
```
Signal received
    ↓
Check position size OK?
    ├─ NO → Reject, alert user
    ├─ YES ↓
Check portfolio exposure OK?
    ├─ NO → Reject, alert user
    ├─ YES ↓
Check leverage OK? (if perps)
    ├─ NO → Reject, alert user
    ├─ YES ↓
Check stop loss defined?
    ├─ NO → Reject, alert user
    ├─ YES ↓
Calculate risk score
    ├─ REJECT (score>8) → Reject
    ├─ WARN (score 6-8) → Log warning, append to portfolio risk dashboard
    ├─ APPROVE (score<6) ↓
✅ PASS to Execution Engine
```

---

# 10.1 Paper Trading Simulator Service (NEW — Phase 1)

**Purpose**: Validate signals on live market data without real capital risk. Gate paper trading performance: Only signals achieving ≥80% of backtest Sharpe advance to live users.

**Responsibilities**:

1. **Shadow Mirroring** – Mirror live signals in real-time
   - Signal fires 15:30 UTC: Entry 63,200, SL 62,100, TP 65,000
   - Paper engine records entry at market price + 0.1% slippage
   - Position tracked separately from live positions

2. **Simulated Execution**
   - Entry: Market price + 0.1% slippage (realistic for retail)
   - Exit: Exact price if SL or TP hit
   - Liquidation: Simulated if leverage exceeded (perpetuals)
   - Partial fills: Not simulated (assume full fill)

3. **Performance Tracking**
   - Same metrics as live: Win rate, Sharpe, drawdown, profit factor
   - Measured weekly
   - Compared to backtest baseline

4. **Signal Approval Gate** (Internal Signals)
   - Duration: 4 weeks minimum per signal
   - Pass criterion: Live Sharpe ≥ 80% of backtest Sharpe
   - Example: Backtest 1.5 Sharpe → need ≥1.2 in paper to approve
   - YES → Approve for live users; NO → Back to R&D

5. **User Paper Trading**
   - Unlimited duration (no time gate)
   - No account minimum
   - Free during 7-day trial
   - Conversion prompts: Day 14, 21, 28 (with 30% first-month discount)
   - Users see paper vs live side-by-side

**Data Storage**:
```
paper_trades table:
  signal_id (FK)
  user_id (FK or NULL if internal validation)
  asset
  side (LONG/SHORT)
  entry_price, entry_time
  exit_price, exit_time
  pnl
  status (OPEN, CLOSED, LIQUIDATED)
  is_internal_validation (boolean)
  created_at
```

**Paper to Live Conversion Flow**:
```
User clicks "Trade Live"
    ↓
System prompts: "Connect exchange API"
    ↓
API key + test mode submission
    ↓
Risk disclosure modal (5-digit code required)
    ↓
30% off Month 1 offer displayed
    ↓
New live portfolio created (separate from paper)
    ↓
Paper positions remain visible for comparison
    ↓
First live trade requires KYC verification
```

**Approval Recommendation Display**:
- After 4-week internal paper trading: Public "Proof" tab shows
  - Backtest chart (equity curve) + metrics
  - Paper trading results (4-week live validation)
  - Hypothesis commitment timestamp (blockchain or hash proof)
  - Status: PASSED or FAILED

---



Handles automated trade placement.

Responsibilities:

Exchange API communication  
Order creation  
Order monitoring  
Retry logic  

Execution workflow:

Signal received  
↓  
Position size calculated  
↓  
Trade placed on exchange  
↓  
Order confirmation received  
↓  
Portfolio updated  

---

## 11.1 Idempotency & Duplicate Order Prevention

Duplicate order placement is the highest-risk failure mode in automated trading.

**Idempotency Key Design**

Every order is assigned an idempotency key before it is submitted to an exchange.

Key format:

`{user_id}:{signal_id}:{asset}:{direction}:{timestamp_ms}`

Key lifecycle:

- key is written to Redis with a 24-hour TTL before the order is placed
- if the same key already exists, the order is rejected at the service layer and not forwarded to the exchange
- key includes the signal ID to scope idempotency to a specific signal event, not just an asset direction pair

**Order Confirmation Monitoring**

Order confirmation is tracked with a state machine:

| State | Description |
|---|---|
| `PENDING` | Order submitted to exchange, awaiting confirmation |
| `CONFIRMED` | Exchange acknowledged the order |
| `FILLED` | Order fully executed |
| `PARTIAL_FILL` | Order partially executed |
| `FAILED` | Exchange rejected the order |
| `PENDING_CONFIRMATION` | No confirmation received within timeout window |

If an order does not reach `CONFIRMED` within 5 seconds:

- state is set to `PENDING_CONFIRMATION`
- operations alert is fired immediately
- system does NOT auto-retry — unconfirmed orders require human review
- the position is not reflected in the portfolio until confirmation is received

**Exchange Abstraction Layer**

All exchange communication is routed through a unified abstraction layer.

Features:

- rate limit management with token bucket algorithm
- exponential backoff with jitter (base: 500ms, max: 30s) on transient errors
- circuit breaker per exchange: opens after 10 consecutive failures, auto-closes after 60-second recovery window
- dual-channel: REST as primary, WebSocket for order status updates
- circuit breaker state exposed via health check endpoint for monitoring dashboards

---

# 12. Portfolio Service

Tracks all user trading activity.

Responsibilities:

Account balances  
Open positions  
Trade history  
Realized PnL  
Unrealized PnL  

This service powers the portfolio dashboard.

---

# 13. Strategy Service

Manages trading strategies and signal logic.

Responsibilities:

Strategy configuration  
Strategy performance tracking  
Strategy metadata  

Future functionality:

Strategy marketplace  
User-created strategies  

---

# 14. Analytics Service

Provides advanced market and portfolio analytics.

Responsibilities:

Signal performance metrics  
Strategy performance analysis  
Market analytics dashboards  

Metrics calculated include:

Win rate  
Sharpe ratio  
Profit factor  
Maximum drawdown  

---

# 15. Notification Service

Responsible for sending real-time alerts.

Notification channels include:

Web push notifications  
Telegram alerts  
Discord alerts  
Email notifications  

Signals must be delivered within seconds.

---

# 16. Billing Service

Handles platform monetization.

Responsibilities:

Subscription management  
Payment processing  
Plan upgrades  
Usage tracking  

Supported billing models:

Monthly subscriptions  
Profit-sharing model  
API access fees

---

# 17. API Gateway

The API Gateway acts as the central entry point for clients.

Responsibilities:

Route requests to services  
Handle authentication  
Rate limiting  
Request validation  

Example endpoints:

/api/signals  
/api/trades  
/api/portfolio  
/api/analytics  
/api/strategies  

---

# 18. Event Streaming Architecture

AlphaForge uses an **event-driven architecture**.

Events are transmitted through a streaming platform.

Example pipeline:

Market Data Collectors  
↓  
Kafka Topics  
↓  
Feature Engineering Workers  
↓  
Signal Engine  
↓  
Risk Engine  
↓  
Execution Engine  

This allows services to process events asynchronously.

---

# 19. Database Architecture

AlphaForge uses multiple specialized databases.

---

## Transaction Database

Stores platform data.

Recommended:

PostgreSQL.

Data includes:

Users  
Trades  
Signals  
Subscriptions  

---

## Time-Series Database

Stores historical market data.

Recommended:

ClickHouse or TimescaleDB.

Used for:

price history  
volume  
market indicators  

---

## Feature Store

Stores ML feature data.

This ensures consistent model inputs across training and production.

---

## Cache Layer

Redis is used for:

session caching  
real-time signals  
API response caching  

---

# 20. Containerized Deployment

All services run inside containers.

Each microservice is packaged as a Docker container.

Advantages:

portable deployments  
environment consistency  
easy scaling  

---

# 21. Kubernetes Orchestration

Kubernetes manages container deployment.

Responsibilities:

Service scaling  
Load balancing  
Self-healing containers  
Rolling updates  

Clusters are divided into:

Development environment  
Staging environment  
Production environment  

---

# 22. CI/CD Pipeline

Continuous Integration and Continuous Deployment automate updates.

Pipeline stages:

Code commit  
↓  
Automated tests  
↓  
Container build  
↓  
Deployment to staging  
↓  
Production rollout  

This ensures safe and reliable releases.

---

# 23. Observability and Monitoring

Monitoring ensures system health.

Key metrics include:

Signal generation latency  
API response times  
Execution success rate  
System resource usage  

Observability tools include:

Centralized logging  
Distributed tracing  
Error monitoring  

---

# 24. Scalability Strategy

AlphaForge scales horizontally.

Scaling layers include:

API servers  
Signal workers  
Market data collectors  
execution workers  

Load balancers distribute traffic across services.

---

# 25. Fault Tolerance

The system must remain operational even during failures.

Strategies include:

Message queue buffering  
Retry mechanisms  
Circuit breakers  
Service isolation  

Example scenario:

If an exchange API fails, execution workers retry automatically.

---

# 26. Future Platform Expansion

As the platform grows, additional services may include:

AI Research Service  
Strategy Marketplace Service  
Sentiment Analysis Service  
Multi-Asset Trading Service  

---

## 26.1 Sentiment Analysis Service

Crypto markets are heavily influenced by social media and news events. The Sentiment Analysis Service provides an additional signal layer beyond technical indicators.

**Data Sources**

| Source | Data Type | Collection Method |
|---|---|---|
| Twitter/X | Mentions of assets, influencer tweets | Filtered stream API |
| Reddit | r/CryptoCurrency, r/Bitcoin, relevant subs | PRAW or Pushshift API |
| Telegram | Public trading channels | Telegram Bot API |
| News feeds | Reuters, CoinDesk, CoinTelegraph | RSS + web scraping |
| On-chain data | Whale movements, exchange inflows/outflows | Glassnode API, Dune Analytics |

**NLP Pipeline**

1. Raw text collected and published to `sentiment.raw` Kafka topic
2. NLP worker processes each message using:
   - **FinBERT** — fine-tuned BERT model for financial sentiment (bullish/bearish/neutral)
   - **VADER** — rule-based fallback for high-throughput, low-latency scoring
3. Sentiment scores aggregated over rolling windows (1h, 4h, 24h) per asset
4. Aggregated scores stored in the feature store as additional features for the signal engine

**On-Chain Metrics (Glassnode / Dune Analytics)**

On-chain signals include:

- exchange inflows — large inflows to exchanges often precede sell pressure
- exchange outflows — large outflows suggest accumulation/cold storage
- whale wallet movements — wallets holding >1000 BTC transaction events
- stablecoin supply — rising stablecoin supply on-chain indicates dry powder for buying

These metrics are available at hourly resolution and are added as features alongside technical indicators.

---

## 26.2 Strategy Marketplace Service (Phase 3)

Responsibilities:

- strategy submission and review pipeline
- verification badge assignment (after audit)
- performance leaderboard with standardised metrics
- creator revenue share calculation
- paper-trade-before-copy flow enforcement
- reputation score management

Verification process:

1. creator submits strategy with backtest reports
2. AlphaForge audit service reruns backtest on its own data to verify claims
3. strategy is assigned a verification badge if claims are validated within 5% tolerance
4. strategy enters 4-week paper trading gate before live copy trading is enabled
5. creator reputation score updated based on live performance

---

# 27. Architecture Summary

AlphaForge uses a modern **cloud-native microservices architecture** designed for:

Real-time financial data processing  
AI-driven signal generation  
secure automated trading  
large-scale user analytics  

This architecture allows AlphaForge to evolve into a **full institutional-grade trading intelligence platform for retail traders**.

---

# 28. Audit Log Service

A dedicated Audit Log Service provides an immutable, append-only record of all security-relevant and operationally significant events across the platform.

---

## 28.1 Events Captured

**Authentication & Access**

- user logins (success and failure, with IP and user agent)
- 2FA verification attempts
- session creation and expiration
- password changes
- API key creation, rotation, and deletion

**Trading & Execution**

- signal subscription activations and deactivations
- copy trading enabled or disabled
- each order placement with idempotency key logged
- order confirmation events
- trade fills with price and quantity

**Account & Billing**

- subscription plan changes
- payment events (success and failure)
- email and profile changes

**Admin Events**

- all staff actions performed on user accounts
- feature flag changes
- system configuration changes

---

## 28.2 Storage & Integrity

Audit logs are written to an append-only store.

Options:

- AWS CloudTrail + S3 with Object Lock (WORM)
- dedicated PostgreSQL audit table with row-level security (no UPDATE or DELETE permissions for application role)
- OpenTelemetry log pipeline to an immutable observability backend (e.g., Grafana Loki with retention lock)

Integrity guarantees:

- each log entry includes a hash of the previous entry (linked-list integrity check)
- daily integrity verification job confirms the log chain has not been tampered with
- logs retained for minimum 24 months

---

## 28.3 Access

- users can view their own audit log via the settings dashboard
- platform staff can query logs via an internal admin tool
- logs are exported on request for regulatory or legal proceedings
- no application code path has UPDATE or DELETE access to the audit log table
