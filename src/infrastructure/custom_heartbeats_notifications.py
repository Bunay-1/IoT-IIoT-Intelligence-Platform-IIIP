import json

import requests


class CustomHeartbeatsNotifications:
    def __init__(self, notification_server):
        """
        Initialize the custom heartbeats notifications system.
        Args:
            notification_server (str): URL of the notification server.
        """
        self.notification_server = notification_server

    def send_heartbeat_notification(self, system_id, status):
        """
        Send a heartbeat notification for a specific system.
        Args:
            system_id (str): ID of the system sending the heartbeat.
            status (str): Status of the system (e.g., "online", "offline").
        """
        # Prepare the notification payload
        notification_payload = {
            "system_id": system_id,
            "status": status,
            "timestamp": "2025-12-11T13:09:01Z",
        }

        # Send the notification to the server
        response = requests.post(
            f"{self.notification_server}/heartbeat",
            headers={"Content-Type": "application/json"},
            data=json.dumps(notification_payload),
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to send heartbeat notification for system {system_id}: {response.text}"
            )

        print(
            f"Heartbeat notification sent successfully for system {system_id} with status {status}."
        )

    def send_alert_notification(self, system_id, alert_message):
        """
        Send an alert notification for a specific system.
        Args:
            system_id (str): ID of the system sending the alert.
            alert_message (str): Alert message to be sent.
        """
        # Prepare the alert payload
        alert_payload = {
            "system_id": system_id,
            "alert_message": alert_message,
            "timestamp": "2025-12-11T13:09:01Z",
        }

        # Send the alert to the server
        response = requests.post(
            f"{self.notification_server}/alert",
            headers={"Content-Type": "application/json"},
            data=json.dumps(alert_payload),
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to send alert notification for system {system_id}: {response.text}"
            )

        print(
            f"Alert notification sent successfully for system {system_id}: {alert_message}."
        )
