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
import matplotlib.pyplot as plt
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
    """Клас за извършване на Статистически Процесен Контрол (SPC)."""

    def __init__(self):
        # Константи за контролни карти (за n <= 10)
        self.control_chart_constants = {
            2: {'A2': 1.880, 'D3': 0, 'D4': 3.267},
            3: {'A2': 1.023, 'D3': 0, 'D4': 2.574},
            4: {'A2': 0.729, 'D3': 0, 'D4': 2.282},
            5: {'A2': 0.577, 'D3': 0, 'D4': 2.114},
            6: {'A2': 0.483, 'D3': 0, 'D4': 2.004},
            7: {'A2': 0.419, 'D3': 0.076, 'D4': 1.924},
            8: {'A2': 0.373, 'D3': 0.136, 'D4': 1.864},
            9: {'A2': 0.337, 'D3': 0.184, 'D4': 1.816},
            10: {'A2': 0.308, 'D3': 0.223, 'D4': 1.777},
        }

    def calculate_control_limits(self, data: pd.DataFrame):
        """
        Изчислява контролните лимити за X-bar и R карти.
        Args:
            data (pd.DataFrame): DataFrame с измервания, където всяка колона е измерване, а всеки ред е извадка.
        Returns:
            dict: Речник, съдържащ изчислените контролни лимити.
        """
        n = data.shape[1]  # Размер на извадката
        if n not in self.control_chart_constants:
            raise ValueError(f"Размер на извадката {n} не се поддържа. Поддържат се стойности от 2 до 10.")

        # Изчисляване на средните стойности (X-bar) и обхватите (R) за всяка извадка
        x_bars = data.mean(axis=1)
        ranges = data.max(axis=1) - data.min(axis=1)

        # Изчисляване на централните линии
        cl_x_bar = x_bars.mean()
        cl_r = ranges.mean()

        # Вземане на константите
        constants = self.control_chart_constants[n]
        A2, D3, D4 = constants['A2'], constants['D3'], constants['D4']

        # Изчисляване на контролните лимити
        ucl_x_bar = cl_x_bar + A2 * cl_r
        lcl_x_bar = cl_x_bar - A2 * cl_r
        ucl_r = D4 * cl_r
        lcl_r = D3 * cl_r

        limits = {
            'x_bar': {'UCL': ucl_x_bar, 'CL': cl_x_bar, 'LCL': lcl_x_bar},
            'r_chart': {'UCL': ucl_r, 'CL': cl_r, 'LCL': lcl_r},
            'x_bars': x_bars,
            'ranges': ranges
        }
        return limits

    def analyze_process_data(self, new_data: pd.DataFrame, limits: dict):
        """
        Анализира нови данни спрямо изчислените контролни лимити.
        Args:
            new_data (pd.DataFrame): Нови измервания за анализ.
            limits (dict): Контролни лимити, изчислени от `calculate_control_limits`.
        Returns:
            dict: Резултати от анализа, включително точки извън контрол.
        """
        x_bars = new_data.mean(axis=1)
        ranges = new_data.max(axis=1) - new_data.min(axis=1)

        # Проверка за точки извън контрол
        x_bar_out_of_control = x_bars[(x_bars < limits['x_bar']['LCL']) | (x_bars > limits['x_bar']['UCL'])]
        r_chart_out_of_control = ranges[(ranges < limits['r_chart']['LCL']) | (ranges > limits['r_chart']['UCL'])]

        results = {
            'x_bar_data': x_bars,
            'r_chart_data': ranges,
            'x_bar_out_of_control': x_bar_out_of_control,
            'r_chart_out_of_control': r_chart_out_of_control,
            'is_stable': len(x_bar_out_of_control) == 0 and len(r_chart_out_of_control) == 0
        }
        return results

    def plot_control_charts(self, limits: dict, analysis_results: dict, filename_prefix: str):
        """
        Генерира и запазва графики на контролните карти.
        """
        plt.style.use('seaborn-v0_8-whitegrid')

        # --- X-bar Карта ---
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(analysis_results['x_bar_data'].index, analysis_results['x_bar_data'], marker='o', linestyle='-', label='Средно (X-bar)')
        ax.axhline(limits['x_bar']['UCL'], color='red', linestyle='--', label='UCL')
        ax.axhline(limits['x_bar']['CL'], color='green', linestyle='-', label='CL')
        ax.axhline(limits['x_bar']['LCL'], color='red', linestyle='--', label='LCL')

        # Маркиране на точки извън контрол
        outliers = analysis_results['x_bar_out_of_control']
        if not outliers.empty:
            ax.scatter(outliers.index, outliers.values, color='red', s=100, zorder=5, label='Извън контрол')

        ax.set_title('X-bar Control Chart')
        ax.set_xlabel('Номер на извадка')
        ax.set_ylabel('Средна стойност')
        ax.legend()
        plt.tight_layout()
        x_bar_filename = f"{filename_prefix}_x_bar_chart.png"
        plt.savefig(x_bar_filename)
        plt.close()
        logger.info(f"X-bar картата е запазена в {x_bar_filename}")

        # --- R Карта ---
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(analysis_results['r_chart_data'].index, analysis_results['r_chart_data'], marker='o', linestyle='-', label='Обхват (R)')
        ax.axhline(limits['r_chart']['UCL'], color='red', linestyle='--', label='UCL')
        ax.axhline(limits['r_chart']['CL'], color='green', linestyle='-', label='CL')
        ax.axhline(limits['r_chart']['LCL'], color='red', linestyle='--', label='LCL')

        # Маркиране на точки извън контрол
        outliers = analysis_results['r_chart_out_of_control']
        if not outliers.empty:
            ax.scatter(outliers.index, outliers.values, color='red', s=100, zorder=5, label='Извън контрол')

        ax.set_title('R-Chart (Range Control Chart)')
        ax.set_xlabel('Номер на извадка')
        ax.set_ylabel('Обхват')
        ax.legend()
        plt.tight_layout()
        r_chart_filename = f"{filename_prefix}_r_chart.png"
        plt.savefig(r_chart_filename)
        plt.close()
        logger.info(f"R картата е запазена в {r_chart_filename}")

        return x_bar_filename, r_chart_filename


