"""
Security Audit and Hardening Tools for IoT IIoT Platform
Security assessment, vulnerability scanning, and hardening recommendations
"""

import asyncio
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import ipaddress
import aiohttp

from utils.logging_config import get_logger

logger = get_logger(__name__)


class SecurityAudit:
    """
    Security audit and vulnerability assessment tool.
    """

    def __init__(self):
        self.findings: List[Dict[str, Any]] = []
        self.risk_levels = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 1,
            "info": 0
        }

    def add_finding(
        self,
        title: str,
        description: str,
        risk_level: str,
        category: str,
        recommendation: str,
        evidence: Optional[Any] = None,
        cve: Optional[str] = None
    ):
        """Add a security finding."""
        finding = {
            "id": f"SEC-{len(self.findings) + 1:03d}",
            "title": title,
            "description": description,
            "risk_level": risk_level,
            "risk_score": self.risk_levels.get(risk_level, 0),
            "category": category,
            "recommendation": recommendation,
            "evidence": evidence,
            "cve": cve,
            "timestamp": datetime.now().isoformat(),
            "status": "open"
        }

        self.findings.append(finding)
        logger.warning(f"Security finding: {title} ({risk_level})")

    async def run_full_audit(self, target_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """
        Run comprehensive security audit.

        Args:
            target_url: Target API URL

        Returns:
            Audit results
        """
        logger.info("Starting comprehensive security audit")

        self.findings = []

        # Run various security checks
        await self._check_api_security(target_url)
        await self._check_authentication_security()
        await self._check_data_security()
        await self._check_infrastructure_security()
        self._check_code_security()

        # Calculate risk score
        total_risk = sum(f["risk_score"] for f in self.findings)
        max_risk = len(self.findings) * 10
        risk_percentage = (total_risk / max_risk) * 100 if max_risk > 0 else 0

        audit_results = {
            "timestamp": datetime.now().isoformat(),
            "target": target_url,
            "total_findings": len(self.findings),
            "findings_by_risk": self._group_findings_by_risk(),
            "findings_by_category": self._group_findings_by_category(),
            "overall_risk_score": total_risk,
            "risk_percentage": risk_percentage,
            "recommendations": self._generate_recommendations(),
            "findings": self.findings
        }

        logger.info(f"Security audit completed: {len(self.findings)} findings, risk score: {total_risk}")
        return audit_results

    async def _check_api_security(self, target_url: str):
        """Check API security."""
        try:
            async with aiohttp.ClientSession() as session:
                # Check for common vulnerabilities

                # Test SQL injection
                test_payloads = [
                    "' OR '1'='1",
                    "'; DROP TABLE users; --",
                    "<script>alert('xss')</script>",
                    "../../../etc/passwd"
                ]

                for payload in test_payloads:
                    try:
                        # Test login endpoint
                        async with session.post(
                            f"{target_url}/api/v1/auth/login",
                            json={"username": payload, "password": "test"},
                            timeout=5
                        ) as response:
                            if response.status == 200:
                                self.add_finding(
                                    "Potential SQL Injection Vulnerability",
                                    f"Login endpoint accepts suspicious input: {payload}",
                                    "high",
                                    "Injection",
                                    "Implement proper input validation and parameterized queries",
                                    f"Response status: {response.status}"
                                )
                    except:
                        pass

                # Check security headers
                async with session.get(f"{target_url}/", timeout=5) as response:
                    headers = dict(response.headers)

                    security_headers = [
                        "X-Content-Type-Options",
                        "X-Frame-Options",
                        "X-XSS-Protection",
                        "Content-Security-Policy",
                        "Strict-Transport-Security"
                    ]

                    missing_headers = []
                    for header in security_headers:
                        if header not in headers:
                            missing_headers.append(header)

                    if missing_headers:
                        self.add_finding(
                            "Missing Security Headers",
                            f"API responses missing important security headers: {', '.join(missing_headers)}",
                            "medium",
                            "Headers",
                            "Add security headers middleware to all responses",
                            f"Missing: {missing_headers}"
                        )

                # Check for information disclosure
                async with session.get(f"{target_url}/api/health", timeout=5) as response:
                    if "server" in dict(response.headers).get("Server", "").lower():
                        self.add_finding(
                            "Server Information Disclosure",
                            "Server header reveals technology stack information",
                            "low",
                            "Information Disclosure",
                            "Configure server to not disclose version information",
                            f"Server: {response.headers.get('Server')}"
                        )

        except Exception as e:
            logger.error(f"API security check failed: {e}")

    async def _check_authentication_security(self):
        """Check authentication security."""
        # Check password policies
        # This would require access to user database

        # Check for weak default passwords
        self.add_finding(
            "Default Admin Password",
            "System may be using default admin credentials",
            "high",
            "Authentication",
            "Change default admin password and implement password complexity requirements",
            "Check settings for default credentials"
        )

        # Check session management
        self.add_finding(
            "Session Security Review",
            "Review JWT token expiration and refresh mechanisms",
            "medium",
            "Authentication",
            "Implement proper session timeout and token refresh policies",
            "Check JWT configuration"
        )

    async def _check_data_security(self):
        """Check data security."""
        # Check encryption at rest
        self.add_finding(
            "Data Encryption at Rest",
            "Verify that sensitive data is encrypted in the database",
            "medium",
            "Data Protection",
            "Implement database-level encryption for sensitive data",
            "Check database encryption settings"
        )

        # Check data transmission security
        self.add_finding(
            "TLS Configuration",
            "Ensure all API communications use TLS 1.3",
            "high",
            "Data Protection",
            "Configure TLS 1.3 and disable older protocols",
            "Check SSL/TLS configuration"
        )

        # Check API rate limiting
        self.add_finding(
            "Rate Limiting",
            "Implement rate limiting to prevent abuse",
            "medium",
            "Access Control",
            "Add rate limiting middleware to API endpoints",
            "Check for rate limiting implementation"
        )

    async def _check_infrastructure_security(self):
        """Check infrastructure security."""
        # Check for exposed ports
        self.add_finding(
            "Port Exposure Review",
            "Audit which ports are exposed and their necessity",
            "medium",
            "Infrastructure",
            "Close unnecessary ports and implement firewall rules",
            "Check running services and open ports"
        )

        # Check container security
        self.add_finding(
            "Container Security",
            "Ensure containers run as non-root and have minimal privileges",
            "medium",
            "Infrastructure",
            "Configure containers with security best practices",
            "Check Docker/Kubernetes security configurations"
        )

    def _check_code_security(self):
        """Check code for security issues."""
        # This would scan source code for common vulnerabilities
        # For now, add general recommendations

        self.add_finding(
            "Input Validation",
            "Ensure all user inputs are properly validated",
            "high",
            "Input Validation",
            "Implement comprehensive input validation using Pydantic models",
            "Review API input models"
        )

        self.add_finding(
            "Dependency Vulnerabilities",
            "Regularly scan dependencies for known vulnerabilities",
            "medium",
            "Dependencies",
            "Use tools like safety or pip-audit to check dependencies",
            "Run dependency vulnerability scan"
        )

    def _group_findings_by_risk(self) -> Dict[str, int]:
        """Group findings by risk level."""
        groups = {}
        for finding in self.findings:
            risk = finding["risk_level"]
            groups[risk] = groups.get(risk, 0) + 1
        return groups

    def _group_findings_by_category(self) -> Dict[str, int]:
        """Group findings by category."""
        groups = {}
        for finding in self.findings:
            category = finding["category"]
            groups[category] = groups.get(category, 0) + 1
        return groups

    def _generate_recommendations(self) -> List[str]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Sort findings by risk score
        sorted_findings = sorted(self.findings, key=lambda x: x["risk_score"], reverse=True)

        for finding in sorted_findings[:10]:  # Top 10 recommendations
            recommendations.append(f"[{finding['risk_level'].upper()}] {finding['recommendation']}")

        return recommendations

    def generate_report(self, filepath: str):
        """Generate security audit report."""
        report = {
            "security_audit_report": {
                "generated_at": datetime.now().isoformat(),
                "total_findings": len(self.findings),
                "executive_summary": self._generate_executive_summary(),
                "findings": self.findings,
                "recommendations": self._generate_recommendations()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Security audit report saved to {filepath}")

    def _generate_executive_summary(self) -> str:
        """Generate executive summary."""
        risk_counts = self._group_findings_by_risk()

        summary = f"Security audit identified {len(self.findings)} findings. "
        summary += f"Critical: {risk_counts.get('critical', 0)}, "
        summary += f"High: {risk_counts.get('high', 0)}, "
        summary += f"Medium: {risk_counts.get('medium', 0)}, "
        summary += f"Low: {risk_counts.get('low', 0)}. "

        if self.findings:
            top_risk = max(self.findings, key=lambda x: x["risk_score"])
            summary += f"Top risk: {top_risk['title']}."

        return summary


class SecurityHardening:
    """
    Security hardening tools and recommendations.
    """

    def __init__(self):
        self.hardening_actions: List[Dict[str, Any]] = []

    def add_hardening_action(
        self,
        title: str,
        description: str,
        implementation: str,
        priority: str,
        automated: bool = False
    ):
        """Add a hardening action."""
        action = {
            "title": title,
            "description": description,
            "implementation": implementation,
            "priority": priority,
            "automated": automated,
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }

        self.hardening_actions.append(action)

    def generate_hardening_plan(self) -> Dict[str, Any]:
        """Generate security hardening plan."""
        # Add common hardening actions
        self._add_common_hardening_actions()

        plan = {
            "hardening_plan": {
                "generated_at": datetime.now().isoformat(),
                "total_actions": len(self.hardening_actions),
                "actions_by_priority": self._group_actions_by_priority(),
                "automated_actions": len([a for a in self.hardening_actions if a["automated"]]),
                "manual_actions": len([a for a in self.hardening_actions if not a["automated"]]),
                "actions": self.hardening_actions
            }
        }

        return plan

    def _add_common_hardening_actions(self):
        """Add common security hardening actions."""
        self.add_hardening_action(
            "Implement Security Headers",
            "Add security headers to all HTTP responses",
            "Add CORS middleware with security headers (HSTS, CSP, X-Frame-Options, etc.)",
            "high",
            True
        )

        self.add_hardening_action(
            "Enable Rate Limiting",
            "Implement rate limiting to prevent abuse",
            "Add rate limiting middleware using Redis for distributed rate limiting",
            "high",
            True
        )

        self.add_hardening_action(
            "Strengthen Password Policies",
            "Implement strong password requirements",
            "Configure password complexity, expiration, and history policies",
            "high",
            False
        )

        self.add_hardening_action(
            "Enable Audit Logging",
            "Implement comprehensive audit logging",
            "Log all authentication, authorization, and sensitive operations",
            "medium",
            True
        )

        self.add_hardening_action(
            "Regular Security Updates",
            "Keep dependencies and system updated",
            "Implement automated dependency updates and security patching",
            "medium",
            False
        )

        self.add_hardening_action(
            "Database Encryption",
            "Encrypt sensitive data at rest",
            "Configure database encryption and key management",
            "high",
            False
        )

        self.add_hardening_action(
            "API Input Validation",
            "Implement strict input validation",
            "Use Pydantic models with comprehensive validation rules",
            "high",
            True
        )

        self.add_hardening_action(
            "Zero-Trust Architecture",
            "Implement zero-trust security model",
            "Verify all requests, implement micro-segmentation",
            "medium",
            False
        )

    def _group_actions_by_priority(self) -> Dict[str, int]:
        """Group actions by priority."""
        groups = {}
        for action in self.hardening_actions:
            priority = action["priority"]
            groups[priority] = groups.get(priority, 0) + 1
        return groups


async def run_security_audit(target_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Run complete security audit.

    Args:
        target_url: Target API URL

    Returns:
        Audit results
    """
    audit = SecurityAudit()
    results = await audit.run_full_audit(target_url)

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"security_audit_{timestamp}.json"
    audit.generate_report(filename)

    return results


def generate_hardening_plan() -> Dict[str, Any]:
    """
    Generate security hardening plan.

    Returns:
        Hardening plan
    """
    hardening = SecurityHardening()
    return hardening.generate_hardening_plan()


if __name__ == "__main__":
    # Run security audit
    import sys

    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    async def main():
        results = await run_security_audit(target_url)
        print(json.dumps(results, indent=2, default=str))

    asyncio.run(main())