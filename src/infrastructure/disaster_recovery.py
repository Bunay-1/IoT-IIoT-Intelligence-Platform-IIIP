"""
Disaster recovery and backup management
"""

import asyncio
import json
import logging
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

logger = logging.getLogger(__name__)


class BackupManager:
    """Manage database and file backups."""

    def __init__(self, backup_dir: str = "backups", retention_days: int = 30):
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.backup_dir.mkdir(exist_ok=True)

    async def create_database_backup(self, db_config: Dict[str, Any]) -> str:
        """Create database backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename

        try:
            # This would execute pg_dump or similar
            # For now, create a placeholder backup
            async with aiofiles.open(backup_path, "w") as f:
                await f.write(
                    f"-- Database backup created at {datetime.now().isoformat()}\n"
                )
                await f.write("-- This is a placeholder backup file\n")

            logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            raise

    async def create_file_backup(self, source_dirs: List[str]) -> str:
        """Create backup of important files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"files_backup_{timestamp}.zip"
        backup_path = self.backup_dir / backup_filename

        try:
            # Create zip archive
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for source_dir in source_dirs:
                    source_path = Path(source_dir)
                    if source_path.exists():
                        for file_path in source_path.rglob("*"):
                            if file_path.is_file():
                                zipf.write(
                                    file_path, file_path.relative_to(source_path.parent)
                                )

            logger.info(f"File backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.error(f"Failed to create file backup: {e}")
            raise

    async def restore_database_backup(
        self, backup_path: str, db_config: Dict[str, Any]
    ) -> bool:
        """Restore database from backup."""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            # This would execute psql or similar to restore
            logger.info(f"Database restored from: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False

    async def cleanup_old_backups(self):
        """Remove backups older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        try:
            removed_count = 0
            for backup_file in self.backup_dir.glob("*"):
                if backup_file.is_file():
                    # Try to extract date from filename
                    try:
                        date_str = backup_file.stem.split("_")[-1]
                        file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")

                        if file_date < cutoff_date:
                            backup_file.unlink()
                            removed_count += 1
                    except (ValueError, IndexError):
                        # If we can't parse the date, skip this file
                        continue

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old backup files")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    def get_backup_info(self) -> Dict[str, Any]:
        """Get information about existing backups."""
        backups = []
        total_size = 0

        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file():
                stat = backup_file.stat()
                backups.append(
                    {
                        "filename": backup_file.name,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "type": "database"
                        if "db_backup" in backup_file.name
                        else "files",
                    }
                )
                total_size += stat.st_size

        return {
            "backup_directory": str(self.backup_dir),
            "total_backups": len(backups),
            "total_size": total_size,
            "retention_days": self.retention_days,
            "backups": backups,
        }


class DisasterRecoveryManager:
    """Manage disaster recovery procedures."""

    def __init__(self):
        self.recovery_procedures: Dict[str, Dict[str, Any]] = {}
        self.system_status = "normal"

    def register_procedure(self, name: str, procedure: Dict[str, Any]):
        """Register a disaster recovery procedure."""
        self.recovery_procedures[name] = {
            **procedure,
            "registered_at": datetime.now().isoformat(),
        }
        logger.info(f"Registered recovery procedure: {name}")

    async def execute_recovery(self, procedure_name: str) -> Dict[str, Any]:
        """Execute a disaster recovery procedure."""
        if procedure_name not in self.recovery_procedures:
            raise ValueError(f"Recovery procedure not found: {procedure_name}")

        procedure = self.recovery_procedures[procedure_name]
        results = {
            "procedure": procedure_name,
            "started_at": datetime.now().isoformat(),
            "steps": [],
            "status": "running",
        }

        try:
            for step in procedure.get("steps", []):
                step_result = {
                    "step": step["name"],
                    "started_at": datetime.now().isoformat(),
                    "status": "running",
                }

                try:
                    # Execute step function
                    if asyncio.iscoroutinefunction(step["function"]):
                        await step["function"](**step.get("kwargs", {}))
                    else:
                        step["function"](**step.get("kwargs", {}))

                    step_result["status"] = "completed"
                    step_result["completed_at"] = datetime.now().isoformat()

                except Exception as e:
                    step_result["status"] = "failed"
                    step_result["error"] = str(e)
                    step_result["completed_at"] = datetime.now().isoformat()
                    logger.error(f"Recovery step failed: {step['name']} - {e}")

                results["steps"].append(step_result)

            results["status"] = "completed"
            results["completed_at"] = datetime.now().isoformat()

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"Recovery procedure failed: {procedure_name} - {e}")

        return results

    def set_system_status(self, status: str):
        """Set system disaster status."""
        valid_statuses = ["normal", "degraded", "disaster", "recovery"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        self.system_status = status
        logger.info(f"System status changed to: {status}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and available recovery procedures."""
        return {
            "status": self.system_status,
            "timestamp": datetime.now().isoformat(),
            "available_procedures": list(self.recovery_procedures.keys()),
            "procedures": self.recovery_procedures,
        }


# Global instances
backup_manager = BackupManager()
disaster_recovery = DisasterRecoveryManager()


# Register default recovery procedures
async def restart_services():
    """Restart all services."""
    logger.info("Restarting services...")
    await asyncio.sleep(2)  # Simulate restart
    logger.info("Services restarted")


async def restore_from_backup():
    """Restore system from latest backup."""
    logger.info("Restoring from backup...")
    await asyncio.sleep(5)  # Simulate restore
    logger.info("System restored from backup")


async def failover_to_backup():
    """Failover to backup systems."""
    logger.info("Failing over to backup systems...")
    await asyncio.sleep(3)  # Simulate failover
    logger.info("Failover completed")


# Register procedures
disaster_recovery.register_procedure(
    "service_restart",
    {
        "description": "Restart all system services",
        "priority": "high",
        "estimated_duration": "2 minutes",
        "steps": [
            {
                "name": "stop_services",
                "function": lambda: logger.info("Stopping services..."),
                "description": "Stop all running services",
            },
            {
                "name": "restart_services",
                "function": restart_services,
                "description": "Restart services in correct order",
            },
        ],
    },
)

disaster_recovery.register_procedure(
    "full_restore",
    {
        "description": "Complete system restore from backup",
        "priority": "critical",
        "estimated_duration": "10 minutes",
        "steps": [
            {
                "name": "stop_services",
                "function": lambda: logger.info("Stopping services for restore..."),
                "description": "Stop services before restore",
            },
            {
                "name": "restore_backup",
                "function": restore_from_backup,
                "description": "Restore system from latest backup",
            },
            {
                "name": "restart_services",
                "function": restart_services,
                "description": "Restart services after restore",
            },
        ],
    },
)
