"""
Load Testing CLI - Run performance tests against AlphaForge backend
Usage: python run_load_tests.py
"""

import asyncio
import logging
from datetime import datetime

from load_testing_suite import (
    LoadTestScenario,
    LoadTestExecutor,
    LoadTestReporter,
    PerformanceBenchmark,
    mock_request_handler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run comprehensive load tests"""
    
    logger.info("=" * 80)
    logger.info("AlphaForge Backend - Load Testing Suite")
    logger.info(f"Started: {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)
    
    # Initialize executor
    executor = LoadTestExecutor(base_url="http://localhost:8000")
    benchmark = PerformanceBenchmark()
    
    # Define test scenarios
    scenarios = [
        LoadTestScenario(
            name="API: Signal High Performers",
            endpoint="/api/signals/high-performers",
            method="GET",
            concurrent_users=20,
            requests_per_user=50,
            delay_between_requests_ms=50
        ),
        LoadTestScenario(
            name="API: Market Correlations",
            endpoint="/api/market/correlations",
            method="GET",
            concurrent_users=15,
            requests_per_user=40,
            delay_between_requests_ms=100
        ),
        LoadTestScenario(
            name="API: Backtest Single Signal",
            endpoint="/api/backtest",
            method="POST",
            concurrent_users=10,
            requests_per_user=30,
            delay_between_requests_ms=200,
            payload={"signal_ids": ["sig_001"], "asset": "BTC"}
        ),
        LoadTestScenario(
            name="API: Monitoring Stats",
            endpoint="/api/monitoring/stats",
            method="GET",
            concurrent_users=25,
            requests_per_user=100,
            delay_between_requests_ms=20
        ),
        LoadTestScenario(
            name="API: Strategy List",
            endpoint="/api/strategies",
            method="GET",
            concurrent_users=20,
            requests_per_user=60,
            delay_between_requests_ms=50
        ),
        LoadTestScenario(
            name="API: Portfolio Risk Analysis",
            endpoint="/api/portfolio/risk-analysis",
            method="POST",
            concurrent_users=8,
            requests_per_user=20,
            delay_between_requests_ms=300,
            payload={"positions": {"BTC": 50000, "ETH": 30000}}
        ),
    ]
    
    # Set performance benchmarks
    benchmark.set_target("/api/signals/high-performers", "success_rate", 0.95)
    benchmark.set_target("/api/signals/high-performers", "avg_response_time", 200)
    benchmark.set_target("/api/signals/high-performers", "p95_response_time", 500)
    
    benchmark.set_target("/api/market/correlations", "success_rate", 0.90)
    benchmark.set_target("/api/market/correlations", "avg_response_time", 300)
    
    benchmark.set_target("/api/backtest", "success_rate", 0.85)
    benchmark.set_target("/api/backtest", "avg_response_time", 400)
    
    benchmark.set_target("/api/monitoring/stats", "success_rate", 0.98)
    benchmark.set_target("/api/monitoring/stats", "requests_per_second", 100)
    
    # Execute all scenarios
    all_stats = []
    
    for scenario in scenarios:
        logger.info("")
        logger.info(f"Running: {scenario.name}")
        logger.info("-" * 80)
        
        stats = await executor.execute_scenario(scenario, mock_request_handler)
        all_stats.append(stats)
        
        # Evaluate against benchmark
        benchmark_result = benchmark.evaluate(stats)
        
        if benchmark_result.get("benchmark_passed"):
            logger.info(f"✅ Benchmark: PASSED")
        else:
            logger.warning(f"⚠️ Benchmark: FAILED")
            for metric, result in benchmark_result.get("metrics", {}).items():
                if not result.get("passed"):
                    logger.warning(
                        f"   {metric}: {result['actual']:.2f} (target: {result['target']:.2f})"
                    )
    
    # Generate summary report
    logger.info("")
    logger.info("=" * 80)
    logger.info("Load Test Summary Report")
    logger.info("=" * 80)
    
    summary = LoadTestReporter.generate_summary(all_stats)
    
    logger.info(f"Total Endpoints Tested: {summary['total_endpoints_tested']}")
    logger.info(f"Total Requests: {summary['total_requests']:,}")
    logger.info(f"Successful: {summary['total_successful']:,}")
    logger.info(f"Failed: {summary['total_failed']:,}")
    logger.info(f"Success Rate: {summary['overall_success_rate']*100:.2f}%")
    logger.info(f"Overall Throughput: {summary['overall_requests_per_second']:.2f} req/s")
    logger.info(f"Total Test Duration: {summary['total_test_duration']:.2f}s")
    logger.info("")
    logger.info(f"Fastest Endpoint: {summary['fastest_endpoint']}")
    logger.info(f"Slowest Endpoint: {summary['slowest_endpoint']}")
    logger.info("")
    
    # Per-endpoint breakdown
    logger.info("Per-Endpoint Statistics:")
    logger.info("-" * 80)
    
    for endpoint_stats in summary["endpoint_results"]:
        logger.info(f"\n{endpoint_stats['endpoint']}")
        logger.info(f"  Requests: {endpoint_stats['total_requests']} ({endpoint_stats['success_rate']*100:.1f}% success)")
        logger.info(f"  Response Times: min={endpoint_stats['min_response_time_ms']:.1f}ms, " +
                   f"avg={endpoint_stats['avg_response_time_ms']:.1f}ms, " +
                   f"max={endpoint_stats['max_response_time_ms']:.1f}ms")
        logger.info(f"  Percentiles: p95={endpoint_stats['p95_response_time_ms']:.1f}ms, " +
                   f"p99={endpoint_stats['p99_response_time_ms']:.1f}ms")
        logger.info(f"  Throughput: {endpoint_stats['requests_per_second']:.2f} req/s")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"Completed: {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
