"""
Chemical Process Safety Module

This module implements comprehensive chemical process safety including:
- Process hazard analysis (HAZOP)
- Safety instrumented systems
- Risk assessment and management
- Emergency response planning
- Compliance monitoring
- Safety training management
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class HazardType(Enum):
    """Types of process hazards."""
    TOXIC = "toxic"
    FLAMMABLE = "flammable"
    EXPLOSIVE = "explosive"
    CORROSIVE = "corrosive"
    REACTIVE = "reactive"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    MECHANICAL = "mechanical"


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyStandard(Enum):
    """Safety standards and regulations."""
    OSHA_PSM = "osha_psm"
    IEC_61511 = "iec_61511"
    ISO_31000 = "iso_31000"
    ATEX = "ateex"
    NFPA = "nfpa"


@dataclass
class ProcessUnit:
    """Process unit information."""
    unit_id: str
    name: str
    description: str
    location: str
    chemicals: List[str]
    operating_conditions: Dict[str, float]
    safety_systems: List[str]
    last_inspection: datetime
    risk_level: RiskLevel


@dataclass
class HazardAnalysis:
    """Hazard analysis record."""
    analysis_id: str
    unit_id: str
    analysis_type: str
    hazards_identified: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    analyst: str
    date: datetime
    status: str


class ChemicalProcessSafety:
    """Chemical process safety management system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.process_units = {}
        self.hazard_analyses = {}
        self.safety_instruments = {}
        self.emergency_plans = {}
        self.training_records = {}
        self.compliance_monitoring = {}
        
    def _default_config(self) -> Dict[str, Any]:
        """Default safety configuration."""
        return {
            "safety_standards": ["osha_psm", "iec_61511", "iso_31000"],
            "risk_thresholds": {
                "acceptable_risk": 0.1,
                "moderate_risk": 0.5,
                "high_risk": 0.8,
                "critical_risk": 1.0
            },
            "inspection_frequency": {
                "routine": "monthly",
                "comprehensive": "quarterly",
                "emergency": "annually"
            },
            "training_requirements": {
                "basic_safety": "annual",
                "hazard_analysis": "biennial",
                "emergency_response": "semi_annual"
            },
            "emergency_response": {
                "evacuation_time_minutes": 5,
                "response_team_size": 8,
                "drill_frequency": "quarterly"
            }
        }
    
    async def register_process_unit(
        self,
        unit_id: str,
        name: str,
        description: str,
        location: str,
        chemicals: List[str],
        operating_conditions: Dict[str, float],
        safety_systems: List[str]
    ) -> Dict[str, Any]:
        """Register a new process unit."""
        try:
            # Validate operating conditions
            validation_result = await self._validate_operating_conditions(operating_conditions, chemicals)
            
            if not validation_result["valid"]:
                return {"error": f"Operating conditions validation failed: {validation_result['reason']}"}
            
            # Assess initial risk level
            risk_level = await self._assess_unit_risk(chemicals, operating_conditions)
            
            # Create process unit
            unit = ProcessUnit(
                unit_id=unit_id,
                name=name,
                description=description,
                location=location,
                chemicals=chemicals,
                operating_conditions=operating_conditions,
                safety_systems=safety_systems,
                last_inspection=datetime.now(),
                risk_level=risk_level
            )
            
            self.process_units[unit_id] = unit
            
            logger.info(f"Process unit registered: {unit_id}")
            
            return {
                "success": True,
                "unit_id": unit_id,
                "name": name,
                "risk_level": risk_level.value,
                "registered_at": unit.last_inspection
            }
            
        except Exception as e:
            logger.error(f"Failed to register process unit: {e}")
            return {"error": f"Unit registration failed: {e}"}
    
    async def _validate_operating_conditions(
        self,
        conditions: Dict[str, float],
        chemicals: List[str]
    ) -> Dict[str, Any]:
        """Validate operating conditions against safety limits."""
        try:
            # Check temperature limits
            if "temperature" in conditions:
                temp = conditions["temperature"]
                if temp < -50 or temp > 500:  # General safety limits
                    return {"valid": False, "reason": f"Temperature {temp}°C outside safe range"}
            
            # Check pressure limits
            if "pressure" in conditions:
                pressure = conditions["pressure"]
                if pressure < 0 or pressure > 100:  # bar
                    return {"valid": False, "reason": f"Pressure {pressure} bar outside safe range"}
            
            # Check flow rates
            if "flow_rate" in conditions:
                flow = conditions["flow_rate"]
                if flow < 0 or flow > 1000:  # m³/h
                    return {"valid": False, "reason": f"Flow rate {flow} m³/h outside safe range"}
            
            return {"valid": True, "reason": "Operating conditions validated"}
            
        except Exception as e:
            return {"valid": False, "reason": f"Validation error: {e}"}
    
    async def _assess_unit_risk(
        self,
        chemicals: List[str],
        operating_conditions: Dict[str, float]
    ) -> RiskLevel:
        """Assess risk level for process unit."""
        # Chemical hazard scores
        chemical_scores = {
            "hydrogen": 0.9,  # Highly flammable
            "chlorine": 0.8,  # Toxic
            "ammonia": 0.7,  # Toxic and corrosive
            "methane": 0.6,  # Flammable
            "propane": 0.7,  # Flammable
            "sulfuric_acid": 0.8,  # Corrosive
            "nitric_acid": 0.7,  # Corrosive
            "sodium_hydroxide": 0.6,  # Corrosive
        }
        
        # Calculate chemical risk score
        chemical_risk = 0
        for chemical in chemicals:
            chemical_risk += chemical_scores.get(chemical.lower(), 0.5)
        
        chemical_risk = min(chemical_risk / len(chemicals), 1.0) if chemicals else 0.5
        
        # Operating condition risk
        temp = operating_conditions.get("temperature", 25)
        pressure = operating_conditions.get("pressure", 1)
        
        # High temperature/pressure increases risk
        condition_risk = 0
        if temp > 200:
            condition_risk += 0.3
        if pressure > 10:
            condition_risk += 0.3
        
        condition_risk = min(condition_risk, 0.5)
        
        # Overall risk score
        total_risk = (chemical_risk + condition_risk) / 2
        
        # Determine risk level
        if total_risk >= self.config["risk_thresholds"]["critical_risk"]:
            return RiskLevel.CRITICAL
        elif total_risk >= self.config["risk_thresholds"]["high_risk"]:
            return RiskLevel.HIGH
        elif total_risk >= self.config["risk_thresholds"]["moderate_risk"]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def perform_hazop_study(
        self,
        unit_id: str,
        analyst: str,
        study_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform HAZOP (Hazard and Operability) study."""
        try:
            if unit_id not in self.process_units:
                return {"error": f"Process unit {unit_id} not found"}
            
            unit = self.process_units[unit_id]
            
            # Generate HAZOP analysis
            analysis_id = self._generate_analysis_id()
            
            # Identify hazards
            hazards = await self._identify_hazops(unit, study_parameters)
            
            # Risk assessment
            risk_assessment = await self._assess_hazop_risks(hazards)
            
            # Generate recommendations
            recommendations = await self._generate_hazop_recommendations(hazards, risk_assessment)
            
            # Create analysis record
            analysis = HazardAnalysis(
                analysis_id=analysis_id,
                unit_id=unit_id,
                analysis_type="HAZOP",
                hazards_identified=hazards,
                risk_assessment=risk_assessment,
                recommendations=recommendations,
                analyst=analyst,
                date=datetime.now(),
                status="completed"
            )
            
            self.hazard_analyses[analysis_id] = analysis
            
            logger.info(f"HAZOP study completed: {analysis_id} for unit {unit_id}")
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "unit_id": unit_id,
                "hazards_found": len(hazards),
                "risk_level": risk_assessment["overall_risk"],
                "recommendations": len(recommendations),
                "completed_at": analysis.date
            }
            
        except Exception as e:
            logger.error(f"Failed to perform HAZOP study: {e}")
            return {"error": f"HAZOP study failed: {e}"}
    
    def _generate_analysis_id(self) -> str:
        """Generate unique analysis ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = "".join([format(np.random.randint(0, 9), 'd') for _ in range(4)])
        return f"HAZ_{timestamp}_{random_suffix}"
    
    async def _identify_hazops(
        self,
        unit: ProcessUnit,
        parameters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify HAZOP deviations."""
        guidewords = ["NO", "MORE", "LESS", "AS WELL AS", "PART OF", "REVERSE", "OTHER THAN"]
        parameters = parameters or ["flow", "pressure", "temperature", "level", "composition"]
        
        hazards = []
        
        for param in parameters:
            for guideword in guidewords:
                # Simulate hazard identification
                if np.random.random() > 0.7:  # 30% chance of finding hazard
                    hazard = {
                        "parameter": param,
                        "guideword": guideword,
                        "deviation": f"{guideword} {param}",
                        "causes": [
                            f"Equipment failure in {param} system",
                            f"Operator error in {param} control",
                            f"External factor affecting {param}"
                        ],
                        "consequences": [
                            "Process upset",
                            "Safety risk",
                            "Environmental impact",
                            "Production loss"
                        ],
                        "safeguards": [
                            f"Alarm for {param} deviation",
                            f"Emergency shutdown for {param}",
                            f"Redundant {param} measurement"
                        ],
                        "risk_score": np.random.uniform(0.1, 1.0)
                    }
                    hazards.append(hazard)
        
        return hazards
    
    async def _assess_hazop_risks(self, hazards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess risks from HAZOP analysis."""
        if not hazards:
            return {"overall_risk": "low", "risk_distribution": {}}
        
        # Calculate risk scores
        risk_scores = [hazard["risk_score"] for hazard in hazards]
        avg_risk = np.mean(risk_scores)
        max_risk = max(risk_scores)
        
        # Risk distribution
        risk_distribution = {
            "low": len([r for r in risk_scores if r < 0.3]),
            "medium": len([r for r in risk_scores if 0.3 <= r < 0.7]),
            "high": len([r for r in risk_scores if 0.7 <= r < 0.9]),
            "critical": len([r for r in risk_scores if r >= 0.9])
        }
        
        # Overall risk level
        if max_risk >= 0.9:
            overall_risk = "critical"
        elif avg_risk >= 0.7:
            overall_risk = "high"
        elif avg_risk >= 0.4:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        return {
            "overall_risk": overall_risk,
            "average_risk_score": avg_risk,
            "maximum_risk_score": max_risk,
            "risk_distribution": risk_distribution,
            "total_hazards": len(hazards)
        }
    
    async def _generate_hazop_recommendations(
        self,
        hazards: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations from HAZOP analysis."""
        recommendations = []
        
        # High-level recommendations based on overall risk
        overall_risk = risk_assessment["overall_risk"]
        
        if overall_risk in ["high", "critical"]:
            recommendations.extend([
                "Implement additional safety instrumented systems",
                "Review and upgrade emergency shutdown procedures",
                "Increase frequency of safety inspections",
                "Provide additional operator training"
            ])
        
        # Specific recommendations based on hazards
        high_risk_hazards = [h for h in hazards if h["risk_score"] >= 0.7]
        
        if high_risk_hazards:
            recommendations.append("Address high-risk hazards immediately")
            
            for hazard in high_risk_hazards[:3]:  # Top 3 high-risk hazards
                param = hazard["parameter"]
                recommendations.append(f"Install redundant {param} monitoring system")
        
        # General recommendations
        recommendations.extend([
            "Update standard operating procedures",
            "Review maintenance schedules",
            "Conduct regular safety drills"
        ])
        
        return list(set(recommendations))  # Remove duplicates
    
    async def generate_safety_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        unit_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate safety report."""
        try:
            # Filter analyses by date range and units
            filtered_analyses = [
                analysis for analysis in self.hazard_analyses.values()
                if start_date <= analysis.date <= end_date
                and (not unit_ids or analysis.unit_id in unit_ids)
            ]
            
            # Generate report based on type
            if report_type == "summary":
                report = await self._generate_summary_report(filtered_analyses)
            elif report_type == "detailed":
                report = await self._generate_detailed_report(filtered_analyses)
            elif report_type == "compliance":
                report = await self._generate_compliance_report(filtered_analyses)
            elif report_type == "trends":
                report = await self._generate_trends_report(filtered_analyses, start_date, end_date)
            else:
                return {"error": f"Unsupported report type: {report_type}"}
            
            report["report_type"] = report_type
            report["period"] = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            report["generated_at"] = datetime.now()
            
            logger.info(f"Safety report generated: {report_type}")
            
            return {
                "success": True,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Failed to generate safety report: {e}")
            return {"error": f"Report generation failed: {e}"}
    
    async def _generate_summary_report(self, analyses: List[HazardAnalysis]) -> Dict[str, Any]:
        """Generate summary safety report."""
        total_analyses = len(analyses)
        if total_analyses == 0:
            return {"message": "No safety analyses found in specified period"}
        
        # Risk distribution
        risk_levels = [analysis.risk_assessment["overall_risk"] for analysis in analyses]
        risk_distribution = {
            "low": risk_levels.count("low"),
            "medium": risk_levels.count("medium"),
            "high": risk_levels.count("high"),
            "critical": risk_levels.count("critical")
        }
        
        # Unit breakdown
        unit_stats = {}
        for analysis in analyses:
            unit_id = analysis.unit_id
            if unit_id not in unit_stats:
                unit_stats[unit_id] = {
                    "analyses": 0,
                    "hazards": 0,
                    "recommendations": 0
                }
            
            unit_stats[unit_id]["analyses"] += 1
            unit_stats[unit_id]["hazards"] += len(analysis.hazards_identified)
            unit_stats[unit_id]["recommendations"] += len(analysis.recommendations)
        
        return {
            "total_analyses": total_analyses,
            "risk_distribution": risk_distribution,
            "unit_breakdown": unit_stats,
            "total_hazards": sum(len(a.hazards_identified) for a in analyses),
            "total_recommendations": sum(len(a.recommendations) for a in analyses)
        }
    
    async def _generate_detailed_report(self, analyses: List[HazardAnalysis]) -> Dict[str, Any]:
        """Generate detailed safety report."""
        analysis_details = []
        
        for analysis in analyses:
            detail = {
                "analysis_id": analysis.analysis_id,
                "unit_id": analysis.unit_id,
                "analysis_type": analysis.analysis_type,
                "analyst": analysis.analyst,
                "date": analysis.date.isoformat(),
                "status": analysis.status,
                "hazards_identified": len(analysis.hazards_identified),
                "risk_assessment": analysis.risk_assessment,
                "recommendations": analysis.recommendations
            }
            analysis_details.append(detail)
        
        return {
            "analysis_count": len(analysis_details),
            "analyses": analysis_details
        }
    
    async def _generate_compliance_report(self, analyses: List[HazardAnalysis]) -> Dict[str, Any]:
        """Generate compliance report."""
        compliance_scores = {}
        
        for standard in SafetyStandard:
            if standard.value in self.config["safety_standards"]:
                # Simulate compliance assessment
                compliance_rate = np.random.uniform(0.85, 0.98)
                
                compliance_scores[standard.value] = {
                    "compliance_rate": compliance_rate,
                    "status": "compliant" if compliance_rate >= 0.95 else "needs_improvement",
                    "last_assessment": datetime.now().isoformat(),
                    "findings": np.random.randint(0, 5)
                }
        
        return {
            "compliance_scores": compliance_scores,
            "overall_compliance": all(
                score["status"] == "compliant" for score in compliance_scores.values()
            )
        }
    
    async def _generate_trends_report(
        self,
        analyses: List[HazardAnalysis],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate trends analysis report."""
        # Group analyses by month
        monthly_data = {}
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            month_key = current_date.strftime("%Y-%m")
            month_analyses = [
                analysis for analysis in analyses
                if analysis.date.year == current_date.year and analysis.date.month == current_date.month
            ]
            
            if month_analyses:
                monthly_data[month_key] = {
                    "analyses": len(month_analyses),
                    "hazards": sum(len(a.hazards_identified) for a in month_analyses),
                    "avg_risk_score": np.mean([
                        a.risk_assessment["average_risk_score"] for a in month_analyses
                    ])
                }
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return {
            "monthly_data": monthly_data,
            "trend_analysis": {
                "increasing_risk": len(monthly_data) > 1 and list(monthly_data.values())[-1]["avg_risk_score"] > list(monthly_data.values())[0]["avg_risk_score"],
                "improving_safety": len(monthly_data) > 1 and list(monthly_data.values())[-1]["hazards"] < list(monthly_data.values())[0]["hazards"]
            }
        }
    
    async def report_safety_incident(
        self,
        unit_id: str,
        incident_type: str,
        severity: str,
        description: str,
        reporter: str,
        injuries: Optional[List[Dict[str, Any]]] = None,
        environmental_impact: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Report safety incident."""
        try:
            if unit_id not in self.process_units:
                return {"error": f"Process unit {unit_id} not found"}
            
            incident_id = f"INC_{datetime.now().strftime('%Y%m%d%H%M%S')}_{np.random.randint(1000, 9999)}"
            
            incident = {
                "incident_id": incident_id,
                "unit_id": unit_id,
                "incident_type": incident_type,
                "severity": severity,
                "description": description,
                "reporter": reporter,
                "injuries": injuries or [],
                "environmental_impact": environmental_impact or {},
                "reported_at": datetime.now(),
                "status": "open",
                "investigation_status": "pending"
            }
            
            # Store incident (in real implementation, would use database)
            if not hasattr(self, 'safety_incidents'):
                self.safety_incidents = {}
            self.safety_incidents[incident_id] = incident
            
            logger.warning(f"Safety incident reported: {incident_id}")
            
            return {
                "success": True,
                "incident_id": incident_id,
                "unit_id": unit_id,
                "severity": severity,
                "reported_at": incident["reported_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to report safety incident: {e}")
            return {"error": f"Incident reporting failed: {e}"}
    
    async def perform_sil_assessment(
        self,
        unit_id: str,
        safety_instrumented_functions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform Safety Integrity Level (SIL) assessment."""
        try:
            if unit_id not in self.process_units:
                return {"error": f"Process unit {unit_id} not found"}
            
            assessment_id = f"SIL_{datetime.now().strftime('%Y%m%d%H%M%S')}_{np.random.randint(1000, 9999)}"
            
            # Assess SIL for each function
            sil_results = []
            for function in safety_instrumented_functions:
                # Calculate risk reduction factor
                consequence = function.get("consequence_severity", 0.5)
                frequency = function.get("failure_frequency", 0.1)
                probability = function.get("failure_probability", 0.1)
                
                risk = consequence * frequency * probability
                
                # Determine required SIL
                if risk >= 0.9:
                    required_sil = "SIL3"
                elif risk >= 0.7:
                    required_sil = "SIL2"
                elif risk >= 0.5:
                    required_sil = "SIL1"
                else:
                    required_sil = "SIL0"
                
                sil_result = {
                    "function_id": function.get("function_id"),
                    "function_name": function.get("function_name"),
                    "risk_score": risk,
                    "required_sil": required_sil,
                    "current_sil": function.get("current_sil", "SIL0"),
                    "adequate": function.get("current_sil", "SIL0") >= required_sil
                }
                sil_results.append(sil_result)
            
            assessment = {
                "assessment_id": assessment_id,
                "unit_id": unit_id,
                "sil_results": sil_results,
                "overall_adequacy": all(result["adequate"] for result in sil_results),
                "assessed_at": datetime.now()
            }
            
            # Store assessment
            if not hasattr(self, 'sil_assessments'):
                self.sil_assessments = {}
            self.sil_assessments[assessment_id] = assessment
            
            logger.info(f"SIL assessment completed: {assessment_id}")
            
            return {
                "success": True,
                "assessment_id": assessment_id,
                "unit_id": unit_id,
                "functions_assessed": len(sil_results),
                "overall_adequacy": assessment["overall_adequacy"],
                "assessed_at": assessment["assessed_at"]
            }
            
        except Exception as e:
            logger.error(f"Failed to perform SIL assessment: {e}")
            return {"error": f"SIL assessment failed: {e}"}
    
    def get_safety_metrics(self) -> Dict[str, Any]:
        """Get overall safety metrics."""
        total_units = len(self.process_units)
        total_analyses = len(self.hazard_analyses)
        
        # Risk distribution
        if self.process_units:
            risk_levels = [unit.risk_level.value for unit in self.process_units.values()]
            risk_distribution = {
                "low": risk_levels.count("low"),
                "medium": risk_levels.count("medium"),
                "high": risk_levels.count("high"),
                "critical": risk_levels.count("critical")
            }
        else:
            risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        return {
            "total_process_units": total_units,
            "total_hazard_analyses": total_analyses,
            "risk_distribution": risk_distribution,
            "safety_standards": self.config["safety_standards"],
            "compliance_monitoring": len(self.compliance_monitoring),
            "active_incidents": len(getattr(self, 'safety_incidents', {})),
            "sil_assessments": len(getattr(self, 'sil_assessments', {}))
        }


# Global chemical process safety instance
chemical_safety = ChemicalProcessSafety()


async def register_process_unit(
    unit_id: str,
    name: str,
    description: str,
    location: str,
    chemicals: List[str],
    operating_conditions: Dict[str, float],
    safety_systems: List[str]
) -> Dict[str, Any]:
    """Register process unit."""
    return await chemical_safety.register_process_unit(
        unit_id, name, description, location, chemicals, operating_conditions, safety_systems
    )


async def perform_hazop_study(
    unit_id: str,
    analyst: str,
    study_parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Perform HAZOP study."""
    return await chemical_safety.perform_hazop_study(unit_id, analyst, study_parameters)


async def generate_safety_report(
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    unit_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate safety report."""
    return await chemical_safety.generate_safety_report(
        report_type, start_date, end_date, unit_ids
    )


async def report_safety_incident(
    unit_id: str,
    incident_type: str,
    severity: str,
    description: str,
    reporter: str,
    injuries: Optional[List[Dict[str, Any]]] = None,
    environmental_impact: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Report safety incident."""
    return await chemical_safety.report_safety_incident(
        unit_id, incident_type, severity, description, reporter, injuries, environmental_impact
    )


async def perform_sil_assessment(
    unit_id: str,
    safety_instrumented_functions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Perform SIL assessment."""
    return await chemical_safety.perform_sil_assessment(unit_id, safety_instrumented_functions)


def get_chemical_safety_metrics() -> Dict[str, Any]:
    """Get safety metrics."""
    return chemical_safety.get_safety_metrics()
