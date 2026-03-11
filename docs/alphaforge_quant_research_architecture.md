# AlphaForge — Quantitative Research & Alpha Generation Architecture

Version: 1.0

---

# 1. Document Overview

This document describes the **Quantitative Research Architecture** used by AlphaForge to discover, validate, and deploy profitable trading signals.

The architecture is inspired by the workflows used by quantitative trading firms such as:

- Renaissance Technologies
- Two Sigma
- Citadel
- Jane Street

The goal is to build a scalable system that continuously:

1. Collects market data
2. Generates trading features
3. Discovers predictive signals
4. validates strategies
5. deploys profitable models

This process is commonly referred to as **alpha research**.

---

# 2. What is Alpha?

In finance, **alpha** represents a strategy's ability to outperform the market.

Example:

If Bitcoin rises 5% but a strategy produces 12% returns, the strategy generated **7% alpha**.

The mission of AlphaForge is to systematically discover and deploy **alpha-generating trading strategies**.

---

# 3. Quant Research System Overview

The AlphaForge research pipeline consists of several layers:

Market Data Layer  
↓  
Feature Engineering Layer  
↓  
Alpha Research Layer  
↓  
Strategy Testing Layer  
↓  
Portfolio Construction Layer  
↓  
Signal Deployment Layer

Each layer performs a specific function in the signal discovery pipeline.

---

# 4. Market Data Layer

The foundation of any trading intelligence platform is **high-quality market data**.

AlphaForge collects multiple data types from exchanges.

## 4.1 Data Sources

Market data includes:

Price Data  
Open  
High  
Low  
Close  
Volume  

Order Book Data  
Bid depth  
Ask depth  
Spread  

Derivatives Data  
Funding rates  
Open interest  
Liquidations  

Market Sentiment Data  
Fear and greed index  
Social media signals  
News sentiment

---

## 4.2 Data Provider Strategy

High-quality data is the foundation of signal quality. AlphaForge does not rely exclusively on direct exchange feeds.

**Primary source:** Exchange WebSocket feeds for real-time data.

**Secondary source:** Institutional-grade data providers for redundancy, normalisation, and historical backfill.

---

## 4.3 Data Quality SLA & Failover

Market data is the lifeblood of signal generation. Gaps, latency spikes, or corrupted data directly impact signal quality.

**SLA Standards**

| Metric | Target | Action If Breached |
|---|---|---|
| Data availability | 99.8% | Auto-failover to secondary provider within 5s |
| Real-time latency | ≤100ms (P99) | Alert raised; failover initiated if >500ms |
| Gap detection (missing candles) | <1% | Backfill from archive; quarantine affected signals |
| Data duplication rate | <0.1% | Deduplicate before feature engineering |
| Clock skew tolerance | ±1s | Reconcile against NTP time servers |

**Failover Logic**

1. Binance (primary) → CoinAPI (secondary) → Kaiko (tertiary)
2. Automatic detection of data gaps >30 seconds
3. Trigger secondary provider ingestion within 5 seconds
4. Quarantine signals generated during gap period (do not execute)
5. Log incident for post-crisis analysis

Recommended providers:

| Provider | Strength | Use Case |
|---|---|---|
| **Polygon.io** | Crypto and equities, normalised feeds | Real-time backup, historical fills |
| **CoinAPI** | 300+ exchanges, unified API | Deduplication, anomaly filtering |
| **Kaiko** | Institutional tick data | Order book analytics, historical research |
| **Glassnode** | On-chain metrics | Whale movements, exchange inflows/outflows |
| **Dune Analytics** | On-chain SQL queries | Custom on-chain metric research |

Data quality directly determines signal quality. A data validation layer runs upstream of the feature engineering pipeline to detect gaps, outliers, duplicates, and clock-skew issues before data enters the model.

---

# 4.2 Data Frequency

AlphaForge stores data at multiple time resolutions:

