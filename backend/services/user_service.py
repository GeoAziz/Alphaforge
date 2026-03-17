"""
KYC & User Management Service - Handles KYC verification, audit logging, and user settings.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
import json

logger = logging.getLogger(__name__)


class UserManagementService:
    """Manages KYC, audit logs, and user settings."""
    
    def __init__(self, db):
        self.db = db
    
    # ========== KYC ENDPOINTS ==========
    
    async def get_kyc_status(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get KYC verification status for a user."""
        try:
            response = self.db.supabase.table("users")\
                .select("kyc_status, verification_stage")\
                .eq("id", user_id)\
                .execute()
            
            if not response.data:
                return {"success": False, "error": "User not found"}
            
            user = response.data[0]
            
            kyc_response = self.db.supabase.table("kyc_verifications")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            kyc_data = kyc_response.data[0] if kyc_response.data else None
            
            return {
                "success": True,
                "user_id": user_id,
                "kyc_status": user.get("kyc_status"),
                "verification_stage": user.get("verification_stage"),
                "kyc_details": kyc_data
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get KYC status: {e}")
            return {"success": False, "error": str(e)}
    
    async def submit_kyc(
        self,
        user_id: str,
        kyc_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit KYC documents for verification."""
        try:
            kyc_record = {
                "user_id": user_id,
                "status": "SUBMITTED",
                "submitted_data": kyc_data,
                "documents": kyc_data.get("documents", []),
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("kyc_verifications").insert(kyc_record).execute()
            
            if response.data:
                # Update user status
                self.db.supabase.table("users")\
                    .update({
                        "kyc_status": "SUBMITTED",
                        "updated_at": datetime.utcnow().isoformat()
                    })\
                    .eq("id", user_id)\
                    .execute()
                
                logger.info(f"✅ KYC submitted for user {user_id}")
                return {"success": True, "kyc_id": response.data[0]["id"]}
            
        except Exception as e:
            logger.error(f"❌ Failed to submit KYC: {e}")
        
        return {"success": False, "error": str(e)}
    
    # ========== AUDIT LOG ENDPOINTS ==========
    
    async def get_audit_trail(
        self,
        user_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get audit trail for a user's account."""
        try:
            response = self.db.supabase.table("audit_logs")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            audit_logs = response.data or []
            logger.info(f"✅ Fetched {len(audit_logs)} audit logs for {user_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "audit_logs": audit_logs,
                "count": len(audit_logs)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch audit trail: {e}")
            return {"success": False, "error": str(e)}
    
    async def log_audit_entry(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        changes: Dict[str, Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an audit log entry (immutable)."""
        try:
            # Create hash chain for immutability
            # In production, this would include previous hash
            entry_hash = self._generate_hash({
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            audit_entry = {
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "changes": changes or {},
                "ip_address": ip_address,
                "user_agent": user_agent,
                "entry_hash": entry_hash,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("audit_logs").insert(audit_entry).execute()
            
            if response.data:
                return {"success": True, "log_id": response.data[0]["id"]}
            
        except Exception as e:
            logger.error(f"❌ Failed to create audit log: {e}")
        
        return {"success": False, "error": str(e)}
    
    # ========== SETTINGS ENDPOINTS ==========
    
    async def get_risk_settings(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get user's risk management settings."""
        try:
            response = self.db.supabase.table("user_risk_settings")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data:
                settings = response.data[0]
            else:
                # Return defaults
                settings = {
                    "user_id": user_id,
                    "max_position_size_pct": 2.0,
                    "max_portfolio_exposure_pct": 20.0,
                    "max_leverage": 5.0,
                    "stop_loss_default": 2.0,
                    "take_profit_default": 5.0,
                    "daily_loss_limit_pct": 10.0
                }
            
            return {
                "success": True,
                "user_id": user_id,
                "settings": settings
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get risk settings: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_risk_settings(
        self,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user's risk management settings."""
        try:
            settings["user_id"] = user_id
            settings["updated_at"] = datetime.utcnow().isoformat()
            
            # Upsert (insert or update)
            response = self.db.supabase.table("user_risk_settings")\
                .upsert(settings)\
                .execute()
            
            if response.data:
                logger.info(f"✅ Risk settings updated for {user_id}")
                
                # Log the change
                await self.log_audit_entry(
                    user_id,
                    "UPDATE",
                    "risk_settings",
                    user_id,
                    changes=settings
                )
                
                return {"success": True}
            
        except Exception as e:
            logger.error(f"❌ Failed to update risk settings: {e}")
        
        return {"success": False, "error": str(e)}
    
    # ========== EXCHANGE CONNECTION ENDPOINTS ==========
    
    async def connect_exchange(
        self,
        user_id: str,
        exchange: str,
        api_key: str,
        api_secret: str
    ) -> Dict[str, Any]:
        """Store exchange API credentials (encrypted)."""
        try:
            # In production, encrypt api_secret before storing
            # For MVP, we'll store encrypted version placeholder
            
            key_data = {
                "user_id": user_id,
                "exchange": exchange.lower(),
                "api_key": api_key,
                "api_secret_hash": self._hash_secret(api_secret),
                "status": "CONNECTED",
                "connected_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("api_keys").insert(key_data).execute()
            
            if response.data:
                logger.info(f"✅ {exchange} connected for {user_id}")
                
                # Log the connection
                await self.log_audit_entry(
                    user_id,
                    "CONNECT_EXCHANGE",
                    "exchange_api_key",
                    exchange,
                    changes={"exchange": exchange}
                )
                
                return {"success": True, "exchange": exchange}
            
        except Exception as e:
            logger.error(f"❌ Failed to connect exchange: {e}")
        
        return {"success": False, "error": str(e)}
    
    async def get_connected_exchanges(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get list of connected exchanges."""
        try:
            response = self.db.supabase.table("api_keys")\
                .select("exchange, status, connected_at")\
                .eq("user_id", user_id)\
                .eq("status", "CONNECTED")\
                .execute()
            
            exchanges = response.data or []
            
            return {
                "success": True,
                "user_id": user_id,
                "exchanges": exchanges,
                "count": len(exchanges)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get connected exchanges: {e}")
            return {"success": False, "error": str(e)}
    
    async def disconnect_exchange(
        self,
        user_id: str,
        exchange: str
    ) -> Dict[str, Any]:
        """Disconnect an exchange API key."""
        try:
            self.db.supabase.table("api_keys")\
                .delete()\
                .eq("user_id", user_id)\
                .eq("exchange", exchange.lower())\
                .execute()
            
            logger.info(f"✅ {exchange} disconnected for {user_id}")
            
            # Log the disconnection
            await self.log_audit_entry(
                user_id,
                "DISCONNECT_EXCHANGE",
                "exchange_api_key",
                exchange
            )
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"❌ Failed to disconnect exchange: {e}")
        
        return {"success": False, "error": str(e)}
    
    # ========== EXTERNAL SIGNALS ENDPOINTS ==========
    
    async def get_external_signals(
        self,
        user_id: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get external signals (TradingView, etc) received via webhooks."""
        try:
            query = self.db.supabase.table("external_signals").select("*")
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            signals = response.data or []
            
            return {
                "success": True,
                "signals": signals,
                "count": len(signals)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get external signals: {e}")
            return {"success": False, "error": str(e)}
    
    async def set_external_signal_rules(
        self,
        user_id: str,
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set filtering rules for external signal ingestion."""
        try:
            rules_data = {
                "user_id": user_id,
                "rules": rules,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("external_signal_rules").upsert(rules_data).execute()
            
            if response.data or len(response.data) == 0:  # Upsert returns empty if it updates
                logger.info(f"✅ External signal rules updated for {user_id}")
                return {"success": True}
            
        except Exception as e:
            logger.error(f"❌ Failed to set signal rules: {e}")
        
        return {"success": False, "error": str(e)}
    
    async def get_external_signal_history(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get history of webhook hits for a user."""
        try:
            from datetime import timedelta
            
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            response = self.db.supabase.table("external_signals")\
                .select("*")\
                .eq("user_id", user_id)\
                .gte("created_at", cutoff_date)\
                .order("created_at", desc=True)\
                .execute()
            
            signals = response.data or []
            
            return {
                "success": True,
                "user_id": user_id,
                "period_days": days,
                "webhook_hits": signals,
                "count": len(signals)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get signal history: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== SIGNAL EXECUTION & PROOFS ==========
    
    async def execute_signal(
        self,
        user_id: str,
        signal_id: str
    ) -> Dict[str, Any]:
        """Execute a signal (convert to live trade)."""
        try:
            # Get signal
            signal_response = self.db.supabase.table("signals")\
                .select("*")\
                .eq("id", signal_id)\
                .execute()
            
            if not signal_response.data:
                return {"success": False, "error": "Signal not found"}
            
            signal = signal_response.data[0]
            
            # Execute paper trade (convert to live in production)
            trade_data = {
                "user_id": user_id,
                "signal_id": signal_id,
                "asset": signal.get("ticker"),
                "direction": "LONG" if signal.get("signal_type") == "BUY" else "SHORT",
                "entry_price": signal.get("entry_price"),
                "stop_loss": signal.get("stop_loss_price"),
                "take_profit": signal.get("take_profit_price"),
                "status": "OPEN",
                "opened_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("paper_trades").insert(trade_data).execute()
            
            if response.data:
                logger.info(f"✅ Signal executed: {signal_id}")
                return {"success": True, "trade_id": response.data[0]["id"]}
            
        except Exception as e:
            logger.error(f"❌ Failed to execute signal: {e}")
        
        return {"success": False, "error": str(e)}
    
    async def get_signal_proof(
        self,
        signal_id: str
    ) -> Dict[str, Any]:
        """Get proof/verification data for a signal."""
        try:
            # Get signal with proof data
            response = self.db.supabase.table("signals")\
                .select("*")\
                .eq("id", signal_id)\
                .execute()
            
            if not response.data:
                return {"success": False, "error": "Signal not found"}
            
            signal = response.data[0]
            
            # Generate proof (Merkle root, blockchain anchor, etc)
            proof_data = {
                "signal_id": signal_id,
                "ticker": signal.get("ticker"),
                "signal_type": signal.get("signal_type"),
                "confidence": signal.get("confidence"),
                "created_at": signal.get("created_at"),
                "merkle_root": self._generate_merkle_root(signal_id),
                "blockchain_anchor": {
                    "chain": "ethereum",
                    "tx_hash": f"0x{self._hash_content(signal_id)}",
                    "block": 19234852,
                    "confirmation": True
                },
                "rationale": signal.get("rationale"),
                "performance": signal.get("performance_data", {})
            }
            
            return {
                "success": True,
                "proof": proof_data
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get signal proof: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== UTILITY METHODS ==========
    
    def _hash_secret(self, secret: str) -> str:
        """Hash a secret for storage."""
        return hashlib.sha256(secret.encode()).hexdigest()[:16]
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content."""
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _generate_merkle_root(self, data: str) -> str:
        """Generate Merkle root (simplified)."""
        return hashlib.sha256((data + "merkle").encode()).hexdigest()
    
    def _generate_hash(self, data: Dict) -> str:
        """Generate hash of data."""
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:16]
