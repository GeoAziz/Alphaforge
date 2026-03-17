"""
Creator Verification Service - Manages creator verification pipeline and reputation.
Handles 5-stage verification process and reputation scoring.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CreatorVerificationService:
    """Manages creator verification workflow and reputation."""
    
    def __init__(self, db):
        self.db = db
        
        # Verification stages
        self.STAGES = [
            "stage_1_intro",
            "stage_2_paper_trading",
            "stage_3_performance_check",
            "stage_4_kyc",
            "stage_5_approved"
        ]
    
    async def get_verification_status(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get creator's full verification status and pipeline."""
        try:
            # Get user
            user_response = self.db.supabase.table("users")\
                .select("verification_stage, kyc_status")\
                .eq("id", user_id)\
                .execute()
            
            if not user_response.data:
                return {"success": False, "error": "User not found"}
            
            user_data = user_response.data[0]
            current_stage = user_data.get("verification_stage", "stage_1_intro")
            
            # Get creator profile
            creator_response = self.db.supabase.table("creator_profiles")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            creator_profile = creator_response.data[0] if creator_response.data else None
            
            # Build pipeline stages
            stages = []
            for idx, stage in enumerate(self.STAGES):
                is_current = stage == current_stage
                is_completed = self.STAGES.index(stage) < self.STAGES.index(current_stage)
                
                stages.append({
                    "stage": idx + 1,
                    "name": self._stage_name(stage),
                    "status": "completed" if is_completed else "current" if is_current else "pending",
                    "stage_key": stage,
                    "description": self._stage_description(stage)
                })
            
            return {
                "success": True,
                "user_id": user_id,
                "current_stage": current_stage,
                "kyc_status": user_data.get("kyc_status"),
                "pipeline": stages,
                "creator_profile": creator_profile,
                "reputation_score": creator_profile.get("reputation_score", 0) if creator_profile else 0
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to get verification status: {e}")
            return {"success": False, "error": str(e)}
    
    async def submit_strategy(
        self,
        user_id: str,
        strategy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit strategy for creator verification."""
        try:
            strategy_record = {
                "user_id": user_id,
                "name": strategy_data.get("name"),
                "description": strategy_data.get("description"),
                "parameters": strategy_data.get("parameters", {}),
                "backtest_results": strategy_data.get("backtest_results", {}),
                "status": "PENDING_REVIEW",
                "submitted_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("creator_strategies").insert(strategy_record).execute()
            
            if response.data:
                # Update verification stage if needed
                current_stage_num = self._get_stage_number(user_id)
                if current_stage_num == 1:
                    # Move to stage 2 (paper trading)
                    self.db.supabase.table("users")\
                        .update({"verification_stage": "stage_2_paper_trading"})\
                        .eq("id", user_id)\
                        .execute()
                
                logger.info(f"✅ Strategy submitted by {user_id}")
                return {"success": True, "strategy_id": response.data[0]["id"]}
            
        except Exception as e:
            logger.error(f"❌ Failed to submit strategy: {e}")
        
        return {"success": False, "error": str(e)}
    
    async def get_reputation_score(
        self,
        creator_id: str
    ) -> Dict[str, Any]:
        """Calculate creator reputation score."""
        try:
            # Get creator profile
            creator_response = self.db.supabase.table("creator_profiles")\
                .select("*")\
                .eq("user_id", creator_id)\
                .execute()
            
            if not creator_response.data:
                return {"success": False, "error": "Creator not found"}
            
            creator = creator_response.data[0]
            
            # Calculate reputation components
            win_rate = creator.get("win_rate", 0) * 0.3  # 30% weight
            signals_quality = creator.get("avg_confidence", 0) * 0.3  # 30% weight
            follower_count = min(creator.get("total_followers", 0) / 1000, 1.0) * 0.2  # 20% weight
            verified_status = (1.0 if creator.get("verified_at") else 0) * 0.2  # 20% weight
            
            # Total reputation (0-10 scale)
            reputation_score = (win_rate + signals_quality + follower_count + verified_status) * 10
            
            # Determine tier
            if reputation_score >= 8:
                tier = "Tier 1 Institutional"
            elif reputation_score >= 6:
                tier = "Tier 2 Professional"
            elif reputation_score >= 4:
                tier = "Tier 3 Verified"
            else:
                tier = "Unverified"
            
            return {
                "success": True,
                "creator_id": creator_id,
                "reputation_score": round(reputation_score, 1),
                "tier": tier,
                "components": {
                    "win_rate": f"{win_rate:.1f}",
                    "signal_quality": f"{signals_quality:.1f}",
                    "follower_influence": f"{follower_count:.1f}",
                    "verified_status": f"{verified_status:.1f}"
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to calculate reputation: {e}")
            return {"success": False, "error": str(e)}
    
    async def advance_to_stage(
        self,
        user_id: str,
        next_stage: str
    ) -> Dict[str, Any]:
        """Advance creator to next verification stage."""
        try:
            update_data = {
                "verification_stage": next_stage,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("users")\
                .update(update_data)\
                .eq("id", user_id)\
                .execute()
            
            if response.data:
                logger.info(f"✅ User {user_id} advanced to {next_stage}")
                return {"success": True}
        
        except Exception as e:
            logger.error(f"❌ Failed to advance stage: {e}")
        
        return {"success": False, "error": str(e)}
    
    def _stage_name(self, stage: str) -> str:
        """Get readable stage name."""
        names = {
            "stage_1_intro": "Account Setup",
            "stage_2_paper_trading": "Paper Trading",
            "stage_3_performance_check": "Performance Review",
            "stage_4_kyc": "KYC Verification",
            "stage_5_approved": "Approved Creator"
        }
        return names.get(stage, stage)
    
    def _stage_description(self, stage: str) -> str:
        """Get stage description."""
        descriptions = {
            "stage_1_intro": "Complete your profile and agree to terms",
            "stage_2_paper_trading": "Run 20+ paper trades to demonstrate strategy",
            "stage_3_performance_check": "Achieve minimum 55% win rate in paper trading",
            "stage_4_kyc": "Complete KYC verification (AML compliant)",
            "stage_5_approved": "Approved to publish strategies on marketplace"
        }
        return descriptions.get(stage, "")
    
    def _get_stage_number(self, user_id: str) -> int:
        """Get current stage number (1-5)."""
        try:
            response = self.db.supabase.table("users")\
                .select("verification_stage")\
                .eq("id", user_id)\
                .execute()
            
            if response.data:
                stage = response.data[0].get("verification_stage")
                return self.STAGES.index(stage) + 1 if stage in self.STAGES else 1
        except:
            pass
        
        return 1
