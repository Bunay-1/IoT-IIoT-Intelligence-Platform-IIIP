"""
Collaborative Workspace Module for IoT IIoT Intelligence Platform

This module provides collaborative workspaces for remote team interaction,
enabling real-time collaboration, shared digital twins, and synchronized workflows.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import asyncio
import time
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class CollaborationMode(Enum):
    """Types of collaboration modes."""
    REAL_TIME = "real_time"
    ASYNC = "async"
    HYBRID = "hybrid"

class AccessLevel(Enum):
    """Access levels for workspace participants."""
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"

@dataclass
class WorkspaceParticipant:
    """Represents a participant in a collaborative workspace."""
    user_id: str
    avatar_id: str
    access_level: AccessLevel
    joined_at: float
    last_activity: float
    current_focus: Optional[str] = None
    contributions: List[Dict] = field(default_factory=list)

@dataclass
class SharedAsset:
    """Represents a shared asset in the workspace."""
    asset_id: str
    asset_type: str  # 'digital_twin', 'document', 'dashboard', '3d_model'
    owner_id: str
    current_version: int
    collaborators: List[str] = field(default_factory=list)
    lock_holder: Optional[str] = None
    lock_timestamp: Optional[float] = None
    change_history: List[Dict] = field(default_factory=list)

@dataclass
class CollaborationSession:
    """Represents an active collaboration session."""
    session_id: str
    workspace_id: str
    mode: CollaborationMode
    participants: List[WorkspaceParticipant] = field(default_factory=list)
    shared_assets: List[SharedAsset] = field(default_factory=list)
    active_tasks: List[Dict] = field(default_factory=list)
    communications: List[Dict] = field(default_factory=list)
    start_time: float
    last_activity: float

class CollaborativeWorkspace:
    """
    Collaborative workspace for remote team interaction and synchronized workflows.
    """

    def __init__(self, workspaces_path: str = "data/collaborative_workspaces.json",
                 sessions_path: str = "data/workspace_sessions.json"):
        """
        Initialize collaborative workspace system.

        Args:
            workspaces_path: Path to workspace configurations
            sessions_path: Path to session data
        """
        self.workspaces_path = Path(workspaces_path)
        self.sessions_path = Path(sessions_path)

        self.workspaces_path.parent.mkdir(parents=True, exist_ok=True)
        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)

        self.workspaces: Dict[str, Dict] = {}
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.session_history: List[CollaborationSession] = []

        # Load data
        self._load_workspaces()
        self._load_sessions()

        # Initialize default workspace if none exist
        if not self.workspaces:
            self._create_default_workspace()

    def _load_workspaces(self):
        """Load workspace configurations."""
        try:
            if self.workspaces_path.exists():
                with open(self.workspaces_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.workspaces = data.get('workspaces', {})
                logger.info(f"Loaded {len(self.workspaces)} workspaces")
        except Exception as e:
            logger.error(f"Failed to load workspaces: {e}")

    def _load_sessions(self):
        """Load session data."""
        try:
            if self.sessions_path.exists():
                with open(self.sessions_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for session_data in data.get('sessions', []):
                        session = CollaborationSession(**session_data)
                        self.session_history.append(session)
                logger.info(f"Loaded {len(self.session_history)} sessions")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")

    def _create_default_workspace(self):
        """Create a default collaborative workspace."""
        workspace = {
            "workspace_id": "default_collab_001",
            "name": "Production Optimization Workspace",
            "description": "Collaborative workspace for production optimization and troubleshooting",
            "created_by": "system",
            "created_at": time.time(),
            "participants": ["admin", "supervisor", "engineer"],
            "assets": [
                {
                    "asset_id": "production_dashboard",
                    "type": "dashboard",
                    "owner": "admin",
                    "permissions": {"view": ["all"], "edit": ["admin", "supervisor"]}
                },
                {
                    "asset_id": "cnc_twin_shared",
                    "type": "digital_twin",
                    "owner": "engineer",
                    "permissions": {"view": ["all"], "edit": ["engineer", "supervisor"]}
                }
            ],
            "tools": [
                "shared_whiteboard",
                "voice_chat",
                "screen_sharing",
                "task_manager",
                "version_control"
            ],
            "settings": {
                "max_participants": 10,
                "auto_save": True,
                "version_history": True,
                "real_time_sync": True
            }
        }

        self.workspaces[workspace["workspace_id"]] = workspace
        self._save_workspaces()

    def _save_workspaces(self):
        """Save workspaces."""
        try:
            data = {'workspaces': self.workspaces}
            with open(self.workspaces_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Workspaces saved successfully")
        except Exception as e:
            logger.error(f"Failed to save workspaces: {e}")

    def _save_sessions(self):
        """Save sessions."""
        try:
            data = {
                'sessions': [
                    {
                        'session_id': s.session_id,
                        'workspace_id': s.workspace_id,
                        'mode': s.mode.value,
                        'participants': [vars(p) for p in s.participants],
                        'shared_assets': [vars(a) for a in s.shared_assets],
                        'active_tasks': s.active_tasks,
                        'communications': s.communications,
                        'start_time': s.start_time,
                        'last_activity': s.last_activity
                    }
                    for s in self.session_history
                ]
            }
            with open(self.sessions_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Sessions saved successfully")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def create_workspace(self, workspace_config: Dict[str, Any], creator_id: str) -> str:
        """
        Create a new collaborative workspace.

        Args:
            workspace_config: Workspace configuration
            creator_id: Creator user ID

        Returns:
            Workspace ID
        """
        workspace_id = f"workspace_{creator_id}_{int(time.time())}"

        workspace = {
            "workspace_id": workspace_id,
            "name": workspace_config["name"],
            "description": workspace_config.get("description", ""),
            "created_by": creator_id,
            "created_at": time.time(),
            "participants": workspace_config.get("participants", [creator_id]),
            "assets": workspace_config.get("assets", []),
            "tools": workspace_config.get("tools", ["shared_whiteboard", "voice_chat"]),
            "settings": workspace_config.get("settings", {
                "max_participants": 10,
                "auto_save": True,
                "version_history": True,
                "real_time_sync": True
            })
        }

        self.workspaces[workspace_id] = workspace
        self._save_workspaces()

        logger.info(f"Created workspace {workspace_id}")
        return workspace_id

    def start_collaboration_session(self, workspace_id: str, initiator_id: str,
                                  mode: CollaborationMode = CollaborationMode.REAL_TIME) -> Dict[str, Any]:
        """
        Start a collaboration session.

        Args:
            workspace_id: Workspace identifier
            initiator_id: Session initiator
            mode: Collaboration mode

        Returns:
            Session configuration
        """
        if workspace_id not in self.workspaces:
            raise ValueError(f"Workspace {workspace_id} not found")

        workspace = self.workspaces[workspace_id]

        # Check permissions
        if initiator_id not in workspace["participants"]:
            raise PermissionError(f"User {initiator_id} not authorized for workspace {workspace_id}")

        session_id = f"session_{workspace_id}_{int(time.time())}"

        # Create participants
        participants = [
            WorkspaceParticipant(
                user_id=user_id,
                avatar_id=f"avatar_{user_id}",
                access_level=AccessLevel.ADMIN if user_id == workspace["created_by"] else AccessLevel.EDITOR,
                joined_at=time.time(),
                last_activity=time.time()
            )
            for user_id in workspace["participants"]
        ]

        # Create shared assets
        shared_assets = [
            SharedAsset(
                asset_id=asset["asset_id"],
                asset_type=asset["type"],
                owner_id=asset["owner"],
                current_version=1,
                collaborators=asset.get("permissions", {}).get("edit", [])
            )
            for asset in workspace["assets"]
        ]

        session = CollaborationSession(
            session_id=session_id,
            workspace_id=workspace_id,
            mode=mode,
            participants=participants,
            shared_assets=shared_assets,
            start_time=time.time(),
            last_activity=time.time()
        )

        self.active_sessions[session_id] = session

        logger.info(f"Started collaboration session {session_id}")

        return {
            'session_id': session_id,
            'workspace': workspace,
            'participants': [vars(p) for p in participants],
            'shared_assets': [vars(a) for a in shared_assets],
            'mode': mode.value,
            'tools_available': workspace["tools"]
        }

    def join_workspace_session(self, session_id: str, user_id: str,
                              avatar_id: str) -> Dict[str, Any]:
        """
        Join an existing collaboration session.

        Args:
            session_id: Session identifier
            user_id: User identifier
            avatar_id: Avatar identifier

        Returns:
            Join confirmation
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        workspace = self.workspaces[session.workspace_id]

        # Check if user is authorized
        if user_id not in workspace["participants"]:
            raise PermissionError(f"User {user_id} not authorized for this workspace")

        # Check participant limit
        if len(session.participants) >= workspace["settings"]["max_participants"]:
            raise ValueError("Session is full")

        # Add participant
        participant = WorkspaceParticipant(
            user_id=user_id,
            avatar_id=avatar_id,
            access_level=AccessLevel.EDITOR,  # Default access
            joined_at=time.time(),
            last_activity=time.time()
        )

        session.participants.append(participant)
        session.last_activity = time.time()

        logger.info(f"User {user_id} joined session {session_id}")

        return {
            'status': 'joined',
            'participant': vars(participant),
            'session_state': self._get_session_state(session_id)
        }

    def _get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get current state of a session."""
        session = self.active_sessions[session_id]

        return {
            'participants': [vars(p) for p in session.participants],
            'active_tasks': session.active_tasks,
            'recent_communications': session.communications[-5:],  # Last 5 messages
            'asset_states': [
                {
                    'asset_id': a.asset_id,
                    'locked_by': a.lock_holder,
                    'version': a.current_version
                }
                for a in session.shared_assets
            ]
        }

    def share_asset(self, session_id: str, user_id: str, asset_id: str,
                   asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Share an asset in the collaborative session.

        Args:
            session_id: Session identifier
            user_id: User identifier
            asset_id: Asset identifier
            asset_data: Asset data

        Returns:
            Share confirmation
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]

        # Find or create shared asset
        shared_asset = next((a for a in session.shared_assets if a.asset_id == asset_id), None)

        if not shared_asset:
            shared_asset = SharedAsset(
                asset_id=asset_id,
                asset_type=asset_data.get("type", "unknown"),
                owner_id=user_id,
                current_version=1
            )
            session.shared_assets.append(shared_asset)

        # Update asset
        shared_asset.current_version += 1
        shared_asset.change_history.append({
            'version': shared_asset.current_version,
            'user_id': user_id,
            'timestamp': time.time(),
            'changes': asset_data.get('changes', {})
        })

        session.last_activity = time.time()

        # Notify other participants
        self._notify_participants(session, 'asset_updated', {
            'asset_id': asset_id,
            'updated_by': user_id,
            'version': shared_asset.current_version
        })

        return {
            'status': 'shared',
            'asset_id': asset_id,
            'version': shared_asset.current_version,
            'collaborators': shared_asset.collaborators
        }

    def lock_asset(self, session_id: str, user_id: str, asset_id: str) -> Dict[str, Any]:
        """
        Lock an asset for exclusive editing.

        Args:
            session_id: Session identifier
            user_id: User identifier
            asset_id: Asset identifier

        Returns:
            Lock confirmation
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        shared_asset = next((a for a in session.shared_assets if a.asset_id == asset_id), None)

        if not shared_asset:
            raise ValueError(f"Asset {asset_id} not found in session")

        if shared_asset.lock_holder and shared_asset.lock_holder != user_id:
            raise ValueError(f"Asset {asset_id} is locked by {shared_asset.lock_holder}")

        shared_asset.lock_holder = user_id
        shared_asset.lock_timestamp = time.time()

        session.last_activity = time.time()

        return {
            'status': 'locked',
            'asset_id': asset_id,
            'locked_by': user_id,
            'timestamp': shared_asset.lock_timestamp
        }

    def unlock_asset(self, session_id: str, user_id: str, asset_id: str) -> Dict[str, Any]:
        """
        Unlock an asset.

        Args:
            session_id: Session identifier
            user_id: User identifier
            asset_id: Asset identifier

        Returns:
            Unlock confirmation
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        shared_asset = next((a for a in session.shared_assets if a.asset_id == asset_id), None)

        if not shared_asset:
            raise ValueError(f"Asset {asset_id} not found in session")

        if shared_asset.lock_holder != user_id:
            raise PermissionError(f"Only {shared_asset.lock_holder} can unlock asset {asset_id}")

        shared_asset.lock_holder = None
        shared_asset.lock_timestamp = None

        session.last_activity = time.time()

        return {
            'status': 'unlocked',
            'asset_id': asset_id
        }

    def send_message(self, session_id: str, user_id: str, message: str,
                    message_type: str = "text", target_users: Optional[List[str]] = None) -> str:
        """
        Send a message in the collaborative session.

        Args:
            session_id: Session identifier
            user_id: User identifier
            message: Message content
            message_type: Type of message
            target_users: Target users (for private messages)

        Returns:
            Message ID
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]

        message_data = {
            'message_id': f"msg_{int(time.time())}_{user_id}",
            'user_id': user_id,
            'message': message,
            'type': message_type,
            'target_users': target_users,
            'timestamp': time.time()
        }

        session.communications.append(message_data)
        session.last_activity = time.time()

        # Update participant activity
        participant = next((p for p in session.participants if p.user_id == user_id), None)
        if participant:
            participant.last_activity = time.time()

        # Notify participants
        self._notify_participants(session, 'new_message', message_data)

        return message_data['message_id']

    def create_task(self, session_id: str, user_id: str, task_data: Dict[str, Any]) -> str:
        """
        Create a collaborative task.

        Args:
            session_id: Session identifier
            user_id: User identifier
            task_data: Task information

        Returns:
            Task ID
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]

        task_id = f"task_{int(time.time())}_{user_id}"

        task = {
            'task_id': task_id,
            'title': task_data['title'],
            'description': task_data.get('description', ''),
            'created_by': user_id,
            'assigned_to': task_data.get('assigned_to', []),
            'status': 'open',
            'priority': task_data.get('priority', 'medium'),
            'created_at': time.time(),
            'due_date': task_data.get('due_date'),
            'tags': task_data.get('tags', [])
        }

        session.active_tasks.append(task)
        session.last_activity = time.time()

        # Notify participants
        self._notify_participants(session, 'task_created', task)

        return task_id

    def update_task_status(self, session_id: str, user_id: str, task_id: str,
                          new_status: str) -> Dict[str, Any]:
        """
        Update task status.

        Args:
            session_id: Session identifier
            user_id: User identifier
            task_id: Task identifier
            new_status: New status

        Returns:
            Update confirmation
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        task = next((t for t in session.active_tasks if t['task_id'] == task_id), None)

        if not task:
            raise ValueError(f"Task {task_id} not found")

        old_status = task['status']
        task['status'] = new_status
        task['updated_at'] = time.time()
        task['updated_by'] = user_id

        session.last_activity = time.time()

        # Notify participants
        self._notify_participants(session, 'task_updated', {
            'task_id': task_id,
            'old_status': old_status,
            'new_status': new_status,
            'updated_by': user_id
        })

        return {
            'status': 'updated',
            'task_id': task_id,
            'new_status': new_status
        }

    def _notify_participants(self, session: CollaborationSession, event_type: str,
                           event_data: Dict[str, Any]):
        """Notify session participants of events."""
        # In a real implementation, this would send WebSocket messages or other notifications
        logger.info(f"Notifying {len(session.participants)} participants of {event_type}: {event_data}")

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a collaboration session.

        Args:
            session_id: Session identifier

        Returns:
            Session summary
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]

        end_time = time.time()
        duration = end_time - session.start_time

        summary = {
            'session_id': session_id,
            'workspace_id': session.workspace_id,
            'duration_seconds': duration,
            'participants_count': len(session.participants),
            'tasks_completed': len([t for t in session.active_tasks if t['status'] == 'completed']),
            'messages_sent': len(session.communications),
            'assets_shared': len(session.shared_assets),
            'end_time': datetime.fromtimestamp(end_time).isoformat()
        }

        # Move to history
        self.session_history.append(session)

        # Clean up
        del self.active_sessions[session_id]

        # Save sessions
        self._save_sessions()

        logger.info(f"Ended collaboration session {session_id}")

        return {
            'status': 'ended',
            'summary': summary
        }

    def get_workspace_stats(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get statistics for a workspace.

        Args:
            workspace_id: Workspace identifier

        Returns:
            Workspace statistics
        """
        if workspace_id not in self.workspaces:
            raise ValueError(f"Workspace {workspace_id} not found")

        workspace = self.workspaces[workspace_id]

        # Get session history for this workspace
        workspace_sessions = [s for s in self.session_history if s.workspace_id == workspace_id]

        total_sessions = len(workspace_sessions)
        total_participants = len(set(
            p.user_id for s in workspace_sessions for p in s.participants
        ))

        total_duration = sum(
            s.last_activity - s.start_time for s in workspace_sessions
        )

        return {
            'workspace_id': workspace_id,
            'name': workspace['name'],
            'total_sessions': total_sessions,
            'unique_participants': total_participants,
            'total_collaboration_time_hours': total_duration / 3600,
            'average_session_duration_minutes': (total_duration / max(1, total_sessions)) / 60,
            'assets_count': len(workspace['assets']),
            'created_at': workspace['created_at']
        }

    def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get workspaces accessible to a user.

        Args:
            user_id: User identifier

        Returns:
            List of accessible workspaces
        """
        accessible_workspaces = []

        for workspace in self.workspaces.values():
            if user_id in workspace["participants"]:
                accessible_workspaces.append({
                    'workspace_id': workspace['workspace_id'],
                    'name': workspace['name'],
                    'description': workspace['description'],
                    'role': 'admin' if workspace['created_by'] == user_id else 'participant',
                    'participants_count': len(workspace['participants']),
                    'assets_count': len(workspace['assets'])
                })

        return accessible_workspaces


# Example usage
if __name__ == "__main__":
    # Initialize collaborative workspace
    collab_workspace = CollaborativeWorkspace()

    # Create a new workspace
    workspace_config = {
        "name": "Quality Control Collaboration",
        "description": "Workspace for quality control team collaboration",
        "participants": ["qc_lead", "engineer1", "technician1"],
        "assets": [
            {
                "asset_id": "quality_dashboard",
                "type": "dashboard",
                "owner": "qc_lead",
                "permissions": {"view": ["all"], "edit": ["qc_lead"]}
            }
        ],
        "tools": ["shared_whiteboard", "voice_chat", "task_manager"]
    }

    workspace_id = collab_workspace.create_workspace(workspace_config, "qc_lead")
    print(f"Created workspace: {workspace_id}")

    # Start collaboration session
    session = collab_workspace.start_collaboration_session(
        workspace_id, "qc_lead", CollaborationMode.REAL_TIME
    )
    print(f"Started session: {session['session_id']}")

    # Join session
    join_result = collab_workspace.join_workspace_session(
        session['session_id'], "engineer1", "avatar_engineer1"
    )
    print("User joined session:", join_result['status'])

    # Send message
    msg_id = collab_workspace.send_message(
        session['session_id'], "qc_lead", "Let's review the quality metrics"
    )
    print(f"Sent message: {msg_id}")

    # Create task
    task_id = collab_workspace.create_task(
        session['session_id'], "qc_lead",
        {
            "title": "Review quality control procedures",
            "description": "Review and update QC procedures based on recent findings",
            "assigned_to": ["engineer1"],
            "priority": "high"
        }
    )
    print(f"Created task: {task_id}")

    # Share asset
    share_result = collab_workspace.share_asset(
        session['session_id'], "qc_lead", "quality_dashboard",
        {"type": "dashboard", "changes": {"add_metric": "defect_rate"}}
    )
    print("Asset shared:", share_result['status'])

    # End session
    summary = collab_workspace.end_session(session['session_id'])
    print("Session ended:", summary['summary']['duration_seconds'], "seconds")

    # Get workspace stats
    stats = collab_workspace.get_workspace_stats(workspace_id)
    print(f"Workspace stats: {stats['total_sessions']} sessions, {stats['unique_participants']} participants")