"""
Adaptive User Interface Module

This module implements a sophisticated, stateful adaptive user interface system.
It manages user profiles, learns from interactions, and dynamically generates
context-aware, personalized, and responsive UI experiences.
"""

import asyncio
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set

from src.utils.logging_config import get_logger

# --- Enums for UI Adaptation ---

class DeviceType(Enum):
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"
    WEARABLE = "wearable"

class UserRole(Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    ENGINEER = "engineer"
    MANAGER = "manager"
    VIEWER = "viewer"

class UIContext(Enum):
    DASHBOARD = "dashboard"
    ANALYTICS = "analytics"
    CONFIGURATION = "configuration"
    ALERTS = "alerts"

class UserGoal(Enum):
    QUICK_OVERVIEW = "quick_overview"
    IN_DEPTH_ANALYSIS = "in_depth_analysis"
    SYSTEM_CONFIGURATION = "system_configuration"
    INCIDENT_RESPONSE = "incident_response"
    EXPLORATION = "exploration"

# --- Helper Classes for Logic Segregation ---

class DynamicLayoutEngine:
    """Engine for dynamically generating UI layouts."""
    def __init__(self, logger):
        self.logger = logger
        self._widget_catalog = {
            'alerts_panel': {'roles': {UserRole.ADMIN, UserRole.OPERATOR}, 'goals': {UserGoal.INCIDENT_RESPONSE}},
            'kpi_summary': {'roles': {UserRole.MANAGER, UserRole.VIEWER}, 'goals': {UserGoal.QUICK_OVERVIEW}},
            'detailed_chart': {'roles': {UserRole.ENGINEER}, 'goals': {UserGoal.IN_DEPTH_ANALYSIS}},
            'system_config_panel': {'roles': {UserRole.ADMIN, UserRole.ENGINEER}, 'goals': {UserGoal.SYSTEM_CONFIGURATION}},
            'activity_feed': {'roles': {UserRole.OPERATOR, UserRole.MANAGER}, 'goals': {UserGoal.EXPLORATION, UserGoal.QUICK_OVERVIEW}},
        }

    def generate_layout(self, user_profile: Dict, goal: UserGoal) -> List[Dict]:
        user_role = user_profile.get('info', {}).get('role', UserRole.VIEWER)

        relevant_widgets = []
        for name, rules in self._widget_catalog.items():
            if user_role in rules['roles'] and goal in rules['goals']:
                relevant_widgets.append({'name': name, 'priority': 1.0})

        frequent_widgets = user_profile.get('learned_behavior', {}).get('frequent_widgets', set())
        for widget in relevant_widgets:
            if widget['name'] in frequent_widgets:
                widget['priority'] *= 1.5

        sorted_layout = sorted(relevant_widgets, key=lambda w: w['priority'], reverse=True)
        self.logger.info(f"Generated layout for role '{user_role.name}' and goal '{goal.name}' with {len(sorted_layout)} widgets.")
        return sorted_layout

class UIRecommender:
    """Engine for providing feature recommendations."""
    def __init__(self, logger):
        self.logger = logger
        self._feature_catalog = {
            "advanced_analytics_dashboard": {"min_expertise": 50, "roles": {UserRole.ENGINEER, UserRole.MANAGER}},
            "bulk_config_editor": {"min_expertise": 70, "roles": {UserRole.ADMIN}},
        }

    def get_recommendations(self, user_profile: Dict) -> List[str]:
        expertise = user_profile.get("learned_behavior", {}).get("expertise_score", 0)
        role = user_profile.get("info", {}).get("role", UserRole.VIEWER)

        recommendations = []
        for feature, criteria in self._feature_catalog.items():
            if expertise >= criteria["min_expertise"] and role in criteria["roles"]:
                 recommendations.append(feature)

        if recommendations:
            self.logger.info(f"Generated {len(recommendations)} recommendations for user {user_profile['user_id']}.")
        return recommendations

# --- Main Stateful UI Manager Class ---

class AdaptiveUserInterface:
    """A stateful adaptive UI system that manages user profiles and learns from interactions."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        self.user_profiles: Dict[str, Dict] = {}
        self.device_profiles: Dict[str, Dict] = {}
        self.interaction_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.config["max_user_history"]))

        self.layout_engine = DynamicLayoutEngine(self.logger)
        self.recommender = UIRecommender(self.logger)

        self.logger.info("Stateful Adaptive User Interface initialized")

    def _get_default_config(self) -> Dict:
        return {
            "max_user_history": 1000,
            "default_theme": "light",
            "supported_languages": ["en", "bg", "de"],
        }

    def register_user(self, user_id: str, role: UserRole, preferences: Optional[Dict] = None):
        if user_id in self.user_profiles:
            self.logger.warning(f"User {user_id} already exists. Updating role and preferences.")
            self.user_profiles[user_id]['info']['role'] = role
            self.user_profiles[user_id]['preferences'].update(preferences or {})
            return

        self.user_profiles[user_id] = {
            "user_id": user_id,
            "info": {"role": role},
            "preferences": preferences or {"theme": self.config['default_theme']},
            "created_at": datetime.now(timezone.utc),
            "learned_behavior": {
                "expertise_score": 0,
                "frequent_widgets": set(),
                "preferred_density": "default",
            },
        }
        self.logger.info(f"Registered new user: {user_id} with role {role.name}")

    def register_device(self, device_id: str, device_type: DeviceType, capabilities: Dict):
        self.device_profiles[device_id] = {
            "device_id": device_id,
            "type": device_type,
            "capabilities": capabilities,
        }
        self.logger.info(f"Registered device: {device_id} ({device_type.name})")

    async def generate_ui(self, user_id: str, device_id: str, context: UIContext) -> Dict:
        user_profile = self.user_profiles.get(user_id)
        device_profile = self.device_profiles.get(device_id)
        if not user_profile or not device_profile:
            error_msg = f"User '{user_id}' or device '{device_id}' not registered."
            self.logger.error(error_msg)
            return {"error": error_msg}

        # 1. Record interaction and learn from it
        await self._record_and_learn(user_id, device_id, context)

        # 2. Infer user's current goal
        user_goal = self._infer_user_goal(user_id)

        # 3. Generate a personalized widget layout
        widgets = self.layout_engine.generate_layout(user_profile, user_goal)

        # 4. Apply device-specific adaptations
        final_config = self._apply_device_adaptation(
            base_config={"widgets": widgets},
            device_type=device_profile['type']
        )

        # 5. Add other user-specific details
        final_config['theme'] = user_profile.get('preferences', {}).get('theme', 'light')
        final_config['user_id'] = user_id
        final_config['context'] = context.name
        final_config['inferred_goal'] = user_goal.name

        return final_config

    async def _record_and_learn(self, user_id: str, device_id: str, context: UIContext):
        interaction = {
            "timestamp": datetime.now(timezone.utc),
            "device_id": device_id,
            "context": context,
        }
        self.interaction_history[user_id].append(interaction)

        # Learning logic
        user_profile = self.user_profiles[user_id]
        behavior = user_profile['learned_behavior']

        # Increase expertise score based on context
        if context in {UIContext.ANALYTICS, UIContext.CONFIGURATION}:
            behavior['expertise_score'] += 2
        else:
            behavior['expertise_score'] += 1

        # In a real system, we'd analyze widget interactions to update frequent_widgets
        # For this simulation, we'll leave it to the layout engine's output

    def _infer_user_goal(self, user_id: str, last_n: int = 10) -> UserGoal:
        history = list(self.interaction_history.get(user_id, []))[-last_n:]
        if not history:
            return UserGoal.QUICK_OVERVIEW

        context_sequence = [i['context'] for i in history]

        if UIContext.CONFIGURATION in context_sequence:
            return UserGoal.SYSTEM_CONFIGURATION
        if UIContext.ALERTS in context_sequence:
            return UserGoal.INCIDENT_RESPONSE
        if context_sequence.count(UIContext.ANALYTICS) > 3:
            return UserGoal.IN_DEPTH_ANALYSIS
        if len(set(context_sequence)) > 2:
            return UserGoal.EXPLORATION

        return UserGoal.QUICK_OVERVIEW

    def _apply_device_adaptation(self, base_config: Dict, device_type: DeviceType) -> Dict:
        adapted_config = base_config.copy()
        if device_type == DeviceType.MOBILE:
            adapted_config['layout_style'] = "single_column"
            adapted_config['density'] = "compact"
            adapted_config['navigation'] = "bottom_tabs"
        elif device_type == DeviceType.TABLET:
            adapted_config['layout_style'] = "grid_two_column"
            adapted_config['density'] = "default"
        else: # Desktop
            adapted_config['layout_style'] = "dynamic_grid"
            adapted_config['density'] = "comfortable"
        return adapted_config

    def get_recommendations(self, user_id: str) -> List[str]:
        user_profile = self.user_profiles.get(user_id)
        if not user_profile: return []
        return self.recommender.get_recommendations(user_profile)

if __name__ == "__main__":
    async def main():
        print("--- Stateful Adaptive UI Demonstration ---")
        ui_service = AdaptiveUserInterface()

        # 1. Register users and devices
        print("\n--- 1. Registering Users and Devices ---")
        ui_service.register_user("jane_engineer", UserRole.ENGINEER)
        ui_service.register_user("bob_manager", UserRole.MANAGER)
        ui_service.register_device("desktop_main", DeviceType.DESKTOP, {})
        ui_service.register_device("mobile_field", DeviceType.MOBILE, {})

        # 2. Simulate Engineer's session focused on analysis
        print("\n--- 2. Simulating Engineer's Analysis Session on Desktop ---")
        for _ in range(5):
            await ui_service.generate_ui("jane_engineer", "desktop_main", UIContext.ANALYTICS)

        # Generate UI after building history
        final_desktop_ui = await ui_service.generate_ui("jane_engineer", "desktop_main", UIContext.ANALYTICS)
        print(f"Engineer's Desktop UI (Goal: {final_desktop_ui['inferred_goal']}):")
        print(f"  Widgets: {[w['name'] for w in final_desktop_ui['widgets']]}")
        print(f"  Layout: {final_desktop_ui['layout_style']}")

        # 3. Same Engineer, but on mobile in a different context
        print("\n--- 3. Same Engineer, now on Mobile checking Dashboard ---")
        mobile_ui = await ui_service.generate_ui("jane_engineer", "mobile_field", UIContext.DASHBOARD)
        print(f"Engineer's Mobile UI (Goal: {mobile_ui['inferred_goal']}):")
        print(f"  Widgets: {[w['name'] for w in mobile_ui['widgets']]}")
        print(f"  Layout: {mobile_ui['layout_style']}")

        # 4. Simulate Manager's session for a quick overview
        print("\n--- 4. Simulating Manager's Session for Quick Overview ---")
        for _ in range(3):
            await ui_service.generate_ui("bob_manager", "desktop_main", UIContext.DASHBOARD)
        manager_ui = await ui_service.generate_ui("bob_manager", "desktop_main", UIContext.DASHBOARD)
        print(f"Manager's Desktop UI (Goal: {manager_ui['inferred_goal']}):")
        print(f"  Widgets: {[w['name'] for w in manager_ui['widgets']]}")

        # 5. Check for recommendations after usage
        print("\n--- 5. Checking for Feature Recommendations ---")
        jane_expertise = ui_service.user_profiles['jane_engineer']['learned_behavior']['expertise_score']
        print(f"Jane's current expertise score: {jane_expertise}")
        # Manually boost score for demonstration
        ui_service.user_profiles['jane_engineer']['learned_behavior']['expertise_score'] = 80
        print("Jane's expertise boosted to 80.")

        jane_recs = ui_service.get_recommendations("jane_engineer")
        bob_recs = ui_service.get_recommendations("bob_manager")
        print(f"Recommendations for Jane (Engineer): {jane_recs}")
        print(f"Recommendations for Bob (Manager): {bob_recs}")

    asyncio.run(main())