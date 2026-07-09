"""
Big Data Processing Pipeline Module

This module implements big data processing pipelines for the IoT IIoT platform,
handling large-scale data ingestion, processing, and analytics using distributed computing.
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union, Callable, Any
from enum import Enum

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DataSource(Enum):
    """Data source types."""
    IOT_SENSORS = "iot_sensors"
    INDUSTRIAL_EQUIPMENT = "industrial_equipment"
    API_ENDPOINTS = "api_endpoints"
    DATABASES = "databases"
    LOG_FILES = "log_files"
    SOCIAL_MEDIA = "social_media"


class ProcessingStage(Enum):
    """Data processing pipeline stages."""
    INGESTION = "ingestion"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    ENRICHMENT = "enrichment"
    AGGREGATION = "aggregation"
    ANALYTICS = "analytics"
    STORAGE = "storage"


class PipelineStatus(Enum):
    """Pipeline execution status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    STOPPED = "stopped"


class BigDataProcessingPipeline:
    """
    Big data processing pipeline for IoT IIoT platform.

    Features:
    - Distributed data ingestion
    - Real-time and batch processing
    - Data quality validation
    - Advanced analytics and ML
    - Scalable storage integration
    - Pipeline monitoring and optimization
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Pipeline definitions
        self.pipelines: Dict[str, Dict] = {}

        # Data sources
        self.data_sources: Dict[str, Dict] = {}

        # Processing stages
        self.processing_stages: Dict[str, List[Dict]] = defaultdict(list)

        # Data buffers and queues
        self.data_queues: Dict[str, asyncio.Queue] = {}
        self.processing_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)

        # Performance monitoring
        self.pipeline_metrics: Dict[str, Dict] = defaultdict(dict)
        self.data_throughput: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # ML models for data processing
        self.ml_models: Dict[str, Any] = {}

        # Distributed processing nodes
        self.processing_nodes: Dict[str, Dict] = {}

        self.logger = get_logger(__name__)
        self.logger.info("Big Data Processing Pipeline initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "max_pipeline_concurrency": 10,
            "batch_size": 1000,
            "processing_timeout": 300,  # 5 minutes
            "data_retention_days": 90,
            "enable_real_time_processing": True,
            "enable_batch_processing": True,
            "compression_enabled": True,
            "parallel_processing": True,
            "max_queue_size": 10000,
            "monitoring_interval": 60,  # seconds
        }

    def create_pipeline(
        self,
        pipeline_name: str,
        stages: List[Dict],
        config: Optional[Dict] = None
    ) -> bool:
        """
        Create a data processing pipeline.

        Args:
            pipeline_name: Unique pipeline name
            stages: List of processing stages
            config: Pipeline configuration

        Returns:
            Creation success
        """
        try:
            pipeline_config = config or {}
            pipeline_config.update({
                "name": pipeline_name,
                "stages": stages,
                "status": PipelineStatus.STOPPED.value,
                "created_at": datetime.now(),
                "last_run": None,
                "run_count": 0,
                "success_rate": 0.0,
                "avg_processing_time": 0.0,
                "data_processed": 0,
                "errors": 0
            })

            self.pipelines[pipeline_name] = pipeline_config

            # Initialize queues for pipeline
            self.data_queues[pipeline_name] = asyncio.Queue(maxsize=self.config["max_queue_size"])

            # Validate pipeline stages
            if not self._validate_pipeline_stages(stages):
                self.logger.error(f"Invalid pipeline stages for {pipeline_name}")
                return False

            self.logger.info(f"Created pipeline: {pipeline_name} with {len(stages)} stages")
            return True

        except Exception as e:
            self.logger.error(f"Pipeline creation failed: {e}")
            return False

    def _validate_pipeline_stages(self, stages: List[Dict]) -> bool:
        """Validate pipeline stages configuration."""
        required_fields = ["stage_type", "name"]

        for stage in stages:
            if not all(field in stage for field in required_fields):
                return False

            # Validate stage type
            try:
                ProcessingStage(stage["stage_type"])
            except ValueError:
                return False

        return True

    def add_data_source(
        self,
        source_name: str,
        source_type: DataSource,
        config: Dict,
        pipelines: List[str]
    ) -> bool:
        """
        Add data source to pipeline.

        Args:
            source_name: Source name
            source_type: Type of data source
            config: Source configuration
            pipelines: List of pipelines to feed

        Returns:
            Addition success
        """
        try:
            source_config = {
                "name": source_name,
                "type": source_type.value,
                "config": config,
                "pipelines": pipelines,
                "status": "active",
                "last_ingestion": None,
                "data_rate": 0.0,  # records per second
                "error_rate": 0.0,
                "created_at": datetime.now()
            }

            self.data_sources[source_name] = source_config

            # Validate pipelines exist
            for pipeline_name in pipelines:
                if pipeline_name not in self.pipelines:
                    self.logger.error(f"Pipeline {pipeline_name} not found for source {source_name}")
                    return False

            self.logger.info(f"Added data source: {source_name} ({source_type.value})")
            return True

        except Exception as e:
            self.logger.error(f"Data source addition failed: {e}")
            return False

    async def start_pipeline(self, pipeline_name: str) -> bool:
        """Start a data processing pipeline."""
        if pipeline_name not in self.pipelines:
            return False

        pipeline = self.pipelines[pipeline_name]

        if pipeline["status"] == PipelineStatus.RUNNING.value:
            return True  # Already running

        try:
            pipeline["status"] = PipelineStatus.RUNNING.value
            pipeline["last_run"] = datetime.now()

            # Start pipeline processing task
            asyncio.create_task(self._run_pipeline(pipeline_name))

            self.logger.info(f"Started pipeline: {pipeline_name}")
            return True

        except Exception as e:
            self.logger.error(f"Pipeline start failed: {e}")
            pipeline["status"] = PipelineStatus.FAILED.value
            return False

    async def stop_pipeline(self, pipeline_name: str) -> bool:
        """Stop a data processing pipeline."""
        if pipeline_name not in self.pipelines:
            return False

        pipeline = self.pipelines[pipeline_name]
        pipeline["status"] = PipelineStatus.STOPPED.value

        self.logger.info(f"Stopped pipeline: {pipeline_name}")
        return True

    async def ingest_data(
        self,
        source_name: str,
        data: Union[Dict, List[Dict], bytes],
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Ingest data from source into pipelines.

        Args:
            source_name: Data source name
            data: Data to ingest
            metadata: Additional metadata

        Returns:
            Ingestion success
        """
        if source_name not in self.data_sources:
            return False

        source_config = self.data_sources[source_name]

        if source_config["status"] != "active":
            return False

        try:
            # Convert data to list of records
            if isinstance(data, dict):
                records = [data]
            elif isinstance(data, list):
                records = data
            else:
                # Assume bytes, try to parse as JSON
                try:
                    parsed = json.loads(data.decode('utf-8'))
                    records = [parsed] if isinstance(parsed, dict) else parsed
                except:
                    self.logger.error(f"Unable to parse data from source {source_name}")
                    return False

            # Add metadata to records
            enriched_records = []
            for record in records:
                enriched_record = {
                    **record,
                    "_metadata": {
                        "source": source_name,
                        "ingested_at": datetime.now().isoformat(),
                        "pipeline_metadata": metadata or {}
                    }
                }
                enriched_records.append(enriched_record)

            # Route to pipelines
            success_count = 0
            for pipeline_name in source_config["pipelines"]:
                if pipeline_name in self.pipelines:
                    # Add to pipeline queue
                    for record in enriched_records:
                        await self.data_queues[pipeline_name].put(record)
                    success_count += 1

            # Update source metrics
            source_config["last_ingestion"] = datetime.now()
            source_config["data_rate"] = len(enriched_records) / max(1, (datetime.now() - source_config["created_at"]).total_seconds())

            self.logger.info(f"Ingested {len(enriched_records)} records from {source_name} to {success_count} pipelines")
            return success_count > 0

        except Exception as e:
            self.logger.error(f"Data ingestion failed for source {source_name}: {e}")
            source_config["error_rate"] += 1
            return False

    async def _run_pipeline(self, pipeline_name: str):
        """Run pipeline processing loop."""
        pipeline = self.pipelines[pipeline_name]
        stages = pipeline["stages"]

        self.logger.info(f"Pipeline {pipeline_name} processing started")

        while pipeline["status"] == PipelineStatus.RUNNING.value:
            try:
                # Get data from queue
                try:
                    data_record = await asyncio.wait_for(
                        self.data_queues[pipeline_name].get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process through stages
                processed_data = data_record
                stage_success = True

                for stage in stages:
                    try:
                        processed_data = await self._execute_stage(stage, processed_data, pipeline_name)
                        if processed_data is None:
                            stage_success = False
                            break
                    except Exception as e:
                        self.logger.error(f"Stage {stage['name']} failed in pipeline {pipeline_name}: {e}")
                        stage_success = False
                        break

                # Update pipeline metrics
                pipeline["run_count"] += 1
                if stage_success:
                    pipeline["data_processed"] += 1
                    success_rate = pipeline["data_processed"] / pipeline["run_count"]
                    pipeline["success_rate"] = success_rate
                else:
                    pipeline["errors"] += 1

                # Record throughput
                self.data_throughput[pipeline_name].append({
                    "timestamp": datetime.now(),
                    "records_processed": 1 if stage_success else 0
                })

            except Exception as e:
                self.logger.error(f"Pipeline {pipeline_name} processing error: {e}")
                pipeline["errors"] += 1

        self.logger.info(f"Pipeline {pipeline_name} processing stopped")

    async def _execute_stage(self, stage: Dict, data: Dict, pipeline_name: str) -> Optional[Dict]:
        """Execute a processing stage."""
        stage_type = ProcessingStage(stage["stage_type"])
        stage_name = stage["name"]

        start_time = time.time()

        try:
            if stage_type == ProcessingStage.INGESTION:
                result = await self._execute_ingestion_stage(stage, data)
            elif stage_type == ProcessingStage.VALIDATION:
                result = await self._execute_validation_stage(stage, data)
            elif stage_type == ProcessingStage.TRANSFORMATION:
                result = await self._execute_transformation_stage(stage, data)
            elif stage_type == ProcessingStage.ENRICHMENT:
                result = await self._execute_enrichment_stage(stage, data)
            elif stage_type == ProcessingStage.AGGREGATION:
                result = await self._execute_aggregation_stage(stage, data)
            elif stage_type == ProcessingStage.ANALYTICS:
                result = await self._execute_analytics_stage(stage, data)
            elif stage_type == ProcessingStage.STORAGE:
                result = await self._execute_storage_stage(stage, data)
            else:
                raise ValueError(f"Unknown stage type: {stage_type}")

            # Record stage performance
            processing_time = time.time() - start_time
            self._record_stage_performance(pipeline_name, stage_name, processing_time)

            return result

        except Exception as e:
            self.logger.error(f"Stage {stage_name} execution failed: {e}")
            raise

    async def _execute_ingestion_stage(self, stage: Dict, data: Dict) -> Dict:
        """Execute data ingestion stage."""
        # Basic ingestion - data is already ingested
        return data

    async def _execute_validation_stage(self, stage: Dict, data: Dict) -> Optional[Dict]:
        """Execute data validation stage."""
        validation_rules = stage.get("config", {}).get("rules", [])

        for rule in validation_rules:
            rule_type = rule.get("type")
            field = rule.get("field")

            if field not in data:
                if rule.get("required", False):
                    return None  # Validation failed
                continue

            value = data[field]

            if rule_type == "type_check":
                expected_type = rule.get("expected_type")
                if not isinstance(value, eval(expected_type)):
                    return None

            elif rule_type == "range_check":
                min_val = rule.get("min")
                max_val = rule.get("max")
                if not (min_val <= value <= max_val):
                    return None

            elif rule_type == "regex_check":
                import re
                pattern = rule.get("pattern")
                if not re.match(pattern, str(value)):
                    return None

        return data

    async def _execute_transformation_stage(self, stage: Dict, data: Dict) -> Dict:
        """Execute data transformation stage."""
        transformations = stage.get("config", {}).get("transformations", [])

        transformed_data = data.copy()

        for transformation in transformations:
            transform_type = transformation.get("type")
            field = transformation.get("field")

            if field not in transformed_data:
                continue

            if transform_type == "normalize":
                # Simple normalization
                value = transformed_data[field]
                if isinstance(value, (int, float)):
                    min_val = transformation.get("min", 0)
                    max_val = transformation.get("max", 100)
                    transformed_data[field] = (value - min_val) / (max_val - min_val)

            elif transform_type == "scale":
                # Feature scaling
                scaler = StandardScaler()
                value = np.array([transformed_data[field]])
                scaled = scaler.fit_transform(value.reshape(-1, 1))
                transformed_data[field] = scaled[0][0]

            elif transform_type == "encode":
                # Simple label encoding
                mapping = transformation.get("mapping", {})
                value = transformed_data[field]
                transformed_data[field] = mapping.get(value, 0)

        return transformed_data

    async def _execute_enrichment_stage(self, stage: Dict, data: Dict) -> Dict:
        """Execute data enrichment stage."""
        enrichments = stage.get("config", {}).get("enrichments", [])

        enriched_data = data.copy()

        for enrichment in enrichments:
            enrichment_type = enrichment.get("type")

            if enrichment_type == "timestamp":
                enriched_data["_processed_at"] = datetime.now().isoformat()

            elif enrichment_type == "geolocation":
                # Add geolocation data based on IP or coordinates
                if "ip_address" in enriched_data:
                    # Mock geolocation lookup
                    enriched_data["_geo"] = {
                        "country": "Unknown",
                        "city": "Unknown",
                        "coordinates": [0.0, 0.0]
                    }

            elif enrichment_type == "device_info":
                # Enrich with device information
                device_id = enriched_data.get("device_id")
                if device_id:
                    enriched_data["_device_info"] = {
                        "type": "sensor",
                        "model": "generic",
                        "firmware_version": "1.0.0"
                    }

        return enriched_data

    async def _execute_aggregation_stage(self, stage: Dict, data: Dict) -> Dict:
        """Execute data aggregation stage."""
        aggregation_config = stage.get("config", {})

        # Simple aggregation - in real implementation would use windowing
        # and distributed aggregation frameworks like Apache Flink

        aggregated_data = data.copy()
        aggregated_data["_aggregated"] = True
        aggregated_data["_aggregation_window"] = aggregation_config.get("window", "1m")

        return aggregated_data

    async def _execute_analytics_stage(self, stage: Dict, data: Dict) -> Dict:
        """Execute analytics stage."""
        analytics_config = stage.get("config", {})

        analytics_data = data.copy()

        # Apply ML analytics
        for analytic in analytics_config.get("analytics", []):
            analytic_type = analytic.get("type")

            if analytic_type == "clustering":
                # K-means clustering
                features = analytic.get("features", [])
                if features and all(f in data for f in features):
                    feature_values = [data[f] for f in features]
                    cluster = await self._apply_clustering(feature_values, analytic)
                    analytics_data["_cluster"] = cluster

            elif analytic_type == "anomaly_detection":
                # Simple anomaly detection
                features = analytic.get("features", [])
                if features:
                    anomaly_score = await self._detect_anomaly(data, features)
                    analytics_data["_anomaly_score"] = anomaly_score

        return analytics_data

    async def _execute_storage_stage(self, stage: Dict, data: Dict) -> Dict:
        """Execute data storage stage."""
        storage_config = stage.get("config", {})

        # In real implementation, would store to various systems:
        # - Data warehouse (Redshift, BigQuery)
        # - Data lake (S3, GCS)
        # - Time-series database (InfluxDB, TimescaleDB)
        # - Search engine (Elasticsearch)

        storage_type = storage_config.get("type", "warehouse")

        # Mock storage operation
        stored_data = {
            **data,
            "_stored_at": datetime.now().isoformat(),
            "_storage_type": storage_type,
            "_storage_location": storage_config.get("location", "default")
        }

        return stored_data

    async def _apply_clustering(self, features: List[float], config: Dict) -> int:
        """Apply clustering algorithm."""
        n_clusters = config.get("n_clusters", 3)

        if f"kmeans_{n_clusters}" not in self.ml_models:
            self.ml_models[f"kmeans_{n_clusters}"] = KMeans(n_clusters=n_clusters, random_state=42)

        model = self.ml_models[f"kmeans_{n_clusters}"]
        cluster = model.fit_predict([features])[0]

        return int(cluster)

    async def _detect_anomaly(self, data: Dict, features: List[str]) -> float:
        """Detect anomalies in data."""
        # Simple statistical anomaly detection
        values = [data[f] for f in features if f in data and isinstance(data[f], (int, float))]

        if len(values) < 2:
            return 0.0

        mean = np.mean(values)
        std = np.std(values)

        # Z-score based anomaly detection
        z_scores = [(v - mean) / std for v in values]
        max_z = max(abs(z) for z in z_scores)

        # Convert to anomaly score (0-1, higher = more anomalous)
        anomaly_score = min(1.0, max_z / 3.0)

        return anomaly_score

    def _record_stage_performance(self, pipeline_name: str, stage_name: str, processing_time: float):
        """Record stage performance metrics."""
        if pipeline_name not in self.pipeline_metrics:
            self.pipeline_metrics[pipeline_name] = {}

        if "stages" not in self.pipeline_metrics[pipeline_name]:
            self.pipeline_metrics[pipeline_name]["stages"] = {}

        stages_metrics = self.pipeline_metrics[pipeline_name]["stages"]

        if stage_name not in stages_metrics:
            stages_metrics[stage_name] = {
                "total_executions": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "max_time": 0.0,
                "min_time": float('inf')
            }

        metrics = stages_metrics[stage_name]
        metrics["total_executions"] += 1
        metrics["total_time"] += processing_time
        metrics["avg_time"] = metrics["total_time"] / metrics["total_executions"]
        metrics["max_time"] = max(metrics["max_time"], processing_time)
        metrics["min_time"] = min(metrics["min_time"], processing_time)

    def get_pipeline_status(self, pipeline_name: str) -> Optional[Dict]:
        """Get pipeline status."""
        return self.pipelines.get(pipeline_name)

    def get_pipeline_metrics(self, pipeline_name: str) -> Optional[Dict]:
        """Get pipeline performance metrics."""
        return self.pipeline_metrics.get(pipeline_name)

    def get_data_sources_status(self) -> Dict[str, Dict]:
        """Get data sources status."""
        return dict(self.data_sources)

    async def optimize_pipeline(self, pipeline_name: str):
        """Optimize pipeline performance."""
        if pipeline_name not in self.pipelines:
            return

        metrics = self.pipeline_metrics.get(pipeline_name, {})
        stages_metrics = metrics.get("stages", {})

        # Identify bottleneck stages
        bottleneck_stages = []
        for stage_name, stage_metrics in stages_metrics.items():
            if stage_metrics["avg_time"] > self.config["processing_timeout"] * 0.5:
                bottleneck_stages.append((stage_name, stage_metrics["avg_time"]))

        if bottleneck_stages:
            bottleneck_stages.sort(key=lambda x: x[1], reverse=True)
            self.logger.info(f"Pipeline {pipeline_name} bottlenecks: {bottleneck_stages[:3]}")

            # In real implementation, would apply optimizations:
            # - Parallel processing for slow stages
            # - Caching for repeated computations
            # - Resource allocation adjustments

    async def continuous_pipeline_monitoring(self):
        """Continuous pipeline monitoring and optimization."""
        while True:
            try:
                # Monitor all active pipelines
                for pipeline_name, pipeline in self.pipelines.items():
                    if pipeline["status"] == PipelineStatus.RUNNING.value:
                        await self.optimize_pipeline(pipeline_name)

                await asyncio.sleep(self.config["monitoring_interval"])

            except Exception as e:
                self.logger.error(f"Pipeline monitoring error: {e}")
                await asyncio.sleep(30)


# Global big data pipeline instance
big_data_pipeline = BigDataProcessingPipeline()


def create_data_pipeline(pipeline_name: str, stages: List[Dict]) -> bool:
    """Create data processing pipeline."""
    return big_data_pipeline.create_pipeline(pipeline_name, stages)


def add_data_source_to_pipeline(
    source_name: str,
    source_type: str,
    config: Dict,
    pipelines: List[str]
) -> bool:
    """Add data source to pipeline."""
    return big_data_pipeline.add_data_source(
        source_name, DataSource(source_type), config, pipelines
    )


async def start_data_pipeline(pipeline_name: str) -> bool:
    """Start data pipeline."""
    return await big_data_pipeline.start_pipeline(pipeline_name)


async def ingest_data_to_pipeline(source_name: str, data: Union[Dict, List[Dict]]) -> bool:
    """Ingest data to pipeline."""
    return await big_data_pipeline.ingest_data(source_name, data)


def get_pipeline_status(pipeline_name: str) -> Optional[Dict]:
    """Get pipeline status."""
    return big_data_pipeline.get_pipeline_status(pipeline_name)


def get_pipeline_metrics(pipeline_name: str) -> Optional[Dict]:
    """Get pipeline metrics."""
    return big_data_pipeline.get_pipeline_metrics(pipeline_name)