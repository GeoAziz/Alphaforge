"""
AlphaAcademy Education Service - Content management, progress tracking, and signal breakdowns.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SIGNAL_PATTERN_MAP = {
    "momentum_divergence": {
        "related_content_tags": ["momentum", "divergence", "RSI", "MACD"],
        "default_category": "patterns",
    },
    "breakout": {
        "related_content_tags": ["breakout", "support", "resistance", "volume"],
        "default_category": "patterns",
    },
    "mean_reversion": {
        "related_content_tags": ["mean reversion", "z-score", "Bollinger Bands", "RSI"],
        "default_category": "patterns",
    },
    "volume_spike": {
        "related_content_tags": ["volume", "breakout"],
        "default_category": "patterns",
    },
    "trend_continuation": {
        "related_content_tags": ["breakout", "momentum"],
        "default_category": "patterns",
    },
    "risk_alert": {
        "related_content_tags": ["risk management", "stop loss", "drawdown"],
        "default_category": "risk_mgmt",
    },
    "portfolio_rebalance": {
        "related_content_tags": ["position sizing", "portfolio management"],
        "default_category": "strategies",
    },
}


class EducationService:
    """Manages education content, user progress, and signal breakdowns."""

    def __init__(self, db):
        self.db = db

    # ========== CONTENT ENDPOINTS ==========

    async def list_content(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all education content with optional filters."""
        try:
            query = self.db.supabase.table("education_content").select("*")

            if category:
                query = query.eq("category", category)
            if difficulty:
                query = query.eq("difficulty", difficulty)

            response = query.order("created_at", desc=True).execute()

            return {
                "success": True,
                "content": response.data or [],
                "total": len(response.data or []),
            }
        except Exception as e:
            logger.error(f"Failed to list education content: {e}")
            return {"success": False, "error": str(e), "content": []}

    async def get_content(self, content_id: str) -> Dict[str, Any]:
        """Get a single content piece by ID."""
        try:
            response = (
                self.db.supabase.table("education_content")
                .select("*")
                .eq("content_id", content_id)
                .execute()
            )

            if not response.data:
                return {"success": False, "error": "Content not found"}

            return {"success": True, "content": response.data[0]}
        except Exception as e:
            logger.error(f"Failed to get education content {content_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_related_content(self, signal_type: str) -> Dict[str, Any]:
        """Get education content related to a signal type."""
        try:
            mapping = SIGNAL_PATTERN_MAP.get(signal_type)
            if not mapping:
                return {"success": True, "content": [], "category": None}

            tags = mapping["related_content_tags"]
            category = mapping["default_category"]

            response = (
                self.db.supabase.table("education_content")
                .select("*")
                .eq("category", category)
                .execute()
            )

            content_items = response.data or []

            scored = []
            for item in content_items:
                item_tags = item.get("tags", [])
                overlap = len(set(tags) & set(item_tags))
                scored.append((overlap, item))

            scored.sort(key=lambda x: x[0], reverse=True)
            related = [item for _, item in scored if _ > 0][:5]

            return {
                "success": True,
                "content": related,
                "category": category,
                "signal_type": signal_type,
            }
        except Exception as e:
            logger.error(f"Failed to get related content for {signal_type}: {e}")
            return {"success": False, "error": str(e), "content": []}

    # ========== PROGRESS TRACKING ==========

    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get a user's education progress."""
        try:
            response = (
                self.db.supabase.table("user_education_progress")
                .select("*, education_content(title, category, difficulty)")
                .eq("user_id", user_id)
                .execute()
            )

            progress_entries = response.data or []
            completed_count = sum(1 for p in progress_entries if p.get("completed"))
            total_count_response = (
                self.db.supabase.table("education_content")
                .select("content_id", count="exact")
                .execute()
            )
            total_content = len(total_count_response.data or [])

            scores = [
                p["quiz_score"]
                for p in progress_entries
                if p.get("quiz_score") is not None
            ]
            avg_score = sum(scores) / len(scores) if scores else None

            return {
                "success": True,
                "user_id": user_id,
                "progress": progress_entries,
                "completed_count": completed_count,
                "total_content": total_content,
                "completion_pct": (
                    round((completed_count / total_content * 100), 1)
                    if total_content > 0
                    else 0
                ),
                "average_quiz_score": round(avg_score, 1) if avg_score is not None else None,
            }
        except Exception as e:
            logger.error(f"Failed to get progress for user {user_id}: {e}")
            return {"success": False, "error": str(e), "progress": []}

    async def mark_completed(
        self,
        user_id: str,
        content_id: str,
        quiz_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Mark a content piece as completed for a user."""
        try:
            now = datetime.utcnow().isoformat()

            existing = (
                self.db.supabase.table("user_education_progress")
                .select("*")
                .eq("user_id", user_id)
                .eq("content_id", content_id)
                .execute()
            )

            if existing.data:
                update_data = {
                    "completed": True,
                    "completed_at": now,
                }
                if quiz_score is not None:
                    update_data["quiz_score"] = quiz_score

                response = (
                    self.db.supabase.table("user_education_progress")
                    .update(update_data)
                    .eq("user_id", user_id)
                    .eq("content_id", content_id)
                    .execute()
                )
            else:
                insert_data = {
                    "user_id": user_id,
                    "content_id": content_id,
                    "completed": True,
                    "completed_at": now,
                }
                if quiz_score is not None:
                    insert_data["quiz_score"] = quiz_score

                response = (
                    self.db.supabase.table("user_education_progress")
                    .insert(insert_data)
                    .execute()
                )

            return {
                "success": True,
                "user_id": user_id,
                "content_id": content_id,
                "completed": True,
                "quiz_score": quiz_score,
            }
        except Exception as e:
            logger.error(f"Failed to mark content completed: {e}")
            return {"success": False, "error": str(e)}

    # ========== SIGNAL BREAKDOWNS ==========

    async def get_signal_breakdown(self, signal_id: str) -> Dict[str, Any]:
        """Get an existing signal breakdown."""
        try:
            response = (
                self.db.supabase.table("signal_breakdowns")
                .select("*")
                .eq("signal_id", signal_id)
                .execute()
            )

            if not response.data:
                return {"success": False, "error": "Breakdown not found"}

            return {"success": True, "breakdown": response.data[0]}
        except Exception as e:
            logger.error(f"Failed to get breakdown for signal {signal_id}: {e}")
            return {"success": False, "error": str(e)}

    async def generate_breakdown(self, signal_id: str) -> Dict[str, Any]:
        """Generate an AI breakdown explanation for a signal."""
        try:
            signal_response = (
                self.db.supabase.table("signals")
                .select("*")
                .eq("id", signal_id)
                .execute()
            )

            if not signal_response.data:
                return {"success": False, "error": "Signal not found"}

            signal = signal_response.data[0]
            ticker = signal.get("ticker", "Unknown")
            signal_type = signal.get("signal_type", "Unknown")
            confidence = signal.get("confidence", 0)
            entry_price = signal.get("entry_price")
            stop_loss = signal.get("stop_loss_price")
            take_profit = signal.get("take_profit_price")
            drivers = signal.get("drivers", [])
            rationale = signal.get("rationale", "")

            if isinstance(drivers, str):
                import json
                try:
                    drivers = json.loads(drivers)
                except (json.JSONDecodeError, TypeError):
                    drivers = []

            pattern_name = "General Signal"
            key_metrics = {}

            if isinstance(drivers, list) and drivers:
                first_driver = drivers[0] if isinstance(drivers[0], str) else str(drivers[0])
                pattern_name = first_driver.replace("_", " ").title()
                key_metrics["drivers"] = drivers

            if entry_price:
                key_metrics["entry_price"] = entry_price
            if stop_loss:
                key_metrics["stop_loss"] = stop_loss
            if take_profit:
                key_metrics["take_profit"] = take_profit
            if confidence:
                key_metrics["confidence"] = confidence

            risk_reward = None
            if entry_price and stop_loss and take_profit and entry_price > 0:
                risk = abs(float(entry_price) - float(stop_loss))
                reward = abs(float(take_profit) - float(entry_price))
                if risk > 0:
                    risk_reward = round(reward / risk, 2)
                    key_metrics["risk_reward_ratio"] = risk_reward

            breakdown_parts = [
                f"**{signal_type} Signal for {ticker}**",
                f"Confidence: {confidence:.0%}" if confidence else "",
                "",
            ]

            if rationale:
                breakdown_parts.append(f"**Rationale:** {rationale}")
                breakdown_parts.append("")

            if drivers and isinstance(drivers, list):
                breakdown_parts.append("**Key Drivers:**")
                for d in drivers:
                    label = d.replace("_", " ").title() if isinstance(d, str) else str(d)
                    breakdown_parts.append(f"- {label}")
                breakdown_parts.append("")

            if risk_reward is not None:
                breakdown_parts.append(f"**Risk/Reward Ratio:** {risk_reward}:1")
                if risk_reward >= 2:
                    breakdown_parts.append("This is a favorable risk/reward setup (>= 2:1).")
                elif risk_reward >= 1:
                    breakdown_parts.append("Moderate risk/reward. Ensure position sizing is appropriate.")
                else:
                    breakdown_parts.append("Low risk/reward. Consider whether this trade meets your criteria.")
                breakdown_parts.append("")

            breakdown_parts.append(f"**Pattern:** {pattern_name}")

            breakdown_summary = "\n".join(part for part in breakdown_parts if part is not None)

            related_content_resp = await self.get_related_content(
                pattern_name.lower().replace(" ", "_")
            )
            related_items = related_content_resp.get("content", [])
            if related_items:
                breakdown_parts.append("")
                breakdown_parts.append("**Learn More:**")
                for item in related_items[:3]:
                    breakdown_parts.append(
                        f"- [{item.get('title', 'Guide')}](/academy/{item.get('content_id', '')})"
                    )
                breakdown_summary = "\n".join(breakdown_parts)

            import json as _json
            breakdown_record = {
                "signal_id": signal_id,
                "breakdown_summary": breakdown_summary,
                "pattern_name": pattern_name,
                "key_metrics": _json.dumps(key_metrics) if isinstance(key_metrics, dict) else key_metrics,
                "generated_at": datetime.utcnow().isoformat(),
            }

            existing = (
                self.db.supabase.table("signal_breakdowns")
                .select("signal_id")
                .eq("signal_id", signal_id)
                .execute()
            )

            if existing.data:
                self.db.supabase.table("signal_breakdowns").update(breakdown_record).eq(
                    "signal_id", signal_id
                ).execute()
            else:
                self.db.supabase.table("signal_breakdowns").insert(breakdown_record).execute()

            return {
                "success": True,
                "breakdown": breakdown_record,
                "related_content": related_items,
            }
        except Exception as e:
            logger.error(f"Failed to generate breakdown for signal {signal_id}: {e}")
            return {"success": False, "error": str(e)}
