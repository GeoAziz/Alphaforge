-- AlphaForge Database Performance Optimization
-- Run these commands to optimize query performance

-- ============================================================================
-- INDEXES FOR CRITICAL QUERIES
-- ============================================================================

-- User queries
CREATE INDEX IF NOT EXISTS idx_users_firebase_uid_created_at
  ON users(firebase_uid, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_users_kyc_status_verification_stage
  ON users(kyc_status, verification_stage);

-- Signal queries
CREATE INDEX IF NOT EXISTS idx_signals_confidence_created_at
  ON signals(confidence DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_signals_created_by_ticker
  ON signals(created_by, ticker);

CREATE INDEX IF NOT EXISTS idx_signals_expires_at
  ON signals(expires_at) WHERE expires_at IS NOT NULL;

-- Paper trades (critical for portfolio calculations)
CREATE INDEX IF NOT EXISTS idx_paper_trades_user_status
  ON paper_trades(user_id, status);

CREATE INDEX IF NOT EXISTS idx_paper_trades_opened_at_user
  ON paper_trades(user_id, opened_at DESC);

CREATE INDEX IF NOT EXISTS idx_paper_trades_signal_id
  ON paper_trades(signal_id);

-- Portfolio queries
CREATE INDEX IF NOT EXISTS idx_portfolios_user_updated_at
  ON portfolios(user_id, updated_at DESC);

-- Positions (real-time lookups)
CREATE INDEX IF NOT EXISTS idx_positions_user_ticker
  ON positions(user_id, ticker);

CREATE INDEX IF NOT EXISTS idx_positions_user_opened_at
  ON positions(user_id, opened_at DESC);

-- Chat messages (history queries)
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_created
  ON chat_messages(user_id, created_at DESC)
  WHERE deleted_at IS NULL;

-- Strategies
CREATE INDEX IF NOT EXISTS idx_strategies_creator_status
  ON strategies(creator_id, status);

CREATE INDEX IF NOT EXISTS idx_strategies_public_rating
  ON strategies(public, rating DESC)
  WHERE status = 'ACTIVE';

-- ============================================================================
-- PERFORMANCE TUNING
-- ============================================================================

-- Increase work memory for complex queries (adjust based on server memory)
SET work_mem = '256MB';

-- Increase maintenance work memory for index creation
SET maintenance_work_mem = '512MB';

-- Enable parallel query execution for large tables
ALTER TABLE paper_trades SET (parallel_workers = 4);
ALTER TABLE signals SET (parallel_workers = 4);
ALTER TABLE users SET (parallel_workers = 2);

-- ============================================================================
-- QUERY ANALYSIS - RUN THESE TO CHECK PERFORMANCE
-- ============================================================================

-- Get slowest queries
/*
SELECT
  query,
  calls,
  mean_exec_time,
  max_exec_time,
  total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
*/

-- Check table sizes
/*
SELECT
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
*/

-- Check index usage
/*
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
*/

-- ============================================================================
-- VACUUM & ANALYZE
-- ============================================================================

-- Analyze all tables (recommended weekly)
ANALYZE;

-- Vacuum all tables (recommended nightly)
VACUUM ANALYZE;

-- ============================================================================
-- CRITICAL MATERIALIZED VIEWS FOR FAST PORTFOLIO QUERIES
-- ============================================================================

-- Portfolio metrics (refreshed every 5 minutes)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_portfolio_metrics AS
SELECT
  u.id as user_id,
  COUNT(CASE WHEN pt.status = 'CLOSED' THEN 1 END) as total_closed_trades,
  COUNT(CASE WHEN pt.status = 'OPEN' THEN 1 END) as open_positions,
  SUM(CASE WHEN pt.status = 'CLOSED' AND pt.pnl > 0 THEN 1 END) as win_count,
  SUM(CASE WHEN pt.status = 'CLOSED' AND pt.pnl <= 0 THEN 1 END) as loss_count,
  COALESCE(AVG(pt.pnl_percent), 0) as avg_pnl_percent,
  COALESCE(SUM(pt.pnl), 0) as total_realized_pnl,
  p.current_balance,
  p.starting_balance,
  NOW() as last_updated
FROM users u
LEFT JOIN paper_trades pt ON u.id = pt.user_id
LEFT JOIN portfolios p ON u.id = p.user_id
GROUP BY u.id, p.current_balance, p.starting_balance;

CREATE INDEX IF NOT EXISTS idx_mv_portfolio_user_id ON mv_portfolio_metrics(user_id);

-- Signal performance leaderboard (top signals)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_signal_leaderboard AS
SELECT
  s.id,
  s.ticker,
  s.created_by,
  COUNT(pt.id) as total_trades,
  SUM(CASE WHEN pt.pnl > 0 THEN 1 END) as wins,
  ROUND(100.0 * SUM(CASE WHEN pt.pnl > 0 THEN 1 END) / COUNT(pt.id), 2) as win_rate,
  COALESCE(AVG(pt.pnl_percent), 0) as avg_return,
  MAX(pt.pnl_percent) as best_trade,
  MIN(pt.pnl_percent) as worst_trade
FROM signals s
LEFT JOIN paper_trades pt ON s.id = pt.signal_id
WHERE s.created_at > NOW() - INTERVAL '30 days'
GROUP BY s.id, s.ticker, s.created_by
HAVING COUNT(pt.id) > 0
ORDER BY win_rate DESC;

CREATE INDEX IF NOT EXISTS idx_mv_leaderboard_created_by ON mv_signal_leaderboard(created_by);

-- ============================================================================
-- REFRESH STRATEGY
-- ============================================================================

-- Refresh materialized views (add to scheduled jobs/cron)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_portfolio_metrics;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_signal_leaderboard;

-- ============================================================================
-- PARTITIONING FOR VERY LARGE TABLES (if needed)
-- ============================================================================

-- Partition paper_trades by month (for 1M+ rows)
/*
CREATE TABLE paper_trades_2024_01 PARTITION OF paper_trades
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE paper_trades_2024_02 PARTITION OF paper_trades
  FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
*/

-- ============================================================================
-- MONITORING QUERIES
-- ============================================================================

-- Monitor slow queries during runtime
/*
SET log_min_duration_statement = 1000; -- Log queries taking > 1 second
SET log_statement = 'all'; -- Log all statements (be careful in prod)
*/

-- Check active connections
/*
SELECT datname, usename, application_name, state, count(*)
FROM pg_stat_activity
GROUP BY datname, usename, application_name, state;
*/

-- Check table locks
/*
SELECT
  t.schemaname,
  t.tablename,
  l.locktype,
  l.database,
  l.page,
  l.tuple,
  l.virtualxid,
  l.transactionid,
  l.classid,
  l.objid,
  l.objsubid,
  l.virtualtransactionid,
  l.pid,
  l.mode,
  l.granted
FROM pg_locks l
JOIN pg_tables t ON l.relation = t.tableoid
WHERE t.schemaname = 'public';
*/
