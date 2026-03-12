# AlphaForge — Competitive Response Roadmap

**Version:** 1.0 | **Date:** March 2026  
**Status:** Strategic Planning | **Derived From:** Competitive Intelligence Report v1.0

---

# 1. Document Purpose

This document layers the 12 strategic recommendations from the Competitive Intelligence Report onto the existing AlphaForge architecture (Frontend Build Guide, Microservices Architecture, Quant Research Architecture, Infrastructure & DevOps Architecture).

**Goal:** Identify how each recommendation integrates with existing systems, what new components are required, and which docs need updates.

**Approach:** Organize by Phase (1, 2, 3+) and map each recommendation to:
- Affected System Layers
- New Microservices Required
- Database/Schema Changes
- Frontend Components to Build
- Integration Points with Existing Services

---

# 2. Phase 1 Additions (Ship with MVP)

These are table-stakes for retail acquisition and competitive parity.

---

## 2.1 Conversational AI Assistant ("AlphaAI Chat")

### What It Is
A real-time chat interface where users ask questions about their signals, strategies, portfolio, and risk exposure. Returns contextual, conversational answers with links to trading actions.

**Example Interactions:**
- "Why did my BTC signal trigger on 2026-03-12 at 14:32?"
- "What's the max loss on my current ETH position?"
- "Show me my top 3 performing strategies"
- "Explain the momentum divergence pattern"

### Architecture Integration

**New Microservice:** `AlphaAI Chat Service` (stateless, horizontally scalable)
- Receives user questions via WebSocket or REST
- Calls LLM API (Claude Opus via Anthropic) with system prompts
- Context injection from existing services:
  - **Signal Engine Service** → signal reasoning, ML feature importance
  - **Risk Engine Service** → current position exposure, max loss, VaR
  - **Paper Trading Simulator** → strategy performance history
  - **User Service** → portfolio composition, holdings
- Returns streamed responses with action links (e.g., "Copy this strategy", "View backtesting results")

**Frontend Integration:**
- New `<ChatPanel />` component (sidebar or modal)
- Real-time message stream with markdown + rich UI elements
- Context-aware prompts based on current page (e.g., signal detail page → pre-populated question)

**Database:** Minimal — chat messages stored in `chat_history` table for user-facing history, logs to observability layer for LLM fine-tuning

**APIs Added:**
- `POST /api/chat/message` — send user question, receive streamed response
- `GET /api/chat/history` — retrieve past conversations
- `POST /api/chat/context` — optionally pass additional context (current signal ID, strategy ID, etc.)

**Cost Model:** LLM inference per token. At scale, need token budget management and caching of common questions.

**Docs to Update:**
- ✅ Frontend Build Guide — Add Chat UI section, component structure
- ✅ Microservices Architecture — Add AlphaAI Chat Service, integration points
- ✅ Infrastructure & DevOps — Add LLM API rate limiting, token budget alerts, failover to degraded mode (no chat)

### Implementation Timeline
- Week 1-2: Set up Anthropic API, design system prompts, test context injection
- Week 3: Build frontend ChatPanel component
- Week 4: Integration testing, observability, rate limiting

---

## 2.2 Move Mobile to Phase 2 (React Native)

### What It Is
Fully-featured iOS/Android app shipping as Phase 2 (not Phase 4). Handles 80% of user workflows on mobile.

**MVP Mobile Features:**
- Signal notifications (push) with one-tap trading
- Portfolio PnL dashboard (real-time)
- Signal history + filtering (sortable by performance)
- Copy trading controls (subscribe, pause, adjust risk multiplier)
- Paper trading position viewer
- Settings (notification preferences, risk limits)
- Chat with AlphaAI (integrated)

**Out of Scope for Mobile Phase 1:**
- Backtesting (desktop-only for now)
- Strategy marketplace (web-only, link to web for details)
- Market intelligence dashboards (simplified version OK)

### Architecture Integration

**Frontend Structure:** React Native with shared TypeScript types
- `/apps/web` — existing Next.js web app (unchanged)
- `/apps/mobile` — React Native app (new)
- `/packages/shared` — shared types, utilities, API client

