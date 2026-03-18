"""
Automated Monitoring Alert System
Threshold-based alerts with multiple notification channels
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AlertType(str, Enum):
    """Types of alerts"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    HIGH_ERROR_RATE = "high_error_rate"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATA_DRIFT = "data_drift"
    MODEL_REGRESSION = "model_regression"
    SIGNAL_ANOMALY = "signal_anomaly"
    LIQUIDITY_WARNING = "liquidity_warning"
    PORTFOLIO_WARNING = "portfolio_warning"


@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    metric_name: str
    threshold_value: float
    comparison: str  # "greater_than", "less_than", "equal"
    severity: AlertSeverity
    enabled: bool = True


@dataclass
class Alert:
    """Alert instance"""
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    metric_name: str
    metric_value: float
    threshold: float
    timestamp: str
    acknowledged: bool = False
    resolved: bool = False


class AlertManager:
    """Central alert management system"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.thresholds: Dict[str, AlertThreshold] = {}
        self.handlers: List[Callable] = []
        self.max_history_size = 1000
        
        self._initialize_default_thresholds()
    
    def _initialize_default_thresholds(self):
        """Set default alert thresholds"""
        defaults = [
            AlertThreshold("error_rate_pct", 5.0, "greater_than", AlertSeverity.WARNING),
            AlertThreshold("response_time_ms", 1000, "greater_than", AlertSeverity.WARNING),
            AlertThreshold("rate_limit_usage_pct", 90, "greater_than", AlertSeverity.WARNING),
            AlertThreshold("data_drift_magnitude", 0.3, "greater_than", AlertSeverity.CRITICAL),
            AlertThreshold("model_f1_regression", 0.05, "greater_than", AlertSeverity.WARNING),
        ]
        
        for threshold in defaults:
            self.thresholds[threshold.metric_name] = threshold
    
    def add_alert_handler(self, handler: Callable):
        """Add handler for alert notifications"""
        self.handlers.append(handler)
    
    async def check_threshold(
        self,
        metric_name: str,
        metric_value: float
    ) -> Optional[Alert]:
        """Check if metric exceeds threshold"""
        if metric_name not in self.thresholds:
            return None
        
        threshold = self.thresholds[metric_name]
        if not threshold.enabled:
            return None
        
        violates = False
        if threshold.comparison == "greater_than":
            violates = metric_value > threshold.threshold_value
        elif threshold.comparison == "less_than":
            violates = metric_value < threshold.threshold_value
        elif threshold.comparison == "equal":
            violates = abs(metric_value - threshold.threshold_value) < 0.001
        
        if violates:
            alert = self._create_alert(metric_name, metric_value, threshold)
            await self._trigger_alert(alert)
            return alert
        
        return None
    
    def _create_alert(
        self,
        metric_name: str,
        metric_value: float,
        threshold: AlertThreshold
    ) -> Alert:
        """Create alert instance"""
        alert_type_map = {
            "error_rate_pct": AlertType.HIGH_ERROR_RATE,
            "response_time_ms": AlertType.PERFORMANCE_DEGRADATION,
            "rate_limit_usage_pct": AlertType.RATE_LIMIT_EXCEEDED,
            "data_drift_magnitude": AlertType.DATA_DRIFT,
            "model_f1_regression": AlertType.MODEL_REGRESSION,
        }
        
        alert_type = alert_type_map.get(metric_name, AlertType.SIGNAL_ANOMALY)
        
        return Alert(
            alert_type=alert_type,
            severity=threshold.severity,
            title=f"{alert_type.value.replace('_', ' ').title()} Alert",
            message=f"{metric_name} = {metric_value:.2f} (threshold: {threshold.threshold_value})",
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=threshold.threshold_value,
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def _trigger_alert(self, alert: Alert):
        """Execute alert handlers"""
        alert_key = f"{alert.alert_type}_{alert.metric_name}"
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        if len(self.alert_history) > self.max_history_size:
            self.alert_history.pop(0)
        
        # Call all handlers
        for handler in self.handlers:
            try:
                await handler(alert) if asyncio.iscoroutinefunction(handler) else handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
    
    def acknowledge_alert(self, alert_key: str) -> bool:
        """Mark alert as acknowledged"""
        if alert_key in self.active_alerts:
            self.active_alerts[alert_key].acknowledged = True
            return True
        return False
    
    def resolve_alert(self, alert_key: str) -> bool:
        """Resolve and close alert"""
        if alert_key in self.active_alerts:
            alert = self.active_alerts.pop(alert_key)
            alert.resolved = True
            return True
        return False
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active unresolved alerts"""
        return [asdict(alert) for alert in self.active_alerts.values() if not alert.resolved]
    
    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        return [asdict(alert) for alert in self.alert_history[-limit:]]
    
    def update_threshold(
        self,
        metric_name: str,
        threshold_value: float,
        severity: AlertSeverity = AlertSeverity.WARNING
    ):
        """Update or create alert threshold"""
        if metric_name in self.thresholds:
            self.thresholds[metric_name].threshold_value = threshold_value
            self.thresholds[metric_name].severity = severity
        else:
            self.thresholds[metric_name] = AlertThreshold(
                metric_name=metric_name,
                threshold_value=threshold_value,
                comparison="greater_than",
                severity=severity
            )
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert system statistics"""
        by_severity = {}
        by_type = {}
        
        for alert in self.alert_history:
            severity = alert.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            alert_type = alert.alert_type.value
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
        
        return {
            "total_alerts": len(self.alert_history),
            "active_alerts": len(self.active_alerts),
            "by_severity": by_severity,
            "by_type": by_type,
            "acknowledged_count": sum(1 for a in self.alert_history if a.acknowledged),
            "resolved_count": sum(1 for a in self.alert_history if a.resolved)
        }


class AlertNotificationChannel:
    """Base class for alert notification channels"""
    
    async def send(self, alert: Alert):
        raise NotImplementedError


class LogAlertChannel(AlertNotificationChannel):
    """Log-based alert channel"""
    
    async def send(self, alert: Alert):
        level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.CRITICAL,
            AlertSeverity.EMERGENCY: logging.CRITICAL,
        }.get(alert.severity, logging.WARNING)
        
        logger.log(level, f"[{alert.severity.value}] {alert.title}: {alert.message}")


class SlackAlertChannel(AlertNotificationChannel):
    """Slack notification channel (mock)"""
    
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url
    
    async def send(self, alert: Alert):
        # In production, would call Slack API
        if alert.severity in (AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY):
            logger.warning(f"Slack notification: {alert.title}")


class EmailAlertChannel(AlertNotificationChannel):
    """Email notification channel (mock)"""
    
    def __init__(self, recipients: List[str] = None):
        self.recipients = recipients or []
    
    async def send(self, alert: Alert):
        # In production, would send email
        if alert.severity == AlertSeverity.EMERGENCY:
            logger.warning(f"Email alert to {self.recipients}: {alert.title}")


import asyncio
