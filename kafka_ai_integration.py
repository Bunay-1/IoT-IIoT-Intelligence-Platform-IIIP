"""
Kafka Integration за real-time streaming от 120 CNC машини към AI Pipeline
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List

import asyncpg
import numpy as np
import redis.asyncio as redis
from kafka import KafkaConsumer, KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic

from src.cnc_ai_pipeline import CNCIntelligencePipeline, MachineState, Prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 1. KAFKA CONFIGURATION
# ============================================================================


class KafkaConfig:
    """Kafka configuration"""

    BOOTSTRAP_SERVERS = ["localhost:9092"]

    # Topics
    TOPIC_RAW_DATA = "cnc-raw-data"  # raw data от машините
    TOPIC_FEATURES = "cnc-features"  # extracted features
    TOPIC_PREDICTIONS = "cnc-predictions"  # AI predictions
    TOPIC_ALERTS = "cnc-alerts"  # критични алерти
    TOPIC_OPTIMIZATION = "cnc-optimization"  # optimization suggestions
    TOPIC_PREPROCESSED_DATA = (
        "cnc-preprocessed-data"  # preprocessed data за AI training
    )
    TOPIC_CHATBOT_REQUESTS = "cnc-chatbot-requests"  # chatbot requests
    TOPIC_CHATBOT_RESPONSES = "cnc-chatbot-responses"  # chatbot responses
    TOPIC_FORECASTS = "cnc-forecasts"  # AI forecasts
    TOPIC_MACHINE_PERFORMANCE_DATA = (
        "machine_performance_data"  # New topic for raw machine performance data
    )
    TOPIC_ANALYSED_MACHINE_PERFORMANCE = (
        "analysed_machine_performance"  # Topic for analysed performance data
    )

    # Consumer groups
    GROUP_AI_PROCESSOR = "ai-processor-group"
    GROUP_DASHBOARD = "dashboard-group"
    GROUP_ALERTS = "alerts-group"

    # Performance tuning за 120 машини
    BATCH_SIZE = 16384 * 4  # 64KB batches
    LINGER_MS = 100  # buffer за 100ms
    COMPRESSION_TYPE = "lz4"  # бърза компресия
    MAX_REQUEST_SIZE = 1048576  # 1MB


# ============================================================================
# 2. KAFKA SETUP
# ============================================================================


class KafkaSetup:
    """Setup Kafka topics и partitions"""

    @staticmethod
    def create_topics():
        """Създай всички нужни topics"""
        admin_client = KafkaAdminClient(
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS, client_id="cnc-admin"
        )

        topics = [
            NewTopic(
                name=KafkaConfig.TOPIC_RAW_DATA,
                num_partitions=12,  # 10 partitions за 120 машини (10 per partition)
                replication_factor=2,  # за reliability
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_FEATURES, num_partitions=12, replication_factor=2
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_PREDICTIONS,
                num_partitions=6,
                replication_factor=2,
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_ALERTS,
                num_partitions=3,
                replication_factor=3,  # по-висока reliability за alerts
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_OPTIMIZATION,
                num_partitions=6,
                replication_factor=2,
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_PREPROCESSED_DATA,
                num_partitions=12,
                replication_factor=2,
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_CHATBOT_REQUESTS,
                num_partitions=3,
                replication_factor=2,
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_CHATBOT_RESPONSES,
                num_partitions=3,
                replication_factor=2,
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_FORECASTS, num_partitions=6, replication_factor=2
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_MACHINE_PERFORMANCE_DATA,
                num_partitions=12,
                replication_factor=2,
            ),
            NewTopic(
                name=KafkaConfig.TOPIC_ANALYSED_MACHINE_PERFORMANCE,
                num_partitions=6,
                replication_factor=2,
            ),
        ]

        try:
            admin_client.create_topics(new_topics=topics, validate_only=False)
            logger.info("✅ Kafka topics created successfully")
        except Exception as e:
            logger.warning(f"Topics might already exist: {e}")
        finally:
            admin_client.close()


# ============================================================================
# 3. DATA PRODUCER (Симулира CNC машини)
# ============================================================================


class CNCDataProducer:
    """Симулира данни от CNC машини (в production ще е real data)"""

    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            compression_type=KafkaConfig.COMPRESSION_TYPE,
            batch_size=KafkaConfig.BATCH_SIZE,
            linger_ms=KafkaConfig.LINGER_MS,
            max_request_size=KafkaConfig.MAX_REQUEST_SIZE,
        )

    def send_machine_data(self, machine_id: str, data: Dict):
        """Изпрати данни за машина"""
        message = {
            "machine_id": machine_id,
            "timestamp": datetime.now().isoformat(),
            **data,
        }

        # Partition key = machine_id за ordering
        self.producer.send(
            KafkaConfig.TOPIC_RAW_DATA, value=message, key=machine_id.encode("utf-8")
        )

    def close(self):
        self.producer.flush()
        self.producer.close()


# ============================================================================
# 4. AI PROCESSOR SERVICE (Main Worker)
# ============================================================================


class AIProcessorService:
    """
    Main service който:
    1. Чете от Kafka raw data
    2. Прокарва през AI pipeline
    3. Публикува predictions обратно в Kafka
    4. Cache в Redis за instant access
    """

    def __init__(self, pipeline: "CNCIntelligencePipeline"):
        self.pipeline = pipeline

        # Kafka consumer
        self.consumer = KafkaConsumer(
            KafkaConfig.TOPIC_RAW_DATA,
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            group_id=KafkaConfig.GROUP_AI_PROCESSOR,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
            max_poll_records=500,  # batch processing
            session_timeout_ms=30000,
        )

        # Kafka producers
        self.predictions_producer = KafkaProducer(
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            compression_type=KafkaConfig.COMPRESSION_TYPE,
        )

        self.alerts_producer = KafkaProducer(
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",  # ensure delivery за alerts
        )

        # Redis за caching
        self.redis_client = None

        # Stats
        self.messages_processed = 0
        self.alerts_sent = 0

    async def initialize_redis(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(
            "redis://localhost:6379", encoding="utf-8", decode_responses=True
        )

    async def process_messages(self):
        """Main processing loop"""
        logger.info("🚀 AI Processor started - listening for CNC data...")

        await self.initialize_redis()

        try:
            # Process messages in batches
            while True:
                # Poll messages
                msg_pack = self.consumer.poll(timeout_ms=1000, max_records=100)

                if not msg_pack:
                    await asyncio.sleep(0.1)
                    continue

                # Process batch
                tasks = []
                for topic_partition, messages in msg_pack.items():
                    for message in messages:
                        tasks.append(self._process_single_message(message.value))

                # Process concurrently
                await asyncio.gather(*tasks)

                if self.messages_processed % 100 == 0 and self.messages_processed > 0:
                    logger.info(
                        f"Processed {self.messages_processed} messages. Sent {self.alerts_sent} alerts."
                    )

                # Flush producers to ensure messages are sent
                self.predictions_producer.flush()
                self.alerts_producer.flush()

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.consumer.close()
            self.predictions_producer.close()
            self.alerts_producer.close()
            if self.redis_client:
                await self.redis_client.close()

    async def _process_single_message(self, data: Dict):
        """Process single machine state"""
        try:
            # Parse to MachineState
            state = self._parse_machine_state(data)

            # Run через AI pipeline
            prediction = await self.pipeline.process_machine_state(state)

            # Publish prediction
            await self._publish_prediction(prediction)

            # Cache в Redis за fast access
            await self._cache_prediction(prediction)

            # Check for alerts
            await self._check_and_send_alerts(prediction)

            self.messages_processed += 1

            if self.messages_processed % 100 == 0:
                logger.info(
                    f"📊 Processed {self.messages_processed} messages, "
                    f"sent {self.alerts_sent} alerts"
                )

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _parse_machine_state(self, data: Dict) -> "MachineState":
        """Parse JSON to MachineState object"""
        from src.cnc_ai_pipeline import MachineState

        return MachineState(
            machine_id=data["machine_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            spindle_speed=data["spindle_speed"],
            spindle_load=data["spindle_load"],
            feed_rate=data["feed_rate"],
            temperature=data["temperature"],
            vibration_x=data["vibration_x"],
            vibration_y=data["vibration_y"],
            vibration_z=data["vibration_z"],
            tool_wear=data["tool_wear"],
            power_consumption=data["power_consumption"],
            cycle_time=data["cycle_time"],
            status=data["status"],
        )

    async def _publish_prediction(self, prediction: "Prediction"):
        """Publish prediction to Kafka"""
        message = {
            "machine_id": prediction.machine_id,
            "timestamp": prediction.timestamp.isoformat(),
            "anomaly_score": prediction.anomaly_score,
            "failure_probability": prediction.failure_probability,
            "remaining_useful_life": prediction.remaining_useful_life,
            "optimal_speed": prediction.optimal_speed,
            "optimal_feed": prediction.optimal_feed,
            "recommendations": prediction.recommendations,
            "confidence": prediction.confidence,
        }

        self.predictions_producer.send(
            KafkaConfig.TOPIC_PREDICTIONS,
            value=message,
            key=prediction.machine_id.encode("utf-8"),
        )

    async def _cache_prediction(self, prediction: "Prediction"):
        """Cache prediction в Redis"""
        if not self.redis_client:
            return

        key = f"prediction:{prediction.machine_id}"
        value = {
            "timestamp": prediction.timestamp.isoformat(),
            "anomaly_score": prediction.anomaly_score,
            "failure_probability": prediction.failure_probability,
            "rul": prediction.remaining_useful_life,
            "confidence": prediction.confidence,
        }

        # Cache със TTL 5 минути
        await self.redis_client.setex(key, 300, json.dumps(value))  # 5 minutes

        # Update машина status
        status_key = f"machine:status:{prediction.machine_id}"
        status = (
            "critical"
            if prediction.failure_probability > 0.7
            else "warning"
            if prediction.anomaly_score > 0.75
            else "normal"
        )

        await self.redis_client.setex(status_key, 300, status)

    async def _check_and_send_alerts(self, prediction: "Prediction"):
        """Check и изпрати alerts ако е нужно"""
        alerts = []

        # Critical failure риск
        if prediction.failure_probability > 0.8:
            alerts.append(
                {
                    "severity": "CRITICAL",
                    "type": "FAILURE_RISK",
                    "message": f"Висок риск от повреда на {prediction.machine_id}! "
                    f"Вероятност: {prediction.failure_probability:.1%}, "
                    f"RUL: {prediction.remaining_useful_life:.1f}h",
                }
            )

        # High anomaly
        if prediction.anomaly_score > 0.85:
            alerts.append(
                {
                    "severity": "WARNING",
                    "type": "ANOMALY",
                    "message": f"Аномално поведение на {prediction.machine_id}! "
                    f"Score: {prediction.anomaly_score:.2f}",
                }
            )

        # Low RUL
        if prediction.remaining_useful_life < 24:
            alerts.append(
                {
                    "severity": "WARNING",
                    "type": "MAINTENANCE_DUE",
                    "message": f"Планирай maintenance за {prediction.machine_id} "
                    f"в следващите {prediction.remaining_useful_life:.0f}h",
                }
            )

        # Send alerts
        for alert in alerts:
            alert_message = {
                "machine_id": prediction.machine_id,
                "timestamp": datetime.now().isoformat(),
                **alert,
                "recommendations": prediction.recommendations,
            }

            self.alerts_producer.send(
                KafkaConfig.TOPIC_ALERTS,
                value=alert_message,
                key=prediction.machine_id.encode("utf-8"),
            )

            self.alerts_sent += 1

            logger.warning(f"🚨 ALERT: {alert['message']}")


# ============================================================================
# 5. DATA PREPARATION SERVICE
# ============================================================================


class DataPreparationService:
    """
    Service за събиране и подготовка на данни от Kafka и TimescaleDB
    за AI обучение и прогнозиране.
    """

    def __init__(self, timescaledb_conn):
        self.db = timescaledb_conn
        self.consumer = KafkaConsumer(
            KafkaConfig.TOPIC_RAW_DATA,
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            group_id="data-preparation-group",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
        )
        self.producer = KafkaProducer(
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            compression_type=KafkaConfig.COMPRESSION_TYPE,
        )
        logger.info("✅ DataPreparationService initialized.")

    async def _fetch_historical_data(
        self, machine_id: str, limit: int = 1000
    ) -> List[Dict]:
        """Извлича исторически данни от TimescaleDB за дадена машина."""
        query = """
            SELECT
                timestamp, spindle_speed, spindle_load, feed_rate, temperature,
                vibration_x, vibration_y, vibration_z, tool_wear,
                power_consumption, cycle_time, status
            FROM raw_machine_data  -- Предполагаме, че имаме таблица с raw данни
            WHERE machine_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        # TODO: Трябва да създадем таблица raw_machine_data в TimescaleDB
        # Засега ще използваме predictions, ако няма raw_machine_data
        try:
            results = await self.db.fetch(query, machine_id, limit)
        except Exception as e:
            logger.warning(
                f"Could not fetch historical raw_machine_data: {e}. Falling back to predictions table."
            )
            query = """
                SELECT
                    timestamp, anomaly_score, failure_probability, remaining_useful_life,
                    optimal_speed, optimal_feed, confidence
                FROM predictions
                WHERE machine_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            results = await self.db.fetch(query, machine_id, limit)

        return [dict(row) for row in results]

    async def _preprocess_data(self, data: Dict) -> Dict:
        """
        Извършва почистване на данни и инженеринг на характеристики.
        Това е опростена имплементация, която ще бъде разширена.
        """
        processed_data = data.copy()

        # Пример за почистване: попълване на липсващи стойности (ако има такива)
        for key in ["spindle_speed", "temperature", "tool_wear"]:
            if key in processed_data and processed_data[key] is None:
                processed_data[key] = 0.0  # Пример: попълване с 0

        # Пример за инженеринг на характеристики:
        # Добавяне на час от деня
        if "timestamp" in processed_data:
            ts = datetime.fromisoformat(processed_data["timestamp"])
            processed_data["hour_of_day"] = ts.hour
            processed_data["day_of_week"] = ts.weekday()

        # Нормализация или скалиране може да се добави тук
        # processed_data['normalized_temp'] = processed_data['temperature'] / 10.0

        # Добавяне на placeholder за failure_label
        processed_data["failure_label"] = 0  # По подразбиране няма повреда

        return processed_data

    async def process_data_for_training(self):
        """
        Основен цикъл за събиране и предварителна обработка на данни
        за AI обучение.
        """
        logger.info(
            "🚀 Data Preparation Service started - listening for raw CNC data..."
        )
        try:
            while True:
                msg_pack = self.consumer.poll(timeout_ms=1000, max_records=100)

                if not msg_pack:
                    await asyncio.sleep(0.1)
                    continue

                tasks = []
                for topic_partition, messages in msg_pack.items():
                    for message in messages:
                        tasks.append(self._process_single_raw_message(message.value))

                await asyncio.gather(*tasks)

        except KeyboardInterrupt:
            logger.info("Data Preparation Service shutting down...")
        finally:
            self.consumer.close()
            self.producer.close()

    async def _process_single_raw_message(self, data: Dict):
        """Обработва едно съобщение със сурови данни."""
        machine_id = data.get("machine_id")
        if not machine_id:
            logger.error("Received message without machine_id.")
            return

        logger.info(f"Processing raw data for machine {machine_id} for training.")

        # Извличане на исторически данни
        historical_data = await self._fetch_historical_data(machine_id, limit=50)

        # Комбиниране на текущи и исторически данни (опростено)
        combined_data = {"current_data": data, "historical_data": historical_data}

        # Предварителна обработка
        preprocessed_data = await self._preprocess_data(combined_data["current_data"])

        # Примерна логика за генериране на failure_label
        # В реално приложение, това ще дойде от анотации на данни или по-сложна логика
        if (
            preprocessed_data.get("tool_wear", 0) > 0.8
        ):  # Пример: ако tool_wear е над 80%
            preprocessed_data["failure_label"] = 1
        else:
            preprocessed_data["failure_label"] = 0

        # Публикуване на предварително обработени данни
        self.producer.send(
            KafkaConfig.TOPIC_PREPROCESSED_DATA,
            value=preprocessed_data,
            key=machine_id.encode("utf-8"),
        )
        logger.debug(f"Published preprocessed data for {machine_id}")

    async def _fetch_historical_data(
        self, machine_id: str, limit: int = 50
    ) -> List[Dict]:
        """
        Извлича исторически данни от TimescaleDB за дадена машина.
        """
        query = """
            SELECT
                timestamp, spindle_speed, spindle_load, feed_rate, temperature,
                vibration_x, vibration_y, vibration_z, tool_wear,
                power_consumption, cycle_time, status
            FROM machine_data
            WHERE machine_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        """
        results = await self.db.fetch(query, machine_id, limit)
        return [dict(row) for row in results]

    async def _preprocess_data(self, data: Dict) -> Dict:
        """
        Извършва почистване на данни и инженеринг на характеристики.
        Това е опростена имплементация, която ще бъде разширена.
        """
        processed_data = data.copy()

        # Пример за почистване: попълване на липсващи стойности (ако има такива)
        for key in ["spindle_speed", "temperature", "tool_wear"]:
            if key in processed_data and processed_data[key] is None:
                processed_data[key] = 0.0  # Пример: попълване с 0

        # Пример за инженеринг на характеристики:
        # Добавяне на час от деня
        if "timestamp" in processed_data:
            ts = datetime.fromisoformat(processed_data["timestamp"])
            processed_data["hour_of_day"] = ts.hour
            processed_data["day_of_week"] = ts.weekday()

        # Нормализация или скалиране може да се добави тук
        # processed_data['normalized_temp'] = processed_data['temperature'] / 10.0

        # Добавяне на placeholder за failure_label
        processed_data["failure_label"] = 0  # По подразбиране няма повреда

        return processed_data

    def close(self):
        self.consumer.close()
        self.producer.close()


# ============================================================================
# 6. HISTORICAL ANALYTICS SERVICE
# ============================================================================


class HistoricalAnalyticsService:
    """Service за исторически анализи и reporting"""

    def __init__(self, timescaledb_conn):
        self.db = timescaledb_conn

        # Kafka consumer за persistence
        self.consumer = KafkaConsumer(
            KafkaConfig.TOPIC_PREDICTIONS,
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            group_id="analytics-persistence",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",  # read all history
        )

    async def persist_predictions(self):
        """Save predictions to TimescaleDB"""
        for message in self.consumer:
            data = message.value

            # Insert в TimescaleDB
            query = """
                INSERT INTO predictions
                (machine_id, timestamp, anomaly_score, failure_probability,
                 remaining_useful_life, optimal_speed, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            await self.db.execute(
                query,
                (
                    data["machine_id"],
                    data["timestamp"],
                    data["anomaly_score"],
                    data["failure_probability"],
                    data["remaining_useful_life"],
                    data["optimal_speed"],
                    data["confidence"],
                ),
            )

    async def generate_report(self, machine_id: str, hours: int = 24) -> Dict:
        """Генерирай исторически report"""
        query = """
            SELECT
                time_bucket('1 hour', timestamp) AS hour,
                AVG(anomaly_score) as avg_anomaly,
                MAX(failure_probability) as max_failure_risk,
                MIN(remaining_useful_life) as min_rul,
                AVG(confidence) as avg_confidence
            FROM predictions
            WHERE machine_id = %s
              AND timestamp > NOW() - INTERVAL '%s hours'
            GROUP BY hour
            ORDER BY hour DESC
        """

        results = await self.db.fetch(query, machine_id, hours)

        return {
            "machine_id": machine_id,
            "period_hours": hours,
            "hourly_stats": results,
            "summary": self._calculate_summary(results),
        }

    def _calculate_summary(self, results: List) -> Dict:
        """Calculate summary stats"""
        if not results:
            return {}

        anomaly_scores = [r["avg_anomaly"] for r in results]
        failure_probs = [r["max_failure_risk"] for r in results]

        return {
            "avg_anomaly_score": sum(anomaly_scores) / len(anomaly_scores),
            "max_failure_probability": max(failure_probs),
            "hours_with_high_risk": sum(1 for p in failure_probs if p > 0.7),
            "overall_health": "CRITICAL"
            if max(failure_probs) > 0.8
            else "WARNING"
            if max(failure_probs) > 0.5
            else "GOOD",
        }


# ============================================================================
# 7. MAIN APPLICATION
# ============================================================================


async def main():
    """Main application entry point"""

    # 1. Setup Kafka
    logger.info("Setting up Kafka...")
    KafkaSetup.create_topics()

    # 2. Initialize AI Pipeline
    logger.info("Initializing AI Pipeline...")
    pipeline = CNCIntelligencePipeline()

    # 3. Initialize TimescaleDB
    logger.info("Initializing TimescaleDB connection...")
    db_conn = await asyncpg.connect(
        user="postgres",
        password="cnc_password",
        host="localhost",
        port=5432,
        database="cnc_intelligence",
    )

    # 4. Start Data Preparation Service
    logger.info("Starting Data Preparation Service...")
    data_preparation_service = DataPreparationService(db_conn)
    asyncio.create_task(data_preparation_service.process_data_for_training())

    # 5. Start AI Processor Service
    logger.info("Starting AI Processor Service...")
    processor = AIProcessorService(pipeline)
    asyncio.create_task(processor.process_messages())

    # 6. Start Chatbot Service
    logger.info("Starting Chatbot Service...")
    from src.chatbot_service import ChatbotService

    chatbot_service = ChatbotService()
    asyncio.create_task(chatbot_service.start())

    # 7. Start Forecasting Service
    logger.info("Starting Forecasting Service...")
    from src.forecasting_service import ForecastingService

    forecasting_service = ForecastingService(db_conn)
    asyncio.create_task(forecasting_service.process_data_for_forecasting())

    # 8. Start Machine Performance Service
    logger.info("Starting Machine Performance Service...")
    from src.machine_performance_service import MachinePerformanceService

    machine_performance_service = MachinePerformanceService(db_conn)
    asyncio.create_task(machine_performance_service.start())

    # Keep the main loop running indefinitely
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour, or indefinitely
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    finally:
        await db_conn.close()

    logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    # Run main app
    asyncio.run(main())

    def close(self):
        self.consumer.close()
        self.producer.close()


# ============================================================================
# 6. HISTORICAL ANALYTICS SERVICE
# ============================================================================


class HistoricalAnalyticsService:
    """Service за исторически анализи и reporting"""

    def __init__(self, timescaledb_conn):
        self.db = timescaledb_conn

        # Kafka consumer за persistence
        self.consumer = KafkaConsumer(
            KafkaConfig.TOPIC_PREDICTIONS,
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            group_id="analytics-persistence",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",  # read all history
        )

    async def persist_predictions(self):
        """Save predictions to TimescaleDB"""
        for message in self.consumer:
            data = message.value

            # Insert в TimescaleDB
            query = """
                INSERT INTO predictions
                (machine_id, timestamp, anomaly_score, failure_probability,
                 remaining_useful_life, optimal_speed, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            await self.db.execute(
                query,
                (
                    data["machine_id"],
                    data["timestamp"],
                    data["anomaly_score"],
                    data["failure_probability"],
                    data["remaining_useful_life"],
                    data["optimal_speed"],
                    data["confidence"],
                ),
            )

    async def generate_report(self, machine_id: str, hours: int = 24) -> Dict:
        """Генерирай исторически report"""
        query = """
            SELECT
                time_bucket('1 hour', timestamp) AS hour,
                AVG(anomaly_score) as avg_anomaly,
                MAX(failure_probability) as max_failure_risk,
                MIN(remaining_useful_life) as min_rul,
                AVG(confidence) as avg_confidence
            FROM predictions
            WHERE machine_id = %s
              AND timestamp > NOW() - INTERVAL '%s hours'
            GROUP BY hour
            ORDER BY hour DESC
        """

        results = await self.db.fetch(query, machine_id, hours)

        return {
            "machine_id": machine_id,
            "period_hours": hours,
            "hourly_stats": results,
            "summary": self._calculate_summary(results),
        }

    def _calculate_summary(self, results: List) -> Dict:
        """Calculate summary stats"""
        if not results:
            return {}

        anomaly_scores = [r["avg_anomaly"] for r in results]
        failure_probs = [r["max_failure_risk"] for r in results]

        return {
            "avg_anomaly_score": sum(anomaly_scores) / len(anomaly_scores),
            "max_failure_probability": max(failure_probs),
            "hours_with_high_risk": sum(1 for p in failure_probs if p > 0.7),
            "overall_health": "CRITICAL"
            if max(failure_probs) > 0.8
            else "WARNING"
            if max(failure_probs) > 0.5
            else "GOOD",
        }


# ============================================================================
# 7. MAIN APPLICATION
# ============================================================================


async def main():
    """Main application entry point"""

    # 1. Setup Kafka
    logger.info("Setting up Kafka...")
    KafkaSetup.create_topics()

    # 2. Initialize AI Pipeline
    logger.info("Initializing AI Pipeline...")
    from src.cnc_ai_pipeline import CNCIntelligencePipeline

    pipeline = CNCIntelligencePipeline()

    # 3. Initialize TimescaleDB
    logger.info("Initializing TimescaleDB connection...")
    db_conn = await asyncpg.connect(
        user="postgres",
        password="cnc_password",
        host="localhost",
        port=5432,
        database="cnc_intelligence",
    )

    # 4. Start Data Preparation Service
    logger.info("Starting Data Preparation Service...")
    data_preparation_service = DataPreparationService(db_conn)
    asyncio.create_task(data_preparation_service.process_data_for_training())

    # 5. Start AI Processor Service
    logger.info("Starting AI Processor Service...")
    processor = AIProcessorService(pipeline)
    asyncio.create_task(processor.process_messages())

    # 6. Start Chatbot Service
    logger.info("Starting Chatbot Service...")
    from src.chatbot_service import ChatbotService

    chatbot_service = ChatbotService()
    asyncio.create_task(chatbot_service.start())

    # 7. Start Forecasting Service
    logger.info("Starting Forecasting Service...")
    from src.forecasting_service import ForecastingService

    forecasting_service = ForecastingService(db_conn)
    asyncio.create_task(forecasting_service.process_data_for_forecasting())

    # 8. Start Machine Performance Service
    logger.info("Starting Machine Performance Service...")
    from src.machine_performance_service import MachinePerformanceService

    machine_performance_service = MachinePerformanceService(db_conn)
    asyncio.create_task(machine_performance_service.start())

    # Keep the main loop running indefinitely
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour, or indefinitely
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    finally:
        await db_conn.close()

    logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    # Run main app
    asyncio.run(main())
