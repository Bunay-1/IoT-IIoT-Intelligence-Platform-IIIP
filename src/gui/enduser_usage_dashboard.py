import random
from typing import Dict, List, Any
from datetime import datetime, timedelta
import pandas as pd

from fastapi import FastAPI

app = FastAPI()

# Mock data
users = ["user1", "user2", "user3"]
actions = [
    {
        "user": "user1",
        "action": "viewed dashboard",
        "timestamp": "2023-10-01T10:00:00Z",
    },
    {
        "user": "user2",
        "action": "generated report",
        "timestamp": "2023-10-01T11:00:00Z",
    },
    {"user": "user3", "action": "viewed alerts", "timestamp": "2023-10-01T12:00:00Z"},
]


class EnduserUsageDashboard:
    """Dashboard for tracking end-user usage and analytics."""

    def __init__(self):
        self.users = users
        self.actions = actions
        self.usage_stats = self._calculate_usage_stats()

    def _calculate_usage_stats(self) -> Dict[str, Any]:
        """Calculate usage statistics."""
        total_actions = len(self.actions)
        unique_users = len(set(action["user"] for action in self.actions))

        # Actions per user
        actions_per_user = {}
        for action in self.actions:
            user = action["user"]
            actions_per_user[user] = actions_per_user.get(user, 0) + 1

        # Recent activity (last 24 hours)
        recent_actions = []
        for action in self.actions:
            # Assume recent if in mock data
            recent_actions.append(action)

        return {
            "total_users": len(self.users),
            "active_users": unique_users,
            "total_actions": total_actions,
            "actions_per_user": actions_per_user,
            "recent_activity": recent_actions,
            "avg_actions_per_user": total_actions / unique_users if unique_users > 0 else 0
        }

    def get_usage_overview(self) -> Dict[str, Any]:
        """Get usage overview data."""
        return {
            "stats": self.usage_stats,
            "chart_data": self._generate_usage_chart(),
            "top_users": self._get_top_users(),
            "activity_timeline": self._get_activity_timeline()
        }

    def _generate_usage_chart(self) -> Dict[str, Any]:
        """Generate usage chart data."""
        # Mock chart data
        return {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "datasets": [
                {
                    "label": "Active Users",
                    "data": [12, 19, 15, 25, 22, 18, 14],
                    "borderColor": "#4CAF50",
                    "backgroundColor": "rgba(76, 175, 80, 0.1)"
                },
                {
                    "label": "Actions Performed",
                    "data": [45, 67, 52, 89, 76, 63, 41],
                    "borderColor": "#2196F3",
                    "backgroundColor": "rgba(33, 150, 243, 0.1)"
                }
            ]
        }

    def _get_top_users(self) -> List[Dict[str, Any]]:
        """Get top active users."""
        user_activity = {}
        for action in self.actions:
            user = action["user"]
            user_activity[user] = user_activity.get(user, 0) + 1

        sorted_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)
        return [
            {"user": user, "actions": count, "percentage": (count / len(self.actions)) * 100}
            for user, count in sorted_users[:5]
        ]

    def _get_activity_timeline(self) -> List[Dict[str, Any]]:
        """Get activity timeline data."""
        # Mock timeline data
        return [
            {
                "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
                "action": action["action"],
                "user": action["user"]
            }
            for i, action in enumerate(self.actions[-10:])
        ]

    def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific user."""
        user_actions = [action for action in self.actions if action["user"] == user_id]

        return {
            "user_id": user_id,
            "total_actions": len(user_actions),
            "actions": user_actions,
            "last_activity": user_actions[-1]["timestamp"] if user_actions else None,
            "activity_types": list(set(action["action"] for action in user_actions))
        }


@app.get("/usage")
async def get_usage():
    return {"users": users, "actions": actions}


# Example endpoint
@app.get("/")
async def root():
    return {"message": "Enduser Usage Dashboard"}
