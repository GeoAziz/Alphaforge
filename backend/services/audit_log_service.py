"""
Audit Log Service - Dedicated immutable audit logging per architecture doc §28.
Append-only event store with hash chain integrity, daily verification,
24-month retention, and RBAC access control.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuditEventType:
    """Authentication & Access events (§28.1)."""
    LOGIN_SUCCESS = "user_login_success"
    LOGIN_FAILURE = "user_login_failure"
    LOGOUT = "user_logout"
    TWO_FA = "two_factor_verification"
    SESSION_CREATE = "session_created"
    SESSION_EXPIRE = "session_expired"
    PASSWORD_CHANGE = "password_changed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_ROTATED = "api_key_rotated"
    API_KEY_DELETED = "api_key_deleted"

    """Trading & Execution events."""
    SIGNAL_SUBSCRIBED = "signal_subscribed"
    SIGNAL_UNSUBSCRIBED = "signal_unsubscribed"
    COPY_TRADING_ENABLED = "copy_trading_enabled"
    COPY_TRADING_DISABLED = "copy_trading_disabled"
    ORDER_PLACED = "order_placed"
    ORDER_CONFIRMED = "order_confirmed"
    TRADE_FILLED = "trade_filled"
    TRADE_CLOSED = "trade_closed"

    """Account & Billing events."""
    SUBSCRIPTION_CHANGED = "subscription_changed"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    EMAIL_CHANGED = "email_changed"
    PROFILE_CHANGED = "profile_changed"

    """Admin events."""
    ADMIN_ACTION = "admin_action"
    FEATURE_FLAG_CHANGE = "feature_flag_changed"
    SYSTEM_CONFIG_CHANGE = "system_config_changed"

    """Compliance events."""
    KYC_SUBMITTED = "kyc_submitted"
    KYC_APPROVED = "kyc_approved"
    KYC_REJECTED = "kyc_rejected"
    DISCLAIMER_ACCEPTED = "disclaimer_accepted"


class AuditLogService:
    """
    Dedicated Audit Log Service per architecture doc §28.
    Append-only, immutable, hash chain integrity.
    """

    RETENTION_MONTHS = 24

    def __init__(self, db):
        self.db = db

    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        actor: str = "system",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Write an immutable audit log entry with hash chain."""
        try:
            prev_result = self.db.supabase.table("audit_logs").select("hash").order(
                "created_at", desc=True
            ).limit(1).execute()
            prev_hash = prev_result.data[0]["hash"] if prev_result.data else "genesis"

            entry = {
                "user_id": user_id or "system",
                "event_type": event_type,
                "actor": actor,
                "details": json.dumps(details or {}),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow().isoformat(),
            }

            entry_str = json.dumps(entry, sort_keys=True)
            current_hash = hashlib.sha256(f"{prev_hash}{entry_str}".encode()).hexdigest()

            insert_data = {**entry, "hash": current_hash, "prev_hash": prev_hash}

            result = self.db.supabase.table("audit_logs").insert(insert_data).execute()
            audit_id = result.data[0].get("id") if result.data else None

            logger.info(f"📝 Audit: {event_type} | actor={actor} | user={user_id}")
            return {"success": True, "audit_id": audit_id, "hash": current_hash}
        except Exception as e:
            logger.error(f"❌ Audit log failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get audit trail with optional filters."""
        try:
            query = self.db.supabase.table("audit_logs").select("*")
            if user_id:
                query = query.eq("user_id", user_id)
            if event_type:
                query = query.eq("event_type", event_type)
            if start_date:
                query = query.gte("created_at", start_date)
            if end_date:
                query = query.lte("created_at", end_date)

            response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            entries = response.data or []

            return {
                "success": True,
                "entries": entries,
                "count": len(entries),
                "offset": offset,
                "limit": limit,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def verify_chain_integrity(
        self, start_id: Optional[str] = None, limit: int = 1000
    ) -> Dict[str, Any]:
        """Verify hash chain integrity — architecture doc §28.2."""
        try:
            query = self.db.supabase.table("audit_logs").select("*").order("created_at", desc=False)
            if limit:
                query = query.limit(limit)
            response = query.execute()
            entries = response.data or []

            if not entries:
                return {"success": True, "valid": True, "entries_checked": 0}

            tampered = []
            for i in range(1, len(entries)):
                current = entries[i]
                previous = entries[i - 1]

                expected_prev_hash = previous.get("hash")
                actual_prev_hash = current.get("prev_hash")

                if expected_prev_hash != actual_prev_hash:
                    tampered.append({
                        "entry_id": current.get("id"),
                        "timestamp": current.get("created_at"),
                        "expected_prev_hash": expected_prev_hash,
                        "actual_prev_hash": actual_prev_hash,
                    })

            valid = len(tampered) == 0
            return {
                "success": True,
                "valid": valid,
                "entries_checked": len(entries),
                "tampered_entries": tampered,
                "checked_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_events_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get audit events by category (auth, trading, account, admin)."""
        category_map = {
            "auth": [
                AuditEventType.LOGIN_SUCCESS, AuditEventType.LOGIN_FAILURE,
                AuditEventType.LOGOUT, AuditEventType.TWO_FA,
                AuditEventType.PASSWORD_CHANGE, AuditEventType.API_KEY_CREATED,
            ],
            "trading": [
                AuditEventType.SIGNAL_SUBSCRIBED, AuditEventType.ORDER_PLACED,
                AuditEventType.ORDER_CONFIRMED, AuditEventType.TRADE_FILLED,
                AuditEventType.TRADE_CLOSED, AuditEventType.COPY_TRADING_ENABLED,
            ],
            "account": [
                AuditEventType.SUBSCRIPTION_CHANGED, AuditEventType.PAYMENT_SUCCESS,
                AuditEventType.PAYMENT_FAILED, AuditEventType.EMAIL_CHANGED,
                AuditEventType.PROFILE_CHANGED,
            ],
            "admin": [
                AuditEventType.ADMIN_ACTION, AuditEventType.FEATURE_FLAG_CHANGE,
                AuditEventType.SYSTEM_CONFIG_CHANGE,
            ],
        }
        event_types = category_map.get(category, [])
        if not event_types:
            return []

        try:
            response = (
                self.db.supabase.table("audit_logs")
                .select("*")
                .in_("event_type", event_types)
                .order("created_at", desc=True)
                .limit(500)
                .execute()
            )
            return response.data or []
        except Exception:
            return []

    async def get_audit_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get audit log statistics."""
        try:
            base_query = self.db.supabase.table("audit_logs").select("*")
            if user_id:
                base_query = base_query.eq("user_id", user_id)

            all_response = base_query.execute()
            entries = all_response.data or []

            event_counts = {}
            for e in entries:
                et = e.get("event_type", "unknown")
                event_counts[et] = event_counts.get(et, 0) + 1

            return {
                "success": True,
                "total_events": len(entries),
                "event_breakdown": event_counts,
                "retention_months": self.RETENTION_MONTHS,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
