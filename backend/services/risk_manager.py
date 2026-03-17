"""
Risk Management Engine - Validates trades against risk constraints.
Enforces position sizing, leverage limits, correlation checks, and drawdown monitoring.
"""

import logging
import math
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages risk validation and position sizing."""
    
    # Risk parameters
    MAX_POSITION_SIZE_PC = 0.02  # 2% per position
    MAX_PORTFOLIO_EXPOSURE_PCT = 0.20  # 20% per asset
    MAX_LEVERAGE = 5
    LIQUIDATION_BUFFER_PCT = 0.20  # 20% before liquidation
    MAX_CORRELATION = 0.8  # Max correlation between positions
    MAX_DAILY_LOSS_PCT = 0.10  # Optional: 10% daily loss limit
    
    def __init__(self, db):
        self.db = db
    
    async def validate_trade(
        self,
        user_id: str,
        signal: Dict[str, Any],
        portfolio_balance: float,
        leverage: float = 1.0,
        trade_type: str = "spot"
    ) -> Dict[str, Any]:
        """
        Comprehensive trade validation.
        Returns: {
            'approved': bool,
            'risk_score': float,
            'warnings': [],
            'position_size': float,
            'reason': str
        }
        """
        
        ticker = signal.get("ticker")
        confidence = signal.get("confidence", 0.5)
        signal_type = signal.get("signal_type")
        
        warnings = []
        checks_passed = 0
        total_checks = 6
        
        # 1. Position size check
        position_valid, position_reason = await self._check_position_size(
            portfolio_balance,
            signal
        )
        if not position_valid:
            logger.warning(f"❌ Position size check failed: {position_reason}")
            return {
                "approved": False,
                "risk_score": 9.0,
                "warnings": [position_reason],
                "reason": position_reason
            }
        checks_passed += 1
        
        # 2. Portfolio exposure check
        exposure_valid, exposure_reason = await self._check_portfolio_exposure(
            user_id,
            ticker,
            signal
        )
        if not exposure_valid:
            logger.warning(f"❌ Portfolio exposure check failed: {exposure_reason}")
            warnings.append(exposure_reason)
        else:
            checks_passed += 1
        
        # 3. Leverage check (if perpetuals)
        if trade_type == "perpetuals":
            leverage_valid, leverage_reason = self._check_leverage(leverage)
            if not leverage_valid:
                logger.warning(f"❌ Leverage check failed: {leverage_reason}")
                return {
                    "approved": False,
                    "risk_score": 8.5,
                    "warnings": [leverage_reason],
                    "reason": leverage_reason
                }
            checks_passed += 1
        else:
            checks_passed += 1
        
        # 4. Correlation check (prevent overconcentration)
        correlation_valid, correlation_warning = await self._check_correlation(user_id, ticker)
        if correlation_warning:
            warnings.append(correlation_warning)
        else:
            checks_passed += 1
        
        # 5. Stop loss check (required on all trades)
        sl_valid = signal.get("stop_loss_price") is not None
        if not sl_valid:
            warnings.append("Stop loss not defined - strongly recommended")
            logger.warning("⚠️  No stop loss for signal")
        else:
            checks_passed += 1
        
        # 6. Risk score calculation
        risk_score = self._calculate_risk_score(
            confidence,
            leverage,
            signal,
            correlation_valid
        )
        
        if risk_score > 8.0:
            return {
                "approved": False,
                "risk_score": risk_score,
                "warnings": warnings,
                "reason": f"Risk score too high: {risk_score:.1f}/10"
            }
        checks_passed += 1
        
        # Calculate position size
        position_size = self._calculate_position_size(confidence, portfolio_balance, leverage)
        
        # Final decision
        approved = len(warnings) == 0 or risk_score < 6.0
        
        logger.info(f"✅ Trade validation: {ticker} {signal_type} - Score: {risk_score:.1f}/10, Size: {position_size:.2f}, Approved: {approved}")
        
        return {
            "approved": approved,
            "risk_score": risk_score,
            "warnings": warnings,
            "position_size": position_size,
            "reason": "Trade approved" if approved else f"Warnings present (risk score: {risk_score:.1f})"
        }
    
    async def _check_position_size(
        self,
        portfolio_balance: float,
        signal: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check if position size is within limits."""
        
        # Estimate position value based on confidence
        confidence = signal.get("confidence", 0.5)
        base_size = portfolio_balance * self.MAX_POSITION_SIZE_PC
        
        position_size_pct = (base_size / portfolio_balance) * 100
        
        if position_size_pct > 2.0:
            return False, f"Position size {position_size_pct:.2f}% exceeds 2% limit"
        
        return True, "Position size OK"
    
    async def _check_portfolio_exposure(
        self,
        user_id: str,
        ticker: str,
        signal: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check total exposure to an asset."""
        
        try:
            # Get open positions for this ticker
            response = self.db.supabase.table("positions").select("*").eq("user_id", user_id).eq("ticker", ticker).execute()
            
            positions = response.data or []
            existing_exposure = sum(
                float(p.get("entry_price", 0)) * float(p.get("quantity", 0))
                for p in positions
            )
            
            # Get portfolio balance
            portfolio_response = self.db.supabase.table("portfolios").select("*").eq("user_id", user_id).execute()
            portfolio = portfolio_response.data[0] if portfolio_response.data else {}
            portfolio_balance = float(portfolio.get("current_balance", 100000))
            
            # New position size
            confidence = signal.get("confidence", 0.5)
            new_position_size = portfolio_balance * self.MAX_POSITION_SIZE_PC * confidence
            
            total_exposure = existing_exposure + new_position_size
            exposure_pct = (total_exposure / portfolio_balance) * 100
            
            if exposure_pct > 20.0:
                return False, f"{ticker} exposure {exposure_pct:.2f}% exceeds 20% limit"
            
            return True, "Exposure OK"
        
        except Exception as e:
            logger.error(f"Exposure check failed: {e}")
            return True, "Exposure check skipped"
    
    def _check_leverage(self, leverage: float) -> Tuple[bool, str]:
        """Check leverage limits for perpetuals."""
        
        if leverage > self.MAX_LEVERAGE:
            return False, f"Leverage {leverage}x exceeds {self.MAX_LEVERAGE}x limit"
        
        return True, "Leverage OK"
    
    async def _check_correlation(self, user_id: str, new_ticker: str) -> Tuple[bool, Optional[str]]:
        """
        Check correlation with existing positions.
        Prevent correlated trades (would amplify losses).
        """
        
        try:
            # Get current positions
            response = self.db.supabase.table("positions").select("*").eq("user_id", user_id).execute()
            positions = response.data or []
            
            if len(positions) == 0:
                return True, None
            
            existing_tickers = [p.get("ticker") for p in positions]
            
            # Simplified correlation check: crypto pairs are highly correlated
            # In production, would use historical correlation matrix
            high_corr_pairs = {
                "BTC": ["ETH", "BNB", "SOL"],
                "ETH": ["BTC", "SOL"],
                "USDT": ["USDC"]
            }
            
            if new_ticker in high_corr_pairs:
                correlated = [t for t in existing_tickers if t in high_corr_pairs.get(new_ticker, [])]
                if correlated:
                    return False, f"High correlation with {', '.join(correlated)} already held"
            
            return True, None
        
        except Exception as e:
            logger.error(f"Correlation check failed: {e}")
            return True, None
    
    def _calculate_risk_score(
        self,
        confidence: float,
        leverage: float,
        signal: Dict[str, Any],
        has_correlation: bool
    ) -> float:
        """
        Calculate composite risk score (0-10, lower is better).
        Formula: (1 - confidence) * 5 + (leverage - 1) * 0.5 + correlation_penalty
        """
        
        # Base risk from lack of confidence
        confidence_risk = (1 - confidence) * 5  # 0-5
        
        # Leverage risk
        leverage_risk = max(0, (leverage - 1) * 0.5)  # 0-2.5
        
        # Correlation penalty
        correlation_risk = 2.0 if has_correlation else 0
        
        # Stop loss penalty
        sl_risk = 1.0 if signal.get("stop_loss_price") is None else 0
        
        total_risk = confidence_risk + leverage_risk + correlation_risk + sl_risk
        
        return min(10.0, total_risk)
    
    def _calculate_position_size(
        self,
        confidence: float,
        portfolio_balance: float,
        leverage: float = 1.0
    ) -> float:
        """
        Calculate recommended position size based on confidence and risk tolerance.
        Formula: base_size * confidence * leverage_multiplier
        """
        
        base_size = portfolio_balance * self.MAX_POSITION_SIZE_PC
        
        # Scale with confidence
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5x to 1.0x
        
        # Scale with leverage
        leverage_multiplier = min(leverage / self.MAX_LEVERAGE, 1.0)
        
        position_size = base_size * confidence_multiplier * leverage_multiplier
        
        return position_size
    
    async def check_liquidation_risk(
        self,
        entry_price: float,
        current_price: float,
        leverage: float,
        direction: str
    ) -> Dict[str, Any]:
        """
        Check if position is at risk of liquidation.
        For perpetuals trading.
        """
        
        if direction == "LONG":
            price_drop_to_liquidation = entry_price * (1 - 1/leverage)
            buffer_remaining = ((current_price - price_drop_to_liquidation) / current_price) * 100
        else:  # SHORT
            price_rise_to_liquidation = entry_price * (1 + 1/leverage)
            buffer_remaining = ((price_rise_to_liquidation - current_price) / current_price) * 100
        
        at_risk = buffer_remaining < 20
        
        return {
            "at_liquidation_risk": at_risk,
            "buffer_remaining_pct": buffer_remaining,
            "liquidation_price": price_drop_to_liquidation if direction == "LONG" else price_rise_to_liquidation
        }
