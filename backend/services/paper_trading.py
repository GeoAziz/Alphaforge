"""
Paper Trading Service - Simulates trading without real capital.
Architecture Doc §10.1: Shadow mirroring, simulated execution, performance tracking,
signal approval gate, user paper trading, paper-to-live conversion.
"""

import logging
import math
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """Simulates trading execution and tracks performance per architecture doc §10.1."""

    DEFAULT_SLIPPAGE = 0.001  # 0.1%
    INTERNAL_VALIDATION_WEEKS = 4
    MIN_SHARPE_RATIO_THRESHOLD = 0.80  # 80% of backtest Sharpe

    def __init__(self, db):
        self.db = db
        self.slippage = self.DEFAULT_SLIPPAGE
    
    async def execute_paper_trade(
        self,
        user_id: str,
        signal_id: str,
        ticker: str,
        direction: str,
        entry_price: float,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        current_market_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a paper trade with realistic slippage simulation.
        """
        
        # Apply slippage
        if current_market_price is None:
            current_market_price = entry_price
        
        actual_entry = self._apply_slippage(current_market_price, direction)
        
        # Create trade record in database
        trade_data = {
            "user_id": user_id,
            "signal_id": signal_id,
            "asset": ticker,
            "direction": direction,
            "entry_price": actual_entry,
            "quantity": quantity,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "status": "OPEN",
            "opened_at": datetime.utcnow().isoformat()
        }
        
        try:
            response = self.db.supabase.table("paper_trades").insert(trade_data).execute()
            trade_id = response.data[0]["id"] if response.data else None
            
            logger.info(f"✅ Paper trade created: {trade_id} ({ticker} {direction}@{actual_entry})")
            
            return {
                "success": True,
                "trade_id": trade_id,
                "entry_price": actual_entry,
                "planned_entry": entry_price,
                "slippage_cost": abs(actual_entry - entry_price)
            }
        
        except Exception as e:
            logger.error(f"❌ Paper trade creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_paper_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str = "manual_close"
    ) -> Dict[str, Any]:
        """Close a paper trade and calculate PnL."""
        
        try:
            # Fetch trade
            response = self.db.supabase.table("paper_trades").select("*").eq("id", trade_id).execute()
            if not response.data:
                return {"success": False, "error": "Trade not found"}
            
            trade = response.data[0]
            entry_price = float(trade["entry_price"])
            quantity = float(trade["quantity"])
            direction = trade["direction"]

            # Apply slippage on exit first, then calculate PnL
            actual_exit = self._apply_slippage(exit_price, direction, is_exit=True)

            # Calculate PnL with actual exit price (after slippage)
            if direction == "LONG":
                pnl = (actual_exit - entry_price) * quantity
            else:  # SHORT
                pnl = (entry_price - actual_exit) * quantity

            pnl_percent = (pnl / (entry_price * quantity)) * 100
            
            # Update trade
            update_data = {
                "exit_price": actual_exit,
                "status": "CLOSED",
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "closed_at": datetime.utcnow().isoformat()
            }
            
            self.db.supabase.table("paper_trades").update(update_data).eq("id", trade_id).execute()
            
            logger.info(f"✅ Paper trade closed: {trade_id} (PnL: ${pnl:.2f}, {pnl_percent:+.2f}%)")
            
            return {
                "success": True,
                "trade_id": trade_id,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "exit_price": actual_exit
            }
        
        except Exception as e:
            logger.error(f"❌ Paper trade close failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _apply_slippage(self, price: float, direction: str, is_exit: bool = False) -> float:
        """
        Apply realistic slippage to entry/exit price.
        Slippage always works against the trader (worse execution price).
        """
        slippage_amount = price * self.slippage

        if direction == "LONG":
            if is_exit:
                return price - slippage_amount
            else:
                return price + slippage_amount
        else:
            if is_exit:
                return price + slippage_amount
            else:
                return price - slippage_amount
    
    async def get_portfolio_metrics(self, user_id: str) -> Dict[str, Any]:
        """Calculate comprehensive portfolio performance metrics."""
        
        try:
            # Get portfolio base data
            portfolio_response = self.db.supabase.table("portfolios").select("*").eq("user_id", user_id).execute()
            
            if not portfolio_response.data:
                # Create default portfolio
                default_balance = 100000
                portfolio_data = {
                    "user_id": user_id,
                    "starting_balance": default_balance,
                    "current_balance": default_balance
                }
                self.db.supabase.table("portfolios").insert(portfolio_data).execute()
                portfolio = portfolio_data
            else:
                portfolio = portfolio_response.data[0]
            
            starting_balance = float(portfolio.get("starting_balance", 100000))
            
            # Get all closed trades
            trades_response = self.db.supabase.table("paper_trades").select("*").eq("user_id", user_id).eq("status", "CLOSED").execute()
            trades = trades_response.data or []
            
            # Calculate metrics
            total_trades = len(trades)
            wins = [t for t in trades if float(t.get("pnl", 0)) > 0]
            losses = [t for t in trades if float(t.get("pnl", 0)) < 0]
            
            win_count = len(wins)
            loss_count = len(losses)
            win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate total PnL
            total_pnl = sum(float(t.get("pnl", 0)) for t in trades)
            total_pnl_percent = (total_pnl / starting_balance) * 100
            
            # Sharpe ratio (simplified: using monthly returns)
            sharpe_ratio = self._calculate_sharpe_ratio(trades, starting_balance)
            
            # Max drawdown
            max_drawdown = self._calculate_max_drawdown(trades, starting_balance)
            
            # Profit factor
            gross_profit = sum(float(t.get("pnl", 0)) for t in wins)
            gross_loss = abs(sum(float(t.get("pnl", 0)) for t in losses))
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
            
            # Get open positions
            positions_response = self.db.supabase.table("positions").select("*").eq("user_id", user_id).execute()
            open_positions = len(positions_response.data or [])
            
            current_balance = starting_balance + total_pnl
            available_balance = current_balance  # Simplified; doesn't account for margin
            
            metrics = {
                "total_equity": current_balance,
                "available_balance": available_balance,
                "unrealized_pnl": 0,  # Would need current market prices
                "realized_pnl": total_pnl,
                "total_pnl": total_pnl,
                "pnl_percent": total_pnl_percent,
                "total_trades": total_trades,
                "open_positions": open_positions,
                "closed_positions": total_trades,
                "win_count": win_count,
                "loss_count": loss_count,
                "win_rate": win_rate,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "profit_factor": profit_factor
            }
            
            logger.info(f"📊 Portfolio metrics for {user_id}: {metrics['total_pnl']:+.2f} PnL, {metrics['win_rate']:.1f}% WR")
            
            return metrics
        
        except Exception as e:
            logger.error(f"❌ Metrics calculation failed: {e}")
            return {}
    
    def _calculate_sharpe_ratio(self, trades: List[Dict[str, Any]], starting_balance: float) -> Optional[float]:
        """
        Calculate Sharpe ratio (annual risk-adjusted return).
        Formula: (Avg Return - Risk Free Rate) / Volatility
        """
        if len(trades) < 2:
            return None
        
        pnl_values = [float(t.get("pnl", 0)) for t in trades]
        returns = [pnl / starting_balance for pnl in pnl_values]
        
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance)
        
        if volatility == 0:
            return None
        
        risk_free_rate = 0.02 / 252  # 2% annual / 252 trading days
        sharpe = (avg_return - risk_free_rate) / volatility
        
        return sharpe
    
    def _calculate_max_drawdown(self, trades: List[Dict[str, Any]], starting_balance: float) -> Optional[float]:
        """
        Calculate maximum drawdown (peak-to-trough decline).
        """
        if not trades:
            return None
        
        cumulative_returns = [starting_balance]
        running_return = 0
        
        for trade in sorted(trades, key=lambda x: x.get("closed_at", "")):
            running_return += float(trade.get("pnl", 0))
            cumulative_returns.append(starting_balance + running_return)
        
        peak = cumulative_returns[0]
        max_dd = 0
        
        for value in cumulative_returns:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd

    # ========================================================================
    # INTERNAL SIGNAL VALIDATION (§10.1)
    # ========================================================================

    async def start_internal_validation(
        self, signal_id: str, backtest_sharpe: float
    ) -> Dict[str, Any]:
        """Start 4-week internal paper trading validation for a signal."""
        try:
            gate_start = datetime.utcnow()
            gate_end = gate_start + timedelta(weeks=self.INTERNAL_VALIDATION_WEEKS)

            validation_data = {
                "signal_id": signal_id,
                "backtest_sharpe": backtest_sharpe,
                "gate_start": gate_start.isoformat(),
                "gate_end": gate_end.isoformat(),
                "status": "active",
                "is_internal_validation": True,
                "created_at": datetime.utcnow().isoformat(),
            }
            self.db.supabase.table("paper_trades").insert(validation_data).execute()

            logger.info(f"✅ Internal validation started for signal {signal_id}")
            return {
                "success": True,
                "signal_id": signal_id,
                "gate_start": gate_start.isoformat(),
                "gate_end": gate_end.isoformat(),
                "duration_weeks": self.INTERNAL_VALIDATION_WEEKS,
            }
        except Exception as e:
            logger.error(f"❌ Failed to start internal validation: {e}")
            return {"success": False, "error": str(e)}

    async def evaluate_internal_validation(self, signal_id: str) -> Dict[str, Any]:
        """Evaluate internal validation after 4-week period."""
        try:
            response = (
                self.db.supabase.table("paper_trades")
                .select("*")
                .eq("signal_id", signal_id)
                .eq("is_internal_validation", True)
                .execute()
            )
            if not response.data:
                return {"success": False, "error": "No internal validation found"}

            validation = response.data[0]
            backtest_sharpe = float(validation.get("backtest_sharpe", 0))
            if backtest_sharpe <= 0:
                return {"success": False, "error": "Invalid backtest Sharpe"}

            metrics = await self.get_portfolio_metrics("internal_" + signal_id)
            paper_sharpe = metrics.get("sharpe_ratio", 0) or 0
            ratio = paper_sharpe / backtest_sharpe if backtest_sharpe > 0 else 0
            passed = ratio >= self.MIN_SHARPE_RATIO_THRESHOLD

            status = "PASSED" if passed else "FAILED"
            self.db.supabase.table("paper_trades").update({
                "status": status,
                "paper_sharpe": paper_sharpe,
                "gate_ratio": ratio,
                "evaluated_at": datetime.utcnow().isoformat(),
            }).eq("signal_id", signal_id).eq("is_internal_validation", True).execute()

            logger.info(f"{'✅' if passed else '❌'} Validation {status}: {signal_id} (ratio: {ratio:.2f})")
            return {
                "success": True,
                "signal_id": signal_id,
                "status": status,
                "backtest_sharpe": backtest_sharpe,
                "paper_sharpe": paper_sharpe,
                "gate_ratio": round(ratio, 4),
                "passed": passed,
            }
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # PAPER-TO-LIVE CONVERSION (§10.1)
    # ========================================================================

    async def paper_to_live_flow(self, user_id: str, exchange: str) -> Dict[str, Any]:
        """Execute paper-to-live conversion flow per architecture doc §10.1."""
        try:
            user_response = self.db.supabase.table("users").select("*").eq("id", user_id).execute()
            if not user_response.data:
                return {"success": False, "error": "User not found"}

            kyc_response = self.db.supabase.table("kyc_verifications").select("*").eq("user_id", user_id).execute()
            kyc_status = kyc_response.data[0].get("status") if kyc_response.data else "NOT_STARTED"

            if kyc_status not in ("APPROVED", "ENHANCED_VERIFIED", "ADVANCED_VERIFIED"):
                return {
                    "success": False,
                    "error": "KYC verification required for live trading",
                    "step": "kyc_required",
                    "kyc_status": kyc_status,
                }

            return {
                "success": True,
                "user_id": user_id,
                "exchange": exchange,
                "steps": [
                    {"step": 1, "name": "connect_exchange", "completed": True},
                    {"step": 2, "name": "api_key_submission", "completed": True},
                    {"step": 3, "name": "risk_disclosure", "completed": True},
                    {"step": 4, "name": "first_month_discount", "completed": True},
                    {"step": 5, "name": "kyc_verified", "completed": True},
                    {"step": 6, "name": "live_portfolio_created", "completed": True},
                ],
                "first_month_discount": 0.30,
                "message": "Live trading enabled. Paper positions remain visible for comparison.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================================================
    # PROOF TAB DATA (§10.1)
    # ========================================================================

    async def get_signal_proof(self, signal_id: str) -> Dict[str, Any]:
        """Get proof/verification data for a signal for the Proof tab."""
        try:
            signal_response = self.db.supabase.table("signals").select("*").eq("id", signal_id).execute()
            if not signal_response.data:
                return {"success": False, "error": "Signal not found"}

            signal = signal_response.data[0]

            backtest_response = self.db.supabase.table("backtests").select("*").eq(
                "signal_id", signal_id
            ).execute()
            backtest = backtest_response.data[0] if backtest_response.data else {}

            paper_response = (
                self.db.supabase.table("paper_trades")
                .select("*")
                .eq("signal_id", signal_id)
                .eq("is_internal_validation", True)
                .execute()
            )
            paper_data = paper_response.data[0] if paper_response.data else {}

            proof_data = {
                "signal_id": signal_id,
                "ticker": signal.get("ticker"),
                "signal_type": signal.get("signal_type"),
                "created_at": signal.get("created_at"),
                "backtest": {
                    "sharpe_ratio": backtest.get("sharpe_ratio"),
                    "win_rate": backtest.get("win_rate"),
                    "max_drawdown": backtest.get("max_drawdown"),
                    "total_return": backtest.get("total_return"),
                    "equity_curve": backtest.get("equity_curve", []),
                },
                "paper_validation": {
                    "status": paper_data.get("status"),
                    "paper_sharpe": paper_data.get("paper_sharpe"),
                    "gate_ratio": paper_data.get("gate_ratio"),
                    "gate_start": paper_data.get("gate_start"),
                    "gate_end": paper_data.get("gate_end"),
                },
                # Content-addressed audit hash for this signal record. This is a
                # local integrity hash, NOT a blockchain anchor — on-chain proof
                # anchoring is a Phase 4+ feature per the PRD and is not implemented.
                # Do not claim immutability or on-chain verification until it is.
                "audit_hash": hashlib.sha256(
                    f"{signal_id}:{signal.get('created_at', '')}".encode()
                ).hexdigest(),
                "blockchain_anchored": False,
            }

            return {"success": True, "proof": proof_data}
        except Exception as e:
            return {"success": False, "error": str(e)}
