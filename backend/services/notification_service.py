"""
Notification Service - Dedicated multi-channel notification delivery.
Architecture Doc §15: Web push, Telegram, Discord, Email.
"""

import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import os
import asyncio
import urllib.request

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    WEB_PUSH = "web_push"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"


class NotificationType(str, Enum):
    SIGNAL_ALERT = "signal_alert"
    TRADE_EXECUTED = "trade_executed"
    TRADE_CLOSED = "trade_closed"
    RISK_WARNING = "risk_warning"
    KYC_UPDATE = "kyc_update"
    SUBSCRIPTION = "subscription"
    SYSTEM = "system"


class NotificationService:
    """Multi-channel notification delivery service."""

    def __init__(self, db):
        self.db = db
        self._config = {
            "sendgrid_api_key": os.getenv("SENDGRID_API_KEY"),
            "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "discord_webhook_url": os.getenv("DISCORD_WEBHOOK_URL"),
            "vapid_private_key": os.getenv("VAPID_PRIVATE_KEY"),
            "vapid_public_key": os.getenv("VAPID_PUBLIC_KEY"),
            "vapid_claims_sub": os.getenv("VAPID_CLAIMS_SUB", "mailto:admin@alphaforge.io"),
        }

    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = NotificationType.SYSTEM.value,
        channels: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send notification across specified channels."""
        if channels is None:
            channels = self._get_default_channels(notification_type)

        results = {}
        for channel in channels:
            try:
                if channel == NotificationChannel.WEB_PUSH.value:
                    results["web_push"] = await self.send_web_push(user_id, title, message, data)
                elif channel == NotificationChannel.TELEGRAM.value:
                    results["telegram"] = await self.send_telegram(user_id, message)
                elif channel == NotificationChannel.DISCORD.value:
                    results["discord"] = await self.send_discord(
                        self._config["discord_webhook_url"], f"**{title}**\n{message}"
                    )
                elif channel == NotificationChannel.EMAIL.value:
                    results["email"] = await self.send_email(user_id, title, message)
            except Exception as e:
                logger.error(f"Failed to send via {channel}: {e}")
                results[channel] = {"success": False, "error": str(e)}

        await self._store_notification(user_id, title, message, notification_type, data)
        return {"success": True, "channels": results}

    async def send_web_push(
        self, user_id: str, title: str, body: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send web push notification."""
        prefs = await self.get_user_preferences(user_id)
        if not prefs.get("web_push_enabled", True):
            return {"success": False, "reason": "web_push_disabled"}

        endpoint = prefs.get("push_endpoint")
        if not endpoint:
            return {"success": False, "reason": "no_push_subscription"}

        payload = json.dumps({"title": title, "body": body, "data": data or {}})

        if not self._config["vapid_private_key"]:
            logger.warning("VAPID keys not configured, skipping web push")
            return {"success": False, "reason": "vapid_not_configured"}

        try:
            import webpush
            webpush.webpush(
                subscription_info=endpoint,
                data=payload,
                vapid_private_key=self._config["vapid_private_key"],
                vapid_claims={"sub": self._config["vapid_claims_sub"]},
            )
            return {"success": True}
        except ImportError:
            logger.warning("py-vapid not installed")
            return {"success": False, "reason": "dependency_missing"}
        except Exception as e:
            logger.error(f"Web push failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_telegram(self, user_id: str, message: str) -> Dict[str, Any]:
        """Send Telegram notification."""
        token = self._config["telegram_bot_token"]
        if not token:
            return {"success": False, "reason": "telegram_not_configured"}

        prefs = await self.get_user_preferences(user_id)
        chat_id = prefs.get("telegram_chat_id")
        if not chat_id:
            return {"success": False, "reason": "no_telegram_chat_id"}

        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = json.dumps({
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }).encode("utf-8")

            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return {"success": True}
            return {"success": False, "error": f"HTTP {resp.status}"}
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_discord(self, webhook_url: str, message: str) -> Dict[str, Any]:
        """Send Discord webhook notification."""
        if not webhook_url:
            return {"success": False, "reason": "discord_not_configured"}

        try:
            payload = json.dumps({"content": message}).encode("utf-8")
            req = urllib.request.Request(
                webhook_url, data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 204):
                    return {"success": True}
            return {"success": False, "error": f"HTTP {resp.status}"}
        except Exception as e:
            logger.error(f"Discord send failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_email(
        self, user_id: str, subject: str, body: str, is_html: bool = False
    ) -> Dict[str, Any]:
        """Send email notification via SendGrid."""
        api_key = self._config["sendgrid_api_key"]
        if not api_key:
            return {"success": False, "reason": "sendgrid_not_configured"}

        try:
            user_response = self.db.supabase.table("users").select("email").eq("id", user_id).execute()
            if not user_response.data:
                return {"success": False, "reason": "user_not_found"}

            email = user_response.data[0]["email"]
            content_type = "text/html" if is_html else "text/plain"

            payload = json.dumps({
                "personalizations": [{"to": [{"email": email}]}],
                "from": {"email": "alerts@alphaforge.io", "name": "AlphaForge"},
                "subject": subject,
                "content": [{"type": content_type, "value": body}],
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.sendgrid.com/v3/mail/send",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 202):
                    return {"success": True}
            return {"success": False, "error": f"HTTP {resp.status}"}
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user notification preferences."""
        try:
            response = self.db.supabase.table("notifications").select("*").eq("user_id", user_id).execute()
            if response.data:
                return response.data[0].get("preferences", {})
            return {"web_push_enabled": True, "telegram_enabled": True, "email_enabled": True}
        except Exception:
            return {}

    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user notification preferences."""
        try:
            existing = self.db.supabase.table("notifications").select("*").eq("user_id", user_id).execute()
            if existing.data:
                self.db.supabase.table("notifications").update({
                    "preferences": preferences,
                    "updated_at": datetime.utcnow().isoformat(),
                }).eq("user_id", user_id).execute()
            else:
                self.db.supabase.table("notifications").insert({
                    "user_id": user_id,
                    "preferences": preferences,
                }).execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_notification_history(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get notification history for a user."""
        try:
            response = (
                self.db.supabase.table("push_notifications")
                .select("*")
                .eq("user_id", user_id)
                .order("sent_at", desc=True)
                .limit(limit)
                .execute()
            )
            return {"success": True, "notifications": response.data or [], "count": len(response.data or [])}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _store_notification(
        self, user_id: str, title: str, message: str,
        notification_type: str, data: Optional[Dict] = None,
    ):
        """Store notification in database."""
        try:
            self.db.supabase.table("push_notifications").insert({
                "user_id": user_id,
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "data": data or {},
                "sent_at": datetime.utcnow().isoformat(),
            }).execute()
        except Exception as e:
            logger.error(f"Failed to store notification: {e}")

    def _get_default_channels(self, notification_type: str) -> List[str]:
        """Get default channels for a notification type."""
        defaults = {
            NotificationType.SIGNAL_ALERT.value: ["web_push", "email"],
            NotificationType.TRADE_EXECUTED.value: ["email"],
            NotificationType.RISK_WARNING.value: ["web_push", "email"],
            NotificationType.KYC_UPDATE.value: ["email"],
            NotificationType.SYSTEM.value: ["email"],
        }
        return defaults.get(notification_type, ["email"])
