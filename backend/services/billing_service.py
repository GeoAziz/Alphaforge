"""
Subscription Billing Service - Stripe-backed subscription billing (PRD §16,
Option A: Subscription-First).

Tiers (PRD §16 / §18):
  Basic ($39/mo)  - Phase 1 MVP, 4-6 signals/week, 2 exchanges
  Pro   ($99/mo)  - Phase 2, 8+ signals/week, 4 exchanges
  VIP   ($199/mo) - Phase 3, unlimited signals, all exchanges

New users get a 7-day paper-trading-only trial (PRD Decision 4) before the
first charge — Stripe's built-in trial_period_days handles this natively.
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

from config import MarketplaceConfig as Config

logger = logging.getLogger(__name__)

# Stripe price IDs per tier — set these once the products/prices are created
# in the Stripe dashboard. Left unset (None) until configured; checkout will
# fail closed with a clear error rather than silently using the wrong price.
TIER_PRICE_IDS = {
    "basic": os.getenv("STRIPE_PRICE_BASIC"),
    "pro": os.getenv("STRIPE_PRICE_PRO"),
    "vip": os.getenv("STRIPE_PRICE_VIP"),
}

TRIAL_PERIOD_DAYS = 7

TIER_LIMITS = {
    "free": {
        "max_exchanges": 1,
        "max_signals_per_week": 0,
        "max_leverage": 1.0,
        "api_access": False,
        "paper_trading": False,
    },
    "basic": {
        "max_exchanges": 2,
        "max_signals_per_week": 6,
        "max_leverage": 2.0,
        "api_access": False,
        "paper_trading": True,
    },
    "pro": {
        "max_exchanges": 4,
        "max_signals_per_week": 10,
        "max_leverage": 5.0,
        "api_access": False,
        "paper_trading": True,
    },
    "vip": {
        "max_exchanges": 10,
        "max_signals_per_week": None,  # unlimited
        "max_leverage": 10.0,
        "api_access": True,
        "paper_trading": True,
    },
}


class BillingService:
    """Manages Stripe Checkout sessions, webhooks, and subscription state."""

    def __init__(self, db):
        self.db = db
        self.enabled = bool(Config.STRIPE_API_KEY) and not Config.STRIPE_API_KEY.startswith("sk_placeholder")
        self._stripe = None
        if self.enabled:
            try:
                import stripe
                stripe.api_key = Config.STRIPE_API_KEY
                self._stripe = stripe
                logger.info("✅ Stripe billing client initialized")
            except ImportError:
                logger.error("❌ 'stripe' package not installed — billing disabled")
                self.enabled = False
        else:
            logger.warning("⚠️ Stripe API key not configured — billing disabled (checkout will fail closed)")

    async def create_checkout_session(
        self,
        user_id: str,
        email: str,
        tier: str,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout session for a subscription, with the
        7-day paper-trading trial baked in."""
        if not self.enabled:
            return {"success": False, "error": "Billing is not configured"}

        price_id = TIER_PRICE_IDS.get(tier)
        if not price_id:
            return {"success": False, "error": f"No Stripe price configured for tier '{tier}'"}

        try:
            user_row = self.db.supabase.table("users").select("stripe_customer_id").eq("id", user_id).execute()
            existing_customer_id = None
            if user_row.data:
                existing_customer_id = user_row.data[0].get("stripe_customer_id")

            session_params = {
                "mode": "subscription",
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "client_reference_id": user_id,
                "subscription_data": {
                    "trial_period_days": TRIAL_PERIOD_DAYS,
                    "metadata": {"user_id": user_id, "tier": tier},
                },
                "metadata": {"user_id": user_id, "tier": tier},
            }
            if existing_customer_id:
                session_params["customer"] = existing_customer_id
            else:
                session_params["customer_email"] = email

            session = self._stripe.checkout.Session.create(**session_params)
            return {"success": True, "checkout_url": session.url, "session_id": session.id}
        except Exception as e:
            logger.error(f"❌ Checkout session creation failed for {user_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_tier_limits(self, user_id: str) -> Dict[str, Any]:
        """Get the calling user's subscription tier and the limits it unlocks."""
        status = await self.get_subscription_status(user_id)
        if not status.get("success"):
            tier = "free"
        else:
            tier = status.get("tier", "free").lower()
            if tier not in TIER_LIMITS:
                tier = "free"
        return {"tier": tier, "limits": TIER_LIMITS.get(tier, TIER_LIMITS["free"])}

    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Get a user's current subscription tier/status from our DB (source
        of truth is kept in sync via webhooks, not queried live from Stripe
        on every request)."""
        try:
            response = (
                self.db.supabase.table("users")
                .select("subscription_tier, subscription_status, trial_ends_at, current_period_end")
                .eq("id", user_id)
                .execute()
            )
            if not response.data:
                return {"success": False, "error": "User not found"}

            row = response.data[0]
            return {
                "success": True,
                "tier": row.get("subscription_tier", "free"),
                "status": row.get("subscription_status", "none"),
                "trial_ends_at": row.get("trial_ends_at"),
                "current_period_end": row.get("current_period_end"),
            }
        except Exception as e:
            logger.error(f"❌ Failed to fetch subscription status for {user_id}: {e}")
            return {"success": False, "error": str(e)}

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> Optional[Dict[str, Any]]:
        """Verify a Stripe webhook signature and return the parsed event, or
        None if invalid. Never trust webhook payloads without this check —
        anyone could otherwise POST a fake 'subscription active' event."""
        if not self.enabled:
            return None
        webhook_secret = Config.STRIPE_WEBHOOK_SECRET
        if not webhook_secret:
            logger.error("❌ STRIPE_WEBHOOK_SECRET not configured — refusing to process webhook")
            return None
        try:
            return self._stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except Exception as e:
            logger.warning(f"❌ Stripe webhook signature verification failed: {e}")
            return None

    async def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a verified Stripe event to our subscription state."""
        event_type = event.get("type", "")
        data = event.get("data", {}).get("object", {})
        event_id = event.get("id")

        try:
            if event_type == "checkout.session.completed":
                user_id = data.get("client_reference_id") or data.get("metadata", {}).get("user_id")
                customer_id = data.get("customer")
                subscription_id = data.get("subscription")
                tier = data.get("metadata", {}).get("tier", "basic")
                if user_id:
                    self.db.supabase.table("users").update({
                        "stripe_customer_id": customer_id,
                        "stripe_subscription_id": subscription_id,
                        "subscription_tier": tier,
                        "subscription_status": "trialing",
                    }).eq("id", user_id).execute()

            elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
                subscription_id = data.get("id")
                status = data.get("status")
                period_end = data.get("current_period_end")
                period_end_iso = (
                    datetime.utcfromtimestamp(period_end).isoformat() if period_end else None
                )
                self.db.supabase.table("users").update({
                    "subscription_status": status,
                    "current_period_end": period_end_iso,
                }).eq("stripe_subscription_id", subscription_id).execute()

            elif event_type == "customer.subscription.deleted":
                subscription_id = data.get("id")
                self.db.supabase.table("users").update({
                    "subscription_status": "canceled",
                    "subscription_tier": "free",
                }).eq("stripe_subscription_id", subscription_id).execute()

            user_id_for_log = data.get("client_reference_id") or data.get("metadata", {}).get("user_id")
            self.db.supabase.table("billing_events").insert({
                "user_id": user_id_for_log,
                "stripe_event_id": event_id,
                "event_type": event_type,
                "payload": event,
            }).execute()

            return {"success": True, "event_type": event_type}
        except Exception as e:
            logger.error(f"❌ Failed to process billing webhook {event_type}: {e}")
            return {"success": False, "error": str(e)}
