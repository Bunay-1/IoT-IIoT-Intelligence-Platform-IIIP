"""
CI/CD Pipeline Automation Module

This module implements CI/CD pipeline automation for the IoT IIoT platform,
providing automated testing, deployment, monitoring, and rollback capabilities.
"""

import asyncio
import hashlib
import json
import os
import subprocess
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class DeploymentEnvironment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class PipelineTrigger(Enum):
    """Pipeline trigger types."""
    MANUAL = "manual"
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    DEPENDENCY = "dependency"


class TestType(Enum):
    """Test types."""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    SMOKE = "smoke"


class CICDAutomation:
    """
    CI/CD Pipeline Automation system.

    Features:
    - Automated pipeline execution
    - Multi-environment deployments
    - Comprehensive testing
    - Rollback capabilities
    - Monitoring and alerting
    - Security scanning
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Pipeline configurations
        self.pipelines: Dict[str, Dict] = {}

        # Active pipeline executions
        self.active_executions: Dict[str, Dict] = {}

        # Pipeline history
        self.pipeline_history: Dict[str, List[Dict]] = defaultdict(list)

        # Deployment history
        self.deployment_history: Dict[str, List[Dict]] = defaultdict(list)

        # Test results
        self.test_results: Dict[str, Dict] = defaultdict(dict)

        # Rollback configurations
        self.rollback_configs: Dict[str, Dict] = {}

        # Monitoring and metrics
        self.pipeline_metrics: Dict[str, Dict] = defaultdict(dict)

        # Build artifacts
        self.build_artifacts: Dict[str, Dict] = {}

        self.logger = get_logger(__name__)
        self.logger.info("CI/CD Automation initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "max_concurrent_pipelines": 5,
            "pipeline_timeout": 3600,  # 1 hour
            "artifact_retention_days": 30,
            "enable_rollback": True,
            "enable_security_scanning": True,
            "enable_performance_testing": True,
            "notification_channels": ["email", "slack", "webhook"],
            "supported_environments": ["development", "staging", "production"],
            "test_parallelization": True,
            "cache_dependencies": True,
        }

    def create_pipeline(
        self,
        pipeline_name: str,
        pipeline_config: Dict,
        stages: List[Dict]
    ) -> bool:
        """
        Create CI/CD pipeline.

        Args:
            pipeline_name: Pipeline name
            pipeline_config: Pipeline configuration
            stages: Pipeline stages

        Returns:
            Pipeline creation success
        """
        try:
            pipeline = {
                "name": pipeline_name,
                "config": pipeline_config,
                "stages": stages,
                "created_at": datetime.now(),
                "version": "1.0",
                "enabled": True,
                "triggers": pipeline_config.get("triggers", []),
                "environments": pipeline_config.get("environments", ["development"]),
                "required_approvals": pipeline_config.get("required_approvals", []),
                "notifications": pipeline_config.get("notifications", {}),
                "metrics": {
                    "total_runs": 0,
                    "success_rate": 0.0,
                    "avg_duration": 0.0,
                    "last_run": None
                }
            }

            self.pipelines[pipeline_name] = pipeline

            # Create rollback configuration
            if self.config["enable_rollback"]:
                self._create_rollback_config(pipeline_name, pipeline_config)

            self.logger.info(f"Created pipeline: {pipeline_name} with {len(stages)} stages")
            return True

        except Exception as e:
            self.logger.error(f"Pipeline creation failed: {e}")
            return False

    def _create_rollback_config(self, pipeline_name: str, pipeline_config: Dict):
        """Create rollback configuration for pipeline."""
        rollback_config = {
            "pipeline": pipeline_name,
            "strategy": pipeline_config.get("rollback_strategy", "immediate"),
            "backup_versions": pipeline_config.get("backup_versions", 3),
            "auto_rollback_on_failure": pipeline_config.get("auto_rollback", False),
            "rollback_timeout": pipeline_config.get("rollback_timeout", 1800),
            "created_at": datetime.now()
        }

        self.rollback_configs[pipeline_name] = rollback_config

    async def trigger_pipeline(
        self,
        pipeline_name: str,
        trigger_type: PipelineTrigger,
        trigger_data: Optional[Dict] = None,
        environment: Optional[DeploymentEnvironment] = None
    ) -> Optional[str]:
        """
        Trigger pipeline execution.

        Args:
            pipeline_name: Pipeline name
            trigger_type: Trigger type
            trigger_data: Trigger data
            environment: Target environment

        Returns:
            Execution ID
        """
        try:
            if pipeline_name not in self.pipelines:
                raise ValueError(f"Pipeline {pipeline_name} not found")

            pipeline = self.pipelines[pipeline_name]

            # Check if pipeline is enabled
            if not pipeline.get("enabled", True):
                self.logger.warning(f"Pipeline {pipeline_name} is disabled")
                return None

            # Check concurrent pipeline limit
            if len(self.active_executions) >= self.config["max_concurrent_pipelines"]:
                self.logger.warning("Maximum concurrent pipelines reached")
                return None

            # Generate execution ID
            execution_id = f"{pipeline_name}_{int(time.time() * 1000)}"

            # Create execution context
            execution = {
                "execution_id": execution_id,
                "pipeline_name": pipeline_name,
                "trigger_type": trigger_type.value,
                "trigger_data": trigger_data or {},
                "environment": environment.value if environment else "development",
                "status": PipelineStatus.PENDING.value,
                "stages": [],
                "current_stage": None,
                "start_time": None,
                "end_time": None,
                "duration": None,
                "artifacts": {},
                "logs": [],
                "metrics": {},
                "approvals": [],
                "created_at": datetime.now()
            }

            # Initialize stages
            for stage_config in pipeline["stages"]:
                stage = {
                    "name": stage_config["name"],
                    "type": stage_config["type"],
                    "status": PipelineStatus.PENDING.value,
                    "start_time": None,
                    "end_time": None,
                    "duration": None,
                    "logs": [],
                    "artifacts": {},
                    "config": stage_config
                }
                execution["stages"].append(stage)

            self.active_executions[execution_id] = execution

            # Start pipeline execution
            asyncio.create_task(self._execute_pipeline(execution_id))

            self.logger.info(f"Triggered pipeline execution: {execution_id}")
            return execution_id

        except Exception as e:
            self.logger.error(f"Pipeline trigger failed: {e}")
            return None

    async def _execute_pipeline(self, execution_id: str):
        """Execute pipeline stages."""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return

        try:
            execution["status"] = PipelineStatus.RUNNING.value
            execution["start_time"] = datetime.now()

            pipeline = self.pipelines[execution["pipeline_name"]]
            stages = execution["stages"]

            # Execute stages sequentially
            for i, stage in enumerate(stages):
                execution["current_stage"] = stage["name"]
                stage["status"] = PipelineStatus.RUNNING.value
                stage["start_time"] = datetime.now()

                try:
                    # Execute stage
                    success = await self._execute_stage(execution, stage, pipeline)

                    stage["end_time"] = datetime.now()
                    stage["duration"] = (stage["end_time"] - stage["start_time"]).total_seconds()

                    if success:
                        stage["status"] = PipelineStatus.SUCCESS.value
                        self.logger.info(f"Stage {stage['name']} completed successfully")
                    else:
                        stage["status"] = PipelineStatus.FAILED.value
                        execution["status"] = PipelineStatus.FAILED.value
                        self.logger.error(f"Stage {stage['name']} failed")

                        # Attempt rollback if configured
                        if self.config["enable_rollback"]:
                            await self._rollback_pipeline(execution_id)

                        break

                except Exception as e:
                    stage["status"] = PipelineStatus.FAILED.value
                    stage["error"] = str(e)
                    execution["status"] = PipelineStatus.FAILED.value
                    self.logger.error(f"Stage {stage['name']} error: {e}")
                    break

            # Pipeline completion
            execution["end_time"] = datetime.now()
            execution["duration"] = (execution["end_time"] - execution["start_time"]).total_seconds()

            if execution["status"] == PipelineStatus.RUNNING.value:
                execution["status"] = PipelineStatus.SUCCESS.value

            # Store execution history
            self._store_execution_history(execution)

            # Send notifications
            await self._send_pipeline_notifications(execution)

            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

            self.logger.info(f"Pipeline execution {execution_id} completed with status: {execution['status']}")

        except Exception as e:
            execution["status"] = PipelineStatus.FAILED.value
            execution["error"] = str(e)
            self.logger.error(f"Pipeline execution {execution_id} failed: {e}")

    async def _execute_stage(self, execution: Dict, stage: Dict, pipeline: Dict) -> bool:
        """Execute pipeline stage."""
        stage_type = stage["config"]["type"]
        stage_config = stage["config"]

        try:
            if stage_type == "build":
                return await self._execute_build_stage(execution, stage, stage_config)
            elif stage_type == "test":
                return await self._execute_test_stage(execution, stage, stage_config)
            elif stage_type == "security_scan":
                return await self._execute_security_scan_stage(execution, stage, stage_config)
            elif stage_type == "deploy":
                return await self._execute_deploy_stage(execution, stage, stage_config)
            elif stage_type == "approval":
                return await self._execute_approval_stage(execution, stage, stage_config)
            elif stage_type == "notification":
                return await self._execute_notification_stage(execution, stage, stage_config)
            else:
                self.logger.warning(f"Unknown stage type: {stage_type}")
                return False

        except Exception as e:
            self.logger.error(f"Stage execution failed: {e}")
            return False

    async def _execute_build_stage(self, execution: Dict, stage: Dict, config: Dict) -> bool:
        """Execute build stage."""
        try:
            # Simulate build process
            build_commands = config.get("commands", ["echo 'Building...'"])

            for command in build_commands:
                # Execute build command
                result = await self._run_command(command, cwd=config.get("working_directory", "."))
                if result["returncode"] != 0:
                    stage["logs"].append(f"Build failed: {result['stderr']}")
                    return False

                stage["logs"].append(result["stdout"])

            # Create build artifacts
            artifact_path = f"artifacts/{execution['execution_id']}/build"
            os.makedirs(artifact_path, exist_ok=True)

            # Store artifact info
            stage["artifacts"]["build_output"] = {
                "path": artifact_path,
                "created_at": datetime.now(),
                "size": self._calculate_directory_size(artifact_path)
            }

            return True

        except Exception as e:
            stage["logs"].append(f"Build error: {e}")
            return False

    async def _execute_test_stage(self, execution: Dict, stage: Dict, config: Dict) -> bool:
        """Execute test stage."""
        try:
            test_types = config.get("test_types", ["unit"])
            test_results = {}

            for test_type in test_types:
                # Run tests
                result = await self._run_tests(test_type, config)

                test_results[test_type] = {
                    "passed": result.get("passed", 0),
                    "failed": result.get("failed", 0),
                    "skipped": result.get("skipped", 0),
                    "duration": result.get("duration", 0),
                    "coverage": result.get("coverage", 0.0)
                }

                if result.get("failed", 0) > 0:
                    stage["logs"].append(f"Tests failed for {test_type}")
                    return False

            # Store test results
            execution["test_results"] = test_results
            stage["artifacts"]["test_results"] = test_results

            # Check coverage threshold
            min_coverage = config.get("min_coverage", 80.0)
            for test_result in test_results.values():
                if test_result.get("coverage", 0) < min_coverage:
                    stage["logs"].append(f"Coverage below threshold: {test_result['coverage']}% < {min_coverage}%")
                    return False

            return True

        except Exception as e:
            stage["logs"].append(f"Test error: {e}")
            return False

    async def _execute_security_scan_stage(self, execution: Dict, stage: Dict, config: Dict) -> bool:
        """Execute security scan stage."""
        try:
            scan_types = config.get("scan_types", ["sast", "dependency"])

            for scan_type in scan_types:
                # Run security scan
                result = await self._run_security_scan(scan_type, config)

                if result.get("vulnerabilities_found", 0) > 0:
                    max_allowed = config.get("max_vulnerabilities", 0)
                    if result["vulnerabilities_found"] > max_allowed:
                        stage["logs"].append(f"Security scan failed: {result['vulnerabilities_found']} vulnerabilities found")
                        return False

                stage["artifacts"][f"security_scan_{scan_type}"] = result

            return True

        except Exception as e:
            stage["logs"].append(f"Security scan error: {e}")
            return False

    async def _execute_deploy_stage(self, execution: Dict, stage: Dict, config: Dict) -> bool:
        """Execute deployment stage."""
        try:
            environment = execution.get("environment", "development")
            deploy_target = config.get("target", environment)

            # Pre-deployment checks
            if not await self._run_pre_deploy_checks(deploy_target, config):
                stage["logs"].append("Pre-deployment checks failed")
                return False

            # Execute deployment
            deploy_result = await self._run_deployment(deploy_target, config, execution)

            if not deploy_result["success"]:
                stage["logs"].append(f"Deployment failed: {deploy_result.get('error', 'Unknown error')}")
                return False

            # Post-deployment verification
            if not await self._run_post_deploy_verification(deploy_target, config):
                stage["logs"].append("Post-deployment verification failed")
                return False

            # Store deployment info
            deployment_record = {
                "execution_id": execution["execution_id"],
                "environment": environment,
                "target": deploy_target,
                "deployed_at": datetime.now(),
                "version": config.get("version", "latest"),
                "artifacts": deploy_result.get("artifacts", {}),
                "rollback_available": True
            }

            self.deployment_history[deploy_target].append(deployment_record)

            stage["artifacts"]["deployment"] = deployment_record

            return True

        except Exception as e:
            stage["logs"].append(f"Deployment error: {e}")
            return False

    async def _execute_approval_stage(self, execution: Dict, stage: Dict, config: Dict) -> bool:
        """Execute approval stage."""
        try:
            # Check if manual approval is required
            required_approvers = config.get("approvers", [])
            approval_timeout = config.get("timeout", 3600)  # 1 hour

            if not required_approvers:
                return True  # No approval required

            # Send approval request
            approval_request = {
                "execution_id": execution["execution_id"],
                "stage": stage["name"],
                "approvers": required_approvers,
                "timeout": approval_timeout,
                "requested_at": datetime.now(),
                "status": "pending"
            }

            # Wait for approval (simplified - in real implementation would use proper approval workflow)
            approved = await self._wait_for_approval(approval_request, approval_timeout)

            if approved:
                execution["approvals"].append({
                    "stage": stage["name"],
                    "approved_by": "system",  # Would be actual approver
                    "approved_at": datetime.now()
                })
                return True
            else:
                stage["logs"].append("Approval timeout or rejection")
                return False

        except Exception as e:
            stage["logs"].append(f"Approval error: {e}")
            return False

    async def _execute_notification_stage(self, execution: Dict, stage: Dict, config: Dict) -> bool:
        """Execute notification stage."""
        try:
            channels = config.get("channels", ["email"])
            message = config.get("message", f"Pipeline {execution['pipeline_name']} completed")

            for channel in channels:
                await self._send_notification(channel, message, execution)

            return True

        except Exception as e:
            stage["logs"].append(f"Notification error: {e}")
            return False

    async def _run_command(self, command: str, cwd: str = ".") -> Dict:
        """Run shell command."""
        try:
            # In real implementation, would use asyncio.subprocess
            # For demo, simulate command execution
            await asyncio.sleep(0.1)  # Simulate execution time

            return {
                "returncode": 0,
                "stdout": f"Executed: {command}",
                "stderr": ""
            }

        except Exception as e:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": str(e)
            }

    async def _run_tests(self, test_type: str, config: Dict) -> Dict:
        """Run tests."""
        # Simulate test execution
        await asyncio.sleep(0.5)

        # Mock test results
        if test_type == "unit":
            return {"passed": 150, "failed": 0, "skipped": 5, "duration": 45.2, "coverage": 92.5}
        elif test_type == "integration":
            return {"passed": 25, "failed": 0, "skipped": 0, "duration": 120.5, "coverage": 85.0}
        else:
            return {"passed": 10, "failed": 0, "skipped": 0, "duration": 30.0, "coverage": 90.0}

    async def _run_security_scan(self, scan_type: str, config: Dict) -> Dict:
        """Run security scan."""
        await asyncio.sleep(0.3)

        # Mock security scan results
        return {
            "scan_type": scan_type,
            "vulnerabilities_found": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "duration": 25.5
        }

    async def _run_pre_deploy_checks(self, target: str, config: Dict) -> bool:
        """Run pre-deployment checks."""
        await asyncio.sleep(0.1)
        # Simulate checks
        return True

    async def _run_deployment(self, target: str, config: Dict, execution: Dict) -> Dict:
        """Run deployment."""
        await asyncio.sleep(1.0)

        return {
            "success": True,
            "version": "1.2.3",
            "artifacts": {"docker_image": "myapp:1.2.3"}
        }

    async def _run_post_deploy_verification(self, target: str, config: Dict) -> bool:
        """Run post-deployment verification."""
        await asyncio.sleep(0.2)
        return True

    async def _wait_for_approval(self, approval_request: Dict, timeout: int) -> bool:
        """Wait for approval."""
        # Simplified - in real implementation would wait for actual approval
        await asyncio.sleep(min(timeout, 10))  # Simulate waiting
        return True  # Assume approved

    async def _rollback_pipeline(self, execution_id: str):
        """Rollback pipeline deployment."""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return

        try:
            environment = execution["environment"]
            rollback_config = self.rollback_configs.get(execution["pipeline_name"])

            if not rollback_config:
                self.logger.warning(f"No rollback config for pipeline {execution['pipeline_name']}")
                return

            # Find previous successful deployment
            deployments = self.deployment_history.get(environment, [])
            successful_deployments = [d for d in deployments if d.get("rollback_available")]

            if not successful_deployments:
                self.logger.warning("No successful deployment found for rollback")
                return

            # Rollback to last successful deployment
            last_deployment = successful_deployments[-1]

            self.logger.info(f"Rolling back {execution_id} to version {last_deployment['version']}")

            # Execute rollback
            await self._execute_rollback(last_deployment, rollback_config)

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")

    async def _execute_rollback(self, deployment: Dict, config: Dict):
        """Execute rollback operation."""
        await asyncio.sleep(0.5)  # Simulate rollback
        self.logger.info("Rollback completed")

    async def _send_pipeline_notifications(self, execution: Dict):
        """Send pipeline completion notifications."""
        pipeline = self.pipelines[execution["pipeline_name"]]
        notifications = pipeline.get("notifications", {})

        message = f"Pipeline {execution['pipeline_name']} {execution['status']}"

        for channel in self.config["notification_channels"]:
            if notifications.get(channel, False):
                await self._send_notification(channel, message, execution)

    async def _send_notification(self, channel: str, message: str, execution: Dict):
        """Send notification to channel."""
        # Simulate notification sending
        self.logger.info(f"Sent {channel} notification: {message}")

    def _store_execution_history(self, execution: Dict):
        """Store pipeline execution history."""
        pipeline_name = execution["pipeline_name"]
        self.pipeline_history[pipeline_name].append(execution)

        # Keep only recent executions
        if len(self.pipeline_history[pipeline_name]) > 100:
            self.pipeline_history[pipeline_name] = self.pipeline_history[pipeline_name][-100:]

    def _calculate_directory_size(self, path: str) -> int:
        """Calculate directory size."""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            return total_size
        except:
            return 0

    def get_pipeline_status(self, execution_id: str) -> Optional[Dict]:
        """Get pipeline execution status."""
        execution = self.active_executions.get(execution_id)
        if execution:
            return execution

        # Check history
        for executions in self.pipeline_history.values():
            for exec_hist in executions:
                if exec_hist["execution_id"] == execution_id:
                    return exec_hist

        return None

    def get_pipeline_metrics(self, pipeline_name: Optional[str] = None) -> Dict:
        """Get pipeline metrics."""
        if pipeline_name:
            pipeline = self.pipelines.get(pipeline_name)
            return pipeline["metrics"] if pipeline else {}

        # Aggregate metrics
        total_pipelines = len(self.pipelines)
        total_executions = sum(len(execs) for execs in self.pipeline_history.values())
        successful_executions = sum(
            len([e for e in execs if e["status"] == PipelineStatus.SUCCESS.value])
            for execs in self.pipeline_history.values()
        )

        success_rate = successful_executions / max(total_executions, 1)

        return {
            "total_pipelines": total_pipelines,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": success_rate,
            "active_executions": len(self.active_executions)
        }

    def cancel_pipeline(self, execution_id: str) -> bool:
        """Cancel pipeline execution."""
        execution = self.active_executions.get(execution_id)
        if not execution:
            return False

        execution["status"] = PipelineStatus.CANCELLED.value
        execution["end_time"] = datetime.now()
        execution["cancelled_at"] = datetime.now()

        self.logger.info(f"Cancelled pipeline execution: {execution_id}")
        return True

    async def retry_pipeline(self, execution_id: str) -> Optional[str]:
        """Retry failed pipeline execution."""
        # Find execution in history
        for pipeline_name, executions in self.pipeline_history.items():
            for execution in executions:
                if execution["execution_id"] == execution_id and execution["status"] == PipelineStatus.FAILED.value:
                    # Trigger new execution
                    return await self.trigger_pipeline(
                        pipeline_name,
                        PipelineTrigger.MANUAL,
                        {"retry_of": execution_id},
                        DeploymentEnvironment(execution["environment"])
                    )

        return None

    async def continuous_pipeline_monitoring(self):
        """Continuous pipeline monitoring."""
        while True:
            try:
                # Monitor active executions
                for execution_id, execution in list(self.active_executions.items()):
                    start_time = execution.get("start_time")
                    if start_time:
                        duration = (datetime.now() - start_time).total_seconds()
                        if duration > self.config["pipeline_timeout"]:
                            self.logger.warning(f"Pipeline {execution_id} timed out")
                            execution["status"] = PipelineStatus.FAILED.value
                            execution["error"] = "Pipeline timeout"

                # Clean up old artifacts
                await self._cleanup_old_artifacts()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Pipeline monitoring error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_old_artifacts(self):
        """Clean up old build artifacts."""
        cutoff_date = datetime.now() - timedelta(days=self.config["artifact_retention_days"])

        # Clean up old artifacts (simplified)
        # In real implementation would remove old files
        pass


# Global CI/CD automation instance
cicd_automation = CICDAutomation()


def create_cicd_pipeline(name: str, config: Dict, stages: List[Dict]) -> bool:
    """Create CI/CD pipeline."""
    return cicd_automation.create_pipeline(name, config, stages)


async def trigger_pipeline_execution(
    pipeline_name: str,
    trigger_type: str = "manual",
    environment: str = "development"
) -> Optional[str]:
    """Trigger pipeline execution."""
    return await cicd_automation.trigger_pipeline(
        pipeline_name,
        PipelineTrigger(trigger_type),
        environment=DeploymentEnvironment(environment)
    )


def get_pipeline_execution_status(execution_id: str) -> Optional[Dict]:
    """Get pipeline execution status."""
    return cicd_automation.get_pipeline_status(execution_id)


def get_cicd_metrics(pipeline_name: Optional[str] = None) -> Dict:
    """Get CI/CD metrics."""
    return cicd_automation.get_pipeline_metrics(pipeline_name)