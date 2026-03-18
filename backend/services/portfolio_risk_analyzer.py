"""
Portfolio Risk Analysis Service
Comprehensive portfolio risk metrics and analysis
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PositionRisk:
    """Risk metrics for individual position"""
    asset: str
    position_size: float
    portfolio_weight: float
    volatility: float
    beta: float
    var_95: float
    cvar_95: float


@dataclass
class PortfolioRiskMetrics:
    """Comprehensive portfolio risk assessment"""
    total_value: float
    total_exposure: float
    concentration_index: float
    portfolio_var_95: float
    portfolio_cvar_95: float
    portfolio_volatility: float
    portfolio_beta: float
    max_drawdown_potential: float
    diversification_score: float
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    timestamp: str


class PositionAnalyzer:
    """Analyze individual position risk"""
    
    @staticmethod
    def calculate_position_var(
        position_size: float,
        volatility: float,
        confidence_level: float = 0.95
    ) -> float:
        """Calculate Value at Risk for position"""
        z_score = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}.get(confidence_level, 1.96)
        return position_size * volatility * z_score
    
    @staticmethod
    def calculate_position_cvar(
        position_size: float,
        volatility: float
    ) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        # Simplified: CVAR ≈ VaR * 1.25 for normal distribution
        var = PositionAnalyzer.calculate_position_var(position_size, volatility)
        return var * 1.25
    
    @staticmethod
    def get_position_risk(
        asset: str,
        position_size: float,
        portfolio_value: float,
        volatility: float,
        beta: float
    ) -> PositionRisk:
        """Generate complete position risk metrics"""
        weight = position_size / portfolio_value if portfolio_value > 0 else 0
        var_95 = PositionAnalyzer.calculate_position_var(position_size, volatility)
        cvar_95 = PositionAnalyzer.calculate_position_cvar(position_size, volatility)
        
        return PositionRisk(
            asset=asset,
            position_size=position_size,
            portfolio_weight=weight,
            volatility=volatility,
            beta=beta,
            var_95=var_95,
            cvar_95=cvar_95
        )


class PortfolioRiskAnalyzer:
    """Comprehensive portfolio risk analysis"""
    
    def __init__(self):
        self.asset_correlations: Dict[str, Dict[str, float]] = {}
        self.asset_volatilities: Dict[str, float] = {}
    
    def set_asset_volatility(self, asset: str, volatility: float):
        """Set volatility for asset"""
        self.asset_volatilities[asset] = volatility
    
    def set_correlations(self, correlations: Dict[str, Dict[str, float]]):
        """Set correlation matrix between assets"""
        self.asset_correlations = correlations
    
    async def analyze_portfolio(
        self,
        positions: Dict[str, float],  # {asset: size}
        market_data: Dict[str, Dict[str, float]]  # {asset: {volatility, beta, ...}}
    ) -> PortfolioRiskMetrics:
        """Perform comprehensive portfolio risk analysis"""
        
        # Calculate portfolio metrics
        total_value = sum(positions.values())
        position_risks = []
        
        # Individual position analysis
        for asset, size in positions.items():
            vol = market_data.get(asset, {}).get("volatility", 0.02)
            beta = market_data.get(asset, {}).get("beta", 1.0)
            
            position_risk = PositionAnalyzer.get_position_risk(
                asset=asset,
                position_size=size,
                portfolio_value=total_value,
                volatility=vol,
                beta=beta
            )
            position_risks.append(position_risk)
        
        # Portfolio-level metrics
        concentration = self._calculate_concentration_index([r.portfolio_weight for r in position_risks])
        portfolio_vol = self._calculate_portfolio_volatility(position_risks)
        portfolio_beta = self._calculate_portfolio_beta(position_risks)
        portfolio_var = self._calculate_portfolio_var(position_risks, total_value)
        portfolio_cvar = portfolio_var * 1.25
        
        diversification_score = self._calculate_diversification_score(
            [r.portfolio_weight for r in position_risks],
            len(position_risks)
        )
        
        max_drawdown_potential = self._estimate_max_drawdown(portfolio_vol)
        
        risk_level = self._determine_risk_level(concentration, portfolio_vol, portfolio_var)
        
        return PortfolioRiskMetrics(
            total_value=total_value,
            total_exposure=sum(positions.values()),
            concentration_index=concentration,
            portfolio_var_95=portfolio_var,
            portfolio_cvar_95=portfolio_cvar,
            portfolio_volatility=portfolio_vol,
            portfolio_beta=portfolio_beta,
            max_drawdown_potential=max_drawdown_potential,
            diversification_score=diversification_score,
            risk_level=risk_level,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _calculate_concentration_index(self, weights: List[float]) -> float:
        """Herfindahl-Hirschman Index for concentration"""
        return sum(w ** 2 for w in weights)
    
    def _calculate_portfolio_volatility(self, position_risks: List[PositionRisk]) -> float:
        """Estimate portfolio volatility"""
        if not position_risks:
            return 0.0
        
        # Weighted average volatility (simplified, ignores correlations)
        weighted_vol = sum(
            pr.portfolio_weight * pr.volatility
            for pr in position_risks
        )
        return weighted_vol
    
    def _calculate_portfolio_beta(self, position_risks: List[PositionRisk]) -> float:
        """Calculate portfolio beta"""
        if not position_risks:
            return 0.0
        
        return sum(
            pr.portfolio_weight * pr.beta
            for pr in position_risks
        )
    
    def _calculate_portfolio_var(
        self,
        position_risks: List[PositionRisk],
        portfolio_value: float
    ) -> float:
        """Calculate portfolio VaR"""
        if not position_risks or portfolio_value == 0:
            return 0.0
        
        return sum(pr.var_95 for pr in position_risks)
    
    def _calculate_diversification_score(
        self,
        weights: List[float],
        num_assets: int
    ) -> float:
        """Diversification score (0-1, higher is better)"""
        if num_assets <= 1:
            return 0.0
        
        max_concentration = 1.0 / num_assets
        current_concentration = sum(w ** 2 for w in weights)
        
        # Normalize: perfect diversification = 1.0
        perfect_hhi = max_concentration ** 2
        diversification = 1.0 - (current_concentration - perfect_hhi) / (1.0 - perfect_hhi)
        
        return max(0.0, min(1.0, diversification))
    
    def _estimate_max_drawdown(self, volatility: float) -> float:
        """Estimate potential max drawdown"""
        # Assume 2x volatility for worst-case drawdown
        return -volatility * 2.0
    
    def _determine_risk_level(
        self,
        concentration: float,
        volatility: float,
        var: float
    ) -> str:
        """Determine overall portfolio risk level"""
        
        # Score components (0-1)
        concentration_score = min(concentration / 0.5, 1.0)  # HHI > 0.5 = high
        volatility_score = min(volatility / 0.40, 1.0)  # Vol > 40% = high
        var_score = min(var / 100000, 1.0)  # VaR > 100k = high
        
        avg_score = (concentration_score + volatility_score + var_score) / 3
        
        if avg_score > 0.7:
            return "CRITICAL"
        elif avg_score > 0.5:
            return "HIGH"
        elif avg_score > 0.3:
            return "MEDIUM"
        else:
            return "LOW"


class RiskLimitEnforcer:
    """Enforce portfolio risk limits"""
    
    def __init__(self):
        self.position_limits: Dict[str, float] = {}
        self.portfolio_limits: Dict[str, float] = {}
    
    def set_position_limit(self, asset: str, max_allocation: float):
        """Set maximum allocation for asset"""
        self.position_limits[asset] = max_allocation
    
    def set_portfolio_limits(self, limits: Dict[str, float]):
        """Set portfolio-wide limits"""
        self.portfolio_limits = limits
    
    async def check_limits(
        self,
        position_risks: List[PositionRisk],
        portfolio_metrics: PortfolioRiskMetrics
    ) -> Dict[str, Any]:
        """Check if positions comply with limits"""
        violations = []
        warnings = []
        
        # Position limits
        for pr in position_risks:
            limit = self.position_limits.get(pr.asset)
            if limit and pr.portfolio_weight > limit:
                violations.append(f"{pr.asset} exceeds position limit {limit*100}%")
        
        # Portfolio VaR limit
        var_limit = self.portfolio_limits.get("max_var")
        if var_limit and portfolio_metrics.portfolio_var_95 > var_limit:
            violations.append(f"Portfolio VaR {portfolio_metrics.portfolio_var_95:.0f} exceeds limit {var_limit}")
        
        # Volatility limit
        vol_limit = self.portfolio_limits.get("max_volatility")
        if vol_limit and portfolio_metrics.portfolio_volatility > vol_limit:
            warnings.append(f"Portfolio volatility {portfolio_metrics.portfolio_volatility:.2%} near limit {vol_limit:.2%}")
        
        # Concentration limit
        concentration_limit = self.portfolio_limits.get("max_concentration", 0.3)
        if portfolio_metrics.concentration_index > concentration_limit:
            warnings.append(f"Portfolio concentration {portfolio_metrics.concentration_index:.3f} exceeds ideal {concentration_limit}")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "risk_level": portfolio_metrics.risk_level
        }
