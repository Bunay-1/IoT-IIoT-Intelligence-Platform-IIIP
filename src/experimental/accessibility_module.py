"""
Accessibility Module for IoT Intelligence Platform.

This module ensures accessibility compliance, provides inclusive design frameworks,
integrates assistive technologies, and offers user-centric accessibility features.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import asyncio
import random

from src.core.config import settings
from src.utils.logging_config import get_logger


class AccessibilityError(Exception):
    """Base exception for accessibility module errors."""
    pass


class ComplianceError(AccessibilityError):
    """Raised when accessibility compliance fails."""
    pass


class DesignError(AccessibilityError):
    """Raised when design validation fails."""
    pass


class AccessibilityModule:
    """
    Accessibility Module for inclusive IoT interfaces.

    Provides compliance checking, inclusive design, assistive technology integration,
    and user-centric accessibility optimizations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the accessibility module with state for audit history.
        """
        self.config = config or {}
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.supported_standards = self.config.get('supported_standards', ['WCAG2.1', 'ADA', 'Section508'])

        # State management for audit history and user preferences
        self.audit_history: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.logger.info("Accessibility Module initialized with state management.")

    def _validate_config(self) -> None:
        """Configuration validation is handled in the constructor or methods."""
        pass

    def run_accessibility_audit(self, url: str, standards: List[str]) -> Dict[str, Any]:
        """
        Run a dynamic, simulated accessibility audit on a given URL.
        """
        self.logger.info(f"Starting dynamic accessibility audit for {url} against {standards}")

        possible_issues = [
            {"type": "Color Contrast", "severity": "Critical", "element": "button.primary", "message": "Low contrast (2.5:1)", "penalty": 20},
            {"type": "Alt Text", "severity": "Serious", "element": "img.product-image", "message": "Missing alt attribute", "penalty": 15},
            {"type": "Keyboard Navigation", "severity": "Critical", "element": "div.modal", "message": "Modal dialog traps keyboard focus", "penalty": 25},
            {"type": "Form Labels", "severity": "Serious", "element": "input#email", "message": "Input field is missing a label", "penalty": 15},
            {"type": "ARIA Roles", "severity": "Moderate", "element": "div.custom-checkbox", "message": "Missing ARIA role for custom checkbox", "penalty": 10},
            {"type": "Heading Structure", "severity": "Moderate", "element": "h3.section-title", "message": "Skipped heading level (h1 -> h3)", "penalty": 5},
            {"type": "Resizable Text", "severity": "Serious", "element": "p.caption", "message": "Text does not reflow correctly when resized", "penalty": 10},
        ]

        issues = []
        score = 100
        num_issues_to_find = random.randint(1, 4)

        found_issues_sample = random.sample(possible_issues, num_issues_to_find)

        for issue_template in found_issues_sample:
            issues.append({
                "type": issue_template["type"],
                "severity": issue_template["severity"],
                "element": issue_template["element"],
                "message": issue_template["message"],
            })
            score -= issue_template["penalty"]

        score = max(0, score) # Ensure score doesn't go below 0

        audit_result = {
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_score": score,
            "standards": standards,
            "issues_found": len(issues),
            "details": issues
        }

        self.audit_history.append(audit_result)
        self.logger.info(f"Dynamic audit for {url} completed with score {score}.")
        return audit_result

    def generate_audit_report(self, audit_id: int) -> str:
        """
        Generate a detailed string report for a specific audit from history.
        """
        if audit_id < 0 or audit_id >= len(self.audit_history):
            raise IndexError("Audit ID out of range.")

        result = self.audit_history[audit_id]
        report = f"Accessibility Report for {result['url']} ({result['timestamp']})\n"
        report += f"Overall Score: {result['overall_score']}/100\n"
        report += f"Standards Checked: {', '.join(result['standards'])}\n"
        report += "="*40 + "\n"

        if not result['details']:
            report += "No issues found. Great job!\n"
        else:
            for issue in result['details']:
                report += f"- Severity: {issue.get('severity', 'N/A')} | Type: {issue['type']} | Element: {issue['element']}\n"
                report += f"  Message: {issue['message']}\n\n"
        return report

    def get_audit_history(self) -> List[Dict[str, Any]]:
        """
        Retrieve the full history of accessibility audits.
        """
        return self.audit_history

    def inclusive_design_framework(self, design_principles: List[str]) -> Dict[str, Any]:
        """
        Provides guidance on applying inclusive design principles.
        """
        self.logger.info(f"Applying {len(design_principles)} inclusive design principles.")
        # This method is now more of a guideline provider than an active processor
        return {
            "status": "guidance_provided",
            "principles": design_principles,
            "recommendation": "Follow these principles during the design phase to ensure maximum accessibility.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def manage_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set or update accessibility preferences for a user.
        """
        self.logger.info(f"Updating accessibility preferences for user {user_id}")
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        self.user_preferences[user_id].update(preferences)
        return {"status": "success", "user_id": user_id, "preferences": self.user_preferences[user_id]}

    def simulate_screen_reader(self, html_element: str) -> str:
        """
        Simulate how a screen reader would interpret an HTML element.
        """
        # This is a simplified simulation
        if "<button" in html_element:
            text = html_element.split('>')[1].split('<')[0]
            return f"Button: '{text}'"
        elif "<img" in html_element:
            alt_text = html_element.split('alt="')[1].split('"')[0] if 'alt="' in html_element else "An image without a description"
            return f"Image: '{alt_text}'"
        else:
            return "Element type not recognized for screen reader simulation."

    def adapt_content_dynamically(self, html_content: str, user_id: str) -> str:
        """
        Adapt HTML content based on a user's accessibility preferences.
        """
        if user_id not in self.user_preferences:
            return html_content # No preferences set

        prefs = self.user_preferences[user_id]
        adapted_content = html_content

        if prefs.get("high_contrast"):
            adapted_content = f'<div class="high-contrast">{html_content}</div>'
        if prefs.get("font_size") == "large":
            adapted_content = f'<div style="font-size: 1.5em;">{adapted_content}</div>'

        return adapted_content

    async def async_accessibility_monitoring(self, url: str) -> Dict[str, Any]:
        """
        Asynchronously monitor a URL for accessibility issues over time.
        """
        try:
            self.logger.info(f"Starting async accessibility monitoring for {url}")
            await asyncio.sleep(0.1) # Simulate a check

            # For this simulation, we just run a new audit
            latest_audit = self.run_accessibility_audit(url, standards=['WCAG2.1'])

            return {
                "monitoring_status": "active",
                "url_monitored": url,
                "latest_score": latest_audit['overall_score'],
                "issues_detected": latest_audit['issues_found'],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Async accessibility monitoring failed: {e}")
            raise AccessibilityError(f"Failed to monitor accessibility: {e}") from e


# Global instance for state management
accessibility_manager = AccessibilityModule()

if __name__ == "__main__":
    async def main():
        print("--- Accessibility Module Demonstration ---")

        # 1. Run a dynamic accessibility audit
        print("\n--- Running Dynamic Accessibility Audit ---")
        audit_result = accessibility_manager.run_accessibility_audit("https://example.com", ["WCAG2.1"])
        print(f"Audit Score: {audit_result['overall_score']}/100")
        print(f"Issues Found: {audit_result['issues_found']}")

        # 2. Generate a report for the first audit
        print("\n--- Generating Audit Report ---")
        report = accessibility_manager.generate_audit_report(0)
        print(report)

        # 3. Manage User Preferences
        print("\n--- Managing User Accessibility Preferences ---")
        user_id = "user123"
        prefs = {"high_contrast": True, "font_size": "large"}
        accessibility_manager.manage_user_preferences(user_id, prefs)
        print(f"Preferences for {user_id}: {accessibility_manager.user_preferences[user_id]}")

        # 4. Simulate Screen Reader
        print("\n--- Simulating Screen Reader ---")
        button_html = '<button class="btn">Click Me</button>'
        image_html = '<img src="logo.png" alt="Company Logo">'
        print(f"Reading '{button_html}': {accessibility_manager.simulate_screen_reader(button_html)}")
        print(f"Reading '{image_html}': {accessibility_manager.simulate_screen_reader(image_html)}")

        # 5. Adapt Content Dynamically
        print("\n--- Adapting Content Dynamically ---")
        original_content = "<p>This is some text.</p>"
        adapted_content = accessibility_manager.adapt_content_dynamically(original_content, user_id)
        print(f"Original: {original_content}")
        print(f"Adapted for {user_id}: {adapted_content}")

        # 6. Asynchronous Monitoring
        print("\n--- Async Accessibility Monitoring ---")
        monitoring_result = await accessibility_manager.async_accessibility_monitoring("https://example.com")
        print(monitoring_result)

    asyncio.run(main())
