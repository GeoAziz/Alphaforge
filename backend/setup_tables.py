#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn_str = os.getenv("DATABASE_URL")

migrations = [
    "CREATE TABLE IF NOT EXISTS signal_performance (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), signal_id TEXT NOT NULL UNIQUE, asset TEXT NOT NULL, direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')), entry_price NUMERIC(20,8) NOT NULL, exit_price NUMERIC(20,8), pnl NUMERIC(18,8), roi_pct NUMERIC(8,4), is_winning BOOLEAN, outcome TEXT CHECK (outcome IN ('WINNING_TRADE', 'LOSING_TRADE')), execution_timestamp TIMESTAMP WITH TIME ZONE, position_size NUMERIC(18,8), created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW())",
    "CREATE INDEX IF NOT EXISTS idx_signal_performance_asset ON signal_performance(asset)",
    "CREATE INDEX IF NOT EXISTS idx_signal_performance_is_winning ON signal_performance(is_winning)",
    "CREATE INDEX IF NOT EXISTS idx_signal_performance_created ON signal_performance(created_at DESC)",
    "CREATE TABLE IF NOT EXISTS signal_sources (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), external_source TEXT NOT NULL UNIQUE, total_signals_received INT DEFAULT 0, total_signals_executed INT DEFAULT 0, signals_ignored INT DEFAULT 0, executed_win_rate NUMERIC(8,4) DEFAULT 0, total_pnl NUMERIC(18,2) DEFAULT 0, reliability_score NUMERIC(8,4) DEFAULT 0, recommendation TEXT, last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW())",
    "CREATE INDEX IF NOT EXISTS idx_signal_sources_reliability ON signal_sources(reliability_score DESC)",
    "CREATE TABLE IF NOT EXISTS market_correlations (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), asset1 TEXT NOT NULL, asset2 TEXT NOT NULL, correlation_1d NUMERIC(5,3), correlation_7d NUMERIC(5,3), correlation_30d NUMERIC(5,3), volatility_1d NUMERIC(8,6), volatility_7d NUMERIC(8,6), volatility_30d NUMERIC(8,6), trend_strength_1d NUMERIC(5,3), trend_strength_7d NUMERIC(5,3), trend_strength_30d NUMERIC(5,3), divergence_detected BOOLEAN DEFAULT FALSE, divergence_strength NUMERIC(5,3), created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), UNIQUE(asset1, asset2))",
    "CREATE INDEX IF NOT EXISTS idx_market_correlations_assets ON market_correlations(asset1, asset2)",
    "CREATE INDEX IF NOT EXISTS idx_market_correlations_divergence ON market_correlations(divergence_detected)",
]

try:
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()
    
    for i, migration in enumerate(migrations, 1):
        try:
            cursor.execute(migration)
            conn.commit()
            print(f"✅ Migration {i}/{len(migrations)} executed")
        except psycopg2.errors.Error as e:
            conn.rollback()
            print(f"⚠️  Migration {i} skipped: {str(e)[:100]}")
    
    cursor.close()
    conn.close()
    print("\n✅ All table migrations completed")
    
except Exception as e:
    print(f"❌ Failed: {e}")
