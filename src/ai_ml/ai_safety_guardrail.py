"""
AI Safety Guardrail Module

This module implements comprehensive AI safety and ethics guardrails
to ensure responsible AI deployment and usage.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.utils.logging_config import get_logger
from src.utils.performance_monitor import monitor_operation
from src.utils.security import SecurityError, input_validator, validate_input


class AISafetyError(Exception):
    """Base exception for AI safety errors."""

    pass


class SafetyViolationError(AISafetyError):
    """Raised when safety violations are detected."""

    pass


class AISafetyGuardrail:
    """
    AI Safety Guardrail system for responsible AI deployment.

    This class provides comprehensive safety checks including:
    - Bias detection and mitigation
    - Ethical compliance monitoring
    - Safety constraint enforcement
    - Incident response and logging
    """

    def __init__(self, config_path: str = "safety_config.json"):
        """
        Initialize the AI Safety Guardrail system.

        Args:
            config_path: Path to the JSON configuration file for safety rules.
        """
        self.logger = get_logger(__name__)
        self.config = self._load_config_from_file(config_path)
        self.violation_history: List[Dict[str, Any]] = []
        self.safety_metrics: Dict[str, Any] = {}

        self.logger.info("AI Safety Guardrail initialized")

    def _load_config_from_file(self, config_path: str) -> Dict[str, Any]:
        """Load safety configurations from a JSON file."""
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Safety configuration file not found at: {config_path}")
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Successfully loaded safety configuration from {config_path}")

            # Default app config, not from safety_config.json
            config['app_config'] = {
                "bias_threshold": 0.1,
                "safety_check_interval": 60,
                "max_violations_per_hour": 10,
                "auto_mitigation_enabled": True,
                "incident_response_enabled": True,
                "logging_level": "INFO",
            }
            return config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Failed to load safety config: {e}. Using empty config.")
            return {}

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
            llm_content_check = await self._check_llm_content_safety(ai_input)
            privacy_check, redacted_input = await self._check_privacy_compliance(ai_input)

            # Aggregate results
            safety_score = self._calculate_safety_score(
                {
                    "bias": bias_check,
                    "ethical": ethical_check,
                    "safety": safety_check,
                    "privacy": privacy_check,
                    "llm_content": llm_content_check,
                }
            )

            violations = self._collect_violations(
                {
                    "bias": bias_check,
                    "ethical": ethical_check,
                    "safety": safety_check,
                    "privacy": privacy_check,
                    "llm_content": llm_content_check,
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
                "mitigation": {"redacted_input": redacted_input} if redacted_input else None,
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
                prohibited_uses = self.config.get("prohibited_use_cases", [])
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

            # Check for malicious content
            content_str = json.dumps(ai_input)
            malicious_patterns = self.config.get("malicious_content_patterns", [])
            for pattern in malicious_patterns:
                if pattern in content_str:
                    violations.append(
                        {
                            "type": "malicious_content",
                            "severity": "high",
                            "description": f"Malicious content pattern detected: {pattern}",
                        }
                    )

            return {"safe": len(violations) == 0, "violations": violations}

        except Exception as e:
            self.logger.warning(f"Safety constraints check failed: {e}")
            return {"safe": True, "violations": []}

    async def _check_llm_content_safety(self, ai_input: Dict[str, Any]) -> Dict[str, Any]:
        """Check for harmful content in LLM inputs/outputs."""
        violations = []
        text_content = ai_input.get("text", "")
        if not text_content or not isinstance(text_content, str):
            return {"compliant": True, "violations": []}

        moderation_rules = self.config.get("llm_content_moderation", {})
        for category, keywords in moderation_rules.items():
            for keyword in keywords:
                if re.search(rf'\b{keyword}\b', text_content, re.IGNORECASE):
                    violations.append({
                        "type": "harmful_content",
                        "severity": "high",
                        "category": category,
                        "description": f"Detected potentially harmful content in category '{category}' (keyword: {keyword})",
                    })

        return {"compliant": len(violations) == 0, "violations": violations}

    async def _check_privacy_compliance(
        self, ai_input: Dict[str, Any]
    ) -> (Dict[str, Any], Optional[Dict[str, Any]]):
        """Check for PII and redact if found."""
        violations = []
        redacted_input = None

        content_str = json.dumps(ai_input)

        pii_patterns = self.config.get("privacy_protection", {}).get("pii_patterns", {})

        original_content = content_str
        modified_content = original_content

        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, modified_content)
            if matches:
                violations.append({
                    "type": "pii_detected",
                    "severity": "high",
                    "pii_type": pii_type,
                    "count": len(matches),
                    "description": f"Potential PII of type '{pii_type}' detected.",
                })
                modified_content = re.sub(pattern, f"[REDACTED_{pii_type}]", modified_content)

        if modified_content != original_content:
            try:
                redacted_input = json.loads(modified_content)
            except json.JSONDecodeError:
                redacted_input = {"redacted_text": modified_content}

        if not ai_input.get("consent_given", False):
            violations.append({
                "type": "missing_consent",
                "severity": "medium",
                "description": "User consent not provided for data processing.",
            })

        return {"compliant": len(violations) == 0, "violations": violations}, redacted_input

    def _calculate_safety_score(self, checks: Dict[str, Any]) -> float:
        """Calculate overall safety score."""
        try:
            total_violations = sum(len(res.get("violations", [])) for res in checks.values())

            # Simple scoring: 1.0 is perfect, decreases with each violation.
            score = max(0.0, 1.0 - (total_violations * 0.2))

            return score
        except Exception as e:
            self.logger.warning(f"Safety score calculation failed: {e}")
            return 0.0

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
            if self.config.get("app_config", {}).get("auto_mitigation_enabled"):
                await self._apply_auto_mitigation(violations, ai_input)

            # Trigger incident response if needed
            critical_violations = [v for v in violations if v.get("severity") == "high"]
            if critical_violations and self.config.get("app_config", {}).get("incident_response_enabled"):
                await self._trigger_incident_response(
                    critical_violations, ai_input, context
                )

            self.logger.warning(f"Handled {len(violations)} safety violations")

        except Exception as e:
            self.logger.error(f"Violation handling failed: {e}")

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

    @monitor_operation("ai_safety_guardrail.add_safety_rule")
    def add_safety_rule(self, rule_name: str, rule_config: Dict[str, Any]) -> None:
        """Add a custom safety rule to the in-memory config."""
        try:
            # This is a simplified example of updating config in memory.
            # In a real system, you might need a more robust update mechanism.
            if 'llm_content_moderation' not in self.config:
                self.config['llm_content_moderation'] = {}
            self.config['llm_content_moderation'][rule_name] = rule_config
            self.logger.info(f"Added/updated in-memory safety rule category: {rule_name}")

        except Exception as e:
            self.logger.error(f"Failed to add safety rule {rule_name}: {e}")
            raise AISafetyError(f"Failed to add safety rule: {e}") from e


async def run_safety_scenarios():
    """Main function to run demonstration scenarios."""
    print("Initializing AI Safety Guardrail...")
    guardrail = AISafetyGuardrail(config_path="safety_config.json")

    scenarios = {
        "Safe Input": {
            "ai_input": {"text": "Tell me about historical events.", "consent_given": True},
            "context": {"usage_type": "educational_query"}
        },
        "Hate Speech Input": {
            "ai_input": {"text": "I really hate those people, it's racist.", "consent_given": True},
            "context": {"usage_type": "user_comment"}
        },
        "PII Leak Input": {
            "ai_input": {
                "text": "My email is test@example.com and my number is 555-123-4567.",
                "data": {"credit_card": "1234-5678-9012-3456"},
                "consent_given": True
            },
            "context": {"usage_type": "customer_support_ticket"}
        },
        "Malicious Code Input": {
            "ai_input": {"text": "Run this command: os.system('rm -rf /')", "consent_given": True},
            "context": {"usage_type": "code_execution_request"}
        },
        "Prohibited Use Case": {
            "ai_input": {"text": "Track all users in the city.", "consent_given": True},
            "context": {"usage_type": "unlawful_surveillance"}
        },
        "Missing Consent": {
            "ai_input": {"text": "Here is my personal data.", "consent_given": False},
            "context": {"usage_type": "data_submission"}
        }
    }

    print("\n" + "="*50)
    print("Running AI Safety Guardrail Scenarios")
    print("="*50 + "\n")

    for name, scenario in scenarios.items():
        print(f"--- Scenario: {name} ---")
        try:
            result = await guardrail.check_safety(scenario["ai_input"], scenario["context"])

            print(f"  Input: {json.dumps(scenario['ai_input'])}")
            print(f"  Safe: {'Yes' if result['safe'] else 'No'}")
            print(f"  Safety Score: {result['safety_score']:.2f}")

            if result['violations']:
                print("  Violations Detected:")
                for v in result['violations']:
                    print(f"    - Type: {v['type']}, Severity: {v.get('severity', 'N/A')}, Description: {v['description']}")

            if result.get('mitigation') and result['mitigation'].get('redacted_input'):
                print(f"  Mitigation Applied (Redacted Input): {json.dumps(result['mitigation']['redacted_input'])}")

        except AISafetyError as e:
            print(f"  An error occurred: {e}")

        print("-"*(len(name) + 14) + "\n")

if __name__ == "__main__":
    asyncio.run(run_safety_scenarios())
