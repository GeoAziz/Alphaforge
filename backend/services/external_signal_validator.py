"""
External Signal Performance Validator
Tracks and validates performance of external trading signals (TradingView, webhooks, etc).
Helps users identify which external sources are most reliable.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

from database.db import Database

logger = logging.getLogger(__name__)


class ExternalSourceType(str, Enum):
    """Types of external signal sources."""
    TRADINGVIEW = "tradingview"
    PINE_SCRIPT = "pine_script"
    WEBHOOK = "webhook"
    TELEGRAM = "telegram"
    OTHER = "other"


class ReliabilityLevel(str, Enum):
    """Reliability assessment of external source."""
    HIGHLY_TRUSTED = "HIGHLY_TRUSTED"     # >65% win rate, >5 occurrences
    RELIABLE = "RELIABLE"                 # 55-65% win rate, >3 occurrences
    MARGINAL = "MARGINAL"                 # 45-55% win rate, any occurrences
    UNRELIABLE = "UNRELIABLE"             # <45% win rate
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"  # <3 executions


class ExternalSignalPerformanceValidator:
    """Validates and tracks performance of external signal sources."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def track_external_signal_execution(
        self,
        user_id: str,
        external_signal_id: str,
        source: ExternalSourceType,
        asset: str,
        side: str,
        signal_received_at: datetime,
        execution_price: float,
        executed: bool = True
    ) -> Dict[str, Any]:
        """Record execution of an external signal."""
        try:
            # Update external_signal_performance table
            period_date = datetime.utcnow().date()
            
            # Try to get existing record for this user/source/period
            result = self.db.supabase.table("external_signal_performance")\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("external_source", source.value)\
                .eq("period_start_date", str(period_date))\
                .eq("period_end_date", str(period_date))\
                .execute()
            
            if result.data and len(result.data) > 0:
                # Update existing record
                record_id = result.data[0]['id']
                
                update_data = {
                    "total_signals_received": self.db.supabase.table("external_signal_performance").select("total_signals_received").eq("id", record_id).execute().data[0]["total_signals_received"] + 1 if result.data else 1,
                    "total_signals_executed": self.db.supabase.table("external_signal_performance").select("total_signals_executed").eq("id", record_id).execute().data[0]["total_signals_executed"] + (1 if executed else 0) if result.data else 1 if executed else 0,
                    "signals_ignored": self.db.supabase.table("external_signal_performance").select("signals_ignored").eq("id", record_id).execute().data[0]["signals_ignored"] + (1 if not executed else 0) if result.data else 1 if not executed else 0,
                    "last_signal_at": signal_received_at.isoformat(),
                    "last_updated_at": datetime.utcnow().isoformat()
                }
                
                updated = self.db.supabase.table("external_signal_performance")\
                    .update(update_data)\
                    .eq("id", record_id)\
                    .execute()
                
                logger.info(f"✅ Updated external signal tracking for {user_id} / {source}")
                return {"success": True, "data": updated.data[0] if updated.data else None}
            
            else:
                # Create new record
                insert_data = {
                    "user_id": user_id,
                    "external_source": source.value,
                    "period_start_date": str(period_date),
                    "period_end_date": str(period_date),
                    "total_signals_received": 1,
                    "total_signals_executed": 1 if executed else 0,
                    "signals_ignored": 0 if executed else 1,
                    "last_signal_at": signal_received_at.isoformat()
                }
                
                inserted = self.db.supabase.table("external_signal_performance")\
                    .insert(insert_data)\
                    .execute()
                
                logger.info(f"✅ Created new external signal tracking for {user_id} / {source}")
                return {"success": True, "data": inserted.data[0] if inserted.data else None}
        
        except Exception as e:
            logger.error(f"❌ Failed to track external signal execution: {e}")
            return {"success": False, "error": str(e)}
    
    async def record_external_signal_closure(
        self,
        user_id: str,
        external_signal_id: str,
        source: ExternalSourceType,
        exit_price: float,
        entry_price: float,
        pnl: float,
        roi_pct: float
    ) -> Dict[str, Any]:
        """Record closure and result of an external signal trade."""
        try:
            period_date = datetime.utcnow().date()
            is_win = pnl > 0
            
            # Get current stats
            result = self.db.supabase.table("external_signal_performance")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("external_source", source.value)\
                .eq("period_start_date", str(period_date))\
                .order("period_end_date", desc=True)\
                .limit(1)\
                .execute()
            
            result = await self.db.execute(select_query, (user_id, source.value, period_date))
            
            if result:
                perf = result[0]
                exec_count = perf.get("total_signals_executed", 0)
                
                # Calculate new stats
                new_win_count = perf.get("executed_win_count", 0) + (1 if is_win else 0)
                new_loss_count = perf.get("executed_loss_count", 0) + (1 if not is_win else 0)
                new_total_pnl = float(perf.get("total_pnl", 0)) + pnl
                new_win_rate = new_win_count / (exec_count + 1) if exec_count >= 0 else 0
                
                # Calculate reliability score
                reliability_score = self._calculate_reliability_score(
                    new_win_rate,
                    exec_count,
                    new_total_pnl,
                    pnl
                )
                
                recommendation = self._get_reliability_recommendation(reliability_score, exec_count)
                
                # Update record
                update_query = """
                UPDATE external_signal_performance
                SET 
                    executed_win_count = %s,
                    executed_loss_count = %s,
                    executed_win_rate = %s,
                    total_pnl = %s,
                    total_roi_pct = %s,
                    avg_roi_per_trade = %s,
                    reliability_score = %s,
                    recommendation = %s,
                    last_updated_at = NOW()
                WHERE user_id = %s
                AND external_source = %s
                AND period_start_date = %s
                RETURNING *
                """
                
                updated = await self.db.execute(
                    update_query,
                    (
                        new_win_count,
                        new_loss_count,
                        new_win_rate,
                        new_total_pnl,
                        new_total_pnl * 100,  # percentage
                        (new_total_pnl / (exec_count + 1)) * 100 if exec_count >= 0 else 0,
                        reliability_score,
                        recommendation,
                        user_id,
                        source.value,
                        period_date
                    )
                )
                
                logger.info(f"✅ Updated external signal closure: {source} win_rate={new_win_rate:.1%}")
                
                return {
                    "success": True,
                    "data": updated[0] if updated else None,
                    "reliability_level": recommendation,
                    "win_rate": new_win_rate
                }
        
        except Exception as e:
            logger.error(f"❌ Failed to record external signal closure: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_reliability_score(
        self,
        win_rate: float,
        execution_count: int,
        total_pnl: float,
        latest_pnl: float
    ) -> float:
        """
        Calculate reliability score (0-1) for external signal source.
        
        Factors:
        - Win rate (40%)
        - Consistency (30%) - measured by ROI stability
        - Profitability (20%) - total PnL
        - Sample size (10%) - more executions = more confident
        """
        
        # Win rate component (40%)
        win_rate_score = min(win_rate / 0.65, 1.0) * 0.40
        
        # Execution count component (10%) - more data = more reliable
        execution_multiplier = min(execution_count / 50, 1.0) * 0.10
        
        # Profitability component (20%)
        profit_score = (1.0 if total_pnl > 0 else 0.0) * 0.20
        
        # Consistency component (30%) - TODO: calculate std deviation of PnL
        consistency_score = 0.30
        
        total_score = win_rate_score + execution_multiplier + profit_score + consistency_score
        
        return min(total_score, 1.0)
    
    def _get_reliability_recommendation(
        self,
        reliability_score: float,
        execution_count: int
    ) -> str:
        """Determine reliability recommendation based on score and sample size."""
        
        if execution_count < 3:
            return ReliabilityLevel.INSUFFICIENT_DATA.value
        
        if reliability_score >= 0.70:
            return ReliabilityLevel.HIGHLY_TRUSTED.value
        elif reliability_score >= 0.60:
            return ReliabilityLevel.RELIABLE.value
        elif reliability_score >= 0.50:
            return ReliabilityLevel.MARGINAL.value
        else:
            return ReliabilityLevel.UNRELIABLE.value
    
    async def get_source_reputation(
        self,
        user_id: str,
        source: ExternalSourceType,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get reputation metrics for external signal source."""
        try:
            query = """
            SELECT 
                external_source,
                executed_win_rate,
                total_pnl,
                total_roi_pct,
                total_signals_received,
                total_signals_executed,
                reliability_score,
                recommendation,
                last_signal_at
            FROM external_signal_performance
            WHERE user_id = %s
            AND external_source = %s
            AND period_end_date >= NOW() - INTERVAL '%d days'
            ORDER BY period_end_date DESC
            LIMIT 1
            """
            
            result = await self.db.execute(
                query,
                (user_id, source.value, days)
            )
            
            if result:
                logger.info(f"📊 Retrieved reputation for {source}: {result[0]['recommendation']}")
                return {"success": True, "data": result[0]}
            else:
                logger.warning(f"⚠️ No reputation data found for {source}")
                return {"success": False, "error": "No data for this period"}
        
        except Exception as e:
            logger.error(f"❌ Failed to get source reputation: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_all_source_rankings(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get all external sources ranked by reliability."""
        try:
            # Get all sources with active performance data (not filtering by user_id to avoid UUID issues in dev)
            response = self.db.supabase.table("external_signal_performance")\
                .select("*")\
                .gt("total_signals_executed", 0)\
                .order("reliability_score", desc=True)\
                .order("total_signals_executed", desc=True)\
                .limit(50)\
                .execute()
            
            results = response.data if response.data else []
            logger.info(f"✅ Retrieved {len(results)} active source rankings")
            return results
        
        except Exception as e:
            logger.error(f"❌ Failed to get source rankings: {e}")
            return []
