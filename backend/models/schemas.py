"""
Pydantic models for AlphaForge backend.
Defines all data structures for API requests/responses and database operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# ENUMS
# ============================================================================

class PlanType(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    
    @classmethod
    def _missing_(cls, value):
        """Allow case-insensitive enum lookup."""
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    
    @classmethod
    def _missing_(cls, value):
        """Allow case-insensitive enum lookup."""
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradeDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PENDING = "PENDING"
    LIQUIDATED = "LIQUIDATED"
    CANCELLED = "CANCELLED"


class KYCStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class VerificationStage(str, Enum):
    STAGE_1_INTRO = "stage_1_intro"
    STAGE_2_PAPER_TRADING = "stage_2_paper_trading"
    STAGE_3_PERFORMANCE_CHECK = "stage_3_performance_check"
    STAGE_4_KYC = "stage_4_kyc"
    STAGE_5_APPROVED = "stage_5_approved"


# ============================================================================
# USER & PROFILE
# ============================================================================

class UserProfileBase(BaseModel):
    email: str  # Accept any email format including test domains
    display_name: str
    institution_name: Optional[str] = None
    plan: PlanType = PlanType.FREE
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    onboarding_complete: bool = False
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format (lenient for test environments)."""
        if not v or not isinstance(v, str):
            raise ValueError('email must be a non-empty string')
        # Accept emails with @ and a domain
        if '@' not in v:
            raise ValueError('email must contain @')
        return v.lower().strip()


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    institution_name: Optional[str] = None
    plan: Optional[PlanType] = None
    risk_tolerance: Optional[RiskTolerance] = None


class UserProfile(UserProfileBase):
    id: str
    kyc_status: KYCStatus = KYCStatus.NOT_STARTED
    verification_stage: VerificationStage = VerificationStage.STAGE_1_INTRO
    created_at: datetime
    updated_at: datetime
    

    class Config:
        from_attributes = True


# ============================================================================
# MARKET DATA
# ============================================================================

class MarketTicker(BaseModel):
    symbol: str
    name: Optional[str] = None
    last_price: float
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    change_24h: float
    change_24h_pct: float
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    timestamp: datetime


class MarketTickerResponse(BaseModel):
    success: bool
    tickers: List[MarketTicker]
    timestamp: datetime


class MarketSentiment(BaseModel):
    bullish_count: int
    neutral_count: int
    bearish_count: int
    bullish_pct: float
    neutral_pct: float
    bearish_pct: float
    composite_score: float  # -100 to +100
    market_status: str  # "BULLISH", "NEUTRAL", "BEARISH"
    timestamp: datetime


class FundingRate(BaseModel):
    asset: str
    funding_rate: float
    predicted_rate: Optional[float] = None
    interval: str  # "8h", "1h", etc
    next_funding_time: Optional[datetime] = None
    timestamp: datetime


class FundingRatesResponse(BaseModel):
    success: bool
    funding_rates: List[FundingRate]
    timestamp: datetime


class OpenInterest(BaseModel):
    asset: str
    open_interest_usd: float
    open_interest_contracts: Optional[float] = None
    change_24h: float
    change_24h_pct: float
    timestamp: datetime


class OpenInterestResponse(BaseModel):
    success: bool
    open_interest: List[OpenInterest]
    timestamp: datetime


class DataQualityStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


class DataQuality(BaseModel):
    asset: str
    status: DataQualityStatus
    last_update: datetime
    data_points_24h: int
    uptime_pct: float
    latency_ms: float


class DataQualityResponse(BaseModel):
    success: bool
    data_quality: List[DataQuality]
    timestamp: datetime


# ============================================================================
# SIGNALS
# ============================================================================

class SignalBase(BaseModel):
    ticker: str
    signal_type: SignalType
    confidence: float = Field(..., ge=0.0, le=1.0)
    entry_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    rationale: str
    drivers: List[str] = []


class SignalCreate(SignalBase):
    created_by: str  # Signal creator ID


class Signal(SignalBase):
    id: str
    created_by: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    performance_data: Dict[str, Any] = {}
    

    class Config:
        from_attributes = True


# ============================================================================
# PAPER TRADING
# ============================================================================

class PaperTradeBase(BaseModel):
    user_id: str
    signal_id: str
    asset: str
    direction: TradeDirection
    entry_price: float
    quantity: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class PaperTradeCreate(PaperTradeBase):
    pass


class PaperTrade(PaperTradeBase):
    id: str
    exit_price: Optional[float] = None
    status: TradeStatus = TradeStatus.OPEN
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    

    class Config:
        from_attributes = True


# ============================================================================
# PORTFOLIO
# ============================================================================

class PortfolioMetrics(BaseModel):
    total_equity: float
    available_balance: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    pnl_percent: float
    total_trades: int
    open_positions: int
    closed_positions: int
    win_rate: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    profit_factor: Optional[float] = None


class PortfolioSummary(BaseModel):
    id: str
    user_id: str
    starting_balance: float
    current_balance: float
    total_pnl: float
    total_pnl_percent: float
    total_trades: int
    win_count: int
    loss_count: int
    open_positions: int
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    

    class Config:
        from_attributes = True


