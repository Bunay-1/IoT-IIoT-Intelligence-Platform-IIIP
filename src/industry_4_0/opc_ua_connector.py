"""
OPC UA Connector Module

This module provides connectivity to industrial devices using the OPC UA protocol,
which is the standard for industrial communication and data exchange.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

try:
    from opcua import Client, ua
    from opcua.ua import NodeId
    OPCUA_AVAILABLE = True
except ImportError:
    OPCUA_AVAILABLE = False

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class OPCUAConnector:
    """
    OPC UA client for connecting to industrial PLCs and devices.

    Provides methods for reading/writing process variables, subscribing to
    data changes, and browsing the OPC UA address space.
    """

    def __init__(
        self,
        endpoint: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize OPC UA connector.

        Args:
            endpoint: OPC UA server endpoint URL
            config: Connection configuration
        """
        if not OPCUA_AVAILABLE:
            raise ImportError("opcua library not available. Install with: pip install opcua")

        self.endpoint = endpoint
        self.config = config or self._get_default_config()
        self.logger = get_logger(__name__)

        # Connection state
        self.client: Optional[Client] = None
        self.connected = False
        self.subscription: Optional[Any] = None

        # Node cache for performance
        self.node_cache: Dict[str, Any] = {}

        # Data change handlers
        self.data_change_handlers: List[callable] = []

        self.logger.info(f"OPC UA Connector initialized for endpoint: {endpoint}")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "connection_timeout": 10,
            "session_timeout": 3600000,  # 1 hour
            "secure_connection": True,
            "username": None,
            "password": None,
            "certificate_path": None,
            "private_key_path": None,
            "application_uri": "urn:iot-platform:client",
            "product_uri": "urn:iot-platform:product",
            "application_name": "IoT IIoT Intelligence Platform",
            "auto_reconnect": True,
            "reconnect_interval": 5,
            "max_reconnect_attempts": 3
        }

    async def connect(self) -> bool:
        """
        Establish connection to OPC UA server.

        Returns:
            True if connection successful
        """
        try:
            self.logger.info(f"Connecting to OPC UA server: {self.endpoint}")

            # Create client
            self.client = Client(self.endpoint)

            # Configure client
            self.client.application_uri = self.config["application_uri"]
            self.client.product_uri = self.config["product_uri"]
            self.client.name = self.config["application_name"]

            # Set timeouts
            self.client.timeout = self.config["connection_timeout"] * 1000  # milliseconds
            self.client.session_timeout = self.config["session_timeout"]

            # Security configuration
            if self.config["secure_connection"]:
                await self._configure_security()

            # Authentication
            if self.config["username"] and self.config["password"]:
                self.client.set_user(self.config["username"])
                self.client.set_password(self.config["password"])

            # Connect
            await asyncio.get_event_loop().run_in_executor(
                None, self.client.connect
            )

            self.connected = True
            self.logger.info("Successfully connected to OPC UA server")

            # Load namespace and root node
            await self._initialize_namespace()

            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to OPC UA server: {e}")
            self.connected = False
            return False

    async def _configure_security(self) -> None:
        """Configure secure connection."""
        try:
            if self.config["certificate_path"] and self.config["private_key_path"]:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.load_client_certificate(
                        self.config["certificate_path"]
                    )
                )
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.load_private_key(
                        self.config["private_key_path"]
                    )
                )
                self.logger.info("Client certificate configured")
            else:
                # Use basic security policy
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.set_security_string("Basic256Sha256,SignAndEncrypt")
                )
        except Exception as e:
            self.logger.warning(f"Security configuration failed: {e}")

    async def _initialize_namespace(self) -> None:
        """Initialize namespace and cache commonly used nodes."""
        try:
            # Get namespace array
            namespace_array = await asyncio.get_event_loop().run_in_executor(
                None, self.client.get_namespace_array
            )

            # Cache root objects node
            objects_node = await asyncio.get_event_loop().run_in_executor(
                None, self.client.get_objects_node
            )
            self.node_cache["Objects"] = objects_node

            self.logger.debug("Namespace initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize namespace: {e}")

    async def disconnect(self) -> None:
        """Disconnect from OPC UA server."""
        try:
            if self.subscription:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.subscription.unsubscribe
                )

            if self.client and self.connected:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.client.disconnect
                )

            self.connected = False
            self.logger.info("Disconnected from OPC UA server")

        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")

    async def read_variable(
        self,
        node_id: Union[str, NodeId],
        attribute_id: int = ua.AttributeIds.Value
    ) -> Any:
        """
        Read value from OPC UA variable.

        Args:
            node_id: Node ID to read from
            attribute_id: Attribute to read (default: Value)

        Returns:
            Variable value
        """
        if not self.connected:
            raise ConnectionError("Not connected to OPC UA server")

        try:
            node = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.get_node(node_id)
            )

            value = await asyncio.get_event_loop().run_in_executor(
                None, lambda: node.get_value()
            )

            self.logger.debug(f"Read value from {node_id}: {value}")
            return value

        except Exception as e:
            self.logger.error(f"Failed to read variable {node_id}: {e}")
            raise

    async def write_variable(
        self,
        node_id: Union[str, NodeId],
        value: Any,
        data_type: Optional[Any] = None
    ) -> bool:
        """
        Write value to OPC UA variable.

        Args:
            node_id: Node ID to write to
            value: Value to write
            data_type: Data type (optional)

        Returns:
            True if write successful
        """
        if not self.connected:
            raise ConnectionError("Not connected to OPC UA server")

        try:
            node = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.get_node(node_id)
            )

            # Convert value if data type specified
            if data_type:
                value = data_type(value)

            await asyncio.get_event_loop().run_in_executor(
                None, lambda: node.set_value(value)
            )

            self.logger.debug(f"Write value to {node_id}: {value}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write variable {node_id}: {e}")
            return False

    async def read_machine_parameters(self, machine_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read machine parameters using configuration.

        Args:
            machine_config: Machine configuration with node mappings

        Returns:
            Dictionary of parameter values
        """
        if not self.connected:
            raise ConnectionError("Not connected to OPC UA server")

        try:
            parameters = {}

            # Read each configured parameter
            for param_name, node_config in machine_config.get("parameters", {}).items():
                try:
                    node_id = node_config["node_id"]
                    value = await self.read_variable(node_id)

                    parameters[param_name] = {
                        "value": value,
                        "timestamp": asyncio.get_event_loop().time(),
                        "unit": node_config.get("unit"),
                        "description": node_config.get("description")
                    }

                except Exception as e:
                    self.logger.warning(f"Failed to read parameter {param_name}: {e}")
                    parameters[param_name] = {
                        "error": str(e),
                        "timestamp": asyncio.get_event_loop().time()
                    }

            self.logger.info(f"Read {len(parameters)} machine parameters")
            return parameters

        except Exception as e:
            self.logger.error(f"Failed to read machine parameters: {e}")
            raise

    async def browse_address_space(
        self,
        start_node: Union[str, NodeId] = "Objects",
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Browse OPC UA address space.

        Args:
            start_node: Starting node for browsing
            max_depth: Maximum browsing depth

        Returns:
            Address space structure
        """
        if not self.connected:
            raise ConnectionError("Not connected to OPC UA server")

        try:
            def _browse_recursive(node, current_depth=0):
                if current_depth >= max_depth:
                    return None

                try:
                    children = node.get_children()
                    node_info = {
                        "node_id": str(node.nodeid),
                        "browse_name": str(node.get_browse_name()),
                        "node_class": str(node.get_node_class()),
                        "children": {}
                    }

                    for child in children:
                        child_info = _browse_recursive(child, current_depth + 1)
                        if child_info:
                            node_info["children"][child_info["browse_name"]] = child_info

                    return node_info

                except Exception as e:
                    self.logger.warning(f"Failed to browse node {node}: {e}")
                    return None

            start_node_obj = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.get_node(start_node)
            )

            address_space = await asyncio.get_event_loop().run_in_executor(
                None, lambda: _browse_recursive(start_node_obj)
            )

            self.logger.info("Address space browsing completed")
            return address_space or {}

        except Exception as e:
            self.logger.error(f"Failed to browse address space: {e}")
            raise

    async def subscribe_to_variables(
        self,
        variables: List[Union[str, NodeId]],
        handler: Optional[callable] = None
    ) -> bool:
        """
        Subscribe to data change notifications for variables.

        Args:
            variables: List of node IDs to subscribe to
            handler: Custom data change handler

        Returns:
            True if subscription successful
        """
        if not self.connected:
            raise ConnectionError("Not connected to OPC UA server")

        try:
            # Create subscription
            self.subscription = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.create_subscription(500, self)  # 500ms publishing interval
            )

            # Subscribe to variables
            nodes = []
            for var in variables:
                node = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.client.get_node(var)
                )
                nodes.append(node)

            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.subscription.subscribe_data_change(nodes)
            )

            if handler:
                self.data_change_handlers.append(handler)

            self.logger.info(f"Subscribed to {len(variables)} variables")
            return True

        except Exception as e:
            self.logger.error(f"Failed to subscribe to variables: {e}")
            return False

    def datachange_notification(self, node, val, data):
        """
        Handle data change notifications (callback from OPC UA library).

        Args:
            node: Changed node
            val: New value
            data: Additional data
        """
        try:
            node_id = str(node.nodeid)
            timestamp = asyncio.get_event_loop().time()

            change_data = {
                "node_id": node_id,
                "value": val,
                "timestamp": timestamp,
                "data": data
            }

            self.logger.debug(f"Data change notification: {node_id} = {val}")

            # Call registered handlers
            for handler in self.data_change_handlers:
                try:
                    asyncio.create_task(handler(change_data))
                except Exception as e:
                    self.logger.error(f"Error in data change handler: {e}")

        except Exception as e:
            self.logger.error(f"Error processing data change notification: {e}")

    async def call_method(
        self,
        object_node: Union[str, NodeId],
        method_name: str,
        *args
    ) -> Any:
        """
        Call OPC UA method.

        Args:
            object_node: Object node containing the method
            method_name: Method name to call
            *args: Method arguments

        Returns:
            Method result
        """
        if not self.connected:
            raise ConnectionError("Not connected to OPC UA server")

        try:
            obj_node = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.get_node(object_node)
            )

            # Find method node
            method_node = await asyncio.get_event_loop().run_in_executor(
                None, lambda: obj_node.get_child([f"0:{method_name}"])
            )

            # Call method
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: obj_node.call_method(method_node, *args)
            )

            self.logger.debug(f"Called method {method_name} with result: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to call method {method_name}: {e}")
            raise

    async def get_server_info(self) -> Dict[str, Any]:
        """Get OPC UA server information."""
        if not self.connected:
            raise ConnectionError("Not connected to OPC UA server")

        try:
            server_state = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.get_node("ns=0;i=2256").get_value()  # ServerState
            )

            server_time = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.get_node("ns=0;i=2258").get_value()  # ServerTime
            )

            return {
                "server_state": server_state,
                "server_time": server_time,
                "endpoint": self.endpoint,
                "connected": self.connected
            }

        except Exception as e:
            self.logger.error(f"Failed to get server info: {e}")
            return {"error": str(e), "connected": self.connected}

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()