"""
Performance Benchmarking for IoT IIoT Platform
Load testing and performance analysis tools
"""

import asyncio
import json
import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import numpy as np

from utils.performance_monitor import performance_monitor
from utils.logging_config import get_logger

logger = get_logger(__name__)


class LoadTestResult:
    """Results from a load test."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = datetime.now()
        self.end_time = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.status_codes: Dict[int, int] = {}
        self.throughput = 0.0
        self.avg_response_time = 0.0
        self.median_response_time = 0.0
        self.p95_response_time = 0.0
        self.p99_response_time = 0.0
        self.min_response_time = 0.0
        self.max_response_time = 0.0
        self.error_rate = 0.0

    def add_result(self, response_time: float, status_code: int, error: Optional[str] = None):
        """Add a single request result."""
        self.total_requests += 1
        self.response_times.append(response_time)

        if status_code >= 200 and status_code < 300:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        if status_code not in self.status_codes:
            self.status_codes[status_code] = 0
        self.status_codes[status_code] += 1

        if error:
            self.errors.append(error)

    def finalize(self):
        """Calculate final statistics."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        if duration > 0:
            self.throughput = self.total_requests / duration

        if self.response_times:
            self.avg_response_time = statistics.mean(self.response_times)
            self.median_response_time = statistics.median(self.response_times)
            self.min_response_time = min(self.response_times)
            self.max_response_time = max(self.response_times)

            # Calculate percentiles
            sorted_times = sorted(self.response_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)

            self.p95_response_time = sorted_times[min(p95_idx, len(sorted_times) - 1)]
            self.p99_response_time = sorted_times[min(p99_idx, len(sorted_times) - 1)]

        self.error_rate = (self.failed_requests / self.total_requests) * 100 if self.total_requests > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "throughput_rps": self.throughput,
            "avg_response_time_ms": self.avg_response_time * 1000,
            "median_response_time_ms": self.median_response_time * 1000,
            "p95_response_time_ms": self.p95_response_time * 1000,
            "p99_response_time_ms": self.p99_response_time * 1000,
            "min_response_time_ms": self.min_response_time * 1000,
            "max_response_time_ms": self.max_response_time * 1000,
            "error_rate_percent": self.error_rate,
            "status_codes": self.status_codes,
            "error_count": len(self.errors),
            "sample_errors": self.errors[:5]  # First 5 errors
        }


class LoadTester:
    """
    Load testing tool for API endpoints.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        """
        Initialize load tester.

        Args:
            base_url: Base URL of the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=1000, limit_per_host=100)  # High concurrency
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict] = None,
        num_requests: int = 100,
        concurrency: int = 10,
        duration_seconds: Optional[int] = None
    ) -> LoadTestResult:
        """
        Run a load test on an endpoint.

        Args:
            endpoint: API endpoint to test
            method: HTTP method
            headers: Request headers
            data: Request data
            json_data: JSON request data
            num_requests: Number of requests to make
            concurrency: Number of concurrent requests
            duration_seconds: Test duration (alternative to num_requests)

        Returns:
            Load test results
        """
        test_name = f"{method} {endpoint}"
        result = LoadTestResult(test_name)

        logger.info(f"Starting load test: {test_name}")
        logger.info(f"Requests: {num_requests}, Concurrency: {concurrency}")

        # Prepare request parameters
        url = f"{self.base_url}{endpoint}"
        request_kwargs = {
            "method": method,
            "headers": headers or {},
            "timeout": self.timeout
        }

        if json_data:
            request_kwargs["json"] = json_data
        elif data:
            request_kwargs["data"] = data

        # Authentication headers (basic example)
        if "Authorization" not in request_kwargs["headers"]:
            # Add default auth if available
            request_kwargs["headers"]["Authorization"] = "Bearer test_token"  # Placeholder

        # Run the test
        semaphore = asyncio.Semaphore(concurrency)

        async def make_request():
            async with semaphore:
                start_time = time.time()
                try:
                    async with self.session.request(url, **request_kwargs) as response:
                        response_time = time.time() - start_time
                        status_code = response.status
                        error = None
                except Exception as e:
                    response_time = time.time() - start_time
                    status_code = 0
                    error = str(e)

                result.add_result(response_time, status_code, error)

        # Create tasks
        if duration_seconds:
            # Duration-based test
            end_time = time.time() + duration_seconds
            tasks = []

            while time.time() < end_time:
                task = asyncio.create_task(make_request())
                tasks.append(task)

                # Limit concurrent tasks
                if len(tasks) >= concurrency * 2:
                    await asyncio.gather(*tasks[:concurrency])
                    tasks = tasks[concurrency:]

            # Wait for remaining tasks
            if tasks:
                await asyncio.gather(*tasks)

        else:
            # Request count-based test
            tasks = [make_request() for _ in range(num_requests)]
            await asyncio.gather(*tasks)

        result.finalize()

        logger.info(f"Load test completed: {result.total_requests} requests, "
                   f"{result.throughput:.2f} RPS, {result.avg_response_time*1000:.2f}ms avg")

        return result


