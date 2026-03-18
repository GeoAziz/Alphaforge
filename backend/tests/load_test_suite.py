"""
Load Testing Suite for AlphaForge Backend
Comprehensive performance and stress testing capabilities
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import statistics
import random

logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Individual request result"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: str
    success: bool
    error: Optional[str] = None


@dataclass
class LoadTestMetrics:
    """Aggregated load test metrics"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    response_times: Dict[str, float]  # min, max, mean, median, p95, p99
    errors: Dict[str, int]  # error_type -> count
    requests_per_second: float
    duration_seconds: float
    timestamp: str


class RateLimitTracker:
    """Track rate limiting during load tests"""
    
    def __init__(self):
        self.rate_limit_hits = 0
        self.rate_limit_reset_times: List[float] = []
    
    def record_rate_limit(self, reset_time: float):
        """Record rate limit hit"""
        self.rate_limit_hits += 1
        self.rate_limit_reset_times.append(reset_time)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limit statistics"""
        return {
            "rate_limit_hits": self.rate_limit_hits,
            "avg_reset_time": statistics.mean(self.rate_limit_reset_times) if self.rate_limit_reset_times else 0,
            "max_reset_time": max(self.rate_limit_reset_times) if self.rate_limit_reset_times else 0
        }


class LoadTestRunner:
    """Execute load tests against endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[LoadTestResult] = []
        self.rate_limiter = RateLimitTracker()
    
    async def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        num_requests: int = 100,
        concurrent_requests: int = 10,
        delay_between_requests_ms: int = 0,
        request_generator: Optional[Callable] = None
    ) -> LoadTestMetrics:
        """Execute load test on endpoint"""
        logger.info(f"🚀 Starting load test: {method} {endpoint} ({num_requests} requests)")
        
        start_time = time.time()
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        tasks = []
        for i in range(num_requests):
            tasks.append(self._make_request(
                endpoint=endpoint,
                method=method,
                request_num=i,
                semaphore=semaphore,
                delay_ms=delay_between_requests_ms,
                request_generator=request_generator
            ))
        
        # Execute all requests
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        # Process results
        valid_results = [r for r in results if isinstance(r, LoadTestResult)]
        self.results.extend(valid_results)
        
        # Calculate metrics
        metrics = self._calculate_metrics(endpoint, valid_results, duration)
        
        logger.info(f"✅ Load test completed: {metrics.success_rate:.1%} success rate, {metrics.requests_per_second:.1f} RPS")
        
        return metrics
    
    async def _make_request(
        self,
        endpoint: str,
        method: str,
        request_num: int,
        semaphore: asyncio.Semaphore,
        delay_ms: int,
        request_generator: Optional[Callable]
    ) -> LoadTestResult:
        """Make single request"""
        async with semaphore:
            if delay_ms > 0 and request_num > 0:
                await asyncio.sleep(delay_ms / 1000.0)
            
            start_time = time.time()
            
            try:
                # Mock request (in production, use httpx or aiohttp)
                await asyncio.sleep(random.uniform(0.01, 0.1))
                
                # Simulate occasional failures
                if random.random() < 0.05:  # 5% error rate
                    status_code = random.choice([500, 503, 504])
                    success = False
                    error = "Simulated server error"
                else:
                    status_code = 200
                    success = True
                    error = None
                
                # Simulate occasional rate limits
                if random.random() < 0.02:  # 2% rate limit rate
                    status_code = 429
                    success = False
                    error = "Rate limited"
                    self.rate_limiter.record_rate_limit(60)
                
                response_time_ms = (time.time() - start_time) * 1000
                
                return LoadTestResult(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    timestamp=datetime.utcnow().isoformat(),
                    success=success,
                    error=error
                )
                
            except Exception as e:
                response_time_ms = (time.time() - start_time) * 1000
                return LoadTestResult(
                    endpoint=endpoint,
                    method=method,
                    status_code=0,
                    response_time_ms=response_time_ms,
                    timestamp=datetime.utcnow().isoformat(),
                    success=False,
                    error=str(e)
                )
    
    def _calculate_metrics(
        self,
        endpoint: str,
        results: List[LoadTestResult],
        duration: float
    ) -> LoadTestMetrics:
        """Calculate aggregated metrics"""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        
        response_times = [r.response_time_ms for r in results]
        response_times_sorted = sorted(response_times)
        
        error_counts = {}
        for r in results:
            if r.error:
                error_counts[r.error] = error_counts.get(r.error, 0) + 1
        
        metrics = LoadTestMetrics(
            endpoint=endpoint,
            total_requests=total,
            successful_requests=successful,
            failed_requests=failed,
            success_rate=successful / total if total > 0 else 0,
            response_times={
                "min_ms": min(response_times) if response_times else 0,
                "max_ms": max(response_times) if response_times else 0,
                "mean_ms": statistics.mean(response_times) if response_times else 0,
                "median_ms": statistics.median(response_times) if response_times else 0,
                "p95_ms": response_times_sorted[int(len(response_times_sorted) * 0.95)] if len(response_times_sorted) > 0 else 0,
                "p99_ms": response_times_sorted[int(len(response_times_sorted) * 0.99)] if len(response_times_sorted) > 0 else 0,
            },
            errors=error_counts,
            requests_per_second=total / duration if duration > 0 else 0,
            duration_seconds=duration,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return metrics
    
    async def run_soak_test(
        self,
        endpoint: str,
        method: str,
        duration_minutes: int = 30,
        requests_per_second: int = 10
    ) -> Dict[str, Any]:
        """Run soak test (sustained load)"""
        logger.info(f"🔄 Starting soak test: {method} {endpoint} for {duration_minutes} minutes at {requests_per_second} RPS")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        request_count = 0
        interval = 1.0 / requests_per_second
        
        results = []
        
        while time.time() < end_time:
            request_time = time.time()
            
            result = await self._make_request(
                endpoint=endpoint,
                method=method,
                request_num=request_count,
                semaphore=asyncio.Semaphore(1),
                delay_ms=0,
                request_generator=None
            )
            
            results.append(result)
            request_count += 1
            
            # Rate limit to RPS
            elapsed = time.time() - request_time
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
        
        duration = time.time() - start_time
        metrics = self._calculate_metrics(endpoint, results, duration)
        
        logger.info(f"✅ Soak test completed: {request_count} requests over {duration/60:.1f} minutes")
        
        return {
            "soak_test_results": asdict(metrics),
            "total_duration_minutes": duration / 60,
            "rate_limit_stats": self.rate_limiter.get_stats()
        }
    
    async def run_spike_test(
        self,
        endpoint: str,
        method: str,
        normal_rps: int = 10,
        spike_rps: int = 100,
        spike_duration_seconds: int = 30,
        test_duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """Run spike test (sudden traffic spike)"""
        logger.info(f"📈 Starting spike test: {method} {endpoint}")
        
        start_time = time.time()
        end_time = start_time + (test_duration_minutes * 60)
        spike_start = start_time + 60  # Spike after 1 minute
        spike_end = spike_start + spike_duration_seconds
        
        request_count = 0
        results = []
        
        while time.time() < end_time:
            current_time = time.time()
            
            # Determine current RPS
            if spike_start <= current_time < spike_end:
                current_rps = spike_rps
            else:
                current_rps = normal_rps
            
            interval = 1.0 / current_rps
            
            # Make request
            result = await self._make_request(
                endpoint=endpoint,
                method=method,
                request_num=request_count,
                semaphore=asyncio.Semaphore(1),
                delay_ms=0,
                request_generator=None
            )
            
            results.append(result)
            request_count += 1
            
            # Rate limit
            elapsed = time.time() - current_time
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)
        
        duration = time.time() - start_time
        
        # Analyze pre-spike vs spike vs post-spike
        pre_spike_results = [r for r in results if r.timestamp < datetime.fromtimestamp(spike_start).isoformat()]
        spike_results = [r for r in results if datetime.fromtimestamp(spike_start).isoformat() <= r.timestamp < datetime.fromtimestamp(spike_end).isoformat()]
        post_spike_results = [r for r in results if r.timestamp >= datetime.fromtimestamp(spike_end).isoformat()]
        
        return {
            "spike_test_results": {
                "pre_spike": asdict(self._calculate_metrics(endpoint, pre_spike_results, 60)) if pre_spike_results else None,
                "spike": asdict(self._calculate_metrics(endpoint, spike_results, spike_duration_seconds)) if spike_results else None,
                "post_spike": asdict(self._calculate_metrics(endpoint, post_spike_results, 240)) if post_spike_results else None
            },
            "total_duration_minutes": duration / 60,
            "rate_limit_stats": self.rate_limiter.get_stats()
        }
    
    async def run_stress_test(
        self,
        endpoint: str,
        method: str,
        starting_rps: int = 10,
        increment_rps: int = 10,
        increment_interval_seconds: int = 30,
        max_rps: int = 500,
        failure_threshold_pct: float = 10.0
    ) -> Dict[str, Any]:
        """Run stress test (incrementally increase load until failure)"""
        logger.info(f"💥 Starting stress test: {method} {endpoint}")
        
        stages = []
        current_rps = starting_rps
        
        while current_rps <= max_rps:
            logger.info(f"📊 Stress test stage: {current_rps} RPS")
            
            start_time = time.time()
            end_time = start_time + increment_interval_seconds
            request_count = 0
            results = []
            
            while time.time() < end_time:
                current_time = time.time()
                interval = 1.0 / current_rps
                
                result = await self._make_request(
                    endpoint=endpoint,
                    method=method,
                    request_num=request_count,
                    semaphore=asyncio.Semaphore(1),
                    delay_ms=0,
                    request_generator=None
                )
                
                results.append(result)
                request_count += 1
                
                elapsed = time.time() - current_time
                if elapsed < interval:
                    await asyncio.sleep(interval - elapsed)
            
            metrics = self._calculate_metrics(endpoint, results, increment_interval_seconds)
            failure_rate = (1 - metrics.success_rate) * 100
            
            stage_result = {
                "rps": current_rps,
                "metrics": asdict(metrics),
                "failure_rate_pct": failure_rate
            }
            stages.append(stage_result)
            
            # Check if we've exceeded failure threshold
            if failure_rate > failure_threshold_pct:
                logger.warning(f"⚠️ Failure threshold exceeded at {current_rps} RPS ({failure_rate:.1f}% failures)")
                break
            
            current_rps += increment_rps
        
        return {
            "stress_test_stages": stages,
            "breaking_point_rps": stages[-1]["rps"] if stages else 0,
            "rate_limit_stats": self.rate_limiter.get_stats()
        }
    
    def get_all_results(self) -> List[Dict[str, Any]]:
        """Get all test results"""
        return [asdict(r) for r in self.results]
    
    def clear_results(self):
        """Clear stored results"""
        self.results.clear()
