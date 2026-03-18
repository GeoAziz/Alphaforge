"""
Configuration and environment utilities.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # Environment
    ENV = os.getenv("API_ENV", "development")
    DEBUG = ENV == "development"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    
    # Signal Processing
    SIGNAL_PROCESSOR_INTERVAL = int(os.getenv("SIGNAL_PROCESSOR_INTERVAL", 300))
    NUM_TOP_SIGNALS = int(os.getenv("NUM_TOP_SIGNALS", 50))
    
    # External APIs
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    POLYGON_IO_API_KEY = os.getenv("POLYGON_IO_API_KEY")
    TRADINGVIEW_WEBHOOK_SECRET = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")
    
    # Paper Trading
    INITIAL_PAPER_BALANCE = float(os.getenv("INITIAL_PAPER_BALANCE", 100000))
    PAPER_TRADING_SLIPPAGE = float(os.getenv("PAPER_TRADING_SLIPPAGE", 0.001))
    
    # Risk Management
    MAX_POSITION_SIZE_PCT = float(os.getenv("MAX_POSITION_SIZE_PCT", 0.02))
    MAX_PORTFOLIO_EXPOSURE_PCT = float(os.getenv("MAX_PORTFOLIO_EXPOSURE_PCT", 0.20))
    MAX_LEVERAGE = int(os.getenv("MAX_LEVERAGE", 5))
    LIQUIDATION_BUFFER_PCT = float(os.getenv("LIQUIDATION_BUFFER_PCT", 0.20))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Security / Runtime Hardening
    CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")
    TRUSTED_HOSTS = os.getenv("TRUSTED_HOSTS", "*")
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))
    RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 120))
    SECURITY_HEADERS_ENABLED = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"

    # Database strictness
    ALLOW_MOCK_DB_FALLBACK = os.getenv("ALLOW_MOCK_DB_FALLBACK", "true").lower() == "true"
    REQUIRE_REAL_DB = os.getenv("REQUIRE_REAL_DB", "false").lower() == "true"
    REQUIRED_DB_TABLES = os.getenv(
        "REQUIRED_DB_TABLES",
        "users,signals,paper_trades,positions,portfolios,creator_profiles,kyc_verifications,audit_logs,external_signals,api_keys,strategies,creator_strategies,strategy_subscriptions,strategy_paper_trades,backtests,chat_messages,notifications,user_risk_settings,external_signal_rules",
    )


def validate_config():
    """Validate required configuration based on environment."""
    env = (Config.ENV or "development").lower()

    common_required = {
        "SUPABASE_URL": Config.SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": Config.SUPABASE_KEY,
    }

    production_required = {
        "DATABASE_URL": Config.DATABASE_URL,
        "SUPABASE_ANON_KEY": Config.SUPABASE_ANON_KEY,
    }

    missing = [key for key, value in common_required.items() if not value]

    if env == "production":
        missing.extend([key for key, value in production_required.items() if not value])

    if missing:
        raise ValueError(f"Missing required config for {env}: {', '.join(missing)}")

    print(f"✅ Configuration validated for {env}")


def is_production() -> bool:
    return (Config.ENV or "development").lower() == "production"


def get_required_tables() -> list[str]:
    return [table.strip() for table in Config.REQUIRED_DB_TABLES.split(",") if table.strip()]


class SignalConfig:
    """Signal processing configuration."""
    
    MIN_CONFIDENCE = 0.5
    MAX_SIGNALS_PER_TICKER = 1
    SIGNAL_EXPIRY_HOURS = 24
    SIGNAL_SOURCES = ["alpha_vantage", "polygon", "tradingview"]


class RiskConfig:
    """Risk management configuration."""
    
    MAX_POSITION_SIZE_PCT = 0.02
    MAX_PORTFOLIO_EXPOSURE_PCT = 0.20
    MAX_LEVERAGE = 5
    LIQUIDATION_BUFFER_PCT = 0.20
    MAX_CORRELATION = 0.8
    MAX_DAILY_LOSS_PCT = 0.10


class PaperTradingConfig:
    """Paper trading configuration."""
    
    DEFAULT_STARTING_BALANCE = 100000
    DEFAULT_SLIPPAGE = 0.001  # 0.1%
    MINIMUM_SHARPE_FOR_LAUNCH = 0.80  # 80% of backtest sharpe
    PAPER_TRADING_DURATION_DAYS = 28  # 4 weeks
