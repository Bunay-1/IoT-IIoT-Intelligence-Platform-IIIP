"""
Database Optimization Module for TimescaleDB

This module implements database query optimization, indexing strategies,
and performance monitoring for TimescaleDB in the IoT platform.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import asyncpg
# Local imports to avoid circular dependencies
import logging

class LoggerMixin:
    """Simple logger mixin."""
    @property
    def logger(self):
        return logging.getLogger(self.__class__.__name__)

def monitor_operation(operation_name):
    """Simple decorator for operation monitoring."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class DatabaseOptimizer(LoggerMixin):
    """
    Database optimization and monitoring system for TimescaleDB.

    This class provides comprehensive database performance optimization including:
    - Query optimization and indexing
    - TimescaleDB hypertable management
    - Performance monitoring and alerting
    - Connection pooling optimization
    - Query execution analysis
    """

    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize the database optimizer.

        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
        self.optimization_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}

        self.logger.info("Database Optimizer initialized")

    @monitor_operation("database_optimizer.optimize_queries")
    async def optimize_queries(self) -> Dict[str, Any]:
        """
        Perform comprehensive query optimization.

        Returns:
            Optimization results and recommendations
        """
        try:
            self.logger.info("Starting database query optimization")

            # Analyze slow queries
            slow_queries = await self._analyze_slow_queries()

            # Check missing indexes
            missing_indexes = await self._identify_missing_indexes()

            # Optimize hypertables
            hypertable_optimizations = await self._optimize_hypertables()

            # Update compression policies
            compression_updates = await self._update_compression_policies()

            # Generate optimization report
            optimization_report = {
                "timestamp": datetime.now().isoformat(),
                "slow_queries": slow_queries,
                "missing_indexes": missing_indexes,
                "hypertable_optimizations": hypertable_optimizations,
                "compression_updates": compression_updates,
                "recommendations": self._generate_optimization_recommendations(
                    slow_queries, missing_indexes, hypertable_optimizations
                )
            }

            # Store optimization history
            self.optimization_history.append(optimization_report)

            self.logger.info("Database query optimization completed")
            return optimization_report

        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
            return {"error": str(e)}

    async def _analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analyze slow queries using PostgreSQL statistics."""
        try:
            async with self.pool.acquire() as conn:
                # Get slow queries from pg_stat_statements (if available)
                slow_queries = await conn.fetch("""
                    SELECT
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows,
                        shared_blks_hit,
                        shared_blks_read,
                        temp_blks_written
                    FROM pg_stat_statements
                    WHERE mean_time > 100  -- Queries taking > 100ms on average
                    ORDER BY mean_time DESC
                    LIMIT 20
                """)

                return [dict(row) for row in slow_queries]

        except Exception as e:
            self.logger.warning(f"Slow query analysis failed: {e}")
            return []

    async def _identify_missing_indexes(self) -> List[Dict[str, Any]]:
        """Identify potentially missing indexes."""
        try:
            async with self.pool.acquire() as conn:
                # Check for sequential scans on large tables
                missing_indexes = await conn.fetch("""
                    SELECT
                        schemaname,
                        tablename,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del
                    FROM pg_stat_user_tables
                    WHERE seq_scan > idx_scan * 10  -- Much more sequential than index scans
                    AND n_tup_ins > 1000  -- Tables with significant data
                    ORDER BY seq_scan DESC
                    LIMIT 10
                """)

                return [dict(row) for row in missing_indexes]

        except Exception as e:
            self.logger.warning(f"Missing index identification failed: {e}")
            return []

    async def _optimize_hypertables(self) -> Dict[str, Any]:
        """Optimize TimescaleDB hypertables."""
        try:
            async with self.pool.acquire() as conn:
                # Get hypertable information
                hypertables = await conn.fetch("""
                    SELECT
                        ht.hypertable_name,
                        ht.num_chunks,
                        ht.compression_enabled,
                        ht.num_compressed_chunks,
                        c.chunk_name,
                        c.range_start,
                        c.range_end
                    FROM timescaledb_information.hypertables ht
                    LEFT JOIN timescaledb_information.chunks c
                        ON ht.hypertable_name = c.hypertable_name
                    ORDER BY ht.hypertable_name, c.range_start DESC
                """)

                optimizations = []

                # Analyze each hypertable
                for table_name in set(row['hypertable_name'] for row in hypertables):
                    table_chunks = [row for row in hypertables if row['hypertable_name'] == table_name]

                    # Check chunk count - too many chunks can impact performance
                    if len(table_chunks) > 1000:
                        optimizations.append({
                            "table": table_name,
                            "issue": "too_many_chunks",
                            "recommendation": "Consider increasing chunk_time_interval or dropping old chunks"
                        })

                    # Check compression status
                    compressed_chunks = sum(1 for chunk in table_chunks if chunk['compression_enabled'])
                    if compressed_chunks == 0:
                        optimizations.append({
                            "table": table_name,
                            "issue": "no_compression",
                            "recommendation": "Enable compression for better storage and query performance"
                        })

                return {
                    "hypertables_analyzed": len(set(row['hypertable_name'] for row in hypertables)),
                    "optimizations": optimizations
                }

        except Exception as e:
            self.logger.warning(f"Hypertable optimization analysis failed: {e}")
            return {"error": str(e)}

    async def _update_compression_policies(self) -> Dict[str, Any]:
        """Update compression policies for better performance."""
        try:
            async with self.pool.acquire() as conn:
                # Get current compression policies
                policies = await conn.fetch("""
                    SELECT
                        hypertable_name,
                        policy_name,
                        config
                    FROM timescaledb_information.compression_settings
                """)

                updates = []

                # Analyze and update policies
                for policy in policies:
                    config = policy['config']
                    # Check if compression age is reasonable (e.g., compress after 7 days)
                    compress_after = config.get('compress_after')
                    if compress_after and isinstance(compress_after, str):
                        # Parse interval and check if it's reasonable
                        if '00:00:00' in compress_after:  # Very short interval
                            updates.append({
                                "table": policy['hypertable_name'],
                                "action": "update_compression_age",
                                "recommendation": "Increase compression age for better performance"
                            })

                return {
                    "policies_analyzed": len(policies),
                    "updates_recommended": updates
                }

        except Exception as e:
            self.logger.warning(f"Compression policy update failed: {e}")
            return {"error": str(e)}

    def _generate_optimization_recommendations(
        self,
        slow_queries: List[Dict[str, Any]],
        missing_indexes: List[Dict[str, Any]],
        hypertable_optimizations: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Slow query recommendations
        if slow_queries:
            recommendations.append(f"Found {len(slow_queries)} slow queries - consider query optimization")
            recommendations.append("Review query execution plans and add appropriate indexes")

        # Missing index recommendations
        if missing_indexes:
            recommendations.append(f"Identified {len(missing_indexes)} tables with potential missing indexes")
            recommendations.append("Add indexes on frequently queried columns")

        # Hypertable recommendations
        optimizations = hypertable_optimizations.get("optimizations", [])
        if optimizations:
            recommendations.append(f"Found {len(optimizations)} hypertable optimization opportunities")
            recommendations.append("Review chunk intervals and compression policies")

        # General recommendations
        recommendations.extend([
            "Enable query parallelization for large datasets",
            "Consider partitioning strategy for frequently accessed data",
            "Monitor query performance regularly",
            "Review and optimize connection pool settings"
        ])

        return recommendations

    @monitor_operation("database_optimizer.create_performance_indexes")
    async def create_performance_indexes(self) -> Dict[str, Any]:
        """Create performance indexes on key tables."""
        try:
            async with self.pool.acquire() as conn:
                indexes_created = []

                # Index for predictions table
                try:
                    await conn.execute("""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_machine_timestamp
                        ON predictions (machine_id, timestamp DESC)
                    """)
                    indexes_created.append("idx_predictions_machine_timestamp")
                except Exception as e:
                    self.logger.warning(f"Failed to create predictions index: {e}")

                # Index for alerts table
                try:
                    await conn.execute("""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alerts_machine_timestamp
                        ON alerts (machine_id, timestamp DESC)
                    """)
                    indexes_created.append("idx_alerts_machine_timestamp")
                except Exception as e:
                    self.logger.warning(f"Failed to create alerts index: {e}")

                # Index for users table
                try:
                    await conn.execute("""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username
                        ON users (username)
                    """)
                    indexes_created.append("idx_users_username")
                except Exception as e:
                    self.logger.warning(f"Failed to create users index: {e}")

                return {
                    "indexes_created": indexes_created,
                    "total_indexes": len(indexes_created),
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            self.logger.error(f"Index creation failed: {e}")
            return {"error": str(e)}

    @monitor_operation("database_optimizer.optimize_connection_pool")
    async def optimize_connection_pool(self) -> Dict[str, Any]:
        """Optimize database connection pool settings."""
        try:
            # Get current pool stats
            pool_stats = {
                "min_size": self.pool._minsize,
                "max_size": self.pool._maxsize,
                "size": len(self.pool._holders),
                "used": len([h for h in self.pool._holders if h._con is not None])
            }

            recommendations = []

            # Analyze pool utilization
            utilization = pool_stats["used"] / pool_stats["max_size"] if pool_stats["max_size"] > 0 else 0

            if utilization > 0.9:
                recommendations.append("Connection pool heavily utilized - consider increasing max_size")
            elif utilization < 0.3:
                recommendations.append("Connection pool underutilized - consider reducing max_size")

            # Check for connection leaks
            if pool_stats["used"] == pool_stats["max_size"]:
                recommendations.append("All connections in use - check for connection leaks")

            return {
                "pool_stats": pool_stats,
                "utilization": utilization,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Connection pool optimization failed: {e}")
            return {"error": str(e)}

    @monitor_operation("database_optimizer.monitor_performance")
    async def monitor_performance(self) -> Dict[str, Any]:
        """Monitor database performance metrics."""
        try:
            async with self.pool.acquire() as conn:
                # Get database performance metrics
                db_stats = await conn.fetchrow("""
                    SELECT
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT count(*) FROM pg_stat_activity) as total_connections,
                        (SELECT sum(blks_hit) * 100.0 / (sum(blks_hit) + sum(blks_read)) FROM pg_stat_database WHERE datname = current_database()) as cache_hit_ratio,
                        (SELECT sum(xact_commit) + sum(xact_rollback) FROM pg_stat_database WHERE datname = current_database()) as total_transactions,
                        (SELECT sum(tup_inserted) + sum(tup_updated) + sum(tup_deleted) FROM pg_stat_database WHERE datname = current_database()) as total_row_operations
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)

                # Get TimescaleDB specific metrics
                ts_stats = await conn.fetchrow("""
                    SELECT
                        (SELECT count(*) FROM timescaledb_information.chunks) as total_chunks,
                        (SELECT count(*) FROM timescaledb_information.chunks WHERE is_compressed) as compressed_chunks,
                        (SELECT count(*) FROM timescaledb_information.hypertables) as hypertables_count
                """)

                performance_metrics = {
                    "database_stats": dict(db_stats) if db_stats else {},
                    "timescaledb_stats": dict(ts_stats) if ts_stats else {},
                    "timestamp": datetime.now().isoformat()
                }

                # Store metrics history
                self.performance_metrics[datetime.now().isoformat()] = performance_metrics

                return performance_metrics

        except Exception as e:
            self.logger.error(f"Performance monitoring failed: {e}")
            return {"error": str(e)}

    @monitor_operation("database_optimizer.get_optimization_report")
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive database optimization report."""
        try:
            # Get recent optimization history
            recent_optimizations = self.optimization_history[-5:] if self.optimization_history else []

            # Get recent performance metrics
            recent_metrics = list(self.performance_metrics.items())[-10:] if self.performance_metrics else []

            return {
                "optimization_history": recent_optimizations,
                "performance_metrics": dict(recent_metrics),
                "current_recommendations": self._generate_current_recommendations(),
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Optimization report generation failed: {e}")
            return {"error": str(e)}

    def _generate_current_recommendations(self) -> List[str]:
        """Generate current optimization recommendations."""
        recommendations = [
            "Run EXPLAIN ANALYZE on slow queries to identify bottlenecks",
            "Consider partitioning large tables by time or other criteria",
            "Monitor index usage and remove unused indexes",
            "Review and optimize TimescaleDB chunk intervals",
            "Enable compression on historical data",
            "Set up automated maintenance jobs (VACUUM, REINDEX)",
            "Monitor connection pool utilization",
            "Consider read replicas for heavy read workloads"
        ]

        return recommendations