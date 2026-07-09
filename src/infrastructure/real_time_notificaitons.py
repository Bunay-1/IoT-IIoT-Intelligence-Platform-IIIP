"""
Module: Real-Time Notifications

This module handles real-time notifications for events, alerts, and updates across the system. It ensures timely delivery of critical information to users and systems.
"""

import datetime


class RealTimeNotifications:
    def __init__(self):
        self.notifications = []

    def send_notification(self, message, recipient):
        """
        Send a real-time notification to a specific recipient.
        """
        notification = {
            "message": message,
            "recipient": recipient,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.notifications.append(notification)
        print(f"Notification sent to {recipient}: {message}")
        return notification

    def get_notifications(self, recipient=None):
        """
        Retrieve notifications for a specific recipient or all notifications if no recipient is specified.
        """
        if recipient:
            return [n for n in self.notifications if n["recipient"] == recipient]
        return self.notifications

    def clear_notifications(self, recipient=None):
        """
        Clear notifications for a specific recipient or all notifications if no recipient is specified.
        """
        if recipient:
            self.notifications = [
                n for n in self.notifications if n["recipient"] != recipient
            ]
        else:
            self.notifications = []
        print(
            f"Notifications cleared for {recipient if recipient else 'all recipients'}."
        )
