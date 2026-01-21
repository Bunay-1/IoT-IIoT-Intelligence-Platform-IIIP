"""
Automotive Quality Control Module

This module implements comprehensive automotive quality control including:
- Manufacturing quality inspection
- Defect detection and classification
- Quality metrics and KPIs
- Compliance standards verification
- Real-time monitoring
- Quality assurance workflows
"""

import json
import logging
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass

from utils.logging_config import get_logger

logger = get_logger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class QualityStandard(Enum):
    """Automotive quality standards."""
    ISO_9001 = "iso_9001"
    IATF_16949 = "iatf_16949"
    ISO_14001 = "iso_14001"
    ISO_45001 = "iso_45001"
    ISO_26262 = "iso_26262"


class DefectSeverity(Enum):
    """Defect severity levels."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    COSMETIC = "cosmetic"


class InspectionType(Enum):
    """Inspection types."""
    INCOMING = "incoming"
    IN_PROCESS = "in_process"
    FINAL = "final"
    RANDOM = "random"
    CUSTOMER_RETURN = "customer_return"


class ComponentType(Enum):
    """Component types."""
    ENGINE = "engine"
    TRANSMISSION = "transmission"
    BRAKES = "brakes"
    SUSPENSION = "suspension"
    ELECTRICAL = "electrical"
    BODY = "body"
    INTERIOR = "interior"
    EXTERIOR = "exterior"


@dataclass
class QualityInspection:
    """Quality inspection data structure."""
    inspection_id: str
    component_id: str
    component_type: ComponentType
    inspection_type: InspectionType
    inspector_id: str
    timestamp: datetime
    location: str
    standards: List[QualityStandard]
    measurements: Dict[str, float]
    tolerances: Dict[str, Tuple[float, float]]
    defects: List[Dict[str, Any]]
    pass_fail: bool
    quality_score: float
    comments: str


@dataclass
class DefectRecord:
    """Defect record data structure."""
    defect_id: str
    inspection_id: str
    component_id: str
    defect_type: str
    severity: DefectSeverity
    description: str
    location: str
    detected_at: datetime
    detected_by: str
    images: List[str]
    corrective_action: Optional[str]
    root_cause: Optional[str]
    status: str


class AutomotiveQualityControl:
    """Automotive quality control system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.inspections = {}
        self.defects = {}
        self.quality_metrics = {}
        self.compliance_records = {}
        self.inspection_templates = {}
        
    def _default_config(self) -> Dict[str, Any]:
        """Default quality control configuration."""
        return {
            "quality_standards": ["iatf_16949", "iso_9001", "iso_26262"],
            "inspection_frequency": {
                "incoming": "100%",
                "in_process": "10%",
                "final": "100%",
                "random": "5%"
            },
            "quality_thresholds": {
                "minimum_quality_score": 0.85,
                "critical_defect_tolerance": 0,
                "major_defect_tolerance": 0.02,
                "minor_defect_tolerance": 0.05
            },
            "tolerances": {
                "engine": {
                    "compression_ratio": (9.5, 10.5),
                    "oil_pressure": (20, 60),
                    "coolant_temp": (85, 105)
                },
                "brakes": {
                    "pad_thickness": (8, 12),
                    "rotor_thickness": (10, 12),
                    "brake_fluid_pressure": (800, 1200)
                },
                "electrical": {
                    "battery_voltage": (12.4, 12.8),
                    "alternator_output": (13.8, 14.4),
                    "resistance": (0, 0.1)
                }
            },
            "defect_classification": {
                "critical": ["safety_failure", "functional_failure"],
                "major": ["performance_degradation", "cosmetic_major"],
                "minor": ["cosmetic_minor", "fitment_issue"],
                "cosmetic": ["scratch", "dent", "color_mismatch"]
            },
            "reporting": {
                "daily_reports": True,
                "weekly_reports": True,
                "monthly_reports": True,
                "real_time_alerts": True
            }
        }
    
    def create_inspection(
        self,
        component_id: str,
        component_type: ComponentType,
        inspection_type: InspectionType,
        inspector_id: str,
        location: str,
        measurements: Dict[str, float],
        standards: Optional[List[QualityStandard]] = None
    ) -> Dict[str, Any]:
        """Create quality inspection."""
        try:
            # Generate inspection ID
            inspection_id = self._generate_inspection_id()
            
            # Get tolerances for component type
            tolerances = self.config["tolerances"].get(
                component_type.value,
                self._get_default_tolerances()
            )
            
            # Perform quality assessment
            quality_result = self._assess_quality(
                measurements, tolerances, component_type
            )
            
            # Create inspection record
            inspection = QualityInspection(
                inspection_id=inspection_id,
                component_id=component_id,
                component_type=component_type,
                inspection_type=inspection_type,
                inspector_id=inspector_id,
                timestamp=datetime.now(),
                location=location,
                standards=standards or [QualityStandard.IATF_16949],
                measurements=measurements,
                tolerances=tolerances,
                defects=quality_result["defects"],
                pass_fail=quality_result["pass_fail"],
                quality_score=quality_result["quality_score"],
                comments=quality_result["comments"]
            )
            
            self.inspections[inspection_id] = inspection
            
            # Record defects if any
            for defect in inspection.defects:
                self._record_defect(defect, inspection_id, component_id)
            
            # Update quality metrics
            self._update_quality_metrics(component_type, inspection)
            
            logger.info(f"Quality inspection created: {inspection_id}")
            
            return {
                "success": True,
                "inspection_id": inspection_id,
                "component_id": component_id,
                "component_type": component_type.value,
                "inspection_type": inspection_type.value,
                "pass_fail": inspection.pass_fail,
                "quality_score": inspection.quality_score,
                "defects_found": len(inspection.defects),
                "inspected_at": inspection.timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to create inspection: {e}")
            return {"error": f"Inspection creation failed: {e}"}
    
    def _generate_inspection_id(self) -> str:
        """Generate unique inspection ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = "".join([format(np.random.randint(0, 9), 'd') for _ in range(4)])
        return f"QI_{timestamp}_{random_suffix}"
    
    def _get_default_tolerances(self) -> Dict[str, Tuple[float, float]]:
        """Get default tolerances for unknown component types."""
        return {
            "dimension_1": (0, 100),
            "dimension_2": (0, 100),
            "weight": (0, 1000),
            "temperature": (-20, 150),
            "pressure": (0, 1000)
        }
    
    def _assess_quality(
        self,
        measurements: Dict[str, float],
        tolerances: Dict[str, Tuple[float, float]],
        component_type: ComponentType
    ) -> Dict[str, Any]:
        """Assess quality based on measurements and tolerances."""
        defects = []
        total_measurements = len(measurements)
        passed_measurements = 0
        
        # Check each measurement against tolerances
        for measurement_name, value in measurements.items():
            if measurement_name in tolerances:
                min_val, max_val = tolerances[measurement_name]
                
                if min_val <= value <= max_val:
                    passed_measurements += 1
                else:
                    # Create defect record
                    defect = {
                        "measurement": measurement_name,
                        "actual_value": value,
                        "expected_range": (min_val, max_val),
                        "deviation": min(abs(value - min_val), abs(value - max_val)),
                        "severity": self._determine_defect_severity(
                            measurement_name, value, min_val, max_val
                        )
                    }
                    defects.append(defect)
        
        # Calculate quality score
        quality_score = passed_measurements / total_measurements if total_measurements > 0 else 0
        
        # Determine pass/fail
        pass_fail = quality_score >= self.config["quality_thresholds"]["minimum_quality_score"]
        
        # Check for critical defects
        critical_defects = [d for d in defects if d["severity"] == DefectSeverity.CRITICAL]
        if critical_defects:
            pass_fail = False
        
        # Generate comments
        comments = self._generate_quality_comments(quality_score, defects, component_type)
        
        return {
            "defects": defects,
            "pass_fail": pass_fail,
            "quality_score": quality_score,
            "comments": comments
        }
    
    def _determine_defect_severity(
        self,
        measurement_name: str,
        actual_value: float,
        min_val: float,
        max_val: float
    ) -> DefectSeverity:
        """Determine defect severity based on deviation."""
        deviation = min(abs(actual_value - min_val), abs(actual_value - max_val))
        tolerance_range = max_val - min_val
        deviation_percentage = deviation / tolerance_range if tolerance_range > 0 else 0
        
        # Safety-critical measurements
        safety_critical = ["brake_pressure", "steering_angle", "airbag_pressure"]
        if measurement_name in safety_critical:
            return DefectSeverity.CRITICAL
        
        # Performance-critical measurements
        performance_critical = ["compression_ratio", "oil_pressure", "coolant_temp"]
        if measurement_name in performance_critical:
            if deviation_percentage > 0.2:
                return DefectSeverity.CRITICAL
            elif deviation_percentage > 0.1:
                return DefectSeverity.MAJOR
            else:
                return DefectSeverity.MINOR
        
        # General severity based on deviation
        if deviation_percentage > 0.5:
            return DefectSeverity.MAJOR
        elif deviation_percentage > 0.2:
            return DefectSeverity.MINOR
        else:
            return DefectSeverity.COSMETIC
    
    def _generate_quality_comments(
        self,
        quality_score: float,
        defects: List[Dict[str, Any]],
        component_type: ComponentType
    ) -> str:
        """Generate quality assessment comments."""
        if quality_score >= 0.95:
            return "Excellent quality - all measurements within specifications"
        elif quality_score >= 0.85:
            if defects:
                return f"Good quality - {len(defects)} minor deviations detected"
            else:
                return "Good quality - all measurements within specifications"
        elif quality_score >= 0.70:
            critical_defects = [d for d in defects if d["severity"] == DefectSeverity.CRITICAL]
            if critical_defects:
                return f"Poor quality - {len(critical_defects)} critical defects found"
            else:
                return f"Acceptable quality - {len(defects)} defects found"
        else:
            return f"Poor quality - {len(defects)} defects found, review required"
    
    def _record_defect(
        self,
        defect_data: Dict[str, Any],
        inspection_id: str,
        component_id: str
    ):
        """Record defect in system."""
        defect_id = self._generate_defect_id()
        
        defect = DefectRecord(
            defect_id=defect_id,
            inspection_id=inspection_id,
            component_id=component_id,
            defect_type=defect_data["measurement"],
            severity=defect_data["severity"],
            description=f"Measurement {defect_data['measurement']} out of tolerance: {defect_data['actual_value']} (expected: {defect_data['expected_range']})",
            location=f"Component: {component_id}",
            detected_at=datetime.now(),
            detected_by="inspection_system",
            images=[],
            corrective_action=None,
            root_cause=None,
            status="open"
        )
        
        self.defects[defect_id] = defect
    
    def _generate_defect_id(self) -> str:
        """Generate unique defect ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = "".join([format(np.random.randint(0, 9), 'd') for _ in range(4)])
        return f"DEF_{timestamp}_{random_suffix}"
    
    def _update_quality_metrics(
        self,
        component_type: ComponentType,
        inspection: QualityInspection
    ):
        """Update quality metrics for component type."""
        if component_type.value not in self.quality_metrics:
            self.quality_metrics[component_type.value] = {
                "total_inspections": 0,
                "passed_inspections": 0,
                "failed_inspections": 0,
                "total_defects": 0,
                "critical_defects": 0,
                "major_defects": 0,
                "minor_defects": 0,
                "cosmetic_defects": 0,
                "average_quality_score": 0.0,
                "last_updated": datetime.now()
            }
        
        metrics = self.quality_metrics[component_type.value]
        
        # Update inspection counts
        metrics["total_inspections"] += 1
        if inspection.pass_fail:
            metrics["passed_inspections"] += 1
        else:
            metrics["failed_inspections"] += 1
        
        # Update defect counts
        for defect in inspection.defects:
            metrics["total_defects"] += 1
            severity = defect["severity"]
            if severity == DefectSeverity.CRITICAL:
                metrics["critical_defects"] += 1
            elif severity == DefectSeverity.MAJOR:
                metrics["major_defects"] += 1
            elif severity == DefectSeverity.MINOR:
                metrics["minor_defects"] += 1
            elif severity == DefectSeverity.COSMETIC:
                metrics["cosmetic_defects"] += 1
        
        # Update average quality score
        total_score = metrics["average_quality_score"] * (metrics["total_inspections"] - 1)
        metrics["average_quality_score"] = (total_score + inspection.quality_score) / metrics["total_inspections"]
        
        metrics["last_updated"] = datetime.now()
    
    def update_defect_status(
        self,
        defect_id: str,
        status: str,
        corrective_action: Optional[str] = None,
        root_cause: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update defect status and information."""
        try:
            if defect_id not in self.defects:
                return {"error": f"Defect {defect_id} not found"}
            
            defect = self.defects[defect_id]
            defect.status = status
            
            if corrective_action:
                defect.corrective_action = corrective_action
            
            if root_cause:
                defect.root_cause = root_cause
            
            logger.info(f"Defect status updated: {defect_id} -> {status}")
            
            return {
                "success": True,
                "defect_id": defect_id,
                "status": status,
                "updated_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to update defect status: {e}")
            return {"error": f"Defect status update failed: {e}"}
    
    def generate_quality_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        component_types: Optional[List[ComponentType]] = None
    ) -> Dict[str, Any]:
        """Generate quality report."""
        try:
            # Filter inspections by date range
            filtered_inspections = [
                inspection for inspection in self.inspections.values()
                if start_date <= inspection.timestamp <= end_date
                and (not component_types or inspection.component_type in component_types)
            ]
            
            # Generate report based on type
            if report_type == "summary":
                report = self._generate_summary_report(filtered_inspections)
            elif report_type == "detailed":
                report = self._generate_detailed_report(filtered_inspections)
            elif report_type == "trends":
                report = self._generate_trends_report(filtered_inspections, start_date, end_date)
            elif report_type == "compliance":
                report = self._generate_compliance_report(filtered_inspections)
            else:
                return {"error": f"Unsupported report type: {report_type}"}
            
            report["report_type"] = report_type
            report["period"] = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            report["generated_at"] = datetime.now()
            
            logger.info(f"Quality report generated: {report_type}")
            
            return {
                "success": True,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Failed to generate quality report: {e}")
            return {"error": f"Report generation failed: {e}"}
    
    def _generate_summary_report(self, inspections: List[QualityInspection]) -> Dict[str, Any]:
        """Generate summary quality report."""
        total_inspections = len(inspections)
        if total_inspections == 0:
            return {"message": "No inspections found in specified period"}
        
        passed_inspections = sum(1 for insp in inspections if insp.pass_fail)
        failed_inspections = total_inspections - passed_inspections
        
        pass_rate = passed_inspections / total_inspections
        avg_quality_score = sum(insp.quality_score for insp in inspections) / total_inspections
        
        # Component type breakdown
        component_stats = {}
        for inspection in inspections:
            comp_type = inspection.component_type.value
            if comp_type not in component_stats:
                component_stats[comp_type] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "avg_quality": 0
                }
            
            component_stats[comp_type]["total"] += 1
            if inspection.pass_fail:
                component_stats[comp_type]["passed"] += 1
            else:
                component_stats[comp_type]["failed"] += 1
        
        # Calculate averages for each component type
        for comp_type, stats in component_stats.items():
            comp_inspections = [insp for insp in inspections if insp.component_type.value == comp_type]
            stats["avg_quality"] = sum(insp.quality_score for insp in comp_inspections) / len(comp_inspections)
        
        return {
            "total_inspections": total_inspections,
            "passed_inspections": passed_inspections,
            "failed_inspections": failed_inspections,
            "pass_rate": pass_rate,
            "average_quality_score": avg_quality_score,
            "component_breakdown": component_stats
        }
    
    def _generate_detailed_report(self, inspections: List[QualityInspection]) -> Dict[str, Any]:
        """Generate detailed quality report."""
        inspection_details = []
        
        for inspection in inspections:
            detail = {
                "inspection_id": inspection.inspection_id,
                "component_id": inspection.component_id,
                "component_type": inspection.component_type.value,
                "inspection_type": inspection.inspection_type.value,
                "inspector_id": inspection.inspector_id,
                "timestamp": inspection.timestamp.isoformat(),
                "location": inspection.location,
                "pass_fail": inspection.pass_fail,
                "quality_score": inspection.quality_score,
                "measurements": inspection.measurements,
                "defects": inspection.defects,
                "comments": inspection.comments
            }
            inspection_details.append(detail)
        
        return {
            "inspection_count": len(inspection_details),
            "inspections": inspection_details
        }
    
    def _generate_trends_report(
        self,
        inspections: List[QualityInspection],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate trends analysis report."""
        # Group inspections by day
        daily_data = {}
        current_date = start_date
        
        while current_date <= end_date:
            day_inspections = [
                insp for insp in inspections
                if insp.timestamp.date() == current_date.date()
            ]
            
            if day_inspections:
                daily_data[current_date.strftime("%Y-%m-%d")] = {
                    "inspections": len(day_inspections),
                    "pass_rate": sum(1 for insp in day_inspections if insp.pass_fail) / len(day_inspections),
                    "avg_quality": sum(insp.quality_score for insp in day_inspections) / len(day_inspections),
                    "defects": sum(len(insp.defects) for insp in day_inspections)
                }
            
            current_date += timedelta(days=1)
        
        # Calculate trends
        dates = sorted(daily_data.keys())
        if len(dates) >= 2:
            first_day = daily_data[dates[0]]
            last_day = daily_data[dates[-1]]
            
            pass_rate_trend = last_day["pass_rate"] - first_day["pass_rate"]
            quality_trend = last_day["avg_quality"] - first_day["avg_quality"]
            defects_trend = last_day["defects"] - first_day["defects"]
        else:
            pass_rate_trend = 0
            quality_trend = 0
            defects_trend = 0
        
        return {
            "daily_data": daily_data,
            "trends": {
                "pass_rate_trend": pass_rate_trend,
                "quality_score_trend": quality_trend,
                "defects_trend": defects_trend
            }
        }
    
    def _generate_compliance_report(self, inspections: List[QualityInspection]) -> Dict[str, Any]:
        """Generate compliance report."""
        compliance_scores = {}
        
        for standard in QualityStandard:
            standard_inspections = [
                insp for insp in inspections
                if standard in insp.standards
            ]
            
            if standard_inspections:
                passed = sum(1 for insp in standard_inspections if insp.pass_fail)
                compliance_rate = passed / len(standard_inspections)
                
                compliance_scores[standard.value] = {
                    "total_inspections": len(standard_inspections),
                    "passed_inspections": passed,
                    "compliance_rate": compliance_rate,
                    "status": "compliant" if compliance_rate >= 0.95 else "non_compliant"
                }
        
        return {
            "compliance_scores": compliance_scores,
            "overall_compliance": all(
                score["status"] == "compliant" for score in compliance_scores.values()
            )
        }
    
    def get_quality_alerts(self) -> Dict[str, Any]:
        """Get quality alerts and notifications."""
        alerts = []
        
        # Check for critical defects
        critical_defects = [
            defect for defect in self.defects.values()
            if defect.severity == DefectSeverity.CRITICAL and defect.status == "open"
        ]
        
        if critical_defects:
            alerts.append({
                "type": "critical_defects",
                "severity": "high",
                "message": f"{len(critical_defects)} critical defects require immediate attention",
                "count": len(critical_defects),
                "timestamp": datetime.now()
            })
        
        # Check for low quality scores
        for comp_type, metrics in self.quality_metrics.items():
            if metrics["average_quality_score"] < self.config["quality_thresholds"]["minimum_quality_score"]:
                alerts.append({
                    "type": "low_quality_score",
                    "severity": "medium",
                    "message": f"Low quality score for {comp_type}: {metrics['average_quality_score']:.2f}",
                    "component_type": comp_type,
                    "score": metrics["average_quality_score"],
                    "timestamp": datetime.now()
                })
        
        # Check for high defect rates
        for comp_type, metrics in self.quality_metrics.items():
            if metrics["total_inspections"] > 0:
                defect_rate = metrics["total_defects"] / metrics["total_inspections"]
                if defect_rate > 0.1:  # 10% defect rate
                    alerts.append({
                        "type": "high_defect_rate",
                        "severity": "medium",
                        "message": f"High defect rate for {comp_type}: {defect_rate:.2%}",
                        "component_type": comp_type,
                        "defect_rate": defect_rate,
                        "timestamp": datetime.now()
                    })
        
        return {
            "alerts": alerts,
            "total_alerts": len(alerts),
            "generated_at": datetime.now()
        }
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get overall quality metrics."""
        total_inspections = sum(metrics["total_inspections"] for metrics in self.quality_metrics.values())
        total_passed = sum(metrics["passed_inspections"] for metrics in self.quality_metrics.values())
        
        overall_pass_rate = total_passed / total_inspections if total_inspections > 0 else 0
        
        return {
            "total_inspections": total_inspections,
            "total_passed": total_passed,
            "overall_pass_rate": overall_pass_rate,
            "total_defects": sum(metrics["total_defects"] for metrics in self.quality_metrics.values()),
            "component_metrics": self.quality_metrics,
            "active_defects": len([d for d in self.defects.values() if d.status == "open"]),
            "quality_standards": self.config["quality_standards"]
        }


# Global automotive quality control instance
automotive_quality_control = AutomotiveQualityControl()
automotive_quality = automotive_quality_control


class StatisticalProcessControl:
    """Клас за извършване на Статистически Процесен Контрол (SPC) за Dash GUI."""

    def __init__(self, data: pd.DataFrame, measurement_col: str, subgroup_size: int = 5):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Данните трябва да бъдат pandas DataFrame.")
        if measurement_col not in data.columns:
            raise ValueError(f"Колоната '{measurement_col}' не е намерена в DataFrame-а.")

        self.data = data
        self.measurement_col = measurement_col
        self.subgroup_size = subgroup_size

        # Константи за контролни карти
        self.control_chart_constants = {
            2: {'A2': 1.880, 'D3': 0, 'D4': 3.267}, 3: {'A2': 1.023, 'D3': 0, 'D4': 2.574},
            4: {'A2': 0.729, 'D3': 0, 'D4': 2.282}, 5: {'A2': 0.577, 'D3': 0, 'D4': 2.114},
            6: {'A2': 0.483, 'D3': 0, 'D4': 2.004}, 7: {'A2': 0.419, 'D3': 0.076, 'D4': 1.924},
            8: {'A2': 0.373, 'D3': 0.136, 'D4': 1.864}, 9: {'A2': 0.337, 'D3': 0.184, 'D4': 1.816},
            10: {'A2': 0.308, 'D3': 0.223, 'D4': 1.777},
        }

        if self.subgroup_size not in self.control_chart_constants:
            raise ValueError(f"Размер на подгрупа {self.subgroup_size} не се поддържа.")

        self._prepare_subgroups()
        self.limits = {}

    def _prepare_subgroups(self):
        """Разделя данните на подгрупи."""
        self.data['subgroup'] = np.arange(len(self.data)) // self.subgroup_size
        self.subgroups = self.data.groupby('subgroup')[self.measurement_col]

        self.x_bars = self.subgroups.mean()
        self.ranges = self.subgroups.apply(lambda x: x.max() - x.min())

    def calculate_control_limits(self):
        """Изчислява контролните лимити за X-bar и R карти."""
        cl_x_bar = self.x_bars.mean()
        cl_r = self.ranges.mean()

        constants = self.control_chart_constants[self.subgroup_size]
        A2, D3, D4 = constants['A2'], constants['D3'], constants['D4']

        ucl_x_bar = cl_x_bar + A2 * cl_r
        lcl_x_bar = cl_x_bar - A2 * cl_r
        ucl_r = D4 * cl_r
        lcl_r = D3 * cl_r

        self.limits = {
            'x_bar': {'UCL': ucl_x_bar, 'CL': cl_x_bar, 'LCL': lcl_x_bar},
            'r_chart': {'UCL': ucl_r, 'CL': cl_r, 'LCL': lcl_r},
        }

    def analyze(self) -> pd.DataFrame:
        """Анализира данните и идентифицира точки извън контрол."""
        if not self.limits:
            self.calculate_control_limits()

        x_bar_out_of_control = (self.x_bars < self.limits['x_bar']['LCL']) | (self.x_bars > self.limits['x_bar']['UCL'])
        r_chart_out_of_control = (self.ranges < self.limits['r_chart']['LCL']) | (self.ranges > self.limits['r_chart']['UCL'])

        analysis_df = pd.DataFrame({
            'Subgroup': self.x_bars.index,
            'X_bar': self.x_bars,
            'Range': self.ranges,
            'X_bar_OutOfControl': x_bar_out_of_control,
            'R_chart_OutOfControl': r_chart_out_of_control
        })
        return analysis_df

    def plot_x_bar_chart(self) -> go.Figure:
        """Генерира X-bar контролна карта с Plotly."""
        fig = go.Figure()

        # Линии на контролните лимити
        fig.add_hline(y=self.limits['x_bar']['UCL'], line_dash="dash", line_color="red", annotation_text="UCL")
        fig.add_hline(y=self.limits['x_bar']['CL'], line_dash="solid", line_color="green", annotation_text="CL")
        fig.add_hline(y=self.limits['x_bar']['LCL'], line_dash="dash", line_color="red", annotation_text="LCL")

        # Данни
        fig.add_trace(go.Scatter(x=self.x_bars.index, y=self.x_bars, mode='lines+markers', name='Средно (X-bar)'))

        # Маркиране на точки извън контрол
        outliers = self.x_bars[(self.x_bars < self.limits['x_bar']['LCL']) | (self.x_bars > self.limits['x_bar']['UCL'])]
        fig.add_trace(go.Scatter(x=outliers.index, y=outliers, mode='markers', marker_symbol='x', marker_color='red', marker_size=10, name='Извън контрол'))

        fig.update_layout(title_text='X-bar Control Chart', xaxis_title='Номер на подгрупа', yaxis_title='Средна стойност')
        return fig

    def plot_r_chart(self) -> go.Figure:
        """Генерира R-Chart контролна карта с Plotly."""
        fig = go.Figure()

        # Линии на контролните лимити
        fig.add_hline(y=self.limits['r_chart']['UCL'], line_dash="dash", line_color="red", annotation_text="UCL")
        fig.add_hline(y=self.limits['r_chart']['CL'], line_dash="solid", line_color="green", annotation_text="CL")
        fig.add_hline(y=self.limits['r_chart']['LCL'], line_dash="dash", line_color="red", annotation_text="LCL")

        # Данни
        fig.add_trace(go.Scatter(x=self.ranges.index, y=self.ranges, mode='lines+markers', name='Обхват (R)'))

        # Маркиране на точки извън контрол
        outliers = self.ranges[(self.ranges < self.limits['r_chart']['LCL']) | (self.ranges > self.limits['r_chart']['UCL'])]
        fig.add_trace(go.Scatter(x=outliers.index, y=outliers, mode='markers', marker_symbol='x', marker_color='red', marker_size=10, name='Извън контрол'))

        fig.update_layout(title_text='R-Chart (Range Control Chart)', xaxis_title='Номер на подгрупа', yaxis_title='Обхват')
        return fig


if __name__ == '__main__':

    def generate_spc_data_single_col(num_points, mean=10.0, std_dev=0.5, shift_point=None, shift_value=0.0):
        """Генерира симулирани данни за SPC анализ в една колона."""
        data = np.random.normal(loc=mean, scale=std_dev, size=num_points)
        if shift_point is not None:
            data[shift_point:] += shift_value
        return pd.DataFrame({'measurement': data})

    # --- Демонстрация на Статистически Процесен Контрол (SPC) ---
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ НА СТАТИСТИЧЕСКИ ПРОЦЕСЕН КОНТРОЛ (SPC)")
    print("="*50 + "\n")

    # 1. Генериране на данни (150 измервания, което е 30 подгрупи по 5)
    # Промяна в процеса настъпва след 100-тната точка
    process_data = generate_spc_data_single_col(150, mean=25.0, std_dev=1.0, shift_point=100, shift_value=1.5)
    logger.info(f"Генерирани са {len(process_data)} измервания с аномалия след 100-тната точка.")

    # 2. Инициализация на SPC класа
    try:
        spc = StatisticalProcessControl(process_data, 'measurement', subgroup_size=5)

        # 3. Изчисляване на контролните лимити
        spc.calculate_control_limits()
        limits = spc.limits
        logger.info(f"Изчислени X-bar лимити: LCL={limits['x_bar']['LCL']:.3f}, CL={limits['x_bar']['CL']:.3f}, UCL={limits['x_bar']['UCL']:.3f}")
        logger.info(f"Изчислени R-chart лимити: LCL={limits['r_chart']['LCL']:.3f}, CL={limits['r_chart']['CL']:.3f}, UCL={limits['r_chart']['UCL']:.3f}")

        # 4. Анализ на процеса
        analysis_results = spc.analyze()
        unstable_points = analysis_results[analysis_results['X_bar_OutOfControl'] | analysis_results['R_chart_OutOfControl']]

        if unstable_points.empty:
            logger.info("Процесът е СТАБИЛЕН.")
        else:
            logger.warning("Процесът е НЕСТАБИЛЕН. Открити са точки извън контрол!")
            print(unstable_points)

        # 5. Генериране и показване на графики (в среда, която го поддържа)
        logger.info("Генериране на Plotly графики. В интерактивна среда (напр. Jupyter) те ще се покажат.")
        x_bar_fig = spc.plot_x_bar_chart()
        r_chart_fig = spc.plot_r_chart()

        # За демонстрационни цели, можете да ги запишете в HTML файлове
        x_bar_fig.write_html("x_bar_chart.html")
        r_chart_fig.write_html("r_chart.html")
        logger.info("Графиките са запазени като x_bar_chart.html и r_chart.html")

    except (ValueError, TypeError) as e:
        logger.error(f"Грешка при SPC анализ: {e}")

    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯТА НА SPC ПРИКЛЮЧИ")
    print("="*50 + "\n")
