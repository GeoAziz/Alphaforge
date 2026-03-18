"""
Signal Performance Tracker Service
Monitors real-world performance of generated signals for quality assessment and model improvement.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid

from database.db import Database

logger = logging.getLogger(__name__)


class SignalOutcome(str, Enum):
    """Possible outcomes for a signal."""
    WINNING_TRADE = "winning_trade"      # Closed with profit
    LOSING_TRADE = "losing_trade"        # Closed with loss
    BREAK_EVEN = "break_even"            # Closed at entry
    STOPPED_OUT = "stopped_out"          # Hit stop loss
    TAKE_PROFIT_HIT = "take_profit_hit"  # Hit take profit
    EXPIRED = "expired"                  # Signal expired without execution
    NEVER_EXECUTED = "never_executed"    # Signal generated but not traded


class SignalPerformanceTracker:
    """Tracks and analyzes performance of generated signals."""
    
    def __init__(self, db: Database):
        self.db = db
        
    async def record_signal_execution(
        self,
        signal_id: str,
        user_id: str,
        execution_price: float,
        quantity: float
    ) -> Dict[str, Any]:
        """Record that a signal was executed as a paper trade."""
        try:
            # Fetch current state
            response = self.db.supabase.table("signal_performance")\
                .select("*")\
                .eq("signal_id", signal_id)\
                .execute()
            
            if not response.data:
                logger.warning(f"⚠️ Signal performance record not found: {signal_id}")
                return {"success": False, "error": "Signal performance record not found"}
            
            current = response.data[0]
            new_exec_count = current.get("num_times_executed", 0) + 1
            
            # Update signal_performance table
            update_response = self.db.supabase.table("signal_performance")\
                .update({
                    "num_times_executed": new_exec_count,
                    "last_execution_at": datetime.utcnow().isoformat()
                })\
                .eq("signal_id", signal_id)\
                .execute()
            
            logger.info(f"✅ Recorded signal execution: {signal_id}")
            return {"success": True, "data": update_response.data[0] if update_response.data else None}
        
        except Exception as e:
            logger.error(f"❌ Failed to record signal execution: {e}")
            return {"success": False, "error": str(e)}
    
    async def record_signal_closure(
        self,
        signal_id: str,
        paper_trade_id: str,
        exit_price: float,
        entry_price: float,
        outcome: SignalOutcome,
        pnl: float,
        roi_pct: float
    ) -> Dict[str, Any]:
        """Record the closure of a trade linked to a signal."""
        try:
            # Fetch current performance
            response = self.db.supabase.table("signal_performance")\
                .select("*")\
                .eq("signal_id", signal_id)\
                .execute()
            
            if not response.data:
                logger.warning(f"⚠️ No performance record for signal: {signal_id}")
                return {"success": False, "error": "Performance record not found"}
            
            perf = response.data[0]
            already_closed = perf.get("num_times_closed", 0)
            executed_count = perf.get("num_times_executed", 0)
            current_total_pnl = float(perf.get("total_pnl", 0))
            current_win_count = perf.get("win_count", 0)
            current_loss_count = perf.get("loss_count", 0)
            
            # Determine if trade was winning or losing
            is_win = pnl > 0
            new_win_count = current_win_count + (1 if is_win else 0)
            new_loss_count = current_loss_count + (0 if is_win else 1)
            
            new_total_pnl = current_total_pnl + pnl
            new_total_closed = already_closed + 1
            new_win_rate = new_win_count / new_total_closed if new_total_closed > 0 else 0
            
            # Determine if this is a high-performing signal
            avg_roi_per_trade = new_total_pnl / executed_count if executed_count > 0 else 0
            is_high_performer = (new_win_rate >= 0.60) and (avg_roi_per_trade >= 0.10)
            
            # Update signal_performance
            updated = self.db.supabase.table("signal_performance")\
                .update({
                    "num_times_closed": new_total_closed,
                    "total_pnl": new_total_pnl,
                    "avg_pnl_per_execution": new_total_pnl / executed_count if executed_count > 0 else 0,
                    "win_count": new_win_count,
                    "loss_count": new_loss_count,
                    "win_rate": new_win_rate,
                    "total_roi_pct": new_total_pnl * 100,
                    "is_high_performer": is_high_performer,
                    "last_updated_at": datetime.utcnow().isoformat()
                })\
                .eq("signal_id", signal_id)\
                .execute()
            
            logger.info(f"✅ Updated signal performance: {signal_id} | Win Rate: {new_win_rate:.1%} | PnL: {new_total_pnl}")
            
            return {
                "success": True,
                "data": updated.data[0] if updated.data else None,
                "is_high_performer": is_high_performer,
                "win_rate": new_win_rate,
                "total_pnl": new_total_pnl
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to record signal closure: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_high_performing_signals(
        self,
        limit: int = 20,
        min_executions: int = 5
    ) -> List[Dict[str, Any]]:
        """Get highest-performing signals for display and model training."""
        try:
            response = self.db.supabase.table("signal_performance")\
                .select("*")\
                .eq("is_high_performer", True)\
                .gte("num_times_executed", min_executions)\
                .order("win_rate", desc=True)\
                .order("total_roi_pct", desc=True)\
                .limit(limit)\
                .execute()
            
            logger.info(f"✅ Fetched {len(response.data)} high-performing signals")
            return response.data if response.data else []
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch high-performing signals: {e}")
            return []
    
    async def calculate_signal_accuracy_score(
        self,
        signal_id: str
    ) -> float:
        """
        Calculate ML-based accuracy score for a signal (0-1 scale).
        
        Factors:
        - Win rate
        - ROI consistency
        - Sharpe ratio (risk-adjusted returns)
        - Number of observations
        """
        try:
            response = self.db.supabase.table("signal_performance")\
                .select("*")\
                .eq("signal_id", signal_id)\
                .execute()
            
            if not response.data:
                return 0.0
            
            perf = response.data[0]
            win_rate = float(perf.get("win_rate", 0))
            roi_pct = float(perf.get("total_roi_pct", 0)) / 100
            sharpe = float(perf.get("sharpe_ratio", 1))
            num_exec = perf.get("num_times_executed", 0)
            
            # Scoring weights
            win_rate_score = min(win_rate / 0.70, 1.0) * 0.40  # 40% weight, cap at 70% win rate
            roi_score = min(roi_pct / 0.20, 1.0) * 0.30  # 30% weight, cap at 20% ROI
            sharpe_score = min(sharpe / 1.5, 1.0) * 0.20  # 20% weight, cap at 1.5 Sharpe
            
            # Observation penalizer (more data = more confident)
            observation_multiplier = min(num_exec / 20, 1.0)  # 20 executions = maximum confidence
            
            accuracy_score = (win_rate_score + roi_score + sharpe_score) * observation_multiplier
            
            logger.info(f"📊 Signal {signal_id} accuracy score: {accuracy_score:.3f}")
            
            return accuracy_score
        
        except Exception as e:
            logger.error(f"❌ Failed to calculate accuracy score: {e}")
            return 0.0
    
    async def get_signal_performance_summary(self) -> Dict[str, Any]:
        """Get aggregate statistics on all signals for dashboard."""
        try:
            response = self.db.supabase.table("signal_performance")\
                .select("*")\
                .gt("num_times_closed", 0)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                return {"success": False, "error": "No performance data"}
            
            data = response.data
            total_signals = len(data)
            high_performers = sum(1 for s in data if s.get("is_high_performer", False))
            avg_win_rate = sum(s.get("win_rate", 0) for s in data) / total_signals if total_signals > 0 else 0
            avg_roi = sum(s.get("total_roi_pct", 0) for s in data) / total_signals if total_signals > 0 else 0
            total_pnl = sum(s.get("total_pnl", 0) for s in data)
            best_trade = max((s.get("best_trade_pnl", 0) for s in data), default=0)
            worst_trade = min((s.get("worst_trade_pnl", 0) for s in data), default=0)
            
            return {
                "success": True,
                "data": {
                    "total_signals": total_signals,
                    "high_performer_count": high_performers,
                    "avg_win_rate": avg_win_rate,
                    "avg_roi_pct": avg_roi,
                    "avg_executions": sum(s.get("num_times_executed", 0) for s in data) / total_signals if total_signals > 0 else 0,
                    "total_realized_pnl": total_pnl,
                    "best_single_trade": best_trade,
                    "worst_single_trade": worst_trade
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get performance summary: {e}")
            return {"success": False, "error": str(e)}
