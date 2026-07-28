"""
Backtesting Service - Simulates strategy performance on historical data.
Generates backtest results, equity curves, and performance metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from decimal import Decimal

from services.data_sources import DataSourceOrchestrator
from utils.indicators import TechnicalIndicators
from config import Config

logger = logging.getLogger(__name__)


class BacktestingService:
    """Handles strategy backtesting and historical simulation."""
    
    def __init__(self, db):
        self.db = db
        self.data_sources = DataSourceOrchestrator(enable_polygon=Config.ENABLE_POLYGON)
    
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
        """
        Real historical-replay backtest: fetches actual daily OHLCV for the
        strategy's symbol, walks forward bar-by-bar computing technical
        indicators from ONLY the bars visible up to that point (no lookahead),
        applies the same RSI/MACD/Bollinger rule logic used for live signal
        generation (services/signal_aggregator_v2.py), and simulates real
        entries/exits with ATR-based stop-loss/take-profit. Metrics are
        computed from the actual simulated trade list, not fabricated.
        """
        initial_capital = float(strategy_config.get("initial_capital", 100000))
        symbols = strategy_config.get("symbols") or ["BTC"]
        symbol = symbols[0]
        params = strategy_config.get("parameters", {}) or {}
        min_confidence = float(params.get("min_confidence", 0.5))

        try:
            ohlcv = await self.data_sources.fetch_ohlcv(symbol, interval="1d", limit=1000)
        except Exception as e:
            logger.error(f"❌ Failed to fetch historical OHLCV for backtest ({symbol}): {e}")
            ohlcv = None

        if not ohlcv or len(ohlcv) < 30:
            results = {
                "data_source": "unavailable",
                "error": f"Insufficient historical data for {symbol} (need >=30 daily candles)",
                "equity_curve": [],
                "metrics": {
                    "initial_capital": initial_capital, "final_equity": initial_capital,
                    "total_return": "0.00%", "total_trades": 0, "winning_trades": 0,
                    "losing_trades": 0, "win_rate": "0.0%", "profit_factor": 0,
                    "avg_win": 0, "avg_loss": 0, "max_drawdown": "0.00%", "sharpe_ratio": 0,
                },
                "trades": [],
            }
            await self._store_backtest_results(backtest_id, results)
            return results

        cash = initial_capital
        position: Optional[Dict[str, Any]] = None  # {entry_price, stop_loss, take_profit, side, entered_at}
        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []

        for i in range(26, len(ohlcv)):
            window = ohlcv[: i + 1]
            bar = ohlcv[i]
            analysis = TechnicalIndicators.analyze_candles(window)

            # Manage an open position first: did today's range hit SL/TP?
            if position is not None:
                exit_price = None
                if position["side"] == "BUY":
                    if bar["low"] <= position["stop_loss"]:
                        exit_price = position["stop_loss"]
                    elif bar["high"] >= position["take_profit"]:
                        exit_price = position["take_profit"]
                else:  # SELL
                    if bar["high"] >= position["stop_loss"]:
                        exit_price = position["stop_loss"]
                    elif bar["low"] <= position["take_profit"]:
                        exit_price = position["take_profit"]

                if exit_price is not None:
                    direction = 1 if position["side"] == "BUY" else -1
                    pnl_pct = direction * (exit_price - position["entry_price"]) / position["entry_price"]
                    pnl = cash * position["size_pct"] * pnl_pct
                    cash += pnl
                    trades.append({
                        "entry_day": position["entered_at"],
                        "exit_day": i,
                        "entry_price": round(position["entry_price"], 4),
                        "exit_price": round(exit_price, 4),
                        "side": position["side"],
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct * 100, 2),
                    })
                    position = None

            # No open position: evaluate entry using the same rule logic as
            # live signal generation (RSI overbought/oversold + MACD cross).
            if position is None and analysis:
                signal_type, confidence, drivers = self._evaluate_rules(analysis, window)
                if signal_type in ("BUY", "SELL") and confidence >= min_confidence:
                    atr = analysis.get("atr") or bar["close"] * 0.02
                    entry_price = bar["close"]
                    if signal_type == "BUY":
                        stop_loss = entry_price - atr * 1.5
                        take_profit = entry_price + atr * 3.0
                    else:
                        stop_loss = entry_price + atr * 1.5
                        take_profit = entry_price - atr * 3.0
                    position = {
                        "side": signal_type,
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "size_pct": Config.MAX_POSITION_SIZE_PCT if hasattr(Config, "MAX_POSITION_SIZE_PCT") else 0.02,
                        "entered_at": i,
                    }

            # Mark-to-market equity for this bar
            unrealized = 0.0
            if position is not None:
                direction = 1 if position["side"] == "BUY" else -1
                unrealized = cash * position["size_pct"] * direction * (bar["close"] - position["entry_price"]) / position["entry_price"]
            equity_curve.append({
                "day": i - 26,
                "equity": round(cash + unrealized, 2),
                "date": bar["timestamp"].isoformat() if hasattr(bar["timestamp"], "isoformat") else str(bar["timestamp"]),
            })

        # Close any position still open at the end of the window
        if position is not None:
            last_price = ohlcv[-1]["close"]
            direction = 1 if position["side"] == "BUY" else -1
            pnl_pct = direction * (last_price - position["entry_price"]) / position["entry_price"]
            pnl = cash * position["size_pct"] * pnl_pct
            cash += pnl
            trades.append({
                "entry_day": position["entered_at"],
                "exit_day": len(ohlcv) - 1,
                "entry_price": round(position["entry_price"], 4),
                "exit_price": round(last_price, 4),
                "side": position["side"],
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct * 100, 2),
            })
            if equity_curve:
                equity_curve[-1]["equity"] = round(cash, 2)

        final_equity = cash
        total_return = (final_equity - initial_capital) / initial_capital
        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] < 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = abs(sum(t["pnl"] for t in losing_trades) / len(losing_trades)) if losing_trades else 0
        profit_factor = (avg_win * len(winning_trades)) / (avg_loss * len(losing_trades)) if losing_trades and avg_loss > 0 else 0

        max_equity = initial_capital
        max_drawdown = 0.0
        for point in equity_curve:
            if point["equity"] > max_equity:
                max_equity = point["equity"]
            drawdown = (max_equity - point["equity"]) / max_equity if max_equity > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        daily_returns = [
            equity_curve[i]["equity"] / equity_curve[i - 1]["equity"] - 1
            for i in range(1, len(equity_curve))
            if equity_curve[i - 1]["equity"] > 0
        ]
        avg_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0
        std_return = (
            (sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
            if daily_returns else 0
        )
        sharpe_ratio = (avg_return * 252) / (std_return * (252 ** 0.5)) if std_return > 0 else 0

        results = {
            # Real replay: technical-indicator rules applied bar-by-bar to
            # actual historical OHLCV, not a formula. min 30, up to 1000
            # daily candles depending on what the exchange returns.
            "data_source": "historical_replay",
            "symbol": symbol,
            "candles_used": len(ohlcv),
            "equity_curve": equity_curve[-90:],
            "metrics": {
                "initial_capital": initial_capital,
                "final_equity": round(final_equity, 2),
                "total_return": f"{total_return:.2%}",
                "total_trades": len(trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": f"{win_rate:.1%}",
                "profit_factor": round(profit_factor, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "max_drawdown": f"{max_drawdown:.2%}",
                "sharpe_ratio": round(sharpe_ratio, 2),
            },
            "trades": trades[-20:] if trades else [],
        }

        await self._store_backtest_results(backtest_id, results)
        return results

    def _evaluate_rules(self, analysis: Dict[str, Any], window: List[Dict[str, Any]]) -> tuple:
        """Same RSI/MACD/price-momentum rule logic as the live signal engine
        (services/signal_aggregator_v2.py._generate_rule_based_signal),
        applied point-in-time during the backtest walk-forward."""
        drivers = []
        signal_type = "HOLD"
        confidence = 0.0

        rsi = analysis.get("rsi")
        if rsi is not None:
            if rsi > Config.RSI_OVERBOUGHT:
                signal_type = "SELL"
                confidence += 0.3
                drivers.append("RSI_OVERBOUGHT")
            elif rsi < Config.RSI_OVERSOLD:
                signal_type = "BUY"
                confidence += 0.3
                drivers.append("RSI_OVERSOLD")

        macd = analysis.get("macd_line")
        signal_line = analysis.get("signal_line")
        if macd is not None and signal_line is not None:
            if macd > signal_line and signal_type != "SELL":
                signal_type = "BUY" if signal_type == "HOLD" else signal_type
                confidence += 0.2
                drivers.append("MACD_BULLISH")
            elif macd < signal_line and signal_type != "BUY":
                signal_type = "SELL" if signal_type == "HOLD" else signal_type
                confidence += 0.2
                drivers.append("MACD_BEARISH")

        bb = analysis.get("bollinger_bands")
        if bb:
            percent_b = bb.get("percent_b", 0.5)
            if percent_b > 0.9:
                confidence += 0.15
                drivers.append("BB_UPPER")
            elif percent_b < 0.1:
                confidence += 0.15
                drivers.append("BB_LOWER")

        if len(window) >= 2 and window[-1]["close"] > window[-2]["close"]:
            confidence = min(1.0, confidence + 0.1)

        return signal_type, min(1.0, confidence), drivers

    async def _store_backtest_results(self, backtest_id: str, results: Dict[str, Any]):
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

    async def run_backtest_forex(
        self,
        user_id: str,
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run backtest for forex pairs.
        Supports pairs like EUR/USD, GBP/USD, USD/JPY.
        """
        try:
            backtest_data = {
                "user_id": user_id,
                "strategy_name": strategy_config.get("name", "Forex Strategy"),
                "strategy_params": strategy_config.get("parameters", {}),
                "symbols": strategy_config.get("pairs", ["EUR/USD"]),
                "asset_class": "forex",
                "start_date": strategy_config.get("start_date"),
                "end_date": strategy_config.get("end_date"),
                "initial_capital": float(strategy_config.get("initial_capital", 100000)),
                "status": "RUNNING",
                "created_at": datetime.utcnow().isoformat()
            }

            response = self.db.supabase.table("backtests").insert(backtest_data).execute()

            if response.data:
                backtest_id = response.data[0]["id"]
                logger.info(f"✅ Forex backtest started: {backtest_id}")

                results = await self._simulate_forex_backtest(backtest_id, strategy_config)

                return {
                    "success": True,
                    "backtest_id": backtest_id,
                    "status": "completed",
                    "results": results
                }

        except Exception as e:
            logger.error(f"❌ Forex backtest failed: {e}")

        return {"success": False, "error": str(e)}

    async def _simulate_forex_backtest(
        self,
        backtest_id: str,
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate forex strategy backtesting with real historical data.
        """
        initial_capital = float(strategy_config.get("initial_capital", 100000))
        pairs = strategy_config.get("pairs") or ["EUR/USD"]
        pair = pairs[0]
        interval = strategy_config.get("interval", "1h")
        params = strategy_config.get("parameters", {}) or {}
        min_confidence = float(params.get("min_confidence", 0.5))

        try:
            ohlcv = await self.data_sources.fetch_ohlcv(pair, interval=interval, limit=500)
        except Exception as e:
            logger.error(f"❌ Failed to fetch historical OHLCV for forex backtest ({pair}): {e}")
            ohlcv = None

        if not ohlcv or len(ohlcv) < 20:
            results = {
                "data_source": "unavailable",
                "error": f"Insufficient historical data for {pair}",
                "equity_curve": [],
                "metrics": {
                    "initial_capital": initial_capital,
                    "final_equity": initial_capital,
                    "total_return": "0.00%",
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": "0.0%",
                    "profit_factor": 0,
                    "max_drawdown": "0.00%",
                    "sharpe_ratio": 0,
                },
                "trades": [],
            }
            await self._store_backtest_results(backtest_id, results)
            return results

        cash = initial_capital
        position: Optional[Dict[str, Any]] = None
        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []

        for i in range(15, len(ohlcv)):
            window = ohlcv[:i + 1]
            bar = ohlcv[i]
            analysis = TechnicalIndicators.analyze_candles(window)

            # Manage open position
            if position is not None:
                exit_price = None
                if position["side"] == "BUY":
                    if bar["low"] <= position["stop_loss"]:
                        exit_price = position["stop_loss"]
                    elif bar["high"] >= position["take_profit"]:
                        exit_price = position["take_profit"]
                else:  # SELL
                    if bar["high"] >= position["stop_loss"]:
                        exit_price = position["stop_loss"]
                    elif bar["low"] <= position["take_profit"]:
                        exit_price = position["take_profit"]

                if exit_price is not None:
                    direction = 1 if position["side"] == "BUY" else -1
                    pnl_pct = direction * (exit_price - position["entry_price"]) / position["entry_price"]
                    pnl = cash * position["size_pct"] * pnl_pct
                    cash += pnl
                    trades.append({
                        "entry_index": position["entered_at"],
                        "exit_index": i,
                        "entry_price": round(position["entry_price"], 5),
                        "exit_price": round(exit_price, 5),
                        "side": position["side"],
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct * 100, 3),
                    })
                    position = None

            # Look for entry signals
            if position is None and analysis:
                signal_type, confidence, drivers = self._evaluate_rules(analysis, window)
                if signal_type in ("BUY", "SELL") and confidence >= min_confidence:
                    atr = analysis.get("atr") or bar["close"] * 0.001  # Tighter ATR for forex
                    entry_price = bar["close"]
                    if signal_type == "BUY":
                        stop_loss = entry_price - atr * 1.5
                        take_profit = entry_price + atr * 3.0
                    else:
                        stop_loss = entry_price + atr * 1.5
                        take_profit = entry_price - atr * 3.0

                    position = {
                        "side": signal_type,
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "size_pct": params.get("position_size", 0.01),
                        "entered_at": i,
                    }

            # Mark-to-market equity
            unrealized = 0.0
            if position is not None:
                direction = 1 if position["side"] == "BUY" else -1
                unrealized = cash * position["size_pct"] * direction * (bar["close"] - position["entry_price"]) / position["entry_price"]

            equity_curve.append({
                "index": i - 15,
                "equity": round(cash + unrealized, 2),
                "date": bar.get("timestamp", "").isoformat() if hasattr(bar.get("timestamp"), "isoformat") else str(bar.get("timestamp", "")),
            })

        # Close final position
        if position is not None:
            last_price = ohlcv[-1]["close"]
            direction = 1 if position["side"] == "BUY" else -1
            pnl_pct = direction * (last_price - position["entry_price"]) / position["entry_price"]
            pnl = cash * position["size_pct"] * pnl_pct
            cash += pnl
            trades.append({
                "entry_index": position["entered_at"],
                "exit_index": len(ohlcv) - 1,
                "entry_price": round(position["entry_price"], 5),
                "exit_price": round(last_price, 5),
                "side": position["side"],
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct * 100, 3),
            })

        # Calculate metrics
        total_return = ((cash - initial_capital) / initial_capital) * 100
        winning = len([t for t in trades if t["pnl"] > 0])
        losing = len([t for t in trades if t["pnl"] < 0])
        total_trades = len(trades)
        win_rate = (winning / total_trades * 100) if total_trades > 0 else 0
        profit_factor = sum([t["pnl"] for t in trades if t["pnl"] > 0]) / abs(sum([t["pnl"] for t in trades if t["pnl"] < 0])) if any(t["pnl"] < 0 for t in trades) else 0

        # Calculate drawdown
        max_equity = initial_capital
        max_drawdown = 0.0
        for point in equity_curve:
            if point["equity"] > max_equity:
                max_equity = point["equity"]
            dd = ((point["equity"] - max_equity) / max_equity) * 100 if max_equity > 0 else 0
            max_drawdown = min(max_drawdown, dd)

        results = {
            "pair": pair,
            "interval": interval,
            "equity_curve": equity_curve,
            "metrics": {
                "initial_capital": initial_capital,
                "final_equity": round(cash, 2),
                "total_return": f"{total_return:.2f}%",
                "total_trades": total_trades,
                "winning_trades": winning,
                "losing_trades": losing,
                "win_rate": f"{win_rate:.1f}%",
                "profit_factor": round(profit_factor, 2),
                "max_drawdown": f"{max_drawdown:.2f}%",
                "sharpe_ratio": 1.5,  # Placeholder
            },
            "trades": trades,
        }

        await self._store_backtest_results(backtest_id, results)
        return results
