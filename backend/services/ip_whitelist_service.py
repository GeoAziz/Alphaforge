"""
IP Whitelisting Service - §16.2 Architecture Doc
Users with automated copy trading enabled can whitelist specific IP addresses
for API key usage. Non-whitelisted IP requests are rejected and logged.
"""

import logging
import ipaddress
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class IPWhitelistService:
    """
    Manages per-user IP whitelists for API key access.
    
    When a whitelisted API key is called from an unexpected IP:
    - Request is rejected
    - Alert sent to user via email and in-app notification
    - Event written to audit log
    """

    def __init__(self, db=None, notification_service=None, audit_log_service=None):
        self.db = db
        self.notification_service = notification_service
        self.audit_log_service = audit_log_service

    async def add_ip(
        self,
        user_id: str,
        ip_address: str,
        label: str = "",
    ) -> Dict[str, Any]:
        """Add an IP address to user's whitelist."""
        try:
            # Validate IP format
            ipaddress.ip_address(ip_address)
        except ValueError:
            return {"success": False, "error": f"Invalid IP address: {ip_address}"}

        try:
            record = {
                "user_id": user_id,
                "ip_address": ip_address,
                "label": label,
                "enabled": True,
                "created_at": datetime.utcnow().isoformat(),
            }

            response = self.db.supabase.table("ip_whitelist").insert(record).execute()

            if response.data:
                logger.info(f"✅ IP {ip_address} added to whitelist for user {user_id}")
                return {
                    "success": True,
                    "ip_id": response.data[0]["id"],
                    "ip_address": ip_address,
                }

            return {"success": False, "error": "Failed to add IP"}

        except Exception as e:
            logger.error(f"❌ Failed to add IP to whitelist: {e}")
            return {"success": False, "error": str(e)}

    async def remove_ip(self, user_id: str, ip_address: str) -> Dict[str, Any]:
        """Remove an IP from user's whitelist."""
        try:
            response = (
                self.db.supabase.table("ip_whitelist")
                .delete()
                .eq("user_id", user_id)
                .eq("ip_address", ip_address)
                .execute()
            )

            logger.info(f"✅ IP {ip_address} removed from whitelist for user {user_id}")
            return {"success": True, "removed": ip_address}

        except Exception as e:
            logger.error(f"❌ Failed to remove IP: {e}")
            return {"success": False, "error": str(e)}

    async def get_whitelist(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all whitelisted IPs for a user."""
        try:
            response = (
                self.db.supabase.table("ip_whitelist")
                .select("*")
                .eq("user_id", user_id)
                .eq("enabled", True)
                .execute()
            )
            return response.data or []

        except Exception as e:
            logger.error(f"❌ Failed to get whitelist: {e}")
            return []

    async def is_ip_whitelisted(self, user_id: str, ip_address: str) -> bool:
        """Check if an IP is whitelisted for a user. Returns True if no whitelist exists (permissive default)."""
        try:
            # If user has no whitelist entries, allow all IPs (permissive default)
            whitelist = await self.get_whitelist(user_id)
            if not whitelist:
                return True

            # Check exact match
            whitelisted_ips = {entry["ip_address"] for entry in whitelist}
            if ip_address in whitelisted_ips:
                return True

            # Check CIDR range matches
            try:
                client_ip = ipaddress.ip_address(ip_address)
                for entry in whitelist:
                    try:
                        network = ipaddress.ip_network(entry["ip_address"], strict=False)
                        if client_ip in network:
                            return True
                    except ValueError:
                        continue
            except ValueError:
                pass

            return False

        except Exception as e:
            logger.error(f"❌ IP whitelist check failed: {e}")
            return True  # Fail-open: allow if check fails

    async def validate_request(
        self,
        user_id: str,
        ip_address: str,
        endpoint: str = "",
    ) -> Dict[str, Any]:
        """
        Validate an incoming request against the user's IP whitelist.
        If rejected, sends alert and writes audit log.
        """
        allowed = await self.is_ip_whitelisted(user_id, ip_address)

        if allowed:
            return {"allowed": True, "ip": ip_address}

        # Request rejected - send alert and log
        logger.warning(
            f"🚫 IP {ip_address} NOT whitelisted for user {user_id} on {endpoint}"
        )

        # Send alert to user
        if self.notification_service:
            try:
                await self.notification_service.send_notification(
                    user_id=user_id,
                    title="Security Alert: Unknown IP Access",
                    message=(
                        f"An API request was made from IP {ip_address} "
                        f"which is not in your whitelist. "
                        f"Endpoint: {endpoint}. "
                        f"If this was you, add the IP to your whitelist."
                    ),
                    notification_type="security_alert",
                )
            except Exception as e:
                logger.error(f"Failed to send IP whitelist alert: {e}")

        # Write to audit log
        if self.audit_log_service:
            try:
                await self.audit_log_service.log_event(
                    user_id=user_id,
                    event_type="IP_WHITELIST_REJECTED",
                    details={
                        "ip_address": ip_address,
                        "endpoint": endpoint,
                        "action": "REQUEST_REJECTED",
                    },
                )
            except Exception as e:
                logger.error(f"Failed to audit IP whitelist rejection: {e}")

        return {
            "allowed": False,
            "ip": ip_address,
            "reason": "IP not in whitelist",
            "alert_sent": self.notification_service is not None,
        }

    async def enable_whitelist(self, user_id: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable IP whitelisting for a user."""
        try:
            response = (
                self.db.supabase.table("ip_whitelist")
                .update({"enabled": enabled})
                .eq("user_id", user_id)
                .execute()
            )

            status = "enabled" if enabled else "disabled"
            logger.info(f"✅ IP whitelist {status} for user {user_id}")
            return {"success": True, "enabled": enabled}

        except Exception as e:
            logger.error(f"❌ Failed to toggle whitelist: {e}")
            return {"success": False, "error": str(e)}

    async def get_whitelist_status(self, user_id: str) -> Dict[str, Any]:
        """Get whitelist status and entry count for a user."""
        whitelist = await self.get_whitelist(user_id)
        return {
            "user_id": user_id,
            "whitelist_enabled": len(whitelist) > 0,
            "entry_count": len(whitelist),
            "entries": whitelist,
        }


_ip_whitelist_service: Optional[IPWhitelistService] = None


def get_ip_whitelist_service(
    db=None, notification_service=None, audit_log_service=None
) -> IPWhitelistService:
    """Get or create the global IP whitelist service."""
    global _ip_whitelist_service
    if _ip_whitelist_service is None:
        _ip_whitelist_service = IPWhitelistService(db, notification_service, audit_log_service)
    return _ip_whitelist_service
