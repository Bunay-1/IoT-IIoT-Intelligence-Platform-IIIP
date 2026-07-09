import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List

import asyncpg
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Kafka Configuration (assuming similar to KafkaConfig in kafka_ai_integration.py)
KAFKA_BROKER_URL = "localhost:9092"
TOPIC_MACHINE_PERFORMANCE_DATA = (
    "machine_performance_data"  # New topic for raw machine performance data
)
TOPIC_ANALYSED_MACHINE_PERFORMANCE = (
    "analysed_machine_performance"  # Topic for analysed performance data
)


class MachinePerformanceService:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.consumer = None
        self.producer = None
        self.initialize_kafka()

    def initialize_kafka(self):
        while True:
            try:
                self.consumer = KafkaConsumer(
                    TOPIC_MACHINE_PERFORMANCE_DATA,
                    bootstrap_servers=[KAFKA_BROKER_URL],
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    group_id="machine-performance-group",
                )
                self.producer = KafkaProducer(
                    bootstrap_servers=[KAFKA_BROKER_URL],
                    value_serializer=lambda m: json.dumps(m).encode("utf-8"),
                )
                logger.info(
                    "Kafka producer and consumer for MachinePerformanceService initialized."
                )
                break
            except NoBrokersAvailable:
                logger.warning("No Kafka brokers available, retrying in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                logger.error(
                    f"Error initializing Kafka for MachinePerformanceService: {e}"
                )
                time.sleep(5)

    async def _fetch_historical_data(
        self, machine_id: str, days: int = 7
    ) -> List[Dict]:
        """Fetches historical performance data for a given machine from TimescaleDB."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        query = """
            SELECT * FROM machine_data
            WHERE machine_id = $1 AND timestamp BETWEEN $2 AND $3
            ORDER BY timestamp ASC;
        """
        records = await self.db_connection.fetch(
            query, machine_id, start_time, end_time
        )
        return [dict(record) for record in records]

    async def _analyze_performance(
        self, machine_id: str, historical_data: List[Dict]
    ) -> Dict:
        """Performs analysis on historical machine performance data."""
        logger.info(
            f"📊 Analyzing performance for machine {machine_id} with {len(historical_data)} data points."
        )

        if not historical_data:
            return {
                "machine_id": machine_id,
                "timestamp": datetime.now().isoformat(),
                "status": "No historical data available for analysis.",
                "average_vibration": None,
                "max_temperature": None,
                "tool_wear_trend": "N/A",
                "anomalies_detected": False,
                "analysis_summary": "No data to analyze.",
            }

        # Example analysis: calculate average vibration, max temperature, and simple tool wear trend
        total_vibration = 0
        max_temperature = 0
        tool_wear_values = []

        for data_point in historical_data:
            total_vibration += data_point.get("vibration", 0)
            if data_point.get("temperature", 0) > max_temperature:
                max_temperature = data_point.get("temperature", 0)
            tool_wear_values.append(data_point.get("tool_wear", 0))

        average_vibration = (
            total_vibration / len(historical_data) if historical_data else 0
        )

        # Simple trend analysis for tool wear
        tool_wear_trend = "stable"
        if len(tool_wear_values) > 1:
            if tool_wear_values[-1] > tool_wear_values[0]:
                tool_wear_trend = "increasing"
            elif tool_wear_values[-1] < tool_wear_values[0]:
                tool_wear_trend = "decreasing"

        # Dummy anomaly detection (can be replaced with actual ML model)
        anomalies_detected = any(
            dp.get("vibration", 0) > 100 for dp in historical_data
        )  # Example threshold

        analysis_result = {
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat(),
            "status": "Analysis completed successfully.",
            "average_vibration": round(average_vibration, 2),
            "max_temperature": round(max_temperature, 2),
            "tool_wear_trend": tool_wear_trend,
            "anomalies_detected": anomalies_detected,
            "analysis_summary": f"Machine {machine_id} performance analysis: Avg vibration {average_vibration:.2f}, Max temp {max_temperature:.2f}, Tool wear trend: {tool_wear_trend}. Anomalies: {anomalies_detected}.",
        }
        return analysis_result

    async def _publish_analysis_result(self, analysis_result: Dict):
        """Publishes the analysis result to a Kafka topic."""
        try:
            self.producer.send(TOPIC_ANALYSED_MACHINE_PERFORMANCE, analysis_result)
            logger.info(
                f"✅ Published machine performance analysis for {analysis_result['machine_id']} to Kafka."
            )
        except Exception as e:
            logger.error(f"Error publishing analysis result to Kafka: {e}")

    async def process_machine_performance_data(self):
        """Consumes raw machine performance data, analyzes it, and publishes results."""
        logger.info(
            f"Starting MachinePerformanceService to consume from {TOPIC_MACHINE_PERFORMANCE_DATA}..."
        )
        for message in self.consumer:
            raw_data = message.value
            machine_id = raw_data.get("machine_id")

            if not machine_id:
                logger.warning(
                    f"Received data without machine_id, skipping: {raw_data}"
                )
                continue

            logger.info(f"Received raw machine data for machine_id: {machine_id}")

            # Fetch historical data
            historical_data = await self._fetch_historical_data(machine_id)

            # Analyze performance
            analysis_result = await self._analyze_performance(
                machine_id, historical_data
            )

            # Publish analysis result
            await self._publish_analysis_result(analysis_result)

            await asyncio.sleep(0.1)  # Small delay to prevent busy-waiting

    async def start(self):
        """Starts the machine performance service."""
        await self.process_machine_performance_data()


if __name__ == "__main__":

    async def test_run():
        # This is a placeholder for a real DB connection
        class MockDBConnection:
            async def fetch(self, query, *args):
                logger.info(f"MockDB: Executing query: {query} with args: {args}")
                # Return some dummy historical data for testing
                if "machine_data" in query:
                    return [
                        {
                            "machine_id": "CNC-001",
                            "timestamp": datetime.now() - timedelta(hours=i),
                            "vibration": 50 + i,
                            "temperature": 30 + i,
                            "tool_wear": 0.1 + i * 0.01,
                        }
                        for i in range(24)
                    ]
                return []

        mock_db_conn = MockDBConnection()
        service = MachinePerformanceService(mock_db_conn)

        # To test, you would typically send data to TOPIC_MACHINE_PERFORMANCE_DATA
        # For a simple run, we can simulate receiving data
        async def simulate_data_ingestion():
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER_URL],
                value_serializer=lambda m: json.dumps(m).encode("utf-8"),
            )
            for i in range(5):
                data = {
                    "machine_id": "CNC-001",
                    "timestamp": datetime.now().isoformat(),
                    "vibration": 60 + i,
                    "temperature": 35 + i,
                    "tool_wear": 0.5 + i * 0.02,
                }
                producer.send(TOPIC_MACHINE_PERFORMANCE_DATA, data)
                logger.info(f"Simulated sending data: {data}")
                await asyncio.sleep(2)
            producer.close()

        asyncio.create_task(simulate_data_ingestion())
        await service.start()

    asyncio.run(test_run())
