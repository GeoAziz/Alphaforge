"""
Circuit Breaker & Multi-Exchange Failover Service
Implements circuit breaker pattern for exchange connectivity and automatic failover.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class ExchangeHealth:
    """Tracks health state of a single exchange."""

    def __init__(self, name: str):
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.consecutive_failures = 0
        self.total_requests = 0
        self.total_failures = 0
        self.avg_latency_ms = 0.0
        self._latency_samples: List[float] = []

    @property
    def error_rate(self) -> float:
        """Calculate error rate over recent requests."""
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests

    @property
    def is_healthy(self) -> bool:
        """Check if exchange is in healthy state."""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self, latency_ms: float = 0):
        """Record a successful request."""
        self.total_requests += 1
        self.success_count += 1
        self.consecutive_failures = 0
        self.last_success_time = datetime.utcnow()

        # Track latency (rolling 100 samples)
        self._latency_samples.append(latency_ms)
        if len(self._latency_samples) > 100:
            self._latency_samples = self._latency_samples[-100:]
        self.avg_latency_ms = sum(self._latency_samples) / len(self._latency_samples)

        # Transition from HALF_OPEN to CLOSED
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info(f"✅ Circuit closed for {self.name} (recovered)")

    def record_failure(self):
        """Record a failed request."""
        self.total_requests += 1
        self.total_failures += 1
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure_time = datetime.utcnow()

        # Open circuit after 3 consecutive failures
        if self.consecutive_failures >= 3 and self.state == CircuitState.CLOSED:
            self.state = CircuitState.OPEN
            logger.warning(
                f"🔴 Circuit OPENED for {self.name} "
                f"({self.consecutive_failures} consecutive failures)"
            )

    def should_allow_request(self) -> bool:
        """Check if request should be allowed through."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery window has elapsed (5 minutes)
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= 300:  # 5 minutes
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"🟡 Circuit HALF-OPEN for {self.name} (testing recovery)")
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True  # Allow one test request

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "consecutive_failures": self.consecutive_failures,
            "error_rate": round(self.error_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "total_requests": self.total_requests,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
        }


class MultiExchangeFailover:
    """Manages multi-exchange connectivity with automatic failover."""

    def __init__(self):
        self.exchanges: Dict[str, ExchangeHealth] = {}
        self._exchange_priority: List[str] = ["binance", "bybit", "okx", "kraken"]
        self._active_exchange: str = "binance"
        self._recovery_percentage: float = 0.1  # 10% traffic shift per recovery step

    def register_exchange(self, name: str):
        """Register an exchange for health tracking."""
        if name not in self.exchanges:
            self.exchanges[name] = ExchangeHealth(name)
            if name not in self._exchange_priority:
                self._exchange_priority.append(name)
            logger.info(f"📊 Exchange registered: {name}")

    def get_active_exchange(self) -> str:
        """Get the currently active (primary) exchange."""
        # Find first healthy exchange in priority order
        for name in self._exchange_priority:
            if name in self.exchanges and self.exchanges[name].is_healthy:
                return name
        # Fallback to first available
        return self._exchange_priority[0] if self._exchange_priority else "binance"

    def get_exchange_for_request(self) -> str:
        """Get best available exchange for a new request."""
        active = self.get_active_exchange()

        if self.exchanges.get(active, ExchangeHealth(active)).should_allow_request():
            return active

        # Active exchange is circuit-open, find fallback
        for name in self._exchange_priority:
            if name != active and name in self.exchanges:
                health = self.exchanges[name]
                if health.should_allow_request():
                    logger.info(f"🔄 Failing over from {active} to {name}")
                    return name

        # All exchanges down
        logger.error("❌ All exchanges are circuit-open. No exchange available.")
        return active  # Return primary anyway (let it fail)

    async def execute_with_failover(
        self,
        operation: Callable,
        operation_name: str = "operation",
    ) -> Dict[str, Any]:
        """Execute an operation with automatic failover."""
        errors = []

        for exchange_name in self._exchange_priority:
            if exchange_name not in self.exchanges:
                continue

            health = self.exchanges[exchange_name]
            if not health.should_allow_request():
                continue

            start_time = time.time()
            try:
                result = await operation(exchange_name)
                latency_ms = (time.time() - start_time) * 1000
                health.record_success(latency_ms)

                if exchange_name != self._active_exchange:
                    logger.info(f"✅ {operation_name} succeeded on {exchange_name}")

                return {
                    "success": True,
                    "exchange": exchange_name,
                    "latency_ms": round(latency_ms, 2),
                    "data": result,
                }
            except Exception as e:
                health.record_failure()
                errors.append({"exchange": exchange_name, "error": str(e)})
                logger.warning(f"⚠️ {operation_name} failed on {exchange_name}: {e}")

        # All exchanges failed
        return {
            "success": False,
            "error": "All exchanges failed",
            "details": errors,
        }

    # ==========================================================================
    # Health Check
    # ==========================================================================

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all exchanges."""
        return {
            "active_exchange": self.get_active_exchange(),
            "exchanges": {
                name: health.to_dict()
                for name, health in self.exchanges.items()
            },
            "priority_order": self._exchange_priority,
        }

    def get_exchange_for_user(self, user_id: str, preferred_exchange: Optional[str] = None) -> str:
        """Get exchange for a specific user, considering preferences."""
        if preferred_exchange and preferred_exchange in self.exchanges:
            health = self.exchanges[preferred_exchange]
            if health.should_allow_request():
                return preferred_exchange

        # Route to best available
        return self.get_exchange_for_request()

    # ==========================================================================
    # Latency Monitoring
    # ==========================================================================

    def check_latency_health(self, threshold_ms: float = 1000) -> Dict[str, Any]:
        """Check if exchanges are within latency thresholds."""
        results = {}
        for name, health in self.exchanges.items():
            is_healthy = health.avg_latency_ms <= threshold_ms or health.total_requests < 10
            results[name] = {
                "avg_latency_ms": round(health.avg_latency_ms, 2),
                "threshold_ms": threshold_ms,
                "within_threshold": is_healthy,
            }
        return results


# Global instance
multi_exchange_failover: Optional[MultiExchangeFailover] = None


def get_multi_exchange_failover() -> MultiExchangeFailover:
    """Get or create the global multi-exchange failover manager."""
    global multi_exchange_failover
    if multi_exchange_failover is None:
        multi_exchange_failover = MultiExchangeFailover()
        # Register default exchanges
        for exchange in ["binance", "bybit", "okx", "kraken"]:
            multi_exchange_failover.register_exchange(exchange)
    return multi_exchange_failover
