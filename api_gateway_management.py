"""
API Gateway Management Module

This module implements API gateway functionality for the IoT IIoT platform,
providing centralized API management, routing, authentication, rate limiting, and monitoring.
"""

import asyncio
import hashlib
import json
import time
import uuid
import re
import aiohttp
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
from aiohttp import web

from utils.logging_config import get_logger

logger = get_logger(__name__)


class RouteType(Enum):
    """API route types."""
    REST = "rest"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    GRPC = "grpc"


class AuthenticationMethod(Enum):
    """Authentication methods."""
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    MUTUAL_TLS = "mutual_tls"


class RateLimitType(Enum):
    """Rate limiting types."""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    BANDWIDTH_PER_MINUTE = "bandwidth_per_minute"


class GatewayStatus(Enum):
    """Gateway status."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class APIGatewayManagement:
    """
    API Gateway for centralized API management.

    Features:
    - Route management and load balancing
    - Authentication and authorization
    - Rate limiting and throttling
    - Request/response transformation
    - API versioning and documentation
    - Monitoring and analytics
    - Security policies
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Gateway configuration
        self.gateway_status = GatewayStatus.STOPPED

        # API routes
        self.routes: Dict[str, Dict] = {}

        # Upstream services
        self.upstream_services: Dict[str, List[Dict]] = defaultdict(list)

        # Authentication configurations
        self.auth_configs: Dict[str, Dict] = {}

        # Rate limiting rules
        self.rate_limits: Dict[str, Dict] = {}

        # API keys and tokens
        self.api_keys: Dict[str, Dict] = {}
        self.jwt_tokens: Dict[str, Dict] = {}

        # Request/response transformations
        self.transformations: Dict[str, List[Dict]] = defaultdict(list)

        # API documentation
        self.api_docs: Dict[str, Dict] = {}

        # Monitoring and metrics
        self.request_metrics: Dict[str, Dict] = defaultdict(dict)
        self.latency_tracking: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Security policies
        self.security_policies: Dict[str, Dict] = {}

        # Load balancing
        self.load_balancers: Dict[str, Dict] = {}

        # Caching
        self.cache: Dict[str, Tuple[datetime, Dict]] = {}

        self.logger = get_logger(__name__)
        self.logger.info("API Gateway Management initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "host": "0.0.0.0",
            "port": 8080,
            "max_request_size": 10485760,  # 10MB
            "request_timeout": 30,  # seconds
            "max_concurrent_requests": 1000,
            "enable_cors": True,
            "enable_ssl": False,
            "ssl_cert_path": None,
            "ssl_key_path": None,
            "log_requests": True,
            "enable_metrics": True,
            "metrics_retention_days": 30,
        }

    def add_route(
        self,
        route_path: str,
        methods: List[str],
        upstream_service: str,
        route_config: Optional[Dict] = None
    ) -> bool:
        """
        Add API route to gateway.

        Args:
            route_path: Route path (e.g., "/api/v1/users")
            methods: HTTP methods (GET, POST, etc.)
            upstream_service: Upstream service name
            route_config: Route configuration

        Returns:
            Route addition success
        """
        try:
            route_id = str(uuid.uuid4())

            route = {
                "id": route_id,
                "path": route_path,
                "methods": methods,
                "upstream_service": upstream_service,
                "config": route_config or {},
                "created_at": datetime.now(),
                "enabled": True,
                "rate_limit": route_config.get("rate_limit") if route_config else None,
                "auth_required": route_config.get("auth_required", False) if route_config else False,
                "auth_method": route_config.get("auth_method") if route_config else None,
                "transform_request": route_config.get("transform_request") if route_config else None,
                "transform_response": route_config.get("transform_response") if route_config else None,
                "caching_enabled": route_config.get("caching_enabled", False) if route_config else False,
                "cache_ttl": route_config.get("cache_ttl", 300) if route_config else 300,
            }

            self.routes[route_id] = route

            self.logger.info(f"Added route: {methods} {route_path} -> {upstream_service}")
            return True

        except Exception as e:
            self.logger.error(f"Route addition failed: {e}")
            return False

    def add_upstream_service(
        self,
        service_name: str,
        service_url: str,
        service_config: Optional[Dict] = None
    ) -> bool:
        """
        Add upstream service.

        Args:
            service_name: Service name
            service_url: Service URL
            service_config: Service configuration

        Returns:
            Service addition success
        """
        try:
            service = {
                "name": service_name,
                "url": service_url.rstrip('/'),
                "config": service_config or {},
                "health_check_url": service_config.get("health_check_url") if service_config else None,
                "timeout": service_config.get("timeout", self.config["request_timeout"]) if service_config else self.config["request_timeout"],
                "retry_count": service_config.get("retry_count", 3) if service_config else 3,
                "circuit_breaker": {
                    "enabled": service_config.get("circuit_breaker_enabled", True) if service_config else True,
                    "failure_threshold": service_config.get("failure_threshold", 5) if service_config else 5,
                    "recovery_timeout": service_config.get("recovery_timeout", 60) if service_config else 60,
                    "state": "closed",
                    "failure_count": 0,
                    "last_failure": None
                },
                "load_balancing": service_config.get("load_balancing", "round_robin") if service_config else "round_robin",
                "weight": service_config.get("weight", 1) if service_config else 1,
                "created_at": datetime.now(),
                "status": "unknown"
            }

            self.upstream_services[service_name].append(service)

            self.logger.info(f"Added upstream service: {service_name} -> {service_url}")
            return True

        except Exception as e:
            self.logger.error(f"Upstream service addition failed: {e}")
            return False

    def configure_authentication(
        self,
        auth_method: AuthenticationMethod,
        auth_config: Dict
    ) -> bool:
        """
        Configure authentication method.

        Args:
            auth_method: Authentication method
            auth_config: Authentication configuration

        Returns:
            Configuration success
        """
        try:
            self.auth_configs[auth_method.value] = {
                "method": auth_method.value,
                "config": auth_config,
                "enabled": True,
                "created_at": datetime.now()
            }

            self.logger.info(f"Configured authentication: {auth_method.value}")
            return True

        except Exception as e:
            self.logger.error(f"Authentication configuration failed: {e}")
            return False

    def add_api_key(
        self,
        key_name: str,
        api_key: str,
        permissions: List[str],
        key_config: Optional[Dict] = None
    ) -> bool:
        """
        Add API key for authentication.

        Args:
            key_name: Key name
            api_key: API key value
            permissions: Key permissions
            key_config: Key configuration

        Returns:
            Key addition success
        """
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            api_key_config = {
                "name": key_name,
                "key_hash": key_hash,
                "permissions": permissions,
                "config": key_config or {},
                "created_at": datetime.now(),
                "enabled": True,
                "last_used": None,
                "usage_count": 0,
                "rate_limit_override": key_config.get("rate_limit_override") if key_config else None
            }

            self.api_keys[key_hash] = api_key_config

            self.logger.info(f"Added API key: {key_name}")
            return True

        except Exception as e:
            self.logger.error(f"API key addition failed: {e}")
            return False

    def add_rate_limit(
        self,
        limit_name: str,
        limit_type: RateLimitType,
        limit_value: int,
        limit_config: Optional[Dict] = None
    ) -> bool:
        """
        Add rate limiting rule.

        Args:
            limit_name: Limit name
            limit_type: Type of rate limit
            limit_value: Limit value
            limit_config: Limit configuration

        Returns:
            Limit addition success
        """
        try:
            rate_limit = {
                "name": limit_name,
                "type": limit_type.value,
                "value": limit_value,
                "config": limit_config or {},
                "created_at": datetime.now(),
                "enabled": True,
                "counters": defaultdict(lambda: deque(maxlen=1000))  # Request timestamps per client
            }

            self.rate_limits[limit_name] = rate_limit

            self.logger.info(f"Added rate limit: {limit_name} ({limit_type.value}: {limit_value})")
            return True

        except Exception as e:
            self.logger.error(f"Rate limit addition failed: {e}")
            return False

    async def start_gateway(self) -> bool:
        """Start API gateway."""
        try:
            self.gateway_status = GatewayStatus.RUNNING

            # Start background tasks
            asyncio.create_task(self._health_check_services())
            asyncio.create_task(self._cleanup_expired_tokens())
            asyncio.create_task(self._update_metrics())

            self.logger.info(f"API Gateway started on {self.config['host']}:{self.config['port']}")
            return True

        except Exception as e:
            self.logger.error(f"Gateway start failed: {e}")
            self.gateway_status = GatewayStatus.ERROR
            return False

    async def stop_gateway(self) -> bool:
        """Stop API gateway."""
        self.gateway_status = GatewayStatus.STOPPED
        self.logger.info("API Gateway stopped")
        return True

    async def process_request(
        self,
        method: str,
        path: str,
        headers: Dict,
        body: Optional[bytes] = None,
        query_params: Optional[Dict] = None,
        client_ip: Optional[str] = None
    ) -> Dict:
        """
        Process incoming API request.

        Args:
            method: HTTP method
            path: Request path
            headers: Request headers
            body: Request body
            query_params: Query parameters
            client_ip: Client IP address

        Returns:
            Response dictionary
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Find matching route
            route = self._find_route(method, path)
            if not route:
                return self._create_response(404, {"error": "Route not found"})

            # Check if route is enabled
            if not route.get("enabled", True):
                return self._create_response(403, {"error": "Route disabled"})

            # Caching check
            cache_key = None
            if route.get("caching_enabled"):
                cache_key = self._get_cache_key(method, path, headers, body)
                cached_response = self._get_from_cache(cache_key, route)
                if cached_response:
                    self.logger.info(f"Cache hit for request {request_id}")
                    # We still record a metric for cached responses
                    await self._record_request_metrics(request_id, route, cached_response, time.time() - start_time)
                    return cached_response

            # Authentication
            if route.get("auth_required"):
                auth_result = await self._authenticate_request(headers, route)
                if not auth_result["success"]:
                    return self._create_response(401, {"error": auth_result["error"]})

                client_id = auth_result.get("client_id")
            else:
                client_id = client_ip or "anonymous"

            # Rate limiting
            rate_limit_result = await self._check_rate_limit(client_id, route, headers)
            if not rate_limit_result["allowed"]:
                return self._create_response(429, {"error": "Rate limit exceeded"})

            # Request transformation
            transformed_request = await self._transform_request(route, body, headers, query_params)

            # Route to upstream service
            upstream_response = await self._route_to_upstream(route, transformed_request, headers, path)

            # Response transformation
            transformed_response = await self._transform_response(route, upstream_response)

            # Record metrics
            await self._record_request_metrics(request_id, route, upstream_response, time.time() - start_time)

            # Cache the response if enabled
            if route.get("caching_enabled") and cache_key:
                self._add_to_cache(cache_key, transformed_response, route)

            return transformed_response

        except Exception as e:
            self.logger.error(f"Request processing failed: {e}")
            return self._create_response(500, {"error": "Internal server error"})

    def _find_route(self, method: str, path: str) -> Optional[Dict]:
        """Find matching route for request using regex for path parameters."""
        for route in self.routes.values():
            if method.upper() not in route["methods"]:
                continue

            # Convert path template to regex
            # e.g., /users/{id} -> /users/(?P<id>[^/]+)
            path_regex = re.sub(r"{([^/]+)}", r"(?P<\1>[^/]+)", route["path"]) + '$'

            match = re.fullmatch(path_regex, path)
            if match:
                return route

        return None

    async def _authenticate_request(self, headers: Dict, route: Dict) -> Dict:
        """Authenticate API request."""
        auth_method = route.get("auth_method") or "api_key"

        if auth_method == "api_key":
            # Handle case-insensitivity of headers
            api_key = headers.get("x-api-key") or headers.get("X-API-Key") or headers.get("Authorization", "").replace("Bearer ", "")

            if not api_key:
                return {"success": False, "error": "API key required"}

            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            key_config = self.api_keys.get(key_hash)

            if not key_config or not key_config.get("enabled"):
                return {"success": False, "error": "Invalid API key"}

            # Check permissions
            required_permissions = route.get("config", {}).get("required_permissions", [])
            if required_permissions:
                key_permissions = key_config.get("permissions", [])
                if not any(perm in key_permissions for perm in required_permissions):
                    return {"success": False, "error": "Insufficient permissions"}

            # Update key usage
            key_config["last_used"] = datetime.now()
            key_config["usage_count"] += 1

            return {"success": True, "client_id": key_config["name"]}

        elif auth_method == "jwt":
            token = headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                return {"success": False, "error": "JWT token required"}

            # Validate JWT token
            token_data = self.jwt_tokens.get(token)
            if not token_data:
                return {"success": False, "error": "Invalid JWT token"}

            if token_data.get("expires_at") and datetime.now() > token_data["expires_at"]:
                return {"success": False, "error": "JWT token expired"}

            return {"success": True, "client_id": token_data.get("client_id")}

        return {"success": False, "error": "Unsupported authentication method"}

    async def _check_rate_limit(self, client_id: str, route: Dict, headers: Dict) -> Dict:
        """Check rate limiting for request."""
        # Check route-specific rate limit
        route_limit = route.get("rate_limit")
        if route_limit:
            limit_name = route_limit
        else:
            limit_name = "default"

        rate_limit = self.rate_limits.get(limit_name)
        if not rate_limit:
            return {"allowed": True}

        # Get client-specific counter
        counters = rate_limit["counters"]
        client_counter = counters[client_id]

        # Clean old requests
        now = datetime.now()
        window_seconds = self._get_rate_limit_window(rate_limit["type"])
        cutoff = now - timedelta(seconds=window_seconds)

        # Remove old timestamps
        while client_counter and client_counter[0] < cutoff:
            client_counter.popleft()

        # Check if under limit
        if len(client_counter) >= rate_limit["value"]:
            return {"allowed": False, "retry_after": window_seconds}

        # Add current request
        client_counter.append(now)

        return {"allowed": True}

    def _get_rate_limit_window(self, limit_type: str) -> int:
        """Get rate limit window in seconds."""
        if limit_type == "requests_per_minute":
            return 60
        elif limit_type == "requests_per_hour":
            return 3600
        else:
            return 60

    async def _transform_request(self, route: Dict, body: Optional[bytes], headers: Dict, query_params: Optional[Dict]) -> Dict:
        """Transform request before forwarding."""
        transform_config = route.get("transform_request")
        if not transform_config:
            return {"body": body, "headers": headers, "query_params": query_params}

        # Apply transformations
        transformed_body = body
        transformed_headers = headers.copy()
        transformed_params = query_params.copy() if query_params else {}

        # Simple transformation logic - in real implementation would be more sophisticated
        if transform_config.get("add_headers"):
            transformed_headers.update(transform_config["add_headers"])

        if transform_config.get("remove_headers"):
            for header in transform_config["remove_headers"]:
                transformed_headers.pop(header, None)

        return {
            "body": transformed_body,
            "headers": transformed_headers,
            "query_params": transformed_params
        }

    async def _route_to_upstream(self, route: Dict, request_data: Dict, headers: Dict, path: str) -> Dict:
        """Route request to upstream service."""
        upstream_service = route["upstream_service"]
        services = self.upstream_services.get(upstream_service, [])

        if not services:
            return {"status_code": 503, "body": {"error": "No upstream services available"}}

        # Select service using load balancing
        service = self._select_upstream_service(services, upstream_service)

        # Check circuit breaker
        if not self._check_circuit_breaker(service):
            return {"status_code": 503, "body": {"error": "Service temporarily unavailable"}}

        try:
            # Forward request to upstream service
            upstream_response = await self._forward_request(service, route, request_data, headers, path)

            # Update circuit breaker success
            self._record_circuit_breaker_success(service)

            return upstream_response

        except Exception as e:
            # Update circuit breaker failure
            self._record_circuit_breaker_failure(service)
            raise e

    def _select_upstream_service(self, services: List[Dict], service_name: str) -> Dict:
        """Select upstream service using load balancing."""
        # Simple round-robin for now
        lb_config = self.load_balancers.get(service_name, {"index": 0})

        healthy_services = [s for s in services if s["status"] == "healthy"]

        if not healthy_services:
            # Fallback to any service
            healthy_services = services

        index = lb_config.get("index", 0) % len(healthy_services)
        selected_service = healthy_services[index]

        # Update index
        lb_config["index"] = (index + 1) % len(healthy_services)
        self.load_balancers[service_name] = lb_config

        return selected_service

    def _check_circuit_breaker(self, service: Dict) -> bool:
        """Check circuit breaker state."""
        cb = service["circuit_breaker"]

        if cb["state"] == "closed":
            return True
        elif cb["state"] == "open":
            if datetime.now() > cb["last_failure"] + timedelta(seconds=cb["recovery_timeout"]):
                cb["state"] = "half_open"
                return True
            return False
        elif cb["state"] == "half_open":
            return True

        return True

    def _record_circuit_breaker_success(self, service: Dict):
        """Record successful request."""
        cb = service["circuit_breaker"]
        if cb["state"] == "half_open":
            cb["state"] = "closed"
            cb["failure_count"] = 0

    def _record_circuit_breaker_failure(self, service: Dict):
        """Record failed request."""
        cb = service["circuit_breaker"]
        cb["failure_count"] += 1
        cb["last_failure"] = datetime.now()

        if cb["failure_count"] >= cb["failure_threshold"]:
            cb["state"] = "open"

    async def _forward_request(self, service: Dict, route: Dict, request_data: Dict, headers: Dict, path: str) -> Dict:
        """Forward request to upstream service using aiohttp."""
        target_url = f"{service['url']}{path}"

        # Filter headers to avoid sending gateway-specific headers upstream
        forward_headers = {k: v for k, v in headers.items() if k.lower() not in ['host', 'x-api-key']}
        forward_headers['X-Forwarded-For'] = headers.get('X-Forwarded-For', 'unknown')

        try:
            async with aiohttp.ClientSession(headers=forward_headers) as session:
                async with session.request(
                    method=route['methods'][0], # Assuming one method for simplicity
                    url=target_url,
                    params=request_data.get("query_params"),
                    data=request_data.get("body"),
                    timeout=service['timeout']
                ) as response:
                    response_body = await response.json()
                    return {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "body": response_body
                    }
        except aiohttp.ClientError as e:
            self.logger.error(f"Upstream request failed for {service['name']}: {e}")
            return {"status_code": 502, "body": {"error": "Bad Gateway", "details": str(e)}}

    async def _transform_response(self, route: Dict, response: Dict) -> Dict:
        """Transform response before returning to client."""
        transform_config = route.get("transform_response")
        if not transform_config:
            return response

        # Apply response transformations
        transformed_response = response.copy()

        # Simple transformation logic
        if transform_config.get("add_headers"):
            transformed_response["headers"].update(transform_config["add_headers"])

        if transform_config.get("remove_fields"):
            body = transformed_response.get("body", {})
            if isinstance(body, dict):
                for field in transform_config["remove_fields"]:
                    body.pop(field, None)

        return transformed_response

    async def _record_request_metrics(self, request_id: str, route: Dict, response: Dict, latency: float):
        """Record request metrics."""
        route_path = route["path"]

        if route_path not in self.request_metrics:
            self.request_metrics[route_path] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_latency": 0.0,
                "last_request": None
            }

        metrics = self.request_metrics[route_path]
        metrics["total_requests"] += 1
        metrics["last_request"] = datetime.now()

        if response.get("status_code", 500) < 400:
            metrics["successful_requests"] += 1
        else:
            metrics["failed_requests"] += 1

        # Update average latency
        total_requests = metrics["total_requests"]
        current_avg = metrics["avg_latency"]
        metrics["avg_latency"] = (current_avg * (total_requests - 1) + latency) / total_requests

        # Track latency
        self.latency_tracking[route_path].append(latency)

    def _create_response(self, status_code: int, body: Dict, headers: Optional[Dict] = None) -> Dict:
        """Create standardized response."""
        return {
            "status_code": status_code,
            "headers": headers or {"Content-Type": "application/json"},
            "body": body
        }

    async def _health_check_services(self):
        """Perform health checks on upstream services."""
        while self.gateway_status == GatewayStatus.RUNNING:
            try:
                for service_name, services in self.upstream_services.items():
                    for service in services:
                        await self._health_check_service(service)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Service health check error: {e}")
                await asyncio.sleep(30)

    async def _health_check_service(self, service: Dict):
        """Health check individual service by making a real HTTP request."""
        health_url = service.get("health_check_url")
        if not health_url:
            service["status"] = "healthy" # Assume healthy if no health check URL
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=5) as response:
                    if response.status >= 200 and response.status < 300:
                        service["status"] = "healthy"
                    else:
                        service["status"] = "unhealthy"
                        self.logger.warning(f"Health check failed for {service['name']} with status {response.status}")
        except Exception as e:
            self.logger.error(f"Health check failed for {service['name']}: {e}")
            service["status"] = "unhealthy"

    async def _cleanup_expired_tokens(self):
        """Clean up expired JWT tokens."""
        while self.gateway_status == GatewayStatus.RUNNING:
            try:
                now = datetime.now()
                expired_tokens = []

                for token, token_data in self.jwt_tokens.items():
                    if token_data.get("expires_at") and now > token_data["expires_at"]:
                        expired_tokens.append(token)

                for token in expired_tokens:
                    del self.jwt_tokens[token]

                await asyncio.sleep(300)  # Clean every 5 minutes

            except Exception as e:
                self.logger.error(f"Token cleanup error: {e}")
                await asyncio.sleep(300)

    async def _update_metrics(self):
        """Update and aggregate metrics."""
        while self.gateway_status == GatewayStatus.RUNNING:
            try:
                # Aggregate metrics
                total_requests = sum(m.get("total_requests", 0) for m in self.request_metrics.values())
                total_successful = sum(m.get("successful_requests", 0) for m in self.request_metrics.values())

                if total_requests > 0:
                    success_rate = total_successful / total_requests
                    self.logger.info(f"Gateway metrics - Total requests: {total_requests}, Success rate: {success_rate:.2%}")

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                self.logger.error(f"Metrics update error: {e}")
                await asyncio.sleep(60)

    def get_gateway_status(self) -> Dict:
        """Get gateway status."""
        return {
            "status": self.gateway_status.value,
            "routes_count": len([r for r in self.routes.keys() if isinstance(r, str) and r.startswith("route_")]),
            "services_count": len(self.upstream_services),
            "uptime": str(datetime.now() - self.config.get("start_time", datetime.now())),
            "config": self.config
        }

    def get_route_metrics(self, route_path: Optional[str] = None) -> Dict:
        """Get route metrics."""
        if route_path:
            return self.request_metrics.get(route_path, {})

        return dict(self.request_metrics)

    def get_upstream_services_status(self) -> Dict[str, List[Dict]]:
        """Get upstream services status."""
        return {
            service_name: [
                {
                    "name": service["name"],
                    "url": service["url"],
                    "status": service["status"],
                    "circuit_breaker_state": service["circuit_breaker"]["state"]
                }
                for service in services
            ]
            for service_name, services in self.upstream_services.items()
        }

    # --- Caching Methods ---
    def _get_cache_key(self, method: str, path: str, headers: Dict, body: Optional[bytes]) -> str:
        """Generate a cache key for a request."""
        key_parts = f"{method}:{path}"
        # In a real system, you might vary on specific headers
        if body:
            key_parts += ":" + hashlib.md5(body).hexdigest()
        return key_parts

    def _add_to_cache(self, key: str, response: Dict, route: Dict):
        """Add a response to the cache."""
        ttl = timedelta(seconds=route.get("cache_ttl", 300))
        expiration = datetime.now() + ttl
        self.cache[key] = (expiration, response)
        self.logger.info(f"Cached response for key: {key} with TTL: {ttl.seconds}s")

    def _get_from_cache(self, key: str, route: Dict) -> Optional[Dict]:
        """Retrieve a response from the cache if it's valid."""
        if key in self.cache:
            expiration, response = self.cache[key]
            if datetime.now() < expiration:
                return response
            else:
                # Cache expired
                del self.cache[key]
        return None

    # --- Server Methods ---
    async def _handle_request(self, request: web.Request) -> web.Response:
        """Main handler for all incoming aiohttp requests."""
        body = await request.read()
        response_data = await self.process_request(
            method=request.method,
            path=request.path,
            headers={k.lower(): v for k, v in request.headers.items()},
            body=body if body else None,
            query_params=dict(request.query),
            client_ip=request.remote
        )

        # aiohttp's json_response sets Content-Type automatically.
        # We should remove it from our headers if it exists to avoid conflict.
        response_headers = response_data.get("headers", {})
        if 'Content-Type' in response_headers:
            del response_headers['Content-Type']

        return web.json_response(
            data=response_data.get("body"),
            status=response_data.get("status_code", 500),
            headers=response_headers
        )

    async def run_server(self):
        """Run the aiohttp web server."""
        app = web.Application()
        app.router.add_route("*", "/{path:.*}", self._handle_request)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.config["host"], self.config["port"])

        await self.start_gateway()
        self.config["start_time"] = datetime.now()

        logger.info(f"API Gateway server running on http://{self.config['host']}:{self.config['port']}")
        await site.start()

        # Keep server running until stopped
        while self.gateway_status == GatewayStatus.RUNNING:
            await asyncio.sleep(1)

        await runner.cleanup()


