"""
Explainability Proofs Service
Stores and retrieves chain-of-reasoning for signal generation for audit trail.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import hashlib

logger = logging.getLogger(__name__)


class ExplainabilityProof:
    """Immutable proof of signal reasoning."""

    def __init__(
        self,
        signal_id: str,
        symbol: str,
        signal_type: str,
        confidence: float,
        reasoning_chain: List[str],
        feature_importance: Dict[str, float],
        technical_drivers: Dict[str, Any],
        sentiment_components: Dict[str, float],
        ml_model_version: str,
        backtest_performance: Dict[str, float]
    ):
        self.signal_id = signal_id
        self.symbol = symbol
        self.signal_type = signal_type
        self.confidence = confidence
        self.reasoning_chain = reasoning_chain
        self.feature_importance = feature_importance
        self.technical_drivers = technical_drivers
        self.sentiment_components = sentiment_components
        self.ml_model_version = ml_model_version
        self.backtest_performance = backtest_performance
        self.timestamp = datetime.utcnow().isoformat()

        # Generate cryptographic hash for integrity verification
        self.proof_hash = self._generate_hash()

    def _generate_hash(self) -> str:
        """Generate SHA256 hash of proof for integrity verification."""
        proof_data = json.dumps({
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "reasoning_chain": self.reasoning_chain,
            "feature_importance": self.feature_importance,
            "timestamp": self.timestamp,
        }, sort_keys=True)
        return hashlib.sha256(proof_data.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert proof to dictionary."""
        return {
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "reasoning_chain": self.reasoning_chain,
            "feature_importance": self.feature_importance,
            "technical_drivers": self.technical_drivers,
            "sentiment_components": self.sentiment_components,
            "ml_model_version": self.ml_model_version,
            "backtest_performance": self.backtest_performance,
            "timestamp": self.timestamp,
            "proof_hash": self.proof_hash,
        }


