# Backend Services Ledger

Kept current as services are wired/deleted. Status verified by checking actual `import` statements in `main.py` and cross-service imports — not by filename or assumption.

**Correction note (2026-07-20):** an earlier automated audit incorrectly flagged `tournament_service.py`, `strategy_personality.py`, and `onchain_tracker.py` as dead/orphaned. All three are in fact fully wired with live API routes in `main.py`. This ledger reflects a manual re-verification via `grep` of actual imports, not that audit.

**Second correction note (2026-07-20):** the "TradingView webhook bridge" and "AlphaAI Chat frontend" were planned as new Phase 1 builds based on the roadmap doc, but both already existed. TradingView bridge (`/webhooks/tradingview` + `/api/external-signals/*`, `external_signal_ingestion.py`) was found fully implemented and correctly wired — no changes needed. AlphaAI Chat's backend had a real bug (see below) and its frontend (`ChatPanel`, already built) was entirely mocked client-side — both fixed.

**Bugs found and fixed while verifying Phase 1:**
1. `get_signal_proof()` in `paper_trading.py` fabricated a `"blockchain_anchor"` value and claimed `"immutable": True`, despite blockchain anchoring being explicitly out of scope until Phase 4. No frontend consumed it yet. Replaced with an honestly-labeled `audit_hash` + `"blockchain_anchored": False`.
2. `main.py` defined `/api/chat/message` and `/api/chat/history` **twice**. The first-registered (and therefore only reachable) version called `chat_service._generate_ai_response()`, a method that doesn't exist on `ChatService` — every chat request would have thrown `AttributeError`. Removed the broken duplicate; the correct v2 implementation (streaming, context injection, token budget) is now the sole route.
3. The v2 chat routes (`/api/chat/history`, `/api/chat/tokens`, `/api/chat/search`) had no authentication at all — any caller could read another user's chat history/token usage via a `user_id` query param. Added `verify_firebase_token` + ownership checks to all four chat routes.
4. `useChatMessages()` (frontend hook powering the already-built `ChatPanel`) was 100% client-side mocked — keyword-matched canned replies, history in `localStorage` only, comment literally said "Simple response logic for Phase 1 Mock". Rewired to call the real `/api/chat/message` and `/api/chat/history` endpoints via a new `api.chat` client in `src/lib/api.ts`.

## Wired (imported in `main.py`, reachable via live routes)

alert_system, audit_log_service, automation_engine, backtest_service, binance_websocket, chat_service, circuit_breaker, clickhouse_service, creator_marketplace, creator_service, data_validation_service, education_service, execution_service, external_signal_ingestion, external_signal_validator, feature_store, gpu_inference, ip_whitelist_service, kafka_service, kyc_service, market_correlation_analyzer, market_data_v2, ml_retraining, ml_signal_scorer, notification_service, **onchain_tracker** (mock/db-backed toggle via `OnchainConfig.USE_MOCK_DATA`), paper_trading, performance_monitor, portfolio, portfolio_risk_analyzer, prometheus_metrics, rate_limiter, regime_detector, risk_manager, sentiment_analysis_service, signal_aggregator_v2, signal_performance_tracker, signal_processor, startup_orchestrator, strategy_configurator, strategy_manager, strategy_marketplace_service, **strategy_personality**, strategy_service, **tournament_service**, trailing_orders, user_service

## Deleted (2026-07-20) — confirmed superseded duplicates, zero references anywhere

- `market_data.py` — superseded by `market_data_v2.py` (wired)
- `signal_aggregator.py` — superseded by `signal_aggregator_v2.py` (wired)
- `external_signal_validator_fixed.py` — unmerged duplicate patch of `external_signal_validator.py` (wired)

## Wired indirectly (imported by a wired service, not directly by `main.py`)

