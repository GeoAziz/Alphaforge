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
         "users,signals,paper_trades,positions,portfolios,creator_profiles,kyc_verifications,audit_logs,external_signals,api_keys,strategies,creator_strategies,strategy_subscriptions,strategy_paper_trades,backtests,chat_messages,notifications,user_risk_settings,external_signal_rules,user_strategies,strategy_templates,education_content,signal_breakdowns,user_education_progress",
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


# ============================================================================
# FEATURE FLAGS
# ============================================================================

class FeatureFlags:
    """Feature enablement flags."""

    BACKTESTING = os.getenv("FEATURE_BACKTESTING", "true").lower() == "true"
    LIVE_TRADING = os.getenv("FEATURE_LIVE_TRADING", "false").lower() == "true"
    KYC = os.getenv("FEATURE_KYC", "false").lower() == "true"
    MOBILE_APP = os.getenv("FEATURE_MOBILE_APP", "true").lower() == "true"
    COMMUNITY = os.getenv("FEATURE_COMMUNITY", "true").lower() == "true"
    AI_SIGNALS = os.getenv("FEATURE_AI_SIGNALS", "false").lower() == "true"
    REGULATORY = os.getenv("FEATURE_REGULATORY", "false").lower() == "true"
    NOTIFICATIONS = os.getenv("FEATURE_NOTIFICATIONS", "true").lower() == "true"
    SENTIMENT_ANALYSIS = os.getenv("FEATURE_SENTIMENT_ANALYSIS", "true").lower() == "true"
    STRATEGY_MARKETPLACE = os.getenv("FEATURE_STRATEGY_MARKETPLACE", "true").lower() == "true"
    DATA_VALIDATION = os.getenv("FEATURE_DATA_VALIDATION", "true").lower() == "true"


# ============================================================================
# LLM INTEGRATION (Advanced Signal Generation)
# ============================================================================

class LLMConfig:
    """LLM configuration for AI signal generation."""

    PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, google
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_GENKIT_API_KEY = os.getenv("GOOGLE_GENKIT_API_KEY")
    MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo")
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.7))
    MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 2000))
    ENABLED = FeatureFlags.AI_SIGNALS


# ============================================================================
# LIVE TRADING (Exchange Integration)
# ============================================================================

class ExchangeConfig:
    """Exchange API configuration."""

    LIVE_TRADING_ENABLED = os.getenv("LIVE_TRADING_ENABLED", "false").lower() == "true"
    AUTO_EXECUTION = os.getenv("LIVE_TRADING_AUTO_EXECUTION", "false").lower() == "true"
    MAX_POSITION_SIZE = float(os.getenv("LIVE_TRADING_MAX_POSITION_SIZE", 1000))
    LOG_LEVEL = os.getenv("LIVE_TRADING_LOG_LEVEL", "info")

    # Binance
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_SECRET = os.getenv("BINANCE_SECRET_KEY")
    BINANCE_TESTNET = os.getenv("BINANCE_TESTNET_ENABLED", "true").lower() == "true"

    # Bybit
    BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
    BYBIT_SECRET = os.getenv("BYBIT_SECRET_KEY")
    BYBIT_TESTNET = os.getenv("BYBIT_TESTNET_ENABLED", "true").lower() == "true"

    # OKX
    OKX_API_KEY = os.getenv("OKX_API_KEY")
    OKX_SECRET = os.getenv("OKX_SECRET_KEY")
    OKX_PASSPHRASE = os.getenv("OKX_PASSPHRASE")
    OKX_TESTNET = os.getenv("OKX_TESTNET_ENABLED", "true").lower() == "true"

    # Kraken
    KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY")
    KRAKEN_PRIVATE_KEY = os.getenv("KRAKEN_PRIVATE_KEY")
    KRAKEN_TESTNET = os.getenv("KRAKEN_TESTNET_ENABLED", "true").lower() == "true"

    # MEXC
    MEXC_API_KEY = os.getenv("MEXC_API_KEY")
    MEXC_SECRET = os.getenv("MEXC_SECRET_KEY")
    MEXC_TESTNET = os.getenv("MEXC_TESTNET_ENABLED", "true").lower() == "true"

    # Gate.io
    GATEIO_API_KEY = os.getenv("GATEIO_API_KEY")
    GATEIO_SECRET = os.getenv("GATEIO_SECRET_KEY")
    GATEIO_PASSPHRASE = os.getenv("GATEIO_PASSPHRASE")
    GATEIO_TESTNET = os.getenv("GATEIO_TESTNET_ENABLED", "true").lower() == "true"