Tick Data  
1-second data  
1-minute candles  
5-minute candles  
15-minute candles  
1-hour candles  
Daily candles

This allows models to detect patterns across different time horizons.

---

# 5. Feature Engineering Layer

Raw market data is converted into **predictive features**.

Features are inputs used by machine learning models.

---

## 5.1 Technical Indicator Features

Common indicators include:

Relative Strength Index (RSI)

Moving Average Convergence Divergence (MACD)

Exponential Moving Averages (EMA)

Average True Range (ATR)

Bollinger Bands

Momentum indicators

---

## 5.2 Order Flow Features

Order book data can reveal hidden market pressure.

Examples:

Order book imbalance

Bid/ask depth ratios

Large order detection

Liquidity walls

---

## 5.3 Volatility Features

Volatility often predicts market behavior.

Examples:

Rolling volatility

ATR-based volatility

Volatility regime detection

---

## 5.4 Trend Features

Trend strength indicators include:

Moving average slope

Breakout strength

Momentum persistence

---

## 5.5 Market Regime Classification

Markets behave differently depending on conditions.

The system classifies market regimes into:

Bull trend

Bear trend

Sideways market

High volatility regime

Low volatility regime

Models adapt signals depending on the regime.

---

## 5.6 Feature Importance Tracking & Drift Detection

Features degrade in quality over time. A feature that was predictive in 2023 may become decorrelated in 2024.

**Feature Importance Tracking**

For each model in production, track feature importance monthly:

| Feature | Importance (%) | 1M ago | Status |
|---|---|---|---|
| RSI_14 | 18.3% | 22.1% | WARNING Declining |
| OB_Imbalance | 21.4% | 19.1% | OK Stable |
| Sentiment_4h | 8.2% | 15.3% | CRITICAL drop |
| Funding_Rate | 15.1% | 14.8% | OK Stable |
| ATR_Volatility | 11.0% | 12.5% | OK Stable |

**Drift Detection Algorithm**

1. Calculate importance change: Delta = (New - 1M Ago) / 1M Ago
2. If Delta < -20% = Yellow alert (feature degrading)
3. If Delta < -40% = Red alert (feature critical drop)
4. Investigate features with drops >40%:
   - Is feature still predictive? (Run mini-backtest)
   - Has market regime changed? (Check regimes)
   - Is data source corrupted? (Validate data quality)
5. Action items:
   - Yellow: Monitor weekly, prepare replacement features
   - Red: Disable feature immediately, escalate to researcher

---

# 6. Alpha Research Layer

This layer attempts to **discover predictive relationships in market data**.

The goal is to find signals that predict future price movement.

---

## 6.1 Signal Types

Signals fall into several categories.

Momentum Signals

Example:

Price breaking above resistance.

Mean Reversion Signals

Example:

RSI oversold bounce.

Volatility Breakout Signals

Example:

ATR expansion followed by directional movement.

Order Flow Signals

Example:

Large buy pressure in order book.

---

## 6.2 Alpha Hypothesis

Quant research starts with a hypothesis.

Example hypothesis:

"If open interest rises while funding rates become negative, a short squeeze is likely."

The system tests this hypothesis on historical data.

---

# 7. Machine Learning Models

AlphaForge uses machine learning models to predict market movements.

---

## 7.1 Initial Models

Gradient Boosting models

Random Forest models

These models work well on financial tabular data.

---

## 7.2 Deep Learning Models (Future)

Advanced models may include:

LSTM neural networks

Transformer architectures

Temporal convolution networks

These models are capable of detecting complex time-series patterns.

---

# 8. Ensemble Prediction System

Instead of relying on a single model, AlphaForge combines predictions from multiple models.

Example ensemble:

Gradient Boosting model  
Random Forest model  
Deep Learning model  

The final signal confidence is derived from model agreement.

Ensemble models typically improve robustness and accuracy.

---

## 8.1 Ensemble Weighting & Conflict Resolution

