"""
Microservices Architecture Migration Module

This module implements microservices architecture patterns, service discovery,
API gateway, circuit breakers, and distributed tracing for the IoT IIoT platform.
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum

from utils.logging_config import get_logger

logger = get_logger(__name__)


class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class MicroservicesArchitecture:
    """
    Microservices architecture implementation.

    Features:
    - Service discovery and registration
    - API gateway with routing
    - Circuit breaker pattern
    - Distributed tracing
    - Service mesh capabilities
    - Load balancing
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Service registry
        self.service_registry: Dict[str, Dict] = {}
        self.service_instances: Dict[str, List[Dict]] = defaultdict(list)

        # API gateway
        self.api_routes: Dict[str, Dict] = {}
        self.middlewares: List[Callable] = []

        # Circuit breakers
        self.circuit_breakers: Dict[str, Dict] = {}

        # Distributed tracing
        self.traces: Dict[str, Dict] = {}
        self.current_trace_id: Optional[str] = None

        # Load balancers
        self.load_balancers: Dict[str, Dict] = {}

        # Service mesh
        self.service_mesh_enabled = True
        self.mesh_policies: Dict[str, Dict] = {}

        self.logger = get_logger(__name__)
        self.logger.info("Microservices Architecture initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "service_discovery_port": 8500,
            "api_gateway_port": 8080,
            "health_check_interval": 30,
            "circuit_breaker_failure_threshold": 5,
            "circuit_breaker_timeout": 60,
            "circuit_breaker_retry_timeout": 30,
            "tracing_sample_rate": 0.1,
            "load_balancer_strategy": "round_robin",
            "service_mesh_enabled": True,
        }

    async def register_service(
        self,
        service_name: str,
        service_id: str,
        host: str,
        port: int,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Register a service instance.

        Args:
            service_name: Name of the service
            service_id: Unique service instance ID
            host: Service host
            port: Service port
            metadata: Additional service metadata

        Returns:
            Registration success
        """
        try:
            service_instance = {
                "service_id": service_id,
                "service_name": service_name,
                "host": host,
                "port": port,
                "address": f"{host}:{port}",
                "status": ServiceStatus.UNKNOWN.value,
                "registered_at": datetime.now(),
                "last_health_check": None,
                "health_check_failures": 0,
                "metadata": metadata or {},
                "tags": metadata.get("tags", []) if metadata else []
            }

            # Add to service registry
            if service_name not in self.service_registry:
                self.service_registry[service_name] = {
                    "service_name": service_name,
                    "instances": 0,
                    "healthy_instances": 0,
                    "created_at": datetime.now()
                }

            self.service_instances[service_name].append(service_instance)
            self.service_registry[service_name]["instances"] += 1

            # Initialize circuit breaker for this service
            await self._initialize_circuit_breaker(service_name)

            # Initialize load balancer for this service
            await self._initialize_load_balancer(service_name)

            self.logger.info(f"Registered service: {service_name} ({service_id}) at {host}:{port}")
            return True

        except Exception as e:
            self.logger.error(f"Service registration failed: {e}")
            return False

    async def deregister_service(self, service_name: str, service_id: str) -> bool:
        """Deregister a service instance."""
        try:
            if service_name in self.service_instances:
                instances = self.service_instances[service_name]
                for i, instance in enumerate(instances):
                    if instance["service_id"] == service_id:
                        instances.pop(i)
                        self.service_registry[service_name]["instances"] -= 1

                        # Update healthy count
                        if instance["status"] == ServiceStatus.HEALTHY.value:
                            self.service_registry[service_name]["healthy_instances"] -= 1

                        self.logger.info(f"Deregistered service: {service_name} ({service_id})")
                        return True

            return False

        except Exception as e:
            self.logger.error(f"Service deregistration failed: {e}")
            return False

    async def discover_service(self, service_name: str) -> List[Dict]:
        """
        Discover healthy instances of a service.

        Args:
            service_name: Name of the service to discover

        Returns:
            List of healthy service instances
        """
        if service_name not in self.service_instances:
            return []

        instances = self.service_instances[service_name]
        healthy_instances = [
            instance for instance in instances
            if instance["status"] == ServiceStatus.HEALTHY.value
        ]

        return healthy_instances

    async def get_service_instance(self, service_name: str) -> Optional[Dict]:
        """
        Get a service instance using load balancing.

        Args:
            service_name: Service name

        Returns:
            Selected service instance
        """
        healthy_instances = await self.discover_service(service_name)
        if not healthy_instances:
            return None

        # Use load balancer to select instance
        return await self._select_instance(service_name, healthy_instances)

    async def _select_instance(self, service_name: str, instances: List[Dict]) -> Dict:
        """Select service instance using load balancing strategy."""
        if service_name not in self.load_balancers:
            # Default round-robin
            balancer = self.load_balancers.get(service_name, {"index": 0})
            instance = instances[balancer["index"] % len(instances)]
            balancer["index"] += 1
            self.load_balancers[service_name] = balancer
            return instance

        balancer_config = self.load_balancers[service_name]
        strategy = balancer_config.get("strategy", "round_robin")

        if strategy == "round_robin":
            index = balancer_config.get("index", 0)
            instance = instances[index % len(instances)]
            balancer_config["index"] = index + 1
            return instance

        elif strategy == "least_connections":
            # Simplified: return first instance
            return instances[0]

        elif strategy == "random":
            import random
            return random.choice(instances)

        else:
            return instances[0]

    async def add_api_route(
        self,
        path: str,
        service_name: str,
        methods: List[str] = None,
        middlewares: List[Callable] = None
    ):
        """
        Add API route to gateway.

        Args:
            path: Route path
            service_name: Target service name
            methods: Allowed HTTP methods
            middlewares: Route-specific middlewares
        """
        route_config = {
            "path": path,
            "service_name": service_name,
            "methods": methods or ["GET", "POST", "PUT", "DELETE"],
            "middlewares": middlewares or [],
            "created_at": datetime.now(),
            "enabled": True
        }

        self.api_routes[path] = route_config
        self.logger.info(f"Added API route: {path} -> {service_name}")

    async def route_request(self, path: str, method: str = "GET") -> Optional[Dict]:
        """
        Route API request through gateway.

        Args:
            path: Request path
            method: HTTP method

        Returns:
            Routing information
        """
        # Find matching route
        for route_path, route_config in self.api_routes.items():
            if self._path_matches(route_path, path) and method in route_config["methods"]:
                # Get service instance
                service_instance = await self.get_service_instance(route_config["service_name"])

                if service_instance:
                    return {
                        "route": route_config,
                        "service_instance": service_instance,
                        "middlewares": route_config["middlewares"]
                    }

        return None

    def _path_matches(self, route_path: str, request_path: str) -> bool:
        """Check if request path matches route pattern."""
        # Simple pattern matching - in real implementation would use regex
        if route_path.endswith("/*"):
            base_path = route_path[:-2]
            return request_path.startswith(base_path)
        else:
            return route_path == request_path

    async def call_service(
        self,
        service_name: str,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict:
        """
        Call service through circuit breaker.

        Args:
            service_name: Target service name
            endpoint: Service endpoint
            method: HTTP method
            data: Request data
            headers: Request headers

        Returns:
            Service response
        """
        # Check circuit breaker
        if not await self._check_circuit_breaker(service_name):
            return {
                "status": "error",
                "error": "Circuit breaker open",
                "service": service_name
            }

        # Get service instance
        instance = await self.get_service_instance(service_name)
        if not instance:
            await self._record_circuit_breaker_failure(service_name)
            return {
                "status": "error",
                "error": "No healthy instances available",
                "service": service_name
            }

        # Make request with tracing
        trace_id = await self._start_trace(f"call_{service_name}_{endpoint}")

        try:
            response = await self._make_http_request(
                instance, endpoint, method, data, headers
            )

            await self._end_trace(trace_id, "success")
            await self._record_circuit_breaker_success(service_name)

            return response

        except Exception as e:
            await self._end_trace(trace_id, "error", str(e))
            await self._record_circuit_breaker_failure(service_name)

            return {
                "status": "error",
                "error": str(e),
                "service": service_name
            }

    async def _make_http_request(
        self,
        instance: Dict,
        endpoint: str,
        method: str,
        data: Optional[Dict],
        headers: Optional[Dict]
    ) -> Dict:
        """Make HTTP request to service instance."""
        # Placeholder - in real implementation would use aiohttp or similar
        url = f"http://{instance['address']}{endpoint}"

        # Simulate request
        await asyncio.sleep(0.01)  # Simulate network latency

        return {
            "status": "success",
            "url": url,
            "method": method,
            "response_time": 0.01,
            "data": {"message": f"Response from {instance['service_name']}"}
        }

    async def _initialize_circuit_breaker(self, service_name: str):
        """Initialize circuit breaker for service."""
        self.circuit_breakers[service_name] = {
            "state": CircuitBreakerState.CLOSED.value,
            "failure_count": 0,
            "last_failure_time": None,
            "next_retry_time": None
        }

    async def _check_circuit_breaker(self, service_name: str) -> bool:
        """Check if circuit breaker allows requests."""
        cb = self.circuit_breakers.get(service_name)
        if not cb:
            return True

        state = CircuitBreakerState(cb["state"])

        if state == CircuitBreakerState.CLOSED:
            return True
        elif state == CircuitBreakerState.OPEN:
            if datetime.now() > cb["next_retry_time"]:
                cb["state"] = CircuitBreakerState.HALF_OPEN.value
                return True
            return False
        elif state == CircuitBreakerState.HALF_OPEN:
            return True

        return True

    async def _record_circuit_breaker_success(self, service_name: str):
        """Record successful request."""
        cb = self.circuit_breakers.get(service_name)
        if cb and cb["state"] == CircuitBreakerState.HALF_OPEN.value:
            cb["state"] = CircuitBreakerState.CLOSED.value
            cb["failure_count"] = 0

    async def _record_circuit_breaker_failure(self, service_name: str):
        """Record failed request."""
        cb = self.circuit_breakers.get(service_name)
        if not cb:
            return

        cb["failure_count"] += 1
        cb["last_failure_time"] = datetime.now()

        if cb["failure_count"] >= self.config["circuit_breaker_failure_threshold"]:
            cb["state"] = CircuitBreakerState.OPEN.value
            cb["next_retry_time"] = datetime.now() + timedelta(
                seconds=self.config["circuit_breaker_retry_timeout"]
            )
            self.logger.warning(f"Circuit breaker opened for service: {service_name}")

    async def _initialize_load_balancer(self, service_name: str):
        """Initialize load balancer for service."""
        self.load_balancers[service_name] = {
            "strategy": self.config["load_balancer_strategy"],
            "index": 0,
            "connections": defaultdict(int)
        }

    async def _start_trace(self, operation: str) -> str:
        """Start distributed trace."""
        if not self._should_sample():
            return ""

        trace_id = f"trace_{int(time.time() * 1000000)}"
        span_id = f"span_{hash(operation) % 1000000}"

        self.traces[trace_id] = {
            "trace_id": trace_id,
            "root_span": span_id,
            "operation": operation,
            "start_time": datetime.now(),
            "spans": [{
                "span_id": span_id,
                "operation": operation,
                "start_time": datetime.now(),
                "tags": {}
            }],
            "status": "active"
        }

        self.current_trace_id = trace_id
        return trace_id

    async def _end_trace(self, trace_id: str, status: str, error: str = None):
        """End distributed trace."""
        if trace_id not in self.traces:
            return

        trace = self.traces[trace_id]
        trace["end_time"] = datetime.now()
        trace["status"] = status
        trace["duration"] = (trace["end_time"] - trace["start_time"]).total_seconds()

        if error:
            trace["error"] = error

        # Log trace
        self.logger.info(f"Trace completed: {trace_id} ({status}) in {trace['duration']:.3f}s")

    def _should_sample(self) -> bool:
        """Determine if request should be traced."""
        import random
        return random.random() < self.config["tracing_sample_rate"]

    async def health_check_services(self):
        """Perform health checks on all services."""
        for service_name, instances in self.service_instances.items():
            for instance in instances:
                await self._health_check_instance(instance)

    async def _health_check_instance(self, instance: Dict):
        """Health check individual service instance."""
        try:
            # Simple health check - in real implementation would make HTTP request
            # to service health endpoint
            health_status = ServiceStatus.HEALTHY.value

            instance["status"] = health_status
            instance["last_health_check"] = datetime.now()

            if health_status == ServiceStatus.HEALTHY.value:
                instance["health_check_failures"] = 0
            else:
                instance["health_check_failures"] += 1

        except Exception as e:
            instance["status"] = ServiceStatus.UNHEALTHY.value
            instance["health_check_failures"] += 1
            self.logger.error(f"Health check failed for {instance['service_id']}: {e}")

    def get_service_registry(self) -> Dict[str, Dict]:
        """Get service registry information."""
        registry_info = {}

        for service_name, service_info in self.service_registry.items():
            instances = self.service_instances[service_name]
            healthy_count = sum(1 for inst in instances
                              if inst["status"] == ServiceStatus.HEALTHY.value)

            registry_info[service_name] = {
                **service_info,
                "healthy_instances": healthy_count,
                "instances_detail": instances
            }

        return registry_info

    def get_circuit_breaker_status(self) -> Dict[str, Dict]:
        """Get circuit breaker status."""
        return self.circuit_breakers.copy()

    def get_traces(self, limit: int = 100) -> List[Dict]:
        """Get recent traces."""
        traces = list(self.traces.values())
        traces.sort(key=lambda x: x.get("start_time", datetime.min), reverse=True)
        return traces[:limit]

    async def add_middleware(self, middleware: Callable):
        """Add global middleware."""
        self.middlewares.append(middleware)

    async def apply_middlewares(self, request_context: Dict) -> Dict:
        """Apply middlewares to request."""
        context = request_context.copy()

        for middleware in self.middlewares:
            try:
                context = await middleware(context)
            except Exception as e:
                self.logger.error(f"Middleware error: {e}")

        return context

    async def continuous_health_monitoring(self):
        """Continuous health monitoring loop."""
        while True:
            try:
                await self.health_check_services()
                await asyncio.sleep(self.config["health_check_interval"])
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)


# Global microservices architecture instance
microservices_architecture = MicroservicesArchitecture()


async def register_microservice(
    service_name: str,
    service_id: str,
    host: str = "localhost",
    port: int = 8000
) -> bool:
    """Register a microservice."""
    return await microservices_architecture.register_service(
        service_name, service_id, host, port
    )


async def discover_services(service_name: str) -> List[Dict]:
    """Discover service instances."""
    return await microservices_architecture.discover_service(service_name)


async def call_microservice(
    service_name: str,
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None
) -> Dict:
    """Call microservice through architecture."""
    return await microservices_architecture.call_service(
        service_name, endpoint, method, data
    )


def get_service_health() -> Dict[str, Dict]:
    """Get service health status."""
    return microservices_architecture.get_service_registry()