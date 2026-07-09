"""
VR Training Simulator Module for IoT IIoT Intelligence Platform

This module provides virtual reality training environments for industrial operators,
enabling skill development through immersive simulations of industrial processes.
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
class TrainingScenario:
    """Represents a training scenario."""
    scenario_id: str
    title: str
    description: str
    equipment_type: str
    difficulty_level: str
    estimated_duration: int  # minutes
    learning_objectives: List[str]
    required_skills: List[str]
    environment_setup: Dict[str, Any]
    tasks: List[Dict]  # Scenario tasks
    evaluation_criteria: List[Dict]
    success_threshold: float  # 0-1

@dataclass
class TrainingSession:
    """Represents a training session."""
    session_id: str
    trainee_id: str
    scenario_id: str
    start_time: float
    end_time: Optional[float] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    completed_tasks: List[Dict] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    feedback: List[str] = field(default_factory=list)
    score: Optional[float] = None

class VRTrainingSimulator:
    """
    VR Training Simulator for industrial operator skill development.
    Provides immersive training environments with performance tracking.
    """

    def __init__(self, scenarios_path: str = "data/training_scenarios.json",
                 sessions_path: str = "data/training_sessions.json"):
        """
        Initialize VR training simulator.

        Args:
            scenarios_path: Path to training scenarios database
            sessions_path: Path to training sessions database
        """
        self.scenarios_path = Path(scenarios_path)
        self.sessions_path = Path(sessions_path)

        self.scenarios_path.parent.mkdir(parents=True, exist_ok=True)
        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)

        self.scenarios: Dict[str, TrainingScenario] = {}
        self.active_sessions: Dict[str, TrainingSession] = {}
        self.sessions_history: List[TrainingSession] = []

        # Load data
        self._load_scenarios()
        self._load_sessions()

        # Initialize default scenarios if none exist
        if not self.scenarios:
            self._create_default_scenarios()

    def _load_scenarios(self):
        """Load training scenarios from storage."""
        try:
            if self.scenarios_path.exists():
                with open(self.scenarios_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for scenario_data in data.get('scenarios', []):
                        scenario = self._deserialize_scenario(scenario_data)
                        self.scenarios[scenario.scenario_id] = scenario
                logger.info(f"Loaded {len(self.scenarios)} training scenarios")
        except Exception as e:
            logger.error(f"Failed to load scenarios: {e}")

    def _load_sessions(self):
        """Load training sessions from storage."""
        try:
            if self.sessions_path.exists():
                with open(self.sessions_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for session_data in data.get('sessions', []):
                        session = TrainingSession(**session_data)
                        self.sessions_history.append(session)
                logger.info(f"Loaded {len(self.sessions_history)} training sessions")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")

    def _create_default_scenarios(self):
        """Create default training scenarios."""
        # CNC Machine Operation Scenario
        cnc_scenario = TrainingScenario(
            scenario_id="cnc_operation_001",
            title="CNC Machine Basic Operation",
            description="Learn basic CNC machine operation and safety procedures",
            equipment_type="cnc_machine",
            difficulty_level="beginner",
            estimated_duration=45,
            learning_objectives=[
                "Understand CNC machine components",
                "Learn safety procedures",
                "Master basic operation controls",
                "Handle tool changes safely"
            ],
            required_skills=["basic_mechanics", "computer_skills"],
            environment_setup={
                "virtual_machine": "cnc_mill_3axis",
                "workspace": "standard_workshop",
                "lighting": "industrial",
                "sound_effects": True
            },
            tasks=[
                {
                    "task_id": "power_on",
                    "title": "Machine Power On",
                    "description": "Safely power on the CNC machine",
                    "steps": ["Check emergency stop", "Turn on main power", "Initialize controls"],
                    "time_limit": 300,
                    "critical_actions": ["emergency_stop_check", "power_sequence"]
                },
                {
                    "task_id": "tool_setup",
                    "title": "Tool Setup and Calibration",
                    "description": "Set up cutting tools and calibrate measurements",
                    "steps": ["Load tool holders", "Measure tool lengths", "Set work coordinates"],
                    "time_limit": 600,
                    "critical_actions": ["tool_measurement", "coordinate_system"]
                },
                {
                    "task_id": "program_execution",
                    "title": "Program Loading and Execution",
                    "description": "Load and execute a simple machining program",
                    "steps": ["Load G-code program", "Verify tool path", "Execute program", "Monitor process"],
                    "time_limit": 900,
                    "critical_actions": ["program_verification", "safe_execution"]
                }
            ],
            evaluation_criteria=[
                {"metric": "safety_compliance", "weight": 0.4, "target": 1.0},
                {"metric": "task_completion", "weight": 0.3, "target": 1.0},
                {"metric": "time_efficiency", "weight": 0.2, "target": 0.8},
                {"metric": "error_rate", "weight": 0.1, "target": 0.0}
            ],
            success_threshold=0.75
        )

        # Chemical Process Control Scenario
        chem_scenario = TrainingScenario(
            scenario_id="chemical_process_002",
            title="Chemical Process Control",
            description="Learn to monitor and control chemical processing operations",
            equipment_type="chemical_reactor",
            difficulty_level="intermediate",
            estimated_duration=60,
            learning_objectives=[
                "Monitor process parameters",
                "Respond to process deviations",
                "Maintain safety protocols",
                "Optimize process efficiency"
            ],
            required_skills=["chemistry_basics", "process_control"],
            environment_setup={
                "virtual_machine": "batch_reactor",
                "workspace": "chemical_plant",
                "hazards": ["corrosive_materials", "pressure_vessels"],
                "monitoring_systems": True
            },
            tasks=[
                {
                    "task_id": "parameter_monitoring",
                    "title": "Process Parameter Monitoring",
                    "description": "Monitor temperature, pressure, and flow rates",
                    "steps": ["Check all sensors", "Record baseline values", "Set alarm limits"],
                    "time_limit": 600,
                    "critical_actions": ["sensor_verification", "alarm_setup"]
                },
                {
                    "task_id": "deviation_response",
                    "title": "Respond to Process Deviations",
                    "description": "Handle temperature and pressure deviations",
                    "steps": ["Identify deviation", "Assess severity", "Implement correction", "Document response"],
                    "time_limit": 900,
                    "critical_actions": ["deviation_assessment", "corrective_action"]
                }
            ],
            evaluation_criteria=[
                {"metric": "monitoring_accuracy", "weight": 0.3, "target": 0.95},
                {"metric": "response_time", "weight": 0.3, "target": 300},
                {"metric": "safety_compliance", "weight": 0.4, "target": 1.0}
            ],
            success_threshold=0.8
        )

        self.scenarios[cnc_scenario.scenario_id] = cnc_scenario
        self.scenarios[chem_scenario.scenario_id] = chem_scenario
        self._save_scenarios()

    def _deserialize_scenario(self, data: Dict) -> TrainingScenario:
        """Deserialize scenario from JSON data."""
        return TrainingScenario(**data)

    def _save_scenarios(self):
        """Save scenarios to storage."""
        try:
            data = {
                'scenarios': [vars(s) for s in self.scenarios.values()]
            }

            with open(self.scenarios_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("Scenarios saved successfully")
        except Exception as e:
            logger.error(f"Failed to save scenarios: {e}")

    def _save_sessions(self):
        """Save sessions to storage."""
        try:
            data = {
                'sessions': [vars(s) for s in self.sessions_history]
            }

            with open(self.sessions_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("Sessions saved successfully")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def start_training_session(self, trainee_id: str, scenario_id: str) -> Dict[str, Any]:
        """
        Start a new training session.

        Args:
            trainee_id: ID of the trainee
            scenario_id: ID of the training scenario

        Returns:
            Session information and initial scenario data
        """
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")

        scenario = self.scenarios[scenario_id]
        session_id = f"{scenario_id}_{trainee_id}_{int(time.time())}"

        session = TrainingSession(
            session_id=session_id,
            trainee_id=trainee_id,
            scenario_id=scenario_id,
            start_time=time.time()
        )

        self.active_sessions[session_id] = session

        # Generate VR environment setup
        vr_environment = self._generate_vr_environment(scenario)

        logger.info(f"Started training session {session_id} for trainee {trainee_id}")

        return {
            'session_id': session_id,
            'scenario': vars(scenario),
            'vr_environment': vr_environment,
            'status': 'started'
        }

    def _generate_vr_environment(self, scenario: TrainingScenario) -> Dict[str, Any]:
        """Generate VR environment configuration."""
        return {
            'scene': scenario.environment_setup.get('workspace', 'workshop'),
            'equipment': {
                'model': scenario.environment_setup.get('virtual_machine', 'generic'),
                'interactive_elements': True,
                'physics_enabled': True
            },
            'ui_elements': {
                'task_list': True,
                'timer': True,
                'performance_metrics': True,
                'help_system': True
            },
            'feedback_system': {
                'real_time_hints': True,
                'error_correction': True,
                'progress_tracking': True
            },
            'safety_system': {
                'hazard_detection': True,
                'emergency_procedures': True,
                'ppe_requirements': scenario.equipment_type in ['chemical_reactor', 'high_voltage']
            }
        }

    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get current state of a training session.

        Args:
            session_id: Session ID

        Returns:
            Current session state
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        scenario = self.scenarios[session.scenario_id]

        current_task_idx = len(session.completed_tasks)
        current_task = scenario.tasks[current_task_idx] if current_task_idx < len(scenario.tasks) else None

        return {
            'session_id': session_id,
            'scenario_title': scenario.title,
            'current_task': current_task,
            'progress': {
                'completed_tasks': current_task_idx,
                'total_tasks': len(scenario.tasks),
                'percentage': (current_task_idx / len(scenario.tasks)) * 100 if scenario.tasks else 0
            },
            'performance': session.performance_metrics,
            'time_elapsed': time.time() - session.start_time,
            'errors': len(session.errors)
        }

    def submit_task_result(self, session_id: str, task_id: str,
                          result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit results for a completed task.

        Args:
            session_id: Session ID
            task_id: Task ID
            result_data: Task completion data

        Returns:
            Task evaluation and next task info
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        scenario = self.scenarios[session.scenario_id]

        # Find the task
        task = next((t for t in scenario.tasks if t['task_id'] == task_id), None)
        if not task:
            raise ValueError(f"Task {task_id} not found in scenario")

        # Evaluate task performance
        evaluation = self._evaluate_task_performance(task, result_data)

        # Record completion
        task_completion = {
            'task_id': task_id,
            'timestamp': time.time(),
            'result_data': result_data,
            'evaluation': evaluation
        }

        session.completed_tasks.append(task_completion)

        # Update performance metrics
        self._update_performance_metrics(session, evaluation)

        # Check for errors
        if evaluation['score'] < 0.6:  # Threshold for errors
            session.errors.append({
                'task_id': task_id,
                'timestamp': time.time(),
                'evaluation': evaluation
            })

        # Determine next action
        current_task_idx = len(session.completed_tasks)
        if current_task_idx >= len(scenario.tasks):
            # Scenario completed
            return self.complete_session(session_id)
        else:
            next_task = scenario.tasks[current_task_idx]
            return {
                'status': 'task_completed',
                'evaluation': evaluation,
                'next_task': next_task,
                'progress': {
                    'completed': current_task_idx,
                    'total': len(scenario.tasks)
                }
            }

    def _evaluate_task_performance(self, task: Dict, result_data: Dict) -> Dict[str, Any]:
        """Evaluate performance on a task."""
        score = 0.0
        feedback = []

        # Evaluate based on task requirements
        if 'time_taken' in result_data:
            time_limit = task.get('time_limit', 600)
            time_efficiency = min(result_data['time_taken'] / time_limit, 1.0)
            score += 0.3 * (1.0 - time_efficiency)  # Better if faster
            if time_efficiency > 1.2:
                feedback.append("Consider working more efficiently")
            elif time_efficiency < 0.8:
                feedback.append("Good time management")

        # Evaluate critical actions
        critical_actions = task.get('critical_actions', [])
        completed_critical = result_data.get('critical_actions_completed', [])
        critical_score = len(set(completed_critical) & set(critical_actions)) / len(critical_actions) if critical_actions else 1.0
        score += 0.4 * critical_score

        if critical_score < 1.0:
            feedback.append("Ensure all critical safety steps are completed")

        # Evaluate accuracy
        accuracy = result_data.get('accuracy', 1.0)
        score += 0.3 * accuracy

        if accuracy < 0.8:
            feedback.append("Review procedures for better accuracy")

        return {
            'score': score,
            'time_efficiency': result_data.get('time_taken', 0) / task.get('time_limit', 600),
            'critical_completion': critical_score,
            'accuracy': accuracy,
            'feedback': feedback
        }

    def _update_performance_metrics(self, session: TrainingSession, evaluation: Dict):
        """Update session performance metrics."""
        metrics = session.performance_metrics

        # Update averages
        task_count = len(session.completed_tasks)
        metrics['average_score'] = (
            (metrics.get('average_score', 0) * (task_count - 1)) + evaluation['score']
        ) / task_count

        if 'time_efficiency' in evaluation:
            metrics['average_time_efficiency'] = (
                (metrics.get('average_time_efficiency', 0) * (task_count - 1)) + evaluation['time_efficiency']
            ) / task_count

        metrics['total_errors'] = len(session.errors)

    def complete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Complete a training session.

        Args:
            session_id: Session ID

        Returns:
            Session completion summary
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        scenario = self.scenarios[session.scenario_id]

        session.end_time = time.time()
        duration = session.end_time - session.start_time

        # Calculate final score
        final_score = self._calculate_final_score(session, scenario)

        session.score = final_score

        # Generate certificate/recommendations
        completion_data = {
            'session_id': session_id,
            'scenario_title': scenario.title,
            'trainee_id': session.trainee_id,
            'duration_minutes': duration / 60,
            'final_score': final_score,
            'success': final_score >= scenario.success_threshold,
            'performance_metrics': session.performance_metrics,
            'completed_tasks': len(session.completed_tasks),
            'errors': len(session.errors),
            'completion_time': datetime.fromtimestamp(session.end_time).isoformat()
        }

        # Move to history
        self.sessions_history.append(session)
        del self.active_sessions[session_id]

        # Save sessions
        self._save_sessions()

        logger.info(f"Training session {session_id} completed with score {final_score:.2f}")

        return {
            'status': 'completed',
            'completion_data': completion_data,
            'certificate': self._generate_certificate(completion_data) if completion_data['success'] else None,
            'recommendations': self._generate_recommendations(completion_data)
        }

    def _calculate_final_score(self, session: TrainingSession, scenario: TrainingScenario) -> float:
        """Calculate final session score based on evaluation criteria."""
        metrics = session.performance_metrics

        final_score = 0.0
        for criterion in scenario.evaluation_criteria:
            metric_name = criterion['metric']
            weight = criterion['weight']
            target = criterion['target']

            if metric_name == 'safety_compliance':
                # Based on error rate
                error_rate = len(session.errors) / len(scenario.tasks)
                score = 1.0 - min(error_rate, 1.0)
            elif metric_name == 'task_completion':
                score = len(session.completed_tasks) / len(scenario.tasks)
            elif metric_name == 'time_efficiency':
                score = min(metrics.get('average_time_efficiency', 1.0), 1.0)
            elif metric_name == 'error_rate':
                error_rate = len(session.errors) / len(scenario.tasks)
                score = 1.0 - error_rate
            else:
                score = metrics.get(metric_name, 0.5)

            final_score += weight * min(score / target, 1.0) if target > 0 else weight * score

        return final_score

    def _generate_certificate(self, completion_data: Dict) -> Dict[str, Any]:
        """Generate training completion certificate."""
        return {
            'certificate_id': f"CERT_{completion_data['session_id']}",
            'trainee_id': completion_data['trainee_id'],
            'scenario': completion_data['scenario_title'],
            'score': completion_data['final_score'],
            'issued_date': completion_data['completion_time'],
            'validity_period': '2 years',
            'skills_certified': ['equipment_operation', 'safety_procedures', 'process_control']
        }

    def _generate_recommendations(self, completion_data: Dict) -> List[str]:
        """Generate training recommendations."""
        recommendations = []

        if completion_data['final_score'] < 0.7:
            recommendations.append("Consider additional training in basic procedures")
        elif completion_data['final_score'] < 0.85:
            recommendations.append("Practice with more complex scenarios")

        if completion_data['errors'] > 2:
            recommendations.append("Focus on safety procedures and error prevention")

        if completion_data['duration_minutes'] > completion_data.get('estimated_duration', 60) * 1.5:
            recommendations.append("Work on improving time efficiency")

        if not recommendations:
            recommendations.append("Ready for advanced training scenarios")

        return recommendations

    def get_available_scenarios(self, trainee_level: Optional[str] = None) -> List[Dict]:
        """
        Get list of available training scenarios.

        Args:
            trainee_level: Filter by difficulty level

        Returns:
            List of available scenarios
        """
        scenarios = self.scenarios.values()

        if trainee_level:
            scenarios = [s for s in scenarios if s.difficulty_level == trainee_level]

        return [
            {
                'scenario_id': s.scenario_id,
                'title': s.title,
                'description': s.description,
                'equipment_type': s.equipment_type,
                'difficulty_level': s.difficulty_level,
                'estimated_duration': s.estimated_duration,
                'learning_objectives': s.learning_objectives
            }
            for s in scenarios
        ]

    def get_trainee_progress(self, trainee_id: str) -> Dict[str, Any]:
        """
        Get training progress for a trainee.

        Args:
            trainee_id: Trainee ID

        Returns:
            Progress summary
        """
        trainee_sessions = [s for s in self.sessions_history if s.trainee_id == trainee_id]

        if not trainee_sessions:
            return {'trainee_id': trainee_id, 'sessions_completed': 0, 'message': 'No training history'}

        completed_sessions = [s for s in trainee_sessions if s.score is not None]

        average_score = np.mean([s.score for s in completed_sessions]) if completed_sessions else 0
        total_time = sum((s.end_time - s.start_time) for s in completed_sessions if s.end_time)

        scenarios_completed = set(s.scenario_id for s in completed_sessions)

        return {
            'trainee_id': trainee_id,
            'sessions_completed': len(completed_sessions),
            'average_score': average_score,
            'total_training_time_hours': total_time / 3600,
            'scenarios_completed': list(scenarios_completed),
            'certificates_earned': len([s for s in completed_sessions if s.score >= self.scenarios[s.scenario_id].success_threshold])
        }


# Example usage
if __name__ == "__main__":
    # Initialize VR training simulator
    simulator = VRTrainingSimulator()

    # Get available scenarios
    scenarios = simulator.get_available_scenarios()
    print("Available scenarios:", [s['title'] for s in scenarios])

    # Start a training session
    if scenarios:
        session = simulator.start_training_session(
            trainee_id="trainee_001",
            scenario_id=scenarios[0]['scenario_id']
        )
        print("Started session:", session['session_id'])

        # Simulate task completion
        task_result = simulator.submit_task_result(
            session_id=session['session_id'],
            task_id=session['scenario']['tasks'][0]['task_id'],
            result_data={
                'time_taken': 250,
                'critical_actions_completed': ['emergency_stop_check', 'power_sequence'],
                'accuracy': 0.95
            }
        )
        print("Task result:", task_result['status'])

        # Complete session
        completion = simulator.complete_session(session['session_id'])
        print("Session completed with score:", completion['completion_data']['final_score'])

        # Get trainee progress
        progress = simulator.get_trainee_progress("trainee_001")
        print("Trainee progress:", progress)