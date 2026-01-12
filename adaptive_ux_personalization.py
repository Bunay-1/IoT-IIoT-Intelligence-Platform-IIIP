"""
Adaptive UX Personalization Module (Stateful & Predictive)

This module implements an advanced, stateful AI-driven user experience
personalization system. It builds detailed user behavior models, predicts
user intent, and delivers proactive nudges to optimize user journeys.
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

from utils.logging_config import get_logger

# --- Enums and Data Structures ---

class UserAction(Enum):
    """Represents a specific action a user can take."""
    LOGIN = "login"
    VIEW_DASHBOARD = "view_dashboard"
    OPEN_ANALYTICS = "open_analytics"
    RUN_REPORT = "run_report"
    VIEW_ALERTS = "view_alerts"
    CONFIGURE_SYSTEM = "configure_system"
    LOGOUT = "logout"

@dataclass
class InteractionEvent:
    """Represents a single point of interaction."""
    session_id: str
    user_id: str
    action: UserAction
    timestamp: datetime
    metadata: Dict

# --- Predictive and Analytical Engines ---

class UserBehaviorModel:
    """Builds and maintains a model of a user's behavior from interaction history."""
    def __init__(self, user_id: str, logger):
        self.user_id = user_id
        self.logger = logger
        self.transition_counts = defaultdict(lambda: defaultdict(int))
        self.action_durations = defaultdict(list)
        self.feature_mastery = defaultdict(float)
        self.total_sessions = 0

    def update(self, journey: List[InteractionEvent]):
        """Update the model with a completed user journey."""
        if not journey:
            return

        self.total_sessions += 1
        for i in range(len(journey) - 1):
            current_event = journey[i]
            next_event = journey[i+1]

            # Update transition counts (action A -> action B)
            self.transition_counts[current_event.action][next_event.action] += 1

            # Update action durations
            duration = (next_event.timestamp - current_event.timestamp).total_seconds()
            self.action_durations[current_event.action].append(duration)

        # Update feature mastery
        for event in journey:
            # Simple heuristic: more usage and quick actions suggest mastery
            durations = self.action_durations.get(event.action)
            if durations:
                avg_duration = sum(durations) / len(durations)
                mastery_increment = 1.0 / (1.0 + avg_duration / 60.0) # Faster is better
            else:
                mastery_increment = 0.5 # Default increment for actions with no duration (e.g., logout)
            self.feature_mastery[event.action] += mastery_increment

        self.logger.info(f"Updated behavior model for user {self.user_id} with a new journey.")

    def get_most_likely_next_action(self, current_action: UserAction) -> Optional[UserAction]:
        """Get the most probable next action based on historical transitions."""
        if current_action not in self.transition_counts:
            return None

        next_actions = self.transition_counts[current_action]
        return max(next_actions, key=next_actions.get) if next_actions else None

class NextActionPredictor:
    """Simulates an ML model to predict user intent."""
    def __init__(self, logger):
        self.logger = logger

    def predict(self, current_action: UserAction, model: UserBehaviorModel) -> Optional[UserAction]:
        """Predict the next action using the user's behavior model."""
        prediction = model.get_most_likely_next_action(current_action)
        if prediction:
            self.logger.info(f"ML Prediction: After '{current_action.name}', user will likely do '{prediction.name}'.")
        return prediction

class NudgeEngine:
    """Generates proactive suggestions (nudges) to help users."""
    def __init__(self, logger):
        self.logger = logger
        # A simple catalog of potential nudges
        self._nudge_catalog = {
            # If user goes VIEW_DASHBOARD -> OPEN_ANALYTICS -> RUN_REPORT
            (UserAction.VIEW_DASHBOARD, UserAction.RUN_REPORT): "Did you know you can pin key reports directly to your dashboard for quick access?",
            # If user takes a long time in configuration
            (UserAction.CONFIGURE_SYSTEM,): "Struggling with setup? Check out our quick-start templates for system configuration.",
        }

    def generate_nudge(self, journey: List[InteractionEvent], prediction: Optional[UserAction]) -> Optional[str]:
        """Generate a nudge based on the current journey and prediction."""
        if len(journey) < 2:
            return None

        last_action = journey[-2].action
        current_action = journey[-1].action

        # Rule 1: Shortcut suggestion
        if prediction and (last_action, prediction) in self._nudge_catalog:
             # If the user's current action is not the predicted one, maybe offer a shortcut
            if current_action != prediction:
                return self._nudge_catalog[(last_action, prediction)]

        # Rule 2: Long duration suggestion
        duration = (journey[-1].timestamp - journey[-2].timestamp).total_seconds()
        if duration > 180 and (last_action,) in self._nudge_catalog: # 3 minutes
            self.logger.info(f"Generating nudge for long duration ({duration}s) on action {last_action.name}")
            return self._nudge_catalog[(last_action,)]

        return None

# --- Main Stateful Personalization Manager ---