# ============================================================================
# MOBILE APP
# ============================================================================

class MobileAppConfig:
    """Mobile app configuration."""

    ENABLED = os.getenv("MOBILE_APP_ENABLED", "true").lower() == "true"
    API_BASE_URL = os.getenv("MOBILE_APP_API_BASE_URL", "http://localhost:8000")
    WS_URL = os.getenv("MOBILE_APP_WS_URL", "ws://localhost:8000/ws")
    BUILD_NUMBER = int(os.getenv("MOBILE_APP_BUILD_NUMBER", 1))
    VERSION = os.getenv("MOBILE_APP_VERSION", "1.0.0")
    APPLE_APP_ID = os.getenv("APPLE_APP_ID")
    GOOGLE_PLAY_ID = os.getenv("GOOGLE_PLAY_PACKAGE_ID")


# ============================================================================
# COMMUNITY & SOCIAL
# ============================================================================

class CommunityConfig:
    """Community features configuration."""

    ENABLED = os.getenv("COMMUNITY_ENABLED", "true").lower() == "true"
    USER_PROFILES = os.getenv("ENABLE_USER_PROFILES", "true").lower() == "true"
    STRATEGY_COMMENTS = os.getenv("ENABLE_STRATEGY_COMMENTS", "true").lower() == "true"
    SIGNAL_RATINGS = os.getenv("ENABLE_SIGNAL_RATINGS", "true").lower() == "true"
    LEADERBOARDS = os.getenv("ENABLE_LEADERBOARDS", "true").lower() == "true"
    ACHIEVEMENTS = os.getenv("ENABLE_ACHIEVEMENTS", "true").lower() == "true"
    NOTIFICATIONS = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"
    REAL_TIME_CHAT = os.getenv("ENABLE_REAL_TIME_CHAT", "true").lower() == "true"

    # Notification Services
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")


# ============================================================================
# ADVANCED SIGNAL FEATURES
# ============================================================================

class AdvancedSignalsConfig:
    """Advanced signal generation configuration."""

    MULTI_TIMEFRAME = os.getenv("ENABLE_MULTI_TIMEFRAME_SIGNALS", "true").lower() == "true"
    CORRELATION_BASED = os.getenv("ENABLE_CORRELATION_BASED_SIGNALS", "true").lower() == "true"
    SENTIMENT_ANALYSIS = os.getenv("ENABLE_SENTIMENT_ANALYSIS", "true").lower() == "true"
    NEWS_DRIVEN = os.getenv("ENABLE_NEWS_DRIVEN_SIGNALS", "true").lower() == "true"
    ML_RETRAINING = os.getenv("ENABLE_ML_SIGNAL_RETRAINING", "true").lower() == "true"
    ML_RETRAINING_INTERVAL = int(os.getenv("ML_RETRAINING_INTERVAL", 86400))  # seconds


# ============================================================================
# REGULATORY & COMPLIANCE
# ============================================================================

