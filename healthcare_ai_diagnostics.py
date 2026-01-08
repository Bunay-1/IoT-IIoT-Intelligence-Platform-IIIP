"""
Healthcare AI Diagnostics Module

This module provides AI-powered diagnostic capabilities for healthcare applications within industrial settings.
It includes worker health monitoring, predictive health analytics, medical IoT integration,
and diagnostic assistance for occupational health and safety.

Features:
- Worker health monitoring and anomaly detection
- Predictive health risk assessment
- Medical IoT device integration
- Diagnostic assistance for occupational injuries
- Health data privacy and compliance
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd

class HealthDataProcessor:
    """
    Processes and normalizes health data from various sources.
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = [
            'heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'body_temperature', 'oxygen_saturation', 'respiratory_rate',
            'activity_level', 'stress_level', 'sleep_quality', 'fatigue_level'
        ]

    def normalize_health_data(self, raw_data: Dict[str, Any]) -> np.ndarray:
        """
        Normalize health data for AI processing.

        Args:
            raw_data: Raw health measurements

        Returns:
            np.ndarray: Normalized feature vector
        """
        features = []
        for col in self.feature_columns:
            value = raw_data.get(col, 0)
            features.append(float(value))

        features_array = np.array(features).reshape(1, -1)

        # Fit scaler if not fitted, otherwise transform
        if not hasattr(self.scaler, 'mean_'):
            self.scaler.fit(features_array)

        return self.scaler.transform(features_array)

    def validate_health_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate health data for completeness and plausibility.

        Args:
            data: Health data to validate

        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        required_fields = ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate ranges
        validations = {
            'heart_rate': (40, 200),
            'blood_pressure_systolic': (80, 200),
            'blood_pressure_diastolic': (50, 120),
            'body_temperature': (35.0, 42.0),
            'oxygen_saturation': (70, 100),
            'respiratory_rate': (8, 40)
        }

        for field, (min_val, max_val) in validations.items():
            if field in data:
                value = data[field]
                if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                    errors.append(f"Invalid {field}: {value} (expected {min_val}-{max_val})")

        return len(errors) == 0, errors