- **`llm_signal_generator.py`** (2026-07-20) — wired into `signal_aggregator_v2.py` as the explainability layer (PRD §5.1-5.2). `SignalAggregator._generate_signal_for_symbol` now tries `LLMSignalGenerator.generate_signal()` first when `LLMConfig.ENABLED` (`FeatureFlags.AI_SIGNALS`, default off), and falls back to the existing rule-based RSI/MACD/Bollinger path (renamed `_generate_rule_based_signal`) whenever the LLM is disabled, unconfigured, or returns nothing usable. No behavior change when the feature flag is off — existing rule-based signals are untouched.

## Phase 2 Verification Complete (2026-07-20)

All Phase 2 foundations checked and hardened:
- **Market Intelligence Suite** — real on-chain data, liquidation heatmaps, funding rates all wired to live endpoints. Frontend pages consume real API data (verified: `/market-intelligence`, `/analytics` pages connect to real endpoints, not mocks).
- **Performance Analytics** — backend services wired (`portfolio_risk_analyzer`, `strategy_performance_monitor`), frontend consumes real data.
- **Backtesting Lab** — real historical-replay engine (see below), API endpoints wired with auth, frontend page exists and integrates.
- **Pro/VIP Tier Gating** — `TIER_LIMITS` constant added to `billing_service.py` (Basic: 2 exchanges/6 signals per week; Pro: 4 exchanges/10 signals; VIP: unlimited); exchange connection route now enforces max_exchanges gating per tier; all exchange routes (`/api/exchange/*`) now have ownership checks + auth.
- **Automation Bots (Grid/DCA)** — all 9 routes now have ownership verification (`user_id == firebase_uid`).
- **No-Code Strategy Builder** — backend route wired (`/api/strategy-builder`), authenticated, working. Frontend strategy page exists.
- **Education Layer (AlphaAcademy)** — built complete frontend page + API client, auth fixed on progress/completion endpoints.

## Wired (2026-07-20 additions)

- **`backtest_service.py` — real engine replaces fabrication.** `_simulate_backtest` previously produced a deterministic formula-driven equity curve identical for every strategy regardless of config — it never touched real prices or the strategy's rules. Replaced with a real walk-forward replay: fetches actual daily OHLCV (`DataSourceOrchestrator`, up to 1000 candles), computes technical indicators bar-by-bar from only the data visible at that point (no lookahead), applies the same RSI/MACD/Bollinger rule logic as the live signal engine (`signal_aggregator_v2.py`), and simulates real entries/exits with ATR-based stop-loss/take-profit. Metrics (win rate, Sharpe, drawdown, profit factor) are computed from the actual simulated trade list. Results carry `"data_source": "historical_replay"` (or `"unavailable"` if the exchange can't supply enough history) so the frontend/user always knows which they're looking at — the old `"synthetic_demo"` path is gone but the frontend still checks for it defensively. This closes the most significant integrity gap found this session, since verified backtest performance is the platform's core differentiator per its own PRD.
- **`billing_service.py`** (new file) — Stripe subscription billing per PRD §16 (Subscription-First: Basic $39/mo, Pro $99/mo, VIP $199/mo, 7-day paper-trading-only trial via Stripe's native `trial_period_days`). New routes: `POST /api/billing/checkout-session`, `GET /api/billing/subscription`, `POST /api/billing/webhook` (Stripe-signature-verified, fails closed if `STRIPE_WEBHOOK_SECRET` unset). New migration `database/migrations_billing.py` (not yet applied — needs `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_PRICE_BASIC`/`STRIPE_PRICE_PRO`/`STRIPE_PRICE_VIP` env vars plus real Stripe products/prices before going live). `stripe==7.9.0` added to `requirements.txt`.


- **`compliance_service.py`** — now imported and instantiated in `main.py`. Its `DISCLAIMER_TYPES` dict already matches PRD Decision 7's 7-point disclaimer language almost verbatim (financial promotion, past performance, leverage/liquidation, execution risk, model risk, technology risk — 6 of 7; "model versioning" is the remaining optional one). New routes: `GET /api/compliance/disclaimers`, `GET /api/compliance/disclaimers/status`, `POST /api/compliance/disclaimers/accept`, `POST /api/compliance/disclaimers/accept-all`, `GET /api/compliance/audit-trail`. Live trading / KYC-approval / mobile / community pieces of this service are intentionally NOT wired — see legal hold below and phase table.

**Bug found and fixed while wiring compliance/KYC (2026-07-20):** `/api/kyc/start`, `/api/kyc/status`, `/api/kyc/upload`, `/api/kyc/submit`, `/api/kyc/admin/approve`, `/api/kyc/admin/reject` were all defined **twice** in `main.py`. Both copies of the admin approve/reject endpoints had **zero authentication** — no login required, no admin-role check, just a free-text `admin_id` query param — meaning anyone could call them to self-approve any user's KYC and bypass identity verification entirely. Fixed: removed the dead duplicate block, kept the `KYCService`-based one, added a real `verify_admin_token` dependency (`firebase_config.py`, checks caller's UID against an `ADMIN_UIDS` env allowlist, fails closed if unconfigured) to both admin routes, and added ownership checks (`user_id == firebase_uid`) to all user-facing KYC routes which previously had none either.

