"""
Strategy Management Service
CRUD operations for trading strategy configuration and management
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class StrategyStatus(str, Enum):
    """Strategy lifecycle status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    BACKTEST_REQUIRED = "backtest_required"


class StrategyType(str, Enum):
    """Types of trading strategies"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    GRID_TRADING = "grid_trading"
    DCA = "dollar_cost_averaging"
    MACHINE_LEARNING = "machine_learning"
    CUSTOM = "custom"


@dataclass
class StrategyParameter:
    """Strategy configuration parameter"""
    name: str
    value: Any
    param_type: str  # "float", "int", "string", "list"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""


@dataclass
class StrategyBacktestResult:
    """Backtest performance metrics"""
    strategy_id: str
    backtest_date: str
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    profit_factor: float
    trades_executed: int
    passed: bool = True


@dataclass
class TradingStrategy:
    """Complete trading strategy definition"""
    id: str
    name: str
    description: str
    strategy_type: StrategyType
    status: StrategyStatus
    parameters: List[StrategyParameter] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)
    risk_limit_pct: float = 2.0
    max_position_size: float = 5.0
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    backtest_results: List[StrategyBacktestResult] = field(default_factory=list)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["strategy_type"] = self.strategy_type.value
        data["status"] = self.status.value
        return data


class StrategyManagementService:
    """Manage trading strategies with full CRUD operations"""
    
    def __init__(self):
        self.strategies: Dict[str, TradingStrategy] = {}
        self.strategy_history: List[Dict[str, Any]] = []
    
    async def create_strategy(
        self,
        name: str,
        description: str,
        strategy_type: StrategyType,
        assets: List[str],
        parameters: List[Dict[str, Any]],
        user_id: str
    ) -> TradingStrategy:
        """Create new trading strategy"""
        strategy_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        params = [
            StrategyParameter(
                name=p.get("name"),
                value=p.get("value"),
                param_type=p.get("param_type", "float"),
                min_value=p.get("min_value"),
                max_value=p.get("max_value"),
                description=p.get("description", "")
            )
            for p in parameters
        ]
        
        strategy = TradingStrategy(
            id=strategy_id,
            name=name,
            description=description,
            strategy_type=strategy_type,
            status=StrategyStatus.DRAFT,
            parameters=params,
            assets=assets,
            created_at=now,
            updated_at=now,
            created_by=user_id
        )
        
        self.strategies[strategy_id] = strategy
        
        self._record_history("create", strategy_id, user_id, f"Created strategy: {name}")
        logger.info(f"✅ Strategy created: {strategy_id} ({name})")
        
        return strategy
    
    async def get_strategy(self, strategy_id: str) -> Optional[TradingStrategy]:
        """Retrieve strategy by ID"""
        return self.strategies.get(strategy_id)
    
    async def list_strategies(
        self,
        status: Optional[StrategyStatus] = None,
        strategy_type: Optional[StrategyType] = None,
        user_id: Optional[str] = None
    ) -> List[TradingStrategy]:
        """List strategies with optional filters"""
        results = list(self.strategies.values())
        
        if status:
            results = [s for s in results if s.status == status]
        
        if strategy_type:
            results = [s for s in results if s.strategy_type == strategy_type]
        
        return results
    
    async def update_strategy(
        self,
        strategy_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Optional[TradingStrategy]:
        """Update strategy configuration"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        
        # Update allowed fields
        allowed_fields = {"name", "description", "parameters", "assets", "risk_limit_pct", "max_position_size"}
        
        for field_name, value in updates.items():
            if field_name not in allowed_fields:
                continue
            
            if field_name == "parameters":
                strategy.parameters = [
                    StrategyParameter(
                        name=p.get("name"),
                        value=p.get("value"),
                        param_type=p.get("param_type", "float")
                    )
                    for p in value
                ]
            else:
                setattr(strategy, field_name, value)
        
        strategy.updated_at = datetime.utcnow().isoformat()
        
        self._record_history("update", strategy_id, user_id, f"Updated strategy: {strategy.name}")
        logger.info(f"✅ Strategy updated: {strategy_id}")
        
        return strategy
    
    async def activate_strategy(
        self,
        strategy_id: str,
        user_id: str
    ) -> Optional[TradingStrategy]:
        """Activate strategy for trading"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        
        if strategy.status == StrategyStatus.BACKTEST_REQUIRED:
            return None  # Must pass backtest first
        
        strategy.status = StrategyStatus.ACTIVE
        strategy.updated_at = datetime.utcnow().isoformat()
        
        self._record_history("activate", strategy_id, user_id, f"Activated strategy: {strategy.name}")
        logger.info(f"🚀 Strategy activated: {strategy_id}")
        
        return strategy
    
    async def pause_strategy(
        self,
        strategy_id: str,
        user_id: str
    ) -> Optional[TradingStrategy]:
        """Pause strategy execution"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        
        strategy.status = StrategyStatus.PAUSED
        strategy.updated_at = datetime.utcnow().isoformat()
        
        self._record_history("pause", strategy_id, user_id, f"Paused strategy: {strategy.name}")
        logger.info(f"⏸️ Strategy paused: {strategy_id}")
        
        return strategy
    
    async def delete_strategy(
        self,
        strategy_id: str,
        user_id: str
    ) -> bool:
        """Archive strategy (soft delete)"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return False
        
        strategy.status = StrategyStatus.ARCHIVED
        strategy.enabled = False
        strategy.updated_at = datetime.utcnow().isoformat()
        
        self._record_history("archive", strategy_id, user_id, f"Archived strategy: {strategy.name}")
        logger.info(f"🗑️ Strategy archived: {strategy_id}")
        
        return True
    
    async def add_backtest_result(
        self,
        strategy_id: str,
        result: Dict[str, Any],
        user_id: str
    ) -> Optional[TradingStrategy]:
        """Record backtest results for strategy"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return None
        
        backtest = StrategyBacktestResult(
            strategy_id=strategy_id,
            backtest_date=datetime.utcnow().isoformat(),
            win_rate=result.get("win_rate", 0.5),
            sharpe_ratio=result.get("sharpe_ratio", 1.0),
            max_drawdown=result.get("max_drawdown", -0.05),
            total_return=result.get("total_return", 0.1),
            profit_factor=result.get("profit_factor", 1.5),
            trades_executed=result.get("trades", 0),
            passed=result.get("win_rate", 0) > 0.45
        )
        
        strategy.backtest_results.append(backtest)
        
        # Auto-require backtest if quality drops
        if len(strategy.backtest_results) > 1:
            latest = strategy.backtest_results[-1]
            if latest.win_rate < 0.45 or latest.sharpe_ratio < 0.8:
                strategy.status = StrategyStatus.BACKTEST_REQUIRED
        
        self._record_history("backtest", strategy_id, user_id, f"Backtest result: {backtest.passed}")
        
        return strategy
    
    async def validate_parameters(
        self,
        strategy_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate strategy parameters within bounds"""
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            return {"valid": False, "errors": ["Strategy not found"]}
        
        errors = []
        
        for param in strategy.parameters:
            if param.name not in parameters:
                errors.append(f"Missing parameter: {param.name}")
                continue
            
            value = parameters[param.name]
            
            if param.min_value is not None and value < param.min_value:
                errors.append(f"{param.name} below minimum {param.min_value}")
            
            if param.max_value is not None and value > param.max_value:
                errors.append(f"{param.name} exceeds maximum {param.max_value}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _record_history(
        self,
        action: str,
        strategy_id: str,
        user_id: str,
        details: str
    ):
        """Record strategy management action"""
        self.strategy_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "strategy_id": strategy_id,
            "user_id": user_id,
            "details": details
        })
    
    async def get_management_stats(self) -> Dict[str, Any]:
        """Get strategy management statistics"""
        total = len(self.strategies)
        active = sum(1 for s in self.strategies.values() if s.status == StrategyStatus.ACTIVE)
        paused = sum(1 for s in self.strategies.values() if s.status == StrategyStatus.PAUSED)
        
        return {
            "total_strategies": total,
            "active": active,
            "paused": paused,
            "draft": total - active - paused,
            "total_backtests": sum(len(s.backtest_results) for s in self.strategies.values()),
            "recent_actions": self.strategy_history[-10:]
        }
