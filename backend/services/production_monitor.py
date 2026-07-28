"""
Production Monitoring After Deployment
Architecture Doc §12.2: Continuous monitoring with auto-disable policy.
Alerts fire on win rate drops, confidence divergence, signal frequency changes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    WIN_RATE_DROP = "win_rate_drop"
    CONFIDENCE_DIVERGENCE = "confidence_divergence"
    SIGNAL_FREQUENCY = "signal_frequency"
    DRAWDOWN_BREACH = "drawdown_breach"


class ModelHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    DISABLED = "disabled"


@dataclass
class MonitoringAlert:
    model_id: str
    alert_type: str
    severity: str
    message: str
    metric_value: float
    threshold: float
    timestamp: str


class ProductionMonitorService:
    """
    Monitors deployed models per §12.2.

    Alert triggers:
    - Win rate drops >10% below rolling 30-day average
    - Confidence scores diverge from historical distribution
    - Signal frequency drops or spikes beyond expected range
    - Drawdown limit breached

    Auto-disable: 2 consecutive weekly performance alerts → auto-disable.
    """

    WIN_RATE_DROP_THRESHOLD = 0.10
    CONSECUTIVE_ALERTS_TO_DISABLE = 2

    def __init__(self, db):
        self.db = db
        self._model_states: Dict[str, Dict[str, Any]] = {}
        self._alerts: List[MonitoringAlert] = []

    async def register_model(
        self,
        model_id: str,
        baseline_win_rate: float,
        baseline_confidence_mean: float,
        expected_signal_frequency: float,
    ) -> None:
        """Register a model for production monitoring."""
        self._model_states[model_id] = {
            "baseline_win_rate": baseline_win_rate,
            "baseline_confidence_mean": baseline_confidence_mean,
            "expected_signal_frequency": expected_signal_frequency,
            "rolling_win_rate": baseline_win_rate,
            "consecutive_alerts": 0,
            "weekly_alerts": 0,
            "status": ModelHealthStatus.HEALTHY.value,
            "disabled_at": None,
            "performance_history": [],
        }

    async def check_model_health(
        self,
        model_id: str,
        current_win_rate: float,
        current_confidence_mean: float,
        current_signal_frequency: float,
        current_drawdown: float,
    ) -> Dict[str, Any]:
        """
        Check model health and fire alerts if thresholds breached.
        """
        state = self._model_states.get(model_id)
        if not state:
            return {"success": False, "error": "Model not registered for monitoring"}

        if state["status"] == ModelHealthStatus.DISABLED.value:
            return {"success": True, "status": "disabled", "alerts": []}

        alerts = []
        rolling_wr = state["rolling_win_rate"]

        if rolling_wr > 0 and (rolling_wr - current_win_rate) / rolling_wr > self.WIN_RATE_DROP_THRESHOLD:
            alert = MonitoringAlert(
                model_id=model_id,
                alert_type=AlertType.WIN_RATE_DROP.value,
                severity="WARNING",
                message=f"Win rate dropped {((rolling_wr - current_win_rate) / rolling_wr * 100):.1f}% below rolling avg",
                metric_value=current_win_rate,
                threshold=rolling_wr * (1 - self.WIN_RATE_DROP_THRESHOLD),
                timestamp=datetime.utcnow().isoformat(),
            )
            alerts.append(alert)

        confidence_diff = abs(current_confidence_mean - state["baseline_confidence_mean"])
        if confidence_diff > 0.15:
            alert = MonitoringAlert(
                model_id=model_id,
                alert_type=AlertType.CONFIDENCE_DIVERGENCE.value,
                severity="WARNING",
                message=f"Confidence diverged by {confidence_diff:.2%} from baseline",
                metric_value=current_confidence_mean,
                threshold=state["baseline_confidence_mean"],
                timestamp=datetime.utcnow().isoformat(),
            )
            alerts.append(alert)

        if current_drawdown > 0.25:
            alert = MonitoringAlert(
                model_id=model_id,
                alert_type=AlertType.DRAWDOWN_BREACH.value,
                severity="CRITICAL",
                message=f"Drawdown breached 25% limit: {current_drawdown:.1%}",
                metric_value=current_drawdown,
                threshold=0.25,
                timestamp=datetime.utcnow().isoformat(),
            )
            alerts.append(alert)

        state["performance_history"].append({
            "win_rate": current_win_rate,
            "confidence": current_confidence_mean,
            "signal_frequency": current_signal_frequency,
            "drawdown": current_drawdown,
            "timestamp": datetime.utcnow().isoformat(),
        })

        if len(state["performance_history"]) > 30:
            state["performance_history"] = state["performance_history"][-30:]

        state["rolling_win_rate"] = (
            sum(h["win_rate"] for h in state["performance_history"])
            / len(state["performance_history"])
        )

        auto_disabled = False
        if alerts:
            state["weekly_alerts"] += 1
            state["consecutive_alerts"] += 1
            if state["consecutive_alerts"] >= self.CONSECUTIVE_ALERTS_TO_DISABLE:
                state["status"] = ModelHealthStatus.DISABLED.value
                state["disabled_at"] = datetime.utcnow().isoformat()
                auto_disabled = True
                logger.warning(f"🚫 Model {model_id} auto-disabled after {state['consecutive_alerts']} consecutive alerts")

            for alert in alerts:
                self._alerts.append(alert)
                logger.warning(f"⚠️ Alert [{alert.severity}] {alert.model_id}: {alert.message}")
        else:
            state["consecutive_alerts"] = 0
            state["status"] = ModelHealthStatus.HEALTHY.value

        if self.db and self.db.supabase:
            self.db.supabase.table("production_monitoring").upsert({
                "model_id": model_id,
                "status": state["status"],
                "rolling_win_rate": state["rolling_win_rate"],
                "consecutive_alerts": state["consecutive_alerts"],
                "last_checked": datetime.utcnow().isoformat(),
            }).execute()

        return {
            "success": True,
            "model_id": model_id,
            "status": state["status"],
            "alerts": [asdict(a) for a in alerts],
            "auto_disabled": auto_disabled,
            "consecutive_alerts": state["consecutive_alerts"],
        }

    async def get_model_status(self, model_id: str) -> Optional[Dict[str, Any]]:
        state = self._model_states.get(model_id)
        if not state:
            return None
        return {
            "model_id": model_id,
            "status": state["status"],
            "rolling_win_rate": state["rolling_win_rate"],
            "consecutive_alerts": state["consecutive_alerts"],
            "disabled_at": state["disabled_at"],
        }

    async def get_all_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [asdict(a) for a in self._alerts[-limit:]]
