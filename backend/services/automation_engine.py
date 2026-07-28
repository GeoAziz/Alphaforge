"""
Automation Engine Service — Grid Bot & DCA Bot execution.
Manages bot lifecycle, order placement, fill monitoring, and kill-switch logic.
Supports both mock and live exchange modes.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

from config import ExchangeConfig, DevelopmentConfig, AutomationConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class JobType(str, Enum):
    GRID = "grid"
    DCA = "dca"


class JobStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EventType(str, Enum):
    JOB_CREATED = "job_created"
    JOB_STOPPED = "job_stopped"
    JOB_PAUSED = "job_paused"
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FAILED = "order_failed"
    GRID_REBALANCED = "grid_rebalanced"
    DCA_EXECUTED = "dca_executed"
    ERROR = "error"
    KILL_SWITCH = "kill_switch"


# ---------------------------------------------------------------------------
# Exchange connector (thin wrapper around LiveTradingEngine connectors)
# ---------------------------------------------------------------------------

class _MockExchange:
    """Mock exchange for development / testing."""

    async def place_order(self, symbol: str, side: str, quantity: float,
                          order_type: str = "LIMIT", price: float = None) -> Dict[str, Any]:
        order_id = f"mock-{uuid.uuid4().hex[:12]}"
        return {
            "success": True,
            "order": {
                "orderId": order_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "status": "FILLED" if order_type == "MARKET" else "NEW",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        return {"success": True, "order": {"orderId": order_id, "status": "CANCELLED"}}

    async def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        return []

    async def get_price(self, symbol: str) -> float:
        return 50000.0


# ---------------------------------------------------------------------------
# Automation Engine
# ---------------------------------------------------------------------------

class AutomationEngine:
    """
    Core automation engine for Grid Bot and DCA Bot.

    Responsibilities:
      - CRUD for automation jobs (create, pause, stop, status)
      - Grid Bot: place initial grid, rebalance after fills, place counter-orders
      - DCA Bot: execute recurring buys on schedule
      - Kill switch: cancel all open orders and stop the job
      - Event logging for every action
    """

    def __init__(self, db):
        self.db = db
        self._running_jobs: Dict[str, asyncio.Task] = {}
        self._exchange_cache: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Exchange helpers
    # ------------------------------------------------------------------

    def _get_exchange(self, exchange_id: str):
        if exchange_id in self._exchange_cache:
            return self._exchange_cache[exchange_id]

        if DevelopmentConfig.MOCK_EXCHANGE or not ExchangeConfig.LIVE_TRADING_ENABLED:
            connector = _MockExchange()
        else:
            try:
                from services.live_trading_engine import LiveTradingEngine
                engine = LiveTradingEngine()
                connector = engine.connectors.get(exchange_id)
                if not connector:
                    logger.warning(f"Exchange {exchange_id} not configured, using mock")
                    connector = _MockExchange()
            except Exception as e:
                logger.error(f"Failed to init exchange {exchange_id}: {e}")
                connector = _MockExchange()

        self._exchange_cache[exchange_id] = connector
        return connector

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def _insert(self, table: str, data: dict) -> dict:
        try:
            resp = self.db.supabase.table(table).insert(data).execute()
            return resp.data[0] if resp.data else data
        except Exception as e:
            logger.error(f"DB insert to {table} failed: {e}")
            return data

    def _update(self, table: str, data: dict, filters: dict) -> dict:
        try:
            query = self.db.supabase.table(table).update(data)
            for k, v in filters.items():
                query = query.eq(k, v)
            resp = query.execute()
            return resp.data[0] if resp.data else data
        except Exception as e:
            logger.error(f"DB update on {table} failed: {e}")
            return data

    def _select(self, table: str, filters: dict = None, limit: int = None) -> list:
        try:
            query = self.db.supabase.table(table).select("*")
            if filters:
                for k, v in filters.items():
                    query = query.eq(k, v)
            if limit:
                query = query.limit(limit)
            resp = query.execute()
            return resp.data or []
        except Exception as e:
            logger.error(f"DB select from {table} failed: {e}")
            return []

    def _log_event(self, job_id: str, event_type: EventType, details: dict = None):
        self._insert("automation_events", {
            "automation_job_id": job_id,
            "event_type": event_type.value,
            "details": details or {},
            "created_at": datetime.utcnow().isoformat(),
        })

    # ------------------------------------------------------------------
    # Job CRUD
    # ------------------------------------------------------------------

    async def create_grid_bot(
        self,
        user_id: str,
        exchange_id: str,
        symbol: str,
        lower_bound: float,
        upper_bound: float,
        grid_levels: int,
        order_size: float,
    ) -> Dict[str, Any]:
        if not AutomationConfig.ENABLED:
            return {"success": False, "error": "Automation feature is disabled"}

        if grid_levels < 2 or grid_levels > AutomationConfig.MAX_GRID_LEVELS:
            return {"success": False, "error": f"Grid levels must be 2-{AutomationConfig.MAX_GRID_LEVELS}"}
        if upper_bound <= lower_bound:
            return {"success": False, "error": "Upper bound must be greater than lower bound"}
        if order_size * grid_levels > AutomationConfig.MAX_TOTAL_INVESTMENT:
            return {"success": False, "error": f"Total investment exceeds ${AutomationConfig.MAX_TOTAL_INVESTMENT} limit"}

        job_id = str(uuid.uuid4())
        config = {
            "lowerBound": lower_bound,
            "upperBound": upper_bound,
            "gridLevels": grid_levels,
            "orderSize": order_size,
            "totalInvestment": order_size * grid_levels,
        }

        job = self._insert("automation_jobs", {
            "id": job_id,
            "user_id": user_id,
            "job_type": JobType.GRID.value,
            "exchange_id": exchange_id,
            "symbol": symbol,
            "status": JobStatus.RUNNING.value,
            "config": config,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })

        self._log_event(job_id, EventType.JOB_CREATED, {"type": "grid", "config": config})

        # Place initial grid orders
        grid_orders = self._compute_grid_prices(lower_bound, upper_bound, grid_levels)
        placed_orders = []
        exchange = self._get_exchange(exchange_id)

        for i, price in enumerate(grid_orders):
            side = "BUY" if price <= (lower_bound + upper_bound) / 2 else "SELL"
            result = await exchange.place_order(
                symbol=symbol,
                side=side,
                quantity=order_size / price if price > 0 else 0,
                order_type="LIMIT",
                price=price,
            )

            order_id = result.get("order", {}).get("orderId", f"pending-{i}")
            order_record = self._insert("automation_orders", {
                "id": str(uuid.uuid4()),
                "automation_job_id": job_id,
                "order_id": order_id,
                "status": "filled" if result.get("order", {}).get("status") == "FILLED" else "pending",
                "filled_amount": order_size / price if result.get("order", {}).get("status") == "FILLED" else 0,
                "avg_price": price if result.get("order", {}).get("status") == "FILLED" else 0,
                "side": side,
                "price": price,
                "created_at": datetime.utcnow().isoformat(),
            })
            placed_orders.append(order_record)

            self._log_event(job_id, EventType.ORDER_PLACED, {
                "order_id": order_id, "side": side, "price": price,
            })

        logger.info(f"✅ Grid bot {job_id} created with {len(placed_orders)} orders on {exchange_id}")

        return {
            "success": True,
            "job_id": job_id,
            "status": JobStatus.RUNNING.value,
            "config": config,
            "orders_placed": len(placed_orders),
        }

    async def create_dca_bot(
        self,
        user_id: str,
        exchange_id: str,
        symbol: str,
        investment_amount: float,
        frequency: str = "weekly",
        start_time: str = None,
    ) -> Dict[str, Any]:
        if not AutomationConfig.ENABLED:
            return {"success": False, "error": "Automation feature is disabled"}

        if investment_amount <= 0 or investment_amount > AutomationConfig.MAX_DCA_SINGLE_INVESTMENT:
            return {"success": False, "error": f"Investment must be $0-${AutomationConfig.MAX_DCA_SINGLE_INVESTMENT}"}
        if frequency not in ("daily", "weekly", "monthly"):
            return {"success": False, "error": "Frequency must be daily, weekly, or monthly"}

        if start_time:
            try:
                next_exec = datetime.fromisoformat(start_time)
            except ValueError:
                next_exec = self._next_execution_time(frequency)
        else:
            next_exec = self._next_execution_time(frequency)

        job_id = str(uuid.uuid4())
        config = {
            "symbol": symbol,
            "investmentAmount": investment_amount,
            "frequency": frequency,
            "nextExecutionTime": next_exec.isoformat(),
        }

        job = self._insert("automation_jobs", {
            "id": job_id,
            "user_id": user_id,
            "job_type": JobType.DCA.value,
            "exchange_id": exchange_id,
            "symbol": symbol,
            "status": JobStatus.RUNNING.value,
            "config": config,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })

        self._log_event(job_id, EventType.JOB_CREATED, {"type": "dca", "config": config})

        logger.info(f"✅ DCA bot {job_id} created: ${investment_amount} {frequency} on {exchange_id}")

        return {
            "success": True,
            "job_id": job_id,
            "status": JobStatus.RUNNING.value,
            "config": config,
        }

    async def stop_job(self, job_id: str, user_id: str) -> Dict[str, Any]:
        jobs = self._select("automation_jobs", {"id": job_id, "user_id": user_id}, limit=1)
        if not jobs:
            return {"success": False, "error": "Job not found"}

        job = jobs[0]
        if job["status"] == JobStatus.STOPPED.value:
            return {"success": False, "error": "Job already stopped"}

        # Cancel all open orders on exchange
        exchange = self._get_exchange(job["exchange_id"])
        open_orders = self._select("automation_orders", {
            "automation_job_id": job_id,
        })
        cancelled = 0
        for order in open_orders:
            if order.get("status") in ("pending", "partially_filled"):
                try:
                    await exchange.cancel_order(order["order_id"], job["symbol"])
                    self._update("automation_orders", {"status": "cancelled"}, {"id": order["id"]})
                    self._log_event(job_id, EventType.ORDER_CANCELLED, {"order_id": order["order_id"]})
                    cancelled += 1
                except Exception as e:
                    logger.error(f"Failed to cancel order {order['order_id']}: {e}")

        # Update job status
        self._update("automation_jobs", {
            "status": JobStatus.STOPPED.value,
            "updated_at": datetime.utcnow().isoformat(),
        }, {"id": job_id})

        # Cancel running task
        if job_id in self._running_jobs:
            self._running_jobs[job_id].cancel()
            del self._running_jobs[job_id]

        self._log_event(job_id, EventType.KILL_SWITCH, {"cancelled_orders": cancelled})

        logger.info(f"🛑 Kill switch activated for job {job_id}: {cancelled} orders cancelled")

        return {
            "success": True,
            "job_id": job_id,
            "status": JobStatus.STOPPED.value,
            "orders_cancelled": cancelled,
        }

    async def pause_job(self, job_id: str, user_id: str) -> Dict[str, Any]:
        jobs = self._select("automation_jobs", {"id": job_id, "user_id": user_id}, limit=1)
        if not jobs:
            return {"success": False, "error": "Job not found"}

        self._update("automation_jobs", {
            "status": JobStatus.PAUSED.value,
            "updated_at": datetime.utcnow().isoformat(),
        }, {"id": job_id})

        self._log_event(job_id, EventType.JOB_PAUSED)

        return {"success": True, "job_id": job_id, "status": JobStatus.PAUSED.value}

    async def resume_job(self, job_id: str, user_id: str) -> Dict[str, Any]:
        jobs = self._select("automation_jobs", {"id": job_id, "user_id": user_id}, limit=1)
        if not jobs:
            return {"success": False, "error": "Job not found"}

        self._update("automation_jobs", {
            "status": JobStatus.RUNNING.value,
            "updated_at": datetime.utcnow().isoformat(),
        }, {"id": job_id})

        return {"success": True, "job_id": job_id, "status": JobStatus.RUNNING.value}

    # ------------------------------------------------------------------
    # Status & P&L
    # ------------------------------------------------------------------

    async def get_job_status(self, job_id: str, user_id: str) -> Dict[str, Any]:
        jobs = self._select("automation_jobs", {"id": job_id, "user_id": user_id}, limit=1)
        if not jobs:
            return {"success": False, "error": "Job not found"}

        job = jobs[0]
        orders = self._select("automation_orders", {"automation_job_id": job_id})

        total_invested = sum(
            float(o.get("filled_amount", 0)) * float(o.get("avg_price", 0))
            for o in orders if o.get("status") == "filled"
        )
        filled_count = sum(1 for o in orders if o.get("status") == "filled")
        total_count = len(orders)

        config = job.get("config", {})
        total_investment_budget = float(config.get("totalInvestment", config.get("investmentAmount", 0)))

        return {
            "success": True,
            "job": {
                "id": job["id"],
                "job_type": job["job_type"],
                "exchange_id": job["exchange_id"],
                "symbol": job["symbol"],
                "status": job["status"],
                "config": config,
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
            },
            "stats": {
                "total_orders": total_count,
                "filled_orders": filled_count,
                "pending_orders": total_count - filled_count,
                "total_invested": total_invested,
                "investment_budget": total_investment_budget,
                "utilization_pct": (total_invested / total_investment_budget * 100) if total_investment_budget > 0 else 0,
            },
        }

    async def get_job_orders(self, job_id: str, user_id: str) -> Dict[str, Any]:
        jobs = self._select("automation_jobs", {"id": job_id, "user_id": user_id}, limit=1)
        if not jobs:
            return {"success": False, "error": "Job not found"}

        orders = self._select("automation_orders", {"automation_job_id": job_id})

        return {
            "success": True,
            "orders": orders,
            "count": len(orders),
        }

    async def list_user_jobs(self, user_id: str) -> Dict[str, Any]:
        jobs = self._select("automation_jobs", {"user_id": user_id})

        result = []
        for job in jobs:
            orders = self._select("automation_orders", {"automation_job_id": job["id"]})
            filled = [o for o in orders if o.get("status") == "filled"]
            result.append({
                "id": job["id"],
                "job_type": job["job_type"],
                "exchange_id": job["exchange_id"],
                "symbol": job["symbol"],
                "status": job["status"],
                "config": job.get("config", {}),
                "total_orders": len(orders),
                "filled_orders": len(filled),
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
            })

        return {
            "success": True,
            "jobs": result,
            "count": len(result),
        }

    async def get_job_events(self, job_id: str, user_id: str, limit: int = 50) -> Dict[str, Any]:
        jobs = self._select("automation_jobs", {"id": job_id, "user_id": user_id}, limit=1)
        if not jobs:
            return {"success": False, "error": "Job not found"}

        events = self._select("automation_events", {"automation_job_id": job_id}, limit=limit)

        return {
            "success": True,
            "events": events,
            "count": len(events),
        }

    # ------------------------------------------------------------------
    # Grid Bot internal logic
    # ------------------------------------------------------------------

    def _compute_grid_prices(self, lower: float, upper: float, levels: int) -> List[float]:
        step = (upper - lower) / (levels - 1)
        return [round(lower + i * step, 2) for i in range(levels)]

    async def _on_grid_fill(self, job_id: str, order: dict, exchange):
        """When a grid order fills, place the counter-order on the opposite side."""
        config_resp = self._select("automation_jobs", {"id": job_id}, limit=1)
        if not config_resp:
            return
        config = config_resp[0].get("config", {})
        symbol = config_resp[0].get("symbol", "")
        order_size = config.get("orderSize", 0)

        filled_price = float(order.get("avg_price", 0))
        filled_side = order.get("side", "BUY")

        if filled_side == "BUY":
            counter_side = "SELL"
            counter_price = filled_price * (1 + 2.0 / config.get("gridLevels", 10))
        else:
            counter_side = "BUY"
            counter_price = filled_price * (1 - 2.0 / config.get("gridLevels", 10))

        counter_price = round(counter_price, 2)

        result = await exchange.place_order(
            symbol=symbol,
            side=counter_side,
            quantity=order_size / counter_price if counter_price > 0 else 0,
            order_type="LIMIT",
            price=counter_price,
        )

        order_id = result.get("order", {}).get("orderId", f"counter-{uuid.uuid4().hex[:8]}")
        self._insert("automation_orders", {
            "id": str(uuid.uuid4()),
            "automation_job_id": job_id,
            "order_id": order_id,
            "status": "filled" if result.get("order", {}).get("status") == "FILLED" else "pending",
            "filled_amount": order_size / counter_price if result.get("order", {}).get("status") == "FILLED" else 0,
            "avg_price": counter_price if result.get("order", {}).get("status") == "FILLED" else 0,
            "side": counter_side,
            "price": counter_price,
            "created_at": datetime.utcnow().isoformat(),
        })

        self._log_event(job_id, EventType.GRID_REBALANCED, {
            "original_order": order.get("order_id"),
            "counter_order": order_id,
            "counter_side": counter_side,
            "counter_price": counter_price,
        })

    # ------------------------------------------------------------------
    # DCA Bot internal logic
    # ------------------------------------------------------------------

    async def _execute_dca(self, job_id: str):
        jobs = self._select("automation_jobs", {"id": job_id}, limit=1)
        if not jobs or jobs[0]["status"] != JobStatus.RUNNING.value:
            return

        job = jobs[0]
        config = job.get("config", {})
        symbol = job["symbol"]
        investment_amount = float(config.get("investmentAmount", 0))
        exchange = self._get_exchange(job["exchange_id"])

        exchange_symbol = symbol if symbol.endswith("USDT") else f"{symbol}USDT"

        # Get current price
        try:
            current_price = await exchange.get_price(exchange_symbol)
        except Exception:
            current_price = 50000.0

        quantity = investment_amount / current_price if current_price > 0 else 0

        result = await exchange.place_order(
            symbol=exchange_symbol,
            side="BUY",
            quantity=quantity,
            order_type="MARKET",
        )

        order_id = result.get("order", {}).get("orderId", f"dca-{uuid.uuid4().hex[:8]}")
        filled = result.get("order", {}).get("status") == "FILLED"

        self._insert("automation_orders", {
            "id": str(uuid.uuid4()),
            "automation_job_id": job_id,
            "order_id": order_id,
            "status": "filled" if filled else "pending",
            "filled_amount": quantity if filled else 0,
            "avg_price": current_price if filled else 0,
            "side": "BUY",
            "price": current_price,
            "created_at": datetime.utcnow().isoformat(),
        })

        # Update next execution time
        frequency = config.get("frequency", "weekly")
        next_exec = self._next_execution_time(frequency)
        config["nextExecutionTime"] = next_exec.isoformat()
        self._update("automation_jobs", {
            "config": config,
            "updated_at": datetime.utcnow().isoformat(),
        }, {"id": job_id})

        self._log_event(job_id, EventType.DCA_EXECUTED, {
            "amount": investment_amount,
            "price": current_price,
            "quantity": quantity,
            "order_id": order_id,
            "next_execution": next_exec.isoformat(),
        })

        logger.info(f"✅ DCA executed for {job_id}: ${investment_amount} @ ${current_price}")

    def _next_execution_time(self, frequency: str) -> datetime:
        now = datetime.utcnow()
        if frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            month = now.month % 12 + 1
            year = now.year + (1 if month == 1 else 0)
            day = min(now.day, 28)
            return datetime(year, month, day, now.hour, now.minute, now.second)
        return now + timedelta(weeks=1)

    # ------------------------------------------------------------------
    # Background tick (called by scheduler / startup)
    # ------------------------------------------------------------------

    async def tick(self):
        """Periodic tick — check DCA schedules and monitor open orders."""
        try:
            running_jobs = self._select("automation_jobs", {"status": JobStatus.RUNNING.value})
            for job in running_jobs:
                job_id = job["id"]
                job_type = job.get("job_type")

                if job_type == JobType.DCA.value:
                    config = job.get("config", {})
                    next_exec_str = config.get("nextExecutionTime")
                    if next_exec_str:
                        try:
                            next_exec = datetime.fromisoformat(next_exec_str)
                        except ValueError:
                            continue
                        if datetime.utcnow() >= next_exec:
                            await self._execute_dca(job_id)

                elif job_type == JobType.GRID.value:
                    open_orders = self._select("automation_orders", {
                        "automation_job_id": job_id,
                    })
                    pending = [o for o in open_orders if o.get("status") == "pending"]
                    exchange = self._get_exchange(job["exchange_id"])

                    for order in pending:
                        try:
                            open_on_exchange = await exchange.get_open_orders(job["symbol"])
                            found = any(
                                str(o.get("orderId", o.get("order_id"))) == order["order_id"]
                                for o in open_on_exchange
                            )
                            if not found:
                                # Order was filled off-cycle
                                self._update("automation_orders", {
                                    "status": "filled",
                                    "filled_amount": float(order.get("price", 0)),
                                    "avg_price": float(order.get("price", 0)),
                                }, {"id": order["id"]})

                                self._log_event(job_id, EventType.ORDER_FILLED, {
                                    "order_id": order["order_id"],
                                })

                                await self._on_grid_fill(job_id, {
                                    **order,
                                    "status": "filled",
                                    "avg_price": order.get("price"),
                                }, exchange)
                        except Exception as e:
                            logger.error(f"Grid monitor error for {order['order_id']}: {e}")
                            self._log_event(job_id, EventType.ERROR, {
                                "order_id": order["order_id"],
                                "error": str(e),
                            })

        except Exception as e:
            logger.error(f"Automation tick failed: {e}")
