"""
Edge Computing Framework Module

This module implements edge computing capabilities for the IoT IIoT platform,
enabling distributed processing, local AI inference, and edge-to-cloud synchronization.
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EdgeNodeStatus(Enum):
    """Edge node status."""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class ComputationType(Enum):
    """Types of edge computations."""
    AI_INFERENCE = "ai_inference"
    DATA_AGGREGATION = "data_aggregation"
    REAL_TIME_ANALYTICS = "real_time_analytics"
    LOCAL_STORAGE = "local_storage"
    PREPROCESSING = "preprocessing"


class DataSyncMode(Enum):
    """Data synchronization modes."""
    REAL_TIME = "real_time"
    BATCH = "batch"
    HYBRID = "hybrid"
    ON_DEMAND = "on_demand"


class EdgeComputingFramework:
    """
    Edge computing framework for distributed IoT processing.

    Features:
    - Edge node management and orchestration
    - Distributed AI inference
    - Data synchronization between edge and cloud
    - Local processing and storage
    - Edge-to-cloud communication optimization
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Edge nodes registry
        self.edge_nodes: Dict[str, Dict] = {}
        self.node_status: Dict[str, EdgeNodeStatus] = {}

        # Computation tasks
        self.computation_tasks: Dict[str, Dict] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()

        # Data synchronization
        self.sync_sessions: Dict[str, Dict] = {}
        self.data_cache: Dict[str, Dict] = defaultdict(dict)

        # AI models for edge deployment
        self.edge_models: Dict[str, Dict] = {}

        # Communication channels
        self.comm_channels: Dict[str, Dict] = {}

        # Performance monitoring
        self.performance_metrics: Dict[str, List[Dict]] = defaultdict(list)

        self.logger = get_logger(__name__)
        self.logger.info("Edge Computing Framework initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "max_edge_nodes": 1000,
            "heartbeat_interval": 30,  # seconds
            "sync_batch_size": 100,
            "sync_interval": 300,  # 5 minutes
            "cache_ttl": 3600,  # 1 hour
            "max_computation_time": 60,  # seconds
            "bandwidth_limit": 1000000,  # 1MB/s
            "storage_limit_per_node": 1000000000,  # 1GB
            "enable_offline_mode": True,
            "compression_enabled": True,
        }

    async def register_edge_node(
        self,
        node_id: str,
        capabilities: Dict,
        location: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Register an edge node.

        Args:
            node_id: Unique node identifier
            capabilities: Node capabilities (CPU, memory, storage, etc.)
            location: Geographic location
            metadata: Additional metadata

        Returns:
            Registration success
        """
        try:
            if len(self.edge_nodes) >= self.config["max_edge_nodes"]:
                self.logger.warning("Maximum edge nodes limit reached")
                return False

            node_info = {
                "node_id": node_id,
                "capabilities": capabilities,
                "location": location or {},
                "metadata": metadata or {},
                "registered_at": datetime.now(),
                "last_heartbeat": None,
                "status": EdgeNodeStatus.ONLINE.value,
                "computation_load": 0.0,
                "storage_used": 0,
                "network_latency": 0.0,
                "assigned_tasks": []
            }

            self.edge_nodes[node_id] = node_info
            self.node_status[node_id] = EdgeNodeStatus.ONLINE

            # Initialize communication channel
            await self._initialize_comm_channel(node_id)

            self.logger.info(f"Registered edge node: {node_id}")
            return True

        except Exception as e:
            self.logger.error(f"Edge node registration failed: {e}")
            return False

    async def unregister_edge_node(self, node_id: str) -> bool:
        """Unregister an edge node."""
        try:
            if node_id not in self.edge_nodes:
                return False

            # Migrate tasks to other nodes
            await self._migrate_node_tasks(node_id)

            # Clean up resources
            del self.edge_nodes[node_id]
            del self.node_status[node_id]

            if node_id in self.comm_channels:
                del self.comm_channels[node_id]

            self.logger.info(f"Unregistered edge node: {node_id}")
            return True

        except Exception as e:
            self.logger.error(f"Edge node unregistration failed: {e}")
            return False

    async def _migrate_node_tasks(self, node_id: str):
        """Migrate tasks from a node to other available nodes."""
        node_info = self.edge_nodes.get(node_id)
        if not node_info:
            return

        tasks_to_migrate = node_info["assigned_tasks"].copy()

        for task_id in tasks_to_migrate:
            if task_id in self.computation_tasks:
                # Find alternative node
                alternative_node = await self._find_optimal_node(
                    self.computation_tasks[task_id]["requirements"]
                )

                if alternative_node:
                    await self.assign_task_to_node(task_id, alternative_node)
                    self.logger.info(f"Migrated task {task_id} to node {alternative_node}")

    async def submit_computation_task(
        self,
        task_type: ComputationType,
        data: Union[Dict, bytes],
        requirements: Optional[Dict] = None,
        priority: int = 1
    ) -> str:
        """
        Submit computation task for edge processing.

        Args:
            task_type: Type of computation
            data: Input data
            requirements: Resource requirements
            priority: Task priority (1-10)

        Returns:
            Task ID
        """
        task_id = f"task_{task_type.value}_{int(time.time() * 1000000)}"

        task = {
            "task_id": task_id,
            "type": task_type.value,
            "data": data,
            "requirements": requirements or {},
            "priority": priority,
            "status": "queued",
            "submitted_at": datetime.now(),
            "assigned_node": None,
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }

        self.computation_tasks[task_id] = task

        # Add to processing queue
        await self.task_queue.put((priority, task_id))

        self.logger.info(f"Submitted computation task: {task_id}")
        return task_id

    async def assign_task_to_node(self, task_id: str, node_id: str) -> bool:
        """Assign task to specific edge node."""
        if task_id not in self.computation_tasks or node_id not in self.edge_nodes:
            return False

        task = self.computation_tasks[task_id]
        node_info = self.edge_nodes[node_id]

        # Check if node can handle the task
        if not self._node_can_handle_task(node_info, task["requirements"]):
            return False

        # Assign task
        task["assigned_node"] = node_id
        task["status"] = "assigned"
        node_info["assigned_tasks"].append(task_id)

        # Update node load
        node_info["computation_load"] += self._estimate_task_load(task)

        self.logger.info(f"Assigned task {task_id} to node {node_id}")
        return True

    def _node_can_handle_task(self, node_info: Dict, requirements: Dict) -> bool:
        """Check if node can handle task requirements."""
        capabilities = node_info["capabilities"]

        # Check CPU requirements
        if "cpu_cores" in requirements:
            if capabilities.get("cpu_cores", 0) < requirements["cpu_cores"]:
                return False

        # Check memory requirements
        if "memory_gb" in requirements:
            available_memory = capabilities.get("memory_gb", 0) - node_info["computation_load"]
            if available_memory < requirements["memory_gb"]:
                return False

        # Check storage requirements
        if "storage_gb" in requirements:
            available_storage = capabilities.get("storage_gb", 0) - node_info["storage_used"] / (1024**3)
            if available_storage < requirements["storage_gb"]:
                return False

        # Check supported computation types
        if "computation_types" in requirements:
            supported_types = capabilities.get("computation_types", [])
            if not any(comp_type in supported_types for comp_type in requirements["computation_types"]):
                return False

        return True

    def _estimate_task_load(self, task: Dict) -> float:
        """Estimate computational load of task."""
        # Simple estimation based on task type
        base_load = {
            ComputationType.AI_INFERENCE.value: 0.3,
            ComputationType.DATA_AGGREGATION.value: 0.1,
            ComputationType.REAL_TIME_ANALYTICS.value: 0.2,
            ComputationType.PREPROCESSING.value: 0.15,
            ComputationType.LOCAL_STORAGE.value: 0.05
        }

        return base_load.get(task["type"], 0.1)

    async def process_computation_task(self, task_id: str) -> Optional[Dict]:
        """Process a computation task on assigned edge node."""
        if task_id not in self.computation_tasks:
            return None

        task = self.computation_tasks[task_id]
        node_id = task["assigned_node"]

        if not node_id or node_id not in self.edge_nodes:
            task["error"] = "No assigned node available"
            task["status"] = "failed"
            return task

        try:
            task["status"] = "running"
            task["started_at"] = datetime.now()

            # Execute task on edge node
            result = await self._execute_task_on_node(task, node_id)

            task["status"] = "completed"
            task["completed_at"] = datetime.now()
            task["result"] = result

            # Update node load
            node_info = self.edge_nodes[node_id]
            node_info["computation_load"] -= self._estimate_task_load(task)
            node_info["assigned_tasks"].remove(task_id)

            # Cache result
            await self._cache_task_result(task_id, result)

            return task

        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            task["completed_at"] = datetime.now()

            # Update node load
            node_info = self.edge_nodes[node_id]
            node_info["computation_load"] -= self._estimate_task_load(task)

            self.logger.error(f"Task {task_id} failed: {e}")
            return task

    async def _execute_task_on_node(self, task: Dict, node_id: str) -> Dict:
        """Execute task on edge node."""
        # In real implementation, this would communicate with the actual edge node
        # For now, simulate task execution

        task_type = task["type"]
        data = task["data"]

        # Simulate processing time based on task type
        processing_times = {
            ComputationType.AI_INFERENCE.value: 2.0,
            ComputationType.DATA_AGGREGATION.value: 0.5,
            ComputationType.REAL_TIME_ANALYTICS.value: 1.0,
            ComputationType.PREPROCESSING.value: 0.8,
            ComputationType.LOCAL_STORAGE.value: 0.2
        }

        processing_time = processing_times.get(task_type, 1.0)
        await asyncio.sleep(processing_time)

        # Simulate result based on task type
        if task_type == ComputationType.AI_INFERENCE.value:
            result = {"prediction": 0.85, "confidence": 0.92}
        elif task_type == ComputationType.DATA_AGGREGATION.value:
            result = {"aggregated_count": 150, "avg_value": 23.5}
        elif task_type == ComputationType.REAL_TIME_ANALYTICS.value:
            result = {"anomaly_detected": False, "trend": "stable"}
        elif task_type == ComputationType.PREPROCESSING.value:
            result = {"processed_records": 100, "quality_score": 0.95}
        else:
            result = {"status": "completed", "processed_at": node_id}

        return result

    async def _find_optimal_node(self, requirements: Dict) -> Optional[str]:
        """Find optimal edge node for task requirements."""
        available_nodes = [
            node_id for node_id, status in self.node_status.items()
            if status == EdgeNodeStatus.ONLINE
        ]

        if not available_nodes:
            return None

        # Score nodes based on requirements match and current load
        node_scores = {}

        for node_id in available_nodes:
            node_info = self.edge_nodes[node_id]

            if not self._node_can_handle_task(node_info, requirements):
                continue

            # Calculate score based on load, latency, and capabilities match
            load_score = 1.0 - node_info["computation_load"]  # Lower load = higher score
            latency_score = max(0, 1.0 - node_info["network_latency"] / 1000)  # Lower latency = higher score

            # Capabilities match score
            match_score = self._calculate_capability_match(node_info["capabilities"], requirements)

            total_score = (load_score * 0.4) + (latency_score * 0.3) + (match_score * 0.3)
            node_scores[node_id] = total_score

        if not node_scores:
            return None

        # Return node with highest score
        return max(node_scores, key=node_scores.get)

    def _calculate_capability_match(self, capabilities: Dict, requirements: Dict) -> float:
        """Calculate how well node capabilities match requirements."""
        match_score = 0.0
        total_requirements = 0

        # Check CPU match
        if "cpu_cores" in requirements:
            total_requirements += 1
            required = requirements["cpu_cores"]
            available = capabilities.get("cpu_cores", 0)
            if available >= required:
                match_score += 1.0

        # Check memory match
        if "memory_gb" in requirements:
            total_requirements += 1
            required = requirements["memory_gb"]
            available = capabilities.get("memory_gb", 0.0)
            if available >= required:
                match_score += 1.0

        # Check computation types match
        if "computation_types" in requirements:
            total_requirements += 1
            required_types = set(requirements["computation_types"])
            available_types = set(capabilities.get("computation_types", []))
            if required_types.issubset(available_types):
                match_score += 1.0

        return match_score / max(total_requirements, 1)

    async def sync_data_to_cloud(
        self,
        node_id: str,
        data: Dict,
        sync_mode: DataSyncMode = DataSyncMode.BATCH
    ) -> bool:
        """
        Synchronize data from edge node to cloud.

        Args:
            node_id: Edge node ID
            data: Data to sync
            sync_mode: Synchronization mode

        Returns:
            Sync success
        """
        try:
            sync_session_id = f"sync_{node_id}_{int(time.time())}"

            sync_session = {
                "session_id": sync_session_id,
                "node_id": node_id,
                "data": data,
                "mode": sync_mode.value,
                "status": "in_progress",
                "started_at": datetime.now(),
                "completed_at": None,
                "bytes_transferred": 0,
                "compression_ratio": 1.0
            }

            self.sync_sessions[sync_session_id] = sync_session

            # Compress data if enabled
            if self.config["compression_enabled"]:
                data, compression_ratio = await self._compress_data(data)
                sync_session["compression_ratio"] = compression_ratio

            # Sync based on mode
            if sync_mode == DataSyncMode.REAL_TIME:
                success = await self._sync_realtime(node_id, data)
            elif sync_mode == DataSyncMode.BATCH:
                success = await self._sync_batch(node_id, data)
            elif sync_mode == DataSyncMode.HYBRID:
                success = await self._sync_hybrid(node_id, data)
            else:  # ON_DEMAND
                success = await self._sync_ondemand(node_id, data)

            sync_session["status"] = "completed" if success else "failed"
            sync_session["completed_at"] = datetime.now()
            sync_session["bytes_transferred"] = len(json.dumps(data).encode())

            # Cache synced data
            await self._cache_synced_data(node_id, data)

            return success

        except Exception as e:
            self.logger.error(f"Data sync failed for node {node_id}: {e}")
            return False

    async def _sync_realtime(self, node_id: str, data: Dict) -> bool:
        """Real-time data synchronization."""
        # Immediate sync with low latency
        return await self._send_data_to_cloud(node_id, data, priority="high")

    async def _sync_batch(self, node_id: str, data: Dict) -> bool:
        """Batch data synchronization."""
        # Accumulate data and send in batches
        return await self._send_data_to_cloud(node_id, data, priority="normal")

    async def _sync_hybrid(self, node_id: str, data: Dict) -> bool:
        """Hybrid synchronization (real-time + batch)."""
        # Critical data real-time, other data batched
        critical_data = {k: v for k, v in data.items() if self._is_critical_data(k)}
        normal_data = {k: v for k, v in data.items() if not self._is_critical_data(k)}

        success1 = await self._sync_realtime(node_id, critical_data) if critical_data else True
        success2 = await self._sync_batch(node_id, normal_data) if normal_data else True

        return success1 and success2

    async def _sync_ondemand(self, node_id: str, data: Dict) -> bool:
        """On-demand data synchronization."""
        # Sync only when requested or conditions met
        return await self._send_data_to_cloud(node_id, data, priority="low")

    def _is_critical_data(self, key: str) -> bool:
        """Check if data key represents critical information."""
        critical_keywords = ["alert", "emergency", "critical", "security", "anomaly"]
        return any(keyword in key.lower() for keyword in critical_keywords)

    async def _send_data_to_cloud(self, node_id: str, data: Dict, priority: str) -> bool:
        """Send data to cloud storage/API."""
        # Placeholder - in real implementation would use cloud APIs
        try:
            # Simulate network transfer
            data_size = len(json.dumps(data).encode())
            transfer_time = data_size / self.config["bandwidth_limit"]
            await asyncio.sleep(min(transfer_time, 5.0))  # Cap at 5 seconds

            self.logger.info(f"Sent {data_size} bytes from node {node_id} to cloud (priority: {priority})")
            return True

        except Exception as e:
            self.logger.error(f"Cloud sync failed: {e}")
            return False

    async def _compress_data(self, data: Dict) -> Tuple[Dict, float]:
        """Compress data for efficient transfer."""
        # Placeholder compression - in real implementation would use actual compression
        original_size = len(json.dumps(data).encode())
        # Simulate 30% compression
        compressed_data = data  # No actual compression for demo
        compressed_size = int(original_size * 0.7)
        compression_ratio = original_size / compressed_size

        return compressed_data, compression_ratio

    async def _cache_synced_data(self, node_id: str, data: Dict):
        """Cache synced data locally."""
        cache_key = f"{node_id}_{int(time.time())}"
        self.data_cache[node_id][cache_key] = {
            "data": data,
            "cached_at": datetime.now(),
            "ttl": self.config["cache_ttl"]
        }

        # Clean expired cache
        await self._clean_expired_cache(node_id)

    async def _clean_expired_cache(self, node_id: str):
        """Clean expired cache entries."""
        now = datetime.now()
        expired_keys = []

        for cache_key, cache_entry in self.data_cache[node_id].items():
            if now > cache_entry["cached_at"] + timedelta(seconds=cache_entry["ttl"]):
                expired_keys.append(cache_key)

        for key in expired_keys:
            del self.data_cache[node_id][key]

    async def deploy_ai_model_to_edge(self, model_id: str, model_data: bytes, target_nodes: List[str]) -> bool:
        """
        Deploy AI model to edge nodes.

        Args:
            model_id: Model identifier
            model_data: Model binary data
            target_nodes: List of target edge nodes

        Returns:
            Deployment success
        """
        try:
            self.edge_models[model_id] = {
                "model_id": model_id,
                "data": model_data,
                "size": len(model_data),
                "deployed_nodes": [],
                "deployed_at": datetime.now()
            }

            success_count = 0

            for node_id in target_nodes:
                if node_id in self.edge_nodes:
                    success = await self._deploy_model_to_node(model_id, node_id)
                    if success:
                        self.edge_models[model_id]["deployed_nodes"].append(node_id)
                        success_count += 1

            self.logger.info(f"Deployed model {model_id} to {success_count}/{len(target_nodes)} nodes")
            return success_count > 0

        except Exception as e:
            self.logger.error(f"Model deployment failed: {e}")
            return False

    async def _deploy_model_to_node(self, model_id: str, node_id: str) -> bool:
        """Deploy model to specific edge node."""
        # Placeholder - in real implementation would transfer model to edge device
        try:
            await asyncio.sleep(0.5)  # Simulate transfer time
            self.logger.info(f"Deployed model {model_id} to node {node_id}")
            return True
        except Exception:
            return False

    async def _initialize_comm_channel(self, node_id: str):
        """Initialize communication channel with edge node."""
        self.comm_channels[node_id] = {
            "channel_type": "websocket",  # Could be MQTT, HTTP, etc.
            "status": "connected",
            "last_message": datetime.now(),
            "message_count": 0,
            "error_count": 0
        }

    async def update_node_heartbeat(self, node_id: str, status_info: Dict):
        """Update edge node heartbeat and status."""
        if node_id not in self.edge_nodes:
            return

        node_info = self.edge_nodes[node_id]
        node_info["last_heartbeat"] = datetime.now()
        node_info["status"] = status_info.get("status", EdgeNodeStatus.ONLINE.value)
        node_info["computation_load"] = status_info.get("computation_load", 0.0)
        node_info["storage_used"] = status_info.get("storage_used", 0)
        node_info["network_latency"] = status_info.get("network_latency", 0.0)

        # Update status enum
        self.node_status[node_id] = EdgeNodeStatus(node_info["status"])

        # Record performance metrics
        metric_entry = {
            "timestamp": datetime.now(),
            "computation_load": node_info["computation_load"],
            "storage_used": node_info["storage_used"],
            "network_latency": node_info["network_latency"]
        }
        self.performance_metrics[node_id].append(metric_entry)

        # Keep only recent metrics
        if len(self.performance_metrics[node_id]) > 100:
            self.performance_metrics[node_id] = self.performance_metrics[node_id][-100:]

    async def _cache_task_result(self, task_id: str, result: Dict):
        """Cache task result."""
        cache_key = f"task_result_{task_id}"
        self.data_cache["tasks"][cache_key] = {
            "result": result,
            "cached_at": datetime.now(),
            "ttl": 3600  # 1 hour
        }

    def get_edge_nodes_status(self) -> Dict[str, Dict]:
        """Get status of all edge nodes."""
        return {
            node_id: {
                "status": self.node_status.get(node_id, EdgeNodeStatus.UNKNOWN).value,
                "capabilities": node_info.get("capabilities", {}),
                "computation_load": node_info.get("computation_load", 0.0),
                "storage_used": node_info.get("storage_used", 0),
                "last_heartbeat": node_info.get("last_heartbeat")
            }
            for node_id, node_info in self.edge_nodes.items()
        }

    def get_computation_tasks_status(self) -> Dict[str, Dict]:
        """Get status of computation tasks."""
        return self.computation_tasks.copy()

    def get_sync_sessions_status(self) -> Dict[str, Dict]:
        """Get status of data sync sessions."""
        return self.sync_sessions.copy()

    async def continuous_edge_monitoring(self):
        """Continuous edge computing monitoring loop."""
        while True:
            try:
                # Process queued tasks
                await self._process_task_queue()

                # Check node health
                await self._check_node_health()

                # Optimize resource allocation
                await self._optimize_resource_allocation()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                self.logger.error(f"Edge monitoring error: {e}")
                await asyncio.sleep(30)

    async def _process_task_queue(self):
        """Process queued computation tasks."""
        while not self.task_queue.empty():
            try:
                priority, task_id = await self.task_queue.get()

                if task_id not in self.computation_tasks:
                    continue

                task = self.computation_tasks[task_id]

                # Find optimal node for task
                optimal_node = await self._find_optimal_node(task["requirements"])

                if optimal_node:
                    await self.assign_task_to_node(task_id, optimal_node)
                    await self.process_computation_task(task_id)
                else:
                    # Re-queue if no node available
                    await self.task_queue.put((priority, task_id))
                    break

            except Exception as e:
                self.logger.error(f"Task processing error: {e}")

    async def _check_node_health(self):
        """Check health of edge nodes."""
        now = datetime.now()

        for node_id, node_info in self.edge_nodes.items():
            last_heartbeat = node_info.get("last_heartbeat")

            if last_heartbeat and (now - last_heartbeat).seconds > self.config["heartbeat_interval"] * 3:
                # Node is unresponsive
                self.node_status[node_id] = EdgeNodeStatus.OFFLINE
                node_info["status"] = EdgeNodeStatus.OFFLINE.value

                # Migrate tasks from offline node
                await self._migrate_node_tasks(node_id)

    async def _optimize_resource_allocation(self):
        """Optimize resource allocation across edge nodes."""
        # Simple load balancing - move tasks from overloaded to underloaded nodes
        overloaded_nodes = []
        underloaded_nodes = []

        for node_id, node_info in self.edge_nodes.items():
            if self.node_status[node_id] != EdgeNodeStatus.ONLINE:
                continue

            load = node_info["computation_load"]
            if load > 0.8:  # Overloaded
                overloaded_nodes.append((node_id, load))
            elif load < 0.3:  # Underloaded
                underloaded_nodes.append((node_id, load))

        # Migrate tasks from overloaded to underloaded nodes
        for overloaded_node, _ in overloaded_nodes:
            if not underloaded_nodes:
                break

            underloaded_node, _ = underloaded_nodes[0]

            # Find a task to migrate
            node_info = self.edge_nodes[overloaded_node]
            if node_info["assigned_tasks"]:
                task_id = node_info["assigned_tasks"][0]

                if await self.assign_task_to_node(task_id, underloaded_node):
                    node_info["assigned_tasks"].remove(task_id)
                    node_info["computation_load"] -= self._estimate_task_load(self.computation_tasks[task_id])


# Global edge computing framework instance
edge_computing_framework = EdgeComputingFramework()


async def register_edge_node(
    node_id: str,
    capabilities: Dict,
    location: Optional[Dict] = None
) -> bool:
    """Register edge node."""
    return await edge_computing_framework.register_edge_node(
        node_id, capabilities, location
    )


async def submit_edge_task(
    task_type: str,
    data: Union[Dict, bytes],
    requirements: Optional[Dict] = None
) -> str:
    """Submit task for edge processing."""
    return await edge_computing_framework.submit_computation_task(
        ComputationType(task_type), data, requirements
    )


async def sync_edge_data(
    node_id: str,
    data: Dict,
    sync_mode: str = "batch"
) -> bool:
    """Sync data from edge to cloud."""
    return await edge_computing_framework.sync_data_to_cloud(
        node_id, data, DataSyncMode(sync_mode)
    )


def get_edge_nodes_status() -> Dict[str, Dict]:
    """Get edge nodes status."""
    return edge_computing_framework.get_edge_nodes_status()


def get_edge_tasks_status() -> Dict[str, Dict]:
    """Get edge computation tasks status."""
    return edge_computing_framework.get_computation_tasks_status()


def get_sync_sessions_status() -> Dict[str, Dict]:
    """Get status of data sync sessions."""
    return edge_computing_framework.get_sync_sessions_status()