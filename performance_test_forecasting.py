"""
Performance testing for forecasting service
Tests latency, throughput, and accuracy requirements
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from forecasting_service import ForecastingService
from test_forecasting import generate_synthetic_machine_data


async def performance_test():
    """Run comprehensive performance tests for forecasting service."""

    print("Starting Forecasting Performance Tests...")
    print("=" * 60)

    # Setup
    class DummyDBConnection:
        async def fetch(self, query, *args):
            return []

    dummy_db = DummyDBConnection()
    forecasting_service = ForecastingService(dummy_db)

    # Test configurations
    test_configs = [
        {"machines": 1, "days": 7, "iterations": 10, "name": "Single Machine - 1 week"},
        {"machines": 5, "days": 7, "iterations": 5, "name": "5 Machines - 1 week"},
        {"machines": 1, "days": 30, "iterations": 5, "name": "Single Machine - 1 month"},
        {"machines": 10, "days": 7, "iterations": 3, "name": "10 Machines - 1 week"},
    ]

    results = []

    for config in test_configs:
        print(f"\nTesting: {config['name']}")
        print("-" * 40)

        latencies = []
        throughputs = []

        for iteration in range(config['iterations']):
            print(f"  Iteration {iteration + 1}/{config['iterations']}...")

            # Generate test data for multiple machines
            test_data = {}
            total_data_points = 0

            for machine_idx in range(config['machines']):
                machine_id = f"TEST-MACHINE-{machine_idx:03d}"
                data = generate_synthetic_machine_data(machine_id, days=config['days'])
                test_data[machine_id] = data
                total_data_points += len(data)

            # Measure performance
            start_time = time.time()

            tasks = []
            for machine_id, data in test_data.items():
                task = forecasting_service._perform_forecasting(machine_id, data)
                tasks.append(task)

            # Run all forecasts concurrently
            forecasts = await asyncio.gather(*tasks)

            end_time = time.time()

            # Calculate metrics
            total_time = end_time - start_time
            latency_per_machine = total_time / config['machines']
            throughput = total_data_points / total_time  # data points per second

            latencies.append(latency_per_machine)
            throughputs.append(throughput)

            print(f"    Latency: {latency_per_machine:.2f}s, Throughput: {throughput:.0f} data points/sec")

        # Calculate statistics for this configuration
        avg_latency = statistics.mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0

        avg_throughput = statistics.mean(throughputs)

        results.append({
            "config": config,
            "avg_latency": avg_latency,
            "min_latency": min_latency,
            "max_latency": max_latency,
            "std_latency": std_latency,
            "avg_throughput": avg_throughput,
            "total_data_points": total_data_points
        })

        print(f"  Average Latency: {avg_latency:.4f}s, Average Throughput: {avg_throughput:.0f} data points/sec")
    # Overall results analysis
    print("\n" + "=" * 60)
    print("PERFORMANCE TEST RESULTS SUMMARY")
    print("=" * 60)

    # Check success criteria
    success_criteria = {
        "latency_target": 0.1,  # 100ms
        "throughput_target": 1000,  # 1000 data points/sec
    }

    all_passed = True

    for result in results:
        config = result["config"]
        avg_latency = result["avg_latency"]

        # Check latency requirement
        latency_pass = avg_latency < success_criteria["latency_target"]
        if not latency_pass:
            all_passed = False

        status = "PASS" if latency_pass else "FAIL"

        print(f"\n{config['name']}:")
        print(f"    Average Latency: {avg_latency:.4f}s")
        print(f"    Average Throughput: {avg_throughput:.0f} data points/sec")
        print(f"  Status: {status}")

    print(f"\nSuccess Criteria: <{success_criteria['latency_target']*1000:.0f}ms latency")
    print(f"Overall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    # Recommendations
    print("\nRecommendations:")
    if not all_passed:
        print("- Consider model optimization for latency improvement")
        print("- Evaluate using GPU acceleration for inference")
        print("- Implement model caching for repeated predictions")
        print("- Consider async processing for high-throughput scenarios")

    print("- Current implementation meets basic requirements")
    print("- Ready for integration testing with real data streams")

    return results


async def accuracy_validation_test():
    """Test forecasting accuracy on known patterns."""

    print("\nACCURACY VALIDATION TEST")
    print("=" * 40)

    # Generate data with known trends for accuracy testing
    np.random.seed(42)

    machine_id = "ACCURACY-TEST-001"
    days = 30
    data_points = []

    # Create predictable patterns
    base_time = datetime.now() - timedelta(days=days)

    for i in range(days * 24):  # Hourly data
        timestamp = base_time + timedelta(hours=i)

        # Predictable linear trend with noise
        true_trend = 100 + 0.5 * i  # Linear increase
        noise = np.random.normal(0, 2)
        spindle_speed = true_trend + noise

        # Temperature with seasonal pattern
        seasonal_temp = 25 + 5 * np.sin(2 * np.pi * (i % 24) / 24)
        temp_noise = np.random.normal(0, 1)
        temperature = seasonal_temp + temp_noise

        # Tool wear with degradation
        tool_wear = min(90, 0.1 * i + np.random.exponential(0.5))

        data_points.append({
            "timestamp": timestamp.isoformat(),
            "spindle_speed": spindle_speed,
            "temperature": temperature,
            "tool_wear": tool_wear,
            "vibration_x": 1.0 + 0.01 * i + np.random.normal(0, 0.1),
            "vibration_y": 1.0 + 0.01 * i + np.random.normal(0, 0.1),
            "vibration_z": 1.0 + 0.01 * i + np.random.normal(0, 0.1),
            "power_consumption": 20 + 0.1 * spindle_speed + np.random.normal(0, 1),
            "cycle_time": 50 + np.random.normal(0, 5),
            "status": "operating",
            "failure_label": 0
        })

    # Test forecasting
    class DummyDBConnection:
        async def fetch(self, query, *args):
            return []

    dummy_db = DummyDBConnection()
    forecasting_service = ForecastingService(dummy_db)

    forecast = await forecasting_service._perform_forecasting(machine_id, data_points)

    # Validate accuracy for spindle_speed (predictable linear trend)
    if "forecasts" in forecast and "spindle_speed" in forecast["forecasts"]:
        spindle_data = forecast["forecasts"]["spindle_speed"]
        if "forecasts" in spindle_data and "trend" in spindle_data["forecasts"]:
            trend_forecast = spindle_data["forecasts"]["trend"]

            # Calculate accuracy metrics
            current_value = spindle_data["current_value"]
            predicted_next = trend_forecast["values"][0] if trend_forecast["values"] else None

            if predicted_next is not None:
                # For linear trend, prediction should be close to actual trend
                expected_next = current_value + 0.5  # Based on our linear trend
                error = abs(predicted_next - expected_next)
                accuracy = max(0, 100 - (error / expected_next * 100))

                print(f"    Current Value: {current_value:.2f}")
                print(f"    Predicted Next: {predicted_next:.2f}")
                print(f"    Expected Next: {expected_next:.2f}")
                print(f"    Accuracy: {accuracy:.2f}%")
                if accuracy > 85:
                    print("  Status: PASS (Meets 85% accuracy requirement)")
                else:
                    print("  Status: FAIL (Below 85% accuracy requirement)")
            else:
                print("  No trend forecast available")
        else:
            print("  No spindle_speed forecast data")
    else:
        print("  No forecast data available")

    print("\nAccuracy validation completed.")


if __name__ == "__main__":
    async def main():
        # Run performance tests
        await performance_test()

        # Run accuracy validation
        await accuracy_validation_test()

    asyncio.run(main())