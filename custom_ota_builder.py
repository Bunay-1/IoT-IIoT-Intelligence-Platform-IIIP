import json

import requests


class CustomOTABuilder:
    def __init__(self, device_data, update_server):
        """
        Initialize the custom OTA builder.
        Args:
            device_data (dict): Dictionary containing device information.
            update_server (str): URL of the update server.
        """
        self.device_data = device_data
        self.update_server = update_server

    def build_ota_update(self, device_id, update_data):
        """
        Build and send an OTA update for a specific device.
        Args:
            device_id (str): ID of the device to update.
            update_data (dict): Data containing the update information.
        """
        if device_id not in self.device_data:
            raise ValueError(f"Device {device_id} not found in device data.")

        # Prepare the update payload
        update_payload = {"device_id": device_id, "update_data": update_data}

        # Send the update to the server
        response = requests.post(
            f"{self.update_server}/update",
            headers={"Content-Type": "application/json"},
            data=json.dumps(update_payload),
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to send OTA update for device {device_id}: {response.text}"
            )

        print(f"OTA update sent successfully for device {device_id}.")

    def rollback_update(self, device_id):
        """
        Rollback the update for a specific device.
        Args:
            device_id (str): ID of the device to rollback.
        """
        # Send the rollback request to the server
        response = requests.post(
            f"{self.update_server}/rollback",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"device_id": device_id}),
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to rollback update for device {device_id}: {response.text}"
            )

        print(f"Update rollback initiated successfully for device {device_id}.")
