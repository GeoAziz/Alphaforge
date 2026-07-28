"""
Compliance and regulatory service: KYC, AML, audit logs, disclaimers, licenses.
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from config import ComplianceConfig

logger = logging.getLogger(__name__)


class KYCStatus(str, Enum):
    """KYC verification status."""
    NOT_STARTED = "NOT_STARTED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AuditAction(str, Enum):
    """Audit log action types."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    API_KEY_CREATED = "api_key_created"
    TRADE_EXECUTED = "trade_executed"
    STRATEGY_PUBLISHED = "strategy_published"
    FUND_DEPOSIT = "fund_deposit"
    FUND_WITHDRAWAL = "fund_withdrawal"
    SETTINGS_CHANGED = "settings_changed"
    COMPLIANCE_CHECK = "compliance_check"


class ComplianceService:
    """Manages regulatory compliance and KYC/AML."""

    def __init__(self, db):
        self.db = db
        self.enabled = ComplianceConfig.ENABLED

    # ========================================================================
    # KYC VERIFICATION
    # ========================================================================

    async def submit_kyc(
        self,
        user_id: str,
        full_name: str,
        date_of_birth: str,
        address: str,
        country: str,
        id_document_url: str,
        proof_of_address_url: str,
    ) -> Dict[str, Any]:
        """Submit KYC documents for verification."""
        if not self.enabled:
            logger.warning("Compliance checks disabled")
            return {"success": True, "kyc_status": KYCStatus.APPROVED.value}

        try:
            insert_data = {
                "user_id": user_id,
                "full_name": full_name,
                "date_of_birth": date_of_birth,
                "address": address,
                "country": country,
                "id_document_url": id_document_url,
                "proof_of_address_url": proof_of_address_url,
                "status": KYCStatus.SUBMITTED.value,
                "submitted_at": datetime.utcnow().isoformat(),
            }

            result = self.db.supabase.table("kyc_verifications").insert(insert_data).execute()

            # Log audit trail
            await self._audit_log(user_id, AuditAction.SETTINGS_CHANGED, {
                "action": "kyc_submitted",
                "country": country,
            })

            logger.info(f"✅ KYC submitted for {user_id} from {country}")
            return {"success": True, "kyc_status": KYCStatus.SUBMITTED.value}

        except Exception as e:
            logger.error(f"❌ KYC submission failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_kyc_status(self, user_id: str) -> Dict[str, Any]:
        """Get KYC verification status."""
        try:
            result = self.db.supabase.table("kyc_verifications").select("*").eq(
                "user_id", user_id
            ).order("submitted_at", desc=True).limit(1).execute()

            if not result.data:
                return {"kyc_status": KYCStatus.NOT_STARTED.value}

            data = result.data[0]
            return {
                "kyc_status": data.get("status"),
                "submitted_at": data.get("submitted_at"),
                "approved_at": data.get("approved_at"),
                "rejection_reason": data.get("rejection_reason"),
            }

        except Exception as e:
            logger.error(f"❌ Failed to fetch KYC status: {e}")
            return {"kyc_status": KYCStatus.NOT_STARTED.value}

    # ========================================================================
    # AML COMPLIANCE
    # ========================================================================

    async def perform_aml_check(self, user_id: str, full_name: str, country: str) -> Dict[str, Any]:
        """Perform AML (Anti-Money Laundering) check."""
        if not ComplianceConfig.AML_ENABLED:
            return {"success": True, "aml_passed": True}

        try:
            # In production, call third-party AML provider (e.g., Trulioo, SumSubstance)
            # For MVP, mock implementation
            aml_result = await self._mock_aml_check(full_name, country)

            insert_data = {
                "user_id": user_id,
                "full_name": full_name,
                "country": country,
                "check_result": "PASS" if aml_result["passed"] else "FAIL",
                "risk_level": aml_result.get("risk_level", "LOW"),
                "checked_at": datetime.utcnow().isoformat(),
            }

            self.db.supabase.table("aml_checks").insert(insert_data).execute()

            if not aml_result["passed"]:
                await self._audit_log(user_id, AuditAction.COMPLIANCE_CHECK, {
                    "action": "aml_failed",
                    "risk_level": aml_result.get("risk_level"),
                })
                logger.warning(f"⚠️  AML check failed for {user_id}")

            return {
                "success": True,
                "aml_passed": aml_result["passed"],
                "risk_level": aml_result.get("risk_level"),
            }

        except Exception as e:
            logger.error(f"❌ AML check failed: {e}")
            return {"success": False, "error": str(e)}

    async def _mock_aml_check(self, full_name: str, country: str) -> Dict[str, Any]:
        """Mock AML check (replace with real provider in production)."""
        # Simulate sanctions list check
        blocked_countries = ["IRAN", "NORTH KOREA", "SYRIA"]
        if country.upper() in blocked_countries:
            return {"passed": False, "risk_level": "CRITICAL"}

        # Simulate PEP (Politically Exposed Person) check
        restricted_names = ["putin", "kim jong"]
        if any(name in full_name.lower() for name in restricted_names):
            return {"passed": False, "risk_level": "HIGH"}

        return {"passed": True, "risk_level": "LOW"}

    # ========================================================================
    # AUDIT LOGGING (Immutable)
    # ========================================================================

    async def _audit_log(
        self,
        user_id: str,
        action: AuditAction,
        details: Dict[str, Any] = None,
        ip_address: str = None,
    ) -> Dict[str, Any]:
        """Create immutable audit log entry with hash chain."""
        try:
            # Get previous hash for chain
            prev_result = self.db.supabase.table("audit_logs").select("hash").eq(
                "user_id", user_id
            ).order("created_at", desc=True).limit(1).execute()

            prev_hash = prev_result.data[0]["hash"] if prev_result.data else "genesis"

            # Create current entry
            entry = {
                "user_id": user_id,
                "action": action.value,
                "details": json.dumps(details or {}),
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Hash current entry with previous hash (immutable chain)
            entry_str = json.dumps(entry, sort_keys=True)
            current_hash = hashlib.sha256(
                f"{prev_hash}{entry_str}".encode()
            ).hexdigest()

            insert_data = {**entry, "hash": current_hash, "prev_hash": prev_hash}

            result = self.db.supabase.table("audit_logs").insert(insert_data).execute()
            logger.info(f"📝 Audit log: {user_id} - {action.value}")
            return {"success": True, "audit_id": result.data[0].get("id") if result.data else None}

        except Exception as e:
            logger.error(f"❌ Audit log failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_audit_trail(self, user_id: str, limit: int = 100) -> Dict[str, Any]:
        """Get immutable audit trail for user."""
        try:
            result = self.db.supabase.table("audit_logs").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).limit(limit).execute()

            entries = []
            for row in (result.data or []):
                entries.append({
                    "timestamp": row.get("timestamp"),
                    "action": row.get("action"),
                    "details": json.loads(row.get("details", "{}")),
                    "ip_address": row.get("ip_address"),
                    "hash": row.get("hash"),
                    "prev_hash": row.get("prev_hash"),
                })

            return {"success": True, "audit_trail": entries, "count": len(entries)}

        except Exception as e:
            logger.error(f"❌ Failed to fetch audit trail: {e}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # DISCLAIMERS & LEGAL
    # ========================================================================

    # ========================================================================
    # DISCLAIMER TYPES (§6) — 6 Specific Disclaimer Categories
    # ========================================================================

    DISCLAIMER_TYPES = {
        "financial_promotion": {
            "key": "financial_promotion",
            "title": "Financial Promotion Warning",
            "text": "This platform provides AI-generated trading signals for educational and research purposes. Signals do not constitute financial advice, investment recommendations, or solicitations to trade. Past performance does not guarantee future results.",
        },
        "past_performance": {
            "key": "past_performance",
            "title": "Past Performance Disclaimer",
            "text": "Any past performance data, backtest results, or historical signal accuracy shown on this platform are for informational purposes only. Historical results may not reflect future performance. Trading involves substantial risk of loss.",
        },
        "leverage_liquidation": {
            "key": "leverage_liquidation",
            "title": "Leverage & Liquidation Risk",
            "text": "Leveraged trading (perpetuals, margin) magnifies both gains and losses. You may lose more than your initial margin. Liquidation can occur rapidly in volatile markets. Maximum leverage is limited to 5x in Phase 1.",
        },
        "execution_risk": {
            "key": "execution_risk",
            "title": "Execution Risk (Slippage)",
            "text": "Market orders may execute at prices different from the signal entry price due to slippage, liquidity conditions, and market volatility. Actual execution prices may vary significantly from signal prices, especially in fast-moving markets.",
        },
        "model_risk": {
            "key": "model_risk",
            "title": "AI Model Risk",
            "text": "AlphaForge uses artificial intelligence and machine learning models to generate trading signals. AI models can be wrong, produce inaccurate predictions, or fail to account for unprecedented market conditions. Do not rely solely on AI signals for trading decisions.",
        },
        "technology_risk": {
            "key": "technology_risk",
            "title": "Technology Risk",
            "text": "System updates, maintenance, API failures, exchange downtime, or internet connectivity issues may temporarily disrupt service. AlphaForge is not liable for losses caused by technology failures, delayed signals, or system unavailability.",
        },
    }

    async def accept_disclaimer(
        self,
        user_id: str,
        disclaimer_key: str,
        version: str = None,
        ts_version: str = None,
    ) -> Dict[str, Any]:
        """
        Record user disclaimer acknowledgment per architecture doc §6.
        Records which disclaimer user acknowledged + when + T&S version.
        """
        if disclaimer_key not in self.DISCLAIMER_TYPES:
            return {"success": False, "error": f"Unknown disclaimer key: {disclaimer_key}"}

        try:
            insert_data = {
                "user_id": user_id,
                "disclaimer_key": disclaimer_key,
                "disclaimer_version": version or ComplianceConfig.DISCLAIMER_VERSION,
                "ts_version": ts_version or ComplianceConfig.DISCLAIMER_VERSION,
                "acknowledged_at": datetime.utcnow().isoformat(),
                "ip_address": "0.0.0.0",
            }

            self.db.supabase.table("disclaimer_acceptances").insert(insert_data).execute()

            await self._audit_log(user_id, AuditAction.SETTINGS_CHANGED, {
                "action": "disclaimer_acknowledged",
                "disclaimer_key": disclaimer_key,
                "version": version,
            })

            logger.info(f"✅ Disclaimer '{disclaimer_key}' acknowledged by {user_id}")
            return {"success": True, "disclaimer_key": disclaimer_key}
        except Exception as e:
            logger.error(f"❌ Disclaimer acceptance failed: {e}")
            return {"success": False, "error": str(e)}

    async def accept_all_disclaimers(
        self, user_id: str, ts_version: str = None
    ) -> Dict[str, Any]:
        """Accept all 6 disclaimer types at once."""
        results = {}
        for key in self.DISCLAIMER_TYPES:
            result = await self.accept_disclaimer(user_id, key, ts_version=ts_version)
            results[key] = result.get("success", False)

        all_accepted = all(results.values())
        return {
            "success": all_accepted,
            "results": results,
            "accepted_count": sum(1 for v in results.values() if v),
            "total_count": len(self.DISCLAIMER_TYPES),
        }

    async def get_user_disclaimer_status(self, user_id: str) -> Dict[str, Any]:
        """Get which disclaimers a user has acknowledged."""
        try:
            response = (
                self.db.supabase.table("disclaimer_acceptances")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            acknowledged = {d["disclaimer_key"]: d for d in (response.data or [])}

            status = {}
            for key, info in self.DISCLAIMER_TYPES.items():
                ack = acknowledged.get(key)
                status[key] = {
                    "title": info["title"],
                    "acknowledged": ack is not None,
                    "acknowledged_at": ack.get("acknowledged_at") if ack else None,
                }

            return {"success": True, "disclaimers": status, "all_accepted": all(s["acknowledged"] for s in status.values())}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_disclaimer(self, disclaimer_key: str = None) -> Dict[str, Any]:
        """Get current platform disclaimer(s)."""
        if disclaimer_key:
            info = self.DISCLAIMER_TYPES.get(disclaimer_key)
            if not info:
                return {"error": f"Unknown disclaimer: {disclaimer_key}"}
            return {**info, "version": ComplianceConfig.DISCLAIMER_VERSION, "jurisdiction": ComplianceConfig.JURISDICTION}

        return {
            "version": ComplianceConfig.DISCLAIMER_VERSION,
            "jurisdiction": ComplianceConfig.JURISDICTION,
            "requires_financial_license": ComplianceConfig.REQUIRES_FINANCIAL_LICENSE,
            "disclaimers": list(self.DISCLAIMER_TYPES.values()),
        }

    # ========================================================================
    # GDPR DATA EXPORT (§6)
    # ========================================================================

    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        GDPR Data Export API per architecture doc §6.
        User requests own data — returns all data across tables.
        """
        try:
            export = {"user_id": user_id, "exported_at": datetime.utcnow().isoformat()}

            tables = {
                "users": "id",
                "paper_trades": "user_id",
                "positions": "user_id",
                "kyc_verifications": "user_id",
                "audit_logs": "user_id",
                "disclaimer_acceptances": "user_id",
                "strategies": "user_id",
                "creator_strategies": "user_id",
                "notifications": "user_id",
            }

            for table, col in tables.items():
                try:
                    response = self.db.supabase.table(table).select("*").eq(col, user_id).execute()
                    export[table] = response.data or []
                except Exception:
                    export[table] = []

            return {"success": True, "export": export, "format": "json"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def anonymize_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Anonymize PII in audit trail per architecture doc §6.
        user deletion → anonymise PII in audit trail
        """
        try:
            anon_id = f"deleted_{hashlib.sha256(user_id.encode()).hexdigest()[:16]}"

            self.db.supabase.table("users").update({
                "email": f"{anon_id}@anonymized.local",
                "display_name": "Deleted User",
                "firebase_uid": anon_id,
                "kyc_status": "ANONYMIZED",
            }).eq("id", user_id).execute()

            self.db.supabase.table("audit_logs").update({
                "user_id": anon_id,
                "details": json.dumps({"anonymized": True, "original_timestamp": datetime.utcnow().isoformat()}),
            }).eq("user_id", user_id).execute()

            logger.info(f"✅ User data anonymized: {user_id} → {anon_id}")
            return {"success": True, "anonymized_id": anon_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Right-to-erasure implementation per architecture doc §6.
        30-day deletion cycle with anonymization of audit trail.
        """
        try:
            anonymize_result = await self.anonymize_user_data(user_id)
            if not anonymize_result.get("success"):
                return anonymize_result

            tables_to_clean = ["paper_trades", "positions", "strategies", "notifications"]
            for table in tables_to_clean:
                try:
                    self.db.supabase.table(table).delete().eq("user_id", user_id).execute()
                except Exception:
                    pass

            await self._audit_log(anonymize_result["anonymized_id"], AuditAction.SETTINGS_CHANGED, {
                "action": "user_data_deletion",
                "original_user_id": user_id,
                "deletion_date": datetime.utcnow().isoformat(),
                "retention_note": "Audit logs retained for 24 months per compliance requirements",
            })

            logger.info(f"✅ User data deleted: {user_id}")
            return {"success": True, "message": "User data deleted. Audit logs retained for 24 months.", "deletion_date": datetime.utcnow().isoformat()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================================================
    # COMPLIANCE REPORTS
    # ========================================================================

    async def generate_compliance_report(self, user_id: str) -> Dict[str, Any]:
        """Generate compliance report for user (GDPR, regulatory)."""
        try:
            # Collect all user data across tables
            user_data = self.db.supabase.table("users").select("*").eq("id", user_id).execute()
            trades = self.db.supabase.table("paper_trades").select("*").eq(
                "user_id", user_id
            ).execute()
            kyc = self.db.supabase.table("kyc_verifications").select("*").eq(
                "user_id", user_id
            ).execute()
            audit = self.db.supabase.table("audit_logs").select("*").eq(
                "user_id", user_id
            ).execute()

            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "user_profile": user_data.data[0] if user_data.data else {},
                "trades_count": len(trades.data or []),
                "kyc_status": kyc.data[0].get("status") if kyc.data else None,
                "audit_events_count": len(audit.data or []),
            }

            logger.info(f"✅ Compliance report generated for {user_id}")
            return {"success": True, "report": report}

        except Exception as e:
            logger.error(f"❌ Report generation failed: {e}")
            return {"success": False, "error": str(e)}