When multiple models disagree, the ensemble must decide: which signals take priority?

**Model Weighting Strategy**

| Model | Base Weight | Track Record Bonus | Current Weight |
|---|---|---|---|
| Gradient Boosting | 40% | +5% (30-day Sharpe >= 1.2) | 45% |
| Random Forest | 35% | 0% (neutral track record) | 35% |
| FinBERT Sentiment | 15% | +5% (corr +0.32 vs price) | 20% |
| Deep Learning | 10% | 0% (under validation) | 10% |

**Conflict Resolution Rules**

1. Unanimous Agreement: All models bullish/bearish = Signal confidence 95%
2. 3-of-4 Agreement: Majority vote = Signal confidence 75%
3. Split Vote (2-of-4): Abstain = No signal generated (conflict)
4. Single Model: If other models unavailable = Signal confidence 40% (no mandate)

**Confidence Cap Limits**

- Max confidence: 95% (never 100% - preserve optionality)
- Min confidence threshold for execution: 50% (below this = no signal)
- Declining confidence requires human review if <60%

---

# 9. Strategy Testing Layer

Before deployment, strategies must be tested extensively.

This process is known as **backtesting**.

---

## 9.1 Backtesting Process

Historical data is used to simulate trading.

Process:

Historical market data  
↓  
Strategy logic applied  
↓  
Simulated trades executed  
↓  
Performance metrics calculated

---

## 9.2 Key Evaluation Metrics

Strategies are evaluated using multiple metrics.

Win Rate

Percentage of profitable trades.

Profit Factor

Ratio of total profits to total losses.

Maximum Drawdown

Largest peak-to-trough decline.

Sharpe Ratio

Risk-adjusted return.

Sortino Ratio

Downside-risk-adjusted return.

---

## 9.3 Hyperparameter Management & Versioning

Models are defined by hyperparameters (learning rate, tree depth, ensemble size, etc.). Different hyperparameters produce different results. For reproducibility, all hyperparameters must be versioned.

**Model Versioning Rules**

- Minor changes (preprocessing): Increment patch version (v3.2.0 to v3.2.1)
- Model tune changes (hyperparameters): Increment minor version (v3.2.0 to v3.3.0)
- Major algorithmic changes (new model class): Increment major version (v3.0.0 to v4.0.0)
- All versions are immutable once committed
- Every deployed version has a git commit hash for reproducibility

**Reproducibility Guarantee**

Given a model version + git commit + training data hash:
1. Anyone can reconstruct the exact model weights
2. Anyone can reproduce the backtest results
3. Results must match the logged audit entry (cryptographic verification)

---

# 10. Overfitting Prevention

Overfitting occurs when a model performs well on historical data but fails in real markets.

AlphaForge prevents overfitting using:

Walk-forward validation

Out-of-sample testing

Cross validation

Robust feature selection

---

## 10.1 Look-Ahead Bias Prevention

Look-ahead bias occurs when a model is accidentally trained on data that would not have been available at prediction time. It is one of the most common and damaging errors in quantitative research.

Prevention measures:

- all features are computed using only data available strictly before the signal timestamp
- rolling window calculations explicitly use `t-1` and earlier data only — the current bar is always excluded
- labels (future price movement) are generated post-hoc and stored in a separate, access-controlled feature namespace
- a static analysis check runs during feature pipeline builds to flag any feature that references a future data point
- code review policy: any feature engineering PR must be reviewed by a second researcher for look-ahead issues before merge

---

## 10.2 Survivorship Bias Prevention

Survivorship bias occurs when a backtest only includes assets or strategies that survived to the end of the test period, ignoring those that failed or were delisted.

Prevention measures:

- the historical data store includes delisted, failed, and low-liquidity assets alongside active ones
- backtests operate on a universe snapshot at each historical timestamp, not the current asset universe
- strategies are not allowed to be cherry-picked after seeing results — the strategy hypothesis must be logged before the backtest is run
- all backtest runs are logged (see §10.4) and the original hypothesis is locked before execution begins

