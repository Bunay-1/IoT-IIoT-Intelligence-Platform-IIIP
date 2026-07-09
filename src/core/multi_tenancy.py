"""
Multi-Tenancy Module for IoT IIoT Platform
Tenant isolation, resource management, and enterprise features
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import jwt

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Tenant:
    """Tenant configuration."""
    tenant_id: str
    name: str
    domain: str
    status: str = "active"
    created_at: datetime = None
    settings: Dict[str, Any] = None
    resource_limits: Dict[str, Any] = None
    features: Set[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.settings is None:
            self.settings = {}
        if self.resource_limits is None:
            self.resource_limits = {
                "max_machines": 100,
                "max_users": 50,
                "storage_gb": 10,
                "api_calls_per_hour": 10000
            }
        if self.features is None:
            self.features = {"basic_monitoring", "alerts", "reports"}


class TenantManager:
    """
    Multi-tenant management system.
    Handles tenant isolation, resource allocation, and billing.
    """

    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_users: Dict[str, Set[str]] = {}  # tenant_id -> set of user_ids
        self.user_tenants: Dict[str, str] = {}  # user_id -> tenant_id
        self.resource_usage: Dict[str, Dict[str, Any]] = {}  # tenant_id -> usage stats

        # Default tenant for single-tenant mode
        self._create_default_tenant()

        logger.info("Tenant manager initialized")

    def _create_default_tenant(self):
        """Create default tenant for single-tenant deployments."""
        default_tenant = Tenant(
            tenant_id="default",
            name="Default Organization",
            domain="default.local",
            settings={"theme": "default", "timezone": "UTC"},
            resource_limits={
                "max_machines": 1000,
                "max_users": 100,
                "storage_gb": 100,
                "api_calls_per_hour": 100000
            },
            features={"all"}
        )
        self.tenants["default"] = default_tenant
        self.tenant_users["default"] = set()
        self.resource_usage["default"] = {
            "machines": 0,
            "users": 0,
            "storage_used_gb": 0,
            "api_calls_today": 0,
            "last_updated": datetime.now()
        }

    async def create_tenant(
        self,
        tenant_id: str,
        name: str,
        domain: str,
        admin_user_id: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """
        Create a new tenant.

        Args:
            tenant_id: Unique tenant identifier
            name: Tenant display name
            domain: Tenant domain
            admin_user_id: Administrator user ID
            settings: Tenant settings

        Returns:
            Created tenant
        """
        if tenant_id in self.tenants:
            raise ValueError(f"Tenant {tenant_id} already exists")

        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            domain=domain,
            settings=settings or {},
            features={"basic_monitoring", "alerts", "reports"}
        )

        self.tenants[tenant_id] = tenant
        self.tenant_users[tenant_id] = {admin_user_id}
        self.user_tenants[admin_user_id] = tenant_id
        self.resource_usage[tenant_id] = {
            "machines": 0,
            "users": 1,
            "storage_used_gb": 0,
            "api_calls_today": 0,
            "last_updated": datetime.now()
        }

        logger.info(f"Created tenant {tenant_id} for domain {domain}")
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self.tenants.get(tenant_id)

    def get_tenant_for_user(self, user_id: str) -> Optional[Tenant]:
        """Get tenant for a user."""
        tenant_id = self.user_tenants.get(user_id)
        if tenant_id:
            return self.tenants.get(tenant_id)
        return None

    def get_tenant_for_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant for a domain."""
        for tenant in self.tenants.values():
            if tenant.domain == domain:
                return tenant
        return None

    async def add_user_to_tenant(self, user_id: str, tenant_id: str) -> bool:
        """
        Add user to tenant.

        Args:
            user_id: User ID
            tenant_id: Tenant ID

        Returns:
            Success status
        """
        if tenant_id not in self.tenants:
            return False

        if user_id in self.user_tenants:
            # Remove from old tenant
            old_tenant_id = self.user_tenants[user_id]
            if old_tenant_id in self.tenant_users:
                self.tenant_users[old_tenant_id].discard(user_id)

        self.user_tenants[user_id] = tenant_id
        self.tenant_users[tenant_id].add(user_id)
        self.resource_usage[tenant_id]["users"] = len(self.tenant_users[tenant_id])

        logger.info(f"Added user {user_id} to tenant {tenant_id}")
        return True

    async def check_resource_limits(self, tenant_id: str, resource: str, amount: int = 1) -> bool:
        """
        Check if resource usage is within limits.

        Args:
            tenant_id: Tenant ID
            resource: Resource type
            amount: Amount to check

        Returns:
            True if within limits
        """
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False

        limits = tenant.resource_limits
        usage = self.resource_usage.get(tenant_id, {})

        if resource == "machines":
            return (usage.get("machines", 0) + amount) <= limits.get("max_machines", 100)
        elif resource == "users":
            return (usage.get("users", 0) + amount) <= limits.get("max_users", 50)
        elif resource == "storage":
            return (usage.get("storage_used_gb", 0) + amount) <= limits.get("storage_gb", 10)
        elif resource == "api_calls":
            # Check hourly limit
            calls_today = usage.get("api_calls_today", 0)
            return (calls_today + amount) <= limits.get("api_calls_per_hour", 10000)

        return True

    async def update_resource_usage(self, tenant_id: str, resource: str, amount: float):
        """
        Update resource usage for tenant.

        Args:
            tenant_id: Tenant ID
            resource: Resource type
            amount: Amount to add
        """
        if tenant_id not in self.resource_usage:
            self.resource_usage[tenant_id] = {
                "machines": 0,
                "users": 0,
                "storage_used_gb": 0,
                "api_calls_today": 0,
                "last_updated": datetime.now()
            }

        usage = self.resource_usage[tenant_id]

        if resource == "api_calls":
            usage["api_calls_today"] += amount
        elif resource == "storage":
            usage["storage_used_gb"] += amount
        elif resource == "machines":
            usage["machines"] += amount
        elif resource == "users":
            usage["users"] += amount

        usage["last_updated"] = datetime.now()

        # Reset daily counters if needed
        if datetime.now().date() != usage.get("last_reset_date"):
            usage["api_calls_today"] = 0
            usage["last_reset_date"] = datetime.now().date()

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant statistics."""
        tenant = self.tenants.get(tenant_id)
        usage = self.resource_usage.get(tenant_id, {})

        if not tenant:
            return {"error": "Tenant not found"}

        return {
            "tenant_id": tenant_id,
            "name": tenant.name,
            "domain": tenant.domain,
            "status": tenant.status,
            "users": usage.get("users", 0),
            "machines": usage.get("machines", 0),
            "storage_used_gb": usage.get("storage_used_gb", 0),
            "api_calls_today": usage.get("api_calls_today", 0),
            "resource_limits": tenant.resource_limits,
            "features": list(tenant.features),
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None
        }

    def list_tenants(self) -> List[Dict[str, Any]]:
        """List all tenants."""
        return [self.get_tenant_stats(tid) for tid in self.tenants.keys()]

    async def isolate_tenant_data(self, tenant_id: str, table_name: str, query: str) -> str:
        """
        Modify query to include tenant isolation.

        Args:
            tenant_id: Tenant ID
            table_name: Table name
            query: Original query

        Returns:
            Modified query with tenant filter
        """
        # Add tenant filter to WHERE clause
        tenant_filter = f"tenant_id = '{tenant_id}'"

        if "WHERE" in query.upper():
            # Insert tenant filter into existing WHERE
            where_pos = query.upper().find("WHERE")
            modified_query = query[:where_pos + 5] + f" {tenant_filter} AND" + query[where_pos + 5:]
        else:
            # Add WHERE clause
            modified_query = f"{query.rstrip(';')} WHERE {tenant_filter};"

        return modified_query

    def generate_tenant_token(self, tenant_id: str, user_id: str, expires_hours: int = 24) -> str:
        """
        Generate JWT token with tenant context.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            expires_hours: Token expiration in hours

        Returns:
            JWT token
        """
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "iat": datetime.utcnow(),
            "type": "tenant_access"
        }

        # Use a simple secret - in production, use proper key management
        secret = f"tenant_secret_{tenant_id}"
        token = jwt.encode(payload, secret, algorithm="HS256")

        return token

    def validate_tenant_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate tenant token.

        Args:
            token: JWT token

        Returns:
            Decoded payload or None if invalid
        """
        try:
            # Try to decode without verification first to get tenant_id
            header = jwt.get_unverified_header(token)
            payload = jwt.decode(token, options={"verify_signature": False})

            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                return None

            # Verify with tenant-specific secret
            secret = f"tenant_secret_{tenant_id}"
            decoded = jwt.decode(token, secret, algorithms=["HS256"])

            return decoded

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    async def cleanup_inactive_tenants(self, days_inactive: int = 90):
        """
        Clean up inactive tenants.

        Args:
            days_inactive: Days of inactivity before cleanup
        """
        cutoff_date = datetime.now() - timedelta(days=days_inactive)
        inactive_tenants = []

        for tenant_id, usage in self.resource_usage.items():
            last_updated = usage.get("last_updated")
            if last_updated and last_updated < cutoff_date:
                inactive_tenants.append(tenant_id)

        for tenant_id in inactive_tenants:
            logger.info(f"Cleaning up inactive tenant: {tenant_id}")
            # In production, this would archive data and remove tenant
            # For now, just mark as inactive
            if tenant_id in self.tenants:
                self.tenants[tenant_id].status = "inactive"

    def export_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """Export tenant configuration for backup/migration."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}

        return {
            "tenant": {
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "domain": tenant.domain,
                "status": tenant.status,
                "settings": tenant.settings,
                "resource_limits": tenant.resource_limits,
                "features": list(tenant.features),
                "created_at": tenant.created_at.isoformat() if tenant.created_at else None
            },
            "users": list(self.tenant_users.get(tenant_id, [])),
            "resource_usage": self.resource_usage.get(tenant_id, {}),
            "exported_at": datetime.now().isoformat()
        }

    def import_tenant_config(self, config: Dict[str, Any]) -> bool:
        """
        Import tenant configuration.

        Args:
            config: Exported tenant configuration

        Returns:
            Success status
        """
        try:
            tenant_data = config["tenant"]
            tenant_id = tenant_data["tenant_id"]

            tenant = Tenant(
                tenant_id=tenant_id,
                name=tenant_data["name"],
                domain=tenant_data["domain"],
                status=tenant_data.get("status", "active"),
                settings=tenant_data.get("settings", {}),
                resource_limits=tenant_data.get("resource_limits", {}),
                features=set(tenant_data.get("features", []))
            )

            if tenant_data.get("created_at"):
                tenant.created_at = datetime.fromisoformat(tenant_data["created_at"])

            self.tenants[tenant_id] = tenant
            self.tenant_users[tenant_id] = set(config.get("users", []))
            self.resource_usage[tenant_id] = config.get("resource_usage", {})

            # Update user mappings
            for user_id in self.tenant_users[tenant_id]:
                self.user_tenants[user_id] = tenant_id

            logger.info(f"Imported tenant configuration: {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to import tenant config: {e}")
            return False


# Global tenant manager instance
tenant_manager = TenantManager()


async def get_current_tenant(user_id: str) -> Optional[Tenant]:
    """Get current tenant for user."""
    return tenant_manager.get_tenant_for_user(user_id)


async def check_tenant_limits(tenant_id: str, resource: str, amount: int = 1) -> bool:
    """Check if tenant is within resource limits."""
    return await tenant_manager.check_resource_limits(tenant_id, resource, amount)


async def update_tenant_usage(tenant_id: str, resource: str, amount: float):
    """Update tenant resource usage."""
    await tenant_manager.update_resource_usage(tenant_id, resource, amount)