**API Compatibility:** Existing REST APIs remain unchanged. Mobile uses same endpoints.

**Data Layer (Mobile-Specific):**
- Offline-first SQLite for critical data (portfolio, recent signals, settings)
- Incremental sync with backend using `lastUpdated` timestamps
- Fallback to stale-cached data if network down

**Push Notifications:**
- Signal trigger → Firebase Cloud Messaging (FCM) on Android, APNs on iOS
- Backend service sends notification to Firebase topic subscribers
- User taps notification → deep link to signal detail or 1-tap copy

**Frontend:** React Native Navigation (React Navigation) with native tab bar
- Shared component library for cross-platform UI (custom ThemeProvider for mobile)
- Platform-specific overrides for gestures, animations, bottom sheets

**Database:** No changes to backend DB schema. Mobile reads from existing APIs.

**Docs to Update:**
- ✅ Frontend Build Guide — Add React Native section, shared package structure, offline-first strategy, push notification setup
- ✅ Infrastructure & DevOps — Add FCM/APNs configuration, mobile app distribution (TestFlight + Google Play), app release checklist

### Implementation Timeline
- Week 1: React Native project scaffold, navigation structure, shared package setup
- Week 2-3: Port core screens (portfolio, signals, copy trading), offline sync
- Week 4: Push notifications, deep linking, testing
- Week 5-6: App store review prep, TestFlight/internal testing

---

## 2.3 TradingView Alert → Execution Bridge

### What It Is
Users configure TradingView alerts in their scripts. When alert fires, it HTTP POSTs to an AlphaForge webhook. AlphaForge treats the alert as a signal and auto-executes based on user's settings.

**Example Workflow:**
1. User creates TradingView Pine Script with alert: `alertmessage: "LONG BTC/USD confidence=0.92 riskLevel=2"`
2. Alert fires on TradingView → HTTP POST to `https://alphaforge.com/api/webhooks/tradingview`
3. AlphaForge parses alert, validates signal confidence, checks risk engine
4. If valid, auto-executes on user's preferred exchange with user's sizing rules
5. Signal logged to user's "External Signals" feed with full audit trail

### Architecture Integration

**New Microservice:** `TradingView Webhook Receiver` (stateless, rate-limited per user)
- Receives webhooks from TradingView (unauthenticated but rate-limited by source IP hash)
- Validates webhook signature (TradingView signs with shared secret per user)
- Parses alert message (structured format)
- Routes to Execution Service with user context

**New Microservice:** `External Signal Ingestion Service`
- Sits between Webhook Receiver and Execution Service
- Validates external signal against user's ingestion rules:
  - Signal confidence threshold
  - Allowed strategies (e.g., "only from strategy X")
  - Max position size relative to currently open positions
  - Cooldown between signals (avoid spam)
- Creates signal record with `source: "tradingview"`, audit trail, no ML reasoning (marked as external)
- Routes to Risk Engine, then Execution Service

**API Endpoint Added:**
- `POST /api/webhooks/tradingview` — receive alert, no auth required but rate-limited
- `POST /api/external-signals/rules` — user configures ingestion rules (LLM can help)
- `GET /api/external-signals/history` — view all ingested external signals with execution context

**Frontend Integration:**
- New "External Signals" page showing TradingView + any other external signal sources
- Settings page for configuring ingestion rules (confidence threshold, strategy filter, cooldown)
- TradingView webhook URLs & setup guide (copy-paste friendly)

**Database Schema Changes:**
- `signals` table: add `source: enum('internal', 'tradingview', 'other')`
- `signals` table: add `external_metadata: json` (stores webhook payload, signature verification result)
- `signal_ingestion_rules` table: user's rules for filtering external signals
- `webhook_events` table: log all webhook hits for debugging/audit

**Docs to Update:**
- ✅ Frontend Build Guide — Add External Signals page, TradingView setup guide
- ✅ Microservices Architecture — Add Webhook Receiver, External Signal Ingestion Service, routing logic
- ✅ Infrastructure & DevOps — Add webhook rate limiting rules, IP-based throttling, webhook retry logic

