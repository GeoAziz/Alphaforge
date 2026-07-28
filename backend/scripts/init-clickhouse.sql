-- ClickHouse Schema for Analytics
-- High-volume time-series data

-- ==========================================================================
-- MARKET PRICES (Time-series)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS market_prices (
    timestamp DateTime64(3, 'UTC'),
    asset LowCardinality(String),
    exchange LowCardinality(String),
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    quote_volume Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (asset, exchange, timestamp)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- ==========================================================================
-- SIGNAL EVENTS
-- ==========================================================================
CREATE TABLE IF NOT EXISTS signal_events (
    timestamp DateTime64(3, 'UTC'),
    signal_id String,
    user_id String,
    ticker LowCardinality(String),
    signal_type LowCardinality(String),
    confidence Float64,
    entry_price Float64,
    source LowCardinality(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (signal_id, timestamp)
TTL timestamp + INTERVAL 2 YEARS;

-- ==========================================================================
-- TRADE EVENTS
-- ==========================================================================
CREATE TABLE IF NOT EXISTS trade_events (
    timestamp DateTime64(3, 'UTC'),
    trade_id String,
    user_id String,
    signal_id String,
    ticker LowCardinality(String),
    direction LowCardinality(String),
    quantity Float64,
    entry_price Float64,
    exit_price Nullable(Float64),
    pnl Nullable(Float64),
    status LowCardinality(String),
    exchange LowCardinality(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (trade_id, timestamp)
TTL timestamp + INTERVAL 2 YEARS;

-- ==========================================================================
-- PERFORMANCE METRICS
-- ==========================================================================
CREATE TABLE IF NOT EXISTS performance_metrics (
    timestamp DateTime64(3, 'UTC'),
    signal_id String,
    user_id String,
    daily_return Float64,
    cumulative_return Float64,
    sharpe_ratio Float64,
    max_drawdown Float64,
    win_rate Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (signal_id, timestamp);

-- ==========================================================================
-- API REQUEST METRICS
-- ==========================================================================
CREATE TABLE IF NOT EXISTS api_request_metrics (
    timestamp DateTime64(3, 'UTC'),
    endpoint LowCardinality(String),
    method LowCardinality(String),
    status_code UInt16,
    response_time_ms Float64,
    user_id String,
    ip_address String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (endpoint, timestamp)
TTL timestamp + INTERVAL 90 DAY;

-- ==========================================================================
-- USER ACTIVITY EVENTS
-- ==========================================================================
CREATE TABLE IF NOT EXISTS user_activity (
    timestamp DateTime64(3, 'UTC'),
    user_id String,
    event_type LowCardinality(String),
    event_data String,
    session_id String,
    platform LowCardinality(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, timestamp)
TTL timestamp + INTERVAL 1 YEAR;

-- ==========================================================================
-- MATERIALIZED VIEWS (Common analytics queries)
-- ==========================================================================

-- Hourly signal aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_signal_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, ticker, signal_type)
AS SELECT
    toStartOfHour(timestamp) AS hour,
    ticker,
    signal_type,
    count() AS signal_count,
    avg(confidence) AS avg_confidence
FROM signal_events
GROUP BY hour, ticker, signal_type;

-- Daily trade performance
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_trade_performance
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, user_id)
AS SELECT
    toStartOfDay(timestamp) AS day,
    user_id,
    count() AS trade_count,
    sum(pnl) AS total_pnl,
    avg(pnl) AS avg_pnl
FROM trade_events
WHERE pnl IS NOT NULL
GROUP BY day, user_id;
