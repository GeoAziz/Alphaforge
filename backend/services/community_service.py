"""
Community and social features: user profiles, ratings, comments, leaderboards.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AchievementType(str, Enum):
    """Achievement types."""
    FIRST_SIGNAL = "first_signal"
    FIRST_TRADE = "first_trade"
    WIN_STREAK_5 = "win_streak_5"
    WIN_STREAK_10 = "win_streak_10"
    PROFIT_MILESTONE_1K = "profit_1k"
    PROFIT_MILESTONE_10K = "profit_10k"
    POPULAR_STRATEGY = "popular_strategy"
    CREATOR_TIER_1 = "creator_tier_1"
    CREATOR_TIER_5 = "creator_tier_5"
    COMMUNITY_HELPER = "community_helper"


class CommunityService:
    """Manages community features and user interactions."""

    def __init__(self, db):
        self.db = db

    # ========================================================================
    # USER PROFILES
    # ========================================================================

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get public user profile."""
        try:
            profile = self.db.supabase.table("user_profiles").select("*").eq(
                "user_id", user_id
            ).execute()

            if not profile.data:
                return None

            data = profile.data[0]
            return {
                "user_id": user_id,
                "display_name": data.get("display_name"),
                "bio": data.get("bio"),
                "avatar_url": data.get("avatar_url"),
                "total_followers": data.get("total_followers", 0),
                "total_following": data.get("total_following", 0),
                "win_rate": float(data.get("win_rate", 0)),
                "total_pnl": float(data.get("total_pnl", 0)),
                "average_rr": float(data.get("average_rr", 1.0)),
                "verified": data.get("verified", False),
                "created_at": data.get("created_at"),
                "achievements": await self._get_user_achievements(user_id),
            }

        except Exception as e:
            logger.error(f"❌ Failed to fetch profile for {user_id}: {e}")
            return None

    async def update_user_profile(
        self, user_id: str, display_name: str = None, bio: str = None, avatar_url: str = None
    ) -> Dict[str, Any]:
        """Update user profile."""
        try:
            update_data = {}
            if display_name:
                update_data["display_name"] = display_name
            if bio:
                update_data["bio"] = bio
            if avatar_url:
                update_data["avatar_url"] = avatar_url

            result = self.db.supabase.table("user_profiles").update(update_data).eq(
                "user_id", user_id
            ).execute()

            logger.info(f"✅ Profile updated for {user_id}")
            return {"success": True, "profile": result.data[0] if result.data else {}}

        except Exception as e:
            logger.error(f"❌ Profile update failed: {e}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # FOLLOWERS & FOLLOWING
    # ========================================================================

    async def follow_user(self, user_id: str, target_user_id: str) -> Dict[str, Any]:
        """Follow another user."""
        try:
            insert_data = {
                "follower_id": user_id,
                "following_id": target_user_id,
                "created_at": datetime.utcnow().isoformat(),
            }

            self.db.supabase.table("user_follows").insert(insert_data).execute()

            # Update follower count
            await self._update_follower_count(target_user_id)

            logger.info(f"✅ {user_id} followed {target_user_id}")
            return {"success": True}

        except Exception as e:
            logger.error(f"❌ Follow failed: {e}")
            return {"success": False, "error": str(e)}

    async def unfollow_user(self, user_id: str, target_user_id: str) -> Dict[str, Any]:
        """Unfollow user."""
        try:
            self.db.supabase.table("user_follows").delete().eq(
                "follower_id", user_id
            ).eq("following_id", target_user_id).execute()

            await self._update_follower_count(target_user_id)
            logger.info(f"✅ {user_id} unfollowed {target_user_id}")
            return {"success": True}

        except Exception as e:
            logger.error(f"❌ Unfollow failed: {e}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # STRATEGY COMMENTS & RATINGS
    # ========================================================================

    async def add_strategy_comment(
        self, user_id: str, strategy_id: str, comment_text: str
    ) -> Dict[str, Any]:
        """Add comment to strategy."""
        try:
            insert_data = {
                "user_id": user_id,
                "strategy_id": strategy_id,
                "comment_text": comment_text,
                "likes": 0,
                "created_at": datetime.utcnow().isoformat(),
            }

            result = self.db.supabase.table("strategy_comments").insert(insert_data).execute()
            logger.info(f"✅ Comment added to strategy {strategy_id}")
            return {"success": True, "comment": result.data[0] if result.data else {}}

        except Exception as e:
            logger.error(f"❌ Comment failed: {e}")
            return {"success": False, "error": str(e)}

    async def rate_strategy(
        self, user_id: str, strategy_id: str, rating: int
    ) -> Dict[str, Any]:
        """Rate a strategy (1-5 stars)."""
        if rating < 1 or rating > 5:
            return {"success": False, "error": "Rating must be between 1 and 5"}

        try:
            insert_data = {
                "user_id": user_id,
                "strategy_id": strategy_id,
                "rating": rating,
                "created_at": datetime.utcnow().isoformat(),
            }

            result = self.db.supabase.table("strategy_ratings").insert(insert_data).execute()
            logger.info(f"✅ Strategy {strategy_id} rated {rating}/5")
            return {"success": True}

        except Exception as e:
            logger.error(f"❌ Rating failed: {e}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # LEADERBOARDS
    # ========================================================================

    async def get_leaderboard(
        self, metric: str = "pnl", timeframe: str = "all_time", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get leaderboard rankings."""
        try:
            # Mock implementation - in production, use materialized views
            leaderboard = self.db.supabase.table("user_leaderboard").select("*").order(
                metric, desc=True
            ).limit(limit).execute()

            return [
                {
                    "rank": i + 1,
                    "user_id": row.get("user_id"),
                    "display_name": row.get("display_name"),
                    "metric_value": float(row.get(metric, 0)),
                    "win_rate": float(row.get("win_rate", 0)),
                    "total_trades": int(row.get("total_trades", 0)),
                }
                for i, row in enumerate(leaderboard.data or [])
            ]

        except Exception as e:
            logger.error(f"❌ Failed to fetch leaderboard: {e}")
            return []

    # ========================================================================
    # ACHIEVEMENTS & BADGES
    # ========================================================================

    async def award_achievement(
        self, user_id: str, achievement_type: AchievementType
    ) -> Dict[str, Any]:
        """Award achievement to user."""
        try:
            # Check if already awarded
            existing = self.db.supabase.table("user_achievements").select("*").eq(
                "user_id", user_id
            ).eq("achievement_type", achievement_type.value).execute()

            if existing.data:
                logger.info(f"⚠️  User {user_id} already has {achievement_type.value}")
                return {"success": False, "error": "Already awarded"}

            insert_data = {
                "user_id": user_id,
                "achievement_type": achievement_type.value,
                "awarded_at": datetime.utcnow().isoformat(),
            }

            self.db.supabase.table("user_achievements").insert(insert_data).execute()
            logger.info(f"🏆 Achievement '{achievement_type.value}' awarded to {user_id}")
            return {"success": True, "achievement": achievement_type.value}

        except Exception as e:
            logger.error(f"❌ Achievement award failed: {e}")
            return {"success": False, "error": str(e)}

    async def _get_user_achievements(self, user_id: str) -> List[str]:
        """Get all achievements for user."""
        try:
            result = self.db.supabase.table("user_achievements").select(
                "achievement_type"
            ).eq("user_id", user_id).execute()

            return [row["achievement_type"] for row in (result.data or [])]

        except Exception as e:
            logger.error(f"❌ Failed to fetch achievements: {e}")
            return []

    # ========================================================================
    # NOTIFICATIONS
    # ========================================================================

    async def send_notification(
        self, user_id: str, title: str, message: str, notification_type: str = "info"
    ) -> Dict[str, Any]:
        """Send in-app notification."""
        try:
            insert_data = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "is_read": False,
                "created_at": datetime.utcnow().isoformat(),
            }

            result = self.db.supabase.table("notifications").insert(insert_data).execute()
            logger.info(f"✅ Notification sent to {user_id}")
            return {"success": True}

        except Exception as e:
            logger.error(f"❌ Notification send failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_unread_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get unread notifications for user."""
        try:
            result = self.db.supabase.table("notifications").select("*").eq(
                "user_id", user_id
            ).eq("is_read", False).order("created_at", desc=True).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"❌ Failed to fetch notifications: {e}")
            return []

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _update_follower_count(self, user_id: str):
        """Update follower count for user."""
        try:
            count_result = self.db.supabase.table("user_follows").select(
                "follower_id", count="exact"
            ).eq("following_id", user_id).execute()

            follower_count = count_result.count or 0

            self.db.supabase.table("user_profiles").update({
                "total_followers": follower_count
            }).eq("user_id", user_id).execute()

        except Exception as e:
            logger.error(f"⚠️  Failed to update follower count: {e}")