### Implementation Timeline
- Week 1: Design alert message format, webhook security model, signature verification
- Week 2: Implement Webhook Receiver + External Signal Ingestion Service
- Week 3: Risk engine integration, execution routing
- Week 4: Frontend setup guide, testing with real TradingView alerts

---

# 3. Phase 2 Additions (Build After MVP)

These enable specific user segments (bots, accumulators, learners) and drive marketplace engagement.

---

## 3.1 Grid Bot + DCA Bot

### What They Are

**Grid Bot:** Places a grid of buy/sell orders in a price range. Example: User sets BTC $40k-$44k range with 10 grids. Bot places 5 buy orders at $40k, $41k, $42k, $43k, $44k and 5 sell orders at $42k, $43k, $44k, $45k, $46k. Every fill triggers a counter-order. Profits from volatility in sideways markets.

**DCA Bot:** Invests a fixed amount on a recurring schedule. Example: invest $500 in BTC every Sunday. Averages down during downturns, averages up during upturns. Long-term accumulation strategy.

### Architecture Integration

**New Signal Types:** Grid trading and DCA are **not** directional signals but **automation strategies**. They sit alongside copy-traded signals, not within the signal engine.

**New Microservice:** `Automation Engine Service`
- Grid Bot execution: places/updates orders on exchange APIs, monitors fills, adjusts grid
- DCA Bot execution: checks clock, triggers recurring investment, buys target asset
- Distinct from signal-based execution (no ML reasoning, no risk engine override needed)
- Independent scheduling, order management, error recovery

**New Database Schema:**
- `automation_jobs` table (one row per active bot):
  - `user_id, job_type (grid|dca), exchange_id, symbol, status, config (json)`
  - `config` for grid: `{lowerBound, upperBound, gridLevels, orderSize, totalInvestment}`
  - `config` for dca: `{symbol, investmentAmount, frequency (daily|weekly|monthly), nextExecutionTime}`
- `automation_orders` table (orders placed by bots):
  - `automation_job_id, order_id (from exchange), status, filled_amount, avg_price`
- `automation_events` table (audit log):
  - Every grid fill, every DCA trigger, every error logged with timestamp + exchange response

**Frontend Integration:**
- New page: "Automation Bots"
- Grid Bot builder: visual range selector, grid level slider, preview of orders
- DCA Bot builder: symbol selector, amount input, frequency picker, start date
- Active bots dashboard: current P&L per bot, filled orders, next scheduled action
- Kill switch for each bot (close all orders, stop scheduling)

**Risk Engine Integration (Light Touch):**
- Bots still check user's global risk limits before executing:
  - Max portfolio allocation to bots (e.g., "don't let all bots exceed 50% of AUM")
  - Max leverage per position
  - Blacklist symbols or exchanges
- But bots don't require per-order risk approval (unlike signals)

**Docs to Update:**
- ✅ Frontend Build Guide — Add Automation Bots section, builder UI, active bots dashboard
- ✅ Microservices Architecture — Add Automation Engine Service, job scheduler, order management
- ✅ Infrastructure & DevOps — Add bot job queueing (Kafka for scheduling), order retry logic, exchange API failover

### Implementation Timeline
- Week 1: Design automation job schema, exchange order lifecycle
- Week 2: Implement Automation Engine (grid + DCA logic)
- Week 3: Frontend builders and dashboard
- Week 4: Integration testing, exchange API edge cases, error recovery

---

## 3.2 No-Code Strategy Builder

### What It Is
Visual drag-and-drop interface where users customize signal-based strategies without code. Users set:
- Signal filters (min confidence, max volatility, time of day)
- Position sizing rules (fixed $, % of portfolio, Kelly criterion)
- Risk controls (max loss per position, max daily loss)
- Copy trading rules (which signals to copy, which to skip)

