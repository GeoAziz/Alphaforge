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
        trade_type: str = "spot",
        user_sharpe_ratio: float = 1.0,
        current_volatility: float = 0.0,
        historical_volatility: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Comprehensive trade validation per §7 Architecture Doc.
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
        
        # 5. Stop loss check (§7: REQUIRED on all trades — hard reject if missing)
        sl_valid = signal.get("stop_loss_price") is not None
        if not sl_valid:
            logger.warning("❌ Stop loss not defined - REJECTING trade per §7")
            return {
                "approved": False,
                "risk_score": 10.0,
                "warnings": ["Stop loss required per risk policy — order rejected"],
                "reason": "Stop loss required on all orders (§7 Risk Engine)"
            }
        checks_passed += 1
        
        # 6. Risk score calculation (§7: with Sharpe ratio component)
        risk_score = self._calculate_risk_score(
            confidence,
            leverage,
            signal,
            correlation_valid,
            user_sharpe_ratio=user_sharpe_ratio,
            current_volatility=current_volatility,
            historical_volatility=historical_volatility,
        )
        
        if risk_score > 8.0:
            return {
                "approved": False,
                "risk_score": risk_score,
                "warnings": warnings,
                "reason": f"Risk score too high: {risk_score:.1f}/10"
            }
        checks_passed += 1
        
        # Calculate position size (volatility-adjusted if vol data available)
        base_size = self._calculate_position_size(confidence, portfolio_balance, leverage)
        if current_volatility > 0 and historical_volatility > 0:
            position_size = self.calculate_volatility_adjusted_size(
                base_size, current_volatility, historical_volatility
            )
        else:
            position_size = base_size
        
        # Final decision
        approved = risk_score < 6.0
        
        logger.info(f"✅ Trade validation: {ticker} {signal_type} - Score: {risk_score:.1f}/10, Size: {position_size:.2f}, Approved: {approved}")
        
        return {
            "approved": approved,
            "risk_score": risk_score,
            "warnings": warnings,
            "position_size": position_size,
            "reason": "Trade approved" if approved else f"Risk score {risk_score:.1f}/10 exceeds threshold"
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
        has_correlation: bool,
        user_sharpe_ratio: float = 1.0,
        current_volatility: float = 0.0,
        historical_volatility: float = 0.0,
    ) -> float:
        """
        Calculate composite risk score (0-10, lower is better).
        §7 Architecture Doc formula:
        Risk Score = (Position Size % × Leverage × Volatility Index × (1 - Sharpe Ratio)) + Correlation Risk
        """
        
        position_size_pct = 2.0  # Max 2% per position
        
        # Volatility index: ratio of current to historical vol, clamped
        if historical_volatility > 0 and current_volatility > 0:
            vol_index = min(current_volatility / historical_volatility, 3.0)
        else:
            vol_index = 1.0  # Neutral when vol data unavailable
        
        # Sharpe ratio factor (1 - Sharpe), clamped to [0, 1]
        sharpe_factor = max(0.0, min(1.0, 1.0 - user_sharpe_ratio))
        
        # §7 formula: Position Size % × Leverage × Volatility Index × (1 - Sharpe)
        base_risk = position_size_pct * leverage * vol_index * sharpe_factor
        
        # Normalize to 0-10 scale
        confidence_risk = (1 - confidence) * 3  # 0-3
        
        # Leverage excess risk
        leverage_risk = max(0, (leverage - 1) * 0.3)  # 0-1.5
        
        # Correlation penalty
        correlation_risk = 2.0 if has_correlation else 0
        
        total_risk = (base_risk * 0.5) + confidence_risk + leverage_risk + correlation_risk
        
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

    # ========================================================================
    # VOLATILITY-ADJUSTED POSITION SIZING (§10)
    # ========================================================================

    def calculate_volatility_adjusted_size(
        self,
        base_size: float,
        current_vol_20d: float,
        historical_avg_vol_60d: float,
    ) -> float:
        """
        Architecture Doc §10: adjusted_size = base_size × (20-day_vol / 60-day_avg_vol)
        If current IV is 3× historical, position reduced to 33%.
        """
        if historical_avg_vol_60d <= 0:
            return base_size

        vol_ratio = current_vol_20d / historical_avg_vol_60d
        adjusted = base_size / vol_ratio if vol_ratio > 0 else base_size
        return adjusted

    # ========================================================================
    # FUNDING RATE ALERTS (§10)
    # ========================================================================

    async def check_funding_rate(
        self, ticker: str, current_funding_rate: float
    ) -> Dict[str, Any]:
        """
        Architecture Doc §10: Funding rate alert: Warn if >1% daily.
        """
        daily_rate = abs(current_funding_rate)
        alert = daily_rate > 0.01

        return {
            "ticker": ticker,
            "funding_rate": current_funding_rate,
            "daily_rate": daily_rate,
            "alert": alert,
            "message": f"⚠️ Funding rate {daily_rate*100:.2f}% exceeds 1% threshold" if alert else "Funding rate normal",
        }

    # ========================================================================
    # LIQUIDATION PRICE CALCULATION (§10)
    # ========================================================================

    def calculate_liquidation_price(
        self,
        entry_price: float,
        margin: float,
        position_size: float,
        leverage: float,
        direction: str,
    ) -> Dict[str, Any]:
        """
        Architecture Doc §10: Liquidation Price formula.
        System checks: If (Liquidation Price - Mark Price) < (Mark Price * 0.20) → Reject
        """
        if direction == "LONG":
            liq_price = entry_price - (margin * entry_price / position_size)
        else:
            liq_price = entry_price + (margin * entry_price / position_size)

        return {
            "liquidation_price": liq_price,
            "direction": direction,
            "entry_price": entry_price,
            "buffer_pct": abs(liq_price - entry_price) / entry_price * 100 if entry_price else 0,
        }

    def validate_liquidation_buffer(
        self, liquidation_price: float, mark_price: float
    ) -> Dict[str, Any]:
        """Check if liquidation buffer is sufficient (20% cushion)."""
        if mark_price <= 0:
            return {"valid": False, "reason": "Invalid mark price"}

        buffer_pct = abs(liquidation_price - mark_price) / mark_price * 100
        valid = buffer_pct >= self.LIQUIDATION_BUFFER_PCT * 100

        return {
            "valid": valid,
            "buffer_pct": round(buffer_pct, 2),
            "required_pct": self.LIQUIDATION_BUFFER_PCT * 100,
            "liquidation_price": liquidation_price,
            "mark_price": mark_price,
            "reason": "Buffer OK" if valid else f"Buffer {buffer_pct:.1f}% < required {self.LIQUIDATION_BUFFER_PCT*100}%",
        }
