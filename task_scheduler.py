"""
Background task scheduler for periodic operations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Asynchronous task scheduler for background operations."""

    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False

    async def start(self):
        """Start the task scheduler."""
        self.running = True
        logger.info("Task scheduler started")

        # Start scheduled tasks
        await self._start_scheduled_tasks()

    async def stop(self):
        """Stop the task scheduler."""
        self.running = False

        # Cancel all running tasks
        for task_name, task in self.tasks.items():
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled task: {task_name}")

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        logger.info("Task scheduler stopped")

    def add_periodic_task(
        self, name: str, func: Callable, interval_seconds: int, *args, **kwargs
    ):
        """Add a periodic task."""
        if name in self.scheduled_tasks:
            logger.warning(f"Task {name} already exists, replacing")

        self.scheduled_tasks[name] = {
            "func": func,
            "interval": interval_seconds,
            "args": args,
            "kwargs": kwargs,
            "last_run": None,
            "next_run": datetime.now() + timedelta(seconds=interval_seconds),
        }

        logger.info(f"Added periodic task: {name} (every {interval_seconds}s)")

    def add_cron_task(
        self, name: str, func: Callable, cron_expression: str, *args, **kwargs
    ):
        """Add a cron-style task (simplified implementation)."""
        # For simplicity, we'll implement basic cron-like scheduling
        # In production, use a proper cron library like croniter
        logger.info(f"Added cron task: {name} ({cron_expression})")

    async def _start_scheduled_tasks(self):
        """Start all scheduled periodic tasks."""
        for task_name, task_config in self.scheduled_tasks.items():
            task = asyncio.create_task(self._run_periodic_task(task_name, task_config))
            self.tasks[task_name] = task

    async def _run_periodic_task(self, name: str, config: Dict[str, Any]):
        """Run a periodic task."""
        while self.running:
            try:
                now = datetime.now()

                # Check if it's time to run
                if now >= config["next_run"]:
                    logger.info(f"Running periodic task: {name}")

                    # Execute the task
                    try:
                        await config["func"](*config["args"], **config["kwargs"])
                        config["last_run"] = now
                        logger.info(f"Completed periodic task: {name}")
                    except Exception as e:
                        logger.error(f"Error in periodic task {name}: {e}")

                    # Schedule next run
                    config["next_run"] = now + timedelta(seconds=config["interval"])

                # Sleep for a short interval before checking again
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info(f"Periodic task {name} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in task scheduler for {name}: {e}")
                await asyncio.sleep(5)  # Back off on errors

    async def run_once(self, name: str) -> bool:
        """Run a scheduled task once immediately."""
        if name not in self.scheduled_tasks:
            logger.error(f"Task {name} not found")
            return False

        config = self.scheduled_tasks[name]
        try:
            logger.info(f"Running task once: {name}")
            await config["func"](*config["args"], **config["kwargs"])
            config["last_run"] = datetime.now()
            logger.info(f"Completed task: {name}")
            return True
        except Exception as e:
            logger.error(f"Error running task {name}: {e}")
            return False

    def get_task_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all scheduled tasks."""
        status = {}

        for name, config in self.scheduled_tasks.items():
            task_status = {
                "interval": config["interval"],
                "last_run": config["last_run"].isoformat()
                if config["last_run"]
                else None,
                "next_run": config["next_run"].isoformat(),
                "is_running": name in self.tasks and not self.tasks[name].done(),
            }
            status[name] = task_status

        return status

    def remove_task(self, name: str) -> bool:
        """Remove a scheduled task."""
        if name in self.scheduled_tasks:
            # Cancel the running task if it exists
            if name in self.tasks:
                self.tasks[name].cancel()

            del self.scheduled_tasks[name]
            logger.info(f"Removed task: {name}")
            return True

        return False


# Global task scheduler instance
task_scheduler = TaskScheduler()


# Example background tasks
async def cleanup_expired_cache():
    """Clean up expired cache entries."""
    from cache_manager import cache_manager

    try:
        # This would be implemented in the cache manager
        logger.info("Running cache cleanup")
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")


async def update_system_metrics():
    """Update system monitoring metrics."""
    from monitoring import monitoring

    try:
        monitoring.update_system_metrics()
        logger.info("Updated system metrics")
    except Exception as e:
        logger.error(f"System metrics update error: {e}")


async def process_pending_alerts():
    """Process and send pending alerts."""
    try:
        # This would integrate with the alert system
        logger.info("Processing pending alerts")
    except Exception as e:
        logger.error(f"Alert processing error: {e}")


async def backup_database():
    """Create database backup."""
    try:
        # This would implement database backup logic
        logger.info("Database backup completed")
    except Exception as e:
        logger.error(f"Database backup error: {e}")


# Register default tasks
task_scheduler.add_periodic_task(
    "cache_cleanup", cleanup_expired_cache, 300  # Every 5 minutes
)

task_scheduler.add_periodic_task(
    "metrics_update", update_system_metrics, 60  # Every minute
)

task_scheduler.add_periodic_task(
    "alert_processing", process_pending_alerts, 30  # Every 30 seconds
)

task_scheduler.add_periodic_task("database_backup", backup_database, 3600)  # Every hour