---

## 10.3 Purged Walk-Forward Validation

Standard walk-forward validation can still leak information between train and test sets in time-series data because adjacent observations are often autocorrelated.

AlphaForge uses **purged walk-forward** validation:

- a **purge gap** (embargo period) is added between the training set and the test set
- the purge gap removes all observations within a rolling window around each test observation from the training set
- default purge gap: 5 days for daily models, 24 hours for hourly models

This eliminates label leakage caused by overlapping forward-return labels across adjacent time periods.

---

## 10.4 Holdout Set Policy

A holdout (purged test) set is maintained for each asset and strategy class.

Rules:

- the holdout set covers the most recent 10% of available historical data
- the holdout set is never used during model development, hyperparameter tuning, or feature selection
- it is touched only once: for final validation before a model is submitted for production approval
- touching the holdout set terminates its purity for that research cycle; a new holdout must be defined for the next cycle
- holdout set access is logged per researcher per model version

---

## 10.5 Cryptographic Audit Log of Model Versions

To ensure trust, reproducibility, and accountability, all backtest results and model versions are recorded in a tamper-evident audit log.

Each log entry captures:

- model version hash (SHA-256 of serialised model weights)
- training data range and data fingerprint (hash of train set)
- validation data range and data fingerprint
- hyperparameters used
- full backtest performance metrics
- researcher ID and timestamp
- strategy hypothesis (recorded before any backtest is run)

The audit log is:

- append-only — entries cannot be modified or deleted
- signed with the researcher's cryptographic key
- stored in a separate, access-controlled database with no write access from application code

This log serves as the ground truth for performance claims. Any published strategy performance metric must be backed by a matching audit log entry.

---

# 11. Portfolio Construction Layer

Signals must be combined into a portfolio.

This layer determines:

Position sizing

Strategy weighting

Risk exposure

Capital allocation

---

## 11.1 Position Sizing

Typical rule:

Risk no more than **1–2% of capital per trade**.

---

## 11.2 Diversification

Signals are diversified across:

Multiple assets

Multiple strategies

Multiple timeframes

Diversification reduces drawdown risk.

---

# 12. Signal Deployment Layer

Once validated, signals are deployed to the production system.

Deployment pipeline:

Research environment  
↓  
Model validation  
↓  
Strategy approval  
↓  
Production signal engine  

Signals then appear on the AlphaForge platform.

---

## 12.1 Paper Trading Gate

Every new model or strategy must pass a **mandatory paper trading gate** before it is allowed to generate live signals.

Gate requirements:

| Requirement | Threshold |
|---|---|
| Minimum paper trading duration | 2 weeks (minimum), 4 weeks (recommended) |
| Minimum number of signal events | 20 signals |
| Win rate vs backtest baseline | Within ±5% |
| Max drawdown vs backtest baseline | No more than 20% worse |
| Confidence score distribution | Matches backtested confidence distribution |

Gate process:

1. Model exits validation with a passing holdout set result
2. Model is deployed to the paper trading environment (live market data, no real execution)
3. Performance is monitored daily by the quant team
4. At end of gate period, a go/no-go decision is made by the research lead
5. If approved, the model enters production signal engine
6. If rejected, the model returns to research with a written postmortem

This gate exists to catch models that passed backtesting but show degraded performance in live market conditions — a common failure mode known as **model decay on deployment**.

---

## 12.2 Production Monitoring After Deployment

Deployment is not the end of the lifecycle. Models are continuously monitored in production.

Alerts fire automatically when:

- win rate drops more than 10% below the rolling 30-day average
- model confidence scores diverge significantly from historical distribution (distribution shift)
- signal frequency drops or spikes beyond expected ranges
- drawdown limit on signals is breached

Auto-disable policy:

If a model triggers two consecutive weekly performance alerts, it is automatically disabled pending quant team review.

