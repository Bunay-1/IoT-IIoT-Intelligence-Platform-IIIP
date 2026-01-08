"""
Academic Collaborations Module for IoT Intelligence Platform.

This module manages academic partnerships, joint research projects,
knowledge transfer systems, and publication tracking for collaborative
research initiatives.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio

from config import settings
from utils.logging_config import get_logger

logger = get_logger(__name__)


class AcademicCollaborationError(Exception):
    """Base exception for academic collaboration errors."""
    pass


class ValidationError(AcademicCollaborationError):
    """Raised when collaboration data is invalid."""
    pass


class ProcessingError(AcademicCollaborationError):
    """Raised when collaboration processing fails."""
    pass


class AcademicCollaborations:
    """
    Academic Collaborations Management System.

    Handles research partnerships, joint projects, knowledge transfer,
    and publication tracking for academic-industry collaborations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the academic collaborations module with state management.
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # State management
        self.partners: Dict[str, Dict[str, Any]] = {}
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.publications: Dict[str, Dict[str, Any]] = {}
        self.events: Dict[str, Dict[str, Any]] = {}

        # Collaboration settings
        self.max_partners = self.config.get('max_partners', 50)
        self.max_projects = self.config.get('max_projects', 100)
        self._validate_config()
        self.logger.info("Academic Collaborations module initialized with state management.")

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if 'max_partners' in self.config and self.config['max_partners'] <= 0:
            raise ValidationError("max_partners must be a positive integer")

    def research_partnership_brokerage(self, institution_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Establish a new academic research partnership and add it to the state.
        """
        try:
            if institution_id in self.partners:
                raise ValidationError(f"Partnership with {institution_id} already exists.")
            if len(self.partners) >= self.max_partners:
                raise ProcessingError("Maximum number of partners reached.")

            self.logger.info(f"Establishing new partnership with {institution_id}")
            self.partners[institution_id] = {
                "id": institution_id,
                "details": details,
                "status": "active",
                "join_date": datetime.utcnow().isoformat()
            }
            return {"status": "success", "partner": self.partners[institution_id]}

        except Exception as e:
            self.logger.error(f"Failed to establish partnership: {e}")
            raise ProcessingError(str(e))

    def joint_research_projects(self, project_id: str, project_details: Dict[str, Any], partner_ids: List[str]) -> Dict[str, Any]:
        """
        Create and manage a joint research project with existing partners.
        """
        try:
            if project_id in self.projects:
                raise ValidationError(f"Project {project_id} already exists.")
            for pid in partner_ids:
                if pid not in self.partners:
                    raise ValidationError(f"Partner {pid} not found.")

            self.logger.info(f"Creating new joint research project: {project_id}")
            self.projects[project_id] = {
                "id": project_id,
                "details": project_details,
                "partners": partner_ids,
                "status": "ongoing",
                "start_date": datetime.utcnow().isoformat(),
                "budget": {"allocated": 0, "spent": 0}
            }
            return {"status": "success", "project": self.projects[project_id]}

        except Exception as e:
            self.logger.error(f"Failed to create project: {e}")
            raise ProcessingError(str(e))

    def knowledge_transfer_system(self, project_id: str, knowledge_assets: List[str], target_applications: List[str]) -> Dict[str, Any]:
        """
        Simulate the transfer of knowledge assets from a project to industry applications.
        """
        if project_id not in self.projects:
            raise ValidationError(f"Project {project_id} not found.")

        self.logger.info(f"Transferring {len(knowledge_assets)} assets from project {project_id} to {len(target_applications)} applications.")

        # Link the transfer to the project state
        if 'knowledge_transfers' not in self.projects[project_id]:
            self.projects[project_id]['knowledge_transfers'] = []

        transfer_record = {
            "transfer_date": datetime.utcnow().isoformat(),
            "assets": knowledge_assets,
            "targets": target_applications,
            "status": "completed"
        }
        self.projects[project_id]['knowledge_transfers'].append(transfer_record)

        return {"status": "success", "transfer_record": transfer_record}

    def manage_project_budget(self, project_id: str, allocated_budget: float, expenditure: float = 0) -> Dict[str, Any]:
        """
        Manage the budget for a specific research project.
        """
        if project_id not in self.projects:
            raise ValidationError(f"Project {project_id} not found.")

        self.logger.info(f"Updating budget for project {project_id}")
        self.projects[project_id]['budget']['allocated'] = allocated_budget
        self.projects[project_id]['budget']['spent'] += expenditure
        return {"status": "success", "budget": self.projects[project_id]['budget']}

    def publication_tracking_engine(self, pub_id: str, details: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """
        Track a new academic publication and link it to a project.
        """
        if project_id not in self.projects:
            raise ValidationError(f"Project {project_id} not found.")

        self.logger.info(f"Adding new publication {pub_id} for project {project_id}")
        self.publications[pub_id] = {
            "id": pub_id,
            "details": details,
            "project_id": project_id,
            "publication_date": datetime.utcnow().isoformat()
        }
        return {"status": "success", "publication": self.publications[pub_id]}

    def organize_collaborative_event(self, event_id: str, details: Dict[str, Any], partner_ids: List[str]) -> Dict[str, Any]:
        """
        Organize a collaborative event like a workshop or conference.
        """
        for pid in partner_ids:
            if pid not in self.partners:
                raise ValidationError(f"Partner {pid} not found.")

        self.logger.info(f"Organizing new event: {event_id}")
        self.events[event_id] = {
            "id": event_id,
            "details": details,
            "participating_partners": partner_ids,
            "event_date": details.get("date"),
            "status": "planned"
        }
        return {"status": "success", "event": self.events[event_id]}

    def generate_collaboration_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of all collaboration activities.
        """
        return {
            "report_date": datetime.utcnow().isoformat(),
            "summary": {
                "total_partners": len(self.partners),
                "total_projects": len(self.projects),
                "total_publications": len(self.publications),
                "total_events": len(self.events)
            },
            "partners": list(self.partners.values()),
            "projects": list(self.projects.values())
        }

    async def async_collaboration_monitoring(self, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously monitor collaboration activities from the current state.
        """
        try:
            self.logger.info("Starting async collaboration monitoring from state")
            await asyncio.sleep(0.1)

            # Calculate metrics from the current state
            active_projects = [p for p in self.projects.values() if p['status'] == 'ongoing']
            recent_pubs = [pub for pub in self.publications.values() if (datetime.utcnow() - datetime.fromisoformat(pub['publication_date'])).days <= 30]

            result = {
                "monitoring_status": "active",
                "active_partnerships": len(self.partners),
                "ongoing_projects": len(active_projects),
                "publications_this_month": len(recent_pubs),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.logger.info("Async collaboration monitoring completed.")
            return result

        except Exception as e:
            self.logger.error(f"Async collaboration monitoring failed: {e}")
            raise ProcessingError(f"Failed to monitor collaborations: {e}") from e


# Backward compatibility functions
def research_partnership_brokerage(researchers: List[Dict[str, Any]], institutions: List[str]) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    collab = AcademicCollaborations()
    return collab.research_partnership_brokerage(researchers, institutions)


def joint_research_projects(projects: List[Dict[str, Any]], collaborators: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    collab = AcademicCollaborations()
    return collab.joint_research_projects(projects, collaborators)


def knowledge_transfer_system(knowledge: Dict[str, Any], applications: List[str]) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    collab = AcademicCollaborations()
    return collab.knowledge_transfer_system(knowledge, applications)


def publication_tracking_engine(publications: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    collab = AcademicCollaborations()
    return collab.publication_tracking_engine(publications, metrics)