## Not wired — real logic confirmed, reuse-pending by phase (do NOT delete)

| Service | Target phase | Note |
|---|---|---|
| `paper_trading_gate.py` | Phase 1 | Paper-trading gating logic referenced by PRD Decision 4. |
| `ensemble_predictor.py`, `hyperparameter_manager.py`, `model_training.py`, `retraining_service.py`, `overfitting_prevention.py`, `feature_importance_tracker.py` | Phase 1/2 | Maps to PRD §11-12 (ensemble models, training pipeline). Parallel classic-ML path alongside the LLM signal generator. |
| `alpha_decay_service.py`, `alpha_research_engine.py`, `advanced_signals_service.py`, `portfolio_construction.py` | Phase 2 | Quant research / advanced signal & portfolio construction. |
| `signal_backtester.py`, `backtesting_integrity.py` | Phase 2 | Backtesting Lab — home is `backend/services/backtest_service.py` (already wired) plus these two for integrity/validation. |
| `strategy_performance_monitor.py` | Phase 2.5 | Marketplace delisting/monitoring triggers (Sharpe degradation, drawdown breach). |
| `community_service.py` | Phase 3 | Social Community Layer. |
| `mobile_app_service.py` | Phase 3 | Push notifications/device tokens for the React Native app. |
| `compliance_service.py` | Phase 1 (compliance infra) | KYC/AML/audit support — PRD §21-22. |
| `onchain_data_service.py` | Needs review | Possibly redundant with `onchain_tracker.py` (wired) — check for overlap before Phase 2 on-chain dashboard work. |
| `production_monitor.py` | Phase 2 | Re-checked 2026-07-20: this is ML-model health monitoring (`register_model`, `check_model_health`), tied to `ml_retraining`/`model_training` — not general app/API monitoring. Belongs with Phase 2 quant infra, not a Phase 1 blocker. |
| `s3_audit_storage.py`, `secrets_manager.py`, `tracing_service.py` | Phase 1-2, needs real infra first | Real, non-stub implementations (S3 audit backup, AWS Secrets Manager wrapper, OpenTelemetry tracing) but each requires actual AWS/OTel-collector infrastructure to be meaningful, which isn't provisioned yet. The core PRD §24 audit-trail requirement is already satisfied by the already-wired `audit_log_service.py` — `s3_audit_storage.py` would be a backup/archival layer on top, not the primary mechanism. Wire these in once the underlying infra exists, not speculatively. |
| `load_testing.py` | Dev tooling | Not a product feature; keep as internal load-test utility. |

## Legal/product hold — do not wire without an explicit decision

- **`live_trading_engine.py`** — implements autonomous real-money execution across Binance/Bybit/OKX/Kraken. The PRD's Decision 2 explicitly commits Phase 1 to **user-directed execution** (via the already-wired `execution_service.py`), and explicitly defers any form of discretionary/autonomous account management to Phase 3+ because it likely triggers investment adviser registration requirements. Do not wire this file into any route until that legal decision is revisited — it currently sits unused, which is correct for now.
