"""
Load Testing Suite
Comprehensive load and stress testing tools for system validation
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import random

logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Load test execution result"""
    test_name: str
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    throughput_req_per_sec: float
    error_rate_pct: float
    test_duration_seconds: float
    timestamp: str


class LoadTestRunner:
    """Execute load tests against endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[LoadTestResult] = []
    
    async def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        num_requests: int = 100,
        concurrent_requests: int = 10,
        payload: Dict[str, Any] = None,
        test_name: str = None
    ) -> LoadTestResult:
        """Execute load test against endpoint"""
        
        if test_name is None:
            test_name = f"{method} {endpoint}"
        
        logger.info(f"🧪 Starting load test: {test_name}")
        logger.info(f"   Requests: {num_requests}, Concurrency: {concurrent_requests}")
        
        response_times = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        # Create batches of requests
        batches = [
            num_requests // concurrent_requests
            for _ in range(concurrent_requests - 1)
        ]
        batches.append(num_requests - sum(batches))
        
        for batch_size in batches:
            tasks = [
                self._simulate_request(endpoint, method, payload)
                for _ in range(batch_size)
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                else:
                    response_times.append(result)
                    successful += 1
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Calculate metrics
        response_times_sorted = sorted(response_times) if response_times else [0]
        
        result = LoadTestResult(
            test_name=test_name,
            endpoint=endpoint,
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=failed,
            avg_response_time_ms=np.mean(response_times_sorted) if response_times_sorted else 0,
            min_response_time_ms=np.percentile(response_times_sorted, 0),
            max_response_time_ms=np.percentile(response_times_sorted, 100),
            p50_response_time_ms=np.percentile(response_times_sorted, 50),
            p95_response_time_ms=np.percentile(response_times_sorted, 95),
            p99_response_time_ms=np.percentile(response_times_sorted, 99),
            throughput_req_per_sec=num_requests / test_duration,
            error_rate_pct=(failed / num_requests * 100) if num_requests > 0 else 0,
            test_duration_seconds=test_duration,
            timestamp=datetime.utcnow().isoformat()
        )
        
        self.results.append(result)
        
        logger.info(f"✅ Load test completed: {test_name}")
        logger.info(f"   Success: {successful}/{num_requests}, Error rate: {result.error_rate_pct:.2f}%")
        logger.info(f"   Avg response: {result.avg_response_time_ms:.2f}ms, P95: {result.p95_response_time_ms:.2f}ms")
        
        return result
    
    async def _simulate_request(
        self,
        endpoint: str,
        method: str,
        payload: Dict[str, Any]
    ) -> float:
        """Simulate HTTP request (mock)"""
        # In production, use aiohttp or httpx for real requests
        # For now, simulate with Poisson-distributed latency
        
        base_latency = random.uniform(10, 50)  # 10-50ms base
        
        # Add occasional slow requests (5% chance of 200-500ms)
        if random.random() < 0.05:
            base_latency += random.uniform(200, 500)
        
        # Add occasional errors (2% chance)
        if random.random() < 0.02:
            raise Exception("Simulated request failure")
        
        await asyncio.sleep(base_latency / 1000)
        
        return base_latency
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Get summary of all test results"""
        if not self.results:
            return {"message": "No tests executed"}
        
        return {
            "total_tests": len(self.results),
            "total_requests": sum(r.total_requests for r in self.results),
            "total_successful": sum(r.successful_requests for r in self.results),
            "total_failed": sum(r.failed_requests for r in self.results),
            "overall_error_rate": (
                sum(r.failed_requests for r in self.results) / 
                sum(r.total_requests for r in self.results) * 100
            ),
            "avg_throughput": np.mean([r.throughput_req_per_sec for r in self.results]),
            "results": [self._result_to_dict(r) for r in self.results[-10:]]  # Last 10
        }
    
    @staticmethod
    def _result_to_dict(result: LoadTestResult) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "test_name": result.test_name,
            "endpoint": result.endpoint,
            "total_requests": result.total_requests,
            "successful": result.successful_requests,
            "failed": result.failed_requests,
            "error_rate_pct": round(result.error_rate_pct, 2),
            "avg_response_ms": round(result.avg_response_time_ms, 2),
            "min_response_ms": round(result.min_response_time_ms, 2),
            "max_response_ms": round(result.max_response_time_ms, 2),
            "p50_response_ms": round(result.p50_response_time_ms, 2),
            "p95_response_ms": round(result.p95_response_time_ms, 2),
            "p99_response_ms": round(result.p99_response_time_ms, 2),
            "throughput_req_sec": round(result.throughput_req_per_sec, 2),
            "duration_seconds": round(result.test_duration_seconds, 2)
        }