class PerformanceBenchmark:
    """
    Comprehensive performance benchmarking suite.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize performance benchmark.

        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url
        self.load_tester = LoadTester(base_url)
        self.results: List[LoadTestResult] = []

    async def run_full_benchmark(self) -> Dict[str, Any]:
        """
        Run comprehensive performance benchmark.

        Returns:
            Benchmark results
        """
        logger.info("Starting comprehensive performance benchmark")

        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "tests": {}
        }

        async with self.load_tester:
            # Test health endpoint
            result = await self.load_tester.run_load_test(
                "/health",
                num_requests=50,
                concurrency=5
            )
            benchmark_results["tests"]["health_check"] = result.to_dict()
            self.results.append(result)

            # Test API root
            result = await self.load_tester.run_load_test(
                "/",
                num_requests=50,
                concurrency=5
            )
            benchmark_results["tests"]["api_root"] = result.to_dict()
            self.results.append(result)

            # Test authentication (if available)
            try:
                result = await self.load_tester.run_load_test(
                    "/api/v1/auth/login",
                    method="POST",
                    json_data={"username": "test", "password": "test"},
                    num_requests=20,
                    concurrency=2
                )
                benchmark_results["tests"]["auth_login"] = result.to_dict()
                self.results.append(result)
            except Exception as e:
                logger.warning(f"Auth test failed: {e}")

            # Test machine listing
            result = await self.load_tester.run_load_test(
                "/api/machines",
                num_requests=30,
                concurrency=3
            )
            benchmark_results["tests"]["list_machines"] = result.to_dict()
            self.results.append(result)

            # Test analytics overview
            result = await self.load_tester.run_load_test(
                "/api/analytics/overview",
                num_requests=20,
                concurrency=2
            )
            benchmark_results["tests"]["analytics_overview"] = result.to_dict()
            self.results.append(result)

            # Test metrics endpoint
            result = await self.load_tester.run_load_test(
                "/metrics",
                num_requests=100,
                concurrency=10
            )
            benchmark_results["tests"]["prometheus_metrics"] = result.to_dict()
            self.results.append(result)

        # Calculate overall statistics
        benchmark_results["summary"] = self._calculate_summary()

        logger.info("Performance benchmark completed")
        return benchmark_results

    async def run_stress_test(self, endpoint: str, duration_seconds: int = 60, concurrency: int = 50) -> LoadTestResult:
        """
        Run a stress test on a specific endpoint.

        Args:
            endpoint: Endpoint to stress test
            duration_seconds: Test duration
            concurrency: Number of concurrent requests

        Returns:
            Stress test results
        """
        logger.info(f"Starting stress test on {endpoint} for {duration_seconds}s with {concurrency} concurrency")

        async with self.load_tester:
            result = await self.load_tester.run_load_test(
                endpoint,
                duration_seconds=duration_seconds,
                concurrency=concurrency
            )

        self.results.append(result)
        return result

    async def run_scalability_test(self, endpoint: str, max_concurrency: int = 100, step: int = 10) -> Dict[str, Any]:
        """
        Run scalability test with increasing concurrency.

        Args:
            endpoint: Endpoint to test
            max_concurrency: Maximum concurrency level
            step: Concurrency increment

        Returns:
            Scalability test results
        """
        logger.info(f"Starting scalability test on {endpoint}")

        scalability_results = {
            "endpoint": endpoint,
            "concurrency_levels": []
        }

        async with self.load_tester:
            for concurrency in range(step, max_concurrency + 1, step):
                logger.info(f"Testing concurrency level: {concurrency}")

                result = await self.load_tester.run_load_test(
                    endpoint,
                    num_requests=concurrency * 5,  # Scale requests with concurrency
                    concurrency=concurrency
                )

                level_result = {
                    "concurrency": concurrency,
                    "throughput_rps": result.throughput,
                    "avg_response_time_ms": result.avg_response_time * 1000,
                    "error_rate_percent": result.error_rate,
                    "p95_response_time_ms": result.p95_response_time * 1000
                }

                scalability_results["concurrency_levels"].append(level_result)

                # Stop if error rate is too high
                if result.error_rate > 50:
                    logger.warning(f"High error rate at concurrency {concurrency}, stopping test")
                    break

        return scalability_results

    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate overall benchmark summary."""
        if not self.results:
            return {}

        total_requests = sum(r.total_requests for r in self.results)
        total_successful = sum(r.successful_requests for r in self.results)
        total_failed = sum(r.failed_requests for r in self.results)

        all_response_times = []
        for r in self.results:
            all_response_times.extend(r.response_times)

        summary = {
            "total_tests": len(self.results),
            "total_requests": total_requests,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "overall_success_rate": (total_successful / total_requests) * 100 if total_requests > 0 else 0,
            "overall_error_rate": (total_failed / total_requests) * 100 if total_requests > 0 else 0,
        }

        if all_response_times:
            summary.update({
                "avg_response_time_ms": statistics.mean(all_response_times) * 1000,
                "median_response_time_ms": statistics.median(all_response_times) * 1000,
                "p95_response_time_ms": np.percentile(all_response_times, 95) * 1000,
                "p99_response_time_ms": np.percentile(all_response_times, 99) * 1000,
                "min_response_time_ms": min(all_response_times) * 1000,
                "max_response_time_ms": max(all_response_times) * 1000,
            })

        return summary

    def save_results(self, filepath: str):
        """Save benchmark results to file."""
        results_data = {
            "benchmark_summary": self._calculate_summary(),
            "individual_tests": [r.to_dict() for r in self.results]
        }

        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        logger.info(f"Benchmark results saved to {filepath}")


async def run_benchmark(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Run complete performance benchmark.

    Args:
        base_url: API base URL

    Returns:
        Benchmark results
    """
    benchmark = PerformanceBenchmark(base_url)
    results = await benchmark.run_full_benchmark()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"
    benchmark.save_results(filename)

    return results


if __name__ == "__main__":
    # Run benchmark
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    async def main():
        results = await run_benchmark(base_url)
        print(json.dumps(results, indent=2, default=str))

    asyncio.run(main())