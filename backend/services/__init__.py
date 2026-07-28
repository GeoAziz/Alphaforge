"""AlphaForge Backend - Services module"""

# Core Services
from .user_service import UserManagementService as UserService
from .portfolio import PortfolioService
from .paper_trading import PaperTradingEngine
from .signal_aggregator import SignalAggregator
from .risk_manager import RiskManager
from .backtest_service import BacktestingService as BacktestService
from .strategy_service import StrategyService
from .creator_service import CreatorVerificationService as CreatorService
from .chat_service import ChatService
from .kyc_service import KYCService

# Gap Feature Services
from .llm_signal_generator import LLMSignalGenerator
from .live_trading_engine import LiveTradingEngine
from .community_service import CommunityService
from .compliance_service import ComplianceService
from .mobile_app_service import MobileAppService
from .advanced_signals_service import AdvancedSignalsService

# Architecture Doc Gap Services (Existing)
from .execution_service import (
    IdempotencyKeyManager,
    OrderConfirmationMonitor,
    ExchangeAbstractionLayer,
    get_idempotency_manager,
    get_order_monitor,
    get_exchange_layer,
)
from .data_validation_service import DataValidationPipeline, BackupMarketDataProvider
from .notification_service import NotificationService
from .sentiment_analysis_service import SentimentAnalysisService
from .strategy_marketplace_service import StrategyMarketplaceService
from .audit_log_service import AuditLogService

# Architecture Doc Gap Services (Moat Features)
from .ensemble_predictor import EnsemblePredictor
from .overfitting_prevention import OverfittingPreventionService
from .backtesting_integrity import BacktestingIntegrityService
from .explainability_proofs import ExplainabilityProofsService
from .production_monitor import ProductionMonitorService

# Complete Implementations (NEW - Full enforcement)
try:
    from .execution_service_complete import ExecutionService as ExecutionServiceComplete
    from .paper_trading_complete import PaperTradingEngine as PaperTradingEngineComplete
    from .kyc_service_complete import KYCService as KYCServiceComplete
    from .audit_log_service_complete import AuditLogService as AuditLogServiceComplete
    from .creator_marketplace_complete import CreatorMarketplaceService as CreatorMarketplaceServiceComplete
    from .ml_signal_engine_complete import FeatureEngineer, EnsembleSignalPredictor, SignalGenerator
    from .compliance_billing_complete import ComplianceService as ComplianceServiceComplete, BillingService
    from .enforcement_gates import EnforcementGate, LiveTradingExecutionFlow
except ImportError:
    # Fallback if complete versions not yet created
    ExecutionServiceComplete = None
    PaperTradingEngineComplete = None
    KYCServiceComplete = None
    AuditLogServiceComplete = None
    CreatorMarketplaceServiceComplete = None
    FeatureEngineer = None
    EnsembleSignalPredictor = None
    SignalGenerator = None
    ComplianceServiceComplete = None
    BillingService = None
    EnforcementGate = None
    LiveTradingExecutionFlow = None

__all__ = [
    # Core
    "UserService",
    "PortfolioService",
    "PaperTradingEngine",
    "SignalAggregator",
    "RiskManager",
    "BacktestService",
    "StrategyService",
    "CreatorService",
    "ChatService",
    "KYCService",
    # Gap Features
    "LLMSignalGenerator",
    "LiveTradingEngine",
    "CommunityService",
    "ComplianceService",
    "MobileAppService",
    "AdvancedSignalsService",
    # Architecture Doc Gaps (Existing)
    "IdempotencyKeyManager",
    "OrderConfirmationMonitor",
    "ExchangeAbstractionLayer",
    "DataValidationPipeline",
    "BackupMarketDataProvider",
    "NotificationService",
    "SentimentAnalysisService",
    "StrategyMarketplaceService",
    "AuditLogService",
    "get_idempotency_manager",
    "get_order_monitor",
    "get_exchange_layer",
    # Architecture Doc Gaps (Moat Features)
    "EnsemblePredictor",
    "OverfittingPreventionService",
    "BacktestingIntegrityService",
    "ExplainabilityProofsService",
    "ProductionMonitorService",
    # Complete Implementations (NEW)
    "ExecutionServiceComplete",
    "PaperTradingEngineComplete",
    "KYCServiceComplete",
    "AuditLogServiceComplete",
    "CreatorMarketplaceServiceComplete",
    "FeatureEngineer",
    "EnsembleSignalPredictor",
    "SignalGenerator",
    "ComplianceServiceComplete",
    "BillingService",
    "EnforcementGate",
    "LiveTradingExecutionFlow",
]
