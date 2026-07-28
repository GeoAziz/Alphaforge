"""
External Signal Ingestion Service - Processes incoming webhook signals from TradingView
and other external sources. Validates against user-defined ingestion rules,
creates signal records, and routes to execution pipeline.
"""

import os
import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SignalSource(str, Enum):
    TRADINGVIEW = "tradingview"
    OTHER = "other"


class IngestionStatus(str, Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    PROCESSED = "processed"
    EXECUTED = "executed"
    REJECTED = "rejected"
    RATE_LIMITED = "rate_limited"


class ExternalSignalIngestionService:
    """Validates and ingests external signals from webhooks."""

    def __init__(self, db):
        self.db = db
        self._default_rules = {
            "min_confidence": 0.7,
            "auto_execute": False,
            "cooldown_seconds": 300,
            "max_positions_open": 10,
            "risk_multiplier": 1.0,
            "allowed_strategies": [],
        }

    async def get_user_rules(self, user_id: str) -> Dict[str, Any]:
        """Fetch user's ingestion rules, falling back to defaults."""
        try:
            response = self.db.supabase.table("external_signal_rules") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()

            if response.data:
                return response.data
        except Exception:
            pass

        return {**self._default_rules, "user_id": user_id}

    async def set_user_rules(self, user_id: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update user's ingestion rules."""
        rules_data = {
            "user_id": user_id,
            "min_confidence": rules.get("min_confidence", 0.7),
            "auto_execute": rules.get("auto_execute", False),
            "cooldown_seconds": rules.get("cooldown_seconds", 300),
            "max_positions_open": rules.get("max_positions_open", 10),
            "risk_multiplier": rules.get("risk_multiplier", 1.0),
            "allowed_strategies": rules.get("allowed_strategies", []),
            "updated_at": datetime.utcnow().isoformat(),
        }

        try:
            response = self.db.supabase.table("external_signal_rules") \
                .upsert(rules_data) \
                .execute()

            return {"success": True, "rules": response.data[0] if response.data else rules_data}
        except Exception as e:
            logger.error(f"Failed to set ingestion rules: {e}")
            return {"success": False, "error": str(e)}

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: Optional[str],
        secret: Optional[str],
    ) -> bool:
        """Verify HMAC-SHA256 webhook signature."""
        if not secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True

        if not signature:
            return False

        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def parse_tradingview_alert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse TradingView alert message into structured signal data."""
        message = payload.get("message", payload.get("text", ""))
        ticker = payload.get("ticker", payload.get("symbol", "UNKNOWN"))
        action = payload.get("action", "HOLD")

        confidence = 0.8
        risk_level = 2
        parts = message.split()
        for part in parts:
            if "=" in part:
                key, _, val = part.partition("=")
                key = key.strip().lower()
                val = val.strip()
                if key == "confidence":
                    try:
                        confidence = float(val)
                    except ValueError:
                        pass
                elif key == "risklevel":
                    try:
                        risk_level = int(val)
                    except ValueError:
                        pass

        direction = "LONG" if action.upper() in ("BUY", "LONG") else "SHORT" if action.upper() in ("SELL", "SHORT") else "HOLD"

        return {
            "ticker": ticker,
            "direction": direction,
            "confidence": confidence,
            "risk_level": risk_level,
            "raw_message": message,
            "source": "tradingview",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def ingest_signal(
        self,
        user_id: str,
        payload: Dict[str, Any],
        source: str = "tradingview",
        signature_valid: bool = True,
    ) -> Dict[str, Any]:
        """Full ingestion pipeline: parse, validate, store, optionally execute."""
        event_id = None
        try:
            webhook_event = {
                "user_id": user_id,
                "source": source,
                "payload": json.dumps(payload),
                "signature_valid": signature_valid,
                "processing_status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }
            event_resp = self.db.supabase.table("webhook_events").insert(webhook_event).execute()
            if event_resp.data:
                event_id = event_resp.data[0].get("id")
        except Exception as e:
            logger.warning(f"Failed to log webhook event: {e}")

        if not signature_valid:
            self._update_event_status(event_id, "failed", "Invalid signature")
            return {"success": False, "status": IngestionStatus.REJECTED, "reason": "Invalid webhook signature"}

        if source == "tradingview":
            parsed = self.parse_tradingview_alert(payload)
        else:
            parsed = {
                "ticker": payload.get("ticker", "UNKNOWN"),
                "direction": payload.get("direction", "HOLD"),
                "confidence": payload.get("confidence", 0.8),
                "risk_level": payload.get("risk_level", 2),
                "raw_message": json.dumps(payload),
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
            }

        rules = await self.get_user_rules(user_id)
        rejection_reason = self._validate_against_rules(parsed, rules, user_id)

        if rejection_reason:
            self._update_event_status(event_id, "failed", rejection_reason)
            await self._log_external_signal(user_id, parsed, IngestionStatus.REJECTED, rejection_reason)
            return {
                "success": False,
                "status": IngestionStatus.REJECTED,
                "reason": rejection_reason,
                "parsed_signal": parsed,
            }

        signal_record = {
            "ticker": parsed["ticker"],
            "signal_type": parsed["direction"],
            "confidence": parsed["confidence"],
            "source": source,
            "user_id": user_id,
            "metadata": json.dumps(payload),
            "ingestion_status": IngestionStatus.VALIDATED.value,
            "created_at": datetime.utcnow().isoformat(),
        }

        try:
            resp = self.db.supabase.table("signals").insert(signal_record).execute()
            signal_id = resp.data[0].get("id") if resp.data else None
        except Exception as e:
            logger.error(f"Failed to store ingested signal: {e}")
            signal_id = None

        self._update_event_status(event_id, "processed", None)
        await self._log_external_signal(user_id, parsed, IngestionStatus.VALIDATED, None, signal_id)

        return {
            "success": True,
            "status": IngestionStatus.VALIDATED,
            "signal_id": signal_id,
            "parsed_signal": parsed,
            "auto_execute": rules.get("auto_execute", False),
        }

    def _validate_against_rules(
        self,
        signal: Dict[str, Any],
        rules: Dict[str, Any],
        user_id: str,
    ) -> Optional[str]:
        """Validate signal against user's ingestion rules. Returns rejection reason or None."""
        confidence = signal.get("confidence", 0)
        min_conf = rules.get("min_confidence", 0.7)
        if confidence < min_conf:
            return f"Confidence {confidence:.0%} below minimum {min_conf:.0%}"

        allowed = rules.get("allowed_strategies", [])
        if allowed and signal.get("source") not in allowed:
            return f"Source '{signal.get('source')}' not in allowed list"

        return None

    async def _log_external_signal(
        self,
        user_id: str,
        signal_data: Dict[str, Any],
        status: IngestionStatus,
        rejection_reason: Optional[str] = None,
        signal_id: Optional[str] = None,
    ):
        """Log the ingested external signal."""
        try:
            record = {
                "user_id": user_id,
                "source": signal_data.get("source", "unknown"),
                "ticker": signal_data.get("ticker", "UNKNOWN"),
                "direction": signal_data.get("direction", "HOLD"),
                "confidence": signal_data.get("confidence", 0),
                "status": status.value,
                "rejection_reason": rejection_reason,
                "signal_id": signal_id,
                "created_at": datetime.utcnow().isoformat(),
            }
            self.db.supabase.table("external_signals").insert(record).execute()
        except Exception as e:
            logger.warning(f"Failed to log external signal: {e}")

    def _update_event_status(self, event_id: Optional[str], status: str, error: Optional[str] = None):
        """Update webhook event processing status."""
        if not event_id:
            return
        try:
            update = {"processing_status": status}
            if error:
                update["error_message"] = error
            self.db.supabase.table("webhook_events").update(update).eq("id", event_id).execute()
        except Exception as e:
            logger.warning(f"Failed to update event status: {e}")

    async def get_signal_history(
        self,
        user_id: str,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get history of ingested external signals for a user."""
        try:
            query = self.db.supabase.table("external_signals") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit)

            if status:
                query = query.eq("status", status)

            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get signal history: {e}")
            return []

    async def get_webhook_events(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get webhook event log for debugging."""
        try:
            query = self.db.supabase.table("webhook_events") \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(limit)

            if user_id:
                query = query.eq("user_id", user_id)

            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get webhook events: {e}")
            return []
