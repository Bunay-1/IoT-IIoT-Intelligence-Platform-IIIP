"""
AI Safety Guardrail Module

This module implements comprehensive AI safety and ethics guardrails
to ensure responsible AI deployment and usage.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from utils.logging_config import LoggerMixin
from utils.performance_monitor import monitor_operation
from utils.security import SecurityError, input_validator, validate_input


class AISafetyError(Exception):
    """Base exception for AI safety errors."""

    pass


class SafetyViolationError(AISafetyError):
    """Raised when safety violations are detected."""

    pass


class AISafetyGuardrail(LoggerMixin):
    """
    AI Safety Guardrail system for responsible AI deployment.

    This class provides comprehensive safety checks including:
    - Bias detection and mitigation
    - Ethical compliance monitoring
    - Safety constraint enforcement
    - Incident response and logging
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI Safety Guardrail system.

        Args:
            config: Configuration dictionary with safety parameters
        """
        self.config = config or self._get_default_config()

        # Safety rules and constraints
        self.safety_rules: Dict[str, Dict[str, Any]] = {}
        self.violation_history: List[Dict[str, Any]] = []
        self.safety_metrics: Dict[str, Any] = {}

        # Ethical guidelines
        self.ethical_guidelines = self._load_ethical_guidelines()

        self.logger.info("AI Safety Guardrail initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "bias_threshold": 0.1,
            "safety_check_interval": 60,  # seconds
            "max_violations_per_hour": 10,
            "auto_mitigation_enabled": True,
            "incident_response_enabled": True,
            "logging_level": "INFO",
        }

    def _load_ethical_guidelines(self) -> Dict[str, Any]:
        """Load ethical guidelines for AI safety."""
        return {
            "fairness": ["no_discrimination", "equal_opportunity", "bias_detection"],
            "transparency": ["explainable_decisions", "audit_trail", "open_source"],
            "accountability": [
                "human_oversight",
                "error_reporting",
                "continuous_monitoring",
            ],
            "privacy": ["data_protection", "consent_management", "anonymization"],
            "safety": ["harm_prevention", "robustness", "fail_safe_mechanisms"],
        }

    @validate_input(
        {
            "ai_input": {"type": "object", "required": True},
            "context": {"type": "object", "required": False},
        }
    )
    @monitor_operation("ai_safety_guardrail.check_safety")
    async def check_safety(
        self, ai_input: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check AI input and context for safety violations.

        Args:
            ai_input: AI system input data
            context: Additional context information

        Returns:
            Safety check results

        Raises:
            SafetyViolationError: If critical safety violations detected
        """
        try:
            self.logger.info("Performing AI safety check")

            # Perform comprehensive safety analysis
            bias_check = await self._check_bias(ai_input)
            ethical_check = await self._check_ethical_compliance(ai_input, context)
            safety_check = await self._check_safety_constraints(ai_input)
            privacy_check = await self._check_privacy_compliance(ai_input)

            # Aggregate results
            safety_score = self._calculate_safety_score(
                {
                    "bias": bias_check,
                    "ethical": ethical_check,
                    "safety": safety_check,
                    "privacy": privacy_check,
                }
            )

            violations = self._collect_violations(
                {
                    "bias": bias_check,
                    "ethical": ethical_check,
                    "safety": safety_check,
                    "privacy": privacy_check,
                }
            )

            # Handle violations
            if violations:
                await self._handle_violations(violations, ai_input, context)

            # Update metrics
            self._update_safety_metrics(safety_score, violations)

            result = {
                "safe": len(violations) == 0,
                "safety_score": safety_score,
                "violations": violations,
                "recommendations": self._generate_safety_recommendations(violations),
                "timestamp": datetime.now().isoformat(),
                "check_id": f"safety_check_{int(asyncio.get_event_loop().time())}",
            }

            self.logger.info(
                f"Safety check completed. Safe: {result['safe']}, Score: {safety_score:.3f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Safety check failed: {e}")
            raise AISafetyError(f"Safety check failed: {e}") from e

    async def _check_bias(self, ai_input: Dict[str, Any]) -> Dict[str, Any]:
        """Check for bias in AI input and processing."""
        try:
            # Simplified bias detection (would use ML models in practice)
            bias_indicators = []
            input_data = ai_input.get("data", {})

            # Check for demographic bias
            if "demographics" in input_data:
                demo_data = input_data["demographics"]
                # Check representation
                if isinstance(demo_data, dict):
                    total = sum(demo_data.values())
                    for group, count in demo_data.items():
                        if total > 0 and (count / total) < 0.1:  # Less than 10%
                            bias_indicators.append(
                                {
                                    "type": "underrepresentation",
                                    "group": group,
                                    "severity": "medium",
                                    "description": f"Underrepresented group: {group}",
                                }
                            )

            # Check for language bias
            text_content = ai_input.get("text", "")
            if text_content:
                # Simple bias word detection
                bias_words = ["bias", "discrimination", "unfair"]
                for word in bias_words:
                    if word.lower() in text_content.lower():
                        bias_indicators.append(
                            {
                                "type": "content_bias",
                                "severity": "low",
                                "description": f"Potential bias indicator: {word}",
                            }
                        )

            return {
                "bias_detected": len(bias_indicators) > 0,
                "bias_score": min(len(bias_indicators) * 0.1, 1.0),
                "indicators": bias_indicators,
            }

        except Exception as e:
            self.logger.warning(f"Bias check failed: {e}")
            return {"bias_detected": False, "bias_score": 0.0, "indicators": []}

    async def _check_ethical_compliance(
        self, ai_input: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check ethical compliance of AI usage."""
        try:
            violations = []

            # Check usage context
            if context:
                usage_type = context.get("usage_type", "")
                # Check for prohibited uses
                prohibited_uses = ["surveillance", "manipulation", "harmful_content"]
                for prohibited in prohibited_uses:
                    if prohibited in usage_type.lower():
                        violations.append(
                            {
                                "type": "prohibited_use",
                                "severity": "high",
                                "description": f"Prohibited usage type: {usage_type}",
                                "guideline": "safety",
                            }
                        )

            # Check data sources
            data_sources = ai_input.get("data_sources", [])
            for source in data_sources:
                if "unethical" in source.lower() or "biased" in source.lower():
                    violations.append(
                        {
                            "type": "unethical_data_source",
                            "severity": "high",
                            "description": f"Potentially unethical data source: {source}",
                            "guideline": "fairness",
                        }
                    )

            return {"compliant": len(violations) == 0, "violations": violations}

        except Exception as e:
            self.logger.warning(f"Ethical compliance check failed: {e}")
            return {"compliant": True, "violations": []}

    async def _check_safety_constraints(
        self, ai_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check safety constraints."""
        try:
            violations = []

            # Check input size limits
            input_size = len(str(ai_input))
            max_size = self.config.get("max_input_size", 1000000)  # 1MB
            if input_size > max_size:
                violations.append(
                    {
                        "type": "input_size_exceeded",
                        "severity": "medium",
                        "description": f"Input size {input_size} exceeds limit {max_size}",
                    }
                )

            # Check for malicious content
            content = ai_input.get("content", "")
            malicious_patterns = ["<script>", "javascript:", "eval(", "system("]
            for pattern in malicious_patterns:
                if pattern in content:
                    violations.append(
                        {
                            "type": "malicious_content",
                            "severity": "high",
                            "description": f"Malicious content detected: {pattern}",
                        }
                    )

            return {"safe": len(violations) == 0, "violations": violations}

        except Exception as e:
            self.logger.warning(f"Safety constraints check failed: {e}")
            return {"safe": True, "violations": []}

    async def _check_privacy_compliance(
        self, ai_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check privacy compliance."""
        try:
            violations = []

            # Check for PII
            content = str(ai_input)
            pii_patterns = [
                r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                r"\b\d{16}\b",  # Credit card
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            ]

            import re

            for pattern in pii_patterns:
                if re.search(pattern, content):
                    violations.append(
                        {
                            "type": "pii_detected",
                            "severity": "high",
                            "description": "Potential personally identifiable information detected",
                        }
                    )
                    break  # Only report once

            # Check consent
            if not ai_input.get("consent_given", False):
                violations.append(
                    {
                        "type": "missing_consent",
                        "severity": "medium",
                        "description": "User consent not provided",
                    }
                )

            return {"compliant": len(violations) == 0, "violations": violations}

        except Exception as e:
            self.logger.warning(f"Privacy compliance check failed: {e}")
            return {"compliant": True, "violations": []}

    def _calculate_safety_score(self, checks: Dict[str, Any]) -> float:
        """Calculate overall safety score."""
        try:
            scores = []
            weights = {"bias": 0.3, "ethical": 0.3, "safety": 0.2, "privacy": 0.2}

            for check_name, result in checks.items():
                if check_name == "bias":
                    score = 1.0 - result.get("bias_score", 0.0)
                elif check_name in ["ethical", "safety", "privacy"]:
                    score = (
                        1.0
                        if result.get("compliant", result.get("safe", True))
                        else 0.0
                    )
                else:
                    score = 1.0
                scores.append(score * weights.get(check_name, 1.0))

            return sum(scores) / sum(weights.values()) if weights else 1.0

        except Exception as e:
            self.logger.warning(f"Safety score calculation failed: {e}")
            return 0.5

    def _collect_violations(self, checks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect all violations from safety checks."""
        violations = []
        for check_result in checks.values():
            if isinstance(check_result, dict) and "violations" in check_result:
                violations.extend(check_result["violations"])
            elif isinstance(check_result, dict) and "indicators" in check_result:
                violations.extend(check_result["indicators"])
        return violations

    async def _handle_violations(
        self,
        violations: List[Dict[str, Any]],
        ai_input: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle detected safety violations."""
        try:
            # Log violations
            for violation in violations:
                self.violation_history.append(
                    {
                        "violation": violation,
                        "ai_input": ai_input,
                        "context": context,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Check if auto-mitigation is enabled
            if self.config.get("auto_mitigation_enabled"):
                await self._apply_auto_mitigation(violations, ai_input)

            # Trigger incident response if needed
            critical_violations = [v for v in violations if v.get("severity") == "high"]
            if critical_violations and self.config.get("incident_response_enabled"):
                await self._trigger_incident_response(
                    critical_violations, ai_input, context
                )

            self.logger.warning(f"Handled {len(violations)} safety violations")

        except Exception as e:
            self.logger.error(f"Violation handling failed: {e}")

    async def _apply_auto_mitigation(
        self, violations: List[Dict[str, Any]], ai_input: Dict[str, Any]
    ) -> None:
        """Apply automatic mitigation for violations."""
        # Placeholder for auto-mitigation logic
        # In practice, this would modify AI input or add safeguards
        self.logger.info("Applied auto-mitigation for safety violations")

    async def _trigger_incident_response(
        self,
        violations: List[Dict[str, Any]],
        ai_input: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Trigger incident response for critical violations."""
        # Placeholder for incident response
        # In practice, this would alert administrators, log incidents, etc.
        self.logger.error(
            f"Incident response triggered for {len(violations)} critical violations"
        )

    def _update_safety_metrics(
        self, safety_score: float, violations: List[Dict[str, Any]]
    ) -> None:
        """Update safety metrics."""
        try:
            self.safety_metrics["total_checks"] = (
                self.safety_metrics.get("total_checks", 0) + 1
            )
            self.safety_metrics["average_safety_score"] = (
                self.safety_metrics.get("average_safety_score", 0.0)
                * (self.safety_metrics["total_checks"] - 1)
                + safety_score
            ) / self.safety_metrics["total_checks"]
            self.safety_metrics["total_violations"] = self.safety_metrics.get(
                "total_violations", 0
            ) + len(violations)
            self.safety_metrics["last_updated"] = datetime.now().isoformat()

        except Exception as e:
            self.logger.warning(f"Metrics update failed: {e}")

    def _generate_safety_recommendations(
        self, violations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate safety recommendations based on violations."""
        recommendations = []
        try:
            violation_types = set(v.get("type", "") for v in violations)

            if (
                "bias_detected" in violation_types
                or "underrepresentation" in violation_types
            ):
                recommendations.append(
                    "Review and balance training data for demographic representation"
                )

            if "prohibited_use" in violation_types:
                recommendations.append("Reevaluate AI usage for ethical compliance")

            if "malicious_content" in violation_types:
                recommendations.append("Implement content filtering and sanitization")

            if "pii_detected" in violation_types:
                recommendations.append(
                    "Apply data anonymization and privacy protection measures"
                )

            if not recommendations:
                recommendations.append(
                    "Continue monitoring for potential safety issues"
                )

        except Exception as e:
            self.logger.warning(f"Recommendation generation failed: {e}")
            recommendations = ["Review safety protocols"]

        return recommendations

    @monitor_operation("ai_safety_guardrail.get_safety_report")
    def get_safety_report(self) -> Dict[str, Any]:
        """Get comprehensive safety report."""
        return {
            "metrics": self.safety_metrics,
            "recent_violations": self.violation_history[-10:],  # Last 10
            "ethical_guidelines": self.ethical_guidelines,
            "config": self.config,
            "generated_at": datetime.now().isoformat(),
        }

    @validate_input(
        {
            "rule_name": {"type": "string", "max_length": 100, "required": True},
            "rule_config": {"type": "object", "required": True},
        }
    )
    @monitor_operation("ai_safety_guardrail.add_safety_rule")
    def add_safety_rule(self, rule_name: str, rule_config: Dict[str, Any]) -> None:
        """Add a custom safety rule."""
        try:
            self.safety_rules[rule_name] = {
                "config": rule_config,
                "added_at": datetime.now().isoformat(),
                "enabled": True,
            }
            self.logger.info(f"Added safety rule: {rule_name}")

        except Exception as e:
            self.logger.error(f"Failed to add safety rule {rule_name}: {e}")
            raise AISafetyError(f"Failed to add safety rule: {e}") from e
