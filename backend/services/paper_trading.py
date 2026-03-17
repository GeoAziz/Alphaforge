"""
Paper Trading Service - Simulates trading without real capital.
Handles entry/exit, PnL calculation, performance metrics.
"""

import logging
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """Simulates trading execution and tracks performance."""
    
    # Configuration
    DEFAULT_SLIPPAGE = 0.001  # 0.1%
    
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
            
            # Calculate PnL
            if direction == "LONG":
                pnl = (exit_price - entry_price) * quantity
            else:  # SHORT
                pnl = (entry_price - exit_price) * quantity
            
            pnl_percent = (pnl / (entry_price * quantity)) * 100
            
            # Apply slippage on exit
            actual_exit = self._apply_slippage(exit_price, direction, is_exit=True)
            
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
        Entry slippage works against trader (worse price).
        Exit slippage also works against trader for realism.
        """
        slippage_amount = price * self.slippage
        
        if direction == "LONG":
            # Long entry: slippage pushes price up (worse for buyer)
            return price + slippage_amount if not is_exit else price - slippage_amount
        else:  # SHORT
            # Short entry: slippage pushes price down (worse for shorter)
            return price - slippage_amount if not is_exit else price + slippage_amount
    
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
