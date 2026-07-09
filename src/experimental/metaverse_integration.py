"""
Metaverse Integration Module for IoT IIoT Intelligence Platform

This module provides metaverse capabilities for digital twins, enabling
immersive, collaborative, and social experiences in virtual production environments.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import time
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Avatar:
    """Represents a user avatar in the metaverse."""
    avatar_id: str
    user_id: str
    appearance: Dict[str, Any]
    position: Dict[str, float]
    rotation: Dict[str, float]
    actions: List[str] = field(default_factory=list)
    status: str = "active"

@dataclass
class VirtualSpace:
    """Represents a virtual space in the metaverse."""
    space_id: str
    name: str
    environment_type: str
    dimensions: Dict[str, float]
    assets: List[Dict] = field(default_factory=list)
    users: List[str] = field(default_factory=list)
    interactions: List[Dict] = field(default_factory=list)

@dataclass
class SocialInteraction:
    """Represents social interactions in the metaverse."""
    interaction_id: str
    interaction_type: str  # 'voice_chat', 'text_chat', 'gesture', 'collaboration'
    participants: List[str]
    content: Any
    timestamp: float
    location: Dict[str, float]

class MetaverseIntegration:
    """
    Metaverse integration for digital twins, providing immersive social experiences.
    """

    def __init__(self, spaces_path: str = "data/metaverse_spaces.json",
                 avatars_path: str = "data/avatars.json"):
        """
        Initialize metaverse integration.

        Args:
            spaces_path: Path to virtual spaces data
            avatars_path: Path to avatars data
        """
        self.spaces_path = Path(spaces_path)
        self.avatars_path = Path(avatars_path)

        self.spaces_path.parent.mkdir(parents=True, exist_ok=True)
        self.avatars_path.parent.mkdir(parents=True, exist_ok=True)

        self.virtual_spaces: Dict[str, VirtualSpace] = {}
        self.avatars: Dict[str, Avatar] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self.interactions_history: List[SocialInteraction] = []

        # Load data
        self._load_spaces()
        self._load_avatars()

        # Initialize default spaces if none exist
        if not self.virtual_spaces:
            self._create_default_spaces()

    def _load_spaces(self):
        """Load virtual spaces."""
        try:
            if self.spaces_path.exists():
                with open(self.spaces_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for space_data in data.get('spaces', []):
                        space = VirtualSpace(**space_data)
                        self.virtual_spaces[space.space_id] = space
                logger.info(f"Loaded {len(self.virtual_spaces)} virtual spaces")
        except Exception as e:
            logger.error(f"Failed to load spaces: {e}")

    def _load_avatars(self):
        """Load avatars."""
        try:
            if self.avatars_path.exists():
                with open(self.avatars_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for avatar_data in data.get('avatars', []):
                        avatar = Avatar(**avatar_data)
                        self.avatars[avatar.avatar_id] = avatar
                logger.info(f"Loaded {len(self.avatars)} avatars")
        except Exception as e:
            logger.error(f"Failed to load avatars: {e}")

    def _create_default_spaces(self):
        """Create default virtual spaces."""
        # Production Control Room
        control_room = VirtualSpace(
            space_id="control_room_001",
            name="Production Control Room",
            environment_type="control_center",
            dimensions={"width": 20, "height": 10, "depth": 15},
            assets=[
                {
                    "asset_id": "main_dashboard",
                    "type": "dashboard",
                    "position": {"x": 0, "y": 1.5, "z": -5},
                    "size": {"width": 4, "height": 2, "depth": 0.1}
                },
                {
                    "asset_id": "holographic_display",
                    "type": "hologram",
                    "position": {"x": 3, "y": 1, "z": -3},
                    "size": {"width": 2, "height": 2, "depth": 2}
                }
            ]
        )

        # Virtual Factory Floor
        factory_floor = VirtualSpace(
            space_id="factory_floor_001",
            name="Virtual Factory Floor",
            environment_type="production_floor",
            dimensions={"width": 100, "height": 20, "depth": 50},
            assets=[
                {
                    "asset_id": "cnc_machine_1",
                    "type": "digital_twin",
                    "position": {"x": 10, "y": 0, "z": 10},
                    "twin_id": "cnc_001"
                },
                {
                    "asset_id": "robot_arm_1",
                    "type": "digital_twin",
                    "position": {"x": 20, "y": 0, "z": 15},
                    "twin_id": "robot_001"
                },
                {
                    "asset_id": "conveyor_belt_1",
                    "type": "digital_twin",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "twin_id": "conveyor_001"
                }
            ]
        )

        # Collaborative Workspace
        collab_space = VirtualSpace(
            space_id="collab_workspace_001",
            name="Collaborative Design Workspace",
            environment_type="workspace",
            dimensions={"width": 30, "height": 10, "depth": 20},
            assets=[
                {
                    "asset_id": "whiteboard",
                    "type": "interactive_surface",
                    "position": {"x": 0, "y": 1, "z": -5},
                    "size": {"width": 3, "height": 2, "depth": 0.1}
                },
                {
                    "asset_id": "3d_projector",
                    "type": "projector",
                    "position": {"x": 5, "y": 1.5, "z": -3},
                    "size": {"width": 1, "height": 1, "depth": 1}
                }
            ]
        )

        self.virtual_spaces[control_room.space_id] = control_room
        self.virtual_spaces[factory_floor.space_id] = factory_floor
        self.virtual_spaces[collab_space.space_id] = collab_space
        self._save_spaces()

    def _save_spaces(self):
        """Save virtual spaces."""
        try:
            data = {
                'spaces': [vars(s) for s in self.virtual_spaces.values()]
            }

            with open(self.spaces_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("Spaces saved successfully")
        except Exception as e:
            logger.error(f"Failed to save spaces: {e}")

    def _save_avatars(self):
        """Save avatars."""
        try:
            data = {
                'avatars': [vars(a) for a in self.avatars.values()]
            }

            with open(self.avatars_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("Avatars saved successfully")
        except Exception as e:
            logger.error(f"Failed to save avatars: {e}")

    def create_avatar(self, user_id: str, appearance_config: Dict[str, Any]) -> str:
        """
        Create an avatar for a user.

        Args:
            user_id: User identifier
            appearance_config: Avatar appearance configuration

        Returns:
            Avatar ID
        """
        avatar_id = f"avatar_{user_id}_{int(time.time())}"

        avatar = Avatar(
            avatar_id=avatar_id,
            user_id=user_id,
            appearance=appearance_config,
            position={"x": 0, "y": 0, "z": 0},
            rotation={"x": 0, "y": 0, "z": 0}
        )

        self.avatars[avatar_id] = avatar
        self._save_avatars()

        logger.info(f"Created avatar {avatar_id} for user {user_id}")
        return avatar_id

    def start_metaverse_session(self, user_id: str, space_id: str,
                               avatar_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a metaverse session for a user.

        Args:
            user_id: User identifier
            space_id: Virtual space identifier
            avatar_id: Avatar identifier (optional)

        Returns:
            Session configuration
        """
        if space_id not in self.virtual_spaces:
            raise ValueError(f"Virtual space {space_id} not found")

        # Get or create avatar
        if not avatar_id:
            avatar_id = self._get_user_avatar(user_id)
            if not avatar_id:
                # Create default avatar
                default_appearance = {
                    "body_type": "standard",
                    "clothing": "work_uniform",
                    "accessories": []
                }
                avatar_id = self.create_avatar(user_id, default_appearance)

        if avatar_id not in self.avatars:
            raise ValueError(f"Avatar {avatar_id} not found")

        space = self.virtual_spaces[space_id]
        avatar = self.avatars[avatar_id]

        session_id = f"session_{user_id}_{space_id}_{int(time.time())}"

        session = {
            'session_id': session_id,
            'user_id': user_id,
            'space_id': space_id,
            'avatar_id': avatar_id,
            'start_time': time.time(),
            'position': avatar.position.copy(),
            'rotation': avatar.rotation.copy(),
            'interactions': [],
            'permissions': self._get_space_permissions(user_id, space_id)
        }

        self.active_sessions[session_id] = session

        # Add user to space
        if user_id not in space.users:
            space.users.append(user_id)

        logger.info(f"Started metaverse session {session_id}")

        return {
            'session_id': session_id,
            'space': vars(space),
            'avatar': vars(avatar),
            'initial_state': {
                'position': avatar.position,
                'rotation': avatar.rotation,
                'nearby_users': self._get_nearby_users(session),
                'interactive_assets': self._get_interactive_assets(session)
            }
        }

    def _get_user_avatar(self, user_id: str) -> Optional[str]:
        """Get avatar ID for a user."""
        for avatar in self.avatars.values():
            if avatar.user_id == user_id:
                return avatar.avatar_id
        return None

    def _get_space_permissions(self, user_id: str, space_id: str) -> List[str]:
        """Get user permissions for a space."""
        # Simplified permission system
        base_permissions = ["view", "move"]
        if user_id.startswith("admin") or user_id.startswith("supervisor"):
            base_permissions.extend(["edit", "control_assets", "moderate"])
        return base_permissions

    def _get_nearby_users(self, session: Dict) -> List[Dict[str, Any]]:
        """Get users near the current session user."""
        space = self.virtual_spaces[session['space_id']]
        nearby_users = []

        for user_id in space.users:
            if user_id != session['user_id']:
                # Find user's avatar and session
                avatar_id = self._get_user_avatar(user_id)
                if avatar_id and avatar_id in self.avatars:
                    avatar = self.avatars[avatar_id]
                    distance = self._calculate_distance(session['position'], avatar.position)

                    if distance < 10:  # Within 10 units
                        nearby_users.append({
                            'user_id': user_id,
                            'avatar_id': avatar_id,
                            'position': avatar.position,
                            'distance': distance
                        })

        return nearby_users

    def _get_interactive_assets(self, session: Dict) -> List[Dict[str, Any]]:
        """Get interactive assets near the user."""
        space = self.virtual_spaces[session['space_id']]
        interactive_assets = []

        for asset in space.assets:
            distance = self._calculate_distance(session['position'], asset['position'])

            if distance < 15:  # Within interaction range
                interactive_assets.append({
                    'asset_id': asset['asset_id'],
                    'type': asset['type'],
                    'position': asset['position'],
                    'distance': distance,
                    'interactive': True
                })

        return interactive_assets

    def _calculate_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """Calculate distance between two positions."""
        dx = pos1['x'] - pos2['x']
        dy = pos1['y'] - pos2['y']
        dz = pos1['z'] - pos2['z']
        return (dx**2 + dy**2 + dz**2)**0.5

    def update_avatar_position(self, session_id: str, position: Dict[str, float],
                              rotation: Dict[str, float]) -> Dict[str, Any]:
        """
        Update avatar position and rotation.

        Args:
            session_id: Session identifier
            position: New position
            rotation: New rotation

        Returns:
            Update confirmation with nearby updates
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        avatar = self.avatars[session['avatar_id']]

        # Update avatar
        avatar.position = position
        avatar.rotation = rotation
        session['position'] = position
        session['rotation'] = rotation

        # Get updated nearby information
        nearby_users = self._get_nearby_users(session)
        interactive_assets = self._get_interactive_assets(session)

        return {
            'status': 'updated',
            'nearby_users': nearby_users,
            'interactive_assets': interactive_assets,
            'timestamp': time.time()
        }

    def create_social_interaction(self, session_id: str, interaction_type: str,
                                 content: Any, target_users: Optional[List[str]] = None) -> str:
        """
        Create a social interaction in the metaverse.

        Args:
            session_id: Session identifier
            interaction_type: Type of interaction
            content: Interaction content
            target_users: Target users (optional)

        Returns:
            Interaction ID
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        space = self.virtual_spaces[session['space_id']]

        interaction_id = f"interaction_{int(time.time())}_{session_id}"

        participants = [session['user_id']]
        if target_users:
            participants.extend(target_users)

        interaction = SocialInteraction(
            interaction_id=interaction_id,
            interaction_type=interaction_type,
            participants=participants,
            content=content,
            timestamp=time.time(),
            location=session['position'].copy()
        )

        self.interactions_history.append(interaction)

        # Add to space interactions
        space.interactions.append({
            'interaction_id': interaction_id,
            'type': interaction_type,
            'participants': participants,
            'timestamp': interaction.timestamp
        })

        # Record in session
        session['interactions'].append(interaction_id)

        logger.info(f"Created {interaction_type} interaction {interaction_id}")

        return interaction_id

    def get_space_state(self, space_id: str) -> Dict[str, Any]:
        """
        Get current state of a virtual space.

        Args:
            space_id: Space identifier

        Returns:
            Space state
        """
        if space_id not in self.virtual_spaces:
            raise ValueError(f"Space {space_id} not found")

        space = self.virtual_spaces[space_id]

        # Get active avatars in space
        active_avatars = []
        for session in self.active_sessions.values():
            if session['space_id'] == space_id:
                avatar = self.avatars[session['avatar_id']]
                active_avatars.append({
                    'avatar_id': avatar.avatar_id,
                    'user_id': avatar.user_id,
                    'position': avatar.position,
                    'rotation': avatar.rotation,
                    'status': avatar.status
                })

        # Get recent interactions
        recent_interactions = [
            vars(i) for i in self.interactions_history[-10:]  # Last 10 interactions
            if any(user in space.users for user in i.participants)
        ]

        return {
            'space_id': space_id,
            'name': space.name,
            'active_users': len(space.users),
            'active_avatars': active_avatars,
            'assets': space.assets,
            'recent_interactions': recent_interactions,
            'timestamp': time.time()
        }

    def collaborate_on_asset(self, session_id: str, asset_id: str,
                           action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform collaborative action on an asset.

        Args:
            session_id: Session identifier
            asset_id: Asset identifier
            action: Action to perform
            parameters: Action parameters

        Returns:
            Collaboration result
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        space = self.virtual_spaces[session['space_id']]

        # Find asset
        asset = next((a for a in space.assets if a['asset_id'] == asset_id), None)
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        # Check if user can interact with asset
        distance = self._calculate_distance(session['position'], asset['position'])
        if distance > 5:  # Interaction range
            return {'status': 'too_far', 'distance': distance}

        # Perform action based on type
        result = self._execute_asset_action(asset, action, parameters, session)

        # Create collaboration interaction
        self.create_social_interaction(
            session_id,
            'collaboration',
            {
                'asset_id': asset_id,
                'action': action,
                'result': result
            }
        )

        return result

    def _execute_asset_action(self, asset: Dict, action: str,
                            parameters: Dict, session: Dict) -> Dict[str, Any]:
        """Execute action on an asset."""
        asset_type = asset['type']

        if asset_type == 'dashboard':
            return self._handle_dashboard_action(asset, action, parameters)
        elif asset_type == 'digital_twin':
            return self._handle_digital_twin_action(asset, action, parameters, session)
        elif asset_type == 'interactive_surface':
            return self._handle_surface_action(asset, action, parameters)
        elif asset_type == 'hologram':
            return self._handle_hologram_action(asset, action, parameters)
        else:
            return {'status': 'unknown_asset_type'}

    def _handle_dashboard_action(self, asset: Dict, action: str, parameters: Dict) -> Dict[str, Any]:
        """Handle dashboard interactions."""
        if action == 'view_metrics':
            return {
                'status': 'metrics_displayed',
                'metrics': ['throughput', 'efficiency', 'quality'],
                'data': {'throughput': 95.2, 'efficiency': 87.3, 'quality': 98.1}
            }
        elif action == 'adjust_parameter':
            param_name = parameters.get('parameter')
            new_value = parameters.get('value')
            return {
                'status': 'parameter_adjusted',
                'parameter': param_name,
                'new_value': new_value
            }
        return {'status': 'action_not_supported'}

    def _handle_digital_twin_action(self, asset: Dict, action: str,
                                   parameters: Dict, session: Dict) -> Dict[str, Any]:
        """Handle digital twin interactions."""
        twin_id = asset.get('twin_id')
        if not twin_id:
            return {'status': 'no_twin_associated'}

        if action == 'inspect':
            return {
                'status': 'inspection_mode',
                'twin_id': twin_id,
                'inspection_data': {
                    'status': 'operational',
                    'temperature': 65.5,
                    'vibration': 0.8
                }
            }
        elif action == 'simulate':
            scenario = parameters.get('scenario', 'normal_operation')
            return {
                'status': 'simulation_started',
                'twin_id': twin_id,
                'scenario': scenario
            }
        return {'status': 'action_not_supported'}

    def _handle_surface_action(self, asset: Dict, action: str, parameters: Dict) -> Dict[str, Any]:
        """Handle interactive surface actions."""
        if action == 'draw':
            return {
                'status': 'drawing_recorded',
                'coordinates': parameters.get('coordinates', [])
            }
        elif action == 'write':
            return {
                'status': 'text_recorded',
                'text': parameters.get('text', '')
            }
        return {'status': 'action_not_supported'}

    def _handle_hologram_action(self, asset: Dict, action: str, parameters: Dict) -> Dict[str, Any]:
        """Handle hologram interactions."""
        if action == 'rotate':
            return {
                'status': 'rotated',
                'rotation': parameters.get('rotation', {'x': 0, 'y': 0, 'z': 0})
            }
        elif action == 'zoom':
            return {
                'status': 'zoomed',
                'zoom_level': parameters.get('zoom', 1.0)
            }
        return {'status': 'action_not_supported'}

    def end_metaverse_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a metaverse session.

        Args:
            session_id: Session identifier

        Returns:
            Session summary
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        space = self.virtual_spaces[session['space_id']]

        end_time = time.time()
        duration = end_time - session['start_time']

        # Remove user from space
        if session['user_id'] in space.users:
            space.users.remove(session['user_id'])

        summary = {
            'session_id': session_id,
            'duration_seconds': duration,
            'interactions_count': len(session['interactions']),
            'space_id': session['space_id'],
            'end_time': datetime.fromtimestamp(end_time).isoformat()
        }

        # Clean up session
        del self.active_sessions[session_id]

        logger.info(f"Ended metaverse session {session_id}")

        return {
            'status': 'ended',
            'summary': summary
        }

    def get_user_social_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get social statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Social statistics
        """
        user_interactions = [
            i for i in self.interactions_history
            if user_id in i.participants
        ]

        interaction_types = {}
        for interaction in user_interactions:
            itype = interaction.interaction_type
            interaction_types[itype] = interaction_types.get(itype, 0) + 1

        total_sessions = len([
            s for s in self.active_sessions.values()
            if s['user_id'] == user_id
        ])

        return {
            'user_id': user_id,
            'total_interactions': len(user_interactions),
            'interaction_types': interaction_types,
            'active_sessions': total_sessions,
            'collaboration_score': len([i for i in user_interactions if i.interaction_type == 'collaboration'])
        }


# Example usage
if __name__ == "__main__":
    # Initialize metaverse integration
    metaverse = MetaverseIntegration()

    # Create avatar
    avatar_id = metaverse.create_avatar("user_001", {"body_type": "standard", "clothing": "engineer"})
    print(f"Created avatar: {avatar_id}")

    # Start session
    session = metaverse.start_metaverse_session("user_001", "factory_floor_001", avatar_id)
    print(f"Started session: {session['session_id']}")

    # Update position
    update = metaverse.update_avatar_position(session['session_id'],
                                            {"x": 5, "y": 0, "z": 5},
                                            {"x": 0, "y": 45, "z": 0})
    print("Position updated:", update['status'])

    # Create interaction
    interaction_id = metaverse.create_social_interaction(
        session['session_id'], 'voice_chat', 'Hello from metaverse!'
    )
    print(f"Created interaction: {interaction_id}")

    # Get space state
    space_state = metaverse.get_space_state("factory_floor_001")
    print(f"Space has {space_state['active_users']} active users")

    # End session
    summary = metaverse.end_metaverse_session(session['session_id'])
    print("Session ended:", summary['summary']['duration_seconds'], "seconds")