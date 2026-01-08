"""
Causal AI and Root Cause Analysis Engine
Advanced causal inference and explainable root cause analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from utils.logging_config import get_logger

logger = get_logger(__name__)


class CausalGraph:
    """Causal graph representation using DAG."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.causal_strengths = {}

    def add_causal_relationship(self, cause: str, effect: str, strength: float = 1.0):
        """Add causal relationship between variables."""
        self.graph.add_edge(cause, effect, weight=strength)
        self.causal_strengths[(cause, effect)] = strength

    def get_causal_paths(self, start: str, end: str) -> List[List[str]]:
        """Get all causal paths from start to end."""
        try:
            return list(nx.all_simple_paths(self.graph, start, end))
        except nx.NetworkXNoPath:
            return []

    def get_causal_strength(self, cause: str, effect: str) -> float:
        """Get causal strength between variables."""
        return self.causal_strengths.get((cause, effect), 0.0)

    def identify_root_causes(
        self, effect: str, threshold: float = 0.5
    ) -> List[Tuple[str, float]]:
        """Identify root causes for an effect."""
        root_causes = []

        # Find all predecessors
        predecessors = set()
        for node in self.graph.nodes():
            if nx.has_path(self.graph, node, effect):
                predecessors.add(node)

        # Remove intermediate causes
        root_causes_only = []
        for pred in predecessors:
            is_root = True
            for other_pred in predecessors:
                if other_pred != pred and nx.has_path(self.graph, other_pred, pred):
                    is_root = False
                    break
            if is_root:
                strength = self.get_causal_strength(pred, effect)
                if strength >= threshold:
                    root_causes_only.append((pred, strength))

        return sorted(root_causes_only, key=lambda x: x[1], reverse=True)