if __name__ == '__main__':

    def generate_spc_data(num_samples, sample_size, mean=10.0, std_dev=0.5, shift=0.0):
        """Генерира симулирани данни за SPC анализ."""
        data = np.random.normal(loc=mean + shift, scale=std_dev, size=(num_samples, sample_size))
        return pd.DataFrame(data, columns=[f'meas_{i+1}' for i in range(sample_size)])

    # --- Демонстрация на Статистически Процесен Контрол (SPC) ---
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ НА СТАТИСТИЧЕСКИ ПРОЦЕСЕН КОНТРОЛ (SPC)")
    print("="*50 + "\n")

    # 1. Инициализация на SPC модула
    spc = StatisticalProcessControl()

    # 2. Генериране на стабилни данни за калибрация
    # 20 извадки с по 5 измервания всяка
    sample_size = 5
    stable_data = generate_spc_data(num_samples=20, sample_size=sample_size, mean=25.0, std_dev=1.0)
    logger.info(f"Генерирани са {len(stable_data)} стабилни извадки за изчисляване на контролни лимити.")

    # 3. Изчисляване на контролните лимити
    try:
        control_limits = spc.calculate_control_limits(stable_data)
        logger.info(f"Изчислени X-bar лимити: LCL={control_limits['x_bar']['LCL']:.3f}, CL={control_limits['x_bar']['CL']:.3f}, UCL={control_limits['x_bar']['UCL']:.3f}")
        logger.info(f"Изчислени R-chart лимити: LCL={control_limits['r_chart']['LCL']:.3f}, CL={control_limits['r_chart']['CL']:.3f}, UCL={control_limits['r_chart']['UCL']:.3f}")

        # 4. Генериране на нови данни с дефекти (промяна в процеса)
        # 15 нови извадки, като последните 5 имат променена средна стойност
        new_stable_data = generate_spc_data(num_samples=10, sample_size=sample_size, mean=25.0, std_dev=1.0)
        shifted_data = generate_spc_data(num_samples=5, sample_size=sample_size, mean=25.0, std_dev=1.0, shift=2.5) # Промяна!
        process_data = pd.concat([new_stable_data, shifted_data], ignore_index=True)
        logger.info(f"Генерирани са {len(process_data)} нови извадки, някои от които с аномалии.")

        # 5. Анализ на новите данни
        analysis = spc.analyze_process_data(process_data, control_limits)

        if analysis['is_stable']:
            logger.info("Процесът е СТАБИЛЕН. Не са открити точки извън контрол.")
        else:
            logger.warning("Процесът е НЕСТАБИЛЕН. Открити са точки извън контрол!")
            if not analysis['x_bar_out_of_control'].empty:
                print("\nТочки извън контрол (X-bar):")
                print(analysis['x_bar_out_of_control'])
            if not analysis['r_chart_out_of_control'].empty:
                print("\nТочки извън контрол (R-chart):")
                print(analysis['r_chart_out_of_control'])

        # 6. Генериране на визуални отчети (контролни карти)
        spc.plot_control_charts(control_limits, analysis, filename_prefix="spc_analysis_report")

    except ValueError as e:
        logger.error(f"Грешка при SPC анализ: {e}")

    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯТА НА SPC ПРИКЛЮЧИ")
    print("="*50 + "\n")
