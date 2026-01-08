"""
Adaptive UX Personalization Module

This module implements AI-driven user experience personalization for industrial applications.
It analyzes user behavior, preferences, and context to provide personalized dashboards,
themes, languages, and recommendations.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

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


class AdaptiveUXPersonalization(LoggerMixin):
    """
    Advanced UX personalization system with AI-driven recommendations.

    This class provides personalized user experiences by analyzing user behavior,
    preferences, and context using machine learning techniques.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AdaptiveUXPersonalization system.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # User data and preferences
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.user_behavior_history: Dict[str, List[Dict[str, Any]]] = {}
        self.personalization_cache: Dict[str, Dict[str, Any]] = {}

        # Personalization settings
        self.enable_ai_recommendations = self.config.get(
            "enable_ai_recommendations", True
        )
        self.cache_ttl_seconds = self.config.get("cache_ttl_seconds", 3600)  # 1 hour
        self.max_history_size = self.config.get("max_history_size", 1000)

        # Available themes and languages
        self.available_themes = ["light", "dark", "auto", "industrial", "minimal"]
        self.available_languages = ["en", "bg", "de", "fr", "es", "zh"]

        self.logger.info("AdaptiveUXPersonalization initialized")

    @validate_input(
        {
            "user_id": {
                "type": "string",
                "max_length": 50,
                "required": True,
                "pattern": "^[a-zA-Z0-9_-]{1,50}$",
            }
        }
    )
    @monitor_operation("adaptive_ux_personalization.personalize_ux")
    def personalize_ux(
        self, user_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized UX configuration for a user.

        Args:
            user_id: Unique user identifier
            context: Optional context information (time, device, location, etc.)

        Returns:
            Dictionary with personalized UX settings

        Raises:
            ValueError: If user_id is invalid
            SecurityError: If personalization fails due to security constraints
        """
        try:
            # Check cache first
            cache_key = f"{user_id}_{hash(str(context) if context else '')}"
            if cache_key in self.personalization_cache:
                cached_result = self.personalization_cache[cache_key]
                if self._is_cache_valid(cached_result):
                    self.logger.debug(
                        f"Returning cached personalization for user {user_id}"
                    )
                    return cached_result["data"]

            # Analyze user data and context
            personalization = self._analyze_user_data(user_id, context)

            # Generate AI-powered recommendations if enabled
            if self.enable_ai_recommendations:
                personalization[
                    "ai_recommendations"
                ] = self._generate_ai_recommendations(user_id, personalization)

            # Apply context-based adjustments
            if context:
                personalization = self._apply_context_adjustments(
                    personalization, context
                )

            # Cache the result
            self.personalization_cache[cache_key] = {
                "data": personalization,
                "timestamp": datetime.now(),
                "ttl": self.cache_ttl_seconds,
            }

            # Clean old cache entries
            self._clean_cache()

            self.logger.info(f"Generated UX personalization for user {user_id}")
            return personalization

        except Exception as e:
            self.logger.error(f"UX personalization failed for user {user_id}: {e}")
            # Return safe defaults on error
            return self._get_safe_defaults(user_id)

    def _analyze_user_data(
        self, user_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze user data to generate personalization settings.

        Args:
            user_id: User identifier
            context: Optional context information

        Returns:
            Dictionary with personalization settings
        """
        try:
            # Get user profile
            user_profile = self.user_profiles.get(user_id, {})

            # Extract preferences
            theme = user_profile.get("preferred_theme", "auto")
            language = user_profile.get("preferred_language", "en")
            dashboard_layout = user_profile.get("dashboard_layout", "standard")

            # Validate preferences
            if theme not in self.available_themes:
                theme = "auto"
            if language not in self.available_languages:
                language = "en"

            # Analyze behavior history for additional insights
            behavior_insights = self._analyze_behavior_history(user_id)

            personalization = {
                "user_id": user_id,
                "theme": theme,
                "language": language,
                "dashboard_layout": dashboard_layout,
                "behavior_insights": behavior_insights,
                "recommendations": self._generate_recommendations(
                    user_id, behavior_insights
                ),
                "timestamp": datetime.now().isoformat(),
                "version": "2.0",
            }

            return personalization

        except Exception as e:
            self.logger.error(f"Error analyzing user data for {user_id}: {e}")
            return self._get_safe_defaults(user_id)

    def _analyze_behavior_history(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze user behavior history for personalization insights.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with behavior insights
        """
        history = self.user_behavior_history.get(user_id, [])

        if not history:
            return {"interaction_level": "new_user", "preferences_confidence": 0.0}

        try:
            # Analyze interaction patterns
            total_interactions = len(history)
            recent_interactions = [
                h for h in history if self._is_recent(h.get("timestamp"))
            ]

            # Calculate engagement metrics
            avg_session_duration = sum(
                h.get("session_duration", 0) for h in recent_interactions
            ) / max(len(recent_interactions), 1)
            preferred_features = self._extract_preferred_features(history)

            insights = {
                "total_interactions": total_interactions,
                "recent_activity": len(recent_interactions),
                "avg_session_duration": avg_session_duration,
                "preferred_features": preferred_features,
                "interaction_level": self._classify_user_level(
                    total_interactions, avg_session_duration
                ),
                "preferences_confidence": min(
                    total_interactions / 100.0, 1.0
                ),  # Confidence based on interaction volume
            }

            return insights

        except Exception as e:
            self.logger.error(f"Error analyzing behavior history for {user_id}: {e}")
            return {"interaction_level": "unknown", "preferences_confidence": 0.0}

    def _generate_recommendations(
        self, user_id: str, behavior_insights: Dict[str, Any]
    ) -> List[str]:
        """
        Generate personalized recommendations based on user behavior.

        Args:
            user_id: User identifier
            behavior_insights: Behavior analysis results

        Returns:
            List of recommendation strings
        """
        recommendations = []

        try:
            interaction_level = behavior_insights.get("interaction_level", "new_user")
            preferred_features = behavior_insights.get("preferred_features", [])

            # Base recommendations based on user level
            if interaction_level == "new_user":
                recommendations.extend(
                    [
                        "Complete your profile to get better personalization",
                        "Try the interactive dashboard tour",
                        "Explore energy trading features",
                    ]
                )
            elif interaction_level == "regular":
                recommendations.extend(
                    [
                        "Set up automated alerts for critical metrics",
                        "Try advanced analytics features",
                        "Explore predictive maintenance insights",
                    ]
                )
            elif interaction_level == "power_user":
                recommendations.extend(
                    [
                        "Configure custom dashboards",
                        "Set up automated workflows",
                        "Explore API integrations",
                    ]
                )

            # Feature-specific recommendations
            if "energy_trading" in preferred_features:
                recommendations.append("Check out new trading strategies")
            if "predictive_maintenance" in preferred_features:
                recommendations.append("Review maintenance predictions")
            if "real_time_monitoring" in preferred_features:
                recommendations.append("Customize alert thresholds")

            # Limit to top 5 recommendations
            return recommendations[:5]

        except Exception as e:
            self.logger.error(f"Error generating recommendations for {user_id}: {e}")
            return ["Explore platform features", "Set up personalized alerts"]

    def _generate_ai_recommendations(
        self, user_id: str, personalization: Dict[str, Any]
    ) -> List[str]:
        """
        Generate AI-powered recommendations using integrated ML engines.

        Args:
            user_id: User identifier
            personalization: Current personalization settings

        Returns:
            List of AI-generated recommendations
        """
        ai_recommendations = []

        try:
            if not AUTOML_AVAILABLE:
                return ai_recommendations

            # Prepare data for AI analysis
            user_history = self.user_behavior_history.get(user_id, [])
            if len(user_history) < 5:
                return ["Collect more interaction data for AI recommendations"]

            # Use AutoML for behavior pattern analysis
            history_df = self._prepare_behavior_data_for_ml(user_history)

            if history_df is not None and not history_df.empty:
                # This would use AutoML to predict user preferences or behavior patterns
                # For now, return mock AI recommendations
                ai_recommendations.extend(
                    [
                        "AI suggests trying dark theme for better visibility",
                        "Based on your usage patterns, consider enabling predictive alerts",
                        "AI recommends exploring energy optimization features",
                    ]
                )

            return ai_recommendations[:3]

        except Exception as e:
            self.logger.error(f"AI recommendation generation failed for {user_id}: {e}")
            return []

    def _apply_context_adjustments(
        self, personalization: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply context-based adjustments to personalization.

        Args:
            personalization: Current personalization settings
            context: Context information

        Returns:
            Adjusted personalization settings
        """
        try:
            adjusted = personalization.copy()

            # Time-based adjustments
            current_hour = datetime.now().hour
            if current_hour < 6 or current_hour > 22:  # Night time
                if adjusted["theme"] == "auto":
                    adjusted["theme"] = "dark"

            # Device-based adjustments
            device_type = context.get("device_type", "").lower()
            if "mobile" in device_type:
                adjusted["dashboard_layout"] = "mobile_optimized"

            # Location-based adjustments (if available)
            location = context.get("location", "").lower()
            if "production_floor" in location:
                adjusted["theme"] = "industrial"

            return adjusted

        except Exception as e:
            self.logger.error(f"Context adjustment failed: {e}")
            return personalization

    def update_user_behavior(self, user_id: str, behavior_data: Dict[str, Any]) -> None:
        """
        Update user behavior history for personalization learning.

        Args:
            user_id: User identifier
            behavior_data: Behavior data to record
        """
        try:
            if user_id not in self.user_behavior_history:
                self.user_behavior_history[user_id] = []

            # Add timestamp if not provided
            if "timestamp" not in behavior_data:
                behavior_data["timestamp"] = datetime.now()

            # Add to history
            self.user_behavior_history[user_id].append(behavior_data)

            # Limit history size
            if len(self.user_behavior_history[user_id]) > self.max_history_size:
                self.user_behavior_history[user_id] = self.user_behavior_history[
                    user_id
                ][-self.max_history_size :]

            self.logger.debug(f"Updated behavior history for user {user_id}")

        except Exception as e:
            self.logger.error(f"Failed to update behavior for user {user_id}: {e}")

    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Update user profile information.

        Args:
            user_id: User identifier
            profile_data: Profile data to update
        """
        try:
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {}

            # Validate and sanitize profile data
            validated_data = self._validate_profile_data(profile_data)

            # Update profile
            self.user_profiles[user_id].update(validated_data)

            # Clear personalization cache for this user
            self._clear_user_cache(user_id)

            self.logger.info(f"Updated profile for user {user_id}")

        except Exception as e:
            self.logger.error(f"Failed to update profile for user {user_id}: {e}")
            raise

    def _validate_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize profile data."""
        validated = {}

        # Validate theme
        if "preferred_theme" in profile_data:
            theme = profile_data["preferred_theme"]
            if theme in self.available_themes:
                validated["preferred_theme"] = theme

        # Validate language
        if "preferred_language" in profile_data:
            language = profile_data["preferred_language"]
            if language in self.available_languages:
                validated["preferred_language"] = language

        # Add other validations as needed
        for key, value in profile_data.items():
            if key not in ["preferred_theme", "preferred_language"]:
                validated[key] = value

        return validated

    def _is_recent(self, timestamp_str: Optional[str], hours: int = 24) -> bool:
        """Check if a timestamp is within the recent time window."""
        if not timestamp_str:
            return False

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            return (datetime.now() - timestamp) < timedelta(hours=hours)
        except:
            return False

    def _extract_preferred_features(self, history: List[Dict[str, Any]]) -> List[str]:
        """Extract most used features from behavior history."""
        feature_counts = {}
        for entry in history:
            feature = entry.get("feature_used", "")
            if feature:
                feature_counts[feature] = feature_counts.get(feature, 0) + 1

        # Return top 3 features
        sorted_features = sorted(
            feature_counts.items(), key=lambda x: x[1], reverse=True
        )
        return [feature for feature, _ in sorted_features[:3]]

    def _classify_user_level(
        self, total_interactions: int, avg_session_duration: float
    ) -> str:
        """Classify user engagement level."""
        if total_interactions < 10:
            return "new_user"
        elif total_interactions < 100 or avg_session_duration < 300:  # 5 minutes
            return "regular"
        else:
            return "power_user"

    def _prepare_behavior_data_for_ml(
        self, history: List[Dict[str, Any]]
    ) -> Optional[Any]:
        """Prepare behavior data for ML analysis."""
        # Placeholder for ML data preparation
        # Would convert behavior history to DataFrame for AutoML
        return None

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        try:
            cache_time = cache_entry["timestamp"]
            ttl = cache_entry.get("ttl", self.cache_ttl_seconds)
            return (datetime.now() - cache_time) < timedelta(seconds=ttl)
        except:
            return False

    def _clean_cache(self) -> None:
        """Clean expired cache entries."""
        try:
            current_time = datetime.now()
            valid_entries = {}

            for key, entry in self.personalization_cache.items():
                if self._is_cache_valid(entry):
                    valid_entries[key] = entry

            self.personalization_cache = valid_entries
            removed_count = len(self.personalization_cache) - len(valid_entries)

            if removed_count > 0:
                self.logger.debug(f"Cleaned {removed_count} expired cache entries")

        except Exception as e:
            self.logger.error(f"Cache cleaning failed: {e}")

    def _clear_user_cache(self, user_id: str) -> None:
        """Clear cache entries for a specific user."""
        try:
            keys_to_remove = [
                key
                for key in self.personalization_cache.keys()
                if key.startswith(f"{user_id}_")
            ]
            for key in keys_to_remove:
                del self.personalization_cache[key]

            self.logger.debug(f"Cleared cache for user {user_id}")

        except Exception as e:
            self.logger.error(f"Cache clearing failed for user {user_id}: {e}")

    def _get_safe_defaults(self, user_id: str) -> Dict[str, Any]:
        """Get safe default personalization settings."""
        return {
            "user_id": user_id,
            "theme": "auto",
            "language": "en",
            "dashboard_layout": "standard",
            "behavior_insights": {
                "interaction_level": "unknown",
                "preferences_confidence": 0.0,
            },
            "recommendations": [
                "Explore platform features",
                "Set up personalized alerts",
            ],
            "ai_recommendations": [],
            "timestamp": datetime.now().isoformat(),
            "version": "2.0",
        }

    def get_user_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get personalization statistics.

        Args:
            user_id: Optional specific user ID

        Returns:
            Dictionary with statistics
        """
        if user_id:
            return {
                "user_id": user_id,
                "profile_exists": user_id in self.user_profiles,
                "behavior_records": len(self.user_behavior_history.get(user_id, [])),
                "cache_entries": len(
                    [
                        k
                        for k in self.personalization_cache.keys()
                        if k.startswith(f"{user_id}_")
                    ]
                ),
            }
        else:
            return {
                "total_users": len(self.user_profiles),
                "total_behavior_records": sum(
                    len(h) for h in self.user_behavior_history.values()
                ),
                "cache_entries": len(self.personalization_cache),
                "cache_hit_ratio": 0.0,  # Would need to track this
            }