class ComplianceConfig:
    """Regulatory and compliance configuration."""

    ENABLED = os.getenv("REGULATORY_ENABLED", "false").lower() == "true"
    COMPLIANCE_CHECKS = os.getenv("ENABLE_COMPLIANCE_CHECKS", "true").lower() == "true"
    AUDIT_LOGGING = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    BLOCKCHAIN_PROOFS = os.getenv("ENABLE_BLOCKCHAIN_PROOFS", "true").lower() == "true"
    JURISDICTION = os.getenv("COMPLIANCE_JURISDICTION", "global")  # us, eu, global

    # KYC
    KYC_PROVIDER = os.getenv("KYC_PROVIDER", "stripe-verify")
    KYC_API_KEY = os.getenv("KYC_PROVIDER_API_KEY")

    # AML
    AML_ENABLED = os.getenv("AML_CHECK_ENABLED", "true").lower() == "true"
    SANCTIONS_LIST_API = os.getenv("SANCTIONS_LIST_API")

    # Disclaimers
    DISCLAIMER_VERSION = os.getenv("DISCLAIMER_VERSION", "1.0")
    REQUIRES_FINANCIAL_LICENSE = os.getenv("REQUIRES_FINANCIAL_ADVISOR_LICENSE", "false").lower() == "true"
    ACCEPT_DISCLAIMER = os.getenv("DISCLAIMER_ACCEPT_REQUIRED", "true").lower() == "true"


# ============================================================================
# MARKETPLACE & PAYMENTS
# ============================================================================

class MarketplaceConfig:
    """Marketplace payment configuration."""

    ENABLED = os.getenv("ENABLE_MARKETPLACE_PAYMENTS", "true").lower() == "true"
    STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    COMMISSION_PCT = int(os.getenv("MARKETPLACE_COMMISSION_PCT", 30))
    MIN_PAYOUT = float(os.getenv("MARKETPLACE_MIN_PAYOUT", 100))


# ============================================================================
# ANALYTICS & MONITORING
# ============================================================================

class AnalyticsConfig:
    """Analytics and monitoring configuration."""

    SENTRY_DSN = os.getenv("SENTRY_DSN")
    POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY")
    POSTHOG_PROJECT_ID = os.getenv("POSTHOG_PROJECT_ID")
    PERFORMANCE_MONITORING = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
    ERROR_TRACKING = os.getenv("ENABLE_ERROR_TRACKING", "true").lower() == "true"


# ============================================================================
# DEVELOPMENT & TESTING
# ============================================================================

class DevelopmentConfig:
    """Development and testing configuration."""

    MOCK_EXCHANGE = os.getenv("MOCK_EXCHANGE_RESPONSES", "true").lower() == "true"
    MOCK_LLM = os.getenv("MOCK_LLM_RESPONSES", "false").lower() == "true"
    DEBUG_ENDPOINTS = os.getenv("ENABLE_DEBUG_ENDPOINTS", "true").lower() == "true"
    DEBUG_USER_ID = os.getenv("DEBUG_USER_ID", "debug-user-123")


# ============================================================================
# NOTIFICATION SERVICE (§15)
# ============================================================================

class NotificationServiceConfig:
    """Notification service configuration."""

    WEB_PUSH_ENABLED = os.getenv("WEB_PUSH_ENABLED", "true").lower() == "true"
    TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "true").lower() == "true"
    DISCORD_ENABLED = os.getenv("DISCORD_ENABLED", "true").lower() == "true"
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() == "true"


# ============================================================================
# DATA VALIDATION (§7.2)
# ============================================================================

class DataValidationConfig:
    """Data validation pipeline configuration."""

    DEDUP_WINDOW_SECONDS = int(os.getenv("DEDUP_WINDOW_SECONDS", "60"))
    OUTLIER_STD_THRESHOLD = float(os.getenv("OUTLIER_STD_THRESHOLD", "5.0"))
    ROLLING_PERIOD = int(os.getenv("ROLLING_PERIOD", "100"))
    CLOCK_SKEW_MS = float(os.getenv("CLOCK_SKEW_MS", "500.0"))
    CROSS_VENUE_DIVERGENCE_PCT = float(os.getenv("CROSS_VENUE_DIVERGENCE_PCT", "0.5"))


