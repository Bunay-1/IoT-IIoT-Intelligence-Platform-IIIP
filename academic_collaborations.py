"""
Academic Collaborations Module for IoT Intelligence Platform.

This module manages academic partnerships, joint research projects,
knowledge transfer systems, and publication tracking for collaborative
research initiatives.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import asyncio

from config import settings
from utils.logging_config import get_logger


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
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        # State management
        self.partners: Dict[str, Dict[str, Any]] = {}
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.publications: Dict[str, Dict[str, Any]] = {}
        self.events: Dict[str, Dict[str, Any]] = {}
        self.grants: Dict[str, Dict[str, Any]] = {}
        self.intellectual_property: Dict[str, Dict[str, Any]] = {}
        self.researchers: Dict[str, Dict[str, Any]] = {}

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
                "join_date": datetime.now(timezone.utc).isoformat()
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
                "start_date": datetime.now(timezone.utc).isoformat(),
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
            "transfer_date": datetime.now(timezone.utc).isoformat(),
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
            "publication_date": datetime.now(timezone.utc).isoformat()
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
            "report_date": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_partners": len(self.partners),
                "total_projects": len(self.projects),
                "total_publications": len(self.publications),
                "total_events": len(self.events)
            },
            "partners": list(self.partners.values()),
            "projects": list(self.projects.values())
        }

    def track_grant_application(self, grant_id: str, details: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """
        Track a grant application for a research project.
        """
        if project_id not in self.projects:
            raise ValidationError(f"Project {project_id} not found.")

        self.logger.info(f"Tracking new grant application {grant_id} for project {project_id}")
        self.grants[grant_id] = {
            "id": grant_id,
            "details": details,
            "project_id": project_id,
            "status": "submitted",
            "submission_date": datetime.now(timezone.utc).isoformat()
        }
        return {"status": "success", "grant": self.grants[grant_id]}

    def manage_intellectual_property(self, ip_id: str, details: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """
        Manage intellectual property (e.g., patents, licenses) for a project.
        """
        if project_id not in self.projects:
            raise ValidationError(f"Project {project_id} not found.")

        self.logger.info(f"Registering new IP {ip_id} for project {project_id}")
        self.intellectual_property[ip_id] = {
            "id": ip_id,
            "details": details,
            "project_id": project_id,
            "status": "pending",
            "filing_date": datetime.now(timezone.utc).isoformat()
        }
        return {"status": "success", "ip": self.intellectual_property[ip_id]}

    def manage_researcher_profile(self, researcher_id: str, details: Dict[str, Any], institution_id: str) -> Dict[str, Any]:
        """
        Create or update a researcher's profile.
        """
        if institution_id not in self.partners:
            raise ValidationError(f"Institution {institution_id} not found.")

        self.logger.info(f"Managing profile for researcher {researcher_id}")
        self.researchers[researcher_id] = {
            "id": researcher_id,
            "details": details,
            "institution_id": institution_id,
            "projects": [],
            "publications": []
        }
        return {"status": "success", "researcher": self.researchers[researcher_id]}

    def assess_partnership_health(self, partner_id: str) -> Dict[str, Any]:
        """
        Assess the health of a partnership based on collaboration metrics.
        """
        if partner_id not in self.partners:
            raise ValidationError(f"Partner {partner_id} not found.")

        projects = [p for p in self.projects.values() if partner_id in p['partners']]
        project_ids = [p['id'] for p in projects]
        publications = [pub for pub in self.publications.values() if pub['project_id'] in project_ids]

        score = len(projects) * 5 + len(publications) * 10

        health_status = "Excellent" if score > 50 else "Good" if score > 20 else "Needs Attention"

        return {
            "partner_id": partner_id,
            "health_status": health_status,
            "score": score,
            "metrics": {
                "project_count": len(projects),
                "publication_count": len(publications)
            }
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
            now = datetime.now(timezone.utc)
            recent_pubs = [pub for pub in self.publications.values() if (now - datetime.fromisoformat(pub['publication_date'])).days <= 30]

            result = {
                "monitoring_status": "active",
                "active_partnerships": len(self.partners),
                "ongoing_projects": len(active_projects),
                "publications_this_month": len(recent_pubs),
                "timestamp": now.isoformat()
            }
            self.logger.info("Async collaboration monitoring completed.")
            return result

        except Exception as e:
            self.logger.error(f"Async collaboration monitoring failed: {e}")
            raise ProcessingError(f"Failed to monitor collaborations: {e}") from e


# Global instance for state management
collaboration_manager = AcademicCollaborations()

if __name__ == "__main__":
    async def main():
        print("--- Academic Collaborations Module Demonstration ---")

        # 1. Establish Partnerships
        print("\n--- Establishing Partnerships ---")
        collaboration_manager.research_partnership_brokerage("uni_a", {"name": "University A", "domain": "AI"})
        collaboration_manager.research_partnership_brokerage("inst_b", {"name": "Institute B", "domain": "Robotics"})
        print(f"Partners: {collaboration_manager.partners}")

        # 2. Create Joint Research Projects
        print("\n--- Creating Joint Projects ---")
        project_details = {"title": "AI in Autonomous Robotics", "field": "AI/Robotics"}
        collaboration_manager.joint_research_projects("proj_001", project_details, ["uni_a", "inst_b"])
        print(f"Projects: {collaboration_manager.projects}")

        # 3. Manage Project Budget
        print("\n--- Managing Project Budget ---")
        collaboration_manager.manage_project_budget("proj_001", 100000, 15000)
        print(f"Project Budget: {collaboration_manager.projects['proj_001']['budget']}")

        # 4. Track Publications
        print("\n--- Tracking Publications ---")
        pub_details = {"title": "A paper on AI Robot vision", "journal": "Journal of AI"}
        collaboration_manager.publication_tracking_engine("pub_01", pub_details, "proj_001")
        print(f"Publications: {collaboration_manager.publications}")

        # 5. Knowledge Transfer
        print("\n--- Knowledge Transfer System ---")
        assets = ["Algorithm A", "Dataset B"]
        targets = ["Application X", "Product Y"]
        collaboration_manager.knowledge_transfer_system("proj_001", assets, targets)
        print(f"Knowledge Transfers: {collaboration_manager.projects['proj_001']['knowledge_transfers']}")

        # 6. Track Grant Application
        print("\n--- Tracking Grant Applications ---")
        grant_details = {"funder": "National Science Foundation", "amount": 500000}
        collaboration_manager.track_grant_application("grant_01", grant_details, "proj_001")
        print(f"Grants: {collaboration_manager.grants}")

        # 7. Manage Intellectual Property
        print("\n--- Managing Intellectual Property ---")
        ip_details = {"type": "Patent", "title": "Novelty in AI Robotics"}
        collaboration_manager.manage_intellectual_property("ip_01", ip_details, "proj_001")
        print(f"IP: {collaboration_manager.intellectual_property}")

        # 8. Manage Researcher Profiles
        print("\n--- Managing Researcher Profiles ---")
        researcher_details = {"name": "Dr. Smith", "expertise": "Computer Vision"}
        collaboration_manager.manage_researcher_profile("r_001", researcher_details, "uni_a")
        print(f"Researchers: {collaboration_manager.researchers}")

        # 9. Assess Partnership Health
        print("\n--- Assessing Partnership Health ---")
        health_report = collaboration_manager.assess_partnership_health("uni_a")
        print(f"Health Report for uni_a: {health_report}")

        # 10. Generate Final Report
        print("\n--- Generating Collaboration Report ---")
        report = collaboration_manager.generate_collaboration_report()
        print(f"Total Partners: {report['summary']['total_partners']}")
        print(f"Total Projects: {report['summary']['total_projects']}")

        # 11. Async Monitoring
        print("\n--- Async Collaboration Monitoring ---")
        monitoring_result = await collaboration_manager.async_collaboration_monitoring({})
        print(monitoring_result)

    asyncio.run(main())
