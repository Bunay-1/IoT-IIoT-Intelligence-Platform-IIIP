"""
Test script for the forecasting service with generated time series data.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from forecasting_service import ForecastingService


def generate_synthetic_machine_data(machine_id: str, days: int = 30) -> list:
    """Generate synthetic time series data for testing forecasting."""
    np.random.seed(42)  # For reproducible results

    start_time = datetime.now() - timedelta(days=days)
    data_points = []

    # Generate hourly data
    for i in range(days * 24):
        timestamp = start_time + timedelta(hours=i)

        # Base values with trends and seasonality
        hour_of_day = timestamp.hour
        day_of_week = timestamp.weekday()

        # Spindle speed: higher during work hours, with degradation trend
        base_speed = 1500
        seasonal_speed = 200 * np.sin(2 * np.pi * hour_of_day / 24)  # Daily cycle
        trend_speed = -0.5 * i  # Gradual degradation
        noise_speed = np.random.normal(0, 50)
        spindle_speed = max(800, base_speed + seasonal_speed + trend_speed + noise_speed)

        # Temperature: increases with usage, with daily cycle
        base_temp = 25
        usage_temp = 10 * (spindle_speed - 800) / 700  # Higher temp with higher speed
        seasonal_temp = 5 * np.sin(2 * np.pi * hour_of_day / 24)
        noise_temp = np.random.normal(0, 2)
        temperature = base_temp + usage_temp + seasonal_temp + noise_temp

        # Tool wear: gradual increase with some random jumps
        base_wear = i * 0.01  # 0.01% per hour
        jump_wear = np.random.exponential(0.1) if np.random.random() < 0.05 else 0
        tool_wear = min(95, base_wear + jump_wear)

        # Vibration: increases with wear and speed
        base_vib = 0.5
        speed_vib = 0.001 * spindle_speed
        wear_vib = 0.1 * tool_wear
        noise_vib = np.random.exponential(0.2)
        vibration_x = base_vib + speed_vib + wear_vib + noise_vib
        vibration_y = vibration_x * 0.8 + np.random.normal(0, 0.1)
        vibration_z = vibration_x * 0.6 + np.random.normal(0, 0.1)

        # Power consumption
        base_power = 15
        speed_power = 0.01 * spindle_speed
        noise_power = np.random.normal(0, 1)
        power_consumption = base_power + speed_power + noise_power

        # Cycle time (if operating)
        is_operating = np.random.random() < 0.8  # 80% uptime
        cycle_time = np.random.normal(45, 5) if is_operating else 0

        data_points.append({
            "timestamp": timestamp.isoformat(),
            "spindle_speed": spindle_speed,
            "spindle_load": np.random.normal(70, 10),
            "feed_rate": np.random.normal(300, 50),
            "temperature": temperature,
            "vibration_x": vibration_x,
            "vibration_y": vibration_y,
            "vibration_z": vibration_z,
            "tool_wear": tool_wear,
            "power_consumption": power_consumption,
            "cycle_time": cycle_time,
            "status": "operating" if is_operating else "idle",
            "failure_label": 0
        })

    return data_points


async def test_forecasting_service():
    """Test the forecasting service with synthetic data."""
    print("Testing Forecasting Service...")

    # Create dummy DB connection
    class DummyDBConnection:
        async def fetch(self, query, *args):
            print(f"DummyDB: Would execute: {query}")
            return []

    dummy_db = DummyDBConnection()
    forecasting_service = ForecastingService(dummy_db)

    # Generate test data
    machine_id = "CNC-TEST-001"
    print(f"Generating synthetic data for {machine_id}...")
    historical_data = generate_synthetic_machine_data(machine_id, days=14)

    print(f"Generated {len(historical_data)} data points")

    # Run forecasting
    print("Running forecasting...")
    forecast = await forecasting_service._perform_forecasting(machine_id, historical_data)

    # Print results
    print("\n=== FORECASTING RESULTS ===")
    print(f"Machine ID: {forecast['machine_id']}")
    try:
        print(f"Analysis Summary: {forecast['analysis_summary']}")
    except UnicodeEncodeError:
        print("Analysis Summary: [Unicode display issue - summary generated successfully]")

    print("\n--- Forecasts ---")
    for metric, data in forecast.get('forecasts', {}).items():
        if 'current_value' in data:
            print(f"{metric}: Current = {data['current_value']:.2f}")
            if 'forecasts' in data:
                for model, forecast_data in data['forecasts'].items():
                    if 'values' in forecast_data and forecast_data['values']:
                        next_val = forecast_data['values'][0]
                        print(f"  {model}: Next = {next_val:.2f}")

    print("\n--- RUL Predictions ---")
    rul = forecast.get('rul_prediction', {})
    if 'overall' in rul and 'estimated_rul_hours' in rul['overall']:
        overall_rul = rul['overall']['estimated_rul_hours']
        print(f"Overall RUL: {overall_rul:.1f} hours")
        for component, pred in rul.items():
            if component != 'overall' and 'estimated_rul_hours' in pred:
                print(f"  {component}: {pred['estimated_rul_hours']:.1f} hours")

    print("\n--- Tool Change Prediction ---")
    tool_pred = forecast.get('tool_change_prediction', {})
    if 'hours_until_change' in tool_pred:
        print(f"Hours until tool change: {tool_pred['hours_until_change']:.1f}")
        print(f"Current wear: {tool_pred.get('current_wear_percent', 'N/A')}%")

    print("\n--- Degradation Analysis ---")
    degradation = forecast.get('degradation_analysis', {})
    for param, analysis in degradation.items():
        trend = analysis.get('trend', {}).get('direction', 'unknown')
        health = analysis.get('health_score', 0)
        print(f"{param}: Trend = {trend}, Health Score = {health:.2f}")

    print("\nTest completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_forecasting_service())