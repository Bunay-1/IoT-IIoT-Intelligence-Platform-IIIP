"""
Advanced Load Balancing Module

This module implements sophisticated load balancing algorithms for the IoT IIoT platform,
including AI-powered routing, geographic load balancing, and adaptive algorithms.
"""

import asyncio
import hashlib
import math
import random
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"
    LEAST_RESPONSE_TIME = "least_response_time"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    GEOGRAPHIC = "geographic"
    AI_PREDICTIVE = "ai_predictive"
    ADAPTIVE = "adaptive"


class ServerHealth(Enum):
    """Server health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"


class AdvancedLoadBalancing:
    """
    Advanced load balancing system with multiple algorithms and AI optimization.

    Features:
    - Multiple load balancing algorithms
    - Health checking and failover
    - Geographic load balancing
    - AI-powered predictive routing
    - Adaptive algorithm selection
    - Real-time performance monitoring
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Server pools
        self.server_pools: Dict[str, List[Dict]] = defaultdict(list)

        # Algorithm configurations
        self.algorithm_configs: Dict[str, Dict] = {}

        # Health monitoring
        self.server_health: Dict[str, Dict] = {}
        self.health_check_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Performance metrics
        self.performance_metrics: Dict[str, Dict] = defaultdict(dict)

        # Geographic mapping
        self.geographic_zones: Dict[str, List[str]] = defaultdict(list)

        # AI predictive model (placeholder)
        self.predictive_model = None

        # Adaptive algorithm selection
        self.algorithm_performance: Dict[str, Dict] = defaultdict(dict)

        self.logger = logging.getLogger(__name__)
        self.logger.info("Advanced Load Balancing initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "health_check_interval": 30,  # seconds
            "health_check_timeout": 5,    # seconds
            "max_failures": 3,
            "recovery_time": 60,          # seconds
            "metric_window_size": 100,
            "geographic_routing": True,
            "ai_prediction_enabled": False,
            "adaptive_algorithm_enabled": True,
            "default_algorithm": LoadBalancingAlgorithm.ROUND_ROBIN.value,
        }

    def create_server_pool(self, pool_name: str, servers: List[Dict]) -> bool:
        """
        Create a server pool for load balancing.

        Args:
            pool_name: Name of the server pool
            servers: List of server configurations

        Returns:
            Creation success
        """
        try:
            pool_servers = []

            for server in servers:
                server_config = {
                    "id": server["id"],
                    "host": server["host"],
                    "port": server.get("port", 80),
                    "weight": server.get("weight", 1),
                    "max_connections": server.get("max_connections", 1000),
                    "current_connections": 0,
                    "response_time": 0.0,
                    "error_rate": 0.0,
                    "health_status": ServerHealth.HEALTHY.value,
                    "last_health_check": None,
                    "failure_count": 0,
                    "location": server.get("location", {}),
                    "tags": server.get("tags", [])
                }

                pool_servers.append(server_config)

                # Initialize health monitoring
                self.server_health[server["id"]] = {
                    "status": ServerHealth.HEALTHY.value,
                    "last_check": datetime.now(),
                    "response_time": 0.0,
                    "uptime": 100.0
                }

                # Add to geographic zones if location provided
                if server_config["location"]:
                    zone = self._get_geographic_zone(server_config["location"])
                    self.geographic_zones[zone].append(server["id"])

            self.server_pools[pool_name] = pool_servers

            # Set default algorithm for pool
            self.algorithm_configs[pool_name] = {
                "algorithm": self.config["default_algorithm"],
                "round_robin_index": 0,
                "ip_hash_seed": random.randint(0, 1000)
            }

            self.logger.info(f"Created server pool: {pool_name} with {len(pool_servers)} servers")
            return True

        except Exception as e:
            self.logger.error(f"Server pool creation failed: {e}")
            return False

    def add_server_to_pool(self, pool_name: str, server_config: Dict) -> bool:
        """Dynamically add a new server to an existing pool."""
        if pool_name not in self.server_pools:
            self.logger.error(f"Cannot add server: Pool '{pool_name}' not found.")
            return False

        # Basic validation
        if not all(k in server_config for k in ['id', 'host']):
            self.logger.error("New server config must include 'id' and 'host'.")
            return False

        # Check for duplicate ID
        if any(s['id'] == server_config['id'] for s in self.server_pools[pool_name]):
            self.logger.warning(f"Server with ID '{server_config['id']}' already exists in pool '{pool_name}'.")
            return False

        new_server = {
            "id": server_config["id"], "host": server_config["host"],
            "port": server_config.get("port", 80), "weight": server_config.get("weight", 1),
            "max_connections": server_config.get("max_connections", 1000),
            "current_connections": 0, "response_time": 0.0, "error_rate": 0.0,
            "health_status": ServerHealth.HEALTHY.value, "last_health_check": None,
            "failure_count": 0, "location": server_config.get("location", {}),
            "tags": server_config.get("tags", [])
        }

        self.server_pools[pool_name].append(new_server)
        self.server_health[new_server['id']] = {"status": ServerHealth.HEALTHY.value, "last_check": datetime.now()}
        self.logger.info(f"Successfully added server {new_server['id']} to pool {pool_name}.")
        return True

    def remove_server_from_pool(self, pool_name: str, server_id: str) -> bool:
        """Dynamically remove a server from a pool."""
        if pool_name not in self.server_pools:
            self.logger.error(f"Cannot remove server: Pool '{pool_name}' not found.")
            return False

        server_index = -1
        for i, server in enumerate(self.server_pools[pool_name]):
            if server['id'] == server_id:
                server_index = i
                break

        if server_index == -1:
            self.logger.warning(f"Server with ID '{server_id}' not found in pool '{pool_name}'.")
            return False

        # Cleanly remove server and its health data
        self.server_pools[pool_name].pop(server_index)
        if server_id in self.server_health:
            del self.server_health[server_id]
        if server_id in self.health_check_history:
            del self.health_check_history[server_id]

        self.logger.info(f"Successfully removed server {server_id} from pool {pool_name}.")
        return True

    def update_server_weight(self, pool_name: str, server_id: str, new_weight: int) -> bool:
        """Update the weight of a specific server."""
        if pool_name not in self.server_pools:
            return False
        for server in self.server_pools[pool_name]:
            if server['id'] == server_id:
                server['weight'] = max(0, new_weight) # Ensure weight is non-negative
                self.logger.info(f"Updated weight for server {server_id} to {server['weight']}.")
                return True
        return False

    def set_load_balancing_algorithm(
        self,
        pool_name: str,
        algorithm: LoadBalancingAlgorithm,
        config: Optional[Dict] = None
    ):
        """
        Set load balancing algorithm for a server pool.

        Args:
            pool_name: Server pool name
            algorithm: Load balancing algorithm
            config: Algorithm-specific configuration
        """
        if pool_name not in self.server_pools:
            raise ValueError(f"Server pool {pool_name} not found")

        self.algorithm_configs[pool_name]["algorithm"] = algorithm.value

        if config:
            self.algorithm_configs[pool_name].update(config)

        self.logger.info(f"Set algorithm {algorithm.value} for pool {pool_name}")

    async def get_server(
        self,
        pool_name: str,
        client_ip: Optional[str] = None,
        client_location: Optional[Dict] = None,
        request_context: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Get optimal server for request using configured algorithm.

        Args:
            pool_name: Server pool name
            client_ip: Client IP address
            client_location: Client geographic location
            request_context: Additional request context

        Returns:
            Selected server configuration
        """
        if pool_name not in self.server_pools:
            return None

        servers = self.server_pools[pool_name]
        healthy_servers = [
            server for server in servers
            if self.server_health[server["id"]]["status"] == ServerHealth.HEALTHY.value
        ]

        if not healthy_servers:
            self.logger.warning(f"No healthy servers available in pool {pool_name}")
            return None

        algorithm_config = self.algorithm_configs[pool_name]
        algorithm = LoadBalancingAlgorithm(algorithm_config["algorithm"])

        # Select server based on algorithm
        if algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            selected_server = self._round_robin_selection(healthy_servers, algorithm_config)
        elif algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            selected_server = self._least_connections_selection(healthy_servers)
        elif algorithm == LoadBalancingAlgorithm.IP_HASH:
            selected_server = self._ip_hash_selection(healthy_servers, client_ip, algorithm_config)
        elif algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
            selected_server = self._least_response_time_selection(healthy_servers)
        elif algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            selected_server = self._weighted_round_robin_selection(healthy_servers, algorithm_config)
        elif algorithm == LoadBalancingAlgorithm.GEOGRAPHIC:
            selected_server = self._geographic_selection(healthy_servers, client_location)
        elif algorithm == LoadBalancingAlgorithm.AI_PREDICTIVE:
            selected_server = await self._ai_predictive_selection(healthy_servers, request_context)
        elif algorithm == LoadBalancingAlgorithm.ADAPTIVE:
            selected_server = await self._adaptive_selection(healthy_servers, request_context)
        else:
            selected_server = healthy_servers[0]  # Fallback

        if selected_server:
            # Update connection count
            selected_server["current_connections"] += 1

            # Record selection for analytics
            await self._record_server_selection(pool_name, selected_server["id"], request_context)

        return selected_server

    def _round_robin_selection(self, servers: List[Dict], config: Dict) -> Dict:
        """Round-robin server selection."""
        index = config.get("round_robin_index", 0)
        server = servers[index % len(servers)]
        config["round_robin_index"] = (index + 1) % len(servers)
        return server

    def _least_connections_selection(self, servers: List[Dict]) -> Dict:
        """Least connections server selection."""
        return min(servers, key=lambda s: s["current_connections"])

    def _ip_hash_selection(self, servers: List[Dict], client_ip: Optional[str], config: Dict) -> Dict:
        """IP hash-based server selection."""
        if not client_ip:
            return servers[0]

        # Create hash from IP and seed
        hash_input = f"{client_ip}_{config.get('ip_hash_seed', 0)}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        index = hash_value % len(servers)

        return servers[index]

    def _least_response_time_selection(self, servers: List[Dict]) -> Dict:
        """Least response time server selection."""
        # Weight by both response time and current connections
        def score_server(server):
            response_time = server["response_time"] or 1.0
            connections = server["current_connections"]
            return response_time * (1 + connections * 0.1)

        return min(servers, key=score_server)

    def _weighted_round_robin_selection(self, servers: List[Dict], config: Dict) -> Dict:
        """Weighted round-robin server selection."""
        total_weight = sum(server["weight"] for server in servers)
        if total_weight == 0:
            return self._round_robin_selection(servers, config)

        # Find server based on current position
        current_weight = config.get("weighted_index", 0)

        for server in servers:
            current_weight += server["weight"]
            if current_weight > config.get("weighted_position", 0):
                config["weighted_position"] = current_weight
                if current_weight >= total_weight:
                    config["weighted_position"] = 0
                return server

        # Fallback
        return servers[0]

    def _geographic_selection(self, servers: List[Dict], client_location: Optional[Dict]) -> Dict:
        """Geographic-based server selection."""
        if not client_location:
            return servers[0]

        client_zone = self._get_geographic_zone(client_location)

        # Prefer servers in same zone
        zone_servers = [
            server for server in servers
            if server["id"] in self.geographic_zones.get(client_zone, [])
        ]

        if zone_servers:
            return self._least_connections_selection(zone_servers)

        # Fallback to any server
        return self._least_connections_selection(servers)

    async def _ai_predictive_selection(self, servers: List[Dict], request_context: Optional[Dict]) -> Dict:
        """AI-powered predictive server selection."""
        if not self.predictive_model or not request_context:
            return self._least_connections_selection(servers)

        try:
            # Extract features from request context
            features = self._extract_request_features(request_context)

            # Predict best server for this request type
            predictions = {}
            for server in servers:
                server_features = features + [server["current_connections"], server["response_time"]]
                prediction = await self._predict_server_performance(server["id"], server_features)
                predictions[server["id"]] = prediction

            # Select server with best prediction
            best_server_id = max(predictions, key=predictions.get)
            return next(server for server in servers if server["id"] == best_server_id)

        except Exception as e:
            self.logger.error(f"AI predictive selection failed: {e}")
            return self._least_connections_selection(servers)

    async def _adaptive_selection(self, servers: List[Dict], request_context: Optional[Dict]) -> Dict:
        """Adaptive algorithm selection based on performance."""
        if not self.config["adaptive_algorithm_enabled"]:
            return self._least_connections_selection(servers)

        # Analyze recent performance of different algorithms
        best_algorithm = self._get_best_performing_algorithm()

        # Temporarily switch to best algorithm
        if best_algorithm == "least_response_time":
            return self._least_response_time_selection(servers)
        elif best_algorithm == "geographic":
            client_location = request_context.get("location") if request_context else None
            return self._geographic_selection(servers, client_location)
        else:
            return self._least_connections_selection(servers)

    def _get_geographic_zone(self, location: Dict) -> str:
        """Get geographic zone from location."""
        # Simple zone mapping - in real implementation would use geo databases
        lat = location.get("latitude", 0)
        lon = location.get("longitude", 0)

        if 35 <= lat <= 55 and -10 <= lon <= 20:  # Europe
            return "europe"
        elif 25 <= lat <= 50 and -125 <= lon <= -65:  # North America
            return "north_america"
        elif -50 <= lat <= 10 and 110 <= lon <= 155:  # Australia
            return "australia"
        else:
            return "global"

    async def _predict_server_performance(self, server_id: str, features: List[float]) -> float:
        """Predict server performance for given features."""
        # Placeholder - in real implementation would use trained ML model
        # Simulate prediction based on current load
        server_health = self.server_health.get(server_id, {})
        base_score = 1.0 - (server_health.get("response_time", 0) / 10.0)  # Normalize
        return max(0.1, min(1.0, base_score))

    def _extract_request_features(self, request_context: Dict) -> List[float]:
        """Extract features from request context."""
        features = []

        # Request type (GET=0, POST=1, etc.)
        method_map = {"GET": 0, "POST": 1, "PUT": 2, "DELETE": 3}
        features.append(method_map.get(request_context.get("method", "GET"), 0))

        # Request size
        features.append(len(str(request_context.get("body", ""))))

        # Time of day
        hour = datetime.now().hour
        features.append(hour / 24.0)  # Normalize to 0-1

        # User priority (if available)
        features.append(request_context.get("user_priority", 0.5))

        return features

    def _get_best_performing_algorithm(self) -> str:
        """Get best performing algorithm based on recent metrics."""
        # Analyze algorithm performance over time
        algorithm_scores = {}

        for alg, metrics in self.algorithm_performance.items():
            if metrics:
                avg_response_time = sum(m.get("avg_response_time", 1.0) for m in metrics) / len(metrics)
                error_rate = sum(m.get("error_rate", 0.0) for m in metrics) / len(metrics)
                score = 1.0 / (avg_response_time + error_rate + 0.1)  # Higher score = better
                algorithm_scores[alg] = score

        if algorithm_scores:
            return max(algorithm_scores, key=algorithm_scores.get)

        return "least_connections"  # Default

    async def _record_server_selection(
        self,
        pool_name: str,
        server_id: str,
        request_context: Optional[Dict]
    ):
        """Record server selection for analytics."""
        selection_record = {
            "timestamp": datetime.now(),
            "pool_name": pool_name,
            "server_id": server_id,
            "request_context": request_context or {}
        }

        # Store in performance metrics
        if pool_name not in self.performance_metrics:
            self.performance_metrics[pool_name] = {"selections": []}

        self.performance_metrics[pool_name]["selections"].append(selection_record)

        # Keep only recent records
        max_records = self.config["metric_window_size"]
        if len(self.performance_metrics[pool_name]["selections"]) > max_records:
            self.performance_metrics[pool_name]["selections"] = \
                self.performance_metrics[pool_name]["selections"][-max_records:]

    async def update_server_metrics(
        self,
        server_id: str,
        response_time: float,
        success: bool,
        connections: Optional[int] = None
    ):
        """
        Update server performance metrics.

        Args:
            server_id: Server identifier
            response_time: Response time in seconds
            success: Whether request was successful
            connections: Current connection count
        """
        if server_id not in self.server_health:
            return

        server_health = self.server_health[server_id]
        server_config = None

        # Find server in pools
        for pool_servers in self.server_pools.values():
            for server in pool_servers:
                if server["id"] == server_id:
                    server_config = server
                    break
            if server_config:
                break

        if not server_config:
            return

        # Update metrics
        server_config["response_time"] = response_time

        if connections is not None:
            server_config["current_connections"] = connections

        # Update error rate
        recent_checks = list(self.health_check_history[server_id])
        if recent_checks:
            error_count = sum(1 for check in recent_checks[-10:] if not check.get("success", True))
            server_config["error_rate"] = error_count / len(recent_checks[-10:])

        # Record health check
        health_record = {
            "timestamp": datetime.now(),
            "response_time": response_time,
            "success": success,
            "connections": connections
        }
        self.health_check_history[server_id].append(health_record)

        # Update server health status
        await self._update_server_health_status(server_id)

    async def _update_server_health_status(self, server_id: str):
        """Update server health status based on recent performance."""
        if server_id not in self.server_health:
            return

        recent_checks = list(self.health_check_history[server_id])[-10:]  # Last 10 checks

        if not recent_checks:
            return

        # Calculate health metrics
        success_rate = sum(1 for check in recent_checks if check["success"]) / len(recent_checks)
        avg_response_time = sum(check["response_time"] for check in recent_checks) / len(recent_checks)

        # Determine health status
        if success_rate < 0.8:  # Less than 80% success
            status = ServerHealth.UNHEALTHY
        elif avg_response_time > 5.0:  # Slow responses
            status = ServerHealth.OVERLOADED
        else:
            status = ServerHealth.HEALTHY

        self.server_health[server_id]["status"] = status.value
        self.server_health[server_id]["response_time"] = avg_response_time
        self.server_health[server_id]["last_check"] = datetime.now()

        # Update uptime calculation
        total_checks = len(self.health_check_history[server_id])
        successful_checks = sum(1 for check in self.health_check_history[server_id]
                              if check.get("success", False))
        uptime = (successful_checks / total_checks) * 100 if total_checks > 0 else 100.0
        self.server_health[server_id]["uptime"] = uptime

    async def perform_health_checks(self):
        """Perform health checks on all servers."""
        for pool_name, servers in self.server_pools.items():
            for server in servers:
                await self._health_check_server(server)

    async def _health_check_server(self, server: Dict):
        """Perform health check on a server."""
        server_id = server["id"]

        try:
            # Simple health check - in real implementation would make actual HTTP request
            start_time = time.time()

            # Simulate health check
            await asyncio.sleep(0.01)  # Simulate network latency
            success = random.random() > 0.05  # 95% success rate
            response_time = time.time() - start_time

            # Update metrics
            await self.update_server_metrics(server_id, response_time, success)

        except Exception as e:
            self.logger.error(f"Health check failed for server {server_id}: {e}")
            await self.update_server_metrics(server_id, 10.0, False)  # Mark as failed

    def get_pool_status(self, pool_name: str) -> Optional[Dict]:
        """Get status of a server pool."""
        if pool_name not in self.server_pools:
            return None

        servers = self.server_pools[pool_name]
        healthy_servers = sum(1 for server in servers
                            if self.server_health[server["id"]]["status"] == ServerHealth.HEALTHY.value)

        return {
            "pool_name": pool_name,
            "total_servers": len(servers),
            "healthy_servers": healthy_servers,
            "algorithm": self.algorithm_configs[pool_name]["algorithm"],
            "servers": [
                {
                    "id": server["id"],
                    "status": self.server_health[server["id"]]["status"],
                    "connections": server["current_connections"],
                    "response_time": server["response_time"],
                    "error_rate": server["error_rate"]
                }
                for server in servers
            ]
        }

    def get_performance_metrics(self) -> Dict[str, Dict]:
        """Get performance metrics for all pools."""
        return dict(self.performance_metrics)

    async def optimize_pool_configuration(self, pool_name: str):
        """Optimize pool configuration based on performance data."""
        if pool_name not in self.server_pools:
            return

        # Analyze performance data
        metrics = self.performance_metrics.get(pool_name, {})
        selections = metrics.get("selections", [])

        if len(selections) < 10:
            return  # Need more data

        # Analyze algorithm performance
        algorithm_metrics = defaultdict(list)

        for selection in selections[-50:]:  # Last 50 selections
            server_id = selection["server_id"]
            server_health = self.server_health.get(server_id, {})

            alg = self.algorithm_configs[pool_name]["algorithm"]
            algorithm_metrics[alg].append({
                "response_time": server_health.get("response_time", 1.0),
                "success": server_health.get("status") == ServerHealth.HEALTHY.value
            })

        # Update algorithm performance tracking
        for alg, metrics_list in algorithm_metrics.items():
            if metrics_list:
                avg_response_time = sum(m["response_time"] for m in metrics_list) / len(metrics_list)
                success_rate = sum(1 for m in metrics_list if m["success"]) / len(metrics_list)

                self.algorithm_performance[alg][pool_name] = {
                    "avg_response_time": avg_response_time,
                    "success_rate": success_rate,
                    "last_updated": datetime.now()
                }

    async def continuous_load_balancing(self):
        """Continuous load balancing monitoring and optimization."""
        while True:
            try:
                # Perform health checks
                await self.perform_health_checks()

                # Optimize configurations
                for pool_name in self.server_pools.keys():
                    await self.optimize_pool_configuration(pool_name)

                # Adaptive algorithm adjustment
                if self.config["adaptive_algorithm_enabled"]:
                    await self._adjust_algorithms_adaptively()

                await asyncio.sleep(self.config["health_check_interval"])

            except Exception as e:
                self.logger.error(f"Load balancing monitoring error: {e}")
                await asyncio.sleep(30)

    async def _adjust_algorithms_adaptively(self):
        """Adjust algorithms based on performance."""
        for pool_name in self.server_pools.keys():
            current_alg = self.algorithm_configs[pool_name]["algorithm"]
            best_alg = self._get_best_performing_algorithm()

            if best_alg and best_alg != current_alg:
                self.logger.info(f"Switching pool {pool_name} from {current_alg} to {best_alg}")
                self.algorithm_configs[pool_name]["algorithm"] = best_alg

    def _get_best_performing_algorithm(self) -> Optional[str]:
        """Get best performing algorithm across all pools."""
        algorithm_scores = defaultdict(list)

        for alg, pool_metrics in self.algorithm_performance.items():
            for pool_name, metrics in pool_metrics.items():
                # Calculate score (lower response time + higher success rate = better)
                score = (1.0 / (metrics["avg_response_time"] + 0.1)) * metrics["success_rate"]
                algorithm_scores[alg].append(score)

        if not algorithm_scores:
            return None

        # Average scores across pools
        avg_scores = {alg: sum(scores) / len(scores) for alg, scores in algorithm_scores.items()}

        return max(avg_scores, key=avg_scores.get) if avg_scores else None


# Global load balancing instance
advanced_load_balancing = AdvancedLoadBalancing()


def create_server_pool(pool_name: str, servers: List[Dict]) -> bool:
    """Create server pool."""
    return advanced_load_balancing.create_server_pool(pool_name, servers)


async def get_load_balanced_server(
    pool_name: str,
    client_ip: Optional[str] = None,
    client_location: Optional[Dict] = None
) -> Optional[Dict]:
    """Get load balanced server."""
    return await advanced_load_balancing.get_server(
        pool_name, client_ip, client_location
    )


def get_pool_status(pool_name: str) -> Optional[Dict]:
    """Get pool status."""
    return advanced_load_balancing.get_pool_status(pool_name)


def get_load_balancing_metrics() -> Dict[str, Dict]:
    """Get load balancing metrics."""
    return advanced_load_balancing.get_performance_metrics()


# --- New Helper Functions for Dynamic Management ---

def add_server(pool_name: str, server_config: Dict) -> bool:
    """Helper to add a server to a pool."""
    return advanced_load_balancing.add_server_to_pool(pool_name, server_config)


def remove_server(pool_name: str, server_id: str) -> bool:
    """Helper to remove a server from a pool."""
    return advanced_load_balancing.remove_server_from_pool(pool_name, server_id)


def update_weight(pool_name: str, server_id: str, new_weight: int) -> bool:
    """Helper to update a server's weight."""
    return advanced_load_balancing.update_server_weight(pool_name, server_id, new_weight)

async def main_demo():
    """Demonstrates the advanced load balancing functionalities."""
    print("--- Advanced Load Balancing Demo ---")

    # 1. Create a server pool
    pool_name = "web_servers"
    initial_servers = [
        {"id": "server-1", "host": "192.168.1.10", "weight": 5},
        {"id": "server-2", "host": "192.168.1.11", "weight": 10},
    ]
    create_server_pool(pool_name, initial_servers)
    print(f"\n1. Created server pool '{pool_name}'.")
    print(get_pool_status(pool_name))

    # 2. Get a server using Round Robin
    print("\n2. Selecting server with Round Robin...")
    server = await get_load_balanced_server(pool_name)
    print(f"   - Selected server: {server['id']}")
    server = await get_load_balanced_server(pool_name)
    print(f"   - Selected server: {server['id']}")

    # 3. Dynamically add a new server
    print("\n3. Dynamically adding a new server...")
    new_server_config = {"id": "server-3", "host": "192.168.1.12", "weight": 8}
    add_server(pool_name, new_server_config)
    print(f"   - Added server-3.")
    print(get_pool_status(pool_name))

    # 4. Update a server's weight
    print("\n4. Updating server weight...")
    update_weight(pool_name, "server-1", 20)
    print(f"   - Updated server-1 weight to 20.")
    print(get_pool_status(pool_name))

    # 5. Dynamically remove a server
    print("\n5. Dynamically removing a server...")
    remove_server(pool_name, "server-2")
    print(f"   - Removed server-2.")
    print(get_pool_status(pool_name))

    print("\n--- Demo Complete ---")


if __name__ == "__main__":
    asyncio.run(main_demo())