class StressTestRunner:
    """Identify system breaking points"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.breaking_point = None
    
    async def ramp_up_test(
        self,
        endpoint: str,
        initial_concurrent: int = 10,
        max_concurrent: int = 1000,
        step_size: int = 50,
        requests_per_step: int = 100,
        failure_threshold_pct: float = 10.0
    ) -> Dict[str, Any]:
        """Gradually increase load until failure threshold"""
        
        logger.info(f"🔥 Starting ramp-up stress test on {endpoint}")
        
        results = []
        current_concurrent = initial_concurrent
        
        while current_concurrent <= max_concurrent:
            runner = LoadTestRunner(self.base_url)
            
            result = await runner.run_load_test(
                endpoint=endpoint,
                num_requests=requests_per_step,
                concurrent_requests=current_concurrent,
                test_name=f"Ramp-up: {current_concurrent} concurrent"
            )
            
            results.append(result)
            
            # Check if we've hit failure threshold
            if result.error_rate_pct > failure_threshold_pct:
                self.breaking_point = {
                    "concurrent_requests": current_concurrent,
                    "error_rate": result.error_rate_pct,
                    "throughput": result.throughput_req_per_sec
                }
                logger.warning(f"⚠️ Breaking point reached at {current_concurrent} concurrent requests")
                break
            
            current_concurrent += step_size
        
        return {
            "endpoint": endpoint,
            "breaking_point": self.breaking_point,
            "stages": [self._result_to_dict(r) for r in results],
            "recommendation": self._get_recommendation(results)
        }
    
    @staticmethod
    def _result_to_dict(result: LoadTestResult) -> Dict[str, Any]:
        return {
            "concurrent": result.total_requests // max(1, result.test_duration_seconds),
            "error_rate_pct": round(result.error_rate_pct, 2),
            "throughput": round(result.throughput_req_per_sec, 2),
            "avg_response_ms": round(result.avg_response_time_ms, 2),
            "p95_response_ms": round(result.p95_response_time_ms, 2)
        }
    
    @staticmethod
    def _get_recommendation(results: List[LoadTestResult]) -> str:
        """Generate optimization recommendation"""
        if not results:
            return "No data available"
        
        latest = results[-1]
        
        if latest.error_rate_pct > 10:
            return "URGENT: Implement caching or horizontal scaling"
        elif latest.p95_response_time_ms > 1000:
            return "Add database indexes and query optimization"
        elif latest.throughput_req_per_sec < 100:
            return "Consider vertical scaling or code optimization"
        else:
            return "System performing well, continue monitoring"


class SpikeTestRunner:
    """Test system behavior under sudden load spikes"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def execute_spike_test(
        self,
        endpoint: str,
        baseline_concurrent: int = 10,
        spike_concurrent: int = 500,
        spike_duration_seconds: int = 30,
        pre_spike_time: int = 10,
        post_spike_time: int = 10,
        requests_per_phase: int = 100
    ) -> Dict[str, Any]:
        """Simulate sudden traffic spike"""
        
        logger.info(f"⚡ Starting spike test on {endpoint}")
        
        runner = LoadTestRunner(self.base_url)
        
        # Pre-spike baseline
        pre_result = await runner.run_load_test(
            endpoint=endpoint,
            num_requests=requests_per_phase,
            concurrent_requests=baseline_concurrent,
            test_name="Pre-spike baseline"
        )
        
        # During spike
        spike_result = await runner.run_load_test(
            endpoint=endpoint,
            num_requests=requests_per_phase * 3,
            concurrent_requests=spike_concurrent,
            test_name=f"Spike: {spike_concurrent} concurrent"
        )
        
        # Post-spike recovery
        post_result = await runner.run_load_test(
            endpoint=endpoint,
            num_requests=requests_per_phase,
            concurrent_requests=baseline_concurrent,
            test_name="Post-spike recovery"
        )
        
        # Analyze recovery
        recovery_degradation = (
            (post_result.avg_response_time_ms - pre_result.avg_response_time_ms) /
            pre_result.avg_response_time_ms * 100
        )
        
        return {
            "endpoint": endpoint,
            "pre_spike": self._format_result(pre_result),
            "spike": self._format_result(spike_result),
            "post_spike": self._format_result(post_result),
            "recovery_status": {
                "response_time_degradation_pct": round(recovery_degradation, 2),
                "fully_recovered": recovery_degradation < 5,
                "error_rate_returned_to_normal": abs(post_result.error_rate_pct - pre_result.error_rate_pct) < 2
            },
            "recommendation": "System recovers well" if recovery_degradation < 5 else "Implement spike buffers"
        }
    
    @staticmethod
    def _format_result(result: LoadTestResult) -> Dict[str, Any]:
        return {
            "avg_response_ms": round(result.avg_response_time_ms, 2),
            "error_rate_pct": round(result.error_rate_pct, 2),
            "throughput": round(result.throughput_req_per_sec, 2),
            "p95_response_ms": round(result.p95_response_time_ms, 2)
        }