---

# 13. Continuous Learning System - Retraining Policy & Governance

Markets evolve constantly.

Models must adapt.

AlphaForge continuously retrains models using new data.

**Retraining Triggers**

| Trigger | Action | Frequency |
|---|---|---|
| Sharpe drops >20% | Immediate retraining | On-demand |
| Data regime shift detected | Retrain on new regime | Weekly check |
| Quarterly holdout refresh | Update validation set | Quarterly |
| New data accumulation | Retrain with 3-6 months new data | Monthly |
| Feature importance drift | Review & retune features | Monthly |
| Model age > 12 months | Mandatory full rebuild | Annual |

**Retraining Validation Gate**

When a model is retrained:

1. Train on 80% of data (new window)
2. Validate on 20% holdout set (rotated holdout)
3. Compare new holdout performance vs old holdout baseline
4. If new Sharpe < 80% of old Sharpe = REJECT retrain (keep old model)
5. If new Sharpe >= 80% baseline = ACCEPT retrain (deploy new version)
6. Log decision with versioning info

**Holdout Rotation Policy**

- Each quarter, advance the holdout window 3 months forward
- Never reuse a holdout set in the same calendar year
- Archive all historical holdout results for trend analysis

---

# 14. Strategy Performance Monitoring

Every strategy is continuously evaluated.

Metrics monitored include:

Win rate

Drawdown

Profit factor

Trade frequency

Strategies that underperform are automatically disabled.

---

# 15. Alpha Decay - Monitoring & Retirement

Most trading strategies lose effectiveness over time. This is known as **alpha decay**.

**Alpha Decay Detection**

| Phase | Indicators | Actions |
|---|---|---|
| Phase 1: Decay Detected | Live Sharpe drops to 80% of backtest | Yellow alert; increase monitoring |
| Phase 2: Significant Decay | Live Sharpe drops to 60% of backtest | Orange alert; prepare replacement; reduce position size |
| Phase 3: Critical Decay | Live Sharpe drops to 40% of backtest | Red alert; begin user notification; schedule retirement |
| Phase 4: Retirement | Live Sharpe <30% of backtest persistently | Auto-disable signal; retire from marketplace |

**Retirement Workflow**

1. **Quarantine Phase** (Duration: 2 weeks)
   - Signal marked as "under review"
   - New user subscriptions disabled
   - Existing users notified in-app
   - Performance monitored daily for recovery opportunity

2. **Notification Phase** (Duration: 1 week)
   - Email sent to all subscribers
   - In-app banner with retirement date
   - Recommendation for replacement signals shown

3. **Retirement Phase**
   - Signal deleted from marketplace
   - Creator notified with postmortem analysis
   - Creator retains 50% of month's subscription payout (consolation)
   - Historical performance remains visible (archive)

4. **Postmortem Analysis**
   - Why did signal decay?
   - Was fundamental broken or just bad luck?
   - Could it be salvaged with retraining?
   - Logged for pattern analysis across all retired signals

To counter alpha decay:

AlphaForge continuously researches new strategies and retires weak ones.

---

# 16. Strategy Marketplace

In later platform phases, AlphaForge will support a **strategy marketplace**.

Users can publish strategies.

Other traders can subscribe or copy them.

Example leaderboard:

Momentum Alpha  
ROI: +124%

Volatility Hunter  
ROI: +78%

Mean Reversion Pro  
ROI: +65%

Strategy creators receive revenue share.

---

# 17. Future Research Directions

Advanced research areas include:

AI-driven strategy discovery

Reinforcement learning trading agents

Multi-exchange arbitrage

Market microstructure analysis

Sentiment-driven trading

---

# 18. Long-Term Vision

The AlphaForge research system evolves into a **fully automated quant research lab**.

Future capabilities:

Autonomous strategy discovery

Continuous AI retraining

Cross-market intelligence

Global multi-asset trading analytics

