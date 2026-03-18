"""
KYC Verification Service - Handles identity verification for users.

Levels:
1. Basic KYC: Name, email, DOB (on signup)
2. Enhanced KYC: ID document, proof of address, selfie (before live trading)
3. Advanced KYC: Income verification, source of funds (for high volumes)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class KYCStatus(str, Enum):
    """KYC verification status."""
    NOT_STARTED = "NOT_STARTED"
    BASIC_SUBMITTED = "BASIC_SUBMITTED"
    BASIC_VERIFIED = "BASIC_VERIFIED"
    ENHANCED_SUBMITTED = "ENHANCED_SUBMITTED"
    ENHANCED_VERIFIED = "ENHANCED_VERIFIED"
    ADVANCED_SUBMITTED = "ADVANCED_SUBMITTED"
    ADVANCED_VERIFIED = "ADVANCED_VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class KYCService:
    """Manages KYC verification workflow."""
    
    def __init__(self, db):
        self.db = db
        # In Phase 2, integrate with third-party KYC providers:
        # - Jumio
        # - IDology
        # - Onfido
        # - AU10TIX
    
    async def start_kyc(self, user_id: str, kyc_level: str = "enhanced") -> Dict[str, Any]:
        """Start KYC process for user."""
        try:
            # Check existing KYC
            response = self.db.supabase.table("kyc_verifications")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data:
                existing = response.data[0]
                if existing["status"] in [KYCStatus.ENHANCED_VERIFIED, KYCStatus.ADVANCED_VERIFIED]:
                    return {
                        "success": False,
                        "error": f"User already has {existing['status']} KYC"
                    }
            
            # Create KYC record
            kyc_record = {
                "user_id": user_id,
                "kyc_level": kyc_level,
                "status": KYCStatus.BASIC_SUBMITTED,
                "submitted_at": datetime.utcnow().isoformat(),
                "documents": {},
                "verification_data": {},
                "notes": ""
            }
            
            response = self.db.supabase.table("kyc_verifications")\
                .insert(kyc_record)\
                .execute()
            
            if response.data:
                kyc_id = response.data[0]["id"]
                logger.info(f"✅ KYC started for user {user_id}: {kyc_id}")
                
                return {
                    "success": True,
                    "kyc_id": kyc_id,
                    "status": KYCStatus.BASIC_SUBMITTED,
                    "message": f"KYC {kyc_level} verification started"
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to start KYC: {e}")
        
        return {"success": False, "error": "Failed to start KYC"}
    
    async def upload_document(
        self,
        user_id: str,
        document_type: str,
        document_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload KYC document."""
        try:
            # Validate document type
            valid_types = [
                "GOVERNMENT_ID",
                "PASSPORT",
                "DRIVER_LICENSE",
                "PROOF_OF_ADDRESS",
                "BANK_STATEMENT",
                "UTILITY_BILL",
                "SELFIE_WITH_ID"
            ]
            
            if document_type not in valid_types:
                return {"success": False, "error": f"Invalid document type: {document_type}"}
            
            # Get KYC record
            response = self.db.supabase.table("kyc_verifications")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if not response.data:
                return {"success": False, "error": "KYC not started"}
            
            kyc_record = response.data[0]
            documents = kyc_record.get("documents", {})
            
            # Add document
            documents[document_type] = {
                "url": document_url,
                "uploaded_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "verified": False
            }
            
            # Update KYC record
            update_response = self.db.supabase.table("kyc_verifications")\
                .update({"documents": documents})\
                .eq("user_id", user_id)\
                .execute()
            
            if update_response.data:
                logger.info(f"✅ Document {document_type} uploaded for user {user_id}")
                
                return {
                    "success": True,
                    "message": f"{document_type} uploaded successfully"
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload document: {e}")
        
        return {"success": False, "error": "Failed to upload document"}
    
    async def get_kyc_status(self, user_id: str) -> Dict[str, Any]:
        """Get KYC verification status for user."""
        try:
            response = self.db.supabase.table("kyc_verifications")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if not response.data:
                # No KYC started
                return {
                    "success": True,
                    "status": KYCStatus.NOT_STARTED,
                    "level": None,
                    "can_trade_paper": True,
                    "can_trade_live": False
                }
            
            kyc_record = response.data[0]
            status = kyc_record.get("status")
            
            # Determine trading permissions
            can_trade_paper = status not in [KYCStatus.REJECTED, KYCStatus.EXPIRED]
            can_trade_live = status in [
                KYCStatus.ENHANCED_VERIFIED,
                KYCStatus.ADVANCED_VERIFIED
            ]
            
            # Check expiration (KYC valid for 1 year)
            submitted_at = datetime.fromisoformat(kyc_record.get("submitted_at", datetime.utcnow().isoformat()))
            expires_at = submitted_at + timedelta(days=365)
            is_expired = datetime.utcnow() > expires_at
            
            if is_expired and can_trade_live:
                status = KYCStatus.EXPIRED
                can_trade_live = False
                
                # Update status
                self.db.supabase.table("kyc_verifications")\
                    .update({"status": KYCStatus.EXPIRED})\
                    .eq("user_id", user_id)\
                    .execute()
            
            return {
                "success": True,
                "status": status,
                "level": kyc_record.get("kyc_level"),
                "documents": list(kyc_record.get("documents", {}).keys()),
                "can_trade_paper": can_trade_paper,
                "can_trade_live": can_trade_live,
                "submitted_at": kyc_record.get("submitted_at"),
                "verified_at": kyc_record.get("verified_at"),
                "expires_at": expires_at.isoformat() if can_trade_live else None,
                "rejection_reason": kyc_record.get("rejection_reason")
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get KYC status: {e}")
            return {"success": False, "error": str(e)}
    
    async def submit_kyc(self, user_id: str) -> Dict[str, Any]:
        """Submit KYC for review (after uploading documents)."""
        try:
            # Get KYC record
            response = self.db.supabase.table("kyc_verifications")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if not response.data:
                return {"success": False, "error": "KYC not found"}
            
            kyc_record = response.data[0]
            documents = kyc_record.get("documents", {})
            kyc_level = kyc_record.get("kyc_level", "enhanced")
            
            # Validate required documents by level
            required_docs = {
                "basic": ["GOVERNMENT_ID"],
                "enhanced": ["GOVERNMENT_ID", "PROOF_OF_ADDRESS", "SELFIE_WITH_ID"],
                "advanced": ["GOVERNMENT_ID", "PROOF_OF_ADDRESS", "SELFIE_WITH_ID", "BANK_STATEMENT"]
            }
            
            required = required_docs.get(kyc_level, required_docs["enhanced"])
            missing = [doc for doc in required if doc not in documents]
            
            if missing:
                return {
                    "success": False,
                    "error": f"Missing required documents: {', '.join(missing)}"
                }
            
            # Update status to submitted
            new_status = f"{kyc_level.upper()}_SUBMITTED"
            
            update_response = self.db.supabase.table("kyc_verifications")\
                .update({"status": new_status})\
                .eq("user_id", user_id)\
                .execute()
            
            if update_response.data:
                logger.info(f"✅ KYC submitted for user {user_id}")
                
                # In Phase 2, this would queue verification with third-party provider
                # For MVP, simulate automatic approval after 24 hours
                
                return {
                    "success": True,
                    "status": new_status,
                    "message": "KYC submitted for review"
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to submit KYC: {e}")
        
        return {"success": False, "error": "Failed to submit KYC"}
    
    async def approve_kyc(
        self,
        user_id: str,
        admin_id: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Admin endpoint: Approve KYC verification."""
        try:
            # Check admin permission (would be role-based in production)
            # For MVP, assuming admin_id is sufficient
            
            response = self.db.supabase.table("kyc_verifications")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if not response.data:
                return {"success": False, "error": "KYC not found"}
            
            kyc_record = response.data[0]
            kyc_level = kyc_record.get("kyc_level", "enhanced").upper()
            
            new_status = f"{kyc_level}_VERIFIED"
            
            # Update KYC
            update_response = self.db.supabase.table("kyc_verifications")\
                .update({
                    "status": new_status,
                    "verified_at": datetime.utcnow().isoformat(),
                    "verified_by": admin_id,
                    "notes": notes
                })\
                .eq("user_id", user_id)\
                .execute()
            
            if update_response.data:
                # Update user KYC status
                self.db.supabase.table("users")\
                    .update({"kyc_status": new_status})\
                    .eq("id", user_id)\
                    .execute()
                
                logger.info(f"✅ KYC approved for user {user_id} by admin {admin_id}")
                
                return {
                    "success": True,
                    "status": new_status,
                    "message": "KYC verified and approved"
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to approve KYC: {e}")
        
        return {"success": False, "error": "Failed to approve KYC"}
    
    async def reject_kyc(
        self,
        user_id: str,
        admin_id: str,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """Admin endpoint: Reject KYC verification."""
        try:
            update_response = self.db.supabase.table("kyc_verifications")\
                .update({
                    "status": KYCStatus.REJECTED,
                    "rejection_reason": rejection_reason,
                    "rejected_at": datetime.utcnow().isoformat(),
                    "rejected_by": admin_id
                })\
                .eq("user_id", user_id)\
                .execute()
            
            if update_response.data:
                logger.warning(f"⚠️ KYC rejected for user {user_id}: {rejection_reason}")
                
                return {
                    "success": True,
                    "status": KYCStatus.REJECTED,
                    "message": f"KYC rejected: {rejection_reason}"
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to reject KYC: {e}")
        
        return {"success": False, "error": "Failed to reject KYC"}
    
    async def get_pending_kyc_reviews(
        self,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get list of pending KYC submissions for admin review."""
        try:
            response = self.db.supabase.table("kyc_verifications")\
                .select("*")\
                .in_("status", [
                    "BASIC_SUBMITTED",
                    "ENHANCED_SUBMITTED",
                    "ADVANCED_SUBMITTED"
                ])\
                .order("submitted_at", desc=False)\
                .limit(limit)\
                .execute()
            
            pending = response.data or []
            
            return {
                "success": True,
                "pending_reviews": pending,
                "count": len(pending)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get pending KYC reviews: {e}")
            return {"success": False, "error": str(e)}
    
    async def resubmit_kyc(self, user_id: str) -> Dict[str, Any]:
        """Allow user to resubmit KYC after rejection."""
        try:
            response = self.db.supabase.table("kyc_verifications")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            if not response.data:
                return {"success": False, "error": "KYC not found"}
            
            kyc_record = response.data[0]
            
            if kyc_record.get("status") != KYCStatus.REJECTED:
                return {
                    "success": False,
                    "error": "Only rejected KYC can be resubmitted"
                }
            
            # Reset to submitted status
            kyc_level = kyc_record.get("kyc_level", "enhanced")
            new_status = f"{kyc_level.upper()}_SUBMITTED"
            
            # Clear previous rejection
            update_response = self.db.supabase.table("kyc_verifications")\
                .update({
                    "status": new_status,
                    "rejection_reason": None,
                    "submitted_at": datetime.utcnow().isoformat()
                })\
                .eq("user_id", user_id)\
                .execute()
            
            if update_response.data:
                logger.info(f"✅ KYC resubmitted for user {user_id}")
                
                return {
                    "success": True,
                    "status": new_status,
                    "message": "KYC resubmitted for review"
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to resubmit KYC: {e}")
        
        return {"success": False, "error": "Failed to resubmit KYC"}
