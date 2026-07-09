"""
Data Lake Management Module

This module implements data lake management for the IoT IIoT platform,
providing scalable storage, data organization, metadata management, and data governance.
"""

import asyncio
import hashlib
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class DataFormat(Enum):
    """Supported data formats."""
    JSON = "json"
    PARQUET = "parquet"
    CSV = "csv"
    AVRO = "avro"
    ORC = "orc"
    DELTA = "delta"


class StorageTier(Enum):
    """Data storage tiers."""
    HOT = "hot"       # Frequently accessed data
    WARM = "warm"     # Occasionally accessed data
    COLD = "cold"     # Rarely accessed data
    ARCHIVE = "archive"  # Long-term archival


class DataClassification(Enum):
    """Data classification levels."""
    RAW = "raw"
    PROCESSED = "processed"
    ENRICHED = "enriched"
    AGGREGATED = "aggregated"
    ANALYTICS = "analytics"


class DataLakeManagement:
    """
    Data lake management system.

    Features:
    - Hierarchical data organization
    - Metadata management
    - Data lifecycle management
    - Storage tiering
    - Data quality monitoring
    - Access control and governance
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Data lake structure
        self.data_lake_root: Path = Path(self.config["data_lake_root"])
        self.data_lake_root.mkdir(parents=True, exist_ok=True)

        # Metadata store
        self.metadata_store: Dict[str, Dict] = {}

        # Data partitions
        self.partitions: Dict[str, Dict] = {}

        # Storage policies
        self.storage_policies: Dict[str, Dict] = {}

        # Data quality rules
        self.quality_rules: Dict[str, List[Dict]] = defaultdict(list)

        # Access control
        self.access_policies: Dict[str, Dict] = {}

        # Data lifecycle management
        self.lifecycle_policies: Dict[str, Dict] = {}

        # Performance monitoring
        self.performance_metrics: Dict[str, Dict] = defaultdict(dict)

        self.logger = get_logger(__name__)
        self.logger.info("Data Lake Management initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "data_lake_root": "./data_lake",
            "max_file_size_gb": 1.0,
            "partition_strategy": "date_based",
            "compression_enabled": True,
            "default_format": DataFormat.PARQUET.value,
            "retention_days": 365,
            "enable_versioning": True,
            "max_versions": 10,
            "quality_check_enabled": True,
            "access_audit_enabled": True,
        }

    def create_data_zone(
        self,
        zone_name: str,
        zone_type: str,
        config: Optional[Dict] = None
    ) -> bool:
        """
        Create a data zone in the lake.

        Args:
            zone_name: Zone name (e.g., 'raw', 'processed', 'analytics')
            zone_type: Type of data zone
            config: Zone configuration

        Returns:
            Creation success
        """
        try:
            zone_path = self.data_lake_root / zone_name
            zone_path.mkdir(parents=True, exist_ok=True)

            zone_config = config or {}
            zone_config.update({
                "name": zone_name,
                "type": zone_type,
                "path": str(zone_path),
                "created_at": datetime.now(),
                "total_size": 0,
                "file_count": 0,
                "last_modified": None,
                "partitions": []
            })

            self.metadata_store[f"zone_{zone_name}"] = zone_config

            # Create subdirectories based on zone type
            if zone_type == "raw":
                (zone_path / "ingested").mkdir(exist_ok=True)
                (zone_path / "validated").mkdir(exist_ok=True)
            elif zone_type == "processed":
                (zone_path / "transformed").mkdir(exist_ok=True)
                (zone_path / "enriched").mkdir(exist_ok=True)
            elif zone_type == "analytics":
                (zone_path / "aggregated").mkdir(exist_ok=True)
                (zone_path / "reports").mkdir(exist_ok=True)

            self.logger.info(f"Created data zone: {zone_name} ({zone_type})")
            return True

        except Exception as e:
            self.logger.error(f"Data zone creation failed: {e}")
            return False

    def create_partition(
        self,
        zone_name: str,
        partition_key: str,
        partition_config: Optional[Dict] = None
    ) -> bool:
        """
        Create data partition.

        Args:
            zone_name: Zone name
            partition_key: Partition identifier
            partition_config: Partition configuration

        Returns:
            Creation success
        """
        try:
            zone_key = f"zone_{zone_name}"
            if zone_key not in self.metadata_store:
                self.logger.error(f"Zone {zone_name} not found")
                return False

            zone_info = self.metadata_store[zone_key]
            zone_path = Path(zone_info["path"])

            # Create partition path
            partition_path = zone_path / partition_key
            partition_path.mkdir(parents=True, exist_ok=True)

            partition = partition_config or {}
            partition.update({
                "zone": zone_name,
                "key": partition_key,
                "path": str(partition_path),
                "created_at": datetime.now(),
                "file_count": 0,
                "total_size": 0,
                "last_modified": None,
                "data_format": self.config["default_format"],
                "storage_tier": StorageTier.HOT.value
            })

            partition_id = f"partition_{zone_name}_{partition_key}"
            self.partitions[partition_id] = partition

            # Add to zone
            zone_info["partitions"].append(partition_id)

            self.logger.info(f"Created partition: {partition_key} in zone {zone_name}")
            return True

        except Exception as e:
            self.logger.error(f"Partition creation failed: {e}")
            return False

    async def store_data(
        self,
        zone_name: str,
        partition_key: str,
        data: Union[Dict, List[Dict], bytes],
        metadata: Optional[Dict] = None,
        data_format: Optional[DataFormat] = None
    ) -> Optional[str]:
        """
        Store data in the lake.

        Args:
            zone_name: Target zone
            partition_key: Target partition
            data: Data to store
            metadata: Data metadata
            data_format: Data format

        Returns:
            Data object ID
        """
        try:
            partition_id = f"partition_{zone_name}_{partition_key}"
            if partition_id not in self.partitions:
                # Create partition if it doesn't exist
                if not self.create_partition(zone_name, partition_key):
                    return None

            partition = self.partitions[partition_id]
            partition_path = Path(partition["path"])

            # Generate data object ID
            data_id = f"data_{int(datetime.now().timestamp() * 1000000)}"
            format_ext = data_format.value if data_format else partition["data_format"]

            # Create filename
            filename = f"{data_id}.{format_ext}"
            if self.config["compression_enabled"]:
                filename += ".gz"

            file_path = partition_path / filename

            # Serialize data
            if isinstance(data, (dict, list)):
                serialized_data = json.dumps(data, indent=2).encode('utf-8')
            elif isinstance(data, bytes):
                serialized_data = data
            else:
                serialized_data = str(data).encode('utf-8')

            # Compress if enabled
            if self.config["compression_enabled"]:
                import gzip
                serialized_data = gzip.compress(serialized_data)

            # Write to file
            async with asyncio.get_event_loop().run_in_executor(None, self._write_file, file_path, serialized_data):
                pass

            # Update metadata
            data_metadata = {
                "id": data_id,
                "zone": zone_name,
                "partition": partition_key,
                "path": str(file_path),
                "format": format_ext,
                "compressed": self.config["compression_enabled"],
                "size_bytes": len(serialized_data),
                "created_at": datetime.now(),
                "last_accessed": None,
                "access_count": 0,
                "classification": DataClassification.RAW.value,
                "tags": metadata.get("tags", []) if metadata else [],
                "schema": metadata.get("schema", {}) if metadata else {},
                "quality_score": await self._assess_data_quality(data)
            }

            # Store metadata
            self.metadata_store[data_id] = data_metadata

            # Update partition stats
            partition["file_count"] += 1
            partition["total_size"] += len(serialized_data)
            partition["last_modified"] = datetime.now()

            # Update zone stats
            zone_key = f"zone_{zone_name}"
            zone_info = self.metadata_store[zone_key]
            zone_info["file_count"] += 1
            zone_info["total_size"] += len(serialized_data)
            zone_info["last_modified"] = datetime.now()

            # Apply data lifecycle policies
            await self._apply_lifecycle_policies(data_id)

            self.logger.info(f"Stored data object: {data_id} in {zone_name}/{partition_key}")
            return data_id

        except Exception as e:
            self.logger.error(f"Data storage failed: {e}")
            return None

    def _write_file(self, file_path: Path, data: bytes):
        """Write data to file (synchronous)."""
        with open(file_path, 'wb') as f:
            f.write(data)

    async def retrieve_data(
        self,
        data_id: str,
        include_metadata: bool = False
    ) -> Optional[Union[bytes, Dict]]:
        """
        Retrieve data from the lake.

        Args:
            data_id: Data object ID
            include_metadata: Include metadata in response

        Returns:
            Retrieved data
        """
        try:
            if data_id not in self.metadata_store:
                return None

            metadata = self.metadata_store[data_id]
            file_path = Path(metadata["path"])

            if not file_path.exists():
                self.logger.error(f"Data file not found: {file_path}")
                return None

            # Read file
            data_bytes = await asyncio.get_event_loop().run_in_executor(None, self._read_file, file_path)

            # Decompress if needed
            if metadata.get("compressed"):
                import gzip
                data_bytes = gzip.decompress(data_bytes)

            # Parse based on format
            if metadata["format"] == DataFormat.JSON.value:
                data = json.loads(data_bytes.decode('utf-8'))
            else:
                data = data_bytes

            # Update access metadata
            metadata["last_accessed"] = datetime.now()
            metadata["access_count"] += 1

            if include_metadata:
                return {
                    "data": data,
                    "metadata": metadata
                }
            else:
                return data

        except Exception as e:
            self.logger.error(f"Data retrieval failed: {e}")
            return None

    def _read_file(self, file_path: Path) -> bytes:
        """Read data from file (synchronous)."""
        with open(file_path, 'rb') as f:
            return f.read()

    async def query_data(
        self,
        zone_name: Optional[str] = None,
        partition_key: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query data in the lake.

        Args:
            zone_name: Zone to query
            partition_key: Partition to query
            filters: Query filters
            limit: Maximum results

        Returns:
            Query results
        """
        try:
            results = []

            # Find matching data objects
            for data_id, metadata in self.metadata_store.items():
                if not data_id.startswith("data_"):
                    continue

                # Apply filters
                if zone_name and metadata.get("zone") != zone_name:
                    continue
                if partition_key and metadata.get("partition") != partition_key:
                    continue

                if filters:
                    if not self._matches_filters(metadata, filters):
                        continue

                results.append(metadata)

                if len(results) >= limit:
                    break

            return results

        except Exception as e:
            self.logger.error(f"Data query failed: {e}")
            return []

    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if metadata matches filters."""
        for key, value in filters.items():
            if key not in metadata:
                return False

            metadata_value = metadata[key]

            if isinstance(value, dict):
                # Range or complex filter
                if "min" in value and metadata_value < value["min"]:
                    return False
                if "max" in value and metadata_value > value["max"]:
                    return False
                if "contains" in value and value["contains"] not in str(metadata_value):
                    return False
            elif metadata_value != value:
                return False

        return True

    async def move_data_to_tier(
        self,
        data_id: str,
        new_tier: StorageTier
    ) -> bool:
        """
        Move data to different storage tier.

        Args:
            data_id: Data object ID
            new_tier: New storage tier

        Returns:
            Move success
        """
        try:
            if data_id not in self.metadata_store:
                return False

            metadata = self.metadata_store[data_id]
            current_path = Path(metadata["path"])

            # Create tier-specific path
            tier_path = self.data_lake_root / f"tier_{new_tier.value}"
            tier_path.mkdir(parents=True, exist_ok=True)

            # Move file
            new_filename = f"{data_id}_{new_tier.value}.{metadata['format']}"
            if metadata.get("compressed"):
                new_filename += ".gz"

            new_path = tier_path / new_filename

            await asyncio.get_event_loop().run_in_executor(None, shutil.move, str(current_path), str(new_path))

            # Update metadata
            metadata["path"] = str(new_path)
            metadata["storage_tier"] = new_tier.value
            metadata["tier_changed_at"] = datetime.now()

            self.logger.info(f"Moved data {data_id} to tier {new_tier.value}")
            return True

        except Exception as e:
            self.logger.error(f"Data tier move failed: {e}")
            return False

    async def _apply_lifecycle_policies(self, data_id: str):
        """Apply data lifecycle policies."""
        metadata = self.metadata_store[data_id]
        age_days = (datetime.now() - metadata["created_at"]).days

        # Move to warm storage after 30 days
        if age_days > 30 and metadata["storage_tier"] == StorageTier.HOT.value:
            await self.move_data_to_tier(data_id, StorageTier.WARM)

        # Move to cold storage after 90 days
        elif age_days > 90 and metadata["storage_tier"] == StorageTier.WARM.value:
            await self.move_data_to_tier(data_id, StorageTier.COLD)

        # Archive after retention period
        elif age_days > self.config["retention_days"]:
            await self.archive_data(data_id)

    async def archive_data(self, data_id: str) -> bool:
        """Archive data."""
        try:
            if data_id not in self.metadata_store:
                return False

            metadata = self.metadata_store[data_id]
            file_path = Path(metadata["path"])

            # Move to archive
            archive_path = self.data_lake_root / "archive"
            archive_path.mkdir(exist_ok=True)

            archived_path = archive_path / file_path.name
            await asyncio.get_event_loop().run_in_executor(None, shutil.move, str(file_path), str(archived_path))

            metadata["path"] = str(archived_path)
            metadata["archived"] = True
            metadata["archived_at"] = datetime.now()

            self.logger.info(f"Archived data: {data_id}")
            return True

        except Exception as e:
            self.logger.error(f"Data archival failed: {e}")
            return False

    async def _assess_data_quality(self, data: Union[Dict, List[Dict]]) -> float:
        """Assess data quality score."""
        if not self.config["quality_check_enabled"]:
            return 1.0

        score = 1.0

        try:
            if isinstance(data, dict):
                records = [data]
            elif isinstance(data, list):
                records = data
            else:
                return 0.5

            total_records = len(records)
            if total_records == 0:
                return 0.0

            # Check completeness
            completeness_scores = []
            for record in records:
                non_null_fields = sum(1 for v in record.values() if v is not None and str(v).strip())
                completeness = non_null_fields / max(len(record), 1)
                completeness_scores.append(completeness)

            avg_completeness = sum(completeness_scores) / len(completeness_scores)

            # Check consistency (basic)
            consistency_score = 1.0
            if records:
                sample_record = records[0]
                for record in records[1:]:
                    # Check if all records have similar structure
                    common_keys = set(sample_record.keys()) & set(record.keys())
                    consistency_score *= len(common_keys) / max(len(sample_record), len(record), 1)

            # Combine scores
            score = (avg_completeness * 0.7) + (consistency_score * 0.3)

        except Exception as e:
            self.logger.error(f"Data quality assessment failed: {e}")
            score = 0.5

        return max(0.0, min(1.0, score))

    def add_quality_rule(self, zone_name: str, rule: Dict):
        """Add data quality rule."""
        self.quality_rules[zone_name].append({
            **rule,
            "created_at": datetime.now()
        })

    def set_access_policy(self, resource_path: str, policy: Dict):
        """Set access control policy."""
        self.access_policies[resource_path] = {
            **policy,
            "created_at": datetime.now()
        }

    def check_access(self, user: str, resource: str, action: str) -> bool:
        """Check if user has access to resource."""
        # Simple access control - in real implementation would be more sophisticated
        policy = self.access_policies.get(resource, {})

        if not policy:
            return True  # No policy = allow

        allowed_users = policy.get("allowed_users", [])
        allowed_roles = policy.get("allowed_roles", [])
        denied_users = policy.get("denied_users", [])

        if user in denied_users:
            return False

        if user in allowed_users:
            return True

        # Check roles (simplified)
        user_roles = []  # Would get from user management system
        if any(role in allowed_roles for role in user_roles):
            return True

        return False

    def get_data_lake_stats(self) -> Dict:
        """Get data lake statistics."""
        total_size = 0
        total_files = 0
        zones_stats = {}

        for key, metadata in self.metadata_store.items():
            if key.startswith("zone_"):
                zone_name = metadata["name"]
                zones_stats[zone_name] = {
                    "type": metadata["type"],
                    "file_count": metadata["file_count"],
                    "total_size": metadata["total_size"],
                    "partitions": len(metadata["partitions"])
                }
                total_files += metadata["file_count"]
                total_size += metadata["total_size"]

        return {
            "total_zones": len(zones_stats),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_gb": total_size / (1024**3),
            "zones": zones_stats
        }

    def get_partition_info(self, partition_id: str) -> Optional[Dict]:
        """Get partition information."""
        return self.partitions.get(partition_id)

    def list_data_objects(
        self,
        zone_name: Optional[str] = None,
        partition_key: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """List data objects."""
        objects = []

        for data_id, metadata in self.metadata_store.items():
            if not data_id.startswith("data_"):
                continue

            if zone_name and metadata.get("zone") != zone_name:
                continue
            if partition_key and metadata.get("partition") != partition_key:
                continue

            objects.append(metadata)
            if len(objects) >= limit:
                break

        return objects

    async def optimize_storage(self):
        """Optimize data lake storage."""
        # Identify and remove orphaned files
        # Compact small files
        # Optimize partition structure
        # Run garbage collection

        self.logger.info("Running storage optimization")

        # Simple cleanup - remove old temp files, etc.
        # In real implementation would be more comprehensive

    async def continuous_data_lake_monitoring(self):
        """Continuous data lake monitoring."""
        while True:
            try:
                # Monitor storage usage
                stats = self.get_data_lake_stats()

                # Check for storage thresholds
                total_gb = stats["total_size_gb"]
                if total_gb > 100:  # Example threshold
                    self.logger.warning(f"Data lake size exceeds threshold: {total_gb:.2f} GB")

                # Apply lifecycle policies
                for data_id in list(self.metadata_store.keys()):
                    if data_id.startswith("data_"):
                        await self._apply_lifecycle_policies(data_id)

                # Optimize storage periodically
                await self.optimize_storage()

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                self.logger.error(f"Data lake monitoring error: {e}")
                await asyncio.sleep(300)


# Global data lake management instance
data_lake_management = DataLakeManagement()


def create_data_zone(zone_name: str, zone_type: str) -> bool:
    """Create data zone."""
    return data_lake_management.create_data_zone(zone_name, zone_type)


def create_data_partition(zone_name: str, partition_key: str) -> bool:
    """Create data partition."""
    return data_lake_management.create_partition(zone_name, partition_key)


async def store_data_object(
    zone_name: str,
    partition_key: str,
    data: Union[Dict, List[Dict]]
) -> Optional[str]:
    """Store data object."""
    return await data_lake_management.store_data(zone_name, partition_key, data)


async def retrieve_data_object(data_id: str) -> Optional[Union[bytes, Dict]]:
    """Retrieve data object."""
    return await data_lake_management.retrieve_data(data_id)


def query_data_objects(
    zone_name: Optional[str] = None,
    partition_key: Optional[str] = None
) -> List[Dict]:
    """Query data objects."""
    return data_lake_management.list_data_objects(zone_name, partition_key, limit)


def get_data_lake_statistics() -> Dict:
    """Get data lake statistics."""
    return data_lake_management.get_data_lake_stats()