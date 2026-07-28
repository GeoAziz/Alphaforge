"""
Strategy Personality Service - Assigns personality badges and avatars
to trading strategies based on their characteristics.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

PERSONALITY_PROFILES = {
    "conservative_hedge": {
        "name": "Conservative Hedge",
        "badge": "🛡️",
        "avatar_color": "#4A90D9",
        "description": "Low-risk, capital-preservation focused. Prioritizes downside protection over upside capture.",
        "traits": ["Low drawdown", "Steady returns", "Risk-averse"],
        "icon": "shield",
    },
    "growth_seeker": {
        "name": "Growth Seeker",
        "badge": "🚀",
        "avatar_color": "#27AE60",
        "description": "Targets above-average returns with moderate risk. Willing to accept drawdowns for growth.",
        "traits": ["High ROI", "Moderate risk", "Long positions"],
        "icon": "rocket",
    },
    "volatility_hunter": {
        "name": "Volatility Hunter",
        "badge": "⚡",
        "avatar_color": "#E74C3C",
        "description": "Thrives in volatile markets. Uses large moves in both directions to generate returns.",
        "traits": ["High volatility tolerance", "Bilateral trades", "Dynamic sizing"],
        "icon": "lightning",
    },
    "trend_surfer": {
        "name": "Trend Surfer",
        "badge": "🌊",
        "avatar_color": "#3498DB",
        "description": "Rides momentum and trend continuation. Enters late but rides trends for extended periods.",
        "traits": ["Momentum-based", "Trend following", "Patient entries"],
        "icon": "wave",
    },
    "sniper": {
        "name": "Sniper",
        "badge": "🎯",
        "avatar_color": "#8E44AD",
        "description": "Highly selective. Waits for optimal setups and strikes with precision. Few but impactful trades.",
        "traits": ["High win rate", "Selective entries", "Large position sizes"],
        "icon": "target",
    },
    "grid_master": {
        "name": "Grid Master",
        "badge": "📐",
        "avatar_color": "#F39C12",
        "description": "Systematic grid trading approach. Harvests small profits across many trades with tight ranges.",
        "traits": ["High frequency", "Mean-reverting", "Tight stop losses"],
        "icon": "grid",
    },
    "contrarian": {
        "name": "Contrarian",
        "badge": "🔄",
        "avatar_color": "#1ABC9C",
        "description": "Bets against the crowd. Enters when others are fearful and exits when euphoria peaks.",
        "traits": ["Counter-trend", "Mean reversion", "Independent thinker"],
        "icon": "contrarian",
    },
    "diamond_hands": {
        "name": "Diamond Hands",
        "badge": "💎",
        "avatar_color": "#2C3E50",
        "description": "Unshakeable conviction. Holds through volatility with conviction-based position management.",
        "traits": ["Long hold periods", "Conviction-driven", "Deep analysis"],
        "icon": "diamond",
    },
}

PERSONALITY_PROFILES["default"] = {
    "name": "The Generalist",
    "badge": "📊",
    "avatar_color": "#95A5A6",
    "description": "A balanced approach without strong personality leanings. Adapts to market conditions.",
    "traits": ["Balanced", "Adaptive", "Multi-approach"],
    "icon": "chart",
}


def classify_strategy_personality(
    win_rate: float = 0.5,
    avg_roi: float = 0.0,
    max_drawdown: float = 0.1,
    sharpe_ratio: float = 1.0,
    total_trades: int = 0,
    risk_level: str = "medium",
) -> str:
    """Rule-based classification of strategy personality from parameters."""
    win_rate = max(0.0, min(1.0, win_rate))
    max_drawdown = max(0.0, abs(max_drawdown))

    if total_trades < 5:
        return "default"

    risk_low = risk_level.lower() in ("low", "conservative")

    if risk_low and max_drawdown < 0.05 and sharpe_ratio > 1.0:
        return "conservative_hedge"

    if win_rate > 0.75 and total_trades < 20:
        return "sniper"

    if avg_roi > 0.15 and max_drawdown > 0.15:
        return "volatility_hunter"

    if avg_roi > 0.10 and sharpe_ratio > 1.5:
        return "growth_seeker"

    if sharpe_ratio > 1.2 and max_drawdown < 0.08:
        return "grid_master"

    if max_drawdown > 0.20 and avg_roi > 0.05:
        return "diamond_hands"

    if risk_level.lower() in ("high", "aggressive") and avg_roi > 0.08:
        return "trend_surfer"

    return "default"


class StrategyPersonalityService:
    """Assigns and retrieves strategy personality profiles."""

    def __init__(self, db=None):
        self.db = db

    async def get_personality(
        self,
        strategy_id: str,
    ) -> Dict[str, Any]:
        """Get strategy personality based on performance metrics."""
        try:
            strategy_metrics = {}
            if self.db:
                response = (
                    self.db.supabase.table("strategies")
                    .select("*")
                    .eq("id", strategy_id)
                    .execute()
                )
                if response.data:
                    strategy_metrics = response.data[0]

                if not strategy_metrics:
                    response = (
                        self.db.supabase.table("creator_strategies")
                        .select("*")
                        .eq("id", strategy_id)
                        .execute()
                    )
                    if response.data:
                        strategy_metrics = response.data[0]

            win_rate = float(strategy_metrics.get("win_rate") or 0.5)
            avg_roi = float(strategy_metrics.get("avg_roi") or strategy_metrics.get("roi") or 0.0)
            max_drawdown = float(strategy_metrics.get("max_drawdown") or 0.1)
            sharpe_ratio = float(strategy_metrics.get("sharpe_ratio") or 1.0)
            total_trades = int(strategy_metrics.get("total_trades") or 0)
            risk_level = strategy_metrics.get("risk_level", "medium")

            personality_key = classify_strategy_personality(
                win_rate=win_rate,
                avg_roi=avg_roi,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                total_trades=total_trades,
                risk_level=risk_level,
            )

            personality = PERSONALITY_PROFILES.get(personality_key, PERSONALITY_PROFILES["default"])

            return {
                "success": True,
                "strategy_id": strategy_id,
                "personality_key": personality_key,
                "personality": personality,
                "metrics_used": {
                    "win_rate": win_rate,
                    "avg_roi": avg_roi,
                    "max_drawdown": max_drawdown,
                    "sharpe_ratio": sharpe_ratio,
                    "total_trades": total_trades,
                    "risk_level": risk_level,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get strategy personality: {e}")
            return {"success": False, "error": str(e)}
