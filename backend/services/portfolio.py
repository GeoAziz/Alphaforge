"""
Portfolio Service - §10 Architecture Doc
Maintains open positions and calculates portfolio state.
Tracks positions, unrealized PnL, exposure limits, Sharpe ratio,
win rate, max drawdown, profit factor, and margin usage.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)

import numpy as np


class PortfolioService:
    """Manages user portfolio state and open positions."""
    
    def __init__(self, db):
        self.db = db
        self.MAX_POSITION_SIZE_PCT = 0.02  # 2% per position
        self.MAX_PORTFOLIO_EXPOSURE_PCT = 0.20  # 20% per asset
        self.MAX_LEVERAGE = 5
    
    async def open_position(
        self,
        user_id: str,
        ticker: str,
        direction: str,
        entry_price: float,
        quantity: float,
        signal_id: Optional[str] = None,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Open a new trading position.
        """
        
        if current_price is None:
            current_price = entry_price
        
        position_data = {
            "user_id": user_id,
            "ticker": ticker,
            "direction": direction,
            "entry_price": entry_price,
            "quantity": quantity,
            "current_price": current_price,
            "signal_id": signal_id,
            "opened_at": datetime.utcnow().isoformat()
        }
        
        try:
            response = self.db.supabase.table("positions").insert(position_data).execute()
            position_id = response.data[0]["id"] if response.data else None
            
            logger.info(f"✅ Position opened: {ticker} {direction} ({quantity} @{entry_price})")
            
            return {
                "success": True,
                "position_id": position_id,
                "position": position_data
            }
        
        except Exception as e:
            logger.error(f"❌ Position creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_position(
        self,
        user_id: str,
        position_id: str,
        exit_price: float
    ) -> Dict[str, Any]:
        """
        Close an open position and record realized PnL.
        """
        
        try:
            # Fetch position
            response = self.db.supabase.table("positions").select("*").eq("id", position_id).eq("user_id", user_id).execute()
            
            if not response.data:
                return {"success": False, "error": "Position not found"}
            
            position = response.data[0]
            
            entry_price = float(position["entry_price"])
            quantity = float(position["quantity"])
            direction = position["direction"]
            
            # Calculate PnL
            if direction == "LONG":
                pnl = (exit_price - entry_price) * quantity
            else:  # SHORT
                pnl = (entry_price - exit_price) * quantity
            
            # Delete position (closed)
            self.db.supabase.table("positions").delete().eq("id", position_id).execute()
            
            logger.info(f"✅ Position closed: {position['ticker']} (PnL: ${pnl:.2f})")
            
            return {
                "success": True,
                "pnl": pnl,
                "exit_price": exit_price
            }
        
        except Exception as e:
            logger.error(f"❌ Position close failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_position_price(
        self,
        position_id: str,
        current_price: float
    ) -> Dict[str, Any]:
        """Update current price for a position (for real-time updates)."""
        
        try:
            self.db.supabase.table("positions").update({
                "current_price": current_price
            }).eq("id", position_id).execute()
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"❌ Position price update failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_open_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all open positions for a user."""
        
        try:
            response = self.db.supabase.table("positions").select("*").eq("user_id", user_id).execute()
            positions = response.data or []
            
            # Calculate unrealized PnL for each position
            for i, position in enumerate(positions):
                positions[i] = self._calculate_position_pnl(position)

            return positions
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch positions: {e}")
            return []
    
    async def get_portfolio_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        
        try:
            # Fetch portfolio record
            portfolio_response = self.db.supabase.table("portfolios").select("*").eq("user_id", user_id).execute()
            
            if portfolio_response.data:
                portfolio = portfolio_response.data[0]
            else:
                # Create default
                portfolio = {
                    "user_id": user_id,
                    "starting_balance": 100000,
                    "current_balance": 100000,
                    "total_pnl": 0
                }
                self.db.supabase.table("portfolios").insert(portfolio).execute()
            
            # Get open positions
            positions = await self.get_open_positions(user_id)
            
            # Calculate metrics from positions
            total_unrealized_pnl = 0
            total_exposure = 0
            
            for position in positions:
                position = self._calculate_position_pnl(position)
                total_unrealized_pnl += position.get("unrealized_pnl", 0)
                total_exposure += position.get("risk_exposure_pct", 0)
            
            current_balance = float(portfolio.get("current_balance", 100000))
            total_equity = current_balance + total_unrealized_pnl
            
            summary = {
                "portfolio_id": portfolio.get("id"),
                "user_id": user_id,
                "starting_balance": float(portfolio.get("starting_balance", 100000)),
                "current_balance": current_balance,
                "total_equity": total_equity,
                "unrealized_pnl": total_unrealized_pnl,
                "realized_pnl": float(portfolio.get("total_pnl", 0)),
                "total_pnl": total_unrealized_pnl + float(portfolio.get("total_pnl", 0)),
                "total_pnl_percent": (total_unrealized_pnl + float(portfolio.get("total_pnl", 0))) / float(portfolio.get("starting_balance", 100000)) * 100,
                "open_positions_count": len(positions),
                "total_exposure_pct": total_exposure,
                "open_positions": positions
            }
            
            logger.info(f"📊 Portfolio summary for {user_id}: Equity ${summary['total_equity']:.2f}, PnL {summary['total_pnl_percent']:+.2f}%")
            
            return summary
        
        except Exception as e:
            logger.error(f"❌ Portfolio summary calculation failed: {e}")
            return {}
    
    def _calculate_position_pnl(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate unrealized PnL metrics for a position."""
        
        entry_price = float(position.get("entry_price", 0))
        current_price = float(position.get("current_price", entry_price))
        quantity = float(position.get("quantity", 0))
        direction = position.get("direction", "LONG")
        
        # Calculate unrealized PnL
        if direction == "LONG":
            unrealized_pnl = (current_price - entry_price) * quantity
        else:  # SHORT
            unrealized_pnl = (entry_price - current_price) * quantity
        
        unrealized_pnl_percent = (unrealized_pnl / (entry_price * quantity) * 100) if (entry_price * quantity) > 0 else 0
        
        # Risk exposure (as % of position value)
        position_value = entry_price * quantity
        risk_exposure_pct = position_value / 100000 * 100  # Assuming 100k portfolio
        
        position.update({
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": unrealized_pnl_percent,
            "risk_exposure_pct": risk_exposure_pct
        })
        
        return position
    
    async def validate_position_size(
        self,
        user_id: str,
        portfolio_balance: float,
        ticker: str,
        position_value: float
    ) -> Tuple[bool, str]:
        """
        Validate if a new position meets risk constraints.
        Returns: (is_valid, reason)
        """
        
        # Check: Position size limit (2% of portfolio)
        position_size_pct = (position_value / portfolio_balance) * 100
        if position_size_pct > 2:
            return False, f"Position size ({position_size_pct:.2f}%) exceeds 2% limit"
        
        # Check: Existing exposure to same asset
        positions = await self.get_open_positions(user_id)
        existing_exposure = sum(
            float(p.get("entry_price", 0)) * float(p.get("quantity", 0))
            for p in positions
            if p.get("ticker") == ticker
        )
        
        total_exposure = existing_exposure + position_value
        exposure_pct = (total_exposure / portfolio_balance) * 100
        
        if exposure_pct > 20:
            return False, f"Total {ticker} exposure ({exposure_pct:.2f}%) exceeds 20% limit"
        
        return True, "Position size valid"

    # ====================================================================
    # §10 PORTFOLIO METRICS: Sharpe, Win Rate, Max Drawdown, Profit Factor
    # ====================================================================

    async def get_performance_metrics(
        self, user_id: str, period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive portfolio performance metrics (§10).
        Includes: Sharpe ratio (rolling), win rate, max drawdown, profit factor.
        """
        try:
            # Fetch closed trades for the period
            cutoff = (datetime.utcnow() - timedelta(days=period_days)).isoformat()
            response = (
                self.db.supabase.table("paper_trades")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "CLOSED")
                .gte("exit_time", cutoff)
                .order("exit_time", desc=True)
                .execute()
            )
            trades = response.data or []

            if not trades:
                return {
                    "success": True,
                    "period_days": period_days,
                    "total_trades": 0,
                    "sharpe_ratio": 0.0,
                    "win_rate": 0.0,
                    "max_drawdown_pct": 0.0,
                    "profit_factor": 0.0,
                    "total_pnl": 0.0,
                    "avg_pnl": 0.0,
                    "best_trade": 0.0,
                    "worst_trade": 0.0,
                }

            pnls = [float(t.get("pnl", 0)) for t in trades]
            wins = [p for p in pnls if p > 0]
            losses = [abs(p) for p in pnls if p < 0]

            # Win rate
            win_rate = len(wins) / len(pnls) if pnls else 0.0

            # Sharpe ratio (annualized from daily returns)
            if len(pnls) > 1:
                avg_return = np.mean(pnls)
                std_return = np.std(pnls)
                sharpe = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0.0
            else:
                sharpe = 0.0

            # Max drawdown
            cumulative = np.cumsum(pnls)
            peak = np.maximum.accumulate(cumulative)
            drawdowns = (cumulative - peak)
            max_drawdown = float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0
            max_drawdown_pct = abs(max_drawdown) / max(float(peak.max()), 1) * 100 if peak.max() > 0 else 0.0

            # Profit factor
            total_wins = sum(wins)
            total_losses = sum(losses)
            profit_factor = total_wins / total_losses if total_losses > 0 else float("inf") if total_wins > 0 else 0.0

            return {
                "success": True,
                "period_days": period_days,
                "total_trades": len(trades),
                "sharpe_ratio": round(float(sharpe), 4),
                "win_rate": round(win_rate, 4),
                "max_drawdown_pct": round(float(max_drawdown_pct), 2),
                "profit_factor": round(float(profit_factor), 4) if profit_factor != float("inf") else 999.0,
                "total_pnl": round(sum(pnls), 2),
                "avg_pnl": round(float(np.mean(pnls)), 2),
                "best_trade": round(max(pnls), 2) if pnls else 0.0,
                "worst_trade": round(min(pnls), 2) if pnls else 0.0,
                "total_wins": len(wins),
                "total_losses": len(losses),
            }

        except Exception as e:
            logger.error(f"❌ Performance metrics calculation failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_benchmark_comparison(
        self,
        user_id: str,
        market_data_service,
        period_days: int = 30,
        benchmarks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compare portfolio return against BTC/ETH (or custom tickers) over a period (§10).
        """
        benchmarks = benchmarks or ["BTC", "ETH"]

        try:
            summary = await self.get_portfolio_summary(user_id)
            starting_balance = float(summary.get("starting_balance", 100000)) or 100000

            perf = await self.get_performance_metrics(user_id, period_days=period_days)
            portfolio_return_pct = (float(perf.get("total_pnl", 0)) / starting_balance) * 100

            benchmark_results = {}
            for ticker in benchmarks:
                symbol = f"{ticker.upper()}USDT"
                candles = await market_data_service.fetch_ohlcv(symbol, interval="1d", limit=period_days + 1)

                if not candles or len(candles) < 2:
                    benchmark_results[ticker] = {
                        "return_pct": None,
                        "error": "insufficient historical data",
                    }
                    continue

                first_close = float(candles[0]["close"])
                last_close = float(candles[-1]["close"])
                benchmark_return_pct = ((last_close - first_close) / first_close * 100) if first_close else 0.0

                benchmark_results[ticker] = {
                    "return_pct": round(benchmark_return_pct, 4),
                    "alpha_pct": round(portfolio_return_pct - benchmark_return_pct, 4),
                    "outperformed": portfolio_return_pct > benchmark_return_pct,
                }

            return {
                "success": True,
                "user_id": user_id,
                "period_days": period_days,
                "portfolio_return_pct": round(portfolio_return_pct, 4),
                "benchmarks": benchmark_results,
            }

        except Exception as e:
            logger.error(f"❌ Benchmark comparison failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_portfolio_summary_enhanced(self, user_id: str) -> Dict[str, Any]:
        """
        Enhanced portfolio summary with all §10 metrics.
        Combines basic summary with performance metrics.
        """
        basic = await self.get_portfolio_summary(user_id)
        metrics_30d = await self.get_performance_metrics(user_id, period_days=30)
        metrics_90d = await self.get_performance_metrics(user_id, period_days=90)
        all_time = await self.get_performance_metrics(user_id, period_days=3650)

        basic["performance"] = {
            "rolling_30d": {
                "sharpe_ratio": metrics_30d.get("sharpe_ratio", 0),
                "win_rate": metrics_30d.get("win_rate", 0),
                "max_drawdown_pct": metrics_30d.get("max_drawdown_pct", 0),
                "profit_factor": metrics_30d.get("profit_factor", 0),
            },
            "rolling_90d": {
                "sharpe_ratio": metrics_90d.get("sharpe_ratio", 0),
                "win_rate": metrics_90d.get("win_rate", 0),
                "max_drawdown_pct": metrics_90d.get("max_drawdown_pct", 0),
                "profit_factor": metrics_90d.get("profit_factor", 0),
            },
            "all_time": {
                "sharpe_ratio": all_time.get("sharpe_ratio", 0),
                "win_rate": all_time.get("win_rate", 0),
                "max_drawdown_pct": all_time.get("max_drawdown_pct", 0),
                "profit_factor": all_time.get("profit_factor", 0),
            },
        }

        return basic

    async def calculate_margin_usage(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate margin usage for perpetuals positions (§10).
        """
        try:
            positions = await self.get_open_positions(user_id)
            perps = [p for p in positions if p.get("trade_type") == "perpetuals"]

            total_margin = 0.0
            total_unrealised = 0.0
            for p in perps:
                entry = float(p.get("entry_price", 0))
                qty = float(p.get("quantity", 0))
                leverage = float(p.get("leverage", 1))
                margin = (entry * qty) / leverage if leverage > 0 else entry * qty
                total_margin += margin
                total_unrealised += p.get("unrealized_pnl", 0)

            portfolio_response = self.db.supabase.table("portfolios").select("*").eq("user_id", user_id).execute()
            portfolio = portfolio_response.data[0] if portfolio_response.data else {}
            balance = float(portfolio.get("current_balance", 100000))

            margin_used_pct = (total_margin / balance * 100) if balance > 0 else 0

            return {
                "total_margin_used": round(total_margin, 2),
                "total_unrealised_pnl": round(total_unrealised, 2),
                "margin_used_pct": round(margin_used_pct, 2),
                "available_margin": round(balance - total_margin, 2),
                "perps_position_count": len(perps),
            }

        except Exception as e:
            logger.error(f"❌ Margin usage calculation failed: {e}")
            return {"success": False, "error": str(e)}
