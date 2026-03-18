"""
Performance Monitoring for Recommendation Services
Tracks metrics, response times, and error rates for all recommendation endpoints
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors performance metrics for recommendation services"""
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_calls": 0,
            "success_calls": 0,
            "error_calls": 0,
            "total_response_time_ms": 0,
            "min_response_time_ms": float('inf'),
            "max_response_time_ms": 0,
            "errors": [],
            "last_reset": datetime.utcnow()
        })
        self.start_time = datetime.utcnow()
    
    def record_call(self, endpoint: str, response_time_ms: float, success: bool = True, error: Optional[str] = None):
        """Record a single API call"""
        metric = self.metrics[endpoint]
        metric["total_calls"] += 1
        metric["total_response_time_ms"] += response_time_ms
        metric["min_response_time_ms"] = min(metric["min_response_time_ms"], response_time_ms)
        metric["max_response_time_ms"] = max(metric["max_response_time_ms"], response_time_ms)
        
        if success:
            metric["success_calls"] += 1
        else:
            metric["error_calls"] += 1
            if error:
                metric["errors"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": error
                })
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get stats for a specific endpoint"""
        metric = self.metrics.get(endpoint, {})
        if metric["total_calls"] == 0:
            return {"error": "No data for endpoint"}
        
        avg_response_time = metric["total_response_time_ms"] / metric["total_calls"]
        success_rate = metric["success_calls"] / metric["total_calls"] if metric["total_calls"] > 0 else 0
        
        return {
            "endpoint": endpoint,
            "total_calls": metric["total_calls"],
            "success_calls": metric["success_calls"],
            "error_calls": metric["error_calls"],
            "success_rate": f"{success_rate * 100:.1f}%",
            "avg_response_time_ms": f"{avg_response_time:.2f}",
            "min_response_time_ms": f"{metric['min_response_time_ms']:.2f}",
            "max_response_time_ms": f"{metric['max_response_time_ms']:.2f}",
            "recent_errors": metric["errors"][-5:] if metric["errors"] else []
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get aggregate stats for all endpoints"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "total_endpoints_monitored": len(self.metrics),
            "endpoints": {
                endpoint: self.get_endpoint_stats(endpoint)
                for endpoint in self.metrics.keys()
            }
        }
    
    def reset_stats(self, endpoint: Optional[str] = None):
        """Reset stats for an endpoint or all endpoints"""
        if endpoint:
            if endpoint in self.metrics:
                self.metrics[endpoint] = {
                    "total_calls": 0,
                    "success_calls": 0,
                    "error_calls": 0,
                    "total_response_time_ms": 0,
                    "min_response_time_ms": float('inf'),
                    "max_response_time_ms": 0,
                    "errors": [],
                    "last_reset": datetime.utcnow()
                }
        else:
            self.metrics.clear()
            self.start_time = datetime.utcnow()
    
    def log_summary(self):
        """Log a performance summary"""
        stats = self.get_all_stats()
        logger.info(f"\n📊 Performance Monitoring Summary")
        logger.info(f"Uptime: {stats['uptime_seconds']:.1f}s | Endpoints: {stats['total_endpoints_monitored']}")
        
        for endpoint, ep_stats in stats['endpoints'].items():
            logger.info(f"\n  {endpoint}:")
            logger.info(f"    - Calls: {ep_stats['total_calls']} (Success: {ep_stats['success_calls']}, Errors: {ep_stats['error_calls']})")
            logger.info(f"    - Success Rate: {ep_stats['success_rate']}")
            logger.info(f"    - Response Time: {ep_stats['avg_response_time_ms']}ms avg (min: {ep_stats['min_response_time_ms']}ms, max: {ep_stats['max_response_time_ms']}ms)")
            
            if ep_stats['recent_errors']:
                logger.warning(f"    - Recent Errors:")
                for err in ep_stats['recent_errors']:
                    logger.warning(f"      • {err['message']}")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def record_endpoint_performance(endpoint: str, response_time_ms: float, success: bool = True, error: Optional[str] = None):
    """Record endpoint performance data"""
    monitor = get_performance_monitor()
    monitor.record_call(endpoint, response_time_ms, success, error)


def get_performance_stats() -> Dict[str, Any]:
    """Get all performance stats"""
    monitor = get_performance_monitor()
    return monitor.get_all_stats()


class PerformanceMonitoringMiddleware:
    """ASGI middleware for automated performance monitoring"""
    
    def __init__(self, app, paths_to_monitor: Optional[list] = None):
        self.app = app
        self.paths_to_monitor = paths_to_monitor or [
            "/api/signals",
            "/api/external-signals",
            "/api/market",
            "/api/cache",
            "/api/websocket"
        ]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check if path should be monitored
        path = scope.get("path", "")
        should_monitor = any(path.startswith(p) for p in self.paths_to_monitor)
        
        if not should_monitor:
            await self.app(scope, receive, send)
            return
        
        # Start timing
        start_time = datetime.utcnow()
        
        # Capture response status
        response_status = None
        
        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message.get("status", 0)
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
            
            # Record metrics
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            success = response_status and 200 <= response_status < 300
            
            endpoint = f"{scope['method']} {path}"
            record_endpoint_performance(endpoint, elapsed_ms, success)
            
        except Exception as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            endpoint = f"{scope['method']} {path}"
            record_endpoint_performance(endpoint, elapsed_ms, False, str(e))
            raise