# ============================================================================
# AUDIT LOG SERVICE (§28)
# ============================================================================

class AuditLogConfig:
    """Audit log service configuration."""

    RETENTION_MONTHS = int(os.getenv("AUDIT_RETENTION_MONTHS", "24"))
    DAILY_VERIFICATION = os.getenv("AUDIT_DAILY_VERIFICATION", "true").lower() == "true"


# ============================================================================
# STRATEGY MARKETPLACE (§26.2)
# ============================================================================

class StrategyMarketplaceConfig:
    """Strategy marketplace configuration."""

    VERIFICATION_TOLERANCE = float(os.getenv("MARKETPLACE_VERIFICATION_TOLERANCE", "0.05"))
    PAPER_TRADING_WEEKS = int(os.getenv("MARKETPLACE_PAPER_TRADING_WEEKS", "4"))
    COMMISSION_PCT = int(os.getenv("MARKETPLACE_COMMISSION_PCT", "30"))


# ============================================================================
# ALPHAACADEMY (Education Layer)
# ============================================================================

class EducationConfig:
    """Education layer configuration."""

    ENABLED = os.getenv("ALPHAACADEMY_ENABLED", "true").lower() == "true"

    # Content categories
    CATEGORIES = ["patterns", "strategies", "risk_mgmt", "quant_basics"]

    # Difficulty levels
    DIFFICULTIES = ["beginner", "intermediate", "advanced"]

    # Limits
    MAX_CONTENT_PER_PAGE = int(os.getenv("EDUCATION_MAX_CONTENT_PER_PAGE", 50))
    QUIZ_PASSING_SCORE = float(os.getenv("EDUCATION_QUIZ_PASSING_SCORE", 0.7))

    # LLM integration for signal breakdowns
    LLM_BREAKDOWNS_ENABLED = os.getenv("EDUCATION_LLM_BREAKDOWNS", "true").lower() == "true"
    BREAKDOWN_MAX_TOKENS = int(os.getenv("EDUCATION_BREAKDOWN_MAX_TOKENS", 1000))


# ============================================================================
# AUTOMATION (Grid Bot + DCA Bot)
# ============================================================================

class AutomationConfig:
    """Automation engine configuration."""

    ENABLED = os.getenv("AUTOMATION_ENABLED", "true").lower() == "true"

    # Grid Bot limits
    MAX_GRID_LEVELS = int(os.getenv("AUTOMATION_MAX_GRID_LEVELS", 50))
    MAX_TOTAL_INVESTMENT = float(os.getenv("AUTOMATION_MAX_TOTAL_INVESTMENT", 100000))

    # DCA Bot limits
    MAX_DCA_SINGLE_INVESTMENT = float(os.getenv("AUTOMATION_MAX_DCA_INVESTMENT", 10000))

    # Scheduling
    TICK_INTERVAL_SECONDS = int(os.getenv("AUTOMATION_TICK_INTERVAL", 60))


# ============================================================================
# STRATEGY BUILDER (No-Code Strategy Configurator)
# ============================================================================

class StrategyBuilderConfig:
    """No-code strategy builder configuration."""

    # Limits
    MAX_STRATEGIES_PER_USER = int(os.getenv("STRATEGY_BUILDER_MAX_PER_USER", 20))
    MAX_SIGNAL_FILTERS = int(os.getenv("STRATEGY_BUILDER_MAX_SIGNAL_FILTERS", 10))

    # Confidence bounds
    MIN_CONFIDENCE = 0.0
    MAX_CONFIDENCE = 1.0

    # Position sizing
    MIN_BASE_ALLOCATION = 0.001
    MAX_BASE_ALLOCATION = 0.10
    MAX_MAX_PER_POSITION = 10000

    # Risk controls
    MAX_MAX_LOSS_PER_TRADE = 10000
    MAX_MAX_DAILY_LOSS = 50000
    MAX_MAX_OPEN_POSITIONS = 20

    # Simulation
    SIMULATION_LIMIT_DAYS = 365
    SIMULATION_MAX_SIGNALS = 1000