The long-term goal is to create the most advanced **AI trading intelligence platform for retail traders**.

---

# 19. Alternative Data & Sentiment Analysis

Crypto markets are uniquely influenced by social media, news events, and on-chain behaviour. Alternative data provides an edge over strategies that rely solely on price and volume.

---

## 19.1 Social Sentiment Pipeline

**Data Sources**

| Source | Assets Covered | Collection |
|---|---|---|
| Twitter/X | All major assets | Filtered stream API (cashtags, $BTC etc.) |
| Reddit | Bitcoin, Ethereum, altcoins | r/CryptoCurrency, r/Bitcoin, asset-specific subs |
| Telegram | Crypto trading assets | Public channel monitoring via Telegram Bot API |
| News | All assets | Reuters, CoinDesk, CoinTelegraph RSS + scraping |

**NLP Models**

| Model | Type | Use Case |
|---|---|---|
| **FinBERT** | Transformer, fine-tuned on financial text | Accurate bullish/bearish/neutral classification |
| **VADER** | Rule-based lexicon | High-throughput fallback for low-latency scoring |

Pipeline:

Raw social text  
↓  
Cleaning (remove noise, bots, spam)  
↓  
NLP sentiment scoring (FinBERT / VADER)  
↓  
Aggregation over rolling windows (1h, 4h, 24h)  
↓  
Feature store as `sentiment_score_{asset}_{window}`  
↓  
Signal engine feature inputs

Sentiment features are used as additional inputs to the ensemble models, not as standalone signals.

---

## 19.2 On-Chain Data

On-chain metrics provide visibility into the actual movement of assets on the blockchain — information not available from exchange feeds.

**Providers**

| Provider | Data |
|---|---|
| **Glassnode** | Exchange inflows/outflows, whale wallet activity, SOPR, MVRV, stablecoin flows |
| **Dune Analytics** | Custom SQL queries on Ethereum, BTC, and other chains |

**Key On-Chain Signals**

| Metric | Interpretation |
|---|---|
| Exchange inflow spike | Large deposits to exchanges — often precedes selling pressure |
| Exchange outflow spike | Large withdrawals to cold wallets — indicates accumulation |
| Whale wallet activity | Large wallet transactions can precede significant price moves |
| Stablecoin supply increase | Rising USDC/USDT on-chain — dry powder available for buying |
| SOPR > 1 | Coins being sold at a profit — potential distribution zone |
| MVRV Z-score | Identifies market overvaluation or undervaluation relative to realised value |

On-chain data is ingested at hourly resolution and stored in the feature store alongside technical indicators.

---

## 19.3 Alternative Data in the Ensemble

---

## 19.4 Alternative Data Progressive Weighting

Alternative data (sentiment, on-chain) is powerful but risky. A new data source may appear predictive due to luck.

**Progressive Weighting Schedule**

New alternative data source: Starts at 5% model weight

| Quarter | Weight | Condition for Increase | Action on Failed Condition |
|---|---|---|---|
| Q1 | 5% | Sharpe >= baseline - 10% | HOLD at 5% |
| Q2 | 10% | Sharpe >= baseline - 5% | DROP to 5% |
| Q3 | 15% | Sharpe >= baseline | DROP to 10% |
| Q4+ | 20% (stable) | Sharpe >= baseline - 2% | DROP to 15% |

**Quarterly Review Criteria**

Before increasing weight, verify:

1. Is correlation with price stable? (Not declining)
2. Is Sharpe contribution consistent across market regimes?
3. Is data quality high? (No significant gaps or latency)
4. Is feature importance>3%? (Material contribution)

**Rejection Path**

If a data source fails multiple quarters:
- After 3 consecutive failed quarters = Retire data source
- Notify researcher; log failure reason
- Archive for future researchers (may become useful 12+ months later)

Alternative data features are added as an additional model layer.

Approach:

