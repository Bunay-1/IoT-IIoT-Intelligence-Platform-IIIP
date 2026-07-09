"""
AR/VR Features Module for IoT Intelligence Platform.

This module provides Augmented Reality (AR) and Virtual Reality (VR) capabilities
for maintenance guidance, training simulations, and mixed reality dashboards.

Refactored to use modular architecture with separate AR, VR, MR modules
and centralized manager for better maintainability.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio

import pandas as pd

from src.core.config import settings
from src.utils.logging_config import get_logger
from src.gui.arvr_manager import ARVRManager

logger = get_logger(__name__)


class ARVRError(Exception):
    """Base exception for AR/VR module errors."""
    pass


class ARGuidanceError(ARVRError):
    """Raised when AR guidance fails."""
    pass


class VRSimulationError(ARVRError):
    """Raised when VR simulation fails."""
    pass


class MixedRealityError(ARVRError):
    """Raised when mixed reality operations fail."""
    pass


class ARVRFeatures:
    """
    AR/VR Features System for immersive IoT experiences.

    Provides AR maintenance guidance, VR training simulations,
    and mixed reality dashboards for industrial applications.

    Now uses modular architecture with ARVRManager for coordination.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, config_file: Optional[str] = None) -> None:
        """
        Initialize the AR/VR features module.

        Args:
            config: Optional configuration dictionary
            config_file: Optional path to config file
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize manager
        self.manager = ARVRManager(self.config, config_file)

    async def ar_maintenance_guidance(self, device_id: str, user_id: Optional[str] = None, maintenance_type: str = "general") -> Dict[str, Any]:
        """
        Provide AR maintenance guidance for devices.

        Args:
            device_id: ID of the device needing maintenance
            user_id: ID of the user receiving guidance
            maintenance_type: Type of maintenance (general, emergency, preventive)

        Returns:
            Dictionary containing AR guidance information

        Raises:
            ARGuidanceError: If AR guidance fails
            ValueError: If input validation fails
        """
        try:
            return await self.manager.ar_maintenance_guidance(device_id, user_id, maintenance_type)
        except Exception as e:
            if "Maximum number of concurrent AR guidance sessions reached" in str(e):
                raise ARGuidanceError(str(e)) from e
            raise

    def vr_training_simulator(self, scenario: str, user_id: Optional[str] = None, difficulty: str = "normal") -> Dict[str, Any]:
        """
        Run VR training simulation.

        Args:
            scenario: Training scenario to simulate
            user_id: ID of the user undergoing training
            difficulty: Difficulty level (easy, normal, hard)

        Returns:
            Dictionary containing simulation results

        Raises:
            VRSimulationError: If VR simulation fails
        """
        try:
            return self.manager.vr_training_simulator(scenario, user_id, difficulty)
        except Exception as e:
            raise VRSimulationError(str(e)) from e

    def mixed_reality_dashboard(self, data: Union[pd.DataFrame, List[Dict[str, Any]]], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Render mixed reality dashboard.

        Args:
            data: Data to display in the dashboard
            user_id: ID of the user viewing the dashboard

        Returns:
            Dictionary containing dashboard configuration

        Raises:
            MixedRealityError: If dashboard rendering fails
        """
        try:
            return self.manager.mixed_reality_dashboard(data, user_id)
        except Exception as e:
            raise MixedRealityError(str(e)) from e

    async def end_session(self, session_id: str) -> bool:
        """
        End an active AR/VR session.

        Args:
            session_id: Session identifier

        Returns:
            True if session ended successfully
        """
        return await self.manager.end_session(session_id)

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active AR/VR sessions."""
        return self.manager.get_active_sessions()

    async def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        await self.manager.cleanup_expired_sessions()


# Backward compatibility functions
def ar_maintenance_guidance(device_id: str, user_id: Optional[str] = None, maintenance_type: str = "general") -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    import asyncio
    manager = ARVRManager()
    return asyncio.run(manager.ar_maintenance_guidance(device_id, user_id, maintenance_type))


def vr_training_simulator(scenario: str, user_id: Optional[str] = None, difficulty: str = "normal") -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    manager = ARVRManager()
    return manager.vr_training_simulator(scenario, user_id, difficulty)


def mixed_reality_dashboard(data: Union[pd.DataFrame, List[Dict[str, Any]]], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    manager = ARVRManager()
    return manager.mixed_reality_dashboard(data, user_id)