# ============================================================================
# PHASE 3: TOURNAMENTS
# ============================================================================

class TournamentConfig:
    """Trading tournament configuration."""

    ENABLED = os.getenv("FEATURE_TOURNAMENTS", "true").lower() == "true"
    DEFAULT_DURATION_DAYS = int(os.getenv("TOURNAMENT_DURATION_DAYS", 30))
    MAX_ENTRIES_PER_TOURNAMENT = int(os.getenv("TOURNAMENT_MAX_ENTRIES", 1000))
    MIN_ENTRIES_TO_START = int(os.getenv("TOURNAMENT_MIN_ENTRIES", 10))
    SORT_METRICS = ["final_pnl", "final_sharpe", "final_win_rate"]
    LEADERBOARD_REFRESH_SECONDS = int(os.getenv("TOURNAMENT_LEADERBOARD_REFRESH", 60))


class CommunityConfig:
    """Community and social features configuration."""

    ENABLED = os.getenv("FEATURE_COMMUNITY", "true").lower() == "true"
    MAX_BIO_LENGTH = int(os.getenv("COMMUNITY_MAX_BIO_LENGTH", 500))
    MAX_COMMENT_LENGTH = int(os.getenv("COMMUNITY_MAX_COMMENT_LENGTH", 2000))
    LEADERBOARD_CACHE_SECONDS = int(os.getenv("COMMUNITY_LEADERBOARD_CACHE", 300))


# ============================================================================
# PHASE 3: STRATEGY PERSONALITY
# ============================================================================

class StrategyPersonalityConfig:
    """Strategy personality classification configuration."""

    ENABLED = os.getenv("FEATURE_STRATEGY_PERSONALITY", "true").lower() == "true"
    MIN_TRADES_FOR_CLASSIFICATION = int(os.getenv("PERSONALITY_MIN_TRADES", 5))
    RECLASSIFY_AFTER_TRADES = int(os.getenv("PERSONALITY_RECLASSIFY_TRADES", 50))


# ============================================================================
# PHASE 3: TRAILING ORDERS
# ============================================================================

class TrailingOrderConfig:
    """Trailing stop / trailing take-profit configuration."""

    ENABLED = os.getenv("FEATURE_TRAILING_ORDERS", "true").lower() == "true"
    MIN_TRAIL_PERCENT = float(os.getenv("TRAILING_ORDER_MIN_TRAIL_PCT", 0.1))
    MAX_TRAIL_PERCENT = float(os.getenv("TRAILING_ORDER_MAX_TRAIL_PCT", 50.0))
    MAX_ACTIVE_ORDERS_PER_USER = int(os.getenv("TRAILING_ORDER_MAX_PER_USER", 20))
    EVALUATION_INTERVAL_SECONDS = int(os.getenv("TRAILING_ORDER_EVAL_INTERVAL", 5))


# ============================================================================
# PHASE 3: ONCHAIN TRACKER
# ============================================================================

class OnchainConfig:
    """On-chain smart money tracker configuration."""

    ENABLED = os.getenv("FEATURE_ONCHAIN_TRACKER", "true").lower() == "true"
    USE_MOCK_DATA = os.getenv("ONCHAIN_USE_MOCK", "true").lower() == "true"
    WHALE_MOVEMENT_LIMIT = int(os.getenv("ONCHAIN_WHALE_LIMIT", 50))
    METRICS_REFRESH_SECONDS = int(os.getenv("ONCHAIN_METRICS_REFRESH", 300))
    SUPPORTED_ASSETS = os.getenv("ONCHAIN_SUPPORTED_ASSETS", "BTC,ETH,SOL,BNB,XRP").split(",")
    EXCHANGE_FLOWS_LOOKBACK_HOURS = int(os.getenv("ONCHAIN_FLOWS_LOOKBACK_HOURS", 24))
