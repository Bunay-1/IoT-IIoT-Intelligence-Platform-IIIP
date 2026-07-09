"""
FMEA Analysis Module

This module implements Failure Mode and Effects Analysis (FMEA) for
systematic identification and mitigation of potential failure modes
in manufacturing processes and equipment.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from src.utils.logging_config import LoggerMixin
from src.utils.performance_monitor import monitor_operation
from src.utils.security import SecurityError, input_validator, validate_input


class FMEAError(Exception):
    """Base exception for FMEA analysis errors."""
    pass


class FMEAAnalysis(LoggerMixin):
    """
    Failure Mode and Effects Analysis (FMEA) implementation.

    This class provides comprehensive FMEA analysis including:
    - Failure mode identification and analysis
    - Risk Priority Number (RPN) calculation
    - Mitigation strategy development
    - FMEA report generation
    - Risk monitoring and tracking
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the FMEA analyzer.

        Args:
            config: Configuration dictionary with analysis parameters
        """
        self.config = config or self._get_default_config()

        # FMEA database
        self.fmea_records: Dict[str, Dict[str, Any]] = {}
        self.mitigation_actions: Dict[str, List[Dict[str, Any]]] = {}
        self.risk_history: Dict[str, List[Dict[str, Any]]] = {}

        self.logger.info("FMEA Analysis system initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "rpn_thresholds": {
                "high": 100,      # RPN >= 100
                "medium": 50,     # 50 <= RPN < 100
                "low": 0          # RPN < 50
            },
            "severity_scale": {
                "none": 1,
                "minor": 3,
                "moderate": 6,
                "major": 8,
                "critical": 10
            },
            "occurrence_scale": {
                "very_low": 1,
                "low": 3,
                "moderate": 6,
                "high": 8,
                "very_high": 10
            },
            "detection_scale": {
                "almost_certain": 1,
                "very_high": 2,
                "high": 3,
                "moderate": 6,
                "low": 8,
                "very_low": 9,
                "almost_impossible": 10
            },
            "auto_update_interval": 86400,  # 24 hours
            "review_cycle_days": 90
        }

    @validate_input({
        "system_component": {
            "type": "string",
            "max_length": 100,
            "required": True
        },
        "failure_modes": {
            "type": "array",
            "required": True
        }
    })
    @monitor_operation("fmea_analysis.conduct_fmea")
    async def conduct_fmea(
        self,
        system_component: str,
        failure_modes: List[Dict[str, Any]],
        analysis_scope: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Conduct FMEA analysis for a system component.

        Args:
            system_component: Name of the system/component being analyzed
            failure_modes: List of potential failure modes with their details
            analysis_scope: Scope of the analysis (design, process, etc.)

        Returns:
            Complete FMEA analysis results

        Raises:
            FMEAError: If analysis fails
        """
        try:
            self.logger.info(f"Conducting FMEA for {system_component}")

            fmea_id = f"fmea_{system_component}_{int(asyncio.get_event_loop().time())}"

            # Validate failure modes
            validated_modes = await self._validate_failure_modes(failure_modes)

            # Analyze each failure mode
            analyzed_modes = []
            for mode in validated_modes:
                analyzed_mode = await self._analyze_failure_mode(mode, system_component)
                analyzed_modes.append(analyzed_mode)

            # Calculate overall risk metrics
            risk_metrics = self._calculate_risk_metrics(analyzed_modes)

            # Generate recommendations
            recommendations = self._generate_fmea_recommendations(analyzed_modes, risk_metrics)

            # Create FMEA record
            fmea_record = {
                "fmea_id": fmea_id,
                "system_component": system_component,
                "analysis_scope": analysis_scope,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "failure_modes": analyzed_modes,
                "risk_metrics": risk_metrics,
                "recommendations": recommendations,
                "status": "active",
                "review_due": self._calculate_review_date()
            }

            # Store FMEA record
            self.fmea_records[fmea_id] = fmea_record
            self.risk_history[fmea_id] = []

            result = {
                "fmea_id": fmea_id,
                "system_component": system_component,
                "analysis_summary": {
                    "total_failure_modes": len(analyzed_modes),
                    "high_risk_modes": len([m for m in analyzed_modes if m["risk_level"] == "high"]),
                    "overall_risk_score": risk_metrics["overall_risk_score"],
                    "criticality_level": risk_metrics["criticality_level"]
                },
                "failure_modes": analyzed_modes,
                "risk_metrics": risk_metrics,
                "recommendations": recommendations,
                "next_review_date": fmea_record["review_due"]
            }

            self.logger.info(f"FMEA completed for {system_component}. High-risk modes: {result['analysis_summary']['high_risk_modes']}")
            return result

        except Exception as e:
            self.logger.error(f"FMEA analysis failed for {system_component}: {e}")
            raise FMEAError(f"FMEA analysis failed: {e}") from e

    async def _validate_failure_modes(self, failure_modes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate failure mode data."""
        validated = []

        required_fields = ["failure_mode", "effects", "causes"]

        for i, mode in enumerate(failure_modes):
            missing_fields = [field for field in required_fields if field not in mode]
            if missing_fields:
                raise FMEAError(f"Failure mode {i+1} missing required fields: {missing_fields}")

            # Validate severity, occurrence, detection if provided
            for rating_field in ["severity", "occurrence", "detection"]:
                if rating_field in mode:
                    value = mode[rating_field]
                    if not isinstance(value, int) or not (1 <= value <= 10):
                        raise FMEAError(f"Invalid {rating_field} rating: {value}. Must be 1-10")

            validated.append(mode.copy())

        return validated

    async def _analyze_failure_mode(
        self,
        failure_mode: Dict[str, Any],
        system_component: str
    ) -> Dict[str, Any]:
        """Analyze a single failure mode."""
        try:
            # Extract ratings (use defaults if not provided)
            severity = failure_mode.get("severity", self._estimate_severity(failure_mode))
            occurrence = failure_mode.get("occurrence", self._estimate_occurrence(failure_mode))
            detection = failure_mode.get("detection", self._estimate_detection(failure_mode))

            # Calculate RPN
            rpn = severity * occurrence * detection

            # Determine risk level
            risk_level = self._determine_risk_level(rpn)

            # Generate mitigation suggestions
            mitigation_suggestions = self._generate_mitigation_suggestions(
                failure_mode, severity, occurrence, detection, rpn
            )

            analyzed_mode = {
                "failure_mode": failure_mode["failure_mode"],
                "effects": failure_mode["effects"],
                "causes": failure_mode["causes"],
                "severity": severity,
                "occurrence": occurrence,
                "detection": detection,
                "rpn": rpn,
                "risk_level": risk_level,
                "mitigation_suggestions": mitigation_suggestions,
                "current_controls": failure_mode.get("current_controls", []),
                "recommended_actions": failure_mode.get("recommended_actions", []),
                "responsible_party": failure_mode.get("responsible_party", "TBD"),
                "target_completion_date": failure_mode.get("target_completion_date"),
                "analysis_timestamp": datetime.now().isoformat()
            }

            return analyzed_mode

        except Exception as e:
            self.logger.warning(f"Failure mode analysis failed: {e}")
            return {
                "failure_mode": failure_mode.get("failure_mode", "Unknown"),
                "error": str(e),
                "rpn": 0,
                "risk_level": "unknown"
            }

    def _estimate_severity(self, failure_mode: Dict[str, Any]) -> int:
        """Estimate severity rating based on effects."""
        effects = failure_mode.get("effects", "").lower()

        if any(word in effects for word in ["critical", "fatal", "catastrophic", "safety"]):
            return 10
        elif any(word in effects for word in ["major", "significant", "production stop"]):
            return 8
        elif any(word in effects for word in ["moderate", "quality issue"]):
            return 6
        elif any(word in effects for word in ["minor", "cosmetic"]):
            return 3
        else:
            return 1

    def _estimate_occurrence(self, failure_mode: Dict[str, Any]) -> int:
        """Estimate occurrence rating based on causes."""
        causes = failure_mode.get("causes", "")

        # Simple estimation based on cause complexity
        if len(causes.split()) > 20:  # Complex causes
            return 8
        elif len(causes.split()) > 10:
            return 6
        elif len(causes.split()) > 5:
            return 3
        else:
            return 1

    def _estimate_detection(self, failure_mode: Dict[str, Any]) -> int:
        """Estimate detection rating based on current controls."""
        controls = failure_mode.get("current_controls", [])

        if not controls:  # No controls
            return 10
        elif len(controls) >= 3:  # Multiple controls
            return 2
        elif len(controls) >= 2:
            return 3
        else:
            return 6

    def _determine_risk_level(self, rpn: int) -> str:
        """Determine risk level based on RPN."""
        thresholds = self.config["rpn_thresholds"]

        if rpn >= thresholds["high"]:
            return "high"
        elif rpn >= thresholds["medium"]:
            return "medium"
        else:
            return "low"

    def _generate_mitigation_suggestions(
        self,
        failure_mode: Dict[str, Any],
        severity: int,
        occurrence: int,
        detection: int,
        rpn: int
    ) -> List[str]:
        """Generate mitigation suggestions."""
        suggestions = []

        # High severity suggestions
        if severity >= 8:
            suggestions.append("Implement redundant safety systems")
            suggestions.append("Add fail-safe mechanisms")
            suggestions.append("Increase monitoring frequency")

        # High occurrence suggestions
        if occurrence >= 8:
            suggestions.append("Review and improve maintenance procedures")
            suggestions.append("Implement preventive maintenance")
            suggestions.append("Analyze root causes of frequent failures")

        # High detection difficulty suggestions
        if detection >= 8:
            suggestions.append("Add additional sensors and monitoring")
            suggestions.append("Implement automated detection systems")
            suggestions.append("Improve inspection procedures")

        # General suggestions based on RPN
        if rpn >= 100:
            suggestions.append("Immediate action required - high priority")
            suggestions.append("Consider design changes or component replacement")
        elif rpn >= 50:
            suggestions.append("Schedule mitigation actions within 30 days")
            suggestions.append("Monitor closely and track effectiveness")

        if not suggestions:
            suggestions.append("Continue monitoring and regular reviews")

        return suggestions

    def _calculate_risk_metrics(self, analyzed_modes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall risk metrics."""
        try:
            if not analyzed_modes:
                return {"overall_risk_score": 0, "criticality_level": "low"}

            rpn_values = [mode["rpn"] for mode in analyzed_modes if "rpn" in mode]
            risk_levels = [mode["risk_level"] for mode in analyzed_modes if "risk_level" in mode]

            # Overall risk score (average RPN)
            overall_risk_score = sum(rpn_values) / len(rpn_values) if rpn_values else 0

            # Criticality level
            high_risk_count = risk_levels.count("high")
            if high_risk_count > len(analyzed_modes) * 0.3:  # >30% high risk
                criticality_level = "critical"
            elif high_risk_count > len(analyzed_modes) * 0.1:  # >10% high risk
                criticality_level = "high"
            elif high_risk_count > 0:
                criticality_level = "medium"
            else:
                criticality_level = "low"

            return {
                "overall_risk_score": float(overall_risk_score),
                "total_failure_modes": len(analyzed_modes),
                "high_risk_modes": high_risk_count,
                "medium_risk_modes": risk_levels.count("medium"),
                "low_risk_modes": risk_levels.count("low"),
                "criticality_level": criticality_level,
                "rpn_distribution": {
                    "min": min(rpn_values) if rpn_values else 0,
                    "max": max(rpn_values) if rpn_values else 0,
                    "average": overall_risk_score,
                    "median": sorted(rpn_values)[len(rpn_values)//2] if rpn_values else 0
                }
            }

        except Exception as e:
            self.logger.warning(f"Risk metrics calculation failed: {e}")
            return {"overall_risk_score": 0, "criticality_level": "unknown"}

    def _generate_fmea_recommendations(
        self,
        analyzed_modes: List[Dict[str, Any]],
        risk_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate overall FMEA recommendations."""
        recommendations = []

        try:
            criticality = risk_metrics.get("criticality_level", "low")
            high_risk_count = risk_metrics.get("high_risk_modes", 0)

            if criticality == "critical":
                recommendations.append("CRITICAL: Immediate action required for multiple high-risk failure modes")
                recommendations.append("Consider system redesign or component replacement")
                recommendations.append("Implement enhanced monitoring and control systems")

            elif criticality == "high":
                recommendations.append("HIGH PRIORITY: Address high-risk failure modes promptly")
                recommendations.append("Review maintenance and inspection procedures")
                recommendations.append("Consider additional safety measures")

            elif criticality == "medium":
                recommendations.append("MEDIUM PRIORITY: Monitor and mitigate identified risks")
                recommendations.append("Implement recommended actions within scheduled timeframe")

            # Specific recommendations based on failure modes
            high_risk_modes = [m for m in analyzed_modes if m.get("risk_level") == "high"]
            if high_risk_modes:
                recommendations.append(f"Focus on {len(high_risk_modes)} high-risk failure modes first")

            # General recommendations
            recommendations.append("Establish regular FMEA review schedule")
            recommendations.append("Track effectiveness of implemented mitigation actions")
            recommendations.append("Update FMEA when system changes occur")

        except Exception as e:
            self.logger.warning(f"FMEA recommendations generation failed: {e}")
            recommendations = ["Review FMEA analysis results and implement appropriate mitigations"]

        return recommendations

    def _calculate_review_date(self) -> str:
        """Calculate next review date."""
        from datetime import timedelta
        review_days = self.config["review_cycle_days"]
        review_date = datetime.now() + timedelta(days=review_days)
        return review_date.isoformat()

    @validate_input({
        "fmea_id": {
            "type": "string",
            "required": True
        },
        "action_details": {
            "type": "object",
            "required": True
        }
    })
    @monitor_operation("fmea_analysis.add_mitigation_action")
    def add_mitigation_action(
        self,
        fmea_id: str,
        action_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a mitigation action for an FMEA record.

        Args:
            fmea_id: FMEA record identifier
            action_details: Details of the mitigation action

        Returns:
            Action addition result
        """
        try:
            if fmea_id not in self.fmea_records:
                raise FMEAError(f"FMEA record {fmea_id} not found")

            # Validate action details
            required_fields = ["action", "responsible_party", "target_date"]
            missing_fields = [field for field in required_fields if field not in action_details]
            if missing_fields:
                raise FMEAError(f"Missing required fields: {missing_fields}")

            action_record = {
                "action_id": f"action_{fmea_id}_{len(self.mitigation_actions.get(fmea_id, [])) + 1}",
                "action": action_details["action"],
                "responsible_party": action_details["responsible_party"],
                "target_date": action_details["target_date"],
                "status": action_details.get("status", "planned"),
                "priority": action_details.get("priority", "medium"),
                "created_at": datetime.now().isoformat(),
                "notes": action_details.get("notes", "")
            }

            if fmea_id not in self.mitigation_actions:
                self.mitigation_actions[fmea_id] = []

            self.mitigation_actions[fmea_id].append(action_record)

            # Update FMEA record timestamp
            self.fmea_records[fmea_id]["last_updated"] = datetime.now().isoformat()

            self.logger.info(f"Mitigation action added to FMEA {fmea_id}")
            return {
                "action_id": action_record["action_id"],
                "status": "added",
                "fmea_id": fmea_id
            }

        except Exception as e:
            self.logger.error(f"Failed to add mitigation action: {e}")
            raise FMEAError(f"Failed to add mitigation action: {e}") from e

    @monitor_operation("fmea_analysis.get_fmea_report")
    def get_fmea_report(
        self,
        fmea_id: Optional[str] = None,
        system_component: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get FMEA report."""
        try:
            # Filter records
            records = list(self.fmea_records.values())

            if fmea_id:
                records = [r for r in records if r["fmea_id"] == fmea_id]
            elif system_component:
                records = [r for r in records if r["system_component"] == system_component]

            # Generate summary
            summary = {
                "total_fmeas": len(records),
                "active_fmeas": len([r for r in records if r["status"] == "active"]),
                "high_risk_fmeas": len([r for r in records if r["risk_metrics"].get("criticality_level") == "critical"]),
                "total_mitigation_actions": sum(len(self.mitigation_actions.get(r["fmea_id"], [])) for r in records)
            }

            return {
                "summary": summary,
                "fmea_records": records[-10:],  # Last 10 records
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {"error": str(e)}

    @validate_input({
        "fmea_id": {
            "type": "string",
            "required": True
        }
    })
    @monitor_operation("fmea_analysis.update_rpn")
    def update_rpn(
        self,
        fmea_id: str,
        failure_mode_index: int,
        new_ratings: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Update RPN ratings for a failure mode.

        Args:
            fmea_id: FMEA record identifier
            failure_mode_index: Index of the failure mode in the list
            new_ratings: New severity, occurrence, detection ratings

        Returns:
            Updated failure mode data
        """
        try:
            if fmea_id not in self.fmea_records:
                raise FMEAError(f"FMEA record {fmea_id} not found")

            record = self.fmea_records[fmea_id]
            failure_modes = record["failure_modes"]

            if failure_mode_index >= len(failure_modes):
                raise FMEAError(f"Invalid failure mode index: {failure_mode_index}")

            mode = failure_modes[failure_mode_index]

            # Update ratings
            for rating_type in ["severity", "occurrence", "detection"]:
                if rating_type in new_ratings:
                    value = new_ratings[rating_type]
                    if not isinstance(value, int) or not (1 <= value <= 10):
                        raise FMEAError(f"Invalid {rating_type} rating: {value}")
                    mode[rating_type] = value

            # Recalculate RPN
            mode["rpn"] = mode["severity"] * mode["occurrence"] * mode["detection"]
            mode["risk_level"] = self._determine_risk_level(mode["rpn"])

            # Update record
            record["last_updated"] = datetime.now().isoformat()

            # Record risk change in history
            if fmea_id not in self.risk_history:
                self.risk_history[fmea_id] = []

            self.risk_history[fmea_id].append({
                "timestamp": datetime.now().isoformat(),
                "failure_mode": mode["failure_mode"],
                "old_rpn": mode.get("previous_rpn"),
                "new_rpn": mode["rpn"],
                "change_reason": "manual_update"
            })

            mode["previous_rpn"] = mode["rpn"]

            self.logger.info(f"RPN updated for failure mode in FMEA {fmea_id}")
            return {
                "fmea_id": fmea_id,
                "failure_mode": mode["failure_mode"],
                "updated_ratings": {
                    "severity": mode["severity"],
                    "occurrence": mode["occurrence"],
                    "detection": mode["detection"]
                },
                "new_rpn": mode["rpn"],
                "new_risk_level": mode["risk_level"]
            }

        except Exception as e:
            self.logger.error(f"RPN update failed: {e}")
            raise FMEAError(f"RPN update failed: {e}") from e