class AdaptiveUXPersonalization:
    """A stateful system to personalize UX through journey analysis and proactive nudges."""
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        # State
        self.user_models: Dict[str, UserBehaviorModel] = {}
        self.active_sessions: Dict[str, List[InteractionEvent]] = {}

        # Engines
        self.predictor = NextActionPredictor(self.logger)
        self.nudge_engine = NudgeEngine(self.logger)

        self.logger.info("Stateful AdaptiveUXPersonalization initialized.")

    def track_event(self, event: InteractionEvent):
        """Main entry point to track a user's action."""
        session_id = event.session_id
        user_id = event.user_id

        if user_id not in self.user_models:
            self.user_models[user_id] = UserBehaviorModel(user_id, self.logger)

        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = []

        self.active_sessions[session_id].append(event)
        self.logger.debug(f"Tracked event '{event.action.name}' for user {user_id}.")

        # If the journey ends, update the model
        if event.action == UserAction.LOGOUT:
            journey = self.active_sessions.pop(session_id)
            self.user_models[user_id].update(journey)

    def get_personalization(self, user_id: str, session_id: str) -> Dict:
        """Get personalization features, including proactive nudges."""
        journey = self.active_sessions.get(session_id)
        if not journey or not user_id in self.user_models:
            return {"nudge": None, "predicted_next_action": None}

        current_action = journey[-1].action
        user_model = self.user_models[user_id]

        # 1. Predict next action
        prediction = self.predictor.predict(current_action, user_model)

        # 2. Generate a nudge based on the journey so far
        nudge = self.nudge_engine.generate_nudge(journey, prediction)

        return {
            "nudge": nudge,
            "predicted_next_action": prediction.name if prediction else None,
            "user_mastery_level": {k.name: f"{v:.2f}" for k, v in user_model.feature_mastery.items()}
        }


if __name__ == "__main__":
    async def main():
        print("--- Stateful & Predictive UX Personalization Demonstration ---")
        ux_system = AdaptiveUXPersonalization()

        user_id = "test_user"
        session_id = "session_123"

        # --- Part 1: Simulate a user's first journey (learning phase) ---
        print("\n--- 1. Simulating first user journey for model training ---")
        journey_1 = [
            InteractionEvent(session_id, user_id, UserAction.LOGIN, datetime.now(timezone.utc), {}),
            InteractionEvent(session_id, user_id, UserAction.VIEW_DASHBOARD, datetime.now(timezone.utc) + timedelta(seconds=10), {}),
            InteractionEvent(session_id, user_id, UserAction.OPEN_ANALYTICS, datetime.now(timezone.utc) + timedelta(seconds=40), {}),
            InteractionEvent(session_id, user_id, UserAction.RUN_REPORT, datetime.now(timezone.utc) + timedelta(seconds=90), {}),
            InteractionEvent(session_id, user_id, UserAction.LOGOUT, datetime.now(timezone.utc) + timedelta(seconds=120), {}),
        ]
        for event in journey_1:
            ux_system.track_event(event)
        print("Model has been trained with one completed journey.")

        # --- Part 2: Simulate a new session where we can make predictions ---
        print("\n--- 2. Simulating a new session to get proactive nudges ---")
        session_id_2 = "session_456"

        # Step 1: User logs in and views dashboard
        ux_system.track_event(InteractionEvent(session_id_2, user_id, UserAction.LOGIN, datetime.now(timezone.utc), {}))
        ux_system.track_event(InteractionEvent(session_id_2, user_id, UserAction.VIEW_DASHBOARD, datetime.now(timezone.utc) + timedelta(seconds=5), {}))

        personalization = ux_system.get_personalization(user_id, session_id_2)
        print(f"After viewing dashboard:")
        print(f"  - Predicted Next Action: {personalization['predicted_next_action']}")
        print(f"  - Proactive Nudge: {personalization['nudge']}")

        # Step 2: User goes to run a report directly (a slight deviation)
        print("\nUser deviates and goes to run a report...")
        long_wait_time = datetime.now(timezone.utc) + timedelta(minutes=4)
        ux_system.track_event(InteractionEvent(session_id_2, user_id, UserAction.RUN_REPORT, long_wait_time, {}))

        personalization = ux_system.get_personalization(user_id, session_id_2)
        print(f"After running report (with a long delay):")
        print(f"  - Predicted Next Action: {personalization['predicted_next_action']}")
        print(f"  - Proactive Nudge: {personalization['nudge']}") # Expecting a nudge here

        # --- Part 3: Show the learned user model ---
        print("\n--- 3. Displaying the final user behavior model ---")
        final_model = ux_system.user_models[user_id]
        print(f"User Mastery Scores: {personalization['user_mastery_level']}")
        print(f"Learned Transitions from VIEW_DASHBOARD: {dict(final_model.transition_counts[UserAction.VIEW_DASHBOARD])}")

    asyncio.run(main())