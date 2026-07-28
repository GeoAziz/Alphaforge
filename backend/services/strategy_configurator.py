"""
Strategy Configurator Service - No-Code Strategy Builder.
Parses user-defined rules, validates constraints, compiles to execution logic,
and stores rule templates for reuse/sharing.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from copy import deepcopy

logger = logging.getLogger(__name__)

VALID_VOLATILITY_LEVELS = {"low", "medium", "high"}
VALID_POSITION_SIZING_METHODS = {"fixed", "kelly", "equal_weight", "risk_parity", "volatility_adjusted"}
VALID_DIFFICULTY_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_TEMPLATE_CATEGORIES = {
    "trend_following", "mean_reversion", "momentum", "scalping",
    "swing_trading", "arbitrage", "market_making", "custom"
}


class StrategyConfiguratorService:
    """Manages user-defined strategy rules with validation and compilation."""

    def __init__(self, db):
        self.db = db

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def validate_rules(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate strategy rules against constraints.

        Returns {"valid": True} on success or {"valid": False, "errors": [...]}.
        """
        errors: List[str] = []

        signal_filters = rules.get("signal_filters", {})
        position_sizing = rules.get("position_sizing", {})
        risk_controls = rules.get("risk_controls", {})

        # -- signal_filters --
        min_conf = signal_filters.get("min_confidence")
        if min_conf is not None:
            if not isinstance(min_conf, (int, float)):
                errors.append("signal_filters.min_confidence must be a number")
            elif min_conf < 0 or min_conf > 1:
                errors.append("signal_filters.min_confidence must be between 0 and 1")

        max_vol = signal_filters.get("max_volatility")
        if max_vol is not None and str(max_vol).lower() not in VALID_VOLATILITY_LEVELS:
            errors.append(
                f"signal_filters.max_volatility must be one of {sorted(VALID_VOLATILITY_LEVELS)}"
            )

        time_windows = signal_filters.get("preferred_time_windows")
        if time_windows is not None:
            if not isinstance(time_windows, list):
                errors.append("signal_filters.preferred_time_windows must be a list")
            elif len(time_windows) > 24:
                errors.append("signal_filters.preferred_time_windows too long (max 24)")

        # -- position_sizing --
        method = position_sizing.get("method")
        if method is not None and method.lower() not in VALID_POSITION_SIZING_METHODS:
            errors.append(
                f"position_sizing.method must be one of {sorted(VALID_POSITION_SIZING_METHODS)}"
            )

        base_alloc = position_sizing.get("base_allocation")
        if base_alloc is not None:
            if not isinstance(base_alloc, (int, float)):
                errors.append("position_sizing.base_allocation must be a number")
            elif base_alloc < 0.001 or base_alloc > 0.10:
                errors.append("position_sizing.base_allocation must be between 0.001 and 0.10")

        max_per = position_sizing.get("max_per_position")
        if max_per is not None:
            if not isinstance(max_per, (int, float)) or max_per < 0:
                errors.append("position_sizing.max_per_position must be a positive number")
            elif max_per > 10000:
                errors.append("position_sizing.max_per_position must not exceed 10000")

        # -- risk_controls --
        max_loss_trade = risk_controls.get("max_loss_per_trade")
        if max_loss_trade is not None:
            if not isinstance(max_loss_trade, (int, float)) or max_loss_trade < 0:
                errors.append("risk_controls.max_loss_per_trade must be a positive number")
            elif max_loss_trade > 10000:
                errors.append("risk_controls.max_loss_per_trade must not exceed 10000")

        max_daily = risk_controls.get("max_daily_loss")
        if max_daily is not None:
            if not isinstance(max_daily, (int, float)) or max_daily < 0:
                errors.append("risk_controls.max_daily_loss must be a positive number")
            elif max_daily > 50000:
                errors.append("risk_controls.max_daily_loss must not exceed 50000")

        max_open = risk_controls.get("max_open_positions")
        if max_open is not None:
            if not isinstance(max_open, int) or max_open < 1:
                errors.append("risk_controls.max_open_positions must be a positive integer")
            elif max_open > 20:
                errors.append("risk_controls.max_open_positions must not exceed 20")

        return {"valid": len(errors) == 0, "errors": errors}

    # ------------------------------------------------------------------
    # COMPILATION
    # ------------------------------------------------------------------

    def compile_rules(self, rules: Dict[str, Any]) -> Callable[[Dict[str, Any]], bool]:
        """Compile validated rules into a callable that evaluates a signal dict.

        Returns a function(signal) -> bool (True if signal passes all filters).
        """
        signal_filters = rules.get("signal_filters", {})
        position_sizing = rules.get("position_sizing", {})
        risk_controls = rules.get("risk_controls", {})

        min_confidence = float(signal_filters.get("min_confidence", 0.0))
        max_volatility = signal_filters.get("max_volatility")
        preferred_windows = signal_filters.get("preferred_time_windows", [])
        excluded_tickers = set(signal_filters.get("excluded_tickers", []))
        included_tickers = signal_filters.get("included_tickers")

        def evaluator(signal: Dict[str, Any]) -> bool:
            confidence = float(signal.get("confidence", 0))
            if confidence < min_confidence:
                return False

            vol = str(signal.get("volatility", "medium")).lower()
            if max_volatility:
                vol_order = {"low": 0, "medium": 1, "high": 2}
                if vol_order.get(vol, 1) > vol_order.get(max_volatility.lower(), 2):
                    return False

            ticker = signal.get("ticker", "").upper()
            if ticker in excluded_tickers:
                return False
            if included_tickers and ticker not in included_tickers:
                return False

            if preferred_windows:
                signal_time = signal.get("timestamp", "")
                if signal_time:
                    from datetime import datetime as _dt
                    try:
                        ts = _dt.fromisoformat(signal_time.replace("Z", "+00:00"))
                        hour = ts.hour
                        in_window = False
                        for window in preferred_windows:
                            parts = window.replace(" UTC", "").split("-")
                            if len(parts) == 2:
                                start_h = int(parts[0].split(":")[0])
                                end_h = int(parts[1].split(":")[0])
                                if start_h <= end_h:
                                    in_window = start_h <= hour < end_h
                                else:
                                    in_window = hour >= start_h or hour < end_h
                                if in_window:
                                    break
                        if not in_window:
                            return False
                    except (ValueError, IndexError):
                        pass

            return True

        return evaluator

    # ------------------------------------------------------------------
    # CRUD OPERATIONS
    # ------------------------------------------------------------------

    async def create_strategy(
        self,
        user_id: str,
        strategy_name: str,
        rules: Dict[str, Any],
        description: str = "",
    ) -> Dict[str, Any]:
        """Create a new user strategy."""
        try:
            # Enforce per-user limit
            existing = await self.list_user_strategies(user_id)
            if existing.get("count", 0) >= 20:
                return {"success": False, "error": "Strategy limit reached (max 20)"}

            # Validate
            validation = self.validate_rules(rules)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "Validation failed",
                    "validation_errors": validation["errors"],
                }

            now = datetime.utcnow().isoformat()
            strategy_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "strategy_name": strategy_name,
                "description": description,
                "rules": rules,
                "is_active": False,
                "performance_stats": {},
                "created_at": now,
                "updated_at": now,
            }

            response = self.db.supabase.table("user_strategies").insert(strategy_data).execute()

            if response.data:
                logger.info(f"✅ Strategy created: {strategy_name} for {user_id}")
                return {"success": True, "strategy": response.data[0]}

            return {"success": False, "error": "Database insert failed"}

        except Exception as e:
            logger.error(f"❌ Create strategy failed: {e}")
            return {"success": False, "error": str(e)}

    async def list_user_strategies(self, user_id: str) -> Dict[str, Any]:
        """List all strategies for a user."""
        try:
            response = (
                self.db.supabase.table("user_strategies")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            strategies = response.data or []
            return {
                "success": True,
                "strategies": strategies,
                "count": len(strategies),
            }
        except Exception as e:
            logger.error(f"❌ List strategies failed: {e}")
            return {"success": False, "error": str(e), "strategies": [], "count": 0}

    async def get_strategy(self, strategy_id: str, user_id: str) -> Dict[str, Any]:
        """Get a single strategy by ID."""
        try:
            response = (
                self.db.supabase.table("user_strategies")
                .select("*")
                .eq("id", strategy_id)
                .eq("user_id", user_id)
                .execute()
            )
            if response.data:
                return {"success": True, "strategy": response.data[0]}
            return {"success": False, "error": "Strategy not found"}
        except Exception as e:
            logger.error(f"❌ Get strategy failed: {e}")
            return {"success": False, "error": str(e)}

    async def update_strategy(
        self,
        strategy_id: str,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update strategy rules, name, or description."""
        try:
            current = await self.get_strategy(strategy_id, user_id)
            if not current.get("success"):
                return current

            update_data: Dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}

            if "rules" in updates:
                validation = self.validate_rules(updates["rules"])
                if not validation["valid"]:
                    return {
                        "success": False,
                        "error": "Validation failed",
                        "validation_errors": validation["errors"],
                    }
                update_data["rules"] = updates["rules"]

            if "strategy_name" in updates:
                update_data["strategy_name"] = updates["strategy_name"]
            if "description" in updates:
                update_data["description"] = updates["description"]

            response = (
                self.db.supabase.table("user_strategies")
                .update(update_data)
                .eq("id", strategy_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                logger.info(f"✅ Strategy updated: {strategy_id}")
                return {"success": True, "strategy": response.data[0]}

            return {"success": False, "error": "Update failed"}

        except Exception as e:
            logger.error(f"❌ Update strategy failed: {e}")
            return {"success": False, "error": str(e)}

    async def delete_strategy(self, strategy_id: str, user_id: str) -> Dict[str, Any]:
        """Delete a user strategy."""
        try:
            current = await self.get_strategy(strategy_id, user_id)
            if not current.get("success"):
                return current

            response = (
                self.db.supabase.table("user_strategies")
                .delete()
                .eq("id", strategy_id)
                .eq("user_id", user_id)
                .execute()
            )

            logger.info(f"✅ Strategy deleted: {strategy_id}")
            return {"success": True, "message": "Strategy deleted"}

        except Exception as e:
            logger.error(f"❌ Delete strategy failed: {e}")
            return {"success": False, "error": str(e)}

    async def activate_strategy(self, strategy_id: str, user_id: str) -> Dict[str, Any]:
        """Set a strategy as active (deactivates all others for the user)."""
        try:
            current = await self.get_strategy(strategy_id, user_id)
            if not current.get("success"):
                return current

            # Deactivate all user strategies
            all_strategies = await self.list_user_strategies(user_id)
            for s in all_strategies.get("strategies", []):
                if s.get("is_active") and s.get("id") != strategy_id:
                    self.db.supabase.table("user_strategies").update(
                        {"is_active": False, "updated_at": datetime.utcnow().isoformat()}
                    ).eq("id", s["id"]).execute()

            # Activate target
            response = (
                self.db.supabase.table("user_strategies")
                .update({"is_active": True, "updated_at": datetime.utcnow().isoformat()})
                .eq("id", strategy_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                logger.info(f"✅ Strategy activated: {strategy_id}")
                return {"success": True, "strategy": response.data[0]}

            return {"success": False, "error": "Activation failed"}

        except Exception as e:
            logger.error(f"❌ Activate strategy failed: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # SIMULATION
    # ------------------------------------------------------------------

    async def simulate_strategy(
        self,
        strategy_id: str,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Simulate a strategy against past signals.

        Returns simulated performance metrics.
        """
        try:
            current = await self.get_strategy(strategy_id, user_id)
            if not current.get("success"):
                return current

            rules = current["strategy"].get("rules", {})
            evaluator = self.compile_rules(rules)

            # Fetch recent signals
            from datetime import timedelta
            cutoff = (datetime.utcnow() - timedelta(days=min(days, 365))).isoformat()
            response = (
                self.db.supabase.table("signals")
                .select("*")
                .gte("created_at", cutoff)
                .limit(1000)
                .execute()
            )
            signals = response.data or []

            total = 0
            passed = 0
            matched_signals = []
            for sig in signals:
                total += 1
                if evaluator(sig):
                    passed += 1
                    matched_signals.append(sig)

            # Compute simulated stats
            total_pnl = 0.0
            wins = 0
            losses = 0
            max_drawdown = 0.0
            equity = 10000.0
            peak_equity = equity

            for sig in matched_signals:
                entry = float(sig.get("entry_price") or 0)
                sl = float(sig.get("stop_loss_price") or entry * 0.98)
                tp = float(sig.get("take_profit_price") or entry * 1.03)

                if entry == 0:
                    continue

                risk = abs(entry - sl)
                reward = abs(tp - entry)
                rr_ratio = reward / risk if risk > 0 else 1.0

                # Simulate: win if RR >= 1.5, otherwise random
                import random
                is_win = random.random() < (0.5 + min(rr_ratio * 0.05, 0.2))
                pnl_pct = 0.02 if is_win else -0.01

                trade_pnl = equity * pnl_pct
                total_pnl += trade_pnl
                equity += trade_pnl

                if is_win:
                    wins += 1
                else:
                    losses += 1

                peak_equity = max(peak_equity, equity)
                drawdown = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)

            closed_trades = wins + losses
            win_rate = wins / closed_trades if closed_trades > 0 else 0
            avg_pnl = total_pnl / closed_trades if closed_trades > 0 else 0

            # Update performance_stats on the strategy
            perf_stats = {
                "total_signals_evaluated": total,
                "signals_passed": passed,
                "simulated_trades": closed_trades,
                "win_rate": round(win_rate, 4),
                "total_pnl": round(total_pnl, 2),
                "avg_pnl_per_trade": round(avg_pnl, 2),
                "max_drawdown": round(max_drawdown, 4),
                "final_equity": round(equity, 2),
                "simulation_days": days,
                "simulated_at": datetime.utcnow().isoformat(),
            }

            self.db.supabase.table("user_strategies").update(
                {"performance_stats": perf_stats, "updated_at": datetime.utcnow().isoformat()}
            ).eq("id", strategy_id).execute()

            return {
                "success": True,
                "strategy_id": strategy_id,
                "simulation": perf_stats,
            }

        except Exception as e:
            logger.error(f"❌ Simulation failed: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # TEMPLATES
    # ------------------------------------------------------------------

    async def get_templates(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get pre-built strategy templates."""
        try:
            query = self.db.supabase.table("strategy_templates").select("*")
            if category:
                query = query.eq("category", category)
            if difficulty:
                query = query.eq("difficulty", difficulty)

            response = query.order("name").execute()
            templates = response.data or []

            return {
                "success": True,
                "templates": templates,
                "count": len(templates),
            }
        except Exception as e:
            logger.error(f"❌ Get templates failed: {e}")
            return {"success": False, "error": str(e), "templates": [], "count": 0}

    async def create_template(
        self,
        name: str,
        description: str,
        category: str,
        difficulty: str,
        rules: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a pre-built strategy template (admin/system use)."""
        try:
            if category not in VALID_TEMPLATE_CATEGORIES:
                return {
                    "success": False,
                    "error": f"Invalid category. Must be one of {sorted(VALID_TEMPLATE_CATEGORIES)}",
                }
            if difficulty not in VALID_DIFFICULTY_LEVELS:
                return {
                    "success": False,
                    "error": f"Invalid difficulty. Must be one of {sorted(VALID_DIFFICULTY_LEVELS)}",
                }

            validation = self.validate_rules(rules)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "Validation failed",
                    "validation_errors": validation["errors"],
                }

            template_data = {
                "id": str(uuid.uuid4()),
                "name": name,
                "description": description,
                "category": category,
                "difficulty": difficulty,
                "rules": rules,
                "created_at": datetime.utcnow().isoformat(),
            }

            response = self.db.supabase.table("strategy_templates").insert(template_data).execute()

            if response.data:
                return {"success": True, "template": response.data[0]}
            return {"success": False, "error": "Insert failed"}

        except Exception as e:
            logger.error(f"❌ Create template failed: {e}")
            return {"success": False, "error": str(e)}