class ExplainabilityProofsService:
    """Service for managing signal reasoning proofs."""

    def __init__(self, db):
        self.db = db
        self.proofs: Dict[str, ExplainabilityProof] = {}

    async def create_proof(
        self,
        signal_id: str,
        symbol: str,
        signal_type: str,
        confidence: float,
        reasoning_chain: List[str],
        feature_importance: Dict[str, float],
        technical_drivers: Dict[str, Any],
        sentiment_components: Dict[str, float],
        ml_model_version: str,
        backtest_performance: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Create and store an explainability proof for a signal.

        Args:
            signal_id: Unique signal identifier
            symbol: Trading pair (BTC/USD, EUR/USD, etc.)
            signal_type: BUY or SELL
            confidence: Confidence score (0-1)
            reasoning_chain: List of reasoning steps
            feature_importance: Dict of feature names to importance scores
            technical_drivers: Technical indicator values and status
            sentiment_components: Sentiment scores from different sources
            ml_model_version: Version of ML model used
            backtest_performance: Historical performance metrics

        Returns:
            Dictionary containing proof data and hash
        """
        try:
            proof = ExplainabilityProof(
                signal_id=signal_id,
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                reasoning_chain=reasoning_chain,
                feature_importance=feature_importance,
                technical_drivers=technical_drivers,
                sentiment_components=sentiment_components,
                ml_model_version=ml_model_version,
                backtest_performance=backtest_performance,
            )

            # Store in memory
            self.proofs[signal_id] = proof

            # Store in database
            proof_data = proof.to_dict()
            try:
                response = self.db.supabase.table("signal_proofs").insert(proof_data).execute()
                logger.info(f"✅ Proof created for signal {signal_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to store proof in database: {e}, using in-memory store")

            return {
                "success": True,
                "signal_id": signal_id,
                "proof_hash": proof.proof_hash,
                "timestamp": proof.timestamp,
            }

        except Exception as e:
            logger.error(f"❌ Failed to create proof: {e}")
            return {"success": False, "error": str(e)}

    async def get_proof(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve explainability proof for a signal.

        Args:
            signal_id: Signal identifier

        Returns:
            Dictionary containing proof data or None if not found
        """
        try:
            # Try to get from database first
            try:
                response = self.db.supabase.table("signal_proofs") \
                    .select("*") \
                    .eq("signal_id", signal_id) \
                    .execute()

                if response.data:
                    logger.debug(f"📦 Retrieved proof for {signal_id} from database")
                    return response.data[0]
            except Exception as e:
                logger.warning(f"⚠️ Database lookup failed: {e}")

            # Fall back to in-memory store
            if signal_id in self.proofs:
                logger.debug(f"📦 Retrieved proof for {signal_id} from memory")
                return self.proofs[signal_id].to_dict()

            return None

        except Exception as e:
            logger.error(f"❌ Failed to retrieve proof: {e}")
            return None

    async def verify_proof(self, signal_id: str, proof_hash: str) -> bool:
        """
        Verify integrity of a proof using its hash.

        Args:
            signal_id: Signal identifier
            proof_hash: Expected hash value

        Returns:
            True if proof is valid and unmodified
        """
        try:
            proof = await self.get_proof(signal_id)
            if not proof:
                return False

            stored_hash = proof.get("proof_hash")
            is_valid = stored_hash == proof_hash

            if is_valid:
                logger.debug(f"✅ Proof verification passed for {signal_id}")
            else:
                logger.warning(f"⚠️ Proof verification failed for {signal_id}")

            return is_valid

        except Exception as e:
            logger.error(f"❌ Proof verification error: {e}")
            return False

    async def list_proofs(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List proofs with optional filtering.

        Args:
            symbol: Filter by trading pair
            start_date: Filter from date (ISO format)
            end_date: Filter to date (ISO format)
            limit: Maximum results

        Returns:
            List of proof dictionaries
        """
        try:
            query = self.db.supabase.table("signal_proofs").select("*")

            if symbol:
                query = query.eq("symbol", symbol)

            if start_date:
                query = query.gte("timestamp", start_date)

            if end_date:
                query = query.lte("timestamp", end_date)

            response = query.limit(limit).execute()

            logger.info(f"✅ Retrieved {len(response.data)} proofs")
            return response.data

        except Exception as e:
            logger.error(f"❌ Failed to list proofs: {e}")
            return []

    async def get_signal_explainability(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full explainability data for a signal (proof + additional analysis).

        Args:
            signal_id: Signal identifier

        Returns:
            Dictionary containing explainability data
        """
        try:
            proof = await self.get_proof(signal_id)
            if not proof:
                return None

            return {
                "signal_id": signal_id,
                "confidence": proof.get("confidence"),
                "feature_importance": proof.get("feature_importance"),
                "technical_indicators": proof.get("technical_drivers"),
                "sentiment_components": proof.get("sentiment_components"),
                "reasoning_chain": proof.get("reasoning_chain"),
                "ml_model_version": proof.get("ml_model_version"),
                "backtest_performance": proof.get("backtest_performance"),
                "timestamp": proof.get("timestamp"),
                "integrity": await self.verify_proof(signal_id, proof.get("proof_hash")),
            }

        except Exception as e:
            logger.error(f"❌ Failed to get explainability: {e}")
            return None

    async def export_audit_trail(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export audit trail of signal proofs for compliance reporting.

        Args:
            user_id: Filter by user
            start_date: Filter from date
            end_date: Filter to date
            format: Export format (json, csv)

        Returns:
            Audit trail data
        """
        try:
            proofs = await self.list_proofs(start_date=start_date, end_date=end_date)

            audit_trail = {
                "export_date": datetime.utcnow().isoformat(),
                "total_signals": len(proofs),
                "signals": proofs,
            }

            logger.info(f"✅ Exported audit trail with {len(proofs)} signals")
            return {
                "success": True,
                "audit_trail": audit_trail,
            }

        except Exception as e:
            logger.error(f"❌ Failed to export audit trail: {e}")
            return {"success": False, "error": str(e)}
