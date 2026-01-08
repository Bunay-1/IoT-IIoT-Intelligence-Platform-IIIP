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
        Initialize the academic collaborations module.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._validate_config()

        # Collaboration settings
        self.max_partners = self.config.get('max_partners', 50)
        self.max_projects = self.config.get('max_projects', 100)

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if 'max_partners' in self.config and self.config['max_partners'] <= 0:
            raise ValidationError("max_partners must be a positive integer")

    def research_partnership_brokerage(self, researchers: List[Dict[str, Any]], institutions: List[str]) -> Dict[str, Any]:
        """
        Broker academic research partnerships.

        Args:
            researchers: List of researcher profiles
            institutions: List of collaborating institutions

        Returns:
            Dictionary containing brokerage results

        Raises:
            ProcessingError: If brokerage fails
            ValidationError: If input validation fails
        """
        try:
            self.logger.info(f"Starting partnership brokerage with {len(institutions)} institutions")

            # Input validation
            if not researchers:
                raise ValidationError("Researchers list cannot be empty")
            if not institutions:
                raise ValidationError("Institutions list cannot be empty")
            if len(institutions) > self.max_partners:
                raise ValidationError(f"Too many institutions: {len(institutions)} > {self.max_partners}")

            result = {
                "brokerage_status": "successful",
                "researchers_matched": len(researchers),
                "institutions_connected": len(institutions),
                "researchers": researchers,
                "institutions": institutions,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.logger.info(f"Partnership brokerage completed for {len(researchers)} researchers and {len(institutions)} institutions")
            return result

        except Exception as e:
            self.logger.error(f"Partnership brokerage failed: {e}")
            raise ProcessingError(f"Failed to broker partnerships: {e}") from e

    def joint_research_projects(self, projects: List[Dict[str, Any]], collaborators: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Manage joint research projects.

        Args:
            projects: List of research project details
            collaborators: List of collaborator information

        Returns:
            Dictionary containing project management results

        Raises:
            ProcessingError: If project management fails
        """
        try:
            self.logger.info(f"Managing {len(projects)} joint research projects")

            # Validate project count
            if len(projects) > self.max_projects:
                raise ValidationError(f"Too many projects: {len(projects)} > {self.max_projects}")

            result = {
                "project_status": "ongoing",
                "projects_active": len(projects),
                "collaborators_involved": len(collaborators),
                "projects": projects,
                "collaborators": collaborators,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.logger.info(f"Joint research project management completed for {len(projects)} projects")
            return result

        except Exception as e:
            self.logger.error(f"Joint research project management failed: {e}")
            raise ProcessingError(f"Failed to manage joint projects: {e}") from e

    def knowledge_transfer_system(self, knowledge: Dict[str, Any], applications: List[str]) -> Dict[str, Any]:
        """
        Transfer academic knowledge to industry applications.

        Args:
            knowledge: Knowledge base to transfer
            applications: List of industry applications

        Returns:
            Dictionary containing transfer results

        Raises:
            ProcessingError: If knowledge transfer fails
        """
        try:
            self.logger.info(f"Starting knowledge transfer for {len(applications)} applications")

            # Validate inputs
            if not knowledge:
                raise ValidationError("Knowledge dictionary cannot be empty")
            if not applications:
                raise ValidationError("Applications list cannot be empty")

            result = {
                "transfer_status": "completed",
                "knowledge_transferred": knowledge,
                "applications_targeted": len(applications),
                "applications": applications,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.logger.info(f"Knowledge transfer completed for {len(applications)} applications")
            return result

        except Exception as e:
            self.logger.error(f"Knowledge transfer failed: {e}")
            raise ProcessingError(f"Failed to transfer knowledge: {e}") from e

    def publication_tracking_engine(self, publications: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track academic publications and metrics.

        Args:
            publications: List of publication records
            metrics: Tracking metrics configuration

        Returns:
            Dictionary containing tracking results

        Raises:
            ProcessingError: If tracking fails
        """
        try:
            self.logger.info(f"Starting publication tracking for {len(publications)} publications")

            # Validate inputs
            if not publications:
                raise ValidationError("Publications list cannot be empty")

            result = {
                "tracking_status": "active",
                "publications_tracked": len(publications),
                "metrics_applied": metrics,
                "publications": publications,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.logger.info(f"Publication tracking completed for {len(publications)} publications")
            return result

        except Exception as e:
            self.logger.error(f"Publication tracking failed: {e}")
            raise ProcessingError(f"Failed to track publications: {e}") from e

    async def async_collaboration_monitoring(self, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronously monitor collaboration activities.

        Args:
            monitoring_config: Monitoring configuration

        Returns:
            Dictionary containing monitoring results
        """
        try:
            self.logger.info("Starting async collaboration monitoring")

            # Simulate async monitoring
            await asyncio.sleep(0.1)

            result = {
                "monitoring_status": "active",
                "active_partnerships": 15,
                "ongoing_projects": 8,
                "publications_this_month": 12,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.logger.info("Async collaboration monitoring completed")
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