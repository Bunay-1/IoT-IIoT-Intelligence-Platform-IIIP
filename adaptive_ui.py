"""
Adaptive User Interface Module

This module implements adaptive user interface capabilities for the IoT IIoT platform,
providing personalized, context-aware, and responsive UI experiences.
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum

from utils.logging_config import get_logger

logger = get_logger(__name__)


class DeviceType(Enum):
    """Device types for UI adaptation."""
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"
    WEARABLE = "wearable"
    TV = "tv"
    IOT_DEVICE = "iot_device"


class UserRole(Enum):
    """User roles for UI customization."""
    ADMIN = "admin"
    OPERATOR = "operator"
    ENGINEER = "engineer"
    MANAGER = "manager"
    VIEWER = "viewer"


class UIContext(Enum):
    """UI context types."""
    DASHBOARD = "dashboard"
    MONITORING = "monitoring"
    ANALYTICS = "analytics"
    CONFIGURATION = "configuration"
    ALERTS = "alerts"
    REPORTING = "reporting"


class AdaptiveUserInterface:
    """
    Adaptive User Interface system for personalized experiences.

    Features:
    - Device-aware UI adaptation
    - User preference learning
    - Context-aware layouts
    - Accessibility compliance
    - Real-time UI optimization
    - A/B testing and personalization
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # User profiles and preferences
        self.user_profiles: Dict[str, Dict] = {}

        # UI templates and layouts
        self.ui_templates: Dict[str, Dict] = {}

        # Device capabilities
        self.device_profiles: Dict[str, Dict] = {}

        # Context-aware rules
        self.context_rules: Dict[str, List[Dict]] = defaultdict(list)

        # A/B testing configurations
        self.ab_tests: Dict[str, Dict] = {}

        # UI performance metrics
        self.ui_metrics: Dict[str, Dict] = defaultdict(dict)

        # User interaction history
        self.interaction_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Accessibility settings
        self.accessibility_profiles: Dict[str, Dict] = {}

        self.logger = get_logger(__name__)
        self.logger.info("Adaptive User Interface initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "enable_personalization": True,
            "enable_context_awareness": True,
            "enable_ab_testing": False,
            "max_user_history": 1000,
            "ui_update_interval": 300,  # 5 minutes
            "performance_monitoring": True,
            "accessibility_compliance": True,
            "default_theme": "light",
            "supported_languages": ["en", "bg", "de", "fr", "es"],
        }

    def create_user_profile(
        self,
        user_id: str,
        user_info: Dict,
        preferences: Optional[Dict] = None
    ) -> bool:
        """
        Create user profile for UI adaptation.

        Args:
            user_id: Unique user identifier
            user_info: User information
            preferences: User preferences

        Returns:
            Profile creation success
        """
        try:
            profile = {
                "user_id": user_id,
                "info": user_info,
                "preferences": preferences or {},
                "created_at": datetime.now(),
                "last_active": None,
                "device_history": [],
                "ui_interactions": {
                    "total_sessions": 0,
                    "avg_session_duration": 0,
                    "preferred_layouts": {},
                    "click_patterns": {},
                    "accessibility_needs": {}
                },
                "context_history": [],
                "ab_test_assignments": {},
                "performance_metrics": {
                    "load_times": [],
                    "error_rates": [],
                    "satisfaction_scores": []
                }
            }

            self.user_profiles[user_id] = profile

            # Initialize interaction history
            self.interaction_history[user_id] = deque(maxlen=self.config["max_user_history"])

            self.logger.info(f"Created user profile: {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"User profile creation failed: {e}")
            return False

    def register_device_profile(
        self,
        device_id: str,
        device_type: DeviceType,
        capabilities: Dict
    ) -> bool:
        """
        Register device profile for UI adaptation.

        Args:
            device_id: Device identifier
            device_type: Type of device
            capabilities: Device capabilities

        Returns:
            Registration success
        """
        try:
            profile = {
                "device_id": device_id,
                "type": device_type.value,
                "capabilities": capabilities,
                "screen_size": capabilities.get("screen_size", {}),
                "input_methods": capabilities.get("input_methods", ["touch"]),
                "supported_features": capabilities.get("supported_features", []),
                "performance_class": capabilities.get("performance_class", "standard"),
                "registered_at": datetime.now(),
                "usage_stats": {
                    "total_sessions": 0,
                    "avg_load_time": 0.0,
                    "error_count": 0
                }
            }

            self.device_profiles[device_id] = profile

            self.logger.info(f"Registered device profile: {device_id} ({device_type.value})")
            return True

        except Exception as e:
            self.logger.error(f"Device profile registration failed: {e}")
            return False

    def create_ui_template(
        self,
        template_name: str,
        template_type: str,
        base_layout: Dict,
        adaptive_rules: Optional[List[Dict]] = None
    ) -> bool:
        """
        Create UI template with adaptive rules.

        Args:
            template_name: Template name
            template_type: Type of template
            base_layout: Base layout configuration
            adaptive_rules: Adaptive rules

        Returns:
            Template creation success
        """
        try:
            template = {
                "name": template_name,
                "type": template_type,
                "base_layout": base_layout,
                "adaptive_rules": adaptive_rules or [],
                "created_at": datetime.now(),
                "version": "1.0",
                "usage_stats": {
                    "total_views": 0,
                    "avg_load_time": 0.0,
                    "user_satisfaction": 0.0
                },
                "ab_test_variants": {}
            }

            self.ui_templates[template_name] = template

            self.logger.info(f"Created UI template: {template_name}")
            return True

        except Exception as e:
            self.logger.error(f"UI template creation failed: {e}")
            return False

    async def generate_adaptive_ui(
        self,
        user_id: str,
        device_id: str,
        context: UIContext,
        base_template: str,
        user_context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate adaptive UI configuration for user.

        Args:
            user_id: User identifier
            device_id: Device identifier
            context: UI context
            base_template: Base template name
            user_context: Additional user context

        Returns:
            Adaptive UI configuration
        """
        try:
            # Get user profile
            user_profile = self.user_profiles.get(user_id)
            if not user_profile:
                # Create default profile
                self.create_user_profile(user_id, {"role": "viewer"})
                user_profile = self.user_profiles[user_id]

            # Get device profile
            device_profile = self.device_profiles.get(device_id)
            if not device_profile:
                # Assume desktop as default
                self.register_device_profile(device_id, DeviceType.DESKTOP, {})
                device_profile = self.device_profiles[device_id]

            # Get base template
            template = self.ui_templates.get(base_template)
            if not template:
                return {"error": "Template not found"}

            # Start with base layout
            ui_config = template["base_layout"].copy()

            # Apply device adaptation
            ui_config = await self._apply_device_adaptation(ui_config, device_profile)

            # Apply user preferences
            ui_config = await self._apply_user_preferences(ui_config, user_profile)

            # Apply context awareness
            ui_config = await self._apply_context_awareness(ui_config, context, user_context or {})

            # Apply accessibility settings
            ui_config = await self._apply_accessibility(ui_config, user_profile)

            # Apply A/B testing
            ui_config = await self._apply_ab_testing(ui_config, user_id, base_template)

            # Record interaction
            await self._record_ui_interaction(user_id, device_id, context, ui_config)

            # Update user profile
            user_profile["last_active"] = datetime.now()
            user_profile["device_history"].append({
                "device_id": device_id,
                "timestamp": datetime.now(),
                "context": context.value
            })

            return ui_config

        except Exception as e:
            self.logger.error(f"Adaptive UI generation failed: {e}")
            return {"error": str(e)}

    async def _apply_device_adaptation(self, ui_config: Dict, device_profile: Dict) -> Dict:
        """Apply device-specific adaptations."""
        device_type = DeviceType(device_profile["type"])
        capabilities = device_profile["capabilities"]

        adapted_config = ui_config.copy()

        # Screen size adaptations
        screen_size = capabilities.get("screen_size", {})
        width = screen_size.get("width", 1920)
        height = screen_size.get("height", 1080)

        if device_type == DeviceType.MOBILE:
            # Mobile optimizations
            adapted_config["layout"] = "single_column"
            adapted_config["font_size"] = "small"
            adapted_config["touch_targets"] = "large"
            adapted_config["navigation"] = "bottom_tabs"

        elif device_type == DeviceType.TABLET:
            # Tablet optimizations
            adapted_config["layout"] = "two_column"
            adapted_config["font_size"] = "medium"
            adapted_config["navigation"] = "side_menu"

        elif device_type == DeviceType.WEARABLE:
            # Wearable optimizations
            adapted_config["layout"] = "minimal"
            adapted_config["font_size"] = "tiny"
            adapted_config["content"] = "essentials_only"

        elif device_type == DeviceType.TV:
            # TV optimizations
            adapted_config["layout"] = "grid"
            adapted_config["font_size"] = "large"
            adapted_config["navigation"] = "remote_control"

        # Performance adaptations
        performance_class = capabilities.get("performance_class", "standard")
        if performance_class == "low":
            adapted_config["animations"] = "disabled"
            adapted_config["complex_visuals"] = "simplified"

        return adapted_config

    async def _apply_user_preferences(self, ui_config: Dict, user_profile: Dict) -> Dict:
        """Apply user preferences."""
        preferences = user_profile.get("preferences", {})

        adapted_config = ui_config.copy()

        # Theme preference
        if "theme" in preferences:
            adapted_config["theme"] = preferences["theme"]

        # Language preference
        if "language" in preferences:
            adapted_config["language"] = preferences["language"]

        # Layout preferences
        if "layout_style" in preferences:
            adapted_config["layout_style"] = preferences["layout_style"]

        # Dashboard customization
        if "dashboard_widgets" in preferences:
            adapted_config["widgets"] = preferences["dashboard_widgets"]

        # Notification preferences
        if "notification_settings" in preferences:
            adapted_config["notifications"] = preferences["notification_settings"]

        return adapted_config

    async def _apply_context_awareness(self, ui_config: Dict, context: UIContext, user_context: Dict) -> Dict:
        """Apply context-aware adaptations."""
        adapted_config = ui_config.copy()

        # Time-based adaptations
        current_hour = datetime.now().hour
        if 6 <= current_hour < 18:
            adapted_config["color_scheme"] = "bright"
        else:
            adapted_config["color_scheme"] = "dark"

        # Location-based adaptations
        user_location = user_context.get("location")
        if user_location:
            # Adjust based on timezone or region
            timezone = user_location.get("timezone", "UTC")
            adapted_config["timezone"] = timezone

        # Role-based adaptations
        user_role = user_context.get("role", "viewer")
        if user_role == "admin":
            adapted_config["show_advanced_features"] = True
            adapted_config["permissions"] = "full"
        elif user_role == "operator":
            adapted_config["show_realtime_data"] = True
            adapted_config["alert_priority"] = "high"

        # Context-specific adaptations
        if context == UIContext.DASHBOARD:
            adapted_config["refresh_interval"] = 30
            adapted_config["show_kpis"] = True
        elif context == UIContext.MONITORING:
            adapted_config["auto_refresh"] = True
            adapted_config["alert_badges"] = True
        elif context == UIContext.ALERTS:
            adapted_config["notification_banners"] = True
            adapted_config["priority_filtering"] = True

        return adapted_config

    async def _apply_accessibility(self, ui_config: Dict, user_profile: Dict) -> Dict:
        """Apply accessibility settings."""
        if not self.config["accessibility_compliance"]:
            return ui_config

        accessibility = user_profile.get("ui_interactions", {}).get("accessibility_needs", {})

        adapted_config = ui_config.copy()

        # Screen reader support
        if accessibility.get("screen_reader"):
            adapted_config["aria_labels"] = True
            adapted_config["keyboard_navigation"] = True

        # High contrast
        if accessibility.get("high_contrast"):
            adapted_config["theme"] = "high_contrast"

        # Large text
        if accessibility.get("large_text"):
            adapted_config["font_size"] = "large"
            adapted_config["spacing"] = "increased"

        # Reduced motion
        if accessibility.get("reduced_motion"):
            adapted_config["animations"] = "minimal"

        # Color blindness support
        color_blindness = accessibility.get("color_blindness")
        if color_blindness:
            adapted_config["color_scheme"] = f"color_blind_{color_blindness}"

        return adapted_config

    async def _apply_ab_testing(self, ui_config: Dict, user_id: str, template_name: str) -> Dict:
        """Apply A/B testing variants."""
        if not self.config["enable_ab_testing"]:
            return ui_config

        template = self.ui_templates.get(template_name)
        if not template or not template.get("ab_test_variants"):
            return ui_config

        # Check if user is already assigned to a variant
        user_profile = self.user_profiles.get(user_id, {})
        test_assignments = user_profile.get("ab_test_assignments", {})

        if template_name in test_assignments:
            variant = test_assignments[template_name]
        else:
            # Assign user to a variant
            variants = list(template["ab_test_variants"].keys())
            variant = variants[hash(user_id) % len(variants)]
            test_assignments[template_name] = variant
            user_profile["ab_test_assignments"] = test_assignments

        # Apply variant modifications
        variant_config = template["ab_test_variants"][variant]
        adapted_config = ui_config.copy()
        adapted_config.update(variant_config)

        return adapted_config

    async def _record_ui_interaction(
        self,
        user_id: str,
        device_id: str,
        context: UIContext,
        ui_config: Dict
    ):
        """Record UI interaction for learning."""
        interaction = {
            "timestamp": datetime.now(),
            "user_id": user_id,
            "device_id": device_id,
            "context": context.value,
            "ui_config": ui_config,
            "session_id": str(uuid.uuid4())[:8]
        }

        self.interaction_history[user_id].append(interaction)

        # Update user profile
        user_profile = self.user_profiles[user_id]
        user_profile["ui_interactions"]["total_sessions"] += 1

        # Learn from interactions (simplified)
        await self._learn_from_interaction(user_id, interaction)

    async def _learn_from_interaction(self, user_id: str, interaction: Dict):
        """Learn user preferences from interactions."""
        # Simplified learning - in real implementation would use ML
        user_profile = self.user_profiles[user_id]
        preferences = user_profile.get("preferences", {})

        context = interaction["context"]
        ui_config = interaction["ui_config"]

        # Learn preferred layouts
        layout = ui_config.get("layout")
        if layout:
            preferred_layouts = user_profile["ui_interactions"]["preferred_layouts"]
            preferred_layouts[layout] = preferred_layouts.get(layout, 0) + 1

        # Learn theme preferences
        theme = ui_config.get("theme")
        if theme:
            if "preferred_theme" not in preferences:
                preferences["preferred_theme"] = theme
            # Could implement more sophisticated learning here

    def update_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """Update user preferences."""
        if user_id not in self.user_profiles:
            return False

        user_profile = self.user_profiles[user_id]
        user_profile["preferences"].update(preferences)

        self.logger.info(f"Updated preferences for user: {user_id}")
        return True

    def set_accessibility_profile(self, user_id: str, accessibility_settings: Dict) -> bool:
        """Set accessibility profile for user."""
        if user_id not in self.user_profiles:
            return False

        user_profile = self.user_profiles[user_id]
        user_profile["ui_interactions"]["accessibility_needs"] = accessibility_settings

        self.logger.info(f"Set accessibility profile for user: {user_id}")
        return True

    def create_ab_test(
        self,
        test_name: str,
        template_name: str,
        variants: Dict[str, Dict],
        target_users: Optional[List[str]] = None
    ) -> bool:
        """
        Create A/B test for UI template.

        Args:
            test_name: Test name
            template_name: Template to test
            variants: Test variants
            target_users: Target user IDs

        Returns:
            Test creation success
        """
        try:
            if template_name not in self.ui_templates:
                return False

            test = {
                "name": test_name,
                "template": template_name,
                "variants": variants,
                "target_users": target_users or [],
                "created_at": datetime.now(),
                "status": "active",
                "results": {
                    "variant_performance": {},
                    "user_assignments": {}
                }
            }

            self.ab_tests[test_name] = test

            # Add variants to template
            template = self.ui_templates[template_name]
            template["ab_test_variants"].update(variants)

            self.logger.info(f"Created A/B test: {test_name} for template {template_name}")
            return True

        except Exception as e:
            self.logger.error(f"A/B test creation failed: {e}")
            return False

    def get_ui_performance_metrics(self, user_id: Optional[str] = None) -> Dict:
        """Get UI performance metrics."""
        if user_id:
            return self.ui_metrics.get(user_id, {})

        # Aggregate metrics across all users
        total_users = len(self.user_profiles)
        total_sessions = sum(
            profile["ui_interactions"]["total_sessions"]
            for profile in self.user_profiles.values()
        )

        return {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "avg_sessions_per_user": total_sessions / max(total_users, 1),
            "active_users_24h": sum(
                1 for profile in self.user_profiles.values()
                if profile.get("last_active") and
                (datetime.now() - profile["last_active"]) < timedelta(hours=24)
            )
        }

    def get_user_insights(self, user_id: str) -> Optional[Dict]:
        """Get user behavior insights."""
        if user_id not in self.user_profiles:
            return None

        profile = self.user_profiles[user_id]
        interactions = list(self.interaction_history[user_id])

        # Analyze interaction patterns
        insights = {
            "user_id": user_id,
            "total_interactions": len(interactions),
            "preferred_device_types": {},
            "context_usage": {},
            "peak_usage_hours": {},
            "learned_preferences": profile.get("preferences", {})
        }

        # Analyze device preferences
        for interaction in interactions:
            device_id = interaction["device_id"]
            device_profile = self.device_profiles.get(device_id)
            if device_profile:
                device_type = device_profile["type"]
                insights["preferred_device_types"][device_type] = \
                    insights["preferred_device_types"].get(device_type, 0) + 1

        # Analyze context usage
        for interaction in interactions:
            context = interaction["context"]
            insights["context_usage"][context] = \
                insights["context_usage"].get(context, 0) + 1

        # Analyze usage hours
        for interaction in interactions:
            hour = interaction["timestamp"].hour
            insights["peak_usage_hours"][hour] = \
                insights["peak_usage_hours"].get(hour, 0) + 1

        return insights

    async def optimize_ui_performance(self):
        """Optimize UI performance based on usage patterns."""
        # Analyze user behavior patterns
        # Optimize layouts based on preferences
        # Update templates based on A/B test results

        self.logger.info("Running UI performance optimization")

        # Simplified optimization
        for user_id, profile in self.user_profiles.items():
            interactions = list(self.interaction_history[user_id])
            if len(interactions) > 10:
                # Identify most used features
                context_counts = {}
                for interaction in interactions:
                    context = interaction["context"]
                    context_counts[context] = context_counts.get(context, 0) + 1

                # Update preferences based on usage
                most_used_context = max(context_counts, key=context_counts.get)
                profile["preferences"]["most_used_context"] = most_used_context

    async def continuous_ui_learning(self):
        """Continuous UI learning and adaptation."""
        while True:
            try:
                # Update user preferences based on behavior
                await self.optimize_ui_performance()

                # Clean up old interaction history
                cutoff_date = datetime.now() - timedelta(days=30)
                for user_id in self.interaction_history:
                    self.interaction_history[user_id] = deque(
                        (interaction for interaction in self.interaction_history[user_id]
                         if interaction["timestamp"] > cutoff_date),
                        maxlen=self.config["max_user_history"]
                    )

                await asyncio.sleep(self.config["ui_update_interval"])

            except Exception as e:
                self.logger.error(f"UI learning error: {e}")
                await asyncio.sleep(300)


# Global adaptive UI instance
adaptive_ui = AdaptiveUserInterface()


def create_user_ui_profile(user_id: str, user_info: Dict, preferences: Optional[Dict] = None) -> bool:
    """Create user UI profile."""
    return adaptive_ui.create_user_profile(user_id, user_info, preferences)


def register_ui_device_profile(device_id: str, device_type: str, capabilities: Dict) -> bool:
    """Register device profile for UI."""
    return adaptive_ui.register_device_profile(device_id, DeviceType(device_type), capabilities)


async def generate_adaptive_ui_config(
    user_id: str,
    device_id: str,
    context: str,
    template: str
) -> Dict:
    """Generate adaptive UI configuration."""
    return await adaptive_ui.generate_adaptive_ui(
        user_id, device_id, UIContext(context), template
    )


def get_ui_performance_metrics(user_id: Optional[str] = None) -> Dict:
    """Get UI performance metrics."""
    return adaptive_ui.get_ui_performance_metrics(user_id)


def get_user_ui_insights(user_id: str) -> Optional[Dict]:
    """Get user UI insights."""
    return adaptive_ui.get_user_insights(user_id)