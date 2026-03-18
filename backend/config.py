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
    
    # Firebase Configuration (Backend Token Verification & Admin Operations)
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
    FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
    FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID")
    FIREBASE_APP_ID = os.getenv("FIREBASE_APP_ID")
    FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "./serviceAccountKey.json")
    FIREBASE_ENABLED = os.getenv("FIREBASE_ENABLED", "false").lower() == "true"
    
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

    # Cache Configuration
    CACHE_BACKEND = os.getenv("CACHE_BACKEND", "memory")  # "redis" or "memory"
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    
    # Cache TTLs (seconds)
    CACHE_TTL_TICKER = int(os.getenv("CACHE_TTL_TICKER", 10))  # 10 seconds for live tickers
    CACHE_TTL_OHLCV = int(os.getenv("CACHE_TTL_OHLCV", 60))  # 1 minute for OHLCV
    CACHE_TTL_SENTIMENT = int(os.getenv("CACHE_TTL_SENTIMENT", 300))  # 5 minutes for sentiment
    CACHE_TTL_METADATA = int(os.getenv("CACHE_TTL_METADATA", 3600))  # 1 hour for metadata
    
    # Data Source Configuration
    DATA_SOURCE_PRIMARY = os.getenv("DATA_SOURCE_PRIMARY", "binance")  # Primary source for crypto
    DATA_SOURCE_SECONDARY = os.getenv("DATA_SOURCE_SECONDARY", "coingecko")  # Fallback
    ENABLE_POLYGON = os.getenv("ENABLE_POLYGON", "false").lower() == "true"
    
    # CoinGecko API
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")  # Free tier (optional)
    
    # Technical Analysis
    RSI_PERIOD = int(os.getenv("RSI_PERIOD", 14))
    MACD_FAST = int(os.getenv("MACD_FAST", 12))
    MACD_SLOW = int(os.getenv("MACD_SLOW", 26))
    MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", 9))
    BB_PERIOD = int(os.getenv("BB_PERIOD", 20))
    BB_STD_DEV = float(os.getenv("BB_STD_DEV", 2.0))
    
    # Signal Generation Thresholds
    RSI_OVERBOUGHT = int(os.getenv("RSI_OVERBOUGHT", 70))
    RSI_OVERSOLD = int(os.getenv("RSI_OVERSOLD", 30))
    MIN_SIGNAL_CONFIDENCE = float(os.getenv("MIN_SIGNAL_CONFIDENCE", 0.5))

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