# ============================================================================
# POSITIONS
# ============================================================================

class PositionBase(BaseModel):
    user_id: str
    ticker: str
    direction: TradeDirection
    entry_price: float
    quantity: float


class Position(PositionBase):
    id: str
    signal_id: Optional[str] = None
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    risk_exposure_pct: float
    opened_at: datetime
    

    class Config:
        from_attributes = True


# ============================================================================
# CREATOR & VERIFICATION
# ============================================================================

class CreatorProfile(BaseModel):
    id: str
    user_id: str
    verification_stage: VerificationStage
    total_signals_created: int
    win_rate: float
    avg_confidence: float
    total_followers: int
    verified_at: Optional[datetime] = None
    

    class Config:
        from_attributes = True


class CreatorVerificationStep(BaseModel):
    creator_id: str
    stage: VerificationStage
    documents: List[str] = []
    verified: bool = False
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None


# ============================================================================
# KYC/AML
# ============================================================================

class KYCVerification(BaseModel):
    user_id: str
    status: KYCStatus
    onfido_applicant_id: Optional[str] = None
    onfido_check_id: Optional[str] = None
    aml_status: Optional[str] = None
    aml_reason: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    

    class Config:
        from_attributes = True


# ============================================================================
# RISK SCORING
# ============================================================================

class RiskScoreRequest(BaseModel):
    position_size_pct: float
    leverage: float
    volatility_index: float
    sharpe_ratio: Optional[float] = None
    correlation_risk: float = 0.0


class RiskScoreResponse(BaseModel):
    risk_score: float
    is_approved: bool
    warnings: List[str] = []
    recommendation: str


# ============================================================================
# API RESPONSES
# ============================================================================

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None


class PaginatedResponse(BaseModel):
    data: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================================================
# AUDIT LOG
# ============================================================================

class AuditLogEntry(BaseModel):
    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    changes: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    

    class Config:
        from_attributes = True


# ============================================================================
# EXTERNAL SIGNAL INGESTION (TradingView, etc)
# ============================================================================

class ExternalSignalWebhook(BaseModel):
    timestamp: datetime
    ticker: str
    action: SignalType
    price: float
    source: str  # "tradingview", "alpha_vantage", etc
    metadata: Dict[str, Any] = {}


# ============================================================================
# CHAT MESSAGES
# ============================================================================

class ChatMessage(BaseModel):
    id: str
    user_id: str
    message: str
    role: str  # "user" or "assistant"
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    success: bool
    user_message: str
    ai_response: str
    timestamp: datetime


# ============================================================================
# STRATEGY & CREATOR
# ============================================================================

class StrategyBase(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    backtest_results: Dict[str, Any] = {}


class Strategy(StrategyBase):
    id: str
    user_id: str
    status: str  # PENDING_REVIEW, APPROVED, REJECTED
    created_at: datetime
    
    class Config:
        from_attributes = True


class StrategySubscription(BaseModel):
    id: str
    user_id: str
    strategy_id: str
    allocation_pct: float
    status: str
    subscribed_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# BACKTESTING
# ============================================================================

class BacktestRequest(BaseModel):
    name: str
    symbols: List[str]
    initial_capital: float = 100000
    parameters: Dict[str, Any] = {}
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class BacktestResult(BaseModel):
    id: str
    user_id: str
    strategy_name: str
    status: str  # RUNNING, COMPLETED, FAILED
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EquityCurvePoint(BaseModel):
    day: int
    equity: float
    date: str


# ============================================================================
# MARKET INSIGHTS
# ============================================================================

class MarketInsight(BaseModel):
    query: str
    insight: str
    confidence: float
    data_sources: List[str]
    generated_at: datetime


class MarketInsightResponse(BaseModel):
    success: bool
    insight: MarketInsight


# ============================================================================
# CREATOR VERIFICATION
# ============================================================================

class VerificationStageInfo(BaseModel):
    stage: int
    name: str
    status: str  # completed, current, pending
    stage_key: str
    description: str


class VerificationPipeline(BaseModel):
    current_stage: str
    pipeline: List[VerificationStageInfo]
    kyc_status: str
    reputation_score: float


# ============================================================================
# SIGNALS & PROOFS
# ============================================================================

class SignalProof(BaseModel):
    signal_id: str
    ticker: str
    signal_type: str
    confidence: float
    created_at: datetime
    merkle_root: str
    blockchain_anchor: Dict[str, Any]
    rationale: str
    performance: Dict[str, Any] = {}


class SignalProofResponse(BaseModel):
    success: bool
    proof: SignalProof


# ============================================================================
# RISK & SETTINGS
# ============================================================================

class RiskSettings(BaseModel):
    user_id: str
    max_position_size_pct: float = 2.0
    max_portfolio_exposure_pct: float = 20.0
    max_leverage: float = 5.0
    stop_loss_default: float = 2.0
    take_profit_default: float = 5.0
    daily_loss_limit_pct: float = 10.0


class ExchangeConnection(BaseModel):
    exchange: str
    status: str
    connected_at: datetime
    
    class Config:
        from_attributes = True

