"""
Ensemble Prediction System with Weighting & Conflict Resolution
Architecture Doc §8.1: Combines predictions from multiple models with
dynamic weighting, track record bonuses, and conflict resolution rules.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AgreementLevel(str, Enum):
    UNANIMOUS = "unanimous"
    MAJORITY = "majority"
    SPLIT = "split"
    SINGLE = "single"


@dataclass
class ModelWeight:
    model_id: str
    model_name: str
    base_weight: float
    track_record_bonus: float
    current_weight: float
    sharpe_30d: Optional[float] = None


class EnsemblePredictor:
    """
    Combines predictions from multiple models per §8.1.

    Conflict Resolution Rules:
    1. Unanimous Agreement: All models agree = 95% confidence
    2. Majority (3-of-4): 75% confidence
    3. Split (2-of-4): Abstain = No signal
    4. Single Model: 40% confidence (no mandate)
    """

    MAX_CONFIDENCE = 0.95
    MIN_CONFIDENCE_THRESHOLD = 0.5
    HUMAN_REVIEW_THRESHOLD = 0.6

    def __init__(self, db):
        self.db = db
        self._model_weights: Dict[str, ModelWeight] = {}
        self._prediction_history: List[Dict[str, Any]] = []

    def register_model(
        self,
        model_id: str,
        model_name: str,
        base_weight: float,
    ) -> None:
        """Register a model with its base weight."""
        self._model_weights[model_id] = ModelWeight(
            model_id=model_id,
            model_name=model_name,
            base_weight=base_weight,
            track_record_bonus=0.0,
            current_weight=base_weight,
        )
        logger.info(f"📊 Model registered: {model_name} (base weight: {base_weight:.0%})")

    async def update_track_record(
        self,
        model_id: str,
        rolling_sharpe: float,
        sharpe_threshold: float = 1.2,
        bonus_pct: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Update model weight based on 30-day rolling Sharpe ratio.
        Per §8.1 table: Track Record Bonus = +5% if 30-day Sharpe >= 1.2.
        """
        weight = self._model_weights.get(model_id)
        if not weight:
            return {"success": False, "error": "Model not registered"}

        weight.sharpe_30d = rolling_sharpe
        if rolling_sharpe >= sharpe_threshold:
            weight.track_record_bonus = bonus_pct
        else:
            weight.track_record_bonus = 0.0

        weight.current_weight = min(weight.base_weight + weight.track_record_bonus, 0.50)

        if self.db and self.db.supabase:
            self.db.supabase.table("ensemble_weights").upsert({
                "model_id": model_id,
                "base_weight": weight.base_weight,
                "track_record_bonus": weight.track_record_bonus,
                "current_weight": weight.current_weight,
                "sharpe_30d": weight.sharpe_30d,
                "updated_at": datetime.utcnow().isoformat(),
            }).execute()

        return {
            "success": True,
            "model_id": model_id,
            "current_weight": weight.current_weight,
            "track_record_bonus": weight.track_record_bonus,
        }

    async def ensemble_predict(
        self,
        model_predictions: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Combine predictions from multiple models.

        model_predictions: {
            model_id: {"prediction": 0/1, "confidence": 0-1}
        }

        Returns final signal with conflict resolution.
        """
        if not model_predictions:
            return {"success": False, "error": "No model predictions provided"}

        predictions = []
        total_weight = 0.0
        weighted_sum = 0.0

        for model_id, pred in model_predictions.items():
            weight_obj = self._model_weights.get(model_id)
            weight = weight_obj.current_weight if weight_obj else 0.25

            prediction_val = pred.get("prediction", 0)
            confidence = pred.get("confidence", 0.5)

            predictions.append({
                "model_id": model_id,
                "prediction": prediction_val,
                "confidence": confidence,
                "weight": weight,
            })
            weighted_sum += prediction_val * confidence * weight
            total_weight += weight

        if total_weight == 0:
            return {"success": False, "error": "Total weight is zero"}

        agreement = self._calculate_agreement(predictions)
        final_signal = self._resolve_conflict(predictions, agreement, weighted_sum, total_weight)

        self._prediction_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "predictions": predictions,
            "agreement": agreement.value,
            "final_signal": final_signal,
        })

        if self.db and self.db.supabase:
            self.db.supabase.table("ensemble_predictions").insert({
                "predictions": predictions,
                "agreement_level": agreement.value,
                "final_signal": final_signal["signal_type"],
                "final_confidence": final_signal["confidence"],
                "created_at": datetime.utcnow().isoformat(),
            }).execute()

        return final_signal

    def _calculate_agreement(self, predictions: List[Dict[str, Any]]) -> AgreementLevel:
        """Determine agreement level among model predictions."""
        if len(predictions) == 1:
            return AgreementLevel.SINGLE

        directions = [p["prediction"] for p in predictions]
        bullish_count = sum(1 for d in directions if d == 1)
        bearish_count = sum(1 for d in directions if d == 0)
        total = len(directions)

        if bullish_count == total or bearish_count == total:
            return AgreementLevel.UNANIMOUS
        elif bullish_count >= total * 0.75 or bearish_count >= total * 0.75:
            return AgreementLevel.MAJORITY
        else:
            return AgreementLevel.SPLIT

    def _resolve_conflict(
        self,
        predictions: List[Dict[str, Any]],
        agreement: AgreementLevel,
        weighted_sum: float,
        total_weight: float,
    ) -> Dict[str, Any]:
        """
        Resolve model conflicts per §8.1 rules.
        """
        if agreement == AgreementLevel.UNANIMOUS:
            confidence = self.MAX_CONFIDENCE
        elif agreement == AgreementLevel.MAJORITY:
            confidence = 0.75
        elif agreement == AgreementLevel.SPLIT:
            return {
                "success": True,
                "signal_type": "ABSTAIN",
                "confidence": 0.0,
                "agreement": agreement.value,
                "reason": "Models split — no signal generated (conflict)",
            }
        else:
            confidence = 0.40

        weighted_prediction = weighted_sum / total_weight if total_weight > 0 else 0.5
        signal_type = "BUY" if weighted_prediction > 0.5 else "SELL" if weighted_prediction < 0.5 else "HOLD"

        confidence = min(confidence, self.MAX_CONFIDENCE)
        needs_human_review = confidence < self.HUMAN_REVIEW_THRESHOLD

        return {
            "success": True,
            "signal_type": signal_type,
            "confidence": round(confidence, 4),
            "agreement": agreement.value,
            "weighted_score": round(weighted_prediction, 4),
            "model_count": len(predictions),
            "needs_human_review": needs_human_review,
        }

    def get_ensemble_status(self) -> Dict[str, Any]:
        return {
            "registered_models": len(self._model_weights),
            "model_weights": {
                mid: {
                    "name": w.model_name,
                    "current_weight": w.current_weight,
                    "sharpe_30d": w.sharpe_30d,
                }
                for mid, w in self._model_weights.items()
            },
            "total_predictions": len(self._prediction_history),
        }
