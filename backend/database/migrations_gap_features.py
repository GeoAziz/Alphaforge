"""
Database migrations for remaining gap features:
- Community & Social (user profiles, follows, comments, ratings)
- Compliance & Regulatory (KYC, AML, audit logs)
- Mobile App (device tokens, push notifications)
- Advanced Signals (ML models, sentiment data)
- Feature Store (§13.3)
- IP Whitelisting (§16.2)
- Marketplace Governance (§12)
- Signal Proofs (§12.1)
"""

MIGRATIONS_ADDITIONAL = """

-- ============================================================================
-- COMMUNITY & SOCIAL FEATURES
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  display_name TEXT,
  bio TEXT,
  avatar_url TEXT,
  total_followers INT DEFAULT 0,
  total_following INT DEFAULT 0,
  win_rate NUMERIC(8,4) DEFAULT 0,
  total_pnl NUMERIC(18,2) DEFAULT 0,
  average_rr NUMERIC(8,4) DEFAULT 1.0,
  verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_follows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  follower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  following_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(follower_id, following_id)
);

CREATE TABLE IF NOT EXISTS strategy_comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  strategy_id UUID NOT NULL REFERENCES creator_strategies(id) ON DELETE CASCADE,
  comment_text TEXT NOT NULL,
  likes INT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS strategy_ratings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  strategy_id UUID NOT NULL REFERENCES creator_strategies(id) ON DELETE CASCADE,
  rating INT CHECK (rating >= 1 AND rating <= 5),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, strategy_id)
);

CREATE TABLE IF NOT EXISTS user_leaderboard (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  display_name TEXT,
  win_rate NUMERIC(8,4),
  total_pnl NUMERIC(18,2),
  total_trades INT DEFAULT 0,
  average_rr NUMERIC(8,4),
  sharpe_ratio NUMERIC(8,4),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_achievements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  achievement_type TEXT NOT NULL,
  awarded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, achievement_type)
);

-- ============================================================================
-- COMPLIANCE & REGULATORY
-- ============================================================================

CREATE TABLE IF NOT EXISTS kyc_verifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  full_name TEXT NOT NULL,
  date_of_birth DATE,
  address TEXT,
  country TEXT,
  id_document_url TEXT,
  proof_of_address_url TEXT,
  status TEXT DEFAULT 'NOT_STARTED' CHECK (status IN ('NOT_STARTED', 'SUBMITTED', 'APPROVED', 'REJECTED', 'EXPIRED')),
  submitted_at TIMESTAMP WITH TIME ZONE,
  approved_at TIMESTAMP WITH TIME ZONE,
  rejection_reason TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS aml_checks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  full_name TEXT,
  country TEXT,
  check_result TEXT CHECK (check_result IN ('PASS', 'FAIL')),
  risk_level TEXT CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
  checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  details JSONB DEFAULT '{}'::jsonb,
  ip_address TEXT,
  hash TEXT NOT NULL,
  prev_hash TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS disclaimer_acceptances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  disclaimer_version TEXT NOT NULL,
  accepted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ip_address TEXT
);

-- ============================================================================
-- MOBILE APP
-- ============================================================================

CREATE TABLE IF NOT EXISTS device_registrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  device_token TEXT NOT NULL,
  platform TEXT CHECK (platform IN ('ios', 'android', 'web')),
  device_model TEXT,
  app_version TEXT,
  registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, device_token)
);

CREATE TABLE IF NOT EXISTS push_notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  message TEXT,
  notification_type TEXT,
  data JSONB DEFAULT '{}'::jsonb,
  sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  read_at TIMESTAMP WITH TIME ZONE,
  platform TEXT
);

-- ============================================================================
-- ADVANCED SIGNALS & ML
-- ============================================================================

CREATE TABLE IF NOT EXISTS sentiment_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  social_sentiment NUMERIC(5,4),
  news_sentiment NUMERIC(5,4),
  whale_sentiment NUMERIC(5,4),
  fear_greed_index INT,
  data_source TEXT,
  collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml_models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_name TEXT NOT NULL UNIQUE,
  model_version TEXT,
  model_type TEXT,
  accuracy NUMERIC(5,4),
  training_date TIMESTAMP WITH TIME ZONE,
  training_samples INT,
  trained_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS news_feed (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  headline TEXT NOT NULL,
  summary TEXT,
  source TEXT,
  sentiment TEXT CHECK (sentiment IN ('positive', 'negative', 'neutral')),
  importance INT,
  published_at TIMESTAMP WITH TIME ZONE,
  url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- AUTOMATION (Grid Bot + DCA Bot)
-- ============================================================================

CREATE TABLE IF NOT EXISTS automation_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  job_type TEXT NOT NULL CHECK (job_type IN ('grid', 'dca')),
  exchange_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'paused', 'stopped', 'error')),
  config JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS automation_orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  automation_job_id UUID NOT NULL REFERENCES automation_jobs(id) ON DELETE CASCADE,
  order_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'filled', 'partially_filled', 'cancelled', 'failed')),
  filled_amount NUMERIC(18,8) DEFAULT 0,
  avg_price NUMERIC(18,8) DEFAULT 0,
  side TEXT CHECK (side IN ('BUY', 'SELL')),
  price NUMERIC(18,8),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS automation_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  automation_job_id UUID NOT NULL REFERENCES automation_jobs(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  details JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_follower_id ON user_follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_following_id ON user_follows(following_id);
CREATE INDEX IF NOT EXISTS idx_strategy_comments_strategy_id ON strategy_comments(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_ratings_strategy_id ON strategy_ratings(strategy_id);
CREATE INDEX IF NOT EXISTS idx_user_leaderboard_pnl ON user_leaderboard(total_pnl DESC);
CREATE INDEX IF NOT EXISTS idx_user_leaderboard_win_rate ON user_leaderboard(win_rate DESC);
CREATE INDEX IF NOT EXISTS idx_kyc_verifications_user_id ON kyc_verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_kyc_verifications_status ON kyc_verifications(status);
CREATE INDEX IF NOT EXISTS idx_aml_checks_user_id ON aml_checks(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_device_registrations_user_id ON device_registrations(user_id);
CREATE INDEX IF NOT EXISTS idx_push_notifications_user_id ON push_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_data_ticker ON sentiment_data(ticker);
CREATE INDEX IF NOT EXISTS idx_news_feed_ticker ON news_feed(ticker);
CREATE INDEX IF NOT EXISTS idx_news_feed_published ON news_feed(published_at DESC);

CREATE INDEX IF NOT EXISTS idx_automation_jobs_user_id ON automation_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_automation_jobs_status ON automation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_automation_jobs_user_status ON automation_jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_automation_orders_job_id ON automation_orders(automation_job_id);
CREATE INDEX IF NOT EXISTS idx_automation_orders_status ON automation_orders(status);
CREATE INDEX IF NOT EXISTS idx_automation_events_job_id ON automation_events(automation_job_id);
CREATE INDEX IF NOT EXISTS idx_automation_events_type ON automation_events(event_type);

-- ============================================================================
-- PHASE 3: TRADING TOURNAMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS tournaments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE NOT NULL,
  status TEXT NOT NULL DEFAULT 'UPCOMING' CHECK (status IN ('UPCOMING', 'ACTIVE', 'COMPLETED', 'CANCELLED')),
  prize_pool NUMERIC(18,2) DEFAULT 0,
  max_entries INT,
  sort_metric TEXT DEFAULT 'final_pnl',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tournament_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tournament_id UUID NOT NULL REFERENCES tournaments(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  final_pnl NUMERIC(18,2) DEFAULT 0,
  final_sharpe NUMERIC(8,4) DEFAULT 0,
  final_win_rate NUMERIC(8,4) DEFAULT 0,
  rank INT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(tournament_id, user_id)
);

-- ============================================================================
-- PHASE 3: TRAILING ORDERS
-- ============================================================================

CREATE TABLE IF NOT EXISTS trailing_orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  asset TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
  order_type TEXT NOT NULL CHECK (order_type IN ('trailing_stop', 'trailing_take_profit')),
  direction TEXT DEFAULT 'LONG' CHECK (direction IN ('LONG', 'SHORT')),
  trail_percent NUMERIC(8,4) NOT NULL,
  quantity NUMERIC(18,8) NOT NULL,
  activation_price NUMERIC(18,8),
  stop_price NUMERIC(18,8),
  highest_price NUMERIC(18,8),
  lowest_price NUMERIC(18,8),
  triggered_price NUMERIC(18,8),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'triggered', 'cancelled')),
  triggered_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PHASE 3: ONCHAIN DATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS onchain_whale_movements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset TEXT NOT NULL,
  amount NUMERIC(18,8) NOT NULL,
  value_usd NUMERIC(18,2),
  from_address TEXT,
  to_address TEXT,
  movement_type TEXT CHECK (movement_type IN ('exchange_deposit', 'exchange_withdrawal', 'cold_storage', 'otc')),
  tx_hash TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS onchain_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset TEXT NOT NULL,
  mvrv NUMERIC(8,4),
  sopr NUMERIC(8,6),
  nvt_ratio NUMERIC(8,2),
  active_addresses_24h INT,
  exchange_balance_change_pct NUMERIC(8,4),
  miner_revenue_usd NUMERIC(18,2),
  realized_cap NUMERIC(18,2),
  market_cap NUMERIC(18,2),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS onchain_exchange_flows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset TEXT NOT NULL,
  exchange_inflow NUMERIC(18,8) DEFAULT 0,
  exchange_outflow NUMERIC(18,8) DEFAULT 0,
  net_flow NUMERIC(18,8) DEFAULT 0,
  inflow_value_usd NUMERIC(18,2),
  outflow_value_usd NUMERIC(18,2),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PHASE 3: INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tournaments_status ON tournaments(status);
CREATE INDEX IF NOT EXISTS idx_tournaments_start_time ON tournaments(start_time);
CREATE INDEX IF NOT EXISTS idx_tournament_entries_tournament_id ON tournament_entries(tournament_id);
CREATE INDEX IF NOT EXISTS idx_tournament_entries_user_id ON tournament_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_tournament_entries_pnl ON tournament_entries(final_pnl DESC);
CREATE INDEX IF NOT EXISTS idx_trailing_orders_user_id ON trailing_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_trailing_orders_asset_status ON trailing_orders(asset, status);
CREATE INDEX IF NOT EXISTS idx_trailing_orders_status ON trailing_orders(status);
CREATE INDEX IF NOT EXISTS idx_onchain_whale_asset ON onchain_whale_movements(asset);
CREATE INDEX IF NOT EXISTS idx_onchain_whale_timestamp ON onchain_whale_movements(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_onchain_metrics_asset ON onchain_metrics(asset);
CREATE INDEX IF NOT EXISTS idx_onchain_metrics_timestamp ON onchain_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_onchain_flows_asset ON onchain_exchange_flows(asset);
CREATE INDEX IF NOT EXISTS idx_onchain_flows_timestamp ON onchain_exchange_flows(timestamp DESC);

-- ============================================================================
-- EXECUTION SERVICE (§11.1) - Orders with State Machine
-- ============================================================================

CREATE TABLE IF NOT EXISTS orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  signal_id UUID,
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
  order_type TEXT DEFAULT 'MARKET' CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP_LOSS', 'TAKE_PROFIT')),
  quantity NUMERIC(18,8) NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  exchange_order_id TEXT,
  state TEXT NOT NULL DEFAULT 'PENDING' CHECK (state IN ('PENDING', 'CONFIRMED', 'FILLED', 'PARTIAL_FILL', 'FAILED', 'PENDING_CONFIRMATION', 'CANCELLED')),
  filled_quantity NUMERIC(18,8) DEFAULT 0,
  fill_price NUMERIC(18,8),
  failure_reason TEXT,
  confirmed_at TIMESTAMP WITH TIME ZONE,
  filled_at TIMESTAMP WITH TIME ZONE,
  failed_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_state ON orders(state);
CREATE INDEX IF NOT EXISTS idx_orders_idempotency_key ON orders(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_orders_exchange_order_id ON orders(exchange_order_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

-- ============================================================================
-- MARKET DATA VALIDATION (§7.2) - Anomaly & Gap Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_validation_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL CHECK (event_type IN ('DUPLICATE', 'OUTLIER', 'GAP', 'CLOCK_SKEW', 'CROSS_VENUE_DIVERGENCE')),
  ticker TEXT NOT NULL,
  details JSONB DEFAULT '{}'::jsonb,
  severity TEXT DEFAULT 'warning' CHECK (severity IN ('info', 'warning', 'critical')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_validation_events_ticker ON data_validation_events(ticker);
CREATE INDEX IF NOT EXISTS idx_validation_events_type ON data_validation_events(event_type);
CREATE INDEX IF NOT EXISTS idx_validation_events_created ON data_validation_events(created_at DESC);

-- ============================================================================
-- AUDIT LOG SERVICE (§28) - Enhanced with Event Types
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  actor TEXT DEFAULT 'system',
  details JSONB DEFAULT '{}'::jsonb,
  ip_address TEXT,
  user_agent TEXT,
  hash TEXT NOT NULL,
  prev_hash TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_actor ON audit_events(actor);

-- ============================================================================
-- DISCLAIMER ACKNOWLEDGMENTS (§6) - Per-Type Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS disclaimer_acknowledgments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  disclaimer_key TEXT NOT NULL,
  disclaimer_version TEXT,
  ts_version TEXT,
  acknowledged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  ip_address TEXT,
  UNIQUE(user_id, disclaimer_key)
);

CREATE INDEX IF NOT EXISTS idx_disclaimer_ack_user ON disclaimer_acknowledgments(user_id);
CREATE INDEX IF NOT EXISTS idx_disclaimer_ack_key ON disclaimer_acknowledgments(disclaimer_key);

-- ============================================================================
-- NOTIFICATION PREFERENCES (§15) - Per-User Channel Config
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  web_push_enabled BOOLEAN DEFAULT TRUE,
  telegram_enabled BOOLEAN DEFAULT TRUE,
  email_enabled BOOLEAN DEFAULT TRUE,
  discord_enabled BOOLEAN DEFAULT FALSE,
  telegram_chat_id TEXT,
  push_endpoint JSONB,
  signal_alerts BOOLEAN DEFAULT TRUE,
  trade_notifications BOOLEAN DEFAULT TRUE,
  risk_warnings BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notif_prefs_user ON notification_preferences(user_id);

-- ============================================================================
-- SENTIMENT ANALYSIS (§26.1) - NLP Pipeline Data
-- ============================================================================

CREATE TABLE IF NOT EXISTS sentiment_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  source TEXT NOT NULL,
  raw_text TEXT,
  sentiment_label TEXT CHECK (sentiment_label IN ('bullish', 'bearish', 'neutral')),
  sentiment_score NUMERIC(5,4),
  confidence NUMERIC(5,4),
  model_used TEXT DEFAULT 'vader',
  analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sentiment_analyses_ticker ON sentiment_analyses(ticker);
CREATE INDEX IF NOT EXISTS idx_sentiment_analyses_source ON sentiment_analyses(source);
CREATE INDEX IF NOT EXISTS idx_sentiment_analyses_analyzed ON sentiment_analyses(analyzed_at DESC);

-- ============================================================================
-- STRATEGY MARKETPLACE (§26.2) - Verification & Revenue
-- ============================================================================

CREATE TABLE IF NOT EXISTS strategy_verifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_id UUID NOT NULL REFERENCES creator_strategies(id) ON DELETE CASCADE,
  verification_status TEXT DEFAULT 'PENDING' CHECK (verification_status IN ('PENDING', 'UNDER_REVIEW', 'VERIFIED', 'REJECTED', 'EXPIRED')),
  claimed_sharpe NUMERIC(8,4),
  claimed_win_rate NUMERIC(8,4),
  platform_sharpe NUMERIC(8,4),
  platform_win_rate NUMERIC(8,4),
  paper_gate_start TIMESTAMP WITH TIME ZONE,
  paper_gate_end TIMESTAMP WITH TIME ZONE,
  paper_gate_status TEXT DEFAULT 'pending' CHECK (paper_gate_status IN ('pending', 'active', 'completed', 'failed')),
  verified_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategy_verifications_strategy ON strategy_verifications(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_verifications_status ON strategy_verifications(verification_status);

CREATE TABLE IF NOT EXISTS strategy_revenue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_id UUID NOT NULL REFERENCES creator_strategies(id) ON DELETE CASCADE,
  subscriber_count INT DEFAULT 0,
  monthly_fee NUMERIC(10,2) DEFAULT 0,
  gross_revenue NUMERIC(12,2) DEFAULT 0,
  creator_share NUMERIC(12,2) DEFAULT 0,
  platform_share NUMERIC(12,2) DEFAULT 0,
  commission_pct NUMERIC(4,2) DEFAULT 30.0,
  calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategy_revenue_strategy ON strategy_revenue(strategy_id);

-- ============================================================================
-- FEATURE STORE (§13.3)
-- ============================================================================

CREATE TABLE IF NOT EXISTS feature_vectors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  features JSONB NOT NULL,
  version TEXT DEFAULT 'v1',
  computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(ticker)
);

CREATE INDEX IF NOT EXISTS idx_feature_vectors_ticker ON feature_vectors(ticker);
CREATE INDEX IF NOT EXISTS idx_feature_vectors_version ON feature_vectors(version);

-- ============================================================================
-- IP WHITELISTING (§16.2)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ip_whitelist (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ip_address TEXT NOT NULL,
  label TEXT DEFAULT '',
  enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, ip_address)
);

CREATE INDEX IF NOT EXISTS idx_ip_whitelist_user ON ip_whitelist(user_id);
CREATE INDEX IF NOT EXISTS idx_ip_whitelist_ip ON ip_whitelist(ip_address);

-- ============================================================================
-- MARKETPLACE GOVERNANCE (§12)
-- ============================================================================

-- Creator payouts (§12)
CREATE TABLE IF NOT EXISTS creator_payouts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_id UUID NOT NULL REFERENCES creator_strategies(id) ON DELETE CASCADE,
  creator_user_id UUID REFERENCES users(id),
  payout_period TEXT NOT NULL,
  subscriber_count INT DEFAULT 0,
  gross_revenue NUMERIC(12,2) DEFAULT 0,
  alphaforge_cut_10_pct NUMERIC(12,2) DEFAULT 0,
  creator_take_home_90_pct NUMERIC(12,2) DEFAULT 0,
  status TEXT DEFAULT 'CALCULATED' CHECK (status IN ('CALCULATED', 'PAID', 'FAILED')),
  paid_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_creator_payouts_strategy ON creator_payouts(strategy_id);
CREATE INDEX IF NOT EXISTS idx_creator_payouts_period ON creator_payouts(payout_period);

-- Strategy appeals (§12)
CREATE TABLE IF NOT EXISTS strategy_appeals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  strategy_id UUID NOT NULL REFERENCES creator_strategies(id) ON DELETE CASCADE,
  creator_id UUID NOT NULL,
  reason TEXT NOT NULL,
  status TEXT DEFAULT 'PENDING_REVIEW' CHECK (status IN ('PENDING_REVIEW', 'APPROVED', 'DENIED')),
  reviewed_at TIMESTAMP WITH TIME ZONE,
  reviewer_notes TEXT,
  submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategy_appeals_strategy ON strategy_appeals(strategy_id);

-- Live performance tracking for auto-delisting (§12)
ALTER TABLE creator_strategies ADD COLUMN IF NOT EXISTS current_live_sharpe NUMERIC(8,4) DEFAULT NULL;
ALTER TABLE creator_strategies ADD COLUMN IF NOT EXISTS current_live_sharpe_last_updated TIMESTAMP WITH TIME ZONE DEFAULT NULL;
ALTER TABLE creator_strategies ADD COLUMN IF NOT EXISTS months_below_60_pct INT DEFAULT 0;

-- ============================================================================
-- SIGNAL PROOFS (§12.1)
-- ============================================================================

CREATE TABLE IF NOT EXISTS signal_proofs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id UUID NOT NULL,
  hypothesis_text TEXT NOT NULL,
  hypothesis_submitted_at TIMESTAMP WITH TIME ZONE NOT NULL,
  hypothesis_ipfs_hash TEXT,
  backtest_results JSONB,
  paper_trading_results JSONB,
  commitment_blockchain_tx TEXT,
  public_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signal_proofs_signal ON signal_proofs(signal_id);

"""


def run_additional_migrations(db):
    """Execute additional migrations for gap features."""
    try:
        from supabase import create_client
        result = db.supabase.rpc('exec_sql', {'sql': MIGRATIONS_ADDITIONAL})
        print("✅ Additional migrations for gap features completed successfully")
        return True
    except Exception as e:
        print(f"❌ Additional migrations failed: {e}")
        return False
