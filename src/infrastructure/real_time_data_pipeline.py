"""
Real-Time Data Pipeline for IoT Predictive Maintenance
Integrates OPC UA data streams with preprocessing, feature engineering,
anomaly detection, and real-time inference
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from src.opc_ua_connector import OPCUAConnector
from src.contextual_anomaly_classifier import anomaly_detector
from src.forecasting_service import ForecastingService
from src.kafka_ai_integration import KafkaConfig
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class RealTimeDataPipeline:
    """
    Real-time data pipeline that connects to OPC UA servers,
    processes sensor data, and performs anomaly detection.
    """

    def __init__(self, opcua_config: Dict[str, Any], kafka_config: Optional[Dict] = None):
        """
        Initialize the real-time data pipeline.

        Args:
            opcua_config: OPC UA connection configuration
            kafka_config: Kafka configuration (optional)
        """
        self.opcua_config = opcua_config
        self.kafka_config = kafka_config or KafkaConfig.__dict__

        # Components
        self.opcua_connector = None
        self.kafka_producer = None
        self.forecasting_service = None

        # Data processing
        self.machine_configs = {}
        self.data_buffers = {}  # Buffer recent data for feature engineering
        self.buffer_size = 100

        # Forecasting control
        self.forecasting_interval = 50  # Run forecasting every 50 data points
        self.data_point_counters = {}  # Counter per machine

        # Feature engineering
        self.feature_extractors = {}

        # Monitoring
        self.stats = {
            "messages_processed": 0,
            "anomalies_detected": 0,
            "processing_errors": 0,
            "start_time": None
        }

        logger.info("Real-time data pipeline initialized")

    async def start(self) -> bool:
        """
        Start the real-time data pipeline.

        Returns:
            True if started successfully
        """
        try:
            self.stats["start_time"] = datetime.now()

            # Initialize OPC UA connection
            if not await self._initialize_opcua():
                return False

            # Initialize Kafka producer
            if not await self._initialize_kafka():
                logger.warning("Kafka not available, continuing without publishing")
                self.kafka_producer = None

            # Initialize forecasting service
            if not await self._initialize_forecasting():
                logger.warning("Forecasting service not available")
                self.forecasting_service = None

            # Subscribe to data changes
            await self._subscribe_to_data_changes()

            logger.info("Real-time data pipeline started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start data pipeline: {e}")
            return False

    async def stop(self) -> None:
        """Stop the data pipeline."""
        try:
            if self.opcua_connector:
                await self.opcua_connector.disconnect()

            if self.kafka_producer:
                self.kafka_producer.close()

            logger.info("Real-time data pipeline stopped")

        except Exception as e:
            logger.error(f"Error stopping data pipeline: {e}")

    async def _initialize_opcua(self) -> bool:
        """Initialize OPC UA connection."""
        try:
            self.opcua_connector = OPCUAConnector(
                endpoint=self.opcua_config["endpoint"],
                config=self.opcua_config.get("connection_config")
            )

            connected = await self.opcua_connector.connect()
            if connected:
                logger.info("OPC UA connection established")
                return True
            else:
                logger.error("Failed to connect to OPC UA server")
                return False

        except Exception as e:
            logger.error(f"OPC UA initialization failed: {e}")
            return False

    async def _initialize_kafka(self) -> bool:
        """Initialize Kafka producer."""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.kafka_config.get("BOOTSTRAP_SERVERS", ["localhost:9092"]),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                compression_type=self.kafka_config.get("COMPRESSION_TYPE", "gzip")
            )
            logger.info("Kafka producer initialized")
            return True

        except NoBrokersAvailable:
            logger.warning("Kafka brokers not available")
            return False
        except Exception as e:
            logger.error(f"Kafka initialization failed: {e}")
            return False

    async def _initialize_forecasting(self) -> bool:
        """Initialize forecasting service."""
        try:
            # For now, use a dummy DB connection - in production, pass actual DB
            class DummyDBConnection:
                async def fetch(self, query, *args):
                    logger.debug(f"DummyDB: Executing query: {query}")
                    return []

            dummy_db = DummyDBConnection()
            self.forecasting_service = ForecastingService(dummy_db)
            logger.info("Forecasting service initialized")
            return True

        except Exception as e:
            logger.error(f"Forecasting service initialization failed: {e}")
            return False

    async def _subscribe_to_data_changes(self) -> None:
        """Subscribe to OPC UA data changes."""
        if not self.opcua_connector:
            return

        try:
            # Get variables to monitor from config
            variables_to_monitor = self.opcua_config.get("variables_to_monitor", [])

            if not variables_to_monitor:
                logger.warning("No variables configured for monitoring")
                return

            # Subscribe with custom handler
            success = await self.opcua_connector.subscribe_to_variables(
                variables=variables_to_monitor,
                handler=self._handle_data_change
            )

            if success:
                logger.info(f"Subscribed to {len(variables_to_monitor)} variables")
            else:
                logger.error("Failed to subscribe to variables")

        except Exception as e:
            logger.error(f"Failed to subscribe to data changes: {e}")

    async def _handle_data_change(self, change_data: Dict[str, Any]) -> None:
        """
        Handle OPC UA data change notifications.

        Args:
            change_data: Data change information
        """
        try:
            self.stats["messages_processed"] += 1

            # Extract data
            node_id = change_data["node_id"]
            value = change_data["value"]
            timestamp = datetime.fromtimestamp(change_data["timestamp"])

            # Map node_id to machine and parameter
            machine_id, parameter = self._map_node_to_machine(node_id)

            if not machine_id:
                logger.debug(f"No mapping found for node {node_id}")
                return

            # Create data point
            data_point = {
                "machine_id": machine_id,
                "parameter": parameter,
                "value": value,
                "timestamp": timestamp.isoformat(),
                "node_id": node_id
            }

            # Process data point
            await self._process_data_point(data_point)

        except Exception as e:
            self.stats["processing_errors"] += 1
            logger.error(f"Error handling data change: {e}")

    def _map_node_to_machine(self, node_id: str) -> tuple:
        """
        Map OPC UA node ID to machine and parameter.

        Args:
            node_id: OPC UA node ID

        Returns:
            Tuple of (machine_id, parameter_name)
        """
        # Simple mapping - in production, use configuration
        mappings = self.opcua_config.get("node_mappings", {})

        for machine_id, params in mappings.items():
            for param, nid in params.items():
                if nid == node_id:
                    return machine_id, param

        return None, None

    async def _process_data_point(self, data_point: Dict[str, Any]) -> None:
        """
        Process a single data point through the pipeline.

        Args:
            data_point: Sensor data point
        """
        machine_id = data_point["machine_id"]
        parameter = data_point["parameter"]
        value = data_point["value"]
        timestamp = data_point["timestamp"]

        # Update data buffer
        self._update_data_buffer(machine_id, data_point)

        # Check if we have enough data for processing
        buffer = self.data_buffers.get(machine_id, [])
        if len(buffer) < 10:  # Minimum data points for processing
            return

        try:
            # Preprocess data
            processed_data = self._preprocess_data(buffer)

            # Extract features
            features = self._extract_features(processed_data, machine_id)

            # Perform anomaly detection
            anomaly_result = self._detect_anomalies(features, machine_id)

            # Check if we should run forecasting
            forecasting_result = None
            if self.forecasting_service and self._should_run_forecasting(machine_id):
                try:
                    forecasting_result = await self._run_forecasting(machine_id)
                except Exception as e:
                    logger.error(f"Forecasting failed for {machine_id}: {e}")

            # Prepare result
            result = {
                "machine_id": machine_id,
                "timestamp": timestamp,
                "sensor_data": data_point,
                "processed_data": processed_data,
                "features": features,
                "anomaly_detection": anomaly_result,
                "forecasting": forecasting_result,
                "processing_timestamp": datetime.now().isoformat()
            }

            # Publish result
            await self._publish_result(result)

            # Update stats
            if anomaly_result.get("is_anomaly", False):
                self.stats["anomalies_detected"] += 1

        except Exception as e:
            logger.error(f"Error processing data point: {e}")
            self.stats["processing_errors"] += 1

    def _update_data_buffer(self, machine_id: str, data_point: Dict[str, Any]) -> None:
        """Update the data buffer for a machine."""
        if machine_id not in self.data_buffers:
            self.data_buffers[machine_id] = []

        buffer = self.data_buffers[machine_id]
        buffer.append(data_point)

        # Keep only recent data
        if len(buffer) > self.buffer_size:
            buffer.pop(0)

    def _preprocess_data(self, data_buffer: List[Dict]) -> pd.DataFrame:
        """
        Preprocess raw sensor data.

        Args:
            data_buffer: List of recent data points

        Returns:
            Processed DataFrame
        """
        # Convert to DataFrame
        df = pd.DataFrame(data_buffer)

        # Handle missing values
        df = df.fillna(method='ffill').fillna(method='bfill')

        # Convert timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        # Basic filtering (remove outliers using IQR)
        for col in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df[col] = df[col].clip(lower_bound, upper_bound)

        return df

    def _extract_features(self, data: pd.DataFrame, machine_id: str) -> Dict[str, float]:
        """
        Extract features from preprocessed data.

        Args:
            data: Preprocessed DataFrame
            machine_id: Machine identifier

        Returns:
            Dictionary of features
        """
        features = {}

        # Basic statistical features
        numeric_cols = data.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = data[col]
            features[f"{col}_mean"] = series.mean()
            features[f"{col}_std"] = series.std()
            features[f"{col}_min"] = series.min()
            features[f"{col}_max"] = series.max()
            features[f"{col}_range"] = series.max() - series.min()

            # Trend features
            if len(series) > 1:
                features[f"{col}_trend"] = series.iloc[-1] - series.iloc[0]
                features[f"{col}_slope"] = np.polyfit(range(len(series)), series.values, 1)[0]

        # Rolling statistics
        if len(data) >= 5:
            for col in numeric_cols:
                rolling = data[col].rolling(window=min(5, len(data)))
                features[f"{col}_rolling_mean"] = rolling.mean().iloc[-1]
                features[f"{col}_rolling_std"] = rolling.std().iloc[-1]

        # Domain-specific features (customize based on machine type)
        features.update(self._extract_domain_features(data, machine_id))

        return features

    def _extract_domain_features(self, data: pd.DataFrame, machine_id: str) -> Dict[str, float]:
        """
        Extract domain-specific features based on machine type.

        Args:
            data: Preprocessed data
            machine_id: Machine identifier

        Returns:
            Domain-specific features
        """
        features = {}

        # Example: CNC machine features
        if 'spindle_speed' in data.columns and 'power_consumption' in data.columns:
            # Power efficiency
            speed = data['spindle_speed']
            power = data['power_consumption']
            if speed.mean() > 0:
                features['power_efficiency'] = power.mean() / speed.mean()

        if 'temperature' in data.columns:
            # Temperature stability
            temp = data['temperature']
            features['temp_stability'] = 1 / (1 + temp.std())

        if 'vibration_x' in data.columns and 'vibration_y' in data.columns and 'vibration_z' in data.columns:
            # Overall vibration
            vib_x = data['vibration_x']
            vib_y = data['vibration_y']
            vib_z = data['vibration_z']
            features['overall_vibration'] = np.sqrt(vib_x**2 + vib_y**2 + vib_z**2).mean()

        return features

    def _detect_anomalies(self, features: Dict[str, float], machine_id: str) -> Dict[str, Any]:
        """
        Perform anomaly detection on extracted features.

        Args:
            features: Extracted features
            machine_id: Machine identifier

        Returns:
            Anomaly detection results
        """
        try:
            # Convert to DataFrame for anomaly detector
            feature_df = pd.DataFrame([features])

            # Score anomalies
            scores = anomaly_detector.score_anomalies(feature_df)

            # Extract results
            ensemble_scores = scores["scores"].get("ensemble", {})
            anomaly_scores = {alg: scores["scores"][alg]["anomaly_scores"][0]
                            for alg in scores["scores"]}
            predictions = {alg: scores["scores"][alg]["predictions"][0]
                          for alg in scores["scores"]}

            is_anomaly = bool(ensemble_scores.get("predictions", [0])[0])

            return {
                "is_anomaly": is_anomaly,
                "anomaly_scores": anomaly_scores,
                "predictions": predictions,
                "confidence": 1.0 - ensemble_scores.get("anomaly_scores", [0.5])[0],
                "algorithms_used": list(scores["scores"].keys())
            }

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {
                "error": str(e),
                "is_anomaly": False,
                "anomaly_scores": {},
                "predictions": {},
                "confidence": 0.0
            }

    async def _publish_result(self, result: Dict[str, Any]) -> None:
        """
        Publish processing results to Kafka and other sinks.

        Args:
            result: Processing result
        """
        try:
            if self.kafka_producer:
                # Publish to Kafka
                topic = "cnc-anomaly-results"  # Configure topic
                self.kafka_producer.send(topic, value=result)
                logger.debug(f"Published result for {result['machine_id']}")

            # Could also store in database, send alerts, etc.

        except Exception as e:
            logger.error(f"Failed to publish result: {e}")

    def _should_run_forecasting(self, machine_id: str) -> bool:
        """Check if forecasting should be run for this machine."""
        if machine_id not in self.data_point_counters:
            self.data_point_counters[machine_id] = 0

        self.data_point_counters[machine_id] += 1
        return self.data_point_counters[machine_id] % self.forecasting_interval == 0

    async def _run_forecasting(self, machine_id: str) -> Dict[str, Any]:
        """Run forecasting for a machine."""
        try:
            # Get historical data from buffer (convert to expected format)
            buffer = self.data_buffers.get(machine_id, [])
            if len(buffer) < 10:
                return {"error": "Insufficient data for forecasting"}

            # Convert buffer to historical data format
            historical_data = []
            for data_point in buffer[-100:]:  # Use last 100 points
                historical_data.append({
                    "timestamp": data_point["timestamp"],
                    "spindle_speed": data_point.get("value") if data_point.get("parameter") == "spindle_speed" else None,
                    "spindle_load": data_point.get("value") if data_point.get("parameter") == "spindle_load" else None,
                    "feed_rate": data_point.get("value") if data_point.get("parameter") == "feed_rate" else None,
                    "temperature": data_point.get("value") if data_point.get("parameter") == "temperature" else None,
                    "vibration_x": data_point.get("value") if data_point.get("parameter") == "vibration_x" else None,
                    "vibration_y": data_point.get("value") if data_point.get("parameter") == "vibration_y" else None,
                    "vibration_z": data_point.get("value") if data_point.get("parameter") == "vibration_z" else None,
                    "tool_wear": data_point.get("value") if data_point.get("parameter") == "tool_wear" else None,
                    "power_consumption": data_point.get("value") if data_point.get("parameter") == "power_consumption" else None,
                    "cycle_time": data_point.get("value") if data_point.get("parameter") == "cycle_time" else None,
                    "status": data_point.get("value") if data_point.get("parameter") == "status" else None,
                    "failure_label": 0  # Placeholder
                })

            # Run forecasting
            forecast = await self.forecasting_service._perform_forecasting(machine_id, historical_data)

            logger.info(f"Forecasting completed for {machine_id}")
            return forecast

        except Exception as e:
            logger.error(f"Forecasting failed for {machine_id}: {e}")
            return {"error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            **self.stats,
            "uptime_seconds": uptime,
            "active_machines": len(self.data_buffers),
            "opcua_connected": self.opcua_connector.connected if self.opcua_connector else False,
            "kafka_connected": self.kafka_producer is not None
        }

    async def add_machine_config(self, machine_id: str, config: Dict[str, Any]) -> None:
        """
        Add configuration for a machine.

        Args:
            machine_id: Machine identifier
            config: Machine configuration
        """
        self.machine_configs[machine_id] = config
        logger.info(f"Added configuration for machine {machine_id}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


# Global pipeline instance
data_pipeline = None


async def get_data_pipeline(opcua_config: Dict[str, Any]) -> RealTimeDataPipeline:
    """Get or create global data pipeline instance."""
    global data_pipeline
    if data_pipeline is None:
        data_pipeline = RealTimeDataPipeline(opcua_config)
        await data_pipeline.start()
    return data_pipeline