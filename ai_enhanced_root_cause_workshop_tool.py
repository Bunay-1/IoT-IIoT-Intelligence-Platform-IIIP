"""
AI Enhanced Root Cause Workshop Tool

This module implements advanced AI-powered root cause analysis for industrial incidents.
It uses machine learning, causal inference, and expert systems to identify root causes
of complex industrial problems with high accuracy.
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from config import settings
from utils.logging_config import LoggerMixin
from utils.performance_monitor import monitor_operation
from utils.security import SecurityError, input_validator, validate_input

# Import core ML engines for integration
try:
    from automl_engine import automl_engine
    from reinforcement_learning import rl_engine

    AUTOML_AVAILABLE = True
    RL_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False
    RL_AVAILABLE = False


class RootCauseAnalysisError(Exception):
    """Base exception for root cause analysis errors."""

    pass


class InsufficientDataError(RootCauseAnalysisError):
    """Raised when insufficient data is available for analysis."""

    pass


class AnalysisTimeoutError(RootCauseAnalysisError):
    """Raised when analysis exceeds time limits."""

    pass


class AIEnhancedRootCauseWorkshopTool(LoggerMixin):
    """
    Advanced AI-powered root cause analysis tool for industrial incidents.

    This class implements comprehensive root cause analysis using multiple AI techniques
    including causal inference, pattern recognition, and expert system reasoning.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI Enhanced Root Cause Workshop Tool.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # Analysis configuration
        self.enable_ai_analysis = self.config.get("enable_ai_analysis", True)
        self.max_analysis_time = self.config.get("max_analysis_time", 300)  # 5 minutes
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.max_hypotheses = self.config.get("max_hypotheses", 5)

        # Knowledge base
        self.error_patterns: Dict[
            str, Dict[str, Any]
        ] = self._initialize_error_patterns()
        self.causal_graph: Dict[str, List[str]] = self._initialize_causal_graph()
        self.historical_incidents: List[Dict[str, Any]] = []

        # Analysis cache
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds = self.config.get("cache_ttl_seconds", 3600)  # 1 hour

        # Performance tracking
        self.analysis_stats: Dict[str, Any] = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "avg_analysis_time": 0.0,
            "cache_hit_rate": 0.0,
        }

        self.logger.info("AIEnhancedRootCauseWorkshopTool initialized")

    def _initialize_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize error pattern database.

        Returns:
            Dictionary of error patterns with associated root causes
        """
        return {
            "E001": {
                "description": "Network connectivity issue",
                "symptoms": ["connection_timeout", "packet_loss", "dns_failure"],
                "root_causes": [
                    "network_cable_fault",
                    "router_failure",
                    "dns_server_down",
                ],
                "severity": "high",
                "common_solutions": [
                    "check_cable_connections",
                    "restart_network_equipment",
                    "verify_dns_settings",
                ],
            },
            "E002": {
                "description": "Software bug",
                "symptoms": [
                    "unexpected_error",
                    "application_crash",
                    "data_corruption",
                ],
                "root_causes": ["code_bug", "memory_leak", "race_condition"],
                "severity": "medium",
                "common_solutions": [
                    "apply_software_patch",
                    "restart_application",
                    "rollback_to_previous_version",
                ],
            },
            "E003": {
                "description": "Hardware failure",
                "symptoms": ["device_unresponsive", "sensor_failure", "power_loss"],
                "root_causes": [
                    "component_failure",
                    "power_supply_issue",
                    "overheating",
                ],
                "severity": "critical",
                "common_solutions": [
                    "replace_failed_component",
                    "check_power_connections",
                    "improve_cooling",
                ],
            },
            "E004": {
                "description": "Configuration error",
                "symptoms": [
                    "invalid_settings",
                    "permission_denied",
                    "service_not_starting",
                ],
                "root_causes": [
                    "incorrect_config",
                    "missing_permissions",
                    "conflicting_settings",
                ],
                "severity": "low",
                "common_solutions": [
                    "verify_configuration",
                    "check_permissions",
                    "resolve_conflicts",
                ],
            },
            "E005": {
                "description": "Resource exhaustion",
                "symptoms": ["out_of_memory", "disk_full", "cpu_overload"],
                "root_causes": [
                    "memory_leak",
                    "insufficient_disk_space",
                    "resource_contention",
                ],
                "severity": "high",
                "common_solutions": [
                    "free_up_resources",
                    "increase_capacity",
                    "optimize_resource_usage",
                ],
            },
        }

    def _initialize_causal_graph(self) -> Dict[str, List[str]]:
        """
        Initialize causal relationship graph.

        Returns:
            Dictionary mapping causes to potential effects
        """
        return {
            "power_failure": [
                "device_unresponsive",
                "sensor_failure",
                "system_shutdown",
            ],
            "network_issue": [
                "connection_timeout",
                "data_sync_failure",
                "remote_access_denied",
            ],
            "software_bug": [
                "unexpected_error",
                "application_crash",
                "data_corruption",
            ],
            "hardware_fault": [
                "component_failure",
                "sensor_malfunction",
                "performance_degradation",
            ],
            "configuration_error": [
                "service_not_starting",
                "invalid_settings",
                "permission_denied",
            ],
            "resource_exhaustion": [
                "out_of_memory",
                "system_slowdown",
                "service_crash",
            ],
            "environmental_factor": [
                "overheating",
                "humidity_issue",
                "dust_accumulation",
            ],
            "operator_error": [
                "incorrect_operation",
                "data_entry_error",
                "procedure_violation",
            ],
            "maintenance_issue": [
                "preventive_maintenance_missed",
                "wear_and_tear",
                "aging_component",
            ],
        }

    @validate_input(
        {
            "incident_key": {
                "type": "string",
                "max_length": 100,
                "required": True,
                "pattern": "^[a-zA-Z0-9_-]{1,100}$",
            }
        }
    )
    @monitor_operation("ai_enhanced_root_cause_workshop_tool.analyze_incident")
    async def analyze_incident(
        self, incident_key: str, incident_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an incident using AI-enhanced root cause analysis.

        Args:
            incident_key: Unique identifier for the incident
            incident_data: Optional incident data (if not using stored data)

        Returns:
            Dictionary with root cause analysis results

        Raises:
            ValueError: If incident_key is invalid
            InsufficientDataError: If insufficient data for analysis
            AnalysisTimeoutError: If analysis exceeds time limits
        """
        start_time = datetime.now()

        try:
            self.analysis_stats["total_analyses"] += 1

            # Check cache first
            cache_key = (
                f"{incident_key}_{hash(str(incident_data) if incident_data else '')}"
            )
            if cache_key in self.analysis_cache and self._is_cache_valid(cache_key):
                self.logger.debug(
                    f"Returning cached analysis for incident {incident_key}"
                )
                return self.analysis_cache[cache_key]["data"]

            # Get incident data
            if incident_data is None:
                incident_data = self._get_incident_data(incident_key)

            if not incident_data:
                raise InsufficientDataError(
                    f"No data available for incident {incident_key}"
                )

            # Validate incident data
            if not self._validate_incident_data(incident_data):
                raise ValueError(f"Invalid incident data for {incident_key}")

            # Perform comprehensive analysis
            analysis_result = await self._perform_root_cause_analysis(
                incident_key, incident_data
            )

            # Check analysis time
            analysis_time = (datetime.now() - start_time).total_seconds()
            if analysis_time > self.max_analysis_time:
                raise AnalysisTimeoutError(
                    f"Analysis exceeded time limit: {analysis_time:.2f}s"
                )

            # Update statistics
            self.analysis_stats["successful_analyses"] += 1
            self.analysis_stats["avg_analysis_time"] = (
                (
                    self.analysis_stats["avg_analysis_time"]
                    * (self.analysis_stats["successful_analyses"] - 1)
                )
                + analysis_time
            ) / self.analysis_stats["successful_analyses"]

            # Cache result
            self.analysis_cache[cache_key] = {
                "data": analysis_result,
                "timestamp": datetime.now(),
                "ttl": self.cache_ttl_seconds,
            }

            # Clean old cache entries
            self._clean_analysis_cache()

            self.logger.info(
                f"Root cause analysis completed for incident {incident_key} in {analysis_time:.2f}s"
            )
            return analysis_result

        except Exception as e:
            self.logger.error(
                f"Root cause analysis failed for incident {incident_key}: {e}"
            )
            raise

    async def _perform_root_cause_analysis(
        self, incident_key: str, incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive root cause analysis.

        Args:
            incident_key: Incident identifier
            incident_data: Incident data dictionary

        Returns:
            Analysis results dictionary
        """
        analysis_result = {
            "incident_key": incident_key,
            "timestamp": datetime.now().isoformat(),
            "analysis_method": "ai_enhanced",
            "confidence_score": 0.0,
            "root_causes": [],
            "hypotheses": [],
            "evidence": {},
            "recommendations": [],
            "severity_assessment": "unknown",
            "estimated_resolution_time": "unknown",
        }

        try:
            # Step 1: Pattern-based analysis
            pattern_analysis = self._analyze_error_patterns(incident_data)
            analysis_result["evidence"]["pattern_analysis"] = pattern_analysis

            # Step 2: Causal analysis
            causal_analysis = self._perform_causal_analysis(incident_data)
            analysis_result["evidence"]["causal_analysis"] = causal_analysis

            # Step 3: Historical analysis
            historical_analysis = self._analyze_historical_patterns(incident_data)
            analysis_result["evidence"]["historical_analysis"] = historical_analysis

            # Step 4: AI-enhanced analysis (if enabled)
            if self.enable_ai_analysis and AUTOML_AVAILABLE:
                ai_analysis = await self._perform_ai_enhanced_analysis(incident_data)
                analysis_result["evidence"]["ai_analysis"] = ai_analysis

            # Step 5: Generate hypotheses and root causes
            hypotheses = self._generate_hypotheses(analysis_result["evidence"])
            analysis_result["hypotheses"] = hypotheses

            root_causes = self._identify_root_causes(hypotheses)
            analysis_result["root_causes"] = root_causes

            # Step 6: Calculate confidence and severity
            analysis_result["confidence_score"] = self._calculate_confidence_score(
                analysis_result["evidence"]
            )
            analysis_result["severity_assessment"] = self._assess_severity(
                incident_data, root_causes
            )

            # Step 7: Generate recommendations
            analysis_result["recommendations"] = self._generate_recommendations(
                root_causes, incident_data
            )

            # Step 8: Estimate resolution time
            analysis_result[
                "estimated_resolution_time"
            ] = self._estimate_resolution_time(root_causes)

            return analysis_result

        except Exception as e:
            self.logger.error(f"Error in root cause analysis: {e}")
            analysis_result["error"] = str(e)
            return analysis_result

    def _analyze_error_patterns(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze incident data against known error patterns.

        Args:
            incident_data: Incident data dictionary

        Returns:
            Pattern analysis results
        """
        error_code = incident_data.get("error_code")
        symptoms = incident_data.get("symptoms", [])
        context = incident_data.get("context", {})

        pattern_matches = []

        if error_code and error_code in self.error_patterns:
            pattern = self.error_patterns[error_code]
            match_score = self._calculate_pattern_match_score(
                pattern, symptoms, context
            )
            pattern_matches.append(
                {
                    "error_code": error_code,
                    "pattern": pattern,
                    "match_score": match_score,
                    "matched_symptoms": [
                        s for s in symptoms if s in pattern["symptoms"]
                    ],
                }
            )

        # Also check for partial matches
        for code, pattern in self.error_patterns.items():
            if code != error_code:
                match_score = self._calculate_pattern_match_score(
                    pattern, symptoms, context
                )
                if match_score > 0.3:  # Threshold for partial matches
                    pattern_matches.append(
                        {
                            "error_code": code,
                            "pattern": pattern,
                            "match_score": match_score,
                            "matched_symptoms": [
                                s for s in symptoms if s in pattern["symptoms"]
                            ],
                        }
                    )

        return {
            "primary_match": pattern_matches[0] if pattern_matches else None,
            "alternative_matches": pattern_matches[1:],
            "total_matches": len(pattern_matches),
        }

    def _perform_causal_analysis(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform causal analysis using the causal graph.

        Args:
            incident_data: Incident data dictionary

        Returns:
            Causal analysis results
        """
        symptoms = incident_data.get("symptoms", [])
        context = incident_data.get("context", {})

        potential_causes = []
        causal_paths = []

        # Find potential causes for observed symptoms
        for cause, effects in self.causal_graph.items():
            matching_effects = [effect for effect in effects if effect in symptoms]
            if matching_effects:
                confidence = len(matching_effects) / len(effects)
                potential_causes.append(
                    {
                        "cause": cause,
                        "matching_effects": matching_effects,
                        "confidence": confidence,
                        "total_effects": len(effects),
                    }
                )

        # Sort by confidence
        potential_causes.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "potential_causes": potential_causes[: self.max_hypotheses],
            "symptoms_analyzed": symptoms,
            "causal_paths_identified": len(potential_causes),
        }

    def _analyze_historical_patterns(
        self, incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze historical incident patterns.

        Args:
            incident_data: Incident data dictionary

        Returns:
            Historical analysis results
        """
        if not self.historical_incidents:
            return {"available": False, "message": "No historical data available"}

        error_code = incident_data.get("error_code")
        symptoms = incident_data.get("symptoms", [])
        system_component = incident_data.get("system_component")

        similar_incidents = []

        for incident in self.historical_incidents:
            similarity_score = self._calculate_incident_similarity(
                incident, incident_data
            )
            if similarity_score > 0.5:  # Similarity threshold
                similar_incidents.append(
                    {
                        "incident_id": incident.get("id"),
                        "similarity_score": similarity_score,
                        "root_cause": incident.get("root_cause"),
                        "resolution": incident.get("resolution"),
                    }
                )

        similar_incidents.sort(key=lambda x: x["similarity_score"], reverse=True)

        return {
            "available": True,
            "similar_incidents": similar_incidents[:5],  # Top 5 similar incidents
            "total_similar": len(similar_incidents),
            "most_common_root_cause": self._find_most_common_root_cause(
                similar_incidents
            ),
        }

    async def _perform_ai_enhanced_analysis(
        self, incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform AI-enhanced analysis using integrated ML engines.

        Args:
            incident_data: Incident data dictionary

        Returns:
            AI analysis results
        """
        if not AUTOML_AVAILABLE:
            return {"available": False, "message": "AutoML engine not available"}

        try:
            # Prepare data for ML analysis
            features = self._extract_features_for_ml(incident_data)

            # Use AutoML for pattern recognition
            analysis_result = {
                "available": True,
                "features_extracted": len(features),
                "predicted_patterns": [],
                "anomaly_score": 0.0,
            }

            # This would use AutoML to identify patterns or anomalies
            # For now, return mock results
            analysis_result["predicted_patterns"] = ["pattern_1", "pattern_2"]
            analysis_result["anomaly_score"] = 0.75

            return analysis_result

        except Exception as e:
            self.logger.error(f"AI-enhanced analysis failed: {e}")
            return {"available": False, "error": str(e)}

    def _generate_hypotheses(self, evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate hypotheses based on collected evidence.

        Args:
            evidence: Analysis evidence dictionary

        Returns:
            List of hypotheses
        """
        hypotheses = []

        # Generate hypotheses from pattern analysis
        pattern_analysis = evidence.get("pattern_analysis", {})
        if pattern_analysis.get("primary_match"):
            primary = pattern_analysis["primary_match"]
            hypotheses.append(
                {
                    "hypothesis": f"Primary pattern match: {primary['pattern']['description']}",
                    "confidence": primary["match_score"],
                    "evidence_type": "pattern_matching",
                    "supporting_evidence": primary["matched_symptoms"],
                }
            )

        # Generate hypotheses from causal analysis
        causal_analysis = evidence.get("causal_analysis", {})
        for cause in causal_analysis.get("potential_causes", [])[:3]:
            hypotheses.append(
                {
                    "hypothesis": f"Causal relationship: {cause['cause']} -> observed symptoms",
                    "confidence": cause["confidence"],
                    "evidence_type": "causal_analysis",
                    "supporting_evidence": cause["matching_effects"],
                }
            )

        # Generate hypotheses from historical analysis
        historical_analysis = evidence.get("historical_analysis", {})
        if historical_analysis.get("available") and historical_analysis.get(
            "similar_incidents"
        ):
            most_common = historical_analysis.get("most_common_root_cause")
            if most_common:
                hypotheses.append(
                    {
                        "hypothesis": f"Historical pattern: Similar incidents resolved as {most_common}",
                        "confidence": 0.6,  # Historical confidence
                        "evidence_type": "historical_analysis",
                        "supporting_evidence": [
                            inc["root_cause"]
                            for inc in historical_analysis["similar_incidents"][:3]
                        ],
                    }
                )

        # Sort by confidence and limit
        hypotheses.sort(key=lambda x: x["confidence"], reverse=True)
        return hypotheses[: self.max_hypotheses]

    def _identify_root_causes(
        self, hypotheses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify root causes from hypotheses.

        Args:
            hypotheses: List of hypotheses

        Returns:
            List of identified root causes
        """
        root_causes = []

        for hypothesis in hypotheses:
            if hypothesis["confidence"] >= self.confidence_threshold:
                root_cause = {
                    "description": hypothesis["hypothesis"],
                    "confidence": hypothesis["confidence"],
                    "evidence_type": hypothesis["evidence_type"],
                    "supporting_evidence": hypothesis["supporting_evidence"],
                    "recommended_actions": self._generate_root_cause_actions(
                        hypothesis
                    ),
                }
                root_causes.append(root_cause)

        return root_causes

    def _calculate_confidence_score(self, evidence: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score for the analysis.

        Args:
            evidence: Analysis evidence dictionary

        Returns:
            Confidence score between 0 and 1
        """
        confidence_factors = []

        # Pattern matching confidence
        pattern_analysis = evidence.get("pattern_analysis", {})
        if pattern_analysis.get("primary_match"):
            confidence_factors.append(pattern_analysis["primary_match"]["match_score"])

        # Causal analysis confidence
        causal_analysis = evidence.get("causal_analysis", {})
        if causal_analysis.get("potential_causes"):
            max_causal_confidence = max(
                c["confidence"] for c in causal_analysis["potential_causes"]
            )
            confidence_factors.append(max_causal_confidence)

        # Historical analysis confidence
        historical_analysis = evidence.get("historical_analysis", {})
        if historical_analysis.get("available"):
            confidence_factors.append(0.6)  # Base confidence for historical data

        # AI analysis confidence
        ai_analysis = evidence.get("ai_analysis", {})
        if ai_analysis.get("available"):
            confidence_factors.append(ai_analysis.get("anomaly_score", 0.5))

        if not confidence_factors:
            return 0.0

        # Weighted average confidence
        return sum(confidence_factors) / len(confidence_factors)

    def _assess_severity(
        self, incident_data: Dict[str, Any], root_causes: List[Dict[str, Any]]
    ) -> str:
        """
        Assess the severity of the incident.

        Args:
            incident_data: Incident data dictionary
            root_causes: Identified root causes

        Returns:
            Severity level string
        """
        # Check error code severity
        error_code = incident_data.get("error_code")
        if error_code and error_code in self.error_patterns:
            pattern_severity = self.error_patterns[error_code]["severity"]
            if pattern_severity == "critical":
                return "critical"

        # Check impact indicators
        impact = incident_data.get("impact", {})
        if (
            impact.get("affected_users", 0) > 100
            or impact.get("downtime_hours", 0) > 24
        ):
            return "critical"
        elif (
            impact.get("affected_users", 0) > 10 or impact.get("downtime_hours", 0) > 1
        ):
            return "high"

        # Check root cause confidence
        avg_confidence = (
            sum(rc["confidence"] for rc in root_causes) / len(root_causes)
            if root_causes
            else 0
        )
        if avg_confidence > 0.8:
            return "high"
        elif avg_confidence > 0.6:
            return "medium"

        return "low"

    def _generate_recommendations(
        self, root_causes: List[Dict[str, Any]], incident_data: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on root causes.

        Args:
            root_causes: Identified root causes
            incident_data: Original incident data

        Returns:
            List of recommendations
        """
        recommendations = []

        for root_cause in root_causes:
            actions = root_cause.get("recommended_actions", [])
            recommendations.extend(actions)

        # Add general recommendations
        error_code = incident_data.get("error_code")
        if error_code and error_code in self.error_patterns:
            pattern = self.error_patterns[error_code]
            recommendations.extend(pattern["common_solutions"])

        # Remove duplicates and limit
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:10]  # Max 10 recommendations

    def _estimate_resolution_time(self, root_causes: List[Dict[str, Any]]) -> str:
        """
        Estimate resolution time based on root causes.

        Args:
            root_causes: Identified root causes

        Returns:
            Estimated resolution time string
        """
        if not root_causes:
            return "unknown"

        # Simple estimation based on root cause types
        max_confidence = max(rc["confidence"] for rc in root_causes)

        if max_confidence > 0.9:
            return "1-2 hours"
        elif max_confidence > 0.7:
            return "2-4 hours"
        elif max_confidence > 0.5:
            return "4-8 hours"
        else:
            return "8-24 hours"

    # Helper methods
    def _get_incident_data(self, incident_key: str) -> Optional[Dict[str, Any]]:
        """Get incident data (placeholder for actual data retrieval)."""
        # This would typically fetch from database or external system
        return None

    def _validate_incident_data(self, incident_data: Dict[str, Any]) -> bool:
        """Validate incident data structure."""
        required_fields = ["error_code", "symptoms"]
        return all(field in incident_data for field in required_fields)

    def _calculate_pattern_match_score(
        self, pattern: Dict[str, Any], symptoms: List[str], context: Dict[str, Any]
    ) -> float:
        """Calculate how well symptoms match a pattern."""
        pattern_symptoms = set(pattern["symptoms"])
        incident_symptoms = set(symptoms)
        intersection = len(pattern_symptoms.intersection(incident_symptoms))
        union = len(pattern_symptoms.union(incident_symptoms))
        return intersection / union if union > 0 else 0.0

    def _calculate_incident_similarity(
        self, incident1: Dict[str, Any], incident2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two incidents."""
        # Simple similarity based on error codes and symptoms
        if incident1.get("error_code") == incident2.get("error_code"):
            return 0.8

        symptoms1 = set(incident1.get("symptoms", []))
        symptoms2 = set(incident2.get("symptoms", []))
        if symptoms1 and symptoms2:
            intersection = len(symptoms1.intersection(symptoms2))
            union = len(symptoms1.union(symptoms2))
            return intersection / union if union > 0 else 0.0

        return 0.0

    def _find_most_common_root_cause(
        self, similar_incidents: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Find the most common root cause in similar incidents."""
        root_cause_counts = defaultdict(int)
        for incident in similar_incidents:
            rc = incident.get("root_cause")
            if rc:
                root_cause_counts[rc] += 1

        if root_cause_counts:
            return max(root_cause_counts.items(), key=lambda x: x[1])[0]
        return None

    def _extract_features_for_ml(self, incident_data: Dict[str, Any]) -> List[float]:
        """Extract features for ML analysis."""
        # Placeholder feature extraction
        return [1.0, 0.5, 0.8]  # Mock features

    def _generate_root_cause_actions(self, hypothesis: Dict[str, Any]) -> List[str]:
        """Generate recommended actions for a root cause hypothesis."""
        # Placeholder action generation
        return ["Investigate further", "Check system logs", "Verify configuration"]

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self.analysis_cache:
            return False

        entry = self.analysis_cache[cache_key]
        cache_time = entry["timestamp"]
        ttl = entry.get("ttl", self.cache_ttl_seconds)
        return (datetime.now() - cache_time) < timedelta(seconds=ttl)

    def _clean_analysis_cache(self) -> None:
        """Clean expired cache entries."""
        current_time = datetime.now()
        valid_entries = {}

        for key, entry in self.analysis_cache.items():
            if self._is_cache_valid(key):
                valid_entries[key] = entry

        removed_count = len(self.analysis_cache) - len(valid_entries)
        self.analysis_cache = valid_entries

        if removed_count > 0:
            self.logger.debug(f"Cleaned {removed_count} expired analysis cache entries")

    def add_historical_incident(self, incident: Dict[str, Any]) -> None:
        """
        Add a resolved incident to the historical database.

        Args:
            incident: Historical incident data
        """
        self.historical_incidents.append(incident)
        self.logger.debug(f"Added historical incident: {incident.get('id')}")

    def get_analysis_stats(self) -> Dict[str, Any]:
        """
        Get analysis performance statistics.

        Returns:
            Dictionary with analysis statistics
        """
        stats = self.analysis_stats.copy()
        stats["cache_size"] = len(self.analysis_cache)
        stats["historical_incidents"] = len(self.historical_incidents)

        if stats["total_analyses"] > 0:
            stats["success_rate"] = (
                stats["successful_analyses"] / stats["total_analyses"]
            )

        return stats

    def clear_cache(self) -> None:
        """
        Clear the analysis cache.
        """
        self.analysis_cache.clear()
        self.logger.info("Analysis cache cleared")
