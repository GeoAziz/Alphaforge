"""
Supabase schema migration SQL - Run once to set up the database structure.
"""

MIGRATION_SQL = """

-- ============================================================================
-- USERS & PROFILES
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  institution_name TEXT,
  plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'basic', 'pro', 'enterprise')),
  risk_tolerance TEXT DEFAULT 'moderate' CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
  kyc_status TEXT DEFAULT 'NOT_STARTED' CHECK (kyc_status IN ('NOT_STARTED', 'SUBMITTED', 'APPROVED', 'REJECTED', 'EXPIRED')),
  verification_stage TEXT DEFAULT 'stage_1_intro',
  onboarding_complete BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);


-- ============================================================================
-- SIGNALS
-- ============================================================================

CREATE TABLE IF NOT EXISTS signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  signal_type TEXT NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
  confidence NUMERIC(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  entry_price NUMERIC(20,8),
  stop_loss_price NUMERIC(20,8),
  take_profit_price NUMERIC(20,8),
  rationale TEXT,
  drivers JSONB DEFAULT '[]'::jsonb,
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE,
  performance_data JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_created_by ON signals(created_by);


-- ============================================================================
-- PORTFOLIOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS portfolios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  starting_balance NUMERIC(18,2) DEFAULT 100000,
  current_balance NUMERIC(18,2) DEFAULT 100000,
  total_pnl NUMERIC(18,2) DEFAULT 0,
  total_pnl_percent NUMERIC(8,4) DEFAULT 0,
  total_trades INT DEFAULT 0,
  win_count INT DEFAULT 0,
  loss_count INT DEFAULT 0,
  open_positions INT DEFAULT 0,
  sharpe_ratio NUMERIC(8,4),
  max_drawdown NUMERIC(8,4),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);


-- ============================================================================
-- PAPER TRADES
-- ============================================================================

CREATE TABLE IF NOT EXISTS paper_trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  signal_id UUID REFERENCES signals(id) ON DELETE SET NULL,
  asset TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
  entry_price NUMERIC(20,8) NOT NULL,
  quantity NUMERIC(18,8) NOT NULL,
  stop_loss NUMERIC(20,8),
  take_profit NUMERIC(20,8),
  exit_price NUMERIC(20,8),
  status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'PENDING', 'LIQUIDATED', 'CANCELLED')),
  pnl NUMERIC(18,8),
  pnl_percent NUMERIC(8,4),
  opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  closed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_paper_trades_user_id ON paper_trades(user_id);
CREATE INDEX IF NOT EXISTS idx_paper_trades_signal_id ON paper_trades(signal_id);
CREATE INDEX IF NOT EXISTS idx_paper_trades_created ON paper_trades(opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_trades_status ON paper_trades(status);


-- ============================================================================
-- POSITIONS (Current open positions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS positions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ticker TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
  entry_price NUMERIC(20,8) NOT NULL,
  quantity NUMERIC(18,8) NOT NULL,
  current_price NUMERIC(20,8),
  unrealized_pnl NUMERIC(18,8),
  unrealized_pnl_percent NUMERIC(8,4),
  risk_exposure_pct NUMERIC(8,4),
  signal_id UUID REFERENCES signals(id) ON DELETE SET NULL,
  opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_user_id ON positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_ticker ON positions(ticker);


-- ============================================================================
-- CREATORS & VERIFICATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS creator_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  verification_stage TEXT DEFAULT 'stage_1_intro',
  total_signals_created INT DEFAULT 0,
  win_rate NUMERIC(8,4) DEFAULT 0,
  avg_confidence NUMERIC(3,2) DEFAULT 0,
  total_followers INT DEFAULT 0,
  verified_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_creator_profiles_user_id ON creator_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_creator_profiles_verification ON creator_profiles(verification_stage);


-- ============================================================================
-- KYC/AML VERIFICATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS kyc_verifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  status TEXT DEFAULT 'NOT_STARTED' CHECK (status IN ('NOT_STARTED', 'SUBMITTED', 'APPROVED', 'REJECTED', 'EXPIRED')),
  onfido_applicant_id TEXT,
  onfido_check_id TEXT,
  aml_status TEXT,
  aml_reason TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  verified_data JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_kyc_verifications_user_id ON kyc_verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_kyc_verifications_status ON kyc_verifications(status);


-- ============================================================================
-- AUDIT LOG (Immutable)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  changes JSONB DEFAULT '{}'::jsonb,
  ip_address INET,
  user_agent TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  hash_chain TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);


-- ============================================================================
-- EXTERNAL SIGNALS (TradingView webhooks, external sources)
-- ============================================================================

CREATE TABLE IF NOT EXISTS external_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  signal_type TEXT NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
  price NUMERIC(20,8),
  source TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_external_signals_ticker ON external_signals(ticker);
CREATE INDEX IF NOT EXISTS idx_external_signals_source ON external_signals(source);
CREATE INDEX IF NOT EXISTS idx_external_signals_created_at ON external_signals(created_at DESC);


-- ============================================================================
-- API KEYS (For exchange connections)
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  exchange TEXT NOT NULL,
  api_key_encrypted TEXT NOT NULL,
  api_secret_encrypted TEXT NOT NULL,
  permissions JSONB DEFAULT '{"read": true, "trade": false}'::jsonb,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_verified_at TIMESTAMP WITH TIME ZONE,
  UNIQUE(user_id, exchange)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_exchange ON api_keys(exchange);


-- ============================================================================
-- STRATEGIES (User-created or platform strategies)
-- ============================================================================

CREATE TABLE IF NOT EXISTS strategies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  name TEXT NOT NULL,
  description TEXT,
  parameters JSONB DEFAULT '{}'::jsonb,
  is_public BOOLEAN DEFAULT FALSE,
  total_signals INT DEFAULT 0,
  win_rate NUMERIC(8,4),
  sharpe_ratio NUMERIC(8,4),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_is_public ON strategies(is_public);


-- ============================================================================
-- NOTIFICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  message TEXT,
  notification_type TEXT,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);


-- ============================================================================
-- CHAT MESSAGES
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  role TEXT CHECK (role IN ('user', 'assistant')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);


-- ============================================================================
-- CREATOR PROFILES & STRATEGIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS creator_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  total_signals_created INT DEFAULT 0,
  win_rate NUMERIC(8,4) DEFAULT 0,
  avg_confidence NUMERIC(8,4) DEFAULT 0,
  total_followers INT DEFAULT 0,
  reputation_score NUMERIC(4,1) DEFAULT 0,
  verified_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_creator_profiles_user_id ON creator_profiles(user_id);


CREATE TABLE IF NOT EXISTS creator_strategies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  parameters JSONB DEFAULT '{}'::jsonb,
  backtest_results JSONB DEFAULT '{}'::jsonb,
  status TEXT DEFAULT 'PENDING_REVIEW' CHECK (status IN ('PENDING_REVIEW', 'APPROVED', 'REJECTED')),
  popularity INT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_creator_strategies_user_id ON creator_strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_creator_strategies_status ON creator_strategies(status);


-- ============================================================================
-- STRATEGY SUBSCRIPTIONS & PAPER TRADING
-- ============================================================================

CREATE TABLE IF NOT EXISTS strategy_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  strategy_id UUID NOT NULL REFERENCES creator_strategies(id) ON DELETE CASCADE,
  allocation_pct NUMERIC(8,4) DEFAULT 10,
  status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'PAUSED', 'CANCELLED')),
  subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategy_subscriptions_user_id ON strategy_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_subscriptions_strategy_id ON strategy_subscriptions(strategy_id);


CREATE TABLE IF NOT EXISTS strategy_paper_trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  strategy_id UUID NOT NULL REFERENCES creator_strategies(id) ON DELETE CASCADE,
  initial_capital NUMERIC(18,2),
  current_capital NUMERIC(18,2),
  status TEXT DEFAULT 'RUNNING' CHECK (status IN ('RUNNING', 'COMPLETED', 'STOPPED')),
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_strategy_paper_trades_user_id ON strategy_paper_trades(user_id);
CREATE INDEX IF NOT EXISTS idx_strategy_paper_trades_strategy_id ON strategy_paper_trades(strategy_id);


-- ============================================================================
-- BACKTESTING
-- ============================================================================

CREATE TABLE IF NOT EXISTS backtests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  strategy_name TEXT NOT NULL,
  strategy_params JSONB DEFAULT '{}'::jsonb,
  symbols TEXT[] DEFAULT '["BTC","ETH"]'::text[],
  start_date DATE,
  end_date DATE,
  initial_capital NUMERIC(18,2) DEFAULT 100000,
  status TEXT DEFAULT 'RUNNING' CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED')),
  results JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_backtests_user_id ON backtests(user_id);
CREATE INDEX IF NOT EXISTS idx_backtests_status ON backtests(status);


-- ============================================================================
-- USER RISK SETTINGS & EXTERNAL SIGNAL RULES
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_risk_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  max_position_size_pct NUMERIC(8,4) DEFAULT 2.0,
  max_portfolio_exposure_pct NUMERIC(8,4) DEFAULT 20.0,
  max_leverage NUMERIC(8,4) DEFAULT 5.0,
  stop_loss_default NUMERIC(8,4) DEFAULT 2.0,
  take_profit_default NUMERIC(8,4) DEFAULT 5.0,
  daily_loss_limit_pct NUMERIC(8,4) DEFAULT 10.0,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_risk_settings_user_id ON user_risk_settings(user_id);


CREATE TABLE IF NOT EXISTS external_signal_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  rules JSONB DEFAULT '{}'::jsonb,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_external_signal_rules_user_id ON external_signal_rules(user_id);


-- ============================================================================
-- ENABLE Row Level Security (RLS)
-- ============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE backtests ENABLE ROW LEVEL SECURITY;
ALTER TABLE creator_strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategy_subscriptions ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can see own data" ON users
  FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can see own portfolio" ON portfolios
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can see own trades" ON paper_trades
  FOR SELECT USING (auth.uid()::text = user_id::text);

-- Insert permissions
CREATE POLICY "Users can insert own trades" ON paper_trades
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own positions" ON positions
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

"""


def run_migrations(db):
    """Execute migration SQL against Supabase."""
    try:
        from supabase import create_client
        result = db.supabase.rpc('exec_sql', {'sql': MIGRATION_SQL})
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
