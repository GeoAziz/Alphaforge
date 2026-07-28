"""
Prometheus Metrics Service
Exposes application metrics in Prometheus format.
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not installed. Metrics disabled.")


class PrometheusMetrics:
    """Prometheus metrics for AlphaForge."""

    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            return

        # ==========================================================================
        # HTTP Request Metrics
        # ==========================================================================
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "handler", "status"],
        )

        self.http_request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "handler"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        # ==========================================================================
        # Signal Generation Metrics
        # ==========================================================================
        self.signal_generation_total = Counter(
            "signal_generation_total",
            "Total signals generated",
            ["ticker", "source", "signal_type"],
        )

        self.signal_generation_duration = Histogram(
            "signal_generation_duration_seconds",
            "Signal generation duration",
            ["ticker"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
        )

        self.signal_generation_errors = Counter(
            "signal_generation_errors_total",
            "Signal generation errors",
            ["ticker", "error_type"],
        )

        # ==========================================================================
        # Trading Metrics
        # ==========================================================================
        self.trades_total = Counter(
            "trades_total",
            "Total trades executed",
            ["exchange", "direction", "status"],
        )

        self.trade_execution_duration = Histogram(
            "trade_execution_duration_seconds",
            "Trade execution duration",
            ["exchange"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
        )

        self.trade_pnl = Summary(
            "trade_pnl",
            "Trade profit/loss",
            ["exchange", "direction"],
        )

        # ==========================================================================
        # Exchange Health Metrics
        # ==========================================================================
        self.exchange_health = Gauge(
            "exchange_health",
            "Exchange health status (1=healthy, 0=unhealthy)",
            ["exchange"],
        )

        self.exchange_latency = Histogram(
            "exchange_latency_seconds",
            "Exchange API latency",
            ["exchange"],
            buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
        )

        self.exchange_error_rate = Gauge(
            "exchange_error_rate",
            "Exchange error rate",
            ["exchange"],
        )

        # ==========================================================================
        # Database Metrics
        # ==========================================================================
        self.db_connections_active = Gauge(
            "db_connections_active",
            "Active database connections",
        )

        self.db_query_duration = Histogram(
            "db_query_duration_seconds",
            "Database query duration",
            ["operation"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )

        # ==========================================================================
        # Redis Metrics
        # ==========================================================================
        self.redis_operations = Counter(
            "redis_operations_total",
            "Redis operations",
            ["operation", "status"],
        )

        self.redis_hit_rate = Gauge(
            "redis_hit_rate",
            "Redis cache hit rate",
        )

        # ==========================================================================
        # Kafka Metrics
        # ==========================================================================
        self.kafka_messages_published = Counter(
            "kafka_messages_published_total",
            "Kafka messages published",
            ["topic"],
        )

        self.kafka_messages_consumed = Counter(
            "kafka_messages_consumed_total",
            "Kafka messages consumed",
            ["topic", "consumer_group"],
        )

        # ==========================================================================
        # WebSocket Metrics
        # ==========================================================================
        self.websocket_connections = Gauge(
            "alphaforge_websocket_connections_active",
            "Active WebSocket connections",
        )

        # ==========================================================================
        # System Metrics
        # ==========================================================================
        self.active_users = Gauge(
            "active_users",
            "Currently active users",
        )

        self.feature_flag_status = Gauge(
            "feature_flag_status",
            "Feature flag status (1=enabled, 0=disabled)",
            ["flag_name"],
        )

        logger.info("✅ Prometheus metrics initialized")

    def record_request(self, method: str, handler: str, status: int, duration: float):
        """Record an HTTP request."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.http_requests_total.labels(method=method, handler=handler, status=str(status)).inc()
        self.http_request_duration.labels(method=method, handler=handler).observe(duration)

    def record_signal_generation(self, ticker: str, source: str, signal_type: str, duration: float):
        """Record a signal generation event."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.signal_generation_total.labels(
            ticker=ticker, source=source, signal_type=signal_type
        ).inc()
        self.signal_generation_duration.labels(ticker=ticker).observe(duration)

    def record_trade(self, exchange: str, direction: str, status: str, duration: float, pnl: float = 0):
        """Record a trade execution."""
        if not PROMETHEUS_AVAILABLE:
            return
        self.trades_total.labels(exchange=exchange, direction=direction, status=status).inc()
        self.trade_execution_duration.labels(exchange=exchange).observe(duration)
        if pnl != 0:
            self.trade_pnl.labels(exchange=exchange, direction=direction).observe(pnl)

    def get_metrics(self) -> bytes:
        """Get all metrics in Prometheus format."""
        if not PROMETHEUS_AVAILABLE:
            return b"# Metrics not available (prometheus_client not installed)\n"
        return generate_latest()


# Global instance
prometheus_metrics: Optional[PrometheusMetrics] = None


def get_prometheus_metrics() -> PrometheusMetrics:
    """Get or create the global Prometheus metrics."""
    global prometheus_metrics
    if prometheus_metrics is None:
        prometheus_metrics = PrometheusMetrics()
    return prometheus_metrics
