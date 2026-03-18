-- AlphaForge Recommendations Implementation Migration
-- Adds tables for signal performance tracking, external signal validation, and correlation data

BEGIN;

-- ============================================================================
-- Table 1: SIGNAL PERFORMANCE (Track real outcome of generated signals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS signal_performance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id UUID NOT NULL UNIQUE REFERENCES signals(id) ON DELETE CASCADE,
  
  -- Execution tracking
  num_times_executed INT DEFAULT 0,
  num_times_closed INT DEFAULT 0,
  
  -- Performance metrics
  total_pnl NUMERIC(18,8) DEFAULT 0,
  avg_pnl_per_execution NUMERIC(18,8),
  win_count INT DEFAULT 0,
  loss_count INT DEFAULT 0,
  win_rate NUMERIC(5,4),           -- 0.58 = 58%
  
  -- Returns
  total_roi_pct NUMERIC(8,4),       -- 0.1234 = 12.34%
  avg_roi_per_execution NUMERIC(8,4),
  
  -- Risk metrics
  best_trade_pnl NUMERIC(18,8),
  worst_trade_pnl NUMERIC(18,8),
  max_drawdown_pct NUMERIC(8,4),
  sharpe_ratio NUMERIC(8,4),
  
  -- Timing
  first_execution_at TIMESTAMP WITH TIME ZONE,
  last_execution_at TIMESTAMP WITH TIME ZONE,
  last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Metadata
  signal_accuracy_score NUMERIC(5,4),  -- 0-1 scale, ML confidence in signal quality
  is_high_performer BOOLEAN DEFAULT FALSE,  -- Signals with >60% win rate + >10% ROI
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signal_performance_signal_id ON signal_performance(signal_id);
CREATE INDEX IF NOT EXISTS idx_signal_performance_win_rate ON signal_performance(win_rate DESC);
CREATE INDEX IF NOT EXISTS idx_signal_performance_roi ON signal_performance(total_roi_pct DESC);
CREATE INDEX IF NOT EXISTS idx_signal_performance_high_performer ON signal_performance(is_high_performer);

COMMENT ON TABLE signal_performance IS 'Tracks real-world performance of generated signals for quality assessment';

-- ============================================================================
-- Table 2: EXTERNAL SIGNAL PERFORMANCE (Validate third-party signals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS external_signal_performance (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  external_source TEXT NOT NULL CHECK (external_source IN ('tradingview', 'pine_script', 'webhook', 'telegram', 'other')),
  
  -- Aggregated metrics per source per user
  period_start_date DATE NOT NULL,
  period_end_date DATE NOT NULL,
  
  -- Source-level statistics
  total_signals_received INT DEFAULT 0,
  total_signals_executed INT DEFAULT 0,
  signals_ignored INT DEFAULT 0,
  
  -- Performance tracking
  executed_win_count INT DEFAULT 0,
  executed_loss_count INT DEFAULT 0,
  executed_win_rate NUMERIC(5,4),
  
  -- ROI tracking
  total_pnl NUMERIC(18,8) DEFAULT 0,
  total_roi_pct NUMERIC(8,4),
  avg_roi_per_trade NUMERIC(8,4),
  
  -- Risk assessment
  max_drawdown_pct NUMERIC(8,4),
  largest_win NUMERIC(18,8),
  largest_loss NUMERIC(18,8),
  avg_win_size NUMERIC(18,8),
  avg_loss_size NUMERIC(18,8),
  
  -- Reliability score
  reliability_score NUMERIC(5,4),  -- 0-1, based on accuracy + consistency
  recommendation TEXT,  -- "HIGHLY_TRUSTED", "RELIABLE", "MARGINAL", "UNRELIABLE"
  
  -- Metadata
  tracked_since TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_signal_at TIMESTAMP WITH TIME ZONE,
  last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_external_signal_perf_user ON external_signal_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_external_signal_perf_source ON external_signal_performance(external_source);
CREATE INDEX IF NOT EXISTS idx_external_signal_perf_reliability ON external_signal_performance(reliability_score DESC);

COMMENT ON TABLE external_signal_performance IS 'Tracks accuracy and reliability of external signal sources (webhooks, TradingView, etc)';

-- ============================================================================
-- Table 3: MARKET CORRELATION MATRIX (Cross-asset analysis)
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_correlations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Asset pair
  asset1 TEXT NOT NULL,  -- BTC, ETH, SOL, etc
  asset2 TEXT NOT NULL,
  
  -- Correlation metrics (1D, 7D, 30D windows)
  correlation_1d NUMERIC(5,4),      -- -1 to 1
  correlation_7d NUMERIC(5,4),
  correlation_30d NUMERIC(5,4),
  
  -- Volatility
  volatility_1d NUMERIC(8,4),       -- Standard deviation of returns
  volatility_7d NUMERIC(8,4),
  volatility_30d NUMERIC(8,4),
  
  -- Trend strength (0-1, how much assets move together)
  trend_strength_1d NUMERIC(5,4),
  trend_strength_7d NUMERIC(5,4),
  trend_strength_30d NUMERIC(5,4),
  
  -- Divergence tracking (when historically correlated assets diverge)
  divergence_detected BOOLEAN DEFAULT FALSE,
  divergence_strength NUMERIC(5,4),  -- How unusual is this divergence? (0-1)
  
  -- Metadata
  last_computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  data_points_used INT DEFAULT 100,  -- How many candles analyzed
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_corr_asset1 ON market_correlations(asset1);
CREATE INDEX IF NOT EXISTS idx_market_corr_asset2 ON market_correlations(asset2);
CREATE INDEX IF NOT EXISTS idx_market_corr_pairs ON market_correlations(asset1, asset2);
CREATE INDEX IF NOT EXISTS idx_market_corr_divergence ON market_correlations(divergence_detected);

COMMENT ON TABLE market_correlations IS 'Stores cross-asset correlations for signal validation (avoid conflicting signals)';

-- ============================================================================
-- Table 4: USER-SPECIFIC CACHE METADATA (Cache optimization)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_cache_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  
  -- Cache preferences
  cache_backend TEXT DEFAULT 'memory' CHECK (cache_backend IN ('memory', 'redis')),
  cache_ttl_ticker INT DEFAULT 10,    -- seconds
  cache_ttl_portfolio INT DEFAULT 5,  -- short-lived, updated frequently
  cache_ttl_signals INT DEFAULT 60,   -- signals change every minute
  
  -- Performance tracking
  cache_hit_rate NUMERIC(5,4),  -- 0.85 = 85%
  avg_cache_lookup_ms NUMERIC(8,2),
  
  -- Preferences
  enable_aggressive_caching BOOLEAN DEFAULT FALSE,  -- Cache more data for faster reads
  enable_user_specific_cache BOOLEAN DEFAULT TRUE,
  
  last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_cache_preferences_user ON user_cache_preferences(user_id);

COMMENT ON TABLE user_cache_preferences IS 'User-level cache configuration and performance metrics';

-- ============================================================================
-- Table 5: WEBSOCKET CONNECTION LOG (Track real-time subscriptions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS websocket_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Connection tracking
  connection_id TEXT UNIQUE NOT NULL,
  subscribed_channels TEXT[] DEFAULT '{}',  -- ["market-updates", "portfolio-updates", "signals"]
  
  -- Session info
  connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  disconnected_at TIMESTAMP WITH TIME ZONE,
  connection_duration_seconds INT,
  
  -- Performance metrics
  messages_sent INT DEFAULT 0,
  messages_received INT DEFAULT 0,
  latency_ms NUMERIC(8,2),  -- Average round-trip latency
  
  -- Status
  is_active BOOLEAN DEFAULT TRUE,
  last_heartbeat_at TIMESTAMP WITH TIME ZONE,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ws_connections_user ON websocket_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_ws_connections_active ON websocket_connections(is_active);

COMMENT ON TABLE websocket_connections IS 'Tracks WebSocket connections for real-time data delivery';

-- ============================================================================
-- Alter existing tables to support new features
-- ============================================================================

-- Add columns to signals table if not exist
ALTER TABLE IF EXISTS signals
ADD COLUMN IF NOT EXISTS is_tracked_for_performance BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS performance_status TEXT DEFAULT 'pending' CHECK (performance_status IN ('pending', 'closed', 'expired'));

-- Add columns to external_signals table if not exist
ALTER TABLE IF EXISTS external_signals
ADD COLUMN IF NOT EXISTS is_tracked_for_quality BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS quality_score NUMERIC(5,4) DEFAULT 0;

-- Add column to paper_trades to link to external signals
ALTER TABLE IF EXISTS paper_trades
ADD COLUMN IF NOT EXISTS external_signal_id UUID REFERENCES external_signals(id) ON DELETE SET NULL;

COMMIT;
