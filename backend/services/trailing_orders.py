"""
Trailing Orders Service - Dynamic exit orders that follow price movement.
Supports trailing stop-loss and trailing take-profit.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TrailingOrderType:
    TRAILING_STOP = "trailing_stop"
    TRAILING_TAKE_PROFIT = "trailing_take_profit"


class TrailingOrderStatus:
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"


class TrailingOrdersService:
    """Manages trailing stop and trailing take-profit orders."""

    def __init__(self, db):
        self.db = db

    async def create_trailing_order(
        self,
        user_id: str,
        asset: str,
        side: str,
        order_type: str,
        trail_percent: float,
        quantity: float,
        direction: str = "LONG",
        current_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create a trailing stop or trailing take-profit order."""
        try:
            if order_type not in (TrailingOrderType.TRAILING_STOP, TrailingOrderType.TRAILING_TAKE_PROFIT):
                return {"success": False, "error": "Invalid order type. Use trailing_stop or trailing_take_profit"}

            if trail_percent <= 0 or trail_percent > 50:
                return {"success": False, "error": "trail_percent must be between 0 and 50"}

            if quantity <= 0:
                return {"success": False, "error": "quantity must be positive"}

            if current_price is None:
                current_price = 0

            if side.upper() == "SELL":
                activation_price = current_price * (1 - trail_percent / 100)
                stop_price = activation_price
            else:
                activation_price = current_price * (1 + trail_percent / 100)
                stop_price = activation_price

            order_data = {
                "user_id": user_id,
                "asset": asset.upper(),
                "side": side.upper(),
                "order_type": order_type,
                "direction": direction.upper(),
                "trail_percent": trail_percent,
                "quantity": quantity,
                "activation_price": activation_price,
                "stop_price": stop_price,
                "highest_price": current_price if side.upper() == "SELL" else 0,
                "lowest_price": current_price if side.upper() == "BUY" else float("inf"),
                "status": TrailingOrderStatus.ACTIVE,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            response = self.db.supabase.table("trailing_orders").insert(order_data).execute()

            if response.data:
                order_id = response.data[0].get("id")
                logger.info(f"Trailing order created: {order_id} ({order_type} {asset})")
                return {"success": True, "order": response.data[0]}

            return {"success": False, "error": "Failed to create trailing order"}
        except Exception as e:
            logger.error(f"Failed to create trailing order: {e}")
            return {"success": False, "error": str(e)}

    async def update_trailing_order(
        self,
        order_id: str,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a trailing stop order."""
        try:
            existing = (
                self.db.supabase.table("trailing_orders")
                .select("*")
                .eq("id", order_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            if not existing.data:
                return {"success": False, "error": "Trailing order not found"}

            if existing.data.get("status") != TrailingOrderStatus.ACTIVE:
                return {"success": False, "error": "Can only update active orders"}

            allowed_fields = {"trail_percent", "quantity", "activation_price"}
            update_data = {k: v for k, v in updates.items() if k in allowed_fields}
            update_data["updated_at"] = datetime.utcnow().isoformat()

            response = (
                self.db.supabase.table("trailing_orders")
                .update(update_data)
                .eq("id", order_id)
                .execute()
            )

            if response.data:
                return {"success": True, "order": response.data[0]}
            return {"success": False, "error": "Update failed"}
        except Exception as e:
            logger.error(f"Failed to update trailing order: {e}")
            return {"success": False, "error": str(e)}

    async def cancel_trailing_order(
        self,
        order_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Cancel a trailing order."""
        try:
            existing = (
                self.db.supabase.table("trailing_orders")
                .select("*")
                .eq("id", order_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            if not existing.data:
                return {"success": False, "error": "Trailing order not found"}

            response = (
                self.db.supabase.table("trailing_orders")
                .update({
                    "status": TrailingOrderStatus.CANCELLED,
                    "updated_at": datetime.utcnow().isoformat(),
                })
                .eq("id", order_id)
                .execute()
            )

            if response.data:
                logger.info(f"Trailing order cancelled: {order_id}")
                return {"success": True, "order_id": order_id, "status": "CANCELLED"}
            return {"success": False, "error": "Cancel failed"}
        except Exception as e:
            logger.error(f"Failed to cancel trailing order: {e}")
            return {"success": False, "error": str(e)}

    async def list_trailing_orders(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List active trailing orders for a user."""
        try:
            query = (
                self.db.supabase.table("trailing_orders")
                .select("*")
                .eq("user_id", user_id)
            )
            if status_filter:
                query = query.eq("status", status_filter.upper())
            else:
                query = query.eq("status", TrailingOrderStatus.ACTIVE)

            response = query.order("created_at", desc=True).limit(limit).execute()
            orders = response.data or []

            return {
                "success": True,
                "orders": orders,
                "count": len(orders),
            }
        except Exception as e:
            logger.error(f"Failed to list trailing orders: {e}")
            return {"success": False, "error": str(e), "orders": [], "count": 0}

    async def evaluate_trailing_orders(
        self,
        asset: str,
        current_price: float,
    ) -> List[Dict[str, Any]]:
        """Evaluate all active trailing orders for an asset against current price.
        Returns list of triggered orders."""
        try:
            response = (
                self.db.supabase.table("trailing_orders")
                .select("*")
                .eq("asset", asset.upper())
                .eq("status", TrailingOrderStatus.ACTIVE)
                .execute()
            )
            orders = response.data or []
            triggered = []

            for order in orders:
                side = order.get("side", "SELL")
                trail_pct = float(order.get("trail_percent") or 0)
                highest = float(order.get("highest_price") or current_price)
                lowest = float(order.get("lowest_price") or current_price)

                should_trigger = False

                if side == "SELL":
                    if current_price > highest:
                        highest = current_price
                    activation_price = highest * (1 - trail_pct / 100)
                    if current_price <= activation_price:
                        should_trigger = True

                    self.db.supabase.table("trailing_orders").update({
                        "highest_price": highest,
                        "activation_price": activation_price,
                        "updated_at": datetime.utcnow().isoformat(),
                    }).eq("id", order.get("id")).execute()

                elif side == "BUY":
                    if current_price < lowest:
                        lowest = current_price
                    activation_price = lowest * (1 + trail_pct / 100)
                    if current_price >= activation_price:
                        should_trigger = True

                    self.db.supabase.table("trailing_orders").update({
                        "lowest_price": lowest,
                        "activation_price": activation_price,
                        "updated_at": datetime.utcnow().isoformat(),
                    }).eq("id", order.get("id")).execute()

                if should_trigger:
                    self.db.supabase.table("trailing_orders").update({
                        "status": TrailingOrderStatus.TRIGGERED,
                        "triggered_price": current_price,
                        "triggered_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }).eq("id", order.get("id")).execute()
                    triggered.append({
                        "order_id": order.get("id"),
                        "user_id": order.get("user_id"),
                        "asset": asset,
                        "side": side,
                        "order_type": order.get("order_type"),
                        "quantity": float(order.get("quantity") or 0),
                        "triggered_price": current_price,
                    })

            return triggered
        except Exception as e:
            logger.error(f"Failed to evaluate trailing orders: {e}")
            return []
