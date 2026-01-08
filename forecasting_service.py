"""
Advanced Forecasting Service for IoT Predictive Maintenance
Implements time series forecasting, RUL prediction, and degradation modeling
"""

import asyncio
import json
import logging
import warnings
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
import joblib
import numpy as np
import pandas as pd
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

# Try to import statsmodels for ARIMA
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    warnings.warn("statsmodels not available. ARIMA forecasting disabled.")

# Try to import prophet
try:
    from prophet import Prophet

    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False
    warnings.warn("prophet not available. Prophet forecasting disabled.")


# Kafka configuration (local definition to avoid circular imports)
class KafkaConfig:
    BOOTSTRAP_SERVERS = ["localhost:9092"]
    COMPRESSION_TYPE = "gzip"
    TOPIC_PREPROCESSED_DATA = "cnc-preprocessed-data"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForecastingService:
    def __init__(self, timescaledb_conn: asyncpg.Connection):
        self.db = timescaledb_conn
        self.consumer = None
        self.producer = None
        self.initialize_kafka()

    def initialize_kafka(self):
        try:
            self.consumer = KafkaConsumer(
                KafkaConfig.TOPIC_PREPROCESSED_DATA,  # Consume preprocessed data
                bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
                group_id="forecasting-group",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
            )
            self.producer = KafkaProducer(
                bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                compression_type=KafkaConfig.COMPRESSION_TYPE,
            )
            logger.info("✅ Forecasting Kafka producers and consumers initialized.")
        except NoBrokersAvailable:
            logger.error(
                "❌ No Kafka brokers available for ForecastingService. Please ensure Kafka is running."
            )
            exit(1)

    async def _fetch_historical_data_for_forecasting(
        self, machine_id: str, days: int = 30
    ) -> List[Dict]:
        """
        Fetches historical preprocessed data from TimescaleDB for forecasting.
        """
        query = """
            SELECT
                timestamp, spindle_speed, spindle_load, feed_rate, temperature,
                vibration_x, vibration_y, vibration_z, tool_wear,
                power_consumption, cycle_time, status, failure_label
            FROM preprocessed_machine_data  -- Assuming a table for preprocessed data
            WHERE machine_id = $1 AND timestamp >= $2
            ORDER BY timestamp ASC
        """
        # TODO: Ensure 'preprocessed_machine_data' table exists and is populated
        start_date = datetime.now() - timedelta(days=days)
        results = await self.db.fetch(query, machine_id, start_date)
        return [dict(row) for row in results]

    async def _perform_forecasting(
        self, machine_id: str, historical_data: List[Dict]
    ) -> Dict:
        """
        Perform actual forecasting using multiple models and RUL prediction.
        """
        logger.info(
            f"📈 Performing forecasting for machine {machine_id} with {len(historical_data)} data points."
        )

        if not historical_data:
            return self._create_empty_forecast(machine_id)

        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp").sort_index()

        forecasts = {}

        # Time series forecasting for key metrics
        key_metrics = [
            "spindle_speed",
            "temperature",
            "vibration_x",
            "tool_wear",
            "power_consumption",
        ]

        for metric in key_metrics:
            if metric in df.columns:
                try:
                    metric_forecast = await self._forecast_metric(
                        df, metric, machine_id
                    )
                    forecasts[metric] = metric_forecast
                except Exception as e:
                    logger.error(f"Failed to forecast {metric}: {e}")

        # RUL prediction
        rul_prediction = await self._predict_rul(df, machine_id)

        # Equipment degradation analysis
        degradation_analysis = self._analyze_degradation(df)

        # Tool change prediction
        tool_change_prediction = self._predict_tool_change(df)

        forecast = {
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat(),
            "forecasts": forecasts,
            "rul_prediction": rul_prediction,
            "degradation_analysis": degradation_analysis,
            "tool_change_prediction": tool_change_prediction,
            "analysis_summary": self._generate_summary(
                forecasts, rul_prediction, degradation_analysis
            ),
        }
        return forecast

    async def _publish_forecast(self, forecast_data: Dict):
        """
        Publishes the generated forecast to a Kafka topic.
        """
        # TODO: Define a new Kafka topic for forecasts in KafkaConfig
        # For now, we'll use a generic topic or create a new one on the fly if needed
        forecast_topic = "cnc-forecasts"  # New topic for forecasts
        self.producer.send(forecast_topic, value=forecast_data)
        logger.info(f"📊 Published forecast for {forecast_data.get('machine_id')}")

    async def process_data_for_forecasting(self):
        """
        Main loop for the forecasting service, consuming preprocessed data
        and generating forecasts.
        """
        logger.info(
            "🚀 Forecasting Service started - listening for preprocessed data..."
        )
        try:
            while True:
                msg_pack = self.consumer.poll(timeout_ms=1000, max_records=10)

                if not msg_pack:
                    await asyncio.sleep(0.1)
                    continue

                tasks = []
                for topic_partition, messages in msg_pack.items():
                    for message in messages:
                        tasks.append(
                            self._process_single_preprocessed_message(message.value)
                        )

                await asyncio.gather(*tasks)

        except KeyboardInterrupt:
            logger.info("Forecasting Service shutting down...")
        finally:
            if self.consumer:
                self.consumer.close()
            if self.producer:
                self.producer.close()

    async def _process_single_preprocessed_message(self, data: Dict):
        """
        Processes a single preprocessed data message to trigger forecasting.
        """
        machine_id = data.get("machine_id")
        if not machine_id:
            logger.warning(
                "Received preprocessed message without machine_id, skipping."
            )
            return

        # Fetch historical data
        historical_data = await self._fetch_historical_data_for_forecasting(machine_id)

        # Perform forecasting
        forecast = await self._perform_forecasting(machine_id, historical_data)

        # Publish forecast
        await self._publish_forecast(forecast)

    def _create_empty_forecast(self, machine_id: str) -> Dict:
        """Create empty forecast when no data is available."""
        return {
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat(),
            "forecasts": {},
            "rul_prediction": {"error": "No historical data available"},
            "degradation_analysis": {},
            "tool_change_prediction": {"error": "No historical data available"},
            "analysis_summary": "Insufficient data for forecasting",
        }

    async def _forecast_metric(
        self, df: pd.DataFrame, metric: str, machine_id: str
    ) -> Dict:
        """Forecast a specific metric using available models."""
        series = df[metric].dropna()

        if len(series) < 10:
            return {"error": f"Insufficient data for {metric} forecasting"}

        forecasts = {}

        # Prophet forecast
        if HAS_PROPHET:
            try:
                prophet_forecast = self._prophet_forecast(series)
                forecasts["prophet"] = prophet_forecast
            except Exception as e:
                logger.error(f"Prophet forecast failed for {metric}: {e}")

        # ARIMA forecast
        if HAS_STATSMODELS:
            try:
                arima_forecast = self._arima_forecast(series)
                forecasts["arima"] = arima_forecast
            except Exception as e:
                logger.error(f"ARIMA forecast failed for {metric}: {e}")

        # Simple trend-based forecast
        trend_forecast = self._trend_forecast(series)
        forecasts["trend"] = trend_forecast

        return {
            "current_value": float(series.iloc[-1]),
            "forecasts": forecasts,
            "confidence_intervals": self._calculate_confidence_intervals(forecasts),
        }

    def _prophet_forecast(self, series: pd.Series) -> Dict:
        """Perform Prophet forecasting."""
        # Prepare data for Prophet
        prophet_df = pd.DataFrame({"ds": series.index, "y": series.values})

        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=True,
            changepoint_prior_scale=0.05,
        )

        model.fit(prophet_df)

        # Forecast next 24 hours (assuming hourly data)
        future = model.make_future_dataframe(periods=24, freq="H")
        forecast = model.predict(future)

        return {
            "values": forecast.tail(24)["yhat"].tolist(),
            "lower_bound": forecast.tail(24)["yhat_lower"].tolist(),
            "upper_bound": forecast.tail(24)["yhat_upper"].tolist(),
            "timestamps": forecast.tail(24)["ds"]
            .dt.strftime("%Y-%m-%d %H:%M:%S")
            .tolist(),
        }

    def _arima_forecast(self, series: pd.Series) -> Dict:
        """Perform ARIMA forecasting."""
        # Auto-select ARIMA parameters (simplified)
        try:
            model = ARIMA(series, order=(1, 1, 1))
            model_fit = model.fit()

            # Forecast next 24 periods
            forecast = model_fit.forecast(steps=24)

            # Calculate confidence intervals
            pred_ci = model_fit.get_forecast(steps=24).conf_int()

            return {
                "values": forecast.tolist(),
                "lower_bound": pred_ci.iloc[:, 0].tolist(),
                "upper_bound": pred_ci.iloc[:, 1].tolist(),
                "timestamps": [
                    (series.index[-1] + timedelta(hours=i + 1)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    for i in range(24)
                ],
            }
        except Exception as e:
            # Fallback to simple exponential smoothing
            logger.warning(f"ARIMA failed, using simple forecast: {e}")
            return self._simple_forecast(series)

    def _trend_forecast(self, series: pd.Series) -> Dict:
        """Simple trend-based forecasting."""
        # Linear regression on recent data
        recent_data = series.tail(50)  # Last 50 points
        x = np.arange(len(recent_data))
        y = recent_data.values

        # Fit linear trend
        slope, intercept = np.polyfit(x, y, 1)

        # Forecast next 24 periods
        forecast_values = [intercept + slope * (len(x) + i) for i in range(24)]

        # Simple confidence interval based on historical std
        std = np.std(y)
        lower = [v - 1.96 * std for v in forecast_values]
        upper = [v + 1.96 * std for v in forecast_values]

        return {
            "values": forecast_values,
            "lower_bound": lower,
            "upper_bound": upper,
            "timestamps": [
                (series.index[-1] + timedelta(hours=i + 1)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                for i in range(24)
            ],
        }

    def _simple_forecast(self, series: pd.Series) -> Dict:
        """Simple forecast using last value."""
        last_value = series.iloc[-1]
        timestamps = [
            (series.index[-1] + timedelta(hours=i + 1)).strftime("%Y-%m-%d %H:%M:%S")
            for i in range(24)
        ]

        return {
            "values": [last_value] * 24,
            "lower_bound": [last_value * 0.9] * 24,
            "upper_bound": [last_value * 1.1] * 24,
            "timestamps": timestamps,
        }

    async def _predict_rul(self, df: pd.DataFrame, machine_id: str) -> Dict:
        """Predict Remaining Useful Life using degradation modeling."""
        rul_predictions = {}

        # Tool wear-based RUL
        if "tool_wear" in df.columns:
            rul_predictions["tool_wear"] = self._rul_from_wear(df["tool_wear"])

        # Vibration-based RUL
        vibration_cols = [col for col in df.columns if "vibration" in col.lower()]
        if vibration_cols:
            avg_vibration = df[vibration_cols].mean(axis=1)
            rul_predictions["vibration"] = self._rul_from_vibration(avg_vibration)

        # Temperature-based RUL
        if "temperature" in df.columns:
            rul_predictions["temperature"] = self._rul_from_temperature(
                df["temperature"]
            )

        # Overall RUL (weighted average)
        if rul_predictions:
            weights = {"tool_wear": 0.4, "vibration": 0.3, "temperature": 0.3}
            overall_rul = 0
            total_weight = 0

            for component, prediction in rul_predictions.items():
                if "estimated_rul_hours" in prediction:
                    weight = weights.get(component, 0.33)
                    overall_rul += prediction["estimated_rul_hours"] * weight
                    total_weight += weight

            if total_weight > 0:
                overall_rul /= total_weight

            rul_predictions["overall"] = {
                "estimated_rul_hours": overall_rul,
                "confidence": 0.8,
                "based_on": list(rul_predictions.keys()),
            }

        return rul_predictions

    def _rul_from_wear(self, wear_series: pd.Series) -> Dict:
        """Estimate RUL from tool wear data."""
        current_wear = wear_series.iloc[-1]
        wear_rate = wear_series.diff().mean()  # Average wear per time period

        if wear_rate <= 0:
            return {"error": "No degradation detected"}

        max_wear = 100  # Assume 100% is failure threshold
        remaining_wear = max_wear - current_wear

        if remaining_wear <= 0:
            return {"estimated_rul_hours": 0, "immediate_action_required": True}

        # Estimate time periods remaining
        periods_remaining = remaining_wear / abs(wear_rate)

        # Convert to hours (assuming data is hourly)
        rul_hours = periods_remaining

        return {
            "estimated_rul_hours": rul_hours,
            "current_wear_percent": current_wear,
            "wear_rate_per_hour": wear_rate,
            "confidence": 0.85,
        }

    def _rul_from_vibration(self, vibration_series: pd.Series) -> Dict:
        """Estimate RUL from vibration data."""
        current_vibration = vibration_series.iloc[-1]
        vibration_trend = vibration_series.diff().mean()

        # Threshold for concerning vibration levels
        threshold = vibration_series.quantile(0.95)  # 95th percentile as threshold

        if current_vibration < threshold:
            # Estimate when it will reach threshold
            if vibration_trend <= 0:
                return {"estimated_rul_hours": float("inf"), "status": "stable"}

            periods_to_threshold = (threshold - current_vibration) / vibration_trend
            return {
                "estimated_rul_hours": max(0, periods_to_threshold),
                "current_vibration": current_vibration,
                "threshold": threshold,
                "trend": vibration_trend,
                "confidence": 0.75,
            }
        else:
            return {"estimated_rul_hours": 0, "exceeded_threshold": True}

    def _rul_from_temperature(self, temp_series: pd.Series) -> Dict:
        """Estimate RUL from temperature data."""
        current_temp = temp_series.iloc[-1]
        temp_trend = temp_series.diff().mean()

        # Temperature threshold (example: 80°C)
        threshold = 80.0

        if current_temp < threshold:
            if temp_trend <= 0:
                return {"estimated_rul_hours": float("inf"), "status": "cooling"}

            periods_to_threshold = (threshold - current_temp) / temp_trend
            return {
                "estimated_rul_hours": max(0, periods_to_threshold),
                "current_temperature": current_temp,
                "threshold": threshold,
                "trend": temp_trend,
                "confidence": 0.8,
            }
        else:
            return {"estimated_rul_hours": 0, "overheated": True}

    def _analyze_degradation(self, df: pd.DataFrame) -> Dict:
        """Analyze equipment degradation patterns."""
        analysis = {}

        # Trend analysis for key parameters
        key_params = [
            "tool_wear",
            "temperature",
            "vibration_x",
            "vibration_y",
            "vibration_z",
        ]

        for param in key_params:
            if param in df.columns:
                series = df[param].dropna()
                if len(series) > 10:
                    trend = self._calculate_trend(series)
                    analysis[param] = {
                        "trend": trend,
                        "current_value": float(series.iloc[-1]),
                        "change_rate": trend["slope"],
                        "volatility": series.std(),
                        "health_score": self._calculate_health_score(series, trend),
                    }

        return analysis

    def _calculate_trend(self, series: pd.Series) -> Dict:
        """Calculate linear trend for a time series."""
        x = np.arange(len(series))
        y = series.values

        slope, intercept = np.polyfit(x, y, 1)
        r_squared = np.corrcoef(x, y)[0, 1] ** 2

        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "direction": "increasing"
            if slope > 0
            else "decreasing"
            if slope < 0
            else "stable",
        }

    def _calculate_health_score(self, series: pd.Series, trend: Dict) -> float:
        """Calculate a health score based on trend and volatility."""
        # Normalize trend slope (assuming normal ranges)
        # This is a simplified health score calculation
        slope_score = 1.0 - min(1.0, abs(trend["slope"]) / series.std())

        # Volatility score (lower volatility = higher health)
        volatility_score = 1.0 - min(1.0, series.std() / series.mean())

        # Current value score (closer to normal = higher health)
        normal_range = (series.quantile(0.25), series.quantile(0.75))
        current_val = series.iloc[-1]
        if normal_range[0] <= current_val <= normal_range[1]:
            value_score = 1.0
        else:
            distance = min(
                abs(current_val - normal_range[0]), abs(current_val - normal_range[1])
            )
            value_score = max(0.0, 1.0 - distance / (normal_range[1] - normal_range[0]))

        # Weighted average
        health_score = slope_score * 0.4 + volatility_score * 0.3 + value_score * 0.3

        return max(0.0, min(1.0, health_score))

    def _predict_tool_change(self, df: pd.DataFrame) -> Dict:
        """Predict when tool change will be needed."""
        if "tool_wear" not in df.columns:
            return {"error": "No tool wear data available"}

        wear_series = df["tool_wear"].dropna()
        if len(wear_series) < 5:
            return {"error": "Insufficient tool wear data"}

        current_wear = wear_series.iloc[-1]
        wear_rate = wear_series.diff().tail(10).mean()  # Recent wear rate

        if wear_rate <= 0:
            return {"tool_change_needed": False, "reason": "No wear detected"}

        # Assume tool change at 90% wear
        change_threshold = 90.0
        remaining_wear = change_threshold - current_wear

        if remaining_wear <= 0:
            return {
                "tool_change_needed": True,
                "immediate_action_required": True,
                "current_wear_percent": current_wear,
            }

        # Estimate time to change
        periods_to_change = remaining_wear / abs(wear_rate)

        # Convert to datetime (assuming hourly data)
        estimated_change_time = wear_series.index[-1] + timedelta(
            hours=periods_to_change
        )

        return {
            "tool_change_needed": False,
            "estimated_change_time": estimated_change_time.isoformat(),
            "hours_until_change": periods_to_change,
            "current_wear_percent": current_wear,
            "wear_rate_per_hour": wear_rate,
            "confidence": 0.85,
        }

    def _calculate_confidence_intervals(self, forecasts: Dict) -> Dict:
        """Calculate confidence intervals for ensemble forecast."""
        # Simple ensemble method - average available forecasts
        available_forecasts = [
            f for f in forecasts.values() if isinstance(f, dict) and "values" in f
        ]

        if not available_forecasts:
            return {}

        # Average predictions
        num_periods = len(available_forecasts[0]["values"])
        ensemble_values = []
        ensemble_lower = []
        ensemble_upper = []

        for i in range(num_periods):
            values_at_i = [
                f["values"][i] for f in available_forecasts if i < len(f["values"])
            ]
            lowers_at_i = [
                f["lower_bound"][i]
                for f in available_forecasts
                if i < len(f["lower_bound"])
            ]
            uppers_at_i = [
                f["upper_bound"][i]
                for f in available_forecasts
                if i < len(f["upper_bound"])
            ]

            ensemble_values.append(np.mean(values_at_i))
            ensemble_lower.append(np.min(lowers_at_i))  # Conservative lower bound
            ensemble_upper.append(np.max(uppers_at_i))  # Conservative upper bound

        return {
            "ensemble": {
                "values": ensemble_values,
                "lower_bound": ensemble_lower,
                "upper_bound": ensemble_upper,
                "timestamps": available_forecasts[0]["timestamps"][
                    : len(ensemble_values)
                ],
            }
        }

    def _generate_summary(self, forecasts: Dict, rul: Dict, degradation: Dict) -> str:
        """Generate human-readable summary of forecasting results."""
        summary_parts = []

        # Overall health assessment
        if "overall" in rul and "estimated_rul_hours" in rul["overall"]:
            rul_hours = rul["overall"]["estimated_rul_hours"]
            if rul_hours == 0:
                summary_parts.append("⚠️ Critical: Equipment failure imminent")
            elif rul_hours < 24:
                summary_parts.append(
                    f"🚨 Urgent: Equipment failure expected in {rul_hours:.1f} hours"
                )
            elif rul_hours < 168:  # 1 week
                summary_parts.append(
                    f"⚠️ Warning: Equipment failure expected in {rul_hours/24:.1f} days"
                )
            else:
                summary_parts.append("✅ Equipment operating normally")

        # Key parameter alerts
        alerts = []
        for param, data in degradation.items():
            health = data.get("health_score", 1.0)
            trend = data.get("trend", {}).get("direction", "stable")

            if health < 0.5:
                alerts.append(
                    f"{param.replace('_', ' ').title()}: Poor health ({health:.2f})"
                )
            elif trend == "increasing" and param in [
                "temperature",
                "vibration_x",
                "vibration_y",
                "vibration_z",
            ]:
                alerts.append(f"{param.replace('_', ' ').title()}: Trending upward")

        if alerts:
            summary_parts.append("Alerts: " + "; ".join(alerts))

        # Forecast insights
        if forecasts:
            insights = []
            for metric, data in forecasts.items():
                if "forecasts" in data and "trend" in data["forecasts"]:
                    trend_data = data["forecasts"]["trend"]
                    if trend_data["values"]:
                        next_val = trend_data["values"][0]
                        current = data.get("current_value", 0)
                        change = (
                            ((next_val - current) / current * 100)
                            if current != 0
                            else 0
                        )
                        if abs(change) > 5:
                            direction = "increase" if change > 0 else "decrease"
                            insights.append(
                                f"{metric.replace('_', ' ').title()}: {abs(change):.1f}% {direction} expected"
                            )

            if insights:
                summary_parts.append("Forecast: " + "; ".join(insights))

        return (
            " | ".join(summary_parts)
            if summary_parts
            else "Analysis complete - monitoring normal operation"
        )


if __name__ == "__main__":

    async def main():
        # Dummy TimescaleDB connection for standalone testing
        class DummyDBConnection:
            async def fetch(self, query, *args):
                logger.info(f"DummyDB: Executing query: {query} with args {args}")
                return []

        dummy_db_conn = DummyDBConnection()
        forecasting_service = ForecastingService(dummy_db_conn)
        await forecasting_service.process_data_for_forecasting()

    asyncio.run(main())
