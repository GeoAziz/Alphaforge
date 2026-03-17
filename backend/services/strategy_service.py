"""
Strategy Service - Manages user strategies, marketplace, and strategy subscriptions.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)


class StrategyService:
    """Manages trading strategies and marketplace."""
    
    def __init__(self, db):
        self.db = db
    
    async def get_user_strategies(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get all strategies created by a user."""
        try:
            response = self.db.supabase.table("creator_strategies")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            strategies = response.data or []
            logger.info(f"✅ Fetched {len(strategies)} strategies for {user_id}")
            
            return {
                "success": True,
                "strategies": strategies,
                "count": len(strategies)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch user strategies: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_marketplace_strategies(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get approved strategies available on marketplace."""
        try:
            response = self.db.supabase.table("creator_strategies")\
                .select("*")\
                .eq("status", "APPROVED")\
                .order("popularity", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            strategies = response.data or []
            
            # Enhance with creator info
            enhanced_strategies = []
            for strategy in strategies:
                creator_response = self.db.supabase.table("users")\
                    .select("display_name, institution_name")\
                    .eq("id", strategy.get("user_id"))\
                    .execute()
                
                creator = creator_response.data[0] if creator_response.data else {}
                
                enhanced_strategies.append({
                    **strategy,
                    "creator_name": creator.get("display_name"),
                    "creator_institution": creator.get("institution_name")
                })
            
            logger.info(f"✅ Fetched {len(strategies)} marketplace strategies")
            
            return {
                "success": True,
                "strategies": enhanced_strategies,
                "count": len(enhanced_strategies)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch marketplace strategies: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_strategy_performance(
        self,
        strategy_id: str
    ) -> Dict[str, Any]:
        """Get performance metrics for a strategy."""
        try:
            # Get strategy
            strategy_response = self.db.supabase.table("creator_strategies")\
                .select("*")\
                .eq("id", strategy_id)\
                .execute()
            
            if not strategy_response.data:
                return {"success": False, "error": "Strategy not found"}
            
            strategy = strategy_response.data[0]
            
            # Get trades executed on this strategy
            trades_response = self.db.supabase.table("paper_trades")\
                .select("*")\
                .eq("strategy_id", strategy_id)\
                .execute()
            
            trades = trades_response.data or []
            closed_trades = [t for t in trades if t.get("status") == "CLOSED"]
            
            if not closed_trades:
                # Return backtest results if available
                backtest_results = strategy.get("backtest_results", {})
                return {
                    "success": True,
                    "strategy_id": strategy_id,
                    "metrics": backtest_results,
                    "source": "backtest"
                }
            
            # Calculate real trading metrics
            winning_trades = [t for t in closed_trades if t.get("pnl", 0) > 0]
            losing_trades = [t for t in closed_trades if t.get("pnl", 0) < 0]
            
            win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0
            total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
            avg_pnl = total_pnl / len(closed_trades) if closed_trades else 0
            
            metrics = {
                "total_trades": len(trades),
                "closed_trades": len(closed_trades),
                "win_rate": f"{win_rate:.1%}",
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(avg_pnl, 2),
                "largest_win": max([t.get("pnl", 0) for t in winning_trades], default=0),
                "largest_loss": min([t.get("pnl", 0) for t in losing_trades], default=0)
            }
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "metrics": metrics,
                "source": "live_trades"
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get strategy performance: {e}")
            return {"success": False, "error": str(e)}
    
    async def subscribe_to_strategy(
        self,
        user_id: str,
        strategy_id: str,
        allocation_pct: float = 10.0
    ) -> Dict[str, Any]:
        """Subscribe user to a marketplace strategy."""
        try:
            # Get strategy
            strategy_response = self.db.supabase.table("creator_strategies")\
                .select("*")\
                .eq("id", strategy_id)\
                .execute()
            
            if not strategy_response.data:
                return {"success": False, "error": "Strategy not found"}
            
            # Create subscription
            subscription_data = {
                "user_id": user_id,
                "strategy_id": strategy_id,
                "allocation_pct": allocation_pct,
                "status": "ACTIVE",
                "subscribed_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("strategy_subscriptions").insert(subscription_data).execute()
            
            if response.data:
                logger.info(f"✅ User {user_id} subscribed to strategy {strategy_id}")
                return {"success": True, "subscription_id": response.data[0]["id"]}
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to strategy: {e}")
        
        return {"success": False, "error": str(e)}
    
    async def start_paper_trade_strategy(
        self,
        user_id: str,
        strategy_id: str,
        capital: float = 10000.0
    ) -> Dict[str, Any]:
        """Start paper trading a strategy."""
        try:
            # Get strategy
            strategy_response = self.db.supabase.table("creator_strategies")\
                .select("*")\
                .eq("id", strategy_id)\
                .execute()
            
            if not strategy_response.data:
                return {"success": False, "error": "Strategy not found"}
            
            strategy = strategy_response.data[0]
            
            # Create paper trading session
            session_data = {
                "user_id": user_id,
                "strategy_id": strategy_id,
                "initial_capital": capital,
                "current_capital": capital,
                "status": "RUNNING",
                "started_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("strategy_paper_trades").insert(session_data).execute()
            
            if response.data:
                session_id = response.data[0]["id"]
                logger.info(f"✅ Paper trading started for strategy {strategy_id}")
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "strategy_name": strategy.get("name"),
                    "initial_capital": capital
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to start paper trading: {e}")
        
        return {"success": False, "error": str(e)}
    
    async def get_user_subscriptions(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get all active subscriptions for a user."""
        try:
            response = self.db.supabase.table("strategy_subscriptions")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "ACTIVE")\
                .execute()
            
            subscriptions = response.data or []
            
            # Enrich with strategy info
            enriched = []
            for sub in subscriptions:
                strategy_response = self.db.supabase.table("creator_strategies")\
                    .select("name, creator_id, performance")\
                    .eq("id", sub.get("strategy_id"))\
                    .execute()
                
                if strategy_response.data:
                    enriched.append({
                        **sub,
                        "strategy_name": strategy_response.data[0].get("name")
                    })
            
            return {
                "success": True,
                "subscriptions": enriched,
                "count": len(enriched)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get subscriptions: {e}")
            return {"success": False, "error": str(e)}
