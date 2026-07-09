"""
Pharma Compliance Module

This module implements pharmaceutical industry compliance features including:
- GMP (Good Manufacturing Practice) compliance
- Batch record management
- Quality control automation
- Regulatory reporting
- Audit trail management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class GMPComplianceLevel(Enum):
    """GMP compliance levels."""
    LEVEL_A = "A"  # Highest - sterile products
    LEVEL_B = "B"  # Background - sterile products
    LEVEL_C = "C"  # Controlled - non-sterile products
    LEVEL_D = "D"  # Uncontrolled - general areas


class BatchStatus(Enum):
    """Batch processing statuses."""
    CREATED = "created"
    IN_PROCESS = "in_process"
    QUALITY_CHECK = "quality_check"
    APPROVED = "approved"
    REJECTED = "rejected"
    RELEASED = "released"


class PharmaComplianceModule:
    """
    Pharmaceutical compliance and quality management system.

    Implements GMP compliance, batch tracking, and regulatory requirements
    specific to pharmaceutical manufacturing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pharma compliance module.

        Args:
            config: Module configuration
        """
        self.config = config or self._get_default_config()

        # GMP compliance tracking
        self.gmp_areas: Dict[str, Dict[str, Any]] = {}
        self.batch_records: Dict[str, Dict[str, Any]] = {}
        self.quality_tests: Dict[str, Dict[str, Any]] = {}
        self.audit_trail: List[Dict[str, Any]] = []

        # Regulatory compliance
        self.regulatory_reports: Dict[str, Dict[str, Any]] = {}
        self.compliance_alerts: List[Dict[str, Any]] = []

        # Quality control
        self.quality_thresholds: Dict[str, Dict[str, Any]] = {}
        self.calibration_records: Dict[str, Dict[str, Any]] = {}

        self.logger = get_logger(__name__)
        self.logger.info("Pharma Compliance Module initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "gmp_enabled": True,
            "batch_retention_days": 365 * 7,  # 7 years
            "audit_trail_retention_days": 365 * 10,  # 10 years
            "quality_check_frequency_hours": 24,
            "regulatory_reporting_frequency_days": 30,
            "critical_parameter_alert_threshold": 0.95,  # 95% of specification
            "batch_approval_required_signatures": 2
        }

    async def register_gmp_area(
        self,
        area_id: str,
        area_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a GMP-controlled area.

        Args:
            area_id: Unique area identifier
            area_config: Area configuration

        Returns:
            Registration result
        """
        try:
            self.logger.info(f"Registering GMP area {area_id}")

            # Validate GMP compliance level
            compliance_level = area_config.get("compliance_level", "D")
            if compliance_level not in [level.value for level in GMPComplianceLevel]:
                raise ValueError(f"Invalid GMP compliance level: {compliance_level}")

            area = {
                "area_id": area_id,
                "name": area_config.get("name", area_id),
                "compliance_level": GMPComplianceLevel(compliance_level),
                "location": area_config.get("location", {}),
                "environmental_controls": area_config.get("environmental_controls", {}),
                "access_controls": area_config.get("access_controls", {}),
                "monitoring_points": area_config.get("monitoring_points", []),
                "status": "active",
                "registered_at": datetime.now().isoformat(),
                "last_inspection": None,
                "compliance_score": 100.0,
                "metadata": area_config.get("metadata", {})
            }

            self.gmp_areas[area_id] = area

            # Initialize environmental monitoring
            await self._initialize_environmental_monitoring(area_id, area_config)

            self.logger.info(f"GMP area {area_id} registered with {compliance_level} compliance")
            return {
                "area_id": area_id,
                "status": "registered",
                "compliance_level": compliance_level,
                "monitoring_points": len(area["monitoring_points"])
            }

        except Exception as e:
            self.logger.error(f"Failed to register GMP area {area_id}: {e}")
            raise

    async def _initialize_environmental_monitoring(
        self,
        area_id: str,
        area_config: Dict[str, Any]
    ):
        """Initialize environmental monitoring for GMP area."""
        # Set up monitoring points based on compliance level
        compliance_level = area_config.get("compliance_level", "D")

        monitoring_requirements = {
            "A": {"particles": True, "temperature": True, "humidity": True, "pressure": True},
            "B": {"particles": True, "temperature": True, "humidity": True, "pressure": False},
            "C": {"particles": False, "temperature": True, "humidity": True, "pressure": False},
            "D": {"particles": False, "temperature": False, "humidity": False, "pressure": False}
        }

        requirements = monitoring_requirements.get(compliance_level, {})
        monitoring_points = []

        if requirements.get("temperature"):
            monitoring_points.append({
                "type": "temperature",
                "sensor_id": f"{area_id}_temp",
                "specification": {"min": 18, "max": 25},  # Celsius
                "frequency": 60  # seconds
            })

        if requirements.get("humidity"):
            monitoring_points.append({
                "type": "humidity",
                "sensor_id": f"{area_id}_humid",
                "specification": {"min": 40, "max": 60},  # %
                "frequency": 60
            })

        if requirements.get("particles"):
            monitoring_points.append({
                "type": "particles",
                "sensor_id": f"{area_id}_particles",
                "specification": {"max": 3520},  # particles/m³ (ISO 5)
                "frequency": 300  # 5 minutes
            })

        self.gmp_areas[area_id]["monitoring_points"] = monitoring_points

    async def create_batch_record(
        self,
        batch_id: str,
        batch_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new batch record for pharmaceutical production.

        Args:
            batch_id: Unique batch identifier
            batch_config: Batch configuration

        Returns:
            Batch creation result
        """
        try:
            self.logger.info(f"Creating batch record {batch_id}")

            # Validate batch configuration
            await self._validate_batch_config(batch_config)

            batch = {
                "batch_id": batch_id,
                "product_name": batch_config["product_name"],
                "product_code": batch_config.get("product_code"),
                "batch_size": batch_config["batch_size"],
                "unit_of_measure": batch_config.get("unit_of_measure", "kg"),
                "manufacturing_date": batch_config.get("manufacturing_date", datetime.now().isoformat()),
                "expiry_date": batch_config.get("expiry_date"),
                "gmp_area": batch_config.get("gmp_area"),
                "equipment_used": batch_config.get("equipment_used", []),
                "raw_materials": batch_config.get("raw_materials", []),
                "process_parameters": batch_config.get("process_parameters", {}),
                "quality_checks": [],
                "status": BatchStatus.CREATED.value,
                "created_at": datetime.now().isoformat(),
                "approved_signatures": [],
                "rejection_reason": None,
                "metadata": batch_config.get("metadata", {})
            }

            self.batch_records[batch_id] = batch

            # Log audit trail
            await self._log_audit_event(
                "batch_created",
                batch_id,
                f"Batch {batch_id} created for product {batch['product_name']}",
                {"batch_config": batch_config}
            )

            self.logger.info(f"Batch record {batch_id} created for {batch['batch_size']} {batch['unit_of_measure']} of {batch['product_name']}")
            return {
                "batch_id": batch_id,
                "status": "created",
                "product_name": batch["product_name"],
                "batch_size": batch["batch_size"]
            }

        except Exception as e:
            self.logger.error(f"Failed to create batch record {batch_id}: {e}")
            raise

    async def _validate_batch_config(self, config: Dict[str, Any]):
        """Validate batch configuration."""
        required_fields = ["product_name", "batch_size"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        # Validate GMP area if specified
        if config.get("gmp_area"):
            if config["gmp_area"] not in self.gmp_areas:
                raise ValueError(f"GMP area {config['gmp_area']} not registered")

        # Validate expiry date
        if config.get("expiry_date"):
            expiry = datetime.fromisoformat(config["expiry_date"])
            manufacturing = datetime.fromisoformat(config.get("manufacturing_date", datetime.now().isoformat()))
            if expiry <= manufacturing:
                raise ValueError("Expiry date must be after manufacturing date")

    async def update_batch_status(
        self,
        batch_id: str,
        new_status: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update batch processing status.

        Args:
            batch_id: Batch identifier
            new_status: New status
            user_id: User making the change
            notes: Optional notes

        Returns:
            Status update result
        """
        try:
            if batch_id not in self.batch_records:
                raise ValueError(f"Batch {batch_id} not found")

            batch = self.batch_records[batch_id]

            # Validate status transition
            await self._validate_status_transition(batch["status"], new_status)

            old_status = batch["status"]
            batch["status"] = new_status
            batch["last_updated"] = datetime.now().isoformat()

            # Add status change to batch record
            status_change = {
                "timestamp": datetime.now().isoformat(),
                "old_status": old_status,
                "new_status": new_status,
                "user_id": user_id,
                "notes": notes
            }

            if "status_history" not in batch:
                batch["status_history"] = []
            batch["status_history"].append(status_change)

            # Log audit trail
            await self._log_audit_event(
                "batch_status_changed",
                batch_id,
                f"Batch status changed from {old_status} to {new_status}",
                {"user_id": user_id, "notes": notes}
            )

            self.logger.info(f"Batch {batch_id} status updated to {new_status}")
            return {
                "batch_id": batch_id,
                "old_status": old_status,
                "new_status": new_status,
                "updated_at": batch["last_updated"]
            }

        except Exception as e:
            self.logger.error(f"Failed to update batch status {batch_id}: {e}")
            raise

    async def _validate_status_transition(self, current_status: str, new_status: str):
        """Validate batch status transition."""
        valid_transitions = {
            BatchStatus.CREATED.value: [BatchStatus.IN_PROCESS.value],
            BatchStatus.IN_PROCESS.value: [BatchStatus.QUALITY_CHECK.value, BatchStatus.REJECTED.value],
            BatchStatus.QUALITY_CHECK.value: [BatchStatus.APPROVED.value, BatchStatus.REJECTED.value],
            BatchStatus.APPROVED.value: [BatchStatus.RELEASED.value],
            BatchStatus.REJECTED.value: [],  # Terminal state
            BatchStatus.RELEASED.value: []   # Terminal state
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise ValueError(f"Invalid status transition from {current_status} to {new_status}")

    async def perform_quality_check(
        self,
        batch_id: str,
        check_type: str,
        parameters: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Perform quality check on batch.

        Args:
            batch_id: Batch identifier
            check_type: Type of quality check
            parameters: Check parameters and results
            user_id: User performing the check

        Returns:
            Quality check result
        """
        try:
            if batch_id not in self.batch_records:
                raise ValueError(f"Batch {batch_id} not found")

            batch = self.batch_records[batch_id]

            # Perform the quality check
            check_result = await self._execute_quality_check(check_type, parameters)

            # Record the check
            quality_check = {
                "check_id": f"qc_{batch_id}_{int(datetime.now().timestamp())}",
                "batch_id": batch_id,
                "check_type": check_type,
                "parameters": parameters,
                "results": check_result,
                "performed_by": user_id,
                "performed_at": datetime.now().isoformat(),
                "status": "passed" if check_result["passed"] else "failed"
            }

            batch["quality_checks"].append(quality_check)

            # Update batch status if all checks passed
            if check_result["passed"] and batch["status"] == BatchStatus.QUALITY_CHECK.value:
                await self.update_batch_status(batch_id, BatchStatus.APPROVED.value, user_id, "Quality checks passed")

            # Log audit trail
            await self._log_audit_event(
                "quality_check_performed",
                batch_id,
                f"Quality check {check_type} performed: {'PASSED' if check_result['passed'] else 'FAILED'}",
                {"check_result": check_result, "user_id": user_id}
            )

            self.logger.info(f"Quality check {check_type} performed on batch {batch_id}: {'PASSED' if check_result['passed'] else 'FAILED'}")
            return {
                "batch_id": batch_id,
                "check_type": check_type,
                "status": quality_check["status"],
                "results": check_result
            }

        except Exception as e:
            self.logger.error(f"Failed to perform quality check on batch {batch_id}: {e}")
            raise

    async def _execute_quality_check(
        self,
        check_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute specific quality check."""
        if check_type == "assay":
            return await self._check_assay(parameters)
        elif check_type == "impurities":
            return await self._check_impurities(parameters)
        elif check_type == "dissolution":
            return await self._check_dissolution(parameters)
        elif check_type == "microbial":
            return await self._check_microbial(parameters)
        else:
            raise ValueError(f"Unknown quality check type: {check_type}")

    async def _check_assay(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check active ingredient assay."""
        target = parameters.get("target_concentration", 100)
        measured = parameters.get("measured_concentration", 0)
        tolerance = parameters.get("tolerance", 5)  # ±5%

        deviation = abs(measured - target) / target * 100
        passed = deviation <= tolerance

        return {
            "passed": passed,
            "target": target,
            "measured": measured,
            "deviation_percent": deviation,
            "tolerance_percent": tolerance
        }

    async def _check_impurities(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check impurity levels."""
        max_allowed = parameters.get("max_impurities", 0.1)  # 0.1%
        measured = parameters.get("measured_impurities", 0)

        passed = measured <= max_allowed

        return {
            "passed": passed,
            "max_allowed": max_allowed,
            "measured": measured,
            "exceeds_by": max(0, measured - max_allowed)
        }

    async def _check_dissolution(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check dissolution profile."""
        target = parameters.get("target_dissolution", 80)  # 80% in 30 min
        measured = parameters.get("measured_dissolution", 0)
        tolerance = parameters.get("tolerance", 10)  # ±10%

        deviation = abs(measured - target)
        passed = deviation <= tolerance

        return {
            "passed": passed,
            "target": target,
            "measured": measured,
            "deviation": deviation,
            "tolerance": tolerance
        }

    async def _check_microbial(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check microbial contamination."""
        max_tpc = parameters.get("max_total_plate_count", 100)  # CFU/g
        max_yeast = parameters.get("max_yeast_mold", 10)
        max_ecoli = parameters.get("max_e_coli", 0)

        measured_tpc = parameters.get("measured_tpc", 0)
        measured_yeast = parameters.get("measured_yeast", 0)
        measured_ecoli = parameters.get("measured_ecoli", 0)

        passed = (measured_tpc <= max_tpc and
                 measured_yeast <= max_yeast and
                 measured_ecoli <= max_ecoli)

        return {
            "passed": passed,
            "tpc": {"max": max_tpc, "measured": measured_tpc},
            "yeast_mold": {"max": max_yeast, "measured": measured_yeast},
            "e_coli": {"max": max_ecoli, "measured": measured_ecoli}
        }

    async def approve_batch(
        self,
        batch_id: str,
        approver_id: str,
        signature: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve batch for release.

        Args:
            batch_id: Batch identifier
            approver_id: Approver user ID
            signature: Digital signature
            comments: Approval comments

        Returns:
            Approval result
        """
        try:
            if batch_id not in self.batch_records:
                raise ValueError(f"Batch {batch_id} not found")

            batch = self.batch_records[batch_id]

            if batch["status"] != BatchStatus.APPROVED.value:
                raise ValueError(f"Batch {batch_id} is not in approved status")

            # Add approval signature
            approval = {
                "approver_id": approver_id,
                "signature": signature,
                "approved_at": datetime.now().isoformat(),
                "comments": comments
            }

            batch["approved_signatures"].append(approval)

            # Check if we have enough signatures
            if len(batch["approved_signatures"]) >= self.config["batch_approval_required_signatures"]:
                await self.update_batch_status(batch_id, BatchStatus.RELEASED.value, approver_id, "Batch approved and released")

            # Log audit trail
            await self._log_audit_event(
                "batch_approved",
                batch_id,
                f"Batch approved by {approver_id}",
                {"approver_id": approver_id, "comments": comments}
            )

            self.logger.info(f"Batch {batch_id} approved by {approver_id}")
            return {
                "batch_id": batch_id,
                "approver_id": approver_id,
                "signatures_count": len(batch["approved_signatures"]),
                "required_signatures": self.config["batch_approval_required_signatures"],
                "status": batch["status"]
            }

        except Exception as e:
            self.logger.error(f"Failed to approve batch {batch_id}: {e}")
            raise

    async def generate_regulatory_report(
        self,
        report_type: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Generate regulatory compliance report.

        Args:
            report_type: Type of report (batch_summary, quality_metrics, gmp_compliance)
            start_date: Report start date
            end_date: Report end date

        Returns:
            Regulatory report
        """
        try:
            self.logger.info(f"Generating {report_type} regulatory report")

            if report_type == "batch_summary":
                report = await self._generate_batch_summary_report(start_date, end_date)
            elif report_type == "quality_metrics":
                report = await self._generate_quality_metrics_report(start_date, end_date)
            elif report_type == "gmp_compliance":
                report = await self._generate_gmp_compliance_report(start_date, end_date)
            else:
                raise ValueError(f"Unknown report type: {report_type}")

            # Store report
            report_id = f"report_{report_type}_{int(datetime.now().timestamp())}"
            self.regulatory_reports[report_id] = {
                "report_id": report_id,
                "type": report_type,
                "start_date": start_date,
                "end_date": end_date,
                "generated_at": datetime.now().isoformat(),
                "content": report
            }

            return {
                "report_id": report_id,
                "type": report_type,
                "start_date": start_date,
                "end_date": end_date,
                "report": report
            }

        except Exception as e:
            self.logger.error(f"Failed to generate regulatory report {report_type}: {e}")
            raise

    async def _generate_batch_summary_report(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Generate batch summary report."""
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        relevant_batches = [
            batch for batch in self.batch_records.values()
            if start <= datetime.fromisoformat(batch["created_at"]) <= end
        ]

        total_batches = len(relevant_batches)
        approved_batches = len([b for b in relevant_batches if b["status"] == BatchStatus.RELEASED.value])
        rejected_batches = len([b for b in relevant_batches if b["status"] == BatchStatus.REJECTED.value])

        return {
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_batches": total_batches,
                "approved_batches": approved_batches,
                "rejected_batches": rejected_batches,
                "approval_rate": approved_batches / total_batches * 100 if total_batches > 0 else 0
            },
            "batches": relevant_batches
        }

    async def _generate_quality_metrics_report(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Generate quality metrics report."""
        # Aggregate quality check results
        quality_checks = []
        for batch in self.batch_records.values():
            for check in batch.get("quality_checks", []):
                check_date = datetime.fromisoformat(check["performed_at"])
                if start_date <= check_date.isoformat() <= end_date:
                    quality_checks.append(check)

        total_checks = len(quality_checks)
        passed_checks = len([c for c in quality_checks if c["status"] == "passed"])

        return {
            "period": {"start": start_date, "end": end_date},
            "quality_metrics": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "failed_checks": total_checks - passed_checks,
                "pass_rate": passed_checks / total_checks * 100 if total_checks > 0 else 0
            },
            "checks": quality_checks
        }

    async def _generate_gmp_compliance_report(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Generate GMP compliance report."""
        compliance_scores = {}
        for area_id, area in self.gmp_areas.items():
            compliance_scores[area_id] = area.get("compliance_score", 100.0)

        avg_compliance = sum(compliance_scores.values()) / len(compliance_scores) if compliance_scores else 100.0

        return {
            "period": {"start": start_date, "end": end_date},
            "gmp_compliance": {
                "overall_score": avg_compliance,
                "area_scores": compliance_scores,
                "areas_monitored": len(compliance_scores)
            },
            "areas": list(self.gmp_areas.values())
        }

    async def _log_audit_event(
        self,
        event_type: str,
        entity_id: str,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log audit trail event."""
        audit_event = {
            "event_id": f"audit_{int(datetime.now().timestamp())}",
            "event_type": event_type,
            "entity_id": entity_id,
            "description": description,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "user_id": "system"  # In real implementation, get from context
        }

        self.audit_trail.append(audit_event)

        # Keep only recent audit trail
        cutoff_date = datetime.now() - timedelta(days=self.config["audit_trail_retention_days"])
        self.audit_trail = [
            event for event in self.audit_trail
            if datetime.fromisoformat(event["timestamp"]) > cutoff_date
        ]

    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch status and details."""
        return self.batch_records.get(batch_id)

    def get_gmp_area_status(self, area_id: str) -> Optional[Dict[str, Any]]:
        """Get GMP area status."""
        return self.gmp_areas.get(area_id)

    def get_audit_trail(
        self,
        entity_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail with optional filtering."""
        audit_events = self.audit_trail

        if entity_id:
            audit_events = [e for e in audit_events if e["entity_id"] == entity_id]

        if event_type:
            audit_events = [e for e in audit_events if e["event_type"] == event_type]

        # Sort by timestamp (newest first)
        audit_events.sort(key=lambda x: x["timestamp"], reverse=True)

        return audit_events[:limit]


# Global pharma compliance module instance
pharma_compliance = PharmaComplianceModule()


async def register_gmp_area(area_id: str, area_config: Dict[str, Any]) -> Dict[str, Any]:
    """Register GMP area."""
    return await pharma_compliance.register_gmp_area(area_id, area_config)


async def create_batch_record(batch_id: str, batch_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create batch record."""
    return await pharma_compliance.create_batch_record(batch_id, batch_config)


async def perform_quality_check(
    batch_id: str,
    check_type: str,
    parameters: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """Perform quality check."""
    return await pharma_compliance.perform_quality_check(batch_id, check_type, parameters, user_id)


async def generate_regulatory_report(
    report_type: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """Generate regulatory report."""
    return await pharma_compliance.generate_regulatory_report(report_type, start_date, end_date)