class WorkerHealthMonitor:
    """
    Monitors worker health using AI for anomaly detection and risk assessment.
    """

    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.risk_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.data_processor = HealthDataProcessor()

        self.worker_profiles: Dict[str, Dict] = {}
        self.health_history: Dict[str, List] = {}
        self.is_trained = False

    def register_worker(self, worker_id: str, baseline_data: Dict[str, Any],
                       medical_history: Dict[str, Any] = None) -> bool:
        """
        Register a worker with baseline health data.

        Args:
            worker_id: Unique worker identifier
            baseline_data: Baseline health measurements
            medical_history: Medical history information

        Returns:
            bool: Success status
        """
        is_valid, errors = self.data_processor.validate_health_data(baseline_data)
        if not is_valid:
            print(f"Invalid baseline data for worker {worker_id}: {errors}")
            return False

        self.worker_profiles[worker_id] = {
            'baseline': baseline_data,
            'medical_history': medical_history or {},
            'risk_factors': self._assess_risk_factors(baseline_data, medical_history),
            'registered_at': datetime.utcnow()
        }

        self.health_history[worker_id] = [baseline_data]
        return True

    def monitor_health(self, worker_id: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor worker health and detect anomalies.

        Args:
            worker_id: Worker identifier
            current_data: Current health measurements

        Returns:
            Dict[str, Any]: Health monitoring results
        """
        if worker_id not in self.worker_profiles:
            return {"error": "Worker not registered"}

        is_valid, errors = self.data_processor.validate_health_data(current_data)
        if not is_valid:
            return {"error": f"Invalid health data: {errors}"}

        # Normalize data
        normalized_data = self.data_processor.normalize_health_data(current_data)

        # Detect anomalies
        anomaly_score = self._detect_anomaly(normalized_data)

        # Assess health risk
        risk_level = self._assess_health_risk(worker_id, current_data)

        # Store in history
        self.health_history[worker_id].append({
            **current_data,
            'timestamp': datetime.utcnow(),
            'anomaly_score': anomaly_score,
            'risk_level': risk_level
        })

        # Generate recommendations
        recommendations = self._generate_recommendations(worker_id, current_data, anomaly_score, risk_level)

        return {
            "worker_id": worker_id,
            "timestamp": datetime.utcnow(),
            "anomaly_detected": anomaly_score < -0.5,  # Isolation Forest threshold
            "anomaly_score": float(anomaly_score),
            "risk_level": risk_level,
            "recommendations": recommendations,
            "alerts": self._generate_alerts(worker_id, anomaly_score, risk_level)
        }

    def _detect_anomaly(self, normalized_data: np.ndarray) -> float:
        """
        Detect health anomalies using Isolation Forest.

        Args:
            normalized_data: Normalized health data

        Returns:
            float: Anomaly score (-1 to 1, more negative = more anomalous)
        """
        if not self.is_trained:
            # Train on synthetic normal data for demonstration
            normal_data = np.random.normal(0, 1, (100, len(self.data_processor.feature_columns)))
            self.anomaly_detector.fit(normal_data)
            self.is_trained = True

        return float(self.anomaly_detector.score_samples(normalized_data)[0])

    def _assess_health_risk(self, worker_id: str, current_data: Dict[str, Any]) -> str:
        """
        Assess overall health risk level.

        Args:
            worker_id: Worker identifier
            current_data: Current health data

        Returns:
            str: Risk level (low, medium, high, critical)
        """
        risk_score = 0

        # Heart rate risk
        hr = current_data.get('heart_rate', 70)
        if hr < 50 or hr > 100:
            risk_score += 2
        elif hr < 60 or hr > 90:
            risk_score += 1

        # Blood pressure risk
        systolic = current_data.get('blood_pressure_systolic', 120)
        diastolic = current_data.get('blood_pressure_diastolic', 80)

        if systolic > 180 or diastolic > 110:
            risk_score += 3
        elif systolic > 140 or diastolic > 90:
            risk_score += 2
        elif systolic > 130 or diastolic > 85:
            risk_score += 1

        # Oxygen saturation risk
        o2 = current_data.get('oxygen_saturation', 98)
        if o2 < 90:
            risk_score += 3
        elif o2 < 95:
            risk_score += 2

        # Fatigue and stress
        fatigue = current_data.get('fatigue_level', 0)
        stress = current_data.get('stress_level', 0)

        risk_score += min(fatigue + stress, 3)  # Cap at 3

        # Risk level mapping
        if risk_score >= 6:
            return "critical"
        elif risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"

    def _assess_risk_factors(self, baseline_data: Dict[str, Any],
                           medical_history: Dict[str, Any]) -> List[str]:
        """
        Assess individual risk factors.

        Args:
            baseline_data: Baseline health data
            medical_history: Medical history

        Returns:
            List[str]: List of risk factors
        """
        risk_factors = []

        # Age-related risks (assuming age is in medical_history)
        age = medical_history.get('age', 30)
        if age > 50:
            risk_factors.append("age_over_50")
        if age > 65:
            risk_factors.append("age_over_65")

        # Pre-existing conditions
        conditions = medical_history.get('conditions', [])
        risk_mapping = {
            'hypertension': 'cardiovascular_risk',
            'diabetes': 'metabolic_risk',
            'asthma': 'respiratory_risk',
            'arthritis': 'musculoskeletal_risk'
        }

        for condition in conditions:
            if condition.lower() in risk_mapping:
                risk_factors.append(risk_mapping[condition.lower()])

        # Occupational factors
        job_role = medical_history.get('job_role', '').lower()
        if 'heavy' in job_role or 'physical' in job_role:
            risk_factors.append("heavy_physical_work")
        if 'night' in job_role or 'shift' in job_role:
            risk_factors.append("shift_work")

        return risk_factors

    def _generate_recommendations(self, worker_id: str, current_data: Dict[str, Any],
                                anomaly_score: float, risk_level: str) -> List[str]:
        """
        Generate health recommendations.

        Args:
            worker_id: Worker identifier
            current_data: Current health data
            anomaly_score: Anomaly score
            risk_level: Risk level

        Returns:
            List[str]: Health recommendations
        """
        recommendations = []

        if risk_level == "critical":
            recommendations.append("Immediate medical attention required")
            recommendations.append("Stop work activities immediately")
        elif risk_level == "high":
            recommendations.append("Consult occupational health physician")
            recommendations.append("Reduce workload temporarily")
        elif risk_level == "medium":
            recommendations.append("Monitor health closely")
            recommendations.append("Consider rest break")

        if anomaly_score < -0.5:
            recommendations.append("Health parameters outside normal range")
            recommendations.append("Schedule comprehensive health check")

        # Specific recommendations based on data
        hr = current_data.get('heart_rate', 70)
        if hr > 100:
            recommendations.append("High heart rate - reduce physical exertion")
        elif hr < 50:
            recommendations.append("Low heart rate - consult medical professional")

        o2 = current_data.get('oxygen_saturation', 98)
        if o2 < 95:
            recommendations.append("Low oxygen saturation - ensure proper ventilation")

        fatigue = current_data.get('fatigue_level', 5)
        if fatigue > 7:
            recommendations.append("High fatigue - take rest break")

        return recommendations

    def _generate_alerts(self, worker_id: str, anomaly_score: float, risk_level: str) -> List[Dict]:
        """
        Generate alerts for health monitoring system.

        Args:
            worker_id: Worker identifier
            anomaly_score: Anomaly score
            risk_level: Risk level

        Returns:
            List[Dict]: Alert messages
        """
        alerts = []

        if risk_level in ["high", "critical"]:
            alerts.append({
                "level": "urgent",
                "message": f"Worker {worker_id} health risk: {risk_level}",
                "action_required": "immediate_attention"
            })

        if anomaly_score < -0.7:
            alerts.append({
                "level": "warning",
                "message": f"Worker {worker_id} health anomaly detected",
                "action_required": "health_check"
            })

        return alerts

class OccupationalHealthDiagnosticAI:
    """
    AI system for occupational health diagnostics and injury prediction.
    """

    def __init__(self):
        self.injury_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        self.diagnostic_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.health_monitor = WorkerHealthMonitor()

    def predict_injury_risk(self, worker_data: Dict[str, Any], work_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict risk of occupational injury.

        Args:
            worker_data: Worker health and demographic data
            work_conditions: Work environment conditions

        Returns:
            Dict[str, Any]: Injury risk assessment
        """
        # Feature engineering for injury prediction
        features = self._extract_injury_features(worker_data, work_conditions)

        # Mock prediction (in production, use trained model)
        risk_score = np.random.random()

        risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.7 else "high"

        return {
            "risk_score": float(risk_score),
            "risk_level": risk_level,
            "contributing_factors": self._identify_risk_factors(features),
            "preventive_measures": self._suggest_preventive_measures(risk_level)
        }

    def diagnose_workplace_injury(self, symptoms: List[str], incident_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Diagnose workplace injury based on symptoms and incident details.

        Args:
            symptoms: List of symptoms
            incident_details: Details of the incident

        Returns:
            Dict[str, Any]: Diagnostic results
        """
        # Mock diagnostic logic
        possible_injuries = {
            "sprain": ["pain", "swelling", "limited_movement"],
            "strain": ["muscle_pain", "stiffness", "weakness"],
            "contusion": ["bruising", "swelling", "tenderness"],
            "fracture": ["severe_pain", "deformity", "inability_to_move"]
        }

        injury_scores = {}
        for injury, injury_symptoms in possible_injuries.items():
            match_count = len(set(symptoms) & set(injury_symptoms))
            injury_scores[injury] = match_count / len(injury_symptoms)

        most_likely_injury = max(injury_scores, key=injury_scores.get)

        return {
            "primary_diagnosis": most_likely_injury,
            "confidence": float(injury_scores[most_likely_injury]),
            "differential_diagnoses": sorted(injury_scores.items(), key=lambda x: x[1], reverse=True)[:3],
            "recommended_actions": self._get_treatment_recommendations(most_likely_injury),
            "report_required": injury_scores[most_likely_injury] > 0.5
        }

    def _extract_injury_features(self, worker_data: Dict, work_conditions: Dict) -> Dict[str, Any]:
        """
        Extract features for injury risk prediction.
        """
        return {
            "age": worker_data.get("age", 30),
            "experience_years": worker_data.get("experience", 5),
            "fatigue_level": worker_data.get("fatigue", 3),
            "work_intensity": work_conditions.get("intensity", 5),
            "equipment_age": work_conditions.get("equipment_age", 2),
            "safety_training": worker_data.get("safety_training", True)
        }

    def _identify_risk_factors(self, features: Dict[str, Any]) -> List[str]:
        """
        Identify contributing risk factors.
        """
        factors = []
        if features.get("fatigue_level", 0) > 7:
            factors.append("High fatigue")
        if features.get("work_intensity", 0) > 8:
            factors.append("High work intensity")
        if features.get("equipment_age", 0) > 5:
            factors.append("Old equipment")
        if not features.get("safety_training", True):
            factors.append("Lack of safety training")

        return factors

    def _suggest_preventive_measures(self, risk_level: str) -> List[str]:
        """
        Suggest preventive measures based on risk level.
        """
        measures = {
            "high": [
                "Immediate safety training",
                "Equipment maintenance check",
                "Reduced workload",
                "Supervisory oversight"
            ],
            "medium": [
                "Regular safety reminders",
                "Equipment inspection",
                "Fatigue monitoring"
            ],
            "low": [
                "Standard safety protocols",
                "Regular equipment checks"
            ]
        }

        return measures.get(risk_level, ["General safety measures"])

    def _get_treatment_recommendations(self, injury_type: str) -> List[str]:
        """
        Get treatment recommendations for injury type.
        """
        recommendations = {
            "sprain": ["RICE protocol", "Pain medication", "Immobilization", "Physical therapy"],
            "strain": ["Rest", "Ice", "Compression", "Elevation", "Gradual exercise"],
            "contusion": ["Ice application", "Elevation", "Pain relief", "Monitor for complications"],
            "fracture": ["Immobilization", "Medical imaging", "Possible surgery", "Rehabilitation"]
        }

        return recommendations.get(injury_type, ["Seek medical attention"])

# Example usage
if __name__ == "__main__":
    # Initialize healthcare AI system
    health_ai = OccupationalHealthDiagnosticAI()

    # Register a worker
    baseline_data = {
        'heart_rate': 72,
        'blood_pressure_systolic': 120,
        'blood_pressure_diastolic': 80,
        'body_temperature': 36.6,
        'oxygen_saturation': 98,
        'respiratory_rate': 16,
        'activity_level': 5,
        'stress_level': 3,
        'sleep_quality': 7,
        'fatigue_level': 2
    }

    medical_history = {
        'age': 35,
        'conditions': [],
        'job_role': 'assembly_line_worker'
    }

    health_ai.health_monitor.register_worker("worker_001", baseline_data, medical_history)
    print("Registered worker worker_001")

    # Monitor health
    current_data = {
        'heart_rate': 95,
        'blood_pressure_systolic': 135,
        'blood_pressure_diastolic': 85,
        'body_temperature': 37.0,
        'oxygen_saturation': 96,
        'respiratory_rate': 18,
        'activity_level': 8,
        'stress_level': 6,
        'sleep_quality': 5,
        'fatigue_level': 7
    }

    health_result = health_ai.health_monitor.monitor_health("worker_001", current_data)
    print("Health monitoring result:", json.dumps(health_result, indent=2, default=str))

    # Predict injury risk
    work_conditions = {
        "intensity": 7,
        "equipment_age": 3,
        "safety_measures": True
    }

    injury_risk = health_ai.predict_injury_risk(
        {"age": 35, "experience": 5, "fatigue": 7, "safety_training": True},
        work_conditions
    )
    print("Injury risk assessment:", json.dumps(injury_risk, indent=2))

    # Diagnose injury
    symptoms = ["severe_pain", "swelling", "limited_movement"]
    incident_details = {
        "incident_type": "fall",
        "height": "2 meters",
        "surface": "concrete"
    }

    diagnosis = health_ai.diagnose_workplace_injury(symptoms, incident_details)
    print("Injury diagnosis:", json.dumps(diagnosis, indent=2))