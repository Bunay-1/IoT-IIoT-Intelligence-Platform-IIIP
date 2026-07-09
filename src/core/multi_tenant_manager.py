"""
Multi-Tenant Manager Module

This module implements multi-tenancy capabilities for the IoT IIoT Platform,
enabling secure isolation between different customers/organizations while
sharing the same infrastructure.
"""

import asyncio
import hashlib
import logging
import time
from typing import Any, Dict, List, Optional, Set, Union

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class MultiTenantError(Exception):
    """Base exception for multi-tenant errors."""
    pass


class TenantNotFoundError(MultiTenantError):
    """Raised when tenant is not found."""
    pass


class TenantLimitExceededError(MultiTenantError):
    """Raised when tenant limits are exceeded."""
    pass


class ResourceQuotaError(MultiTenantError):
    """Raised when resource quotas are exceeded."""
    pass


class MultiTenantManager:
    """
    Multi-Tenant Manager for secure tenant isolation and resource management.

    Provides comprehensive multi-tenancy features including:
    - Tenant isolation and security
    - Resource quotas and limits
    - Usage tracking and billing
    - Tenant lifecycle management
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Multi-Tenant Manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.logger = get_logger(__name__)

        # Tenant storage
        self.tenants: Dict[str, Dict[str, Any]] = {}
        self.tenant_resources: Dict[str, Dict[str, Any]] = {}
        self.tenant_usage: Dict[str, Dict[str, Any]] = {}

        # Resource pools
        self.resource_pools: Dict[str, Dict[str, Any]] = {}

        # Security and access control
        self.tenant_secrets: Dict[str, str] = {}
        self.access_tokens: Dict[str, Dict[str, Any]] = {}

        # Billing and metering
        self.usage_metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.billing_cycles: Dict[str, Dict[str, Any]] = {}

        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        self.logger.info("Multi-Tenant Manager initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "max_tenants": 1000,
            "default_tenant_quota": {
                "machines": 50,
                "users": 100,
                "api_calls_per_hour": 10000,
                "storage_gb": 100,
                "bandwidth_gb_per_month": 500
            },
            "isolation_level": "full",  # full, partial, none
            "billing_cycle_days": 30,
            "monitoring_interval": 60,  # seconds
            "cleanup_interval": 3600,  # 1 hour
            "token_expiry_hours": 24,
            "rate_limiting_enabled": True,
            "audit_logging_enabled": True
        }

    async def create_tenant(
        self,
        tenant_id: str,
        tenant_config: Dict[str, Any],
        admin_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new tenant.

        Args:
            tenant_id: Unique tenant identifier
            tenant_config: Tenant configuration
            admin_user: Administrator user details

        Returns:
            Tenant creation result
        """
        try:
            # Validate tenant ID
            if not self._validate_tenant_id(tenant_id):
                raise ValueError("Invalid tenant ID format")

            # Check tenant limits
            if len(self.tenants) >= self.config["max_tenants"]:
                raise TenantLimitExceededError("Maximum number of tenants reached")

            # Check if tenant already exists
            if tenant_id in self.tenants:
                raise ValueError(f"Tenant {tenant_id} already exists")

            self.logger.info(f"Creating tenant {tenant_id}")

            # Create tenant record
            tenant = {
                "tenant_id": tenant_id,
                "name": tenant_config.get("name", tenant_id),
                "description": tenant_config.get("description", ""),
                "status": "active",
                "created_at": time.time(),
                "updated_at": time.time(),
                "config": tenant_config,
                "admin_user": admin_user,
                "isolation_level": tenant_config.get("isolation_level", self.config["isolation_level"]),
                "features": tenant_config.get("features", []),
                "metadata": tenant_config.get("metadata", {})
            }

            # Set up quotas
            quotas = tenant_config.get("quotas", self.config["default_tenant_quota"].copy())
            tenant["quotas"] = quotas

            # Initialize resources
            self.tenant_resources[tenant_id] = {
                "allocated": {},
                "used": {},
                "limits": quotas.copy()
            }

            # Initialize usage tracking
            self.tenant_usage[tenant_id] = {
                "current_cycle_start": time.time(),
                "metrics": {},
                "costs": {}
            }

            # Generate tenant secret
            tenant_secret = self._generate_tenant_secret(tenant_id)
            self.tenant_secrets[tenant_id] = tenant_secret

            # Store tenant
            self.tenants[tenant_id] = tenant

            # Initialize billing cycle
            await self._initialize_billing_cycle(tenant_id)

            # Set up tenant isolation
            await self._setup_tenant_isolation(tenant_id, tenant["isolation_level"])

            self.logger.info(f"Tenant {tenant_id} created successfully")

            return {
                "tenant_id": tenant_id,
                "status": "created",
                "tenant_secret": tenant_secret,
                "admin_credentials": await self._create_admin_credentials(tenant_id, admin_user)
            }

        except Exception as e:
            self.logger.error(f"Failed to create tenant {tenant_id}: {e}")
            raise MultiTenantError(f"Failed to create tenant: {e}") from e

    def _validate_tenant_id(self, tenant_id: str) -> bool:
        """Validate tenant ID format."""
        # Tenant ID should be alphanumeric with hyphens/underscores, 3-50 chars
        import re
        pattern = r'^[a-zA-Z0-9_-]{3,50}$'
        return bool(re.match(pattern, tenant_id))

    def _generate_tenant_secret(self, tenant_id: str) -> str:
        """Generate a secure tenant secret."""
        import secrets
        import string

        # Generate random secret
        alphabet = string.ascii_letters + string.digits + string.punctuation
        secret = ''.join(secrets.choice(alphabet) for _ in range(64))

        # Add tenant-specific hash for verification
        tenant_hash = hashlib.sha256(f"{tenant_id}:{secret}".encode()).hexdigest()[:16]
        return f"{tenant_hash}.{secret}"

    async def _create_admin_credentials(
        self,
        tenant_id: str,
        admin_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create administrator credentials for the tenant."""
        # This would integrate with the authentication system
        # For now, return placeholder credentials
        return {
            "username": admin_user.get("email", f"admin@{tenant_id}"),
            "temporary_password": "TempPass123!",  # Would be generated securely
            "login_url": f"https://platform.com/tenant/{tenant_id}/login"
        }

    async def _initialize_billing_cycle(self, tenant_id: str) -> None:
        """Initialize billing cycle for tenant."""
        self.billing_cycles[tenant_id] = {
            "start_date": time.time(),
            "end_date": time.time() + (self.config["billing_cycle_days"] * 24 * 3600),
            "status": "active",
            "usage_summary": {},
            "costs": {}
        }

    async def _setup_tenant_isolation(self, tenant_id: str, isolation_level: str) -> None:
        """Set up tenant isolation based on level."""
        if isolation_level == "full":
            # Create separate database schema, namespaces, etc.
            await self._create_isolated_resources(tenant_id)
        elif isolation_level == "partial":
            # Shared resources with tenant-specific access control
            await self._setup_shared_resources_with_acl(tenant_id)
        # "none" would be no isolation (not recommended for production)

    async def _create_isolated_resources(self, tenant_id: str) -> None:
        """Create fully isolated resources for tenant."""
        # This would create separate database schemas, Kubernetes namespaces, etc.
        # Placeholder for actual implementation
        self.logger.info(f"Created isolated resources for tenant {tenant_id}")

    async def _setup_shared_resources_with_acl(self, tenant_id: str) -> None:
        """Set up shared resources with access control."""
        # This would configure ACLs, row-level security, etc.
        # Placeholder for actual implementation
        self.logger.info(f"Configured shared resources with ACL for tenant {tenant_id}")

    async def authenticate_tenant(self, tenant_secret: str) -> Optional[str]:
        """
        Authenticate tenant using secret.

        Args:
            tenant_secret: Tenant secret

        Returns:
            Tenant ID if authenticated, None otherwise
        """
        try:
            # Extract tenant hash from secret
            if '.' not in tenant_secret:
                return None

            tenant_hash, _ = tenant_secret.split('.', 1)

            # Find tenant by hash
            for tenant_id, stored_secret in self.tenant_secrets.items():
                stored_hash, _ = stored_secret.split('.', 1)
                if stored_hash == tenant_hash:
                    # Verify full secret
                    if stored_secret == tenant_secret:
                        return tenant_id

            return None

        except Exception as e:
            self.logger.error(f"Tenant authentication failed: {e}")
            return None

    async def generate_access_token(
        self,
        tenant_id: str,
        user_id: str,
        permissions: List[str],
        expiry_hours: Optional[int] = None
    ) -> str:
        """
        Generate access token for tenant user.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier within tenant
            permissions: List of permissions
            expiry_hours: Token expiry in hours

        Returns:
            Access token
        """
        try:
            if tenant_id not in self.tenants:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            expiry = expiry_hours or self.config["token_expiry_hours"]
            token_id = f"{tenant_id}.{user_id}.{int(time.time())}"

            token_data = {
                "token_id": token_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "permissions": permissions,
                "issued_at": time.time(),
                "expires_at": time.time() + (expiry * 3600),
                "status": "active"
            }

            self.access_tokens[token_id] = token_data

            # Return token (in practice, this would be signed)
            return token_id

        except Exception as e:
            self.logger.error(f"Failed to generate access token for {tenant_id}:{user_id}: {e}")
            raise MultiTenantError(f"Token generation failed: {e}") from e

    async def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate access token.

        Args:
            token: Access token

        Returns:
            Token data if valid, None otherwise
        """
        try:
            if token not in self.access_tokens:
                return None

            token_data = self.access_tokens[token]

            # Check expiry
            if time.time() > token_data["expires_at"]:
                token_data["status"] = "expired"
                return None

            # Check if tenant is active
            tenant_id = token_data["tenant_id"]
            if tenant_id not in self.tenants or self.tenants[tenant_id]["status"] != "active":
                return None

            return token_data

        except Exception as e:
            self.logger.error(f"Token validation failed: {e}")
            return None

    async def check_resource_quota(
        self,
        tenant_id: str,
        resource_type: str,
        requested_amount: int = 1
    ) -> bool:
        """
        Check if tenant can allocate requested resource amount.

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            requested_amount: Amount requested

        Returns:
            True if quota allows, False otherwise
        """
        try:
            if tenant_id not in self.tenant_resources:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            resources = self.tenant_resources[tenant_id]
            current_used = resources["used"].get(resource_type, 0)
            limit = resources["limits"].get(resource_type, 0)

            if current_used + requested_amount > limit:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Resource quota check failed for {tenant_id}: {e}")
            return False

    async def allocate_resource(
        self,
        tenant_id: str,
        resource_type: str,
        amount: int = 1
    ) -> bool:
        """
        Allocate resource to tenant.

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            amount: Amount to allocate

        Returns:
            True if allocated successfully
        """
        try:
            # Check quota first
            if not await self.check_resource_quota(tenant_id, resource_type, amount):
                raise ResourceQuotaError(f"Resource quota exceeded for {resource_type}")

            resources = self.tenant_resources[tenant_id]
            resources["used"][resource_type] = resources["used"].get(resource_type, 0) + amount
            resources["allocated"][resource_type] = resources["allocated"].get(resource_type, 0) + amount

            # Record usage for billing
            await self._record_usage(tenant_id, resource_type, amount)

            self.logger.debug(f"Allocated {amount} {resource_type} to tenant {tenant_id}")
            return True

        except Exception as e:
            self.logger.error(f"Resource allocation failed for {tenant_id}: {e}")
            return False

    async def deallocate_resource(
        self,
        tenant_id: str,
        resource_type: str,
        amount: int = 1
    ) -> bool:
        """
        Deallocate resource from tenant.

        Args:
            tenant_id: Tenant identifier
            resource_type: Type of resource
            amount: Amount to deallocate

        Returns:
            True if deallocated successfully
        """
        try:
            if tenant_id not in self.tenant_resources:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            resources = self.tenant_resources[tenant_id]
            current_used = resources["used"].get(resource_type, 0)

            if current_used < amount:
                self.logger.warning(f"Attempted to deallocate more {resource_type} than allocated for {tenant_id}")
                amount = current_used

            resources["used"][resource_type] = current_used - amount

            self.logger.debug(f"Deallocated {amount} {resource_type} from tenant {tenant_id}")
            return True

        except Exception as e:
            self.logger.error(f"Resource deallocation failed for {tenant_id}: {e}")
            return False

    async def _record_usage(
        self,
        tenant_id: str,
        resource_type: str,
        amount: int
    ) -> None:
        """Record resource usage for billing."""
        try:
            if tenant_id not in self.usage_metrics:
                self.usage_metrics[tenant_id] = []

            usage_record = {
                "timestamp": time.time(),
                "resource_type": resource_type,
                "amount": amount,
                "cost": await self._calculate_cost(tenant_id, resource_type, amount)
            }

            self.usage_metrics[tenant_id].append(usage_record)

            # Update billing cycle
            if tenant_id in self.billing_cycles:
                cycle = self.billing_cycles[tenant_id]
                cycle["usage_summary"][resource_type] = cycle["usage_summary"].get(resource_type, 0) + amount

        except Exception as e:
            self.logger.error(f"Usage recording failed for {tenant_id}: {e}")

    async def _calculate_cost(
        self,
        tenant_id: str,
        resource_type: str,
        amount: int
    ) -> float:
        """Calculate cost for resource usage."""
        # Placeholder pricing - in practice would use configurable pricing
        pricing = {
            "api_calls": 0.001,  # $0.001 per API call
            "storage_gb": 0.10,  # $0.10 per GB per month
            "bandwidth_gb": 0.05,  # $0.05 per GB
            "machines": 50.0,     # $50 per machine per month
            "users": 5.0          # $5 per user per month
        }

        rate = pricing.get(resource_type, 0.0)
        return amount * rate

    async def get_tenant_usage_report(
        self,
        tenant_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get usage report for tenant.

        Args:
            tenant_id: Tenant identifier
            start_time: Start time for report
            end_time: End time for report

        Returns:
            Usage report
        """
        try:
            if tenant_id not in self.tenants:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            # Set time range
            end_time = end_time or time.time()
            start_time = start_time or (end_time - (30 * 24 * 3600))  # Last 30 days

            # Filter usage metrics
            usage_records = self.usage_metrics.get(tenant_id, [])
            filtered_records = [
                record for record in usage_records
                if start_time <= record["timestamp"] <= end_time
            ]

            # Aggregate by resource type
            resource_usage = {}
            total_cost = 0.0

            for record in filtered_records:
                resource_type = record["resource_type"]
                if resource_type not in resource_usage:
                    resource_usage[resource_type] = {
                        "total_amount": 0,
                        "total_cost": 0.0,
                        "records": []
                    }

                resource_usage[resource_type]["total_amount"] += record["amount"]
                resource_usage[resource_type]["total_cost"] += record["cost"]
                resource_usage[resource_type]["records"].append(record)
                total_cost += record["cost"]

            return {
                "tenant_id": tenant_id,
                "period": {
                    "start": start_time,
                    "end": end_time
                },
                "resource_usage": resource_usage,
                "total_cost": total_cost,
                "generated_at": time.time()
            }

        except Exception as e:
            self.logger.error(f"Failed to generate usage report for {tenant_id}: {e}")
            raise MultiTenantError(f"Usage report generation failed: {e}") from e

    async def update_tenant_config(
        self,
        tenant_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update tenant configuration.

        Args:
            tenant_id: Tenant identifier
            updates: Configuration updates

        Returns:
            True if updated successfully
        """
        try:
            if tenant_id not in self.tenants:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            tenant = self.tenants[tenant_id]

            # Update configuration
            for key, value in updates.items():
                if key in ["quotas", "features", "metadata"]:
                    tenant[key].update(value) if isinstance(value, dict) else tenant.__setitem__(key, value)
                else:
                    tenant[key] = value

            tenant["updated_at"] = time.time()

            # Update resource limits if quotas changed
            if "quotas" in updates:
                self.tenant_resources[tenant_id]["limits"].update(updates["quotas"])

            self.logger.info(f"Updated configuration for tenant {tenant_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update tenant {tenant_id} config: {e}")
            return False

    async def suspend_tenant(self, tenant_id: str, reason: str = "") -> bool:
        """
        Suspend tenant access.

        Args:
            tenant_id: Tenant identifier
            reason: Suspension reason

        Returns:
            True if suspended successfully
        """
        try:
            if tenant_id not in self.tenants:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            tenant = self.tenants[tenant_id]
            tenant["status"] = "suspended"
            tenant["suspended_at"] = time.time()
            tenant["suspension_reason"] = reason
            tenant["updated_at"] = time.time()

            # Revoke all active tokens
            tokens_to_revoke = [
                token_id for token_id, token_data in self.access_tokens.items()
                if token_data["tenant_id"] == tenant_id
            ]

            for token_id in tokens_to_revoke:
                self.access_tokens[token_id]["status"] = "revoked"

            self.logger.info(f"Suspended tenant {tenant_id}: {reason}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to suspend tenant {tenant_id}: {e}")
            return False

    async def reactivate_tenant(self, tenant_id: str) -> bool:
        """
        Reactivate suspended tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            True if reactivated successfully
        """
        try:
            if tenant_id not in self.tenants:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")

            tenant = self.tenants[tenant_id]
            if tenant["status"] != "suspended":
                return False

            tenant["status"] = "active"
            tenant["reactivated_at"] = time.time()
            tenant["updated_at"] = time.time()

            # Clear suspension data
            tenant.pop("suspended_at", None)
            tenant.pop("suspension_reason", None)

            self.logger.info(f"Reactivated tenant {tenant_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reactivate tenant {tenant_id}: {e}")
            return False

    def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant information."""
        if tenant_id not in self.tenants:
            return None

        tenant = self.tenants[tenant_id].copy()
        # Remove sensitive data
        tenant.pop("admin_user", None)

        # Add resource usage summary
        if tenant_id in self.tenant_resources:
            tenant["resource_usage"] = self.tenant_resources[tenant_id]

        return tenant

    def list_tenants(
        self,
        status_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List tenants with optional filtering."""
        tenants = []

        for tenant_id, tenant in self.tenants.items():
            if status_filter and tenant["status"] != status_filter:
                continue

            tenant_info = self.get_tenant_info(tenant_id)
            if tenant_info:
                tenants.append(tenant_info)

            if len(tenants) >= limit:
                break

        return tenants

    async def start_monitoring(self) -> None:
        """Start background monitoring tasks."""
        if self.monitoring_task and not self.monitoring_task.done():
            return

        self.monitoring_task = asyncio.create_task(self._monitoring_worker())
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())

        self.logger.info("Started multi-tenant monitoring tasks")

    async def stop_monitoring(self) -> None:
        """Stop background monitoring tasks."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        self.logger.info("Stopped multi-tenant monitoring tasks")

    async def _monitoring_worker(self) -> None:
        """Background monitoring worker."""
        while True:
            try:
                await asyncio.sleep(self.config["monitoring_interval"])

                # Check tenant quotas and usage
                await self._check_tenant_limits()

                # Update billing cycles
                await self._update_billing_cycles()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring worker error: {e}")

    async def _cleanup_worker(self) -> None:
        """Background cleanup worker."""
        while True:
            try:
                await asyncio.sleep(self.config["cleanup_interval"])

                # Clean up expired tokens
                await self._cleanup_expired_tokens()

                # Archive old usage data
                await self._archive_old_usage_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup worker error: {e}")

    async def _check_tenant_limits(self) -> None:
        """Check tenant resource limits and send alerts."""
        for tenant_id, resources in self.tenant_resources.items():
            for resource_type, limit in resources["limits"].items():
                used = resources["used"].get(resource_type, 0)
                usage_ratio = used / limit if limit > 0 else 0

                if usage_ratio > 0.9:  # 90% usage
                    self.logger.warning(
                        f"Tenant {tenant_id} is approaching {resource_type} limit: "
                        f"{used}/{limit} ({usage_ratio:.1%})"
                    )

    async def _update_billing_cycles(self) -> None:
        """Update billing cycles and generate invoices if needed."""
        current_time = time.time()

        for tenant_id, cycle in self.billing_cycles.items():
            if current_time > cycle["end_date"]:
                # Cycle ended, create new one
                await self._finalize_billing_cycle(tenant_id)
                await self._initialize_billing_cycle(tenant_id)

    async def _finalize_billing_cycle(self, tenant_id: str) -> None:
        """Finalize completed billing cycle."""
        # Placeholder for billing finalization logic
        self.logger.info(f"Finalized billing cycle for tenant {tenant_id}")

    async def _cleanup_expired_tokens(self) -> None:
        """Clean up expired access tokens."""
        current_time = time.time()
        expired_tokens = [
            token_id for token_id, token_data in self.access_tokens.items()
            if current_time > token_data["expires_at"]
        ]

        for token_id in expired_tokens:
            del self.access_tokens[token_id]

        if expired_tokens:
            self.logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")

    async def _archive_old_usage_data(self) -> None:
        """Archive old usage data."""
        # Placeholder for data archiving logic
        # In practice, this would move old data to cheaper storage
        pass