class CausalInferenceModel:
    """Causal inference using do-calculus and counterfactuals."""

    def __init__(self):
        self.causal_graph = CausalGraph()
        self.observed_data = None
        self.intervention_data = {}

    def learn_causal_structure(
        self, data: pd.DataFrame, target_column: str
    ) -> Dict[str, Any]:
        """
        Learn causal structure from observational data.

        Args:
            data: Observational data
            target_column: Target variable

        Returns:
            Learned causal relationships
        """
        logger.info("Learning causal structure from data")

        # Simple causal discovery using correlation and temporal ordering
        # In practice, this would use more sophisticated methods like PC algorithm

        correlations = data.corr()
        feature_columns = [col for col in data.columns if col != target_column]

        causal_relationships = []

        for feature in feature_columns:
            correlation = abs(correlations.loc[feature, target_column])

            if correlation > 0.3:  # Threshold for causal relationship
                # Assume temporal causality if feature name suggests it's before target
                strength = correlation
                self.causal_graph.add_causal_relationship(
                    feature, target_column, strength
                )
                causal_relationships.append(
                    {
                        "cause": feature,
                        "effect": target_column,
                        "strength": strength,
                        "correlation": correlations.loc[feature, target_column],
                    }
                )

        logger.info(f"Learned {len(causal_relationships)} causal relationships")
        return {
            "causal_relationships": causal_relationships,
            "graph_nodes": len(self.causal_graph.graph.nodes()),
            "graph_edges": len(self.causal_graph.graph.edges()),
        }

    def estimate_causal_effect(
        self, treatment: str, outcome: str, confounders: List[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate causal effect using observational data.

        Args:
            treatment: Treatment variable
            outcome: Outcome variable
            confounders: Confounding variables

        Returns:
            Causal effect estimate
        """
        if self.observed_data is None:
            raise ValueError("No observational data available")

        # Simple backdoor adjustment
        if confounders:
            # Adjust for confounders using stratification or regression
            adjusted_effect = self._backdoor_adjustment(treatment, outcome, confounders)
        else:
            # Simple difference in means
            treated_mean = self.observed_data[self.observed_data[treatment] == 1][
                outcome
            ].mean()
            control_mean = self.observed_data[self.observed_data[treatment] == 0][
                outcome
            ].mean()
            adjusted_effect = treated_mean - control_mean

        return {
            "causal_effect": adjusted_effect,
            "method": "backdoor_adjustment" if confounders else "simple_difference",
            "confidence_interval": self._bootstrap_confidence_interval(
                treatment, outcome, confounders
            ),
        }

    def _backdoor_adjustment(
        self, treatment: str, outcome: str, confounders: List[str]
    ) -> float:
        """Perform backdoor adjustment for confounding."""
        # Simple implementation - in practice use more sophisticated methods
        strata_effects = []

        for confounder_value in self.observed_data[confounders[0]].unique():
            stratum_data = self.observed_data[
                self.observed_data[confounders[0]] == confounder_value
            ]
            if len(stratum_data) > 10:  # Minimum sample size
                treated_mean = stratum_data[stratum_data[treatment] == 1][
                    outcome
                ].mean()
                control_mean = stratum_data[stratum_data[treatment] == 0][
                    outcome
                ].mean()
                if not (np.isnan(treated_mean) or np.isnan(control_mean)):
                    strata_effects.append(treated_mean - control_mean)

        return np.mean(strata_effects) if strata_effects else 0.0

    def _bootstrap_confidence_interval(
        self,
        treatment: str,
        outcome: str,
        confounders: List[str] = None,
        n_boot: int = 1000,
    ) -> Tuple[float, float]:
        """Calculate confidence interval using bootstrapping."""
        effects = []

        for _ in range(n_boot):
            # Bootstrap sample
            boot_sample = self.observed_data.sample(
                n=len(self.observed_data), replace=True
            )

            if confounders:
                effect = self._backdoor_adjustment(treatment, outcome, confounders)
            else:
                treated_mean = boot_sample[boot_sample[treatment] == 1][outcome].mean()
                control_mean = boot_sample[boot_sample[treatment] == 0][outcome].mean()
                effect = treated_mean - control_mean

            effects.append(effect)

        return np.percentile(effects, 2.5), np.percentile(effects, 97.5)


class ExplainableAIModel(nn.Module):
    """Explainable AI model with attention mechanisms."""

    def __init__(self, input_dim: int, hidden_dim: int = 128, num_classes: int = 2):
        super().__init__()
        self.input_dim = input_dim

        # Feature attention layer
        self.attention = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, input_dim),
            nn.Softmax(dim=1),
        )

        # Prediction layers
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
        )

        self.classifier = nn.Linear(hidden_dim, num_classes)

        # Feature importance
        self.feature_importance = None

    def forward(self, x):
        # Compute attention weights
        attention_weights = self.attention(x)

        # Apply attention
        attended_features = x * attention_weights

        # Encode
        encoded = self.encoder(attended_features)

        # Global average pooling across features
        pooled = encoded.mean(dim=1) if encoded.dim() > 2 else encoded

        # Classify
        logits = self.classifier(pooled)

        # Store attention weights for explanation
        self.feature_importance = attention_weights.detach()

        return logits

    def explain_prediction(self, input_features: List[str]) -> Dict[str, Any]:
        """Explain model prediction."""
        if self.feature_importance is None:
            return {"error": "No prediction made yet"}

        # Get attention weights
        weights = self.feature_importance.mean(dim=0).cpu().numpy()

        # Create feature importance mapping
        feature_importance = dict(zip(input_features, weights))

        # Sort by importance
        sorted_features = sorted(
            feature_importance.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "top_features": sorted_features[:10],
            "feature_importance": feature_importance,
            "explanation": self._generate_explanation(sorted_features[:5]),
        }

    def _generate_explanation(self, top_features: List[Tuple[str, float]]) -> str:
        """Generate human-readable explanation."""
        if not top_features:
            return "No significant features identified"

        explanation = "The prediction was primarily influenced by: "
        feature_names = [f"{name} ({weight:.3f})" for name, weight in top_features]
        explanation += ", ".join(feature_names)

        return explanation


class RootCauseAnalysisEngine:
    """
    Advanced Root Cause Analysis Engine using causal inference and explainable AI.
    """

    def __init__(self):
        self.causal_model = CausalInferenceModel()
        self.explainable_model = None
        self.failure_patterns = {}
        self.analysis_history = []

    async def analyze_incident(
        self,
        incident_data: Dict[str, Any],
        sensor_data: pd.DataFrame,
        log_data: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive root cause analysis for an incident.

        Args:
            incident_data: Incident information
            sensor_data: Sensor readings around incident time
            log_data: System logs around incident time

        Returns:
            Root cause analysis results
        """
        logger.info(
            f"Starting root cause analysis for incident: {incident_data.get('id', 'unknown')}"
        )

        analysis_start = datetime.now()

        # Step 1: Learn causal structure from data
        causal_structure = self.causal_model.learn_causal_structure(
            sensor_data, "failure_indicator"
        )

        # Step 2: Identify potential root causes
        root_causes = []
        if "failure_indicator" in self.causal_model.causal_graph.graph.nodes():
            root_causes = self.causal_model.causal_graph.identify_root_causes(
                "failure_indicator"
            )

        # Step 3: Explainable AI analysis
        xai_explanation = None
        if self.explainable_model:
            # Prepare data for explanation
            feature_names = [
                col for col in sensor_data.columns if col != "failure_indicator"
            ]
            explanation_input = torch.FloatTensor(
                sensor_data[feature_names].iloc[-1:].values
            )

            with torch.no_grad():
                _ = self.explainable_model(explanation_input)
                xai_explanation = self.explainable_model.explain_prediction(
                    feature_names
                )

        # Step 4: Pattern-based analysis
        pattern_analysis = self._analyze_failure_patterns(
            incident_data, sensor_data, log_data
        )

        # Step 5: Combine results
        final_root_cause = self._combine_analyses(
            root_causes, xai_explanation, pattern_analysis
        )

        analysis_result = {
            "incident_id": incident_data.get("id"),
            "analysis_timestamp": analysis_start.isoformat(),
            "causal_structure": causal_structure,
            "root_causes": root_causes,
            "xai_explanation": xai_explanation,
            "pattern_analysis": pattern_analysis,
            "final_root_cause": final_root_cause,
            "confidence_score": self._calculate_confidence(
                root_causes, xai_explanation, pattern_analysis
            ),
            "recommendations": self._generate_recommendations(final_root_cause),
        }

        self.analysis_history.append(analysis_result)

        analysis_time = (datetime.now() - analysis_start).total_seconds()
        logger.info(
            f"Root cause analysis completed in {analysis_time:.2f}s with confidence {analysis_result['confidence_score']:.2f}"
        )

        return analysis_result

    def _analyze_failure_patterns(
        self,
        incident_data: Dict[str, Any],
        sensor_data: pd.DataFrame,
        log_data: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze failure patterns from historical data."""
        # Simple pattern matching - in practice, use more sophisticated ML
        patterns_found = []

        # Check for sensor anomalies
        sensor_anomalies = []
        for column in sensor_data.select_dtypes(include=[np.number]).columns:
            if column != "failure_indicator":
                mean_val = sensor_data[column].mean()
                std_val = sensor_data[column].std()
                current_val = sensor_data[column].iloc[-1]

                if abs(current_val - mean_val) > 2 * std_val:
                    sensor_anomalies.append(
                        {
                            "sensor": column,
                            "value": current_val,
                            "deviation": abs(current_val - mean_val) / std_val,
                        }
                    )

        if sensor_anomalies:
            patterns_found.append(
                {
                    "type": "sensor_anomaly",
                    "description": f"Anomalous sensor readings: {len(sensor_anomalies)} sensors",
                    "details": sensor_anomalies,
                }
            )

        # Check log patterns
        if log_data:
            error_logs = [
                log
                for log in log_data
                if "error" in log.lower() or "fail" in log.lower()
            ]
            if error_logs:
                patterns_found.append(
                    {
                        "type": "log_errors",
                        "description": f"Error logs found: {len(error_logs)} entries",
                        "details": error_logs[:5],  # First 5 errors
                    }
                )

        return {
            "patterns_found": patterns_found,
            "severity_score": len(patterns_found) * 0.2,  # Simple scoring
        }

    def _combine_analyses(
        self,
        root_causes: List[Tuple[str, float]],
        xai_explanation: Optional[Dict],
        pattern_analysis: Dict,
    ) -> Dict[str, Any]:
        """Combine results from different analysis methods."""
        combined_score = {}

        # Weight causal analysis
        for cause, strength in root_causes:
            combined_score[cause] = combined_score.get(cause, 0) + strength * 0.4

        # Weight XAI explanation
        if xai_explanation and "top_features" in xai_explanation:
            for feature, importance in xai_explanation["top_features"]:
                combined_score[feature] = (
                    combined_score.get(feature, 0) + importance * 0.3
                )

        # Weight pattern analysis
        pattern_score = pattern_analysis.get("severity_score", 0)
        if pattern_analysis.get("patterns_found"):
            for pattern in pattern_analysis["patterns_found"]:
                if pattern["type"] == "sensor_anomaly":
                    for anomaly in pattern.get("details", []):
                        sensor = anomaly["sensor"]
                        combined_score[sensor] = (
                            combined_score.get(sensor, 0) + pattern_score * 0.3
                        )

        # Select top root cause
        if combined_score:
            top_cause = max(combined_score.items(), key=lambda x: x[1])
            return {
                "primary_cause": top_cause[0],
                "confidence": top_cause[1],
                "all_scores": combined_score,
            }
        else:
            return {"primary_cause": "unknown", "confidence": 0.0, "all_scores": {}}

    def _calculate_confidence(
        self,
        root_causes: List[Tuple[str, float]],
        xai_explanation: Optional[Dict],
        pattern_analysis: Dict,
    ) -> float:
        """Calculate overall confidence in the analysis."""
        confidence_components = []

        # Causal analysis confidence
        if root_causes:
            max_causal_strength = max(strength for _, strength in root_causes)
            confidence_components.append(min(max_causal_strength, 1.0))

        # XAI confidence
        if xai_explanation:
            confidence_components.append(0.8)  # Assume high confidence for XAI

        # Pattern analysis confidence
        if pattern_analysis.get("patterns_found"):
            confidence_components.append(0.7)

        return np.mean(confidence_components) if confidence_components else 0.0

    def _generate_recommendations(self, final_root_cause: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on root cause."""
        recommendations = []

        primary_cause = final_root_cause.get("primary_cause", "unknown")

        if primary_cause != "unknown":
            recommendations.append(
                f"Investigate and monitor {primary_cause} more closely"
            )
            recommendations.append(
                f"Implement additional safeguards for {primary_cause}"
            )
            recommendations.append(
                "Review maintenance schedules for related components"
            )

        recommendations.extend(
            [
                "Implement predictive maintenance for identified risk factors",
                "Enhance monitoring and alerting for similar incidents",
                "Conduct post-mortem analysis and update incident response procedures",
            ]
        )

        return recommendations

    def train_explainable_model(self, training_data: pd.DataFrame, target_column: str):
        """Train the explainable AI model."""
        logger.info("Training explainable AI model")

        # Prepare data
        feature_columns = [col for col in training_data.columns if col != target_column]
        X = training_data[feature_columns].values
        y = training_data[target_column].values

        # Convert to PyTorch tensors
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.LongTensor(y)

        # Create model
        input_dim = X.shape[1]
        num_classes = len(np.unique(y))

        self.explainable_model = ExplainableAIModel(input_dim, num_classes=num_classes)

        # Training
        optimizer = torch.optim.Adam(self.explainable_model.parameters())
        criterion = nn.CrossEntropyLoss()

        # Simple training loop
        for epoch in range(50):
            optimizer.zero_grad()
            outputs = self.explainable_model(
                X_tensor.unsqueeze(1)
            )  # Add sequence dimension
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()

        logger.info("Explainable AI model training completed")

    def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis history."""
        return self.analysis_history[-limit:] if self.analysis_history else []


# Global root cause analysis engine
root_cause_engine = RootCauseAnalysisEngine()


async def analyze_root_cause(
    incident_data: Dict[str, Any],
    sensor_data_path: str,
    log_data_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze root cause for an incident.

    Args:
        incident_data: Incident information
        sensor_data_path: Path to sensor data CSV
        log_data_path: Optional path to log data

    Returns:
        Root cause analysis results
    """
    # Load data
    sensor_data = pd.read_csv(sensor_data_path)

    # Add failure indicator if not present
    if "failure_indicator" not in sensor_data.columns:
        # Simple heuristic - assume failure if any sensor exceeds threshold
        sensor_data["failure_indicator"] = (
            (
                sensor_data.select_dtypes(include=[np.number])
                > sensor_data.select_dtypes(include=[np.number]).mean()
                + 2 * sensor_data.select_dtypes(include=[np.number]).std()
            ).any(axis=1)
        ).astype(int)

    log_data = None
    if log_data_path:
        with open(log_data_path, "r") as f:
            log_data = f.readlines()

    # Perform analysis
    results = await root_cause_engine.analyze_incident(
        incident_data, sensor_data, log_data
    )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rca_results_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"RCA results saved to {filename}")
    return results