- tech-only model: uses only price, volume, and derived technical features
- alt-data model: uses sentiment and on-chain features as additional inputs
- ensemble weight: alt-data model contribution is initially small (10–15%) and increases as its out-of-sample track record grows

This incremental weighting prevents alternative data from contaminating a well-working base model before its value is proven.

---

# 20. Backtesting Integrity Standards

Backtesting is the primary tool for strategy validation. It is also the primary source of false confidence if done incorrectly.

The following standards are mandatory for all research conducted on the AlphaForge platform.

---

## 20.1 Pre-Registration Policy

Before any backtest is run:

1. The researcher writes a **strategy hypothesis** in plain English
2. The hypothesis is committed to the audit log with a timestamp
3. The hypothesis specifies: asset universe, timeframe, entry/exit logic, and expected signal driver
4. Post-hoc modifications to the hypothesis are logged as a new version — the original is never deleted

This prevents the common practice of running hundreds of backtests and only publishing the ones that worked.

---

## 20.2 Data Separation Policy

| Dataset | Purpose | Rules |
|---|---|---|
| Training set | Model fitting | Can be used freely during development |
| Validation set | Hyperparameter tuning | Can be used iteratively during development |
| Holdout set | Final validation | Touched exactly once per research cycle |
| Production data | Live performance | Never used for backtesting |

---

## 20.3 Minimum Backtest Requirements

No strategy may enter the paper trading gate unless its backtest meets:

| Metric | Minimum Requirement |
|---|---|
| Test period | At least 2 years of out-of-sample data |
| Trade count | Minimum 100 trades (statistical significance) |
| Sharpe ratio (annualised) | ≥ 1.0 |
| Maximum drawdown | ≤ 25% |
| Profit factor | ≥ 1.5 |
| Win rate (where applicable) | ≥ 50% |

---

## 20.4 Performance Reporting Standards

All published strategy performance — whether internal or on the marketplace — must include:

- full equity curve (not just final return)
- monthly returns breakdown
- worst drawdown with recovery time
- Sharpe and Sortino ratios
- trade count and average trade duration
- clear statement of the backtest period and data source
- disclaimer that past performance does not guarantee future results

No cherry-picked metrics. No selective time periods. Every published performance figure must be backed by a matching audit log entry.

---

## 20.5 Benchmark Comparison Standards

All strategies must demonstrate outperformance vs standard benchmarks.

**Benchmark Requirements (Before Marketplace Launch)**

| Asset | Benchmark | Required Alpha | Verification |
|---|---|---|---|
| BTC | Buy & hodl BTC | +10% annually | Auditable backtest |
| ETH | Buy & hodl ETH | +8% annually | Auditable backtest |
| Altcoins | Buy & hodl respective coin | +5% annually | Auditable backtest |
| Multi-asset | Equally-weighted portfolio | +7% annually | Auditable backtest |

**Outperformance Proof Requirements**

When publishing strategy performance, include:

1. Strategy equity curve (monthly returns)
2. Benchmark equity curve (same period, same assets)
3. Alpha calculation: (Strategy Return - Benchmark Return)
4. Correlation with benchmark
5. Beta calculation (strategy volatility vs benchmark)
6. Clear disclaimer: "Past performance does not guarantee future results"

**Benchmark Failure Path**

If a strategy underperforms benchmark for 2 consecutive months:
- Strategy marked as "underperforming" on marketplace
- Reduced visibility in recommendations
- Subscriber notification: "Strategy underperforming vs benchmark"
- Creator given 4 weeks to respond/improve
- Auto-retire if underperformance continues

---

# 21. In-Flight Research Projects

The research lab maintains an active pipeline of in-development strategies. This section documents the status and progress of active research efforts.

**Project Registry**

