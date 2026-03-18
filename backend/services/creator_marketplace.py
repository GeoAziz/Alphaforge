"""
Creator Marketplace Service - Manages strategy creators and subscriptions.

Handles:
- Creator profile creation and management
- Strategy publishing and verification
- User subscriptions to strategies
- Performance tracking and reputation scoring
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class CreatorMarketplaceService:
    """Manages creator profiles and strategy marketplace."""

    def __init__(self, db):
        self.db = db

    async def create_creator_profile(
        self,
        user_id: str,
        bio: str,
        initial_strategy_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Create a creator profile for a user."""
        try:
            # Check if creator already exists
            response = self.db.supabase.table("creator_profiles").select("*").eq("user_id", user_id).execute()

            if response.data:
                return {
                    "success": False,
                    "error": "Creator profile already exists for this user"
                }

            # Create new profile
            profile = {
                "user_id": user_id,
                "bio": bio,
                "verification_stage": "stage_1_submitted",
                "reputation_score": 50,  # Starting score
                "subscriber_count": 0,
                "total_aum": 0,
                "win_rate": 0,
                "created_at": datetime.utcnow().isoformat()
            }

            response = self.db.supabase.table("creator_profiles").insert(profile).execute()

            if response.data:
                creator_id = response.data[0]["id"]
                logger.info(f"✅ Creator profile created: {creator_id}")

                return {
                    "success": True,
                    "creator_id": creator_id,
                    "profile": response.data[0]
                }

        except Exception as e:
            logger.error(f"❌ Failed to create creator profile: {e}")

        return {"success": False, "error": "Failed to create creator profile"}

    async def get_creator_profile(self, creator_id: str) -> Dict[str, Any]:
        """Retrieve creator profile."""
        try:
            response = self.db.supabase.table("creator_profiles").select("*").eq("id", creator_id).execute()

            if response.data:
                profile = response.data[0]

                # Get subscriber list
                subs_response = self.db.supabase.table("strategy_subscriptions").select("user_id").eq("strategy_id", creator_id).execute()

                subscriber_ids = [s["user_id"] for s in subs_response.data or []]

                return {
                    "success": True,
                    "profile": profile,
                    "subscribers": len(subscriber_ids)
                }

            return {"success": False, "error": "Creator not found"}

        except Exception as e:
            logger.error(f"❌ Failed to get creator profile: {e}")
            return {"success": False, "error": str(e)}

    async def list_creators(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "reputation_score"
    ) -> Dict[str, Any]:
        """List all creators with their stats."""
        try:
            # Get creators ordered by reputation
            response = self.db.supabase.table("creator_profiles").select("*").eq("verification_stage", "stage_4_verified").order(sort_by, desc=True).range(offset, offset + limit).execute()

            creators = response.data or []

            # Enrich with subscriber counts
            for creator in creators:
                subs_response = self.db.supabase.table("strategy_subscriptions").select("count").eq("strategy_id", creator["id"]).execute()
                creator["subscriber_count"] = subs_response.data[0]["count"] if subs_response.data else 0

            return {
                "success": True,
                "creators": creators,
                "count": len(creators)
            }

        except Exception as e:
            logger.error(f"❌ Failed to list creators: {e}")
            return {"success": False, "error": str(e)}

    async def publish_strategy(
        self,
        creator_id: str,
        strategy_name: str,
        description: str,
        backtest_sharpe_ratio: float,
        pricing_tier: str = "basic"
    ) -> Dict[str, Any]:
        """Publish strategy to marketplace (enters 4-week validation gate)."""
        try:
            # Verify creator exists
            creator_response = self.db.supabase.table("creator_profiles").select("*").eq("id", creator_id).execute()

            if not creator_response.data:
                return {"success": False, "error": "Creator not found"}

            # Create strategy record
            strategy = {
                "creator_id": creator_id,
                "name": strategy_name,
                "description": description,
                "backtest_sharpe_ratio": backtest_sharpe_ratio,
                "pricing_tier": pricing_tier,
                "verification_stage": "stage_2_paper_trading",  # Enter 4-week gate
                "paper_trading_start_date": datetime.utcnow().isoformat(),
                "status": "in_evaluation",
                "subscriber_count": 0,
                "created_at": datetime.utcnow().isoformat()
            }

            response = self.db.supabase.table("creator_strategies").insert(strategy).execute()

            if response.data:
                strategy_id = response.data[0]["id"]
                logger.info(f"✅ Strategy published and entered 4-week gate: {strategy_id}")

                return {
                    "success": True,
                    "strategy_id": strategy_id,
                    "status": "in_evaluation",
                    "gate_duration_weeks": 4,
                    "required_sharpe_ratio": backtest_sharpe_ratio * 0.8  # 80% of backtest Sharpe
                }

            return {"success": False, "error": "Failed to publish strategy"}

        except Exception as e:
            logger.error(f"❌ Failed to publish strategy: {e}")
            return {"success": False, "error": str(e)}

    async def check_paper_trading_completion(self, strategy_id: str) -> Dict[str, Any]:
        """Check if strategy passed 4-week paper trading gate."""
        try:
            # Get strategy
            strategy_response = self.db.supabase.table("creator_strategies").select("*").eq("id", strategy_id).execute()

            if not strategy_response.data:
                return {"success": False, "error": "Strategy not found"}

            strategy = strategy_response.data[0]

            # Check if 4 weeks have passed
            if strategy.get("verification_stage") != "stage_2_paper_trading":
                return {
                    "success": True,
                    "passed": strategy.get("verification_stage") == "stage_4_verified",
                    "status": strategy.get("verification_stage")
                }

            # Get paper trading results
            paper_trades_response = self.db.supabase.table("strategy_paper_trades").select("*").eq("strategy_id", strategy_id).execute()

            paper_trades = paper_trades_response.data or []

            if not paper_trades:
                return {
                    "success": True,
                    "passed": False,
                    "reason": "No paper trades executed yet"
                }

            # Calculate paper trading Sharpe ratio
            returns = [float(t.get("pnl", 0)) for t in paper_trades]
            avg_return = sum(returns) / len(returns) if returns else 0
            std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 0
            paper_sharpe = avg_return / std_return if std_return != 0 else 0

            backtest_sharpe = strategy.get("backtest_sharpe_ratio", 1.0)
            required_sharpe = backtest_sharpe * 0.8  # 80% threshold

            passed = paper_sharpe >= required_sharpe

            if passed:
                # Update strategy status to verified
                self.db.supabase.table("creator_strategies").update({
                    "verification_stage": "stage_4_verified",
                    "status": "verified"
                }).eq("id", strategy_id).execute()

                logger.info(f"✅ Strategy passed paper trading gate: {strategy_id} (Sharpe: {paper_sharpe:.2f})")

            return {
                "success": True,
                "passed": passed,
                "paper_trading_sharpe": round(paper_sharpe, 4),
                "required_sharpe": round(required_sharpe, 4),
                "trades_count": len(paper_trades)
            }

        except Exception as e:
            logger.error(f"❌ Failed to check paper trading completion: {e}")
            return {"success": False, "error": str(e)}

    async def subscribe_to_strategy(
        self,
        user_id: str,
        strategy_id: str,
        allocation_pct: float
    ) -> Dict[str, Any]:
        """Subscribe user to a strategy."""
        try:
            # Verify strategy is verified
            strategy_response = self.db.supabase.table("creator_strategies").select("*").eq("id", strategy_id).execute()

            if not strategy_response.data:
                return {"success": False, "error": "Strategy not found"}

            strategy = strategy_response.data[0]

            if strategy.get("verification_stage") != "stage_4_verified":
                return {
                    "success": False,
                    "error": "Strategy not verified yet (still in 4-week evaluation)"
                }

            # Create subscription
            subscription = {
                "user_id": user_id,
                "strategy_id": strategy_id,
                "allocation_percentage": allocation_pct,
                "status": "active",
                "subscribed_at": datetime.utcnow().isoformat()
            }

            response = self.db.supabase.table("strategy_subscriptions").insert(subscription).execute()

            if response.data:
                logger.info(f"✅ User {user_id} subscribed to strategy {strategy_id}")

                return {
                    "success": True,
                    "subscription_id": response.data[0]["id"],
                    "allocation_percentage": allocation_pct
                }

            return {"success": False, "error": "Failed to create subscription"}

        except Exception as e:
            logger.error(f"❌ Failed to subscribe to strategy: {e}")
            return {"success": False, "error": str(e)}

    async def update_creator_reputation(
        self,
        creator_id: str,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update creator reputation score based on performance."""
        try:
            # Get current creator profile
            creator_response = self.db.supabase.table("creator_profiles").select("*").eq("id", creator_id).execute()

            if not creator_response.data:
                return {"success": False, "error": "Creator not found"}

            creator = creator_response.data[0]

            # Calculate new reputation: 50 (base) + win_rate×50 + sharpe_ratio×10
            win_rate = performance_data.get("win_rate", 0.5)  # 0-1
            sharpe_ratio = performance_data.get("sharpe_ratio", 1.0)  # normalized 0-10

            new_reputation = 50 + (win_rate * 50) + min(sharpe_ratio * 10, 20)  # Cap contribution at 20
            new_reputation = min(100, max(0, new_reputation))  # Clamp 0-100

            # Update profile
            self.db.supabase.table("creator_profiles").update({
                "reputation_score": new_reputation,
                "win_rate": win_rate,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", creator_id).execute()

            logger.info(f"✅ Creator reputation updated: {creator_id} (Score: {new_reputation:.1f})")

            return {
                "success": True,
                "new_reputation_score": round(new_reputation, 1),
                "factors": {
                    "base": 50,
                    "win_rate_contribution": round(win_rate * 50, 1),
                    "sharpe_contribution": round(min(sharpe_ratio * 10, 20), 1)
                }
            }

        except Exception as e:
            logger.error(f"❌ Failed to update creator reputation: {e}")
            return {"success": False, "error": str(e)}

    async def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get overall marketplace statistics."""
        try:
            # Count verified creators
            creators_response = self.db.supabase.table("creator_profiles").select("count", count="exact").eq("verification_stage", "stage_4_verified").execute()
            creator_count = creators_response.count or 0

            # Count verified strategies
            strategies_response = self.db.supabase.table("creator_strategies").select("count", count="exact").eq("verification_stage", "stage_4_verified").execute()
            strategy_count = strategies_response.count or 0

            # Count active subscriptions
            subscriptions_response = self.db.supabase.table("strategy_subscriptions").select("count", count="exact").eq("status", "active").execute()
            subscription_count = subscriptions_response.count or 0

            # Calculate total AUM
            aum_response = self.db.supabase.table("strategy_subscriptions").select("allocation_percentage").execute()
            total_aum = sum(float(s.get("allocation_percentage", 0)) for s in aum_response.data or [])

            return {
                "success": True,
                "stats": {
                    "verified_creators": creator_count,
                    "verified_strategies": strategy_count,
                    "active_subscriptions": subscription_count,
                    "total_aum": round(total_aum, 2),
                    "average_subscription_size": round(total_aum / subscription_count if subscription_count > 0 else 0, 2)
                }
            }

        except Exception as e:
            logger.error(f"❌ Failed to get marketplace stats: {e}")
            return {"success": False, "error": str(e)}
