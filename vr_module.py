"""
VR Module - Virtual Reality Core Module

This module implements core VR functionality including:
- VR scene management and rendering
- Immersive environment creation
- Motion tracking and haptic feedback
- Multi-user VR interactions
- VR device compatibility and management
"""

import asyncio
import json
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from utils.logging_config import get_logger

logger = get_logger(__name__)


class VRModule:
    """Core Virtual Reality module for IoT platform."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.active_sessions = {}
        self.vr_environments = {}
        self.user_avatars = {}
        self.motion_tracking = {}
        self.haptic_devices = {}
        self.multiuser_sessions = {}
        
    def _default_config(self) -> Dict[str, Any]:
        """Default VR module configuration."""
        return {
            "rendering": {
                "max_fps": 90,
                "resolution": "4K",
                "fov": 110,  # degrees
                "anti_aliasing": "MSAA_4x",
                "lighting": "global_illumination"
            },
            "tracking": {
                "tracking_types": ["6dof", "hand_tracking", "eye_tracking"],
                "update_frequency": 120,
                "precision": "millimeter",
                "latency_threshold": 20  # ms
            },
            "audio": {
                "spatial_audio": True,
                "audio_quality": "lossless",
                "hrtf": True,
                "audio_zones": 8
            },
            "devices": {
                "supported_platforms": ["Oculus", "HTC_Vive", "Valve_Index", "PSVR", "Quest"],
                "min_requirements": {
                    "gpu": "RTX 2070",
                    "ram": "16GB",
                    "storage": "10GB",
                    "usb_ports": 3
                }
            }
        }
    
    def create_vr_session(
        self,
        session_id: str,
        user_id: str,
        environment_type: str,
        device_type: str,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new VR session."""
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "environment_type": environment_type,
            "device_type": device_type,
            "configuration": configuration or {},
            "status": "initializing",
            "created_at": datetime.now(),
            "tracking_state": "not_tracking",
            "current_environment": None,
            "user_avatar": None,
            "active_objects": [],
            "performance_metrics": {
                "fps": 0,
                "tracking_precision": 0.0,
                "latency": 0.0,
                "cpu_usage": 0.0,
                "gpu_usage": 0.0,
                "memory_usage": 0.0
            }
        }
        
        self.active_sessions[session_id] = session
        logger.info(f"VR session created: {session_id} for user {user_id}")
        
        return session
    
    def create_vr_environment(
        self,
        environment_id: str,
        environment_type: str,
        scene_data: Dict[str, Any],
        interactive_elements: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create VR environment."""
        environment = {
            "environment_id": environment_id,
            "environment_type": environment_type,  # "meeting_room", "factory", "showroom", "training"
            "scene_data": scene_data,
            "interactive_elements": interactive_elements or [],
            "physics_enabled": scene_data.get("physics", True),
            "lighting_setup": scene_data.get("lighting", "dynamic"),
            "audio_zones": scene_data.get("audio_zones", []),
            "created_at": datetime.now(),
            "active_users": [],
            "environment_state": "ready"
        }
        
        self.vr_environments[environment_id] = environment
        logger.info(f"VR environment created: {environment_id} - {environment_type}")
        
        return environment
    
    def load_environment_for_session(
        self,
        session_id: str,
        environment_id: str
    ) -> bool:
        """Load VR environment for session."""
        if session_id not in self.active_sessions:
            return False
        
        if environment_id not in self.vr_environments:
            return False
        
        session = self.active_sessions[session_id]
        environment = self.vr_environments[environment_id]
        
        session["current_environment"] = environment_id
        session["status"] = "environment_loaded"
        
        # Add user to environment
        environment["active_users"].append(session["user_id"])
        
        logger.info(f"Environment loaded: {environment_id} for session {session_id}")
        return True
    
    def create_user_avatar(
        self,
        user_id: str,
        avatar_config: Dict[str, Any],
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create user avatar for VR."""
        avatar = {
            "user_id": user_id,
            "avatar_id": f"avatar_{user_id}",
            "avatar_config": avatar_config,
            "customizations": customizations or {},
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
            "hand_positions": {
                "left": {"x": 0.0, "y": 0.0, "z": 0.0},
                "right": {"x": 0.0, "y": 0.0, "z": 0.0}
            },
            "gestures": [],
            "voice_chat": {
                "enabled": False,
                "muted": False,
                "volume": 1.0
            },
            "created_at": datetime.now()
        }
        
        self.user_avatars[user_id] = avatar
        logger.info(f"User avatar created: {user_id}")
        
        return avatar
    
    def start_motion_tracking(
        self,
        session_id: str,
        tracking_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Start motion tracking for VR session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session["tracking_state"] = "initializing"
        session["tracking_started_at"] = datetime.now()
        
        # Initialize motion tracking data
        self.motion_tracking[session_id] = {
            "head_position": {"x": 0.0, "y": 1.7, "z": 0.0},  # Average head height
            "head_rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
            "left_controller": {"position": {"x": -0.3, "y": 1.2, "z": 0.2}, "rotation": {"x": 0.0, "y": 0.0, "z": 0.0}},
            "right_controller": {"position": {"x": 0.3, "y": 1.2, "z": 0.2}, "rotation": {"x": 0.0, "y": 0.0, "z": 0.0}},
            "tracking_quality": 0.0,
            "last_update": datetime.now(),
            "tracking_history": []
        }
        
        session["tracking_state"] = "tracking"
        logger.info(f"Motion tracking started: {session_id}")
        return True
    
    def update_motion_data(
        self,
        session_id: str,
        head_position: Dict[str, float],
        head_rotation: Dict[str, float],
        left_controller: Optional[Dict[str, Any]] = None,
        right_controller: Optional[Dict[str, Any]] = None,
        tracking_quality: float = 1.0
    ) -> bool:
        """Update motion tracking data."""
        if session_id not in self.motion_tracking:
            return False
        
        tracking = self.motion_tracking[session_id]
        tracking["head_position"] = head_position
        tracking["head_rotation"] = head_rotation
        tracking["tracking_quality"] = tracking_quality
        tracking["last_update"] = datetime.now()
        
        if left_controller:
            tracking["left_controller"] = left_controller
        
        if right_controller:
            tracking["right_controller"] = right_controller
        
        # Add to tracking history
        tracking["tracking_history"].append({
            "timestamp": datetime.now(),
            "head_position": head_position.copy(),
            "head_rotation": head_rotation.copy(),
            "tracking_quality": tracking_quality
        })
        
        # Limit history size
        if len(tracking["tracking_history"]) > 1000:
            tracking["tracking_history"] = tracking["tracking_history"][-500:]
        
        # Update session metrics
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session["performance_metrics"]["tracking_precision"] = tracking_quality
        
        # Update user avatar position
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            user_id = session["user_id"]
            if user_id in self.user_avatars:
                self.user_avatars[user_id]["position"] = head_position
                self.user_avatars[user_id]["rotation"] = head_rotation
                
                if left_controller:
                    self.user_avatars[user_id]["hand_positions"]["left"] = left_controller["position"]
                if right_controller:
                    self.user_avatars[user_id]["hand_positions"]["right"] = right_controller["position"]
        
        return True
    
    def setup_haptic_feedback(
        self,
        session_id: str,
        device_config: Dict[str, Any]
    ) -> bool:
        """Setup haptic feedback devices."""
        if session_id not in self.active_sessions:
            return False
        
        haptic_device = {
            "session_id": session_id,
            "device_config": device_config,
            "enabled": True,
            "intensity": 1.0,
            "active_effects": [],
            "device_status": "ready",
            "created_at": datetime.now()
        }
        
        self.haptic_devices[session_id] = haptic_device
        logger.info(f"Haptic feedback setup: {session_id}")
        return True
    
    def trigger_haptic_effect(
        self,
        session_id: str,
        effect_type: str,
        intensity: float,
        duration: float,
        target_hand: str = "both"
    ) -> bool:
        """Trigger haptic feedback effect."""
        if session_id not in self.haptic_devices:
            return False
        
        device = self.haptic_devices[session_id]
        if not device["enabled"]:
            return False
        
        effect = {
            "effect_type": effect_type,  # "vibration", "impact", "texture", "force"
            "intensity": intensity,
            "duration": duration,
            "target_hand": target_hand,
            "triggered_at": datetime.now()
        }
        
        device["active_effects"].append(effect)
        logger.info(f"Haptic effect triggered: {session_id} - {effect_type}")
        return True
    
    def create_multiuser_session(
        self,
        session_id: str,
        max_users: int = 8,
        session_type: str = "collaborative"
    ) -> Dict[str, Any]:
        """Create multi-user VR session."""
        multiuser = {
            "session_id": session_id,
            "max_users": max_users,
            "current_users": [],
            "session_type": session_type,
            "shared_space": True,
            "voice_chat": True,
            "synchronized_objects": [],
            "created_at": datetime.now(),
            "session_state": "waiting"
        }
        
        self.multiuser_sessions[session_id] = multiuser
        logger.info(f"Multi-user session created: {session_id}")
        
        return multiuser
    
    def join_multiuser_session(
        self,
        session_id: str,
        user_session_id: str,
        user_id: str
    ) -> bool:
        """Join multi-user VR session."""
        if session_id not in self.multiuser_sessions:
            return False
        
        multiuser = self.multiuser_sessions[session_id]
        
        if len(multiuser["current_users"]) >= multiuser["max_users"]:
            return False
        
        user_data = {
            "user_session_id": user_session_id,
            "user_id": user_id,
            "joined_at": datetime.now(),
            "voice_chat_enabled": True
        }
        
        multiuser["current_users"].append(user_data)
        multiuser["session_state"] = "active" if len(multiuser["current_users"]) > 1 else "waiting"
        
        logger.info(f"User joined multi-user session: {user_id} -> {session_id}")
        return True
    
    def add_interactive_object(
        self,
        environment_id: str,
        object_id: str,
        object_type: str,
        position: Dict[str, float],
        properties: Dict[str, Any]
    ) -> bool:
        """Add interactive object to VR environment."""
        if environment_id not in self.vr_environments:
            return False
        
        environment = self.vr_environments[environment_id]
        
        interactive_object = {
            "object_id": object_id,
            "object_type": object_type,
            "position": position,
            "properties": properties,
            "interactions": [],
            "state": "active",
            "created_at": datetime.now()
        }
        
        environment["interactive_elements"].append(interactive_object)
        logger.info(f"Interactive object added: {environment_id} - {object_id}")
        return True
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get VR session status and metrics."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id].copy()
        
        # Add motion tracking data
        if session_id in self.motion_tracking:
            session["motion_tracking"] = self.motion_tracking[session_id]
        
        # Add haptic device info
        if session_id in self.haptic_devices:
            session["haptic_feedback"] = self.haptic_devices[session_id]
        
        # Add environment info
        if session.get("current_environment"):
            env_id = session["current_environment"]
            if env_id in self.vr_environments:
                session["environment"] = self.vr_environments[env_id]
        
        return session
    
    def get_vr_metrics(self) -> Dict[str, Any]:
        """Get overall VR system metrics."""
        active_sessions = len(self.active_sessions)
        tracking_sessions = sum(
            1 for session in self.active_sessions.values()
            if session.get("tracking_state") == "tracking"
        )
        
        multiuser_sessions = len(self.multiuser_sessions)
        total_multiuser_users = sum(
            len(session["current_users"])
            for session in self.multiuser_sessions.values()
        )
        
        total_environments = len(self.vr_environments)
        active_environments = sum(
            1 for env in self.vr_environments.values()
            if len(env["active_users"]) > 0
        )
        
        avg_tracking_quality = 0.0
        if self.motion_tracking:
            qualities = [
                tracking["tracking_quality"] 
                for tracking in self.motion_tracking.values()
            ]
            avg_tracking_quality = sum(qualities) / len(qualities) if qualities else 0.0
        
        return {
            "active_sessions": active_sessions,
            "tracking_sessions": tracking_sessions,
            "multiuser_sessions": multiuser_sessions,
            "total_multiuser_users": total_multiuser_users,
            "total_environments": total_environments,
            "active_environments": active_environments,
            "registered_avatars": len(self.user_avatars),
            "haptic_devices_active": len(self.haptic_devices),
            "average_tracking_quality": avg_tracking_quality,
            "system_uptime": str(datetime.now() - datetime.now().replace(hour=0, minute=0, second=0))
        }
    
    def cleanup_session(self, session_id: str) -> bool:
        """Clean up VR session and associated data."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        user_id = session["user_id"]
        environment_id = session.get("current_environment")
        
        # Remove session
        del self.active_sessions[session_id]
        
        # Remove motion tracking
        if session_id in self.motion_tracking:
            del self.motion_tracking[session_id]
        
        # Remove haptic device
        if session_id in self.haptic_devices:
            del self.haptic_devices[session_id]
        
        # Remove user from environment
        if environment_id and environment_id in self.vr_environments:
            environment = self.vr_environments[environment_id]
            if user_id in environment["active_users"]:
                environment["active_users"].remove(user_id)
        
        # Remove from multiuser sessions
        for multiuser_id, multiuser in self.multiuser_sessions.items():
            multiuser["current_users"] = [
                user for user in multiuser["current_users"]
                if user["user_id"] != user_id
            ]
        
        logger.info(f"VR session cleaned up: {session_id}")
        return True


# Global VR module instance
vr_module = VRModule()


def create_vr_session(
    session_id: str,
    user_id: str,
    environment_type: str,
    device_type: str,
    configuration: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create new VR session."""
    return vr_module.create_vr_session(session_id, user_id, environment_type, device_type, configuration)


def create_vr_environment(
    environment_id: str,
    environment_type: str,
    scene_data: Dict[str, Any],
    interactive_elements: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Create VR environment."""
    return vr_module.create_vr_environment(environment_id, environment_type, scene_data, interactive_elements)


def create_user_avatar(
    user_id: str,
    avatar_config: Dict[str, Any],
    customizations: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create user avatar for VR."""
    return vr_module.create_user_avatar(user_id, avatar_config, customizations)


def start_vr_motion_tracking(
    session_id: str,
    tracking_config: Optional[Dict[str, Any]] = None
) -> bool:
    """Start motion tracking for VR session."""
    return vr_module.start_motion_tracking(session_id, tracking_config)


def update_vr_motion_data(
    session_id: str,
    head_position: Dict[str, float],
    head_rotation: Dict[str, float],
    left_controller: Optional[Dict[str, Any]] = None,
    right_controller: Optional[Dict[str, Any]] = None,
    tracking_quality: float = 1.0
) -> bool:
    """Update motion tracking data."""
    return vr_module.update_motion_data(session_id, head_position, head_rotation, left_controller, right_controller, tracking_quality)


def setup_vr_haptic_feedback(
    session_id: str,
    device_config: Dict[str, Any]
) -> bool:
    """Setup haptic feedback devices."""
    return vr_module.setup_haptic_feedback(session_id, device_config)


def trigger_vr_haptic_effect(
    session_id: str,
    effect_type: str,
    intensity: float,
    duration: float,
    target_hand: str = "both"
) -> bool:
    """Trigger haptic feedback effect."""
    return vr_module.trigger_haptic_effect(session_id, effect_type, intensity, duration, target_hand)


def create_vr_multiuser_session(
    session_id: str,
    max_users: int = 8,
    session_type: str = "collaborative"
) -> Dict[str, Any]:
    """Create multi-user VR session."""
    return vr_module.create_multiuser_session(session_id, max_users, session_type)


def get_vr_session_status(session_id: str) -> Optional[Dict[str, Any]]:
    """Get VR session status."""
    return vr_module.get_session_status(session_id)


def get_vr_metrics() -> Dict[str, Any]:
    """Get overall VR system metrics."""
    return vr_module.get_vr_metrics()
