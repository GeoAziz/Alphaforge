"""
Signal Backtesting Service
Allows users to test trading signals against historical OHLCV data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class BacktestMetrics(str, Enum):
    """Key metrics calculated during backtesting"""
    TOTAL_TRADES = "total_trades"
    WINNING_TRADES = "winning_trades"
    LOSING_TRADES = "losing_trades"
    WIN_RATE = "win_rate"
    TOTAL_PNL = "total_pnl"
    TOTAL_ROI = "total_roi"
    BEST_TRADE = "best_trade"
    WORST_TRADE = "worst_trade"
    AVG_WIN = "avg_win"
    AVG_LOSS = "avg_loss"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    PROFIT_FACTOR = "profit_factor"


class SignalBacktester:
    """Backtests trading signals against historical OHLCV data"""
    
    def __init__(self, initial_capital: float = 100000, slippage_pct: float = 0.1):
        self.initial_capital = initial_capital
        self.slippage_pct = slippage_pct
    
    async def backtest_signal(
        self,
        signal_id: str,
        asset: str,
        signals: List[Dict[str, Any]],  # [{timestamp, direction, confidence}, ...]
        ohlcv_data: List[Dict[str, Any]],  # [{timestamp, open, high, low, close, volume}, ...]
        hold_time_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Backtest a signal against historical OHLCV data.
        
        Args:
            signal_id: Unique signal identifier
            asset: Trading asset (e.g., BTC, ETH)
            signals: List of signals with execution points
            ohlcv_data: Historical OHLCV candles
            hold_time_hours: How long to hold each trade
        
        Returns:
            Comprehensive backtest results with metrics
        """
        try:
            # Validate inputs
            if not signals or not ohlcv_data:
                return {
                    "success": False,
                    "error": "Missing signals or OHLCV data"
                }
            
            # Create price map for fast lookup
            price_map = {
                self._parse_timestamp(candle["timestamp"]): candle
                for candle in ohlcv_data
            }
            
            trades = []
            equity_curve = [self.initial_capital]
            current_capital = self.initial_capital
            
            for signal in signals:
                signal_time = self._parse_timestamp(signal["timestamp"])
                signal_price = self._get_price_at_time(signal_time, price_map, ohlcv_data)
                
                if signal_price is None:
                    continue
                
                # Calculate entry with slippage
                entry_price = signal_price * (1 + (self.slippage_pct / 100) if signal["direction"] == "BUY" else -(self.slippage_pct / 100))
                
                # Find exit after hold_time_hours
                exit_time = signal_time + timedelta(hours=hold_time_hours)
                exit_price = self._get_price_at_time(exit_time, price_map, ohlcv_data)
                
                if exit_price is None:
                    # Use last available price
                    exit_price = ohlcv_data[-1]["close"] if ohlcv_data else entry_price
                
                # Calculate trade outcome
                if signal["direction"] == "BUY":
                    pnl = exit_price - entry_price
                    roi = (pnl / entry_price) * 100
                else:  # SELL
                    pnl = entry_price - exit_price
                    roi = (pnl / entry_price) * 100
                
                quantity = current_capital * 0.02 / entry_price  # 2% position sizing
                trade_pnl = pnl * quantity
                current_capital += trade_pnl
                
                trades.append({
                    "timestamp": signal["timestamp"],
                    "direction": signal["direction"],
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "quantity": quantity,
                    "pnl": trade_pnl,
                    "roi": roi,
                    "outcome": "WIN" if trade_pnl > 0 else "LOSS" if trade_pnl < 0 else "BREAK_EVEN"
                })
                
                equity_curve.append(current_capital)
            
            # Calculate metrics
            metrics = self._calculate_metrics(trades, equity_curve)
            
            logger.info(f"✅ Backtest complete for {signal_id}: {len(trades)} trades, {metrics['win_rate']:.1%} win rate")
            
            return {
                "success": True,
                "signal_id": signal_id,
                "asset": asset,
                "trades": trades,
                "metrics": metrics,
                "equity_curve": equity_curve,
                "final_capital": current_capital
            }
        
        except Exception as e:
            logger.error(f"❌ Backtest failed for {signal_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_timestamp(self, ts: Any) -> datetime:
        """Parse timestamp to datetime"""
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if isinstance(ts, (int, float)):
            return datetime.utcfromtimestamp(ts)
        return datetime.utcnow()
    
    def _get_price_at_time(
        self,
        target_time: datetime,
        price_map: Dict,
        ohlcv_data: List
    ) -> Optional[float]:
        """Get nearest price at or after target time"""
        if target_time in price_map:
            return price_map[target_time]["close"]
        
        # Find nearest future candle
        for candle in ohlcv_data:
            candle_time = self._parse_timestamp(candle["timestamp"])
            if candle_time >= target_time:
                return candle["open"]  # Use open price of next candle
        
        # Return last available close
        return ohlcv_data[-1]["close"] if ohlcv_data else None
    
    def _calculate_metrics(self, trades: List[Dict], equity_curve: List[float]) -> Dict[str, Any]:
        """Calculate comprehensive backtest metrics"""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "total_roi": 0
            }
        
        pnls = [t["pnl"] for t in trades]
        rois = [t["roi"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        total_pnl = sum(pnls)
        total_roi = (total_pnl / self.initial_capital) * 100
        win_rate = len(wins) / len(trades) if trades else 0
        
        # Sharpe Ratio (assuming 252 trading days per year)
        if len(rois) > 1:
            daily_returns = np.array(rois) / 100
            sharpe = np.mean(daily_returns) / (np.std(daily_returns) + 1e-6) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Max Drawdown
        max_equity = equity_curve[0]
        max_dd = 0
        for equity in equity_curve:
            if equity > max_equity:
                max_equity = equity
            dd = (max_equity - equity) / max_equity
            max_dd = max(max_dd, dd)
        
        # Profit Factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = gross_profit / (gross_loss + 1e-6)
        
        return {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "total_roi_pct": total_roi,
            "best_trade": max(pnls) if pnls else 0,
            "worst_trade": min(pnls) if pnls else 0,
            "avg_win": sum(wins) / len(wins) if wins else 0,
            "avg_loss": sum(losses) / len(losses) if losses else 0,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": max_dd * 100,
            "profit_factor": profit_factor
        }


class BatchBacktester:
    """Backtests multiple signals or strategies in parallel"""
    
    def __init__(self, initial_capital: float = 100000):
        self.backtester = SignalBacktester(initial_capital)
        self.results: Dict[str, Any] = {}
    
    async def backtest_portfolio(
        self,
        signals_map: Dict[str, List[Dict]],  # asset -> signals
        ohlcv_map: Dict[str, List[Dict]],    # asset -> ohlcv_data
        hold_time_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Backtest multiple signals across assets.
        
        Returns:
            Aggregated results for all backtests
        """
        portfolio_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_assets": len(signals_map),
            "asset_results": {},
            "portfolio_metrics": {}
        }
        
        all_pnls = []
        
        for asset, signals in signals_map.items():
            ohlcv = ohlcv_map.get(asset, [])
            
            result = await self.backtester.backtest_signal(
                signal_id=f"portfolio_{asset}",
                asset=asset,
                signals=signals,
                ohlcv_data=ohlcv,
                hold_time_hours=hold_time_hours
            )
            
            if result.get("success"):
                portfolio_results["asset_results"][asset] = result
                all_pnls.extend([t["pnl"] for t in result.get("trades", [])])
        
        # Aggregate portfolio metrics
        if all_pnls:
            portfolio_results["portfolio_metrics"] = {
                "total_trades": sum(len(r.get("trades", [])) for r in portfolio_results["asset_results"].values()),
                "total_pnl": sum(all_pnls),
                "total_roi_pct": (sum(all_pnls) / 100000) * 100,  # Assuming 100k initial
                "win_rate": len([p for p in all_pnls if p > 0]) / len(all_pnls) if all_pnls else 0,
                "assets_tested": len(portfolio_results["asset_results"])
            }
        
        return portfolio_results