class LoadTestSuite:
    """Complete load testing suite with multiple test types"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.load_runner = LoadTestRunner(base_url)
        self.stress_runner = StressTestRunner(base_url)
        self.spike_runner = SpikeTestRunner(base_url)
    
    async def run_standard_suite(self) -> Dict[str, Any]:
        """Run standard load test suite on key endpoints"""
        
        endpoints = [
            ("/api/signals/high-performers", "GET"),
            ("/api/external-signals/sources", "GET"),
            ("/api/market/correlations", "GET"),
            ("/api/backtest", "POST"),
            ("/api/monitoring/stats", "GET"),
            ("/api/strategies", "GET"),
            ("/api/portfolio/risk-analysis", "POST"),
        ]
        
        results = []
        
        for endpoint, method in endpoints:
            result = await self.load_runner.run_load_test(
                endpoint=endpoint,
                method=method,
                num_requests=200,
                concurrent_requests=20,
                test_name=f"{method} {endpoint}"
            )
            results.append(result)
            
            # Add delay between tests
            await asyncio.sleep(1)
        
        return {
            "test_suite": "standard",
            "summary": self.load_runner.get_results_summary(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def run_comprehensive_suite(self) -> Dict[str, Any]:
        """Run comprehensive load, stress, and spike tests"""
        
        endpoint = "/api/signals/high-performers"
        
        # Load test
        load_result = await self.load_runner.run_load_test(
            endpoint=endpoint,
            num_requests=500,
            concurrent_requests=50
        )
        
        # Stress test
        stress_result = await self.stress_runner.ramp_up_test(
            endpoint=endpoint,
            initial_concurrent=10,
            max_concurrent=200,
            step_size=20
        )
        
        # Spike test
        spike_result = await self.spike_runner.execute_spike_test(
            endpoint=endpoint,
            baseline_concurrent=20,
            spike_concurrent=300
        )
        
        return {
            "test_suite": "comprehensive",
            "load_test": self.load_runner._result_to_dict(load_result),
            "stress_test": stress_result,
            "spike_test": spike_result,
            "overall_health": self._assess_health(load_result, stress_result, spike_result),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _assess_health(load_result, stress_result, spike_result) -> Dict[str, str]:
        """Assess overall system health"""
        health = {
            "load_handling": "✅ GOOD" if load_result.error_rate_pct < 5 else "⚠️ NEEDS_OPTIMIZATION",
            "stress_tolerance": "✅ GOOD" if stress_result.get("breaking_point") is None else "⚠️ BREAKING_POINT_IDENTIFIED",
            "spike_recovery": "✅ GOOD" if spike_result["recovery_status"]["fully_recovered"] else "⚠️ SLOW_RECOVERY"
        }
        return health
