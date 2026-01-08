"""
IoT Integration Module for IoT IIoT Platform
Comprehensive IoT device connectivity, protocol support, and data management
"""

import asyncio
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import ssl

from utils.logging_config import get_logger

logger = get_logger(__name__)


class IoTProtocol(Enum):
    """Supported IoT communication protocols."""
    MQTT = "mqtt"
    MQTT_TLS = "mqtt_tls"
    OPC_UA = "opc_ua"
    MODBUS = "modbus"
    DNP3 = "dnp3"
    COAP = "coap"
    WEBSOCKET = "websocket"
    HTTP_REST = "http_rest"


class DeviceStatus(Enum):
    """IoT device connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class IoTDevice:
    """IoT device configuration."""
    device_id: str
    name: str
    protocol: IoTProtocol
    connection_params: Dict[str, Any]
    data_points: List[Dict[str, Any]]
    status: DeviceStatus = DeviceStatus.DISCONNECTED
    last_seen: Optional[float] = None
    metadata: Dict[str, Any] = None


@dataclass
class DataPoint:
    """Data point configuration."""
    name: str
    data_type: str
    unit: str
    read_only: bool = True
    scaling_factor: float = 1.0
    offset: float = 0.0


class IoTDataManager:
    """Manages IoT data collection and processing."""

    def __init__(self):
        self.devices: Dict[str, IoTDevice] = {}
        self.data_buffer: Dict[str, List[Dict[str, Any]]] = {}
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.stream_processors: Dict[str, Callable] = {}

    async def register_device(self, device_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new IoT device."""
        try:
            device = IoTDevice(
                device_id=device_config["device_id"],
                name=device_config["name"],
                protocol=IoTProtocol(device_config["protocol"]),
                connection_params=device_config["connection_params"],
                data_points=device_config["data_points"],
                metadata=device_config.get("metadata", {})
            )

            self.devices[device.device_id] = device
            self.data_buffer[device.device_id] = []

            logger.info(f"Registered IoT device: {device.device_id}")
            return {
                "status": "registered",
                "device_id": device.device_id,
                "protocol": device.protocol.value
            }

        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            return {"status": "error", "message": str(e)}

    async def connect_device(self, device_id: str) -> Dict[str, Any]:
        """Connect to an IoT device."""
        if device_id not in self.devices:
            return {"status": "error", "message": "Device not found"}

        device = self.devices[device_id]
        device.status = DeviceStatus.CONNECTING

        try:
            if device.protocol == IoTProtocol.MQTT:
                result = await self._connect_mqtt(device)
            elif device.protocol == IoTProtocol.OPC_UA:
                result = await self._connect_opcua(device)
            elif device.protocol == IoTProtocol.MODBUS:
                result = await self._connect_modbus(device)
            else:
                result = {"status": "error", "message": f"Unsupported protocol: {device.protocol.value}"}

            if result["status"] == "connected":
                device.status = DeviceStatus.CONNECTED
                device.last_seen = time.time()

            return result

        except Exception as e:
            device.status = DeviceStatus.ERROR
            logger.error(f"Failed to connect device {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def _connect_mqtt(self, device: IoTDevice) -> Dict[str, Any]:
        """Connect to MQTT-based device."""
        try:
            # In real implementation, use paho-mqtt or similar
            params = device.connection_params

            # Simulate connection
            await asyncio.sleep(0.1)  # Simulate network delay

            return {
                "status": "connected",
                "client_id": f"client_{device.device_id}",
                "broker": params.get("broker", "localhost"),
                "port": params.get("port", 1883)
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _connect_opcua(self, device: IoTDevice) -> Dict[str, Any]:
        """Connect to OPC UA device."""
        try:
            # In real implementation, use opcua library
            params = device.connection_params

            # Simulate connection
            await asyncio.sleep(0.2)

            return {
                "status": "connected",
                "server_url": params.get("server_url"),
                "security_policy": params.get("security_policy", "None")
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _connect_modbus(self, device: IoTDevice) -> Dict[str, Any]:
        """Connect to Modbus device."""
        try:
            # In real implementation, use pymodbus
            params = device.connection_params

            # Simulate connection
            await asyncio.sleep(0.1)

            return {
                "status": "connected",
                "host": params.get("host"),
                "port": params.get("port", 502),
                "slave_id": params.get("slave_id", 1)
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def read_device_data(self, device_id: str, data_points: Optional[List[str]] = None) -> Dict[str, Any]:
        """Read data from IoT device."""
        if device_id not in self.devices:
            return {"status": "error", "message": "Device not found"}

        device = self.devices[device_id]
        if device.status != DeviceStatus.CONNECTED:
            return {"status": "error", "message": "Device not connected"}

        try:
            if device.protocol == IoTProtocol.MQTT:
                data = await self._read_mqtt_data(device, data_points)
            elif device.protocol == IoTProtocol.OPC_UA:
                data = await self._read_opcua_data(device, data_points)
            elif device.protocol == IoTProtocol.MODBUS:
                data = await self._read_modbus_data(device, data_points)
            else:
                data = {"error": f"Unsupported protocol: {device.protocol.value}"}

            # Store in buffer
            if "readings" in data:
                timestamped_data = {
                    "timestamp": time.time(),
                    "device_id": device_id,
                    "data": data["readings"]
                }
                self.data_buffer[device_id].append(timestamped_data)

                # Keep buffer size manageable
                if len(self.data_buffer[device_id]) > 1000:
                    self.data_buffer[device_id] = self.data_buffer[device_id][-1000:]

            # Notify subscribers
            await self._notify_subscribers(device_id, data)

            device.last_seen = time.time()
            return data

        except Exception as e:
            logger.error(f"Failed to read data from {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def _read_mqtt_data(self, device: IoTDevice, data_points: Optional[List[str]]) -> Dict[str, Any]:
        """Read data via MQTT."""
        # Simulate MQTT data reading
        readings = {}
        for dp in device.data_points:
            if data_points is None or dp["name"] in data_points:
                # Simulate sensor readings
                if dp["data_type"] == "temperature":
                    readings[dp["name"]] = 25.0 + np.random.normal(0, 2)
                elif dp["data_type"] == "pressure":
                    readings[dp["name"]] = 1013.25 + np.random.normal(0, 10)
                elif dp["data_type"] == "vibration":
                    readings[dp["name"]] = abs(np.random.normal(0, 0.5))
                else:
                    readings[dp["name"]] = np.random.random()

        return {"status": "success", "readings": readings}

    async def _read_opcua_data(self, device: IoTDevice, data_points: Optional[List[str]]) -> Dict[str, Any]:
        """Read data via OPC UA."""
        # Simulate OPC UA data reading
        readings = {}
        for dp in device.data_points:
            if data_points is None or dp["name"] in data_points:
                readings[dp["name"]] = np.random.random() * 100

        return {"status": "success", "readings": readings}

    async def _read_modbus_data(self, device: IoTDevice, data_points: Optional[List[str]]) -> Dict[str, Any]:
        """Read data via Modbus."""
        # Simulate Modbus data reading
        readings = {}
        for dp in device.data_points:
            if data_points is None or dp["name"] in data_points:
                readings[dp["name"]] = int(np.random.random() * 65535)

        return {"status": "success", "readings": readings}

    async def write_device_data(self, device_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write data to IoT device."""
        if device_id not in self.devices:
            return {"status": "error", "message": "Device not found"}

        device = self.devices[device_id]
        if device.status != DeviceStatus.CONNECTED:
            return {"status": "error", "message": "Device not connected"}

        try:
            if device.protocol == IoTProtocol.MQTT:
                result = await self._write_mqtt_data(device, data)
            elif device.protocol == IoTProtocol.OPC_UA:
                result = await self._write_opcua_data(device, data)
            elif device.protocol == IoTProtocol.MODBUS:
                result = await self._write_modbus_data(device, data)
            else:
                result = {"status": "error", "message": f"Unsupported protocol: {device.protocol.value}"}

            return result

        except Exception as e:
            logger.error(f"Failed to write data to {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def _write_mqtt_data(self, device: IoTDevice, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write data via MQTT."""
        # Simulate MQTT write
        await asyncio.sleep(0.05)
        return {"status": "success", "written_points": list(data.keys())}

    async def _write_opcua_data(self, device: IoTDevice, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write data via OPC UA."""
        # Simulate OPC UA write
        await asyncio.sleep(0.1)
        return {"status": "success", "written_points": list(data.keys())}

    async def _write_modbus_data(self, device: IoTDevice, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write data via Modbus."""
        # Simulate Modbus write
        await asyncio.sleep(0.05)
        return {"status": "success", "written_points": list(data.keys())}

    def subscribe_to_device(self, device_id: str, callback: Callable) -> str:
        """Subscribe to device data updates."""
        if device_id not in self.subscriptions:
            self.subscriptions[device_id] = []

        subscription_id = f"sub_{device_id}_{len(self.subscriptions[device_id])}"
        self.subscriptions[device_id].append(callback)

        logger.info(f"Subscribed to device {device_id} with ID {subscription_id}")
        return subscription_id

    async def _notify_subscribers(self, device_id: str, data: Dict[str, Any]):
        """Notify subscribers of new data."""
        if device_id in self.subscriptions:
            for callback in self.subscriptions[device_id]:
                try:
                    await callback(device_id, data)
                except Exception as e:
                    logger.error(f"Subscriber callback failed: {e}")

    def add_stream_processor(self, device_id: str, processor: Callable):
        """Add real-time data stream processor."""
        self.stream_processors[device_id] = processor
        logger.info(f"Added stream processor for device {device_id}")

    async def process_data_stream(self, device_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process real-time data stream."""
        if device_id in self.stream_processors:
            try:
                processed_data = await self.stream_processors[device_id](data)
                return processed_data
            except Exception as e:
                logger.error(f"Stream processing failed for {device_id}: {e}")

        return data

    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device status and information."""
        if device_id not in self.devices:
            return None

        device = self.devices[device_id]
        buffer_size = len(self.data_buffer.get(device_id, []))

        return {
            "device_id": device.device_id,
            "name": device.name,
            "protocol": device.protocol.value,
            "status": device.status.value,
            "last_seen": device.last_seen,
            "data_points": len(device.data_points),
            "buffered_readings": buffer_size,
            "metadata": device.metadata
        }

    def get_device_data_history(self, device_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical data for device."""
        if device_id not in self.data_buffer:
            return []

        return self.data_buffer[device_id][-limit:]

    async def start_data_collection(self, device_ids: List[str], interval: float = 1.0):
        """Start periodic data collection from devices."""
        logger.info(f"Starting data collection for {len(device_ids)} devices")

        async def collect_data():
            while True:
                for device_id in device_ids:
                    try:
                        data = await self.read_device_data(device_id)
                        if data.get("status") == "success":
                            # Process stream if processor exists
                            processed_data = await self.process_data_stream(device_id, data)
                            # Could send to analytics pipeline here
                    except Exception as e:
                        logger.error(f"Data collection failed for {device_id}: {e}")

                await asyncio.sleep(interval)

        # Start collection task
        collection_task = asyncio.create_task(collect_data())
        return collection_task

    def get_system_stats(self) -> Dict[str, Any]:
        """Get IoT system statistics."""
        total_devices = len(self.devices)
        connected_devices = len([d for d in self.devices.values() if d.status == DeviceStatus.CONNECTED])
        total_buffered_readings = sum(len(buffer) for buffer in self.data_buffer.values())

        protocol_stats = {}
        for device in self.devices.values():
            protocol = device.protocol.value
            if protocol not in protocol_stats:
                protocol_stats[protocol] = 0
            protocol_stats[protocol] += 1

        return {
            "total_devices": total_devices,
            "connected_devices": connected_devices,
            "connection_rate": connected_devices / max(1, total_devices),
            "total_buffered_readings": total_buffered_readings,
            "protocols": protocol_stats,
            "active_subscriptions": sum(len(subs) for subs in self.subscriptions.values())
        }


# Global IoT manager instance
iot_manager = IoTDataManager()


# Legacy functions for backward compatibility
async def connect_mqtt(broker: str, port: int) -> Dict[str, Any]:
    """Legacy MQTT connection function."""
    device_config = {
        "device_id": f"mqtt_device_{broker}_{port}",
        "name": f"MQTT Device {broker}:{port}",
        "protocol": "mqtt",
        "connection_params": {"broker": broker, "port": port},
        "data_points": [{"name": "data", "data_type": "generic", "unit": "unit"}]
    }

    result = await iot_manager.register_device(device_config)
    if result["status"] == "registered":
        connect_result = await iot_manager.connect_device(result["device_id"])
        return connect_result

    return result


async def publish_mqtt(topic: str, message: Any) -> Dict[str, Any]:
    """Legacy MQTT publish function."""
    # Find MQTT device (simplified)
    mqtt_devices = [d for d in iot_manager.devices.values() if d.protocol == IoTProtocol.MQTT]
    if not mqtt_devices:
        return {"status": "error", "message": "No MQTT device connected"}

    device = mqtt_devices[0]
    return await iot_manager.write_device_data(device.device_id, {"topic": topic, "message": message})


async def subscribe_mqtt(topic: str) -> Dict[str, Any]:
    """Legacy MQTT subscribe function."""
    # Simplified subscription
    return {"status": "subscribed", "topic": topic}


async def connect_opcua(server_url: str) -> Dict[str, Any]:
    """Legacy OPC UA connection function."""
    device_config = {
        "device_id": f"opcua_device_{hash(server_url)}",
        "name": f"OPC UA Device {server_url}",
        "protocol": "opc_ua",
        "connection_params": {"server_url": server_url},
        "data_points": [{"name": "data", "data_type": "industrial", "unit": "value"}]
    }

    result = await iot_manager.register_device(device_config)
    if result["status"] == "registered":
        connect_result = await iot_manager.connect_device(result["device_id"])
        return connect_result

    return result


async def read_opcua(node: str) -> Dict[str, Any]:
    """Legacy OPC UA read function."""
    opcua_devices = [d for d in iot_manager.devices.values() if d.protocol == IoTProtocol.OPC_UA]
    if not opcua_devices:
        return {"status": "error", "message": "No OPC UA device connected"}

    device = opcua_devices[0]
    data = await iot_manager.read_device_data(device.device_id, [node])
    if data.get("status") == "success" and "readings" in data:
        return {
            "value": data["readings"].get(node, "no_data"),
            "timestamp": time.time(),
            "node": node
        }

    return data


async def write_opcua(node: str, value: Any) -> Dict[str, Any]:
    """Legacy OPC UA write function."""
    opcua_devices = [d for d in iot_manager.devices.values() if d.protocol == IoTProtocol.OPC_UA]
    if not opcua_devices:
        return {"status": "error", "message": "No OPC UA device connected"}

    device = opcua_devices[0]
    return await iot_manager.write_device_data(device.device_id, {node: value})