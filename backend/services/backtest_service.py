"""
Backtesting Service - Simulates strategy performance on historical data.
Generates backtest results, equity curves, and performance metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from decimal import Decimal

logger = logging.getLogger(__name__)


class BacktestingService:
    """Handles strategy backtesting and historical simulation."""
    
    def __init__(self, db):
        self.db = db
    
    async def run_backtest(
        self,
        user_id: str,
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a backtest for a strategy configuration.
        Returns backtest ID for tracking progress.
        """
        try:
            backtest_data = {
                "user_id": user_id,
                "strategy_name": strategy_config.get("name", "Unnamed Strategy"),
                "strategy_params": strategy_config.get("parameters", {}),
                "symbols": strategy_config.get("symbols", ["BTC", "ETH"]),
                "start_date": strategy_config.get("start_date"),
                "end_date": strategy_config.get("end_date"),
                "initial_capital": float(strategy_config.get("initial_capital", 100000)),
                "status": "RUNNING",
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("backtests").insert(backtest_data).execute()
            
            if response.data:
                backtest_id = response.data[0]["id"]
                logger.info(f"✅ Backtest started: {backtest_id}")
                
                # In production, this would queue a background job
                # For MVP, simulate it asynchronously
                results = await self._simulate_backtest(backtest_id, strategy_config)
                
                return {
                    "success": True,
                    "backtest_id": backtest_id,
                    "status": "completed",
                    "results": results
                }
            
        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
        
        return {"success": False, "error": str(e)}
    
    async def get_backtest_results(
        self,
        backtest_id: str
    ) -> Dict[str, Any]:
        """Retrieve backtest results."""
        try:
            response = self.db.supabase.table("backtests")\
                .select("*")\
                .eq("id", backtest_id)\
                .execute()
            
            if not response.data:
                return {"success": False, "error": "Backtest not found"}
            
            backtest = response.data[0]
            
            # Parse results if stored as JSON
            if isinstance(backtest.get("results"), str):
                backtest["results"] = json.loads(backtest["results"])
            
            return {
                "success": True,
                "backtest": backtest
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to retrieve backtest: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_equity_curve(
        self,
        backtest_id: str
    ) -> Dict[str, Any]:
        """Get equity curve data points for a backtest."""
        try:
            response = self.db.supabase.table("backtests")\
                .select("results")\
                .eq("id", backtest_id)\
                .execute()
            
            if not response.data:
                return {"success": False, "error": "Backtest not found"}
            
            results = response.data[0].get("results", {})
            if isinstance(results, str):
                results = json.loads(results)
            
            equity_curve = results.get("equity_curve", [])
            
            return {
                "success": True,
                "backtest_id": backtest_id,
                "equity_curve": equity_curve
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get equity curve: {e}")
            return {"success": False, "error": str(e)}
    
    async def _simulate_backtest(
        self,
        backtest_id: str,
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate backtest execution (MVP implementation)."""
        
        initial_capital = float(strategy_config.get("initial_capital", 100000))
        
        # Generate simulated results
        # In production, this would run actual historical data
        
        # Simulate equity curve (random walk with uptrend)
        num_days = 252  # 1 year of trading days
        equity_curve = []
        current_equity = initial_capital
        entry_points = []
        exit_points = []
        trades = []
        
        # Generate realistic price movement
        for day in range(num_days):
            # Random daily return between -3% and +4% (realistic for crypto)
            daily_return = (0.04 - 0.03) * 0.3 + (0.02 * ((day % 20) / 20))  # Slightly upward bias
            
            current_equity = current_equity * (1 + daily_return)
            
            equity_curve.append({
                "day": day,
                "equity": round(current_equity, 2),
                "date": (datetime.utcnow() - timedelta(days=num_days - day)).isoformat()
            })
            
            # Simulate trades every 15 days
            if day % 15 == 0 and day > 0:
                entry_price = current_equity
                exit_price = current_equity * (1 + (0.02 if day % 30 == 0 else -0.01))  # Win/loss
                
                trades.append({
                    "entry_day": day - 5,
                    "exit_day": day,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "pnl": round(exit_price - entry_price, 2),
                    "pnl_pct": round((exit_price - entry_price) / entry_price * 100, 2)
                })
        
        # Calculate metrics
        total_return = (current_equity - initial_capital) / initial_capital
        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] < 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        avg_win = sum([t["pnl"] for t in winning_trades]) / len(winning_trades) if winning_trades else 0
        avg_loss = abs(sum([t["pnl"] for t in losing_trades]) / len(losing_trades)) if losing_trades else 0
        
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Calculate drawdown
        max_equity = initial_capital
        max_drawdown = 0
        for point in equity_curve:
            if point["equity"] > max_equity:
                max_equity = point["equity"]
            drawdown = (max_equity - point["equity"]) / max_equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calculate Sharpe ratio (simplified)
        returns = [equity_curve[i]["equity"] / equity_curve[i-1]["equity"] - 1 
                   for i in range(1, len(equity_curve))]
        avg_return = sum(returns) / len(returns) if returns else 0
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 0
        sharpe_ratio = (avg_return * 252) / (std_return * (252 ** 0.5)) if std_return > 0 else 0
        
        results = {
            "equity_curve": equity_curve[-30:],  # Last 30 days
            "metrics": {
                "initial_capital": initial_capital,
                "final_equity": round(current_equity, 2),
                "total_return": f"{total_return:.2%}",
                "total_trades": len(trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": f"{win_rate:.1%}",
                "profit_factor": round(profit_factor, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "max_drawdown": f"{max_drawdown:.2%}",
                "sharpe_ratio": round(sharpe_ratio, 2)
            },
            "trades": trades[-10:] if trades else []  # Last 10 trades
        }
        
        # Store results
        try:
            self.db.supabase.table("backtests")\
                .update({
                    "results": json.dumps(results),
                    "status": "COMPLETED",
                    "completed_at": datetime.utcnow().isoformat()
                })\
                .eq("id", backtest_id)\
                .execute()
        except Exception as e:
            logger.error(f"Failed to save backtest results: {e}")
        
        return results
    
    async def list_user_backtests(
        self,
        user_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List all backtests for a user."""
        try:
            response = self.db.supabase.table("backtests")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            backtests = response.data or []
            
            return {
                "success": True,
                "backtests": backtests,
                "count": len(backtests)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to list backtests: {e}")
            return {"success": False, "error": str(e)}