if __name__ == "__main__":
    import argparse
    import subprocess

    async def run_dummy_service(port: int, name: str, health_endpoint: bool = False):
        """Runs a simple aiohttp service to act as an upstream target."""
        app = web.Application()

        async def handle(request):
            return web.json_response({"message": f"Response from {name}", "port": port})

        async def handle_health(request):
            return web.json_response({"status": "ok"})

        app.router.add_get("/{path:.*}", handle)
        if health_endpoint:
            app.router.add_get("/health", handle_health)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', port)
        await site.start()
        logger.info(f"Dummy service '{name}' running on http://127.0.0.1:{port}")

        # Keep it running
        while True:
            await asyncio.sleep(3600)

    async def run_tests():
        """Runs a series of curl commands to test the gateway."""
        await asyncio.sleep(2) # Give servers time to start
        logger.info("\n--- Running Integration Tests ---")

        tests = [
            ("Test 1: Valid request to user service", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/users/123", "200"),
            ("Test 2: Valid request to data service with API key", "curl -s -o /dev/null -w '%{http_code}' -H 'X-API-Key: test-key' http://127.0.0.1:8080/data", "200"),
            ("Test 3: Missing API key for protected route", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/data", "401"),
            ("Test 4: Rate limit test (3 requests, 2 should pass, 1 fail)", "", "")
        ]

        for desc, cmd, expected in tests:
            logger.info(f"[TEST] {desc}")
            if cmd:
                process = await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, _ = await process.communicate()
                status_code = stdout.decode().strip()
                if status_code == expected:
                    logger.info(f"  -> PASSED (Expected {expected}, Got {status_code})")
                else:
                    logger.error(f"  -> FAILED (Expected {expected}, Got {status_code})")

            if "Rate limit" in desc:
                # Fire off 3 requests quickly
                for i in range(3):
                    cmd = "curl -s -o /dev/null -w '%{http_code}' -H 'X-API-Key: test-key' http://127.0.0.1:8080/data"
                    process = await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, _ = await process.communicate()
                    status_code = stdout.decode().strip()
                    if i < 2: # First 2 should pass
                        if status_code == "200": logger.info("  -> Request PASSED (as expected)")
                        else: logger.error(f"  -> Request FAILED (Expected 200, Got {status_code})")
                    else: # 3rd should fail
                        if status_code == "429": logger.info("  -> Request BLOCKED (as expected)")
                        else: logger.error(f"  -> Request FAILED to be blocked (Expected 429, Got {status_code})")

        logger.info("--- Integration Tests Finished ---\n")


    async def main():
        """Main async function to coordinate services and gateway."""
        # Start dummy upstream services in the background
        service1_task = asyncio.create_task(run_dummy_service(8081, "user-service"))
        service2_task = asyncio.create_task(run_dummy_service(8082, "data-service", health_endpoint=True))

        # Configure the gateway
        gateway = APIGatewayManagement()
        gateway.add_upstream_service("users", "http://127.0.0.1:8081")
        gateway.add_upstream_service("data", "http://127.0.0.1:8082", {"health_check_url": "http://127.0.0.1:8082/health"})

        gateway.add_route("/users/{id}", ["GET"], "users")
        gateway.add_route("/data", ["GET"], "data", {"auth_required": True, "rate_limit": "data-limit"})

        gateway.add_api_key("test-client", "test-key", ["read:data"])
        gateway.add_rate_limit("data-limit", RateLimitType.REQUESTS_PER_MINUTE, 2) # Very low limit for testing

        # Start tests in the background
        test_task = asyncio.create_task(run_tests())

        # Start the gateway server (this will run until stopped)
        server_task = asyncio.create_task(gateway.run_server())

        await test_task # Wait for tests to complete

        # Cleanly shut down
        await gateway.stop_gateway()
        server_task.cancel()
        service1_task.cancel()
        service2_task.cancel()

        try:
            await server_task
        except asyncio.CancelledError:
            logger.info("Gateway server has been shut down.")


    parser = argparse.ArgumentParser(description="API Gateway Management CLI")
    parser.add_argument("command", choices=["start"], help="Command to execute")
    args = parser.parse_args()

    if args.command == "start":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("Gateway shutting down.")