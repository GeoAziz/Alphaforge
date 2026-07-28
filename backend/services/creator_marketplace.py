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

    # ====================================================================
    # §12 MARKETPLACE GOVERNANCE: Auto-Delisting, Payouts, Appeals
    # ====================================================================

    async def check_auto_delisting(self) -> Dict[str, Any]:
        """
        §12: Automatic delisting for underperforming strategies.
        Flags and delists if Sharpe < 50% of backtest for 2 months.
        """
        try:
            strategies_response = (
                self.db.supabase.table("creator_strategies")
                .select("*")
                .eq("verification_stage", "stage_4_verified")
                .execute()
            )
            strategies = strategies_response.data or []
            delisted = []
            warned = []

            for strategy in strategies:
                strategy_id = strategy["id"]
                backtest_sharpe = float(strategy.get("backtest_sharpe_ratio", 1.0))
                current_live_sharpe = float(strategy.get("current_live_sharpe", backtest_sharpe))
                months_below = int(strategy.get("months_below_60_pct", 0))

                threshold = backtest_sharpe * 0.5  # 50% of backtest baseline

                if current_live_sharpe < threshold:
                    months_below += 1
                    self.db.supabase.table("creator_strategies").update({
                        "months_below_60_pct": months_below,
                        "current_live_sharpe": current_live_sharpe,
                        "current_live_sharpe_last_updated": datetime.utcnow().isoformat(),
                    }).eq("id", strategy_id).execute()

                    if months_below >= 2:
                        # Auto-delist
                        self.db.supabase.table("creator_strategies").update({
                            "verification_stage": "stage_5_delisted",
                            "status": "delisted",
                        }).eq("id", strategy_id).execute()

                        # Cancel active subscriptions
                        self.db.supabase.table("strategy_subscriptions").update({
                            "status": "cancelled",
                        }).eq("strategy_id", strategy_id).eq("status", "active").execute()

                        delisted.append({
                            "strategy_id": strategy_id,
                            "name": strategy.get("name"),
                            "current_sharpe": round(current_live_sharpe, 4),
                            "backtest_sharpe": round(backtest_sharpe, 4),
                            "months_below_threshold": months_below,
                        })
                        logger.warning(f"⚠️ Strategy auto-delisted: {strategy_id} ({strategy.get('name')})")
                    else:
                        warned.append({
                            "strategy_id": strategy_id,
                            "name": strategy.get("name"),
                            "months_below_threshold": months_below,
                            "current_sharpe": round(current_live_sharpe, 4),
                        })
                else:
                    # Recovery: reset counter
                    if months_below > 0:
                        self.db.supabase.table("creator_strategies").update({
                            "months_below_60_pct": 0,
                        }).eq("id", strategy_id).execute()

            return {
                "success": True,
                "delisted_count": len(delisted),
                "warned_count": len(warned),
                "delisted": delisted,
                "warned": warned,
            }

        except Exception as e:
            logger.error(f"❌ Auto-delisting check failed: {e}")
            return {"success": False, "error": str(e)}

    async def calculate_creator_payouts(
        self, payout_period: str = None
    ) -> Dict[str, Any]:
        """
        §12: Calculate monthly revenue share for creators.
        AlphaForge keeps 10%, creators get 90%.
        """
        if payout_period is None:
            payout_period = datetime.utcnow().strftime("%Y-%m")

        try:
            strategies_response = (
                self.db.supabase.table("creator_strategies")
                .select("*")
                .eq("verification_stage", "stage_4_verified")
                .execute()
            )
            strategies = strategies_response.data or []
            payouts = []

            for strategy in strategies:
                strategy_id = strategy["id"]
                creator_id = strategy.get("creator_id")

                # Count active subscribers
                subs_response = (
                    self.db.supabase.table("strategy_subscriptions")
                    .select("allocation_percentage")
                    .eq("strategy_id", strategy_id)
                    .eq("status", "active")
                    .execute()
                )
                subscribers = subs_response.data or []
                subscriber_count = len(subscribers)

                if subscriber_count == 0:
                    continue

                # Calculate revenue (simplified: per-subscriber fee × allocation)
                per_subscriber_fee = 29.0  # $29/month base fee
                gross_revenue = subscriber_count * per_subscriber_fee
                alphaforge_cut = gross_revenue * 0.10
                creator_take_home = gross_revenue * 0.90

                payout_record = {
                    "strategy_id": strategy_id,
                    "creator_user_id": creator_id,
                    "payout_period": payout_period,
                    "subscriber_count": subscriber_count,
                    "gross_revenue": round(gross_revenue, 2),
                    "alphaforge_cut_10_pct": round(alphaforge_cut, 2),
                    "creator_take_home_90_pct": round(creator_take_home, 2),
                    "status": "CALCULATED",
                    "created_at": datetime.utcnow().isoformat(),
                }

                # Upsert payout record
                self.db.supabase.table("creator_payouts").upsert(payout_record).execute()

                payouts.append({
                    "strategy_id": strategy_id,
                    "creator_id": creator_id,
                    "subscribers": subscriber_count,
                    "gross_revenue": round(gross_revenue, 2),
                    "creator_take_home": round(creator_take_home, 2),
                })

            total_creator_payout = sum(p["creator_take_home"] for p in payouts)

            return {
                "success": True,
                "payout_period": payout_period,
                "total_strategies": len(payouts),
                "total_creator_payout": round(total_creator_payout, 2),
                "total_alphaforge_revenue": round(total_creator_payout / 9, 2),
                "payouts": payouts,
            }

        except Exception as e:
            logger.error(f"❌ Payout calculation failed: {e}")
            return {"success": False, "error": str(e)}

    async def submit_appeal(
        self,
        strategy_id: str,
        creator_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        §12: Creator can appeal delisting (1 appeal allowed).
        Routes to external arbitrator.
        """
        try:
            # Check strategy is delisted
            strategy_response = (
                self.db.supabase.table("creator_strategies")
                .select("*")
                .eq("id", strategy_id)
                .execute()
            )
            if not strategy_response.data:
                return {"success": False, "error": "Strategy not found"}

            strategy = strategy_response.data[0]
            if strategy.get("verification_stage") != "stage_5_delisted":
                return {"success": False, "error": "Strategy is not delisted"}

            # Check if appeal already exists
            appeal_response = (
                self.db.supabase.table("strategy_appeals")
                .select("*")
                .eq("strategy_id", strategy_id)
                .execute()
            )
            if appeal_response.data:
                return {"success": False, "error": "Appeal already submitted (1 appeal maximum)"}

            appeal = {
                "strategy_id": strategy_id,
                "creator_id": creator_id,
                "reason": reason,
                "status": "PENDING_REVIEW",
                "submitted_at": datetime.utcnow().isoformat(),
            }
            self.db.supabase.table("strategy_appeals").insert(appeal).execute()

            logger.info(f"📋 Appeal submitted for strategy {strategy_id}")

            return {
                "success": True,
                "message": "Appeal submitted. Routes to external arbitrator for review.",
                "status": "PENDING_REVIEW",
            }

        except Exception as e:
            logger.error(f"❌ Appeal submission failed: {e}")
            return {"success": False, "error": str(e)}

    async def update_live_performance(
        self,
        strategy_id: str,
        live_sharpe: float,
    ) -> Dict[str, Any]:
        """
        §12: Update strategy's live performance (called monthly by monitoring).
        """
        try:
            self.db.supabase.table("creator_strategies").update({
                "current_live_sharpe": live_sharpe,
                "current_live_sharpe_last_updated": datetime.utcnow().isoformat(),
            }).eq("id", strategy_id).execute()

            return {
                "success": True,
                "strategy_id": strategy_id,
                "live_sharpe": live_sharpe,
                "updated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Live performance update failed: {e}")
            return {"success": False, "error": str(e)}
