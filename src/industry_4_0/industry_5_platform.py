"""
Industry 5.0 Platform Module for IoT IIoT Intelligence Platform

This module implements Industry 5.0 features focusing on human-centric manufacturing,
advanced automation, and seamless human-machine collaboration.
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

class CollaborationLevel(Enum):
    """Levels of human-machine collaboration."""
    ASSISTED = "assisted"  # Human leads, machine assists
    COLLABORATIVE = "collaborative"  # Equal partnership
    DELEGATED = "delegated"  # Machine handles routine, human oversees

class DecisionAuthority(Enum):
    """Decision authority levels."""
    HUMAN_ONLY = "human_only"
    HUMAN_IN_LOOP = "human_in_loop"
    MACHINE_SUGGESTED = "machine_suggested"
    MACHINE_AUTONOMOUS = "machine_autonomous"

@dataclass
class HumanOperator:
    """Represents a human operator in the Industry 5.0 ecosystem."""
    operator_id: str
    name: str
    role: str
    skills: List[str]
    experience_level: str
    current_workload: float  # 0-1
    collaboration_preference: CollaborationLevel
    decision_authority: DecisionAuthority
    active_sessions: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AutonomousAgent:
    """Represents an autonomous AI/agent in the system."""
    agent_id: str
    agent_type: str  # 'optimization', 'monitoring', 'maintenance', 'quality'
    capabilities: List[str]
    authority_level: DecisionAuthority
    collaboration_mode: CollaborationLevel
    active_tasks: List[Dict] = field(default_factory=list)
    performance_history: List[Dict] = field(default_factory=dict)

@dataclass
class HumanMachineTeam:
    """Represents a human-machine collaboration team."""
    team_id: str
    name: str
    human_members: List[str]
    machine_agents: List[str]
    collaboration_level: CollaborationLevel
    active_projects: List[Dict] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: float

class Industry5Platform:
    """
    Industry 5.0 Platform for human-centric manufacturing and advanced automation.
    Integrates human operators, autonomous agents, and collaborative workflows.
    """

    def __init__(self, config_path: str = "data/industry_5_config.json"):
        """
        Initialize Industry 5.0 platform.

        Args:
            config_path: Path to platform configuration
        """
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Core components
        self.human_operators: Dict[str, HumanOperator] = {}
        self.autonomous_agents: Dict[str, AutonomousAgent] = {}
        self.collaboration_teams: Dict[str, HumanMachineTeam] = {}

        # Active collaborations
        self.active_collaborations: Dict[str, Dict] = {}
        self.decision_queue: List[Dict] = []

        # Integration with other modules
        self._initialize_integrations()

        # Load configuration
        self._load_config()

        # Initialize default setup if needed
        if not self.human_operators:
            self._create_default_setup()

    def _initialize_integrations(self):
        """Initialize integrations with other platform modules."""
        try:
            # Import and initialize key modules
            from quantum_integration import QuantumOptimizer
            from ar_vr_maintenance_guide import ARVRMaintenanceGuide
            from src.gui.vr_training_simulator import VRTrainingSimulator
            from src.gui.mixed_reality_dashboard import MixedRealityDashboard
            from src.digital_twin_engine import DigitalTwinEngine
            from src.metaverse_integration import MetaverseIntegration
            from src.collaborative_workspace import CollaborativeWorkspace

            self.quantum_optimizer = QuantumOptimizer(platform="simulator")
            self.ar_guide = ARVRMaintenanceGuide()
            self.vr_simulator = VRTrainingSimulator()
            self.mr_dashboard = MixedRealityDashboard()
            self.digital_twin_engine = DigitalTwinEngine()
            self.metaverse = MetaverseIntegration()
            self.collab_workspace = CollaborativeWorkspace()

            logger.info("Industry 5.0 integrations initialized")
        except ImportError as e:
            logger.warning(f"Some integrations not available: {e}")

    def _load_config(self):
        """Load platform configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self._apply_config(config)
                logger.info("Industry 5.0 configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def _apply_config(self, config: Dict[str, Any]):
        """Apply configuration settings."""
        # Load operators
        for op_data in config.get('operators', []):
            operator = HumanOperator(**op_data)
            self.human_operators[operator.operator_id] = operator

        # Load agents
        for agent_data in config.get('agents', []):
            agent = AutonomousAgent(**agent_data)
            self.autonomous_agents[agent.agent_id] = agent

        # Load teams
        for team_data in config.get('teams', []):
            team = HumanMachineTeam(**team_data)
            self.collaboration_teams[team.team_id] = team

    def _create_default_setup(self):
        """Create default Industry 5.0 setup."""
        # Create sample operators
        operators = [
            HumanOperator(
                operator_id="operator_001",
                name="Alex Johnson",
                role="Production Supervisor",
                skills=["process_optimization", "quality_control", "team_leadership"],
                experience_level="expert",
                current_workload=0.7,
                collaboration_preference=CollaborationLevel.COLLABORATIVE,
                decision_authority=DecisionAuthority.HUMAN_IN_LOOP
            ),
            HumanOperator(
                operator_id="operator_002",
                name="Maria Garcia",
                role="Maintenance Technician",
                skills=["mechanical_repair", "predictive_maintenance", "ar_vr_usage"],
                experience_level="advanced",
                current_workload=0.5,
                collaboration_preference=CollaborationLevel.ASSISTED,
                decision_authority=DecisionAuthority.MACHINE_SUGGESTED
            )
        ]

        for op in operators:
            self.human_operators[op.operator_id] = op

        # Create autonomous agents
        agents = [
            AutonomousAgent(
                agent_id="agent_optimization_001",
                agent_type="optimization",
                capabilities=["process_optimization", "resource_allocation", "scheduling"],
                authority_level=DecisionAuthority.MACHINE_SUGGESTED,
                collaboration_mode=CollaborationLevel.COLLABORATIVE
            ),
            AutonomousAgent(
                agent_id="agent_monitoring_001",
                agent_type="monitoring",
                capabilities=["real_time_monitoring", "anomaly_detection", "predictive_alerts"],
                authority_level=DecisionAuthority.MACHINE_AUTONOMOUS,
                collaboration_mode=CollaborationLevel.DELEGATED
            ),
            AutonomousAgent(
                agent_id="agent_maintenance_001",
                agent_type="maintenance",
                capabilities=["predictive_maintenance", "work_order_generation", "spare_parts_optimization"],
                authority_level=DecisionAuthority.HUMAN_IN_LOOP,
                collaboration_mode=CollaborationLevel.ASSISTED
            )
        ]

        for agent in agents:
            self.autonomous_agents[agent.agent_id] = agent

        # Create collaboration team
        team = HumanMachineTeam(
            team_id="team_production_001",
            name="Smart Production Team",
            human_members=["operator_001", "operator_002"],
            machine_agents=["agent_optimization_001", "agent_monitoring_001", "agent_maintenance_001"],
            collaboration_level=CollaborationLevel.COLLABORATIVE,
            created_at=time.time()
        )

        self.collaboration_teams[team.team_id] = team

        self._save_config()

    def _save_config(self):
        """Save current configuration."""
        try:
            config = {
                'operators': [vars(op) for op in self.human_operators.values()],
                'agents': [vars(agent) for agent in self.autonomous_agents.values()],
                'teams': [vars(team) for team in self.collaboration_teams.values()]
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info("Industry 5.0 configuration saved")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    async def initiate_human_machine_collaboration(self, team_id: str,
                                                 project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate a human-machine collaboration project.

        Args:
            team_id: Team identifier
            project_config: Project configuration

        Returns:
            Collaboration session details
        """
        if team_id not in self.collaboration_teams:
            raise ValueError(f"Team {team_id} not found")

        team = self.collaboration_teams[team_id]

        collaboration_id = f"collab_{team_id}_{int(time.time())}"

        # Create collaboration session
        collaboration = {
            'collaboration_id': collaboration_id,
            'team_id': team_id,
            'project': project_config,
            'start_time': time.time(),
            'status': 'active',
            'human_contributions': [],
            'machine_contributions': [],
            'decision_log': [],
            'performance_metrics': {
                'human_satisfaction': 0,
                'machine_efficiency': 0,
                'collaboration_quality': 0,
                'outcome_quality': 0
            }
        }

        self.active_collaborations[collaboration_id] = collaboration

        # Initialize collaborative workspace
        workspace_id = await self._setup_collaborative_workspace(team, project_config)

        # Start autonomous agents
        await self._activate_team_agents(team, collaboration_id)

        # Notify human team members
        await self._notify_team_members(team, collaboration)

        collaboration['workspace_id'] = workspace_id

        logger.info(f"Initiated human-machine collaboration {collaboration_id}")

        return {
            'collaboration_id': collaboration_id,
            'team': vars(team),
            'workspace_id': workspace_id,
            'project': project_config,
            'status': 'active'
        }

    async def _setup_collaborative_workspace(self, team: HumanMachineTeam,
                                           project_config: Dict[str, Any]) -> str:
        """Set up collaborative workspace for the team."""
        workspace_config = {
            'name': f"Collaboration: {project_config['name']}",
            'description': project_config.get('description', ''),
            'participants': team.human_members,
            'assets': [
                {
                    'asset_id': f"project_dashboard_{team.team_id}",
                    'type': 'dashboard',
                    'owner': team.human_members[0],
                    'permissions': {'view': team.human_members, 'edit': team.human_members}
                }
            ],
            'tools': ['shared_whiteboard', 'voice_chat', 'task_manager', 'real_time_sync']
        }

        workspace_id = self.collab_workspace.create_workspace(workspace_config, team.human_members[0])

        # Start collaboration session
        session = self.collab_workspace.start_collaboration_session(
            workspace_id, team.human_members[0]
        )

        return workspace_id

    async def _activate_team_agents(self, team: HumanMachineTeam, collaboration_id: str):
        """Activate autonomous agents for the team."""
        for agent_id in team.machine_agents:
            if agent_id in self.autonomous_agents:
                agent = self.autonomous_agents[agent_id]

                # Initialize agent task
                agent_task = {
                    'collaboration_id': collaboration_id,
                    'start_time': time.time(),
                    'status': 'active',
                    'contributions': []
                }

                agent.active_tasks.append(agent_task)

                # Start agent processing based on type
                if agent.agent_type == 'optimization':
                    asyncio.create_task(self._run_optimization_agent(agent, collaboration_id))
                elif agent.agent_type == 'monitoring':
                    asyncio.create_task(self._run_monitoring_agent(agent, collaboration_id))
                elif agent.agent_type == 'maintenance':
                    asyncio.create_task(self._run_maintenance_agent(agent, collaboration_id))

    async def _notify_team_members(self, team: HumanMachineTeam, collaboration: Dict[str, Any]):
        """Notify human team members of new collaboration."""
        notification = {
            'type': 'new_collaboration',
            'collaboration_id': collaboration['collaboration_id'],
            'team_name': team.name,
            'project': collaboration['project'],
            'timestamp': time.time()
        }

        # In a real implementation, this would send notifications via various channels
        logger.info(f"Notified team members: {notification}")

    async def _run_optimization_agent(self, agent: AutonomousAgent, collaboration_id: str):
        """Run optimization agent tasks."""
        try:
            while collaboration_id in self.active_collaborations:
                collaboration = self.active_collaborations[collaboration_id]

                # Generate optimization suggestions
                suggestions = await self._generate_optimization_suggestions(collaboration)

                if suggestions:
                    # Add to decision queue for human review
                    decision = {
                        'type': 'optimization_suggestion',
                        'agent_id': agent.agent_id,
                        'collaboration_id': collaboration_id,
                        'suggestions': suggestions,
                        'timestamp': time.time(),
                        'requires_approval': True
                    }

                    self.decision_queue.append(decision)

                    # Record contribution
                    agent.active_tasks[-1]['contributions'].append({
                        'type': 'optimization_suggestion',
                        'timestamp': time.time(),
                        'details': suggestions
                    })

                await asyncio.sleep(300)  # Check every 5 minutes

        except Exception as e:
            logger.error(f"Optimization agent error: {e}")

    async def _run_monitoring_agent(self, agent: AutonomousAgent, collaboration_id: str):
        """Run monitoring agent tasks."""
        try:
            while collaboration_id in self.active_collaborations:
                # Monitor system performance and generate alerts
                alerts = await self._generate_system_alerts()

                if alerts:
                    for alert in alerts:
                        decision = {
                            'type': 'system_alert',
                            'agent_id': agent.agent_id,
                            'collaboration_id': collaboration_id,
                            'alert': alert,
                            'timestamp': time.time(),
                            'requires_approval': alert.get('severity') == 'critical'
                        }

                        self.decision_queue.append(decision)

                        # Record contribution
                        agent.active_tasks[-1]['contributions'].append({
                            'type': 'alert_generated',
                            'timestamp': time.time(),
                            'details': alert
                        })

                await asyncio.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"Monitoring agent error: {e}")

    async def _run_maintenance_agent(self, agent: AutonomousAgent, collaboration_id: str):
        """Run maintenance agent tasks."""
        try:
            while collaboration_id in self.active_collaborations:
                # Analyze maintenance needs and generate recommendations
                maintenance_tasks = await self._analyze_maintenance_needs()

                if maintenance_tasks:
                    for task in maintenance_tasks:
                        decision = {
                            'type': 'maintenance_recommendation',
                            'agent_id': agent.agent_id,
                            'collaboration_id': collaboration_id,
                            'task': task,
                            'timestamp': time.time(),
                            'requires_approval': True
                        }

                        self.decision_queue.append(decision)

                        # Record contribution
                        agent.active_tasks[-1]['contributions'].append({
                            'type': 'maintenance_recommendation',
                            'timestamp': time.time(),
                            'details': task
                        })

                await asyncio.sleep(600)  # Check every 10 minutes

        except Exception as e:
            logger.error(f"Maintenance agent error: {e}")

    async def _generate_optimization_suggestions(self, collaboration: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions using quantum computing."""
        # Use quantum optimizer for complex optimization problems
        suggestions = []

        # Example: Process optimization
        optimization_result = self.quantum_optimizer.optimize_scheduling(
            tasks=[],  # Would be populated from current project
            resources=[],
            constraints={}
        )

        if optimization_result:
            suggestions.append({
                'type': 'process_optimization',
                'description': 'Quantum-optimized production schedule',
                'impact': '15% efficiency improvement',
                'confidence': 0.85
            })

        return suggestions

    async def _generate_system_alerts(self) -> List[Dict[str, Any]]:
        """Generate system monitoring alerts."""
        # Simulate monitoring alerts
        alerts = []

        # Check for anomalies (simplified)
        if time.time() % 300 < 60:  # Random alert every 5 minutes
            alerts.append({
                'severity': 'warning',
                'type': 'performance_anomaly',
                'description': 'Unusual vibration pattern detected on CNC machine',
                'equipment': 'cnc_001',
                'recommended_action': 'Schedule inspection'
            })

        return alerts

    async def _analyze_maintenance_needs(self) -> List[Dict[str, Any]]:
        """Analyze maintenance needs using predictive models."""
        maintenance_tasks = []

        # Simulate predictive maintenance analysis
        if time.time() % 1200 < 120:  # Random task every 20 minutes
            maintenance_tasks.append({
                'equipment': 'pump_001',
                'type': 'predictive_maintenance',
                'description': 'Bearing replacement recommended',
                'urgency': 'medium',
                'estimated_downtime': 4,
                'parts_required': ['bearing_608zz', 'lubricant_synthetic']
            })

        return maintenance_tasks

    async def process_decision_queue(self, operator_id: str) -> List[Dict[str, Any]]:
        """
        Process pending decisions requiring human input.

        Args:
            operator_id: Operator identifier

        Returns:
            Pending decisions for the operator
        """
        if operator_id not in self.human_operators:
            raise ValueError(f"Operator {operator_id} not found")

        operator = self.human_operators[operator_id]

        # Get decisions relevant to this operator's teams and authority level
        relevant_decisions = []

        for decision in self.decision_queue:
            collaboration = self.active_collaborations.get(decision['collaboration_id'])
            if collaboration:
                team = self.collaboration_teams.get(collaboration['team_id'])
                if team and operator_id in team.human_members:
                    # Check if operator has authority to make this decision
                    if self._has_decision_authority(operator, decision):
                        relevant_decisions.append(decision)

        return relevant_decisions

    def _has_decision_authority(self, operator: HumanOperator, decision: Dict[str, Any]) -> bool:
        """Check if operator has authority for a decision."""
        decision_type = decision['type']

        # Define authority requirements
        authority_requirements = {
            'optimization_suggestion': DecisionAuthority.HUMAN_IN_LOOP,
            'system_alert': DecisionAuthority.MACHINE_SUGGESTED,
            'maintenance_recommendation': DecisionAuthority.HUMAN_IN_LOOP
        }

        required_authority = authority_requirements.get(decision_type, DecisionAuthority.HUMAN_ONLY)

        # Check operator's authority level
        authority_hierarchy = {
            DecisionAuthority.HUMAN_ONLY: 0,
            DecisionAuthority.HUMAN_IN_LOOP: 1,
            DecisionAuthority.MACHINE_SUGGESTED: 2,
            DecisionAuthority.MACHINE_AUTONOMOUS: 3
        }

        return authority_hierarchy.get(operator.decision_authority, 0) >= authority_hierarchy.get(required_authority, 0)

    async def make_decision(self, operator_id: str, decision_id: str,
                           decision: str, reasoning: str = "") -> Dict[str, Any]:
        """
        Make a decision on a pending item.

        Args:
            operator_id: Operator identifier
            decision_id: Decision identifier
            decision: Decision ('approve', 'reject', 'modify')
            reasoning: Decision reasoning

        Returns:
            Decision result
        """
        # Find the decision in queue
        pending_decision = None
        for d in self.decision_queue:
            if d.get('id', d.get('timestamp')) == decision_id:
                pending_decision = d
                break

        if not pending_decision:
            raise ValueError(f"Decision {decision_id} not found")

        # Record the human decision
        decision_record = {
            'decision_id': decision_id,
            'operator_id': operator_id,
            'decision': decision,
            'reasoning': reasoning,
            'timestamp': time.time()
        }

        collaboration = self.active_collaborations.get(pending_decision['collaboration_id'])
        if collaboration:
            collaboration['decision_log'].append(decision_record)

            # Record human contribution
            collaboration['human_contributions'].append({
                'operator_id': operator_id,
                'type': 'decision_making',
                'decision': decision_record,
                'timestamp': time.time()
            })

        # Remove from queue
        self.decision_queue.remove(pending_decision)

        # Execute decision if approved
        if decision == 'approve':
            await self._execute_decision(pending_decision)

        return {
            'status': 'decision_made',
            'decision_id': decision_id,
            'decision': decision,
            'executed': decision == 'approve'
        }

    async def _execute_decision(self, decision: Dict[str, Any]):
        """Execute an approved decision."""
        decision_type = decision['type']

        if decision_type == 'optimization_suggestion':
            # Implement optimization
            logger.info(f"Implementing optimization: {decision['suggestions']}")
        elif decision_type == 'maintenance_recommendation':
            # Schedule maintenance
            logger.info(f"Scheduling maintenance: {decision['task']}")
        elif decision_type == 'system_alert':
            # Handle alert
            logger.info(f"Handling alert: {decision['alert']}")

    async def get_collaboration_status(self, collaboration_id: str) -> Dict[str, Any]:
        """
        Get status of a collaboration session.

        Args:
            collaboration_id: Collaboration identifier

        Returns:
            Collaboration status
        """
        if collaboration_id not in self.active_collaborations:
            raise ValueError(f"Collaboration {collaboration_id} not found")

        collaboration = self.active_collaborations[collaboration_id]
        team = self.collaboration_teams[collaboration['team_id']]

        # Calculate collaboration metrics
        human_contributions = len(collaboration['human_contributions'])
        machine_contributions = len(collaboration['machine_contributions'])
        decisions_made = len(collaboration['decision_log'])

        collaboration_quality = min(1.0, (human_contributions + machine_contributions) / 10)  # Simplified

        return {
            'collaboration_id': collaboration_id,
            'status': collaboration['status'],
            'team_name': team.name,
            'duration_hours': (time.time() - collaboration['start_time']) / 3600,
            'human_contributions': human_contributions,
            'machine_contributions': machine_contributions,
            'decisions_made': decisions_made,
            'collaboration_quality': collaboration_quality,
            'pending_decisions': len([
                d for d in self.decision_queue
                if d['collaboration_id'] == collaboration_id
            ])
        }

    async def end_collaboration(self, collaboration_id: str) -> Dict[str, Any]:
        """
        End a collaboration session.

        Args:
            collaboration_id: Collaboration identifier

        Returns:
            Collaboration summary
        """
        if collaboration_id not in self.active_collaborations:
            raise ValueError(f"Collaboration {collaboration_id} not found")

        collaboration = self.active_collaborations[collaboration_id]
        team = self.collaboration_teams[collaboration['team_id']]

        end_time = time.time()
        duration = end_time - collaboration['start_time']

        # Calculate final metrics
        summary = {
            'collaboration_id': collaboration_id,
            'team_name': team.name,
            'duration_hours': duration / 3600,
            'human_contributions': len(collaboration['human_contributions']),
            'machine_contributions': len(collaboration['machine_contributions']),
            'decisions_made': len(collaboration['decision_log']),
            'collaboration_level': team.collaboration_level.value,
            'outcome_quality': collaboration['performance_metrics']['outcome_quality'],
            'end_time': datetime.fromtimestamp(end_time).isoformat()
        }

        # Update team performance
        team.performance_metrics['total_collaborations'] = team.performance_metrics.get('total_collaborations', 0) + 1
        team.performance_metrics['average_quality'] = (
            team.performance_metrics.get('average_quality', 0) * (team.performance_metrics['total_collaborations'] - 1) +
            summary['outcome_quality']
        ) / team.performance_metrics['total_collaborations']

        # Clean up
        del self.active_collaborations[collaboration_id]

        # End workspace session
        if 'workspace_id' in collaboration:
            self.collab_workspace.end_session(collaboration['workspace_id'])

        logger.info(f"Ended Industry 5.0 collaboration {collaboration_id}")

        return {
            'status': 'ended',
            'summary': summary
        }

    def get_platform_metrics(self) -> Dict[str, Any]:
        """
        Get overall platform performance metrics.

        Returns:
            Platform metrics
        """
        total_operators = len(self.human_operators)
        total_agents = len(self.autonomous_agents)
        total_teams = len(self.collaboration_teams)
        active_collaborations = len(self.active_collaborations)

        # Calculate average metrics
        operator_workloads = [op.current_workload for op in self.human_operators.values()]
        avg_workload = sum(operator_workloads) / max(1, len(operator_workloads))

        team_qualities = [team.performance_metrics.get('average_quality', 0)
                         for team in self.collaboration_teams.values()]
        avg_team_quality = sum(team_qualities) / max(1, len(team_qualities))

        return {
            'total_operators': total_operators,
            'total_agents': total_agents,
            'total_teams': total_teams,
            'active_collaborations': active_collaborations,
            'average_operator_workload': avg_workload,
            'average_team_quality': avg_team_quality,
            'pending_decisions': len(self.decision_queue),
            'collaboration_levels': {
                level.value: len([t for t in self.collaboration_teams.values()
                                if t.collaboration_level == level])
                for level in CollaborationLevel
            }
        }


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize Industry 5.0 platform
        platform = Industry5Platform()

        # Get platform metrics
        metrics = platform.get_platform_metrics()
        print("Platform metrics:", metrics)

        # Initiate collaboration
        project_config = {
            "name": "Production Line Optimization",
            "description": "Optimize production line efficiency using human-machine collaboration",
            "objectives": ["reduce_downtime", "improve_quality", "optimize_resources"],
            "duration_days": 30
        }

        collaboration = await platform.initiate_human_machine_collaboration(
            "team_production_001", project_config
        )
        print(f"Initiated collaboration: {collaboration['collaboration_id']}")

        # Check for pending decisions
        decisions = await platform.process_decision_queue("operator_001")
        print(f"Pending decisions: {len(decisions)}")

        # Make a decision
        if decisions:
            result = await platform.make_decision(
                "operator_001", decisions[0]['timestamp'], "approve",
                "Approved optimization suggestion"
            )
            print("Decision made:", result['status'])

        # Get collaboration status
        status = await platform.get_collaboration_status(collaboration['collaboration_id'])
        print("Collaboration status:", status)

        # End collaboration
        summary = await platform.end_collaboration(collaboration['collaboration_id'])
        print("Collaboration ended:", summary['summary']['duration_hours'], "hours")

    # Run example
    asyncio.run(main())