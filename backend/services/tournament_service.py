"""
Tournament Service - Monthly competitive trading events on paper trading.
Users compete on leaderboards ranked by return%, Sharpe ratio, and win rate.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TournamentService:
    """Manages trading tournaments, entries, and leaderboards."""

    def __init__(self, db):
        self.db = db

    async def list_tournaments(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List active/upcoming tournaments."""
        try:
            query = self.db.supabase.table("tournaments").select("*")
            if status_filter:
                query = query.eq("status", status_filter.upper())
            else:
                query = query.in_("status", ["ACTIVE", "UPCOMING"])
            response = query.order("start_time", desc=False).limit(limit).execute()
            tournaments = response.data or []
            return {
                "success": True,
                "tournaments": tournaments,
                "count": len(tournaments),
            }
        except Exception as e:
            logger.error(f"Failed to list tournaments: {e}")
            return {"success": False, "error": str(e), "tournaments": [], "count": 0}

    async def join_tournament(
        self,
        tournament_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Join a tournament."""
        try:
            tournament_resp = self.db.supabase.table("tournaments").select("*").eq("id", tournament_id).single().execute()
            tournament = tournament_resp.data
            if not tournament:
                return {"success": False, "error": "Tournament not found"}

            if tournament.get("status") not in ("UPCOMING", "ACTIVE"):
                return {"success": False, "error": "Tournament is not accepting entries"}

            existing = (
                self.db.supabase.table("tournament_entries")
                .select("id")
                .eq("tournament_id", tournament_id)
                .eq("user_id", user_id)
                .execute()
            )
            if existing.data:
                return {"success": False, "error": "Already joined this tournament"}

            entry_data = {
                "tournament_id": tournament_id,
                "user_id": user_id,
                "final_pnl": 0,
                "final_sharpe": 0,
                "final_win_rate": 0,
                "rank": 0,
                "created_at": datetime.utcnow().isoformat(),
            }
            response = self.db.supabase.table("tournament_entries").insert(entry_data).execute()

            if response.data:
                entry_id = response.data[0].get("id")
                logger.info(f"User {user_id} joined tournament {tournament_id}")
                return {"success": True, "entry_id": entry_id, "tournament_id": tournament_id}

            return {"success": False, "error": "Failed to create entry"}
        except Exception as e:
            logger.error(f"Failed to join tournament: {e}")
            return {"success": False, "error": str(e)}

    async def get_leaderboard(
        self,
        tournament_id: str,
        sort_by: str = "final_pnl",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get tournament leaderboard."""
        try:
            valid_sorts = {"final_pnl": "final_pnl", "final_sharpe": "final_sharpe", "final_win_rate": "final_win_rate"}
            order_col = valid_sorts.get(sort_by, "final_pnl")

            response = (
                self.db.supabase.table("tournament_entries")
                .select("*, users(display_name)")
                .eq("tournament_id", tournament_id)
                .order(order_col, desc=True)
                .limit(limit)
                .execute()
            )

            entries = response.data or []
            leaderboard = []
            for rank_idx, entry in enumerate(entries, start=1):
                user_info = entry.get("users") or {}
                leaderboard.append({
                    "rank": rank_idx,
                    "user_id": entry.get("user_id"),
                    "display_name": user_info.get("display_name", "Anonymous"),
                    "final_pnl": float(entry.get("final_pnl") or 0),
                    "final_sharpe": float(entry.get("final_sharpe") or 0),
                    "final_win_rate": float(entry.get("final_win_rate") or 0),
                })

            return {
                "success": True,
                "tournament_id": tournament_id,
                "leaderboard": leaderboard,
                "count": len(leaderboard),
            }
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            return {"success": False, "error": str(e), "leaderboard": [], "count": 0}

    async def get_my_status(
        self,
        tournament_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get user's status in a tournament."""
        try:
            entry_resp = (
                self.db.supabase.table("tournament_entries")
                .select("*")
                .eq("tournament_id", tournament_id)
                .eq("user_id", user_id)
                .execute()
            )

            if not entry_resp.data:
                return {"success": True, "joined": False, "tournament_id": tournament_id}

            entry = entry_resp.data[0]

            leaderboard = await self.get_leaderboard(tournament_id)
            rank = 0
            total_participants = leaderboard.get("count", 0)
            for lb_entry in leaderboard.get("leaderboard", []):
                if lb_entry.get("user_id") == user_id:
                    rank = lb_entry.get("rank", 0)
                    break

            return {
                "success": True,
                "joined": True,
                "tournament_id": tournament_id,
                "entry_id": entry.get("id"),
                "rank": rank,
                "total_participants": total_participants,
                "final_pnl": float(entry.get("final_pnl") or 0),
                "final_sharpe": float(entry.get("final_sharpe") or 0),
                "final_win_rate": float(entry.get("final_win_rate") or 0),
            }
        except Exception as e:
            logger.error(f"Failed to get tournament status: {e}")
            return {"success": False, "error": str(e)}