| Project ID | Name | Status | Start Date | Target Gate | Lead Researcher | Expected Beta |
|---|---|---|---|---|---|---|
| PROJ-001 | "Bitcoin Funding Squeeze" | In Development | 2024-01-15 | Q2 2024 | alice@alphaforge.ai | 1.8 |
| PROJ-002 | "Ethereum Gas Volatility" | Backtesting | 2024-02-01 | Q2 2024 | bob@alphaforge.ai | 1.2 |
| PROJ-003 | "Cross-Exchange Arbitrage" | Paper Trading Gate | 2023-10-15 | Q1 2024 | charlie@alphaforge.ai | 1.5 |
| PROJ-004 | "Altcoin Sentiment Cascade" | Hypothesis Review | 2024-03-01 | Q3 2024 | dana@alphaforge.ai | 0.9 |
| PROJ-005 | "Stablecoin Flow Prediction" | Early Idea | 2024-03-10 | Q4 2024 | eve@alphaforge.ai | TBD |

**Status Definitions**

- **Early Idea**: Hypothesis drafted, awaiting data review
- **Hypothesis Review**: Pre-registered hypothesis accepted, ready to backtest
- **Backtesting**: Running historical simulations, feature engineering in progress
- **Paper Trading Gate**: Live market validation in progress (4-week minimum)
- **In Development**: Post-gate improvements, ready for marketplace submission
- **Production**: Live signals generating revenue
- **Archived**: Retired or deprioritized; available for future revival

**Gate Requirements for Advancement**

| From Status | To Status | Requirements |
|---|---|---|
| Early Idea | Hypothesis Review | Hypothesis document approved by lead researcher |
| Hypothesis Review | Backtesting | Data sources procured and validated |
| Backtesting | Paper Trading Gate | Sharpe >=1.0, PF >=1.5, max DD <=25% |
| Paper Trading Gate | Production | Live Sharpe >=80% of backtest, 4 weeks minimum |

---

# 22. Strategy Lifecycle & Status Tracking

Each strategy progresses through well-defined lifecycle stages. Tracking ensures strategies don't stagnate in development and supports decision-making for resource allocation.

**Strategy State Machine**

```
[Concept]
    |
    v
[Hypothesis] ---(rejected)---> [Archive]
    |
    v
[Development] ---(failed backtest)---> [Archive]
    |
    v
[Paper Trading] ---(underperforming)---> [Archive]
    |
    v
[Live] ---(alpha decay)---> [Monitoring]
    |                            |
    |                            |
    +---------(recovered)--------+
    |
    v
[Retired]
```

**Lifecycle Metrics Tracking**

For each strategy, maintain a dashboard:

| Metric | Development | Paper Trading | Live | Monitoring |
|---|---|---|---|---|
| Sharpe Ratio | Backtest | Real-time | Real-time | Real-time |
| Max Drawdown | Backtest | Real-time | Real-time | Real-time |
| Trade Count | Simulated | Counted | Counted | Counted |
| Win Rate | Backtest | Real-time | Real-time | Real-time |
| Capital Allocation | 0% | 0% | 0-10% | Reduced |
| User Subscribers | 0 | 0 | Growing | Declining |
| Creator Revenue | $0 | $0 | Growing | Declining |

**Automated Lifecycle Transitions**

- **Backtest → Paper Trading**: Automatic when Sharpe >= 1.0 (manual approval still required)
- **Paper Trading → Live**: Automatic when 80% Sharpe maintained for 4 weeks
- **Live → Monitoring**: Automatic when Sharpe < 60% of backtest for 1 month
- **Monitoring → Retirement**: Automatic when Sharpe < 30% of backtest for 2 consecutive months

**Performance Degradation Tiers**

| Tier | Live Sharpe vs Backtest | Action | Timeline |
|---|---|---|---|
| Healthy | 100-80% | Normal operation | Ongoing |
| Degraded | 80-60% | Increase monitoring | Daily checks |
| Critical | 60-40% | User notification | Immediate |
| Failure | <40% | Auto-disable | Immediate |

All lifecycle transitions are logged immutably to the audit trail for full traceability.
