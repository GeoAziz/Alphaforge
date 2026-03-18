"""
Load Testing Suite for AlphaForge Backend
Comprehensive performance and stress testing
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, asdict
import random
import statistics

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
class LoadTestStats:
    """Aggregated load test statistics"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    min_response_time_ms: float
    max_response_time_ms: float
    avg_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    duration_seconds: float
    timestamp: str


class LoadTestScenario:
    """Define a load test scenario"""
    
    def __init__(
        self,
        name: str,
        endpoint: str,
        method: str = "GET",
        concurrent_users: int = 10,
        requests_per_user: int = 100,
        delay_between_requests_ms: int = 100,
        payload: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.endpoint = endpoint
        self.method = method
        self.concurrent_users = concurrent_users
        self.requests_per_user = requests_per_user
        self.delay_between_requests_ms = delay_between_requests_ms
        self.payload = payload or {}


class LoadTestExecutor:
    """Execute load tests against endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[LoadTestResult] = []
        self.scenarios: List[LoadTestScenario] = []
    
    def add_scenario(self, scenario: LoadTestScenario):
        """Add test scenario"""
        self.scenarios.append(scenario)
    
    async def execute_scenario(
        self,
        scenario: LoadTestScenario,
        request_func: Callable
    ) -> LoadTestStats:
        """Execute single scenario"""
        logger.info(f"Starting load test: {scenario.name}")
        logger.info(f"  - Endpoint: {scenario.endpoint}")
        logger.info(f"  - Concurrent Users: {scenario.concurrent_users}")
        logger.info(f"  - Requests per User: {scenario.requests_per_user}")
        
        start_time = time.time()
        scenario_results: List[LoadTestResult] = []
        
        # Create tasks for concurrent users
        tasks = []
        for user_id in range(scenario.concurrent_users):
            task = self._user_session(
                user_id,
                scenario,
                request_func,
                scenario_results
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        # Calculate statistics
        successful = [r for r in scenario_results if r.success]
        response_times = [r.response_time_ms for r in successful]
        
        if response_times:
            response_times_sorted = sorted(response_times)
            p95_idx = int(len(response_times_sorted) * 0.95)
            p99_idx = int(len(response_times_sorted) * 0.99)
            
            stats = LoadTestStats(
                endpoint=scenario.endpoint,
                total_requests=len(scenario_results),
                successful_requests=len(successful),
                failed_requests=len(scenario_results) - len(successful),
                success_rate=len(successful) / len(scenario_results) if scenario_results else 0,
                min_response_time_ms=min(response_times),
                max_response_time_ms=max(response_times),
                avg_response_time_ms=statistics.mean(response_times),
                median_response_time_ms=statistics.median(response_times),
                p95_response_time_ms=response_times_sorted[p95_idx] if p95_idx < len(response_times_sorted) else 0,
                p99_response_time_ms=response_times_sorted[p99_idx] if p99_idx < len(response_times_sorted) else 0,
                requests_per_second=len(scenario_results) / duration if duration > 0 else 0,
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat()
            )
        else:
            stats = LoadTestStats(
                endpoint=scenario.endpoint,
                total_requests=len(scenario_results),
                successful_requests=0,
                failed_requests=len(scenario_results),
                success_rate=0.0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                avg_response_time_ms=0,
                median_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                requests_per_second=0,
                duration_seconds=duration,
                timestamp=datetime.utcnow().isoformat()
            )
        
        self.results.extend(scenario_results)
        logger.info(f"✅ Test completed: {stats.success_rate*100:.1f}% success rate, {stats.requests_per_second:.1f} req/s")
        
        return stats
    
    async def _user_session(
        self,
        user_id: int,
        scenario: LoadTestScenario,
        request_func: Callable,
        results: List[LoadTestResult]
    ):
        """Simulate single user session"""
        for request_num in range(scenario.requests_per_user):
            try:
                start = time.time()
                
                # Mock request execution
                status_code, error = await request_func(
                    scenario.method,
                    scenario.endpoint,
                    scenario.payload
                )
                
                response_time_ms = (time.time() - start) * 1000
                
                result = LoadTestResult(
                    endpoint=scenario.endpoint,
                    method=scenario.method,
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    timestamp=datetime.utcnow().isoformat(),
                    success=200 <= status_code < 300,
                    error=error
                )
                
                results.append(result)
                
                # Delay between requests
                await asyncio.sleep(scenario.delay_between_requests_ms / 1000.0)
                
            except Exception as e:
                logger.error(f"Request error (user {user_id}): {e}")
                results.append(LoadTestResult(
                    endpoint=scenario.endpoint,
                    method=scenario.method,
                    status_code=0,
                    response_time_ms=0,
                    timestamp=datetime.utcnow().isoformat(),
                    success=False,
                    error=str(e)
                ))


class LoadTestReporter:
    """Generate load test reports"""
    
    @staticmethod
    def generate_summary(stats_list: List[LoadTestStats]) -> Dict[str, Any]:
        """Generate overall test summary"""
        if not stats_list:
            return {"status": "No results"}
        
        total_requests = sum(s.total_requests for s in stats_list)
        total_successful = sum(s.successful_requests for s in stats_list)
        total_duration = max(s.duration_seconds for s in stats_list)
        
        return {
            "test_date": datetime.utcnow().isoformat(),
            "total_endpoints_tested": len(stats_list),
            "total_requests": total_requests,
            "total_successful": total_successful,
            "total_failed": total_requests - total_successful,
            "overall_success_rate": total_successful / total_requests if total_requests > 0 else 0,
            "overall_requests_per_second": total_requests / total_duration if total_duration > 0 else 0,
            "total_test_duration": total_duration,
            "slowest_endpoint": max(stats_list, key=lambda s: s.avg_response_time_ms).endpoint if stats_list else None,
            "fastest_endpoint": min(stats_list, key=lambda s: s.avg_response_time_ms).endpoint if stats_list else None,
            "endpoint_results": [asdict(s) for s in stats_list]
        }


class PerformanceBenchmark:
    """Performance benchmark suite for critical endpoints"""
    
    def __init__(self):
        self.benchmarks: Dict[str, Dict[str, float]] = {}
    
    def set_target(self, endpoint: str, metric: str, target_value: float):
        """Set performance target"""
        if endpoint not in self.benchmarks:
            self.benchmarks[endpoint] = {}
        self.benchmarks[endpoint][metric] = target_value
    
    def evaluate(self, stats: LoadTestStats) -> Dict[str, Any]:
        """Evaluate if stats meet benchmarks"""
        if stats.endpoint not in self.benchmarks:
            return {"status": "No benchmark defined"}
        
        targets = self.benchmarks[stats.endpoint]
        passed = True
        results = {}
        
        if "success_rate" in targets:
            benchmark_pass = stats.success_rate >= targets["success_rate"]
            results["success_rate"] = {
                "target": targets["success_rate"],
                "actual": stats.success_rate,
                "passed": benchmark_pass
            }
            passed = passed and benchmark_pass
        
        if "avg_response_time" in targets:
            benchmark_pass = stats.avg_response_time_ms <= targets["avg_response_time"]
            results["avg_response_time_ms"] = {
                "target": targets["avg_response_time"],
                "actual": stats.avg_response_time_ms,
                "passed": benchmark_pass
            }
            passed = passed and benchmark_pass
        
        if "p95_response_time" in targets:
            benchmark_pass = stats.p95_response_time_ms <= targets["p95_response_time"]
            results["p95_response_time_ms"] = {
                "target": targets["p95_response_time"],
                "actual": stats.p95_response_time_ms,
                "passed": benchmark_pass
            }
            passed = passed and benchmark_pass
        
        if "requests_per_second" in targets:
            benchmark_pass = stats.requests_per_second >= targets["requests_per_second"]
            results["requests_per_second"] = {
                "target": targets["requests_per_second"],
                "actual": stats.requests_per_second,
                "passed": benchmark_pass
            }
            passed = passed and benchmark_pass
        
        return {
            "endpoint": stats.endpoint,
            "benchmark_passed": passed,
            "metrics": results
        }


async def mock_request_handler(
    method: str,
    endpoint: str,
    payload: Dict[str, Any]
) -> tuple:
    """Mock HTTP request handler"""
    await asyncio.sleep(random.uniform(0.01, 0.2))  # Simulate network delay
    
    # Randomly succeed 95% of the time
    if random.random() < 0.95:
        return (200, None)
    else:
        return (500, "Internal server error")