**Example Use Case:** A conservative investor says "I only want to copy AlphaForge's signals when confidence > 85%, volatility is low, and I have less than $100k in open positions. Position size me with Kelly criterion."

### Architecture Integration

**New Component:** `Strategy Configurator Service` (rule engine)
- Parses user-defined rules (JSON representation of visual builder selections)
- Validates rule constraints (e.g., "confidence can't be > 100")
- Compiles rules to execution logic (function that evaluates each signal)
- Stores rule templates for reuse/sharing

**New Database Schema:**
- `user_strategies` table:
  - `user_id, strategy_name, description, rules (json), created_at, performance_stats`
  - `rules` JSON structure:
    ```json
    {
      "signal_filters": {
        "min_confidence": 0.85,
        "max_volatility": "medium",
        "preferred_time_windows": ["09:00-16:00 UTC"]
      },
      "position_sizing": {
        "method": "kelly",
        "base_allocation": 0.02,
        "max_per_position": 500
      },
      "risk_controls": {
        "max_loss_per_trade": 200,
        "max_daily_loss": 1000,
        "max_open_positions": 5
      }
    }
    ```
- `strategy_templates` table (pre-built templates for beginner users):
  - "Conservative Copier", "Growth Seeker", "Volatility Hunter", etc.

**Frontend Integration:**
- New page: "Strategy Builder"
- Visual rule editor (dropdowns + sliders, not code)
- Strategy performance simulator (replay past signals through user's rules, show backtest stats)
- Template gallery ("Start with a template")
- Active strategy selector in Portfolio (which strategy's rules are active now)

**Execution Integration:**
- When a signal arrives, Execution Service loads user's active strategy rules
- Evaluates signal against rules (confidence check, volatility check, sizing calc)
- If passes, executes with sized position; if fails, skips signal with reason logged
- User sees in signal history: "✅ Copied (Kelly sized to $450)" vs "🚫 Skipped (confidence 72% < 85% threshold)"

**Docs to Update:**
- ✅ Frontend Build Guide — Add Strategy Builder UI, template gallery
- ✅ Microservices Architecture — Add Strategy Configurator Service, rule evaluation in Execution Service
- ✅ Quant Research Architecture — Add section on rule-based signal filtering at execution time

### Implementation Timeline
- Week 1: Design rule JSON schema, validation logic
- Week 2: Implement Strategy Configurator, rule evaluation
- Week 3: Frontend builder UI, template library
- Week 4: Signal simulator, integration with execution pipeline, testing

---

## 3.3 Social Community Layer

### What It Is
In-platform community features focused on **signal and strategy transparency**. Users share signal ideas, discuss strategies, see leaderboards of top performers.

**Key Features:**
- Strategy leaderboards (sortable by return%, Sharpe, win rate, confidence)
- Trader profiles with verified track record (uses backtesting + live trading data)
- Strategy discussion threads (users post ideas, others remix and test)
- Signal feed (public signals, discussion, performance metrics)
- Follower system (follow traders you trust, get notified when they launch new strategies)

**Example:** User sees "ConsertativeFlow" strategy #1 on leaderboard with 42% YTD return, 65% win rate, 8,200 followers. Clicks profile → sees discussion thread about the strategy → sees full backtesting report → subscribes with one click.

### Architecture Integration

**New Microservices:**
- `Community Feed Service` — generates leaderboards, user feeds, activity streams
- `Social Graph Service` — manages follower relationships, notification routing
- `Discussion Service` — threads, comments, moderation

**New Database Schema:**
- `community_profiles` table (extends `users` table):
  - `bio, avatar, follower_count, verified_track_record (bool), featured_strategy_id`
- `strategy_discussions` table:
  - `strategy_id, title, description, created_by, thread_count, last_activity`
- `strategy_comments` table:
  - `discussion_id, user_id, comment, likes, created_at`
- `follower_relationships` table:
  - `follower_user_id, following_user_id, created_at`
- `community_notifications` table:
  - `user_id, type (new_follower|followed_user_new_strategy|strategy_discussed), triggered_by_user_id, read (bool)`

**Frontend Integration:**
- New page: "Community" hub
  - Leaderboard tab (strategies, traders, signals)
  - Discover tab (trending strategies, new traders, discussion threads)
  - Following tab (activity feed from users you follow)
  - My Profile page (trader profile, edit bio/avatar, my strategies, followers)
  - Strategy detail page expansion (add "Discuss" tab, link to discussion threads)

**Real-Time Updates:**
- Activity feed updates via WebSocket (new follower, new comment, strategy discussed)
- Leaderboard updates on signal completion (rank changes)

**Moderation:**
- Basic spam filters (duplicate comments, excessive links)
- Report button on comments/profiles
- Admin dashboard for moderators

**Docs to Update:**
- ✅ Frontend Build Guide — Add Community pages, leaderboards, profiles, discussion UI
- ✅ Microservices Architecture — Add Community Feed, Social Graph, Discussion Services
- ✅ Infrastructure & DevOps — Add real-time feed generation job, moderation pipeline

### Implementation Timeline
- Week 1: Design social schema, leaderboard calculation logic
- Week 2: Implement Community Feed, Social Graph, Discussion services
- Week 3: Frontend community hub, profile pages, leaderboards
- Week 4: Real-time feed updates, moderation, testing

---

## 3.4 AlphaAcademy (Education Layer)

### What It Is
In-platform education that turns every signal into a learning moment. Users learn **why** signals trigger.

**Content Types:**
- **Signal Breakdowns:** "Here's why your BTC signal triggered on 2026-03-12: momentum divergence detected on hourly MACD + volume surge 23% above SMA(20)"
- **Pattern Guides:** Explanations of common patterns (breakouts, divergences, mean reversion, etc.)
- **Strategy Guides:** How-to guides for copy trading, backtesting, risk management, position sizing
- **Quant Basics:** "What is Sharpe ratio?", "How does Kelly criterion work?", "What's a drawdown?"

**Example Integration:** User sees a BTC signal → clicks "Learn why" → modal opens explaining momentum divergence + MACD calculation + link to "Pattern Guides" section

### Architecture Integration

**New Microservice:** `Content Management Service`
- Manages education content (guides, videos, quizzes)
- Delivers contextual content (given a signal type, return relevant guide)
- Tracks user progress (which guides read, quiz scores)

**New Database Schema:**
- `education_content` table:
  - `content_id, title, category, difficulty (beginner|intermediate|advanced), content (markdown), created_at`
- `signal_breakdowns` table:
  - `signal_id, breakdown_summary, pattern_name, key_metrics (json)`
- `user_education_progress` table:
  - `user_id, content_id, completed (bool), quiz_score (if applicable), completed_at`

**Frontend Integration:**
- New page: "AlphaAcademy" with course library
  - Category filters (Patterns, Strategies, Risk Mgmt, Quant Basics)
  - Difficulty toggle (Beginner, Intermediate, Advanced)
  - Progress tracking (% complete, quiz scores)
- Contextual modals:
  - Signal detail → "Learn why" button opens relevant guide + signal breakdown
  - Portfolio risk → "What's VaR?" link to guide
  - Backtesting results → "Understand your metrics" guide
- Onboarding flow (new users guided through beginner academy tracks)

**LLM Integration (Optional):**
- Use AlphaAI Chat to generate signal breakdowns on-the-fly
- User asks "Why did this signal trigger?" → LLM generates explanation, saved as signal breakdown

**Docs to Update:**
- ✅ Frontend Build Guide — Add AlphaAcademy page, contextual education modals, onboarding flow
- ✅ Microservices Architecture — Add Content Management Service, contextual content delivery
- (Community + Academy integration: leaderboards show top learners, completed courses boost trader credibility)

### Implementation Timeline
- Week 1: Design content schema, category taxonomy
- Week 2: Build Content Management Service, contextual content delivery
- Week 3: Frontend Academy page, modals, progress tracking
- Week 4: Populate initial content, quiz engine, onboarding flow

---

# 4. Phase 3+ Additions (Strategic Enhancements)

Lower priority, deferred but strategically important.

---

## 4.1 Trading Tournaments

**What:** Monthly competitive trading events on paper trading. Users compete for prizes on leaderboards (return%, Sharpe, win rate).

**Architecture:** Add tournament scheduling, leaderboard calculation, prize distribution.

**Docs Update:** Frontend (tournaments page), Microservices (tournament scheduler), DevOps (prize payout saga).

---

## 4.2 Strategy Avatar Personalities

**What:** Each strategy gets a personality badge ("Conservative Hedge", "Growth Seeker", "Volatility Hunter") + avatar. Dramatizes marketplace UI.

**Architecture:** Add strategy personality classification (rule-based or LLM-generated from strategy rules).

**Docs Update:** Frontend (marketplace redesign with avatars), Microservices (strategy classifier).

---

## 4.3 Trailing Stop / Trailing Take-Profit

**What:** Dynamic exit orders that follow price movement.

**Architecture:** Add order type support to Execution Service, exchange webhook integration to update stops.

**Docs Update:** Microservices (execution engine), DevOps (order tracking SLA).

---

## 4.4 Onchain Smart Money Tracker (User-Facing Product)

**What:** Public dashboard showing whale movements, liquidation heatmaps, MVRV/SOPR metrics. Feeds into signal generation but also accessible to users directly.

**Architecture:** Surface existing Glassnode data + on-chain analytics in new UI.

**Docs Update:** Frontend (new market intelligence dashboard), Microservices (on-chain data pipeline enhancements).

---

## 4.5 Client Fund Protection Narrative

**What:** Reframe existing E&O insurance + compliance into a trust signal ("Your trades are protected by $X insurance").

**Architecture:** No code changes. Marketing + compliance ops.

---

# 5. Impact Matrix

| Recommendation | Frontend | Microservices | Quant Research | DevOps | Priority |
|---|---|---|---|---|---|
| AlphaAI Chat | New ChatPanel | New AlphaAI Service | Context injection | LLM API gating | 🔴 P1 |
| Mobile (Phase 2) | React Native app | No change | No change | FCM/APNs setup | 🔴 P1 |
| TradingView Bridge | External Signals page | Webhook Receiver + Ingestion | Signal source enum | Webhook rate limiting | 🔴 P1 |
| Grid + DCA Bots | Automation Bots builder | Automation Engine Service | New signal types | Job scheduling (Kafka) | 🟡 P2 |
| No-Code Builder | Strategy Builder page | Strategy Configurator | Rule evaluation | No change | 🟡 P2 |
| Social Community | Community hub + profiles | Community Feed + Social Graph | Leaderboard calc | Real-time feed jobs | 🟡 P2 |
| AlphaAcademy | Academy page + modals | Content Management Service | Signal breakdown gen | Content CDN | 🟡 P2 |
| Tournaments | Tournament page + leaderboards | Tournament Scheduler | Leaderboard calcs | Prize payout saga | 🟢 P3 |
| Strategy Avatars | Marketplace redesign | Strategy Classifier | Personality inference | No change | 🟢 P3 |
| Trailing Stops | No change (execution info) | Execution Engine enhancement | No change | Order tracking | 🟢 P3 |
| Onchain Tracker | Market Intel dashboard | On-chain data pipeline | Already exists | Data enrichment | 🟢 P3 |
| Protection Narrative | No change | No change | No change | Compliance ops | 🟢 P3 |

---

# 6. Next Steps

1. **Approve Phase 1 additions** (Chat, Mobile, TradingView) or adjust
2. **I will then update Frontend Build Guide** with:
   - Chat panel component spec
   - React Native app structure (high-level)
   - External Signals page + TradingView setup guide
3. **Simultaneously update Microservices Architecture** with:
   - AlphaAI Chat Service
   - Webhook Receiver + External Signal Ingestion
   - TradingView integration diagram
4. **Phase 2 planning** deferred until Phase 1 is locked

---

*Roadmap compiled: March 2026*  
*Based on Competitive Intelligence Report + Core Architecture Docs*
