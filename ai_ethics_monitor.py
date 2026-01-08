"""
AI Ethics Monitor Module

This module implements comprehensive AI ethics monitoring including fairness assessment,
bias detection, and ethical concern evaluation for AI models.
"""

import json
import logging
import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from utils.logging_config import get_logger

logger = get_logger(__name__)


class AIEthicsMonitor:
    """Comprehensive AI ethics monitoring system."""
    
    def __init__(self, protected_attributes: Optional[List[str]] = None):
        self.protected_attributes = protected_attributes or []
        self.fairness_metrics = {}
        self.bias_checks = []
        self.ethical_concerns = []
        
    def assess_model_fairness(
        self,
        model,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        predictions: np.ndarray,
        protected_attribute: str
    ) -> Dict[str, Any]:
        """Assess model fairness for a protected attribute."""
        if protected_attribute not in X_test.columns:
            return {"error": f"Protected attribute {protected_attribute} not found"}
        
        fairness_results = {
            "attribute": protected_attribute,
            "groups": {},
            "overall_fairness_score": 1.0
        }
        
        # Group by protected attribute
        unique_groups = X_test[protected_attribute].unique()
        
        for group in unique_groups:
            group_mask = X_test[protected_attribute] == group
            group_y_true = y_test[group_mask]
            group_y_pred = predictions[group_mask]
            
            if len(group_y_true) > 0:
                group_metrics = {
                    "accuracy": accuracy_score(group_y_true, group_y_pred),
                    "precision": precision_score(group_y_true, group_y_pred, average='weighted', zero_division=0),
                    "recall": recall_score(group_y_true, group_y_pred, average='weighted', zero_division=0),
                    "f1": f1_score(group_y_true, group_y_pred, average='weighted', zero_division=0),
                    "sample_size": len(group_y_true)
                }
                fairness_results["groups"][str(group)] = group_metrics
        
        # Calculate fairness metrics
        if len(fairness_results["groups"]) > 1:
            accuracies = [g["accuracy"] for g in fairness_results["groups"].values()]
            fairness_results["accuracy_disparity"] = max(accuracies) - min(accuracies)
            fairness_results["overall_fairness_score"] = 1.0 - fairness_results["accuracy_disparity"]
        
        self.fairness_metrics[protected_attribute] = fairness_results
        return fairness_results
    
    def detect_bias_in_predictions(
        self,
        predictions: np.ndarray,
        protected_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Detect bias patterns in predictions."""
        bias_results = {
            "statistical_parity": {},
            "disparate_impact": {},
            "overall_bias_score": 0.0
        }
        
        if protected_data is None or protected_data.empty:
            return bias_results
        
        for column in protected_data.columns:
            if protected_data[column].dtype in ['object', 'category']:
                unique_groups = protected_data[column].unique()
                group_rates = {}
                
                for group in unique_groups:
                    group_mask = protected_data[column] == group
                    if group_mask.sum() > 0:
                        group_predictions = predictions[group_mask]
                        positive_rate = np.mean(group_predictions > 0.5) if len(group_predictions) > 0 else 0
                        group_rates[str(group)] = positive_rate
                
                if len(group_rates) > 1:
                    rates = list(group_rates.values())
                    max_rate = max(rates)
                    min_rate = min(rates)
                    
                    bias_results["statistical_parity"][column] = max_rate - min_rate
                    bias_results["disparate_impact"][column] = max_rate / min_rate if min_rate > 0 else float('inf')
        
        # Calculate overall bias score
        all_disparities = list(bias_results["statistical_parity"].values())
        if all_disparities:
            bias_results["overall_bias_score"] = np.mean(all_disparities)
        
        self.bias_checks.append(bias_results)
        return bias_results
    
    def assess_ethical_concerns(
        self,
        model_info: Dict[str, Any],
        predictions: np.ndarray,
        sensitive_data: Optional[bool] = False
    ) -> Dict[str, Any]:
        """Assess ethical concerns in model usage."""
        ethical_assessment = {
            "timestamp": datetime.now().isoformat(),
            "concerns": [],
            "risk_level": "low",
            "recommendations": []
        }
        
        # Check for high-stakes decisions
        high_stakes_indicators = [
            "healthcare", "finance", "criminal", "employment",
            "housing", "insurance", "credit"
        ]
        
        model_purpose = model_info.get("purpose", "").lower()
        is_high_stakes = any(indicator in model_purpose for indicator in high_stakes_indicators)
        
        if is_high_stakes:
            ethical_assessment["concerns"].append({
                "type": "high_stakes_decisions",
                "description": "Model used for high-stakes decisions requiring careful ethical consideration",
                "severity": "high"
            })
        
        # Check prediction distribution
        pred_stats = {
            "mean": np.mean(predictions),
            "std": np.std(predictions),
            "min": np.min(predictions),
            "max": np.max(predictions)
        }
        
        # Check for extreme predictions
        extreme_threshold = pred_stats["mean"] + 3 * pred_stats["std"]
        extreme_predictions = np.sum(predictions > extreme_threshold)
        
        if extreme_predictions > len(predictions) * 0.01:  # More than 1%
            ethical_assessment["concerns"].append({
                "type": "extreme_predictions",
                "description": f"Model produces {extreme_predictions} extreme predictions (>3σ)",
                "severity": "medium"
            })
        
        # Check for sensitive data handling
        if sensitive_data:
            ethical_assessment["concerns"].append({
                "type": "sensitive_data",
                "description": "Model handles sensitive personal data",
                "severity": "high"
            })
        
        # Determine overall risk level
        high_concerns = sum(1 for c in ethical_assessment["concerns"] if c["severity"] == "high")
        medium_concerns = sum(1 for c in ethical_assessment["concerns"] if c["severity"] == "medium")
        
        if high_concerns > 0:
            ethical_assessment["risk_level"] = "high"
        elif medium_concerns > 1:
            ethical_assessment["risk_level"] = "medium"
        
        # Generate recommendations
        if ethical_assessment["risk_level"] == "high":
            ethical_assessment["recommendations"].extend([
                "Implement human oversight for high-risk decisions",
                "Conduct thorough ethical impact assessment",
                "Consider alternative decision-making approaches"
            ])
        elif ethical_assessment["risk_level"] == "medium":
            ethical_assessment["recommendations"].extend([
                "Add transparency measures and explainability",
                "Implement regular ethical audits",
                "Consider bias mitigation techniques"
            ])
        
        # Store ethical concerns
        self.ethical_concerns.extend(ethical_assessment["concerns"])
        
        logger.info(f"Ethical assessment completed: {len(ethical_assessment['concerns'])} concerns, risk={ethical_assessment['risk_level']}")
        
        return ethical_assessment
    
    def generate_ethics_report(self) -> Dict[str, Any]:
        """Generate comprehensive ethics report."""
        report = {
            "ethics_report": {
                "generated_at": datetime.now().isoformat(),
                "fairness_assessments": self.fairness_metrics,
                "bias_detections": self.bias_checks,
                "ethical_concerns": self.ethical_concerns,
                "overall_risk_assessment": self._assess_overall_risk(),
                "recommendations": self._generate_ethics_recommendations()
            }
        }
        
        return report
    
    def _assess_overall_risk(self) -> str:
        """Assess overall ethical risk."""
        high_risks = 0
        medium_risks = 0
        
        # Count fairness issues
        for assessment in self.fairness_metrics.values():
            score = assessment.get("overall_fairness_score", 1.0)
            if score < 0.5:
                high_risks += 1
            elif score < 0.7:
                medium_risks += 1
        
        # Count ethical concerns
        for concern in self.ethical_concerns:
            if concern["severity"] == "high":
                high_risks += 1
            elif concern["severity"] == "medium":
                medium_risks += 1
        
        if high_risks > 0:
            return "high"
        elif medium_risks > 2:
            return "medium"
        elif medium_risks > 0:
            return "low"
        else:
            return "minimal"
    
    def _generate_ethics_recommendations(self) -> List[str]:
        """Generate ethics recommendations."""
        recommendations = [
            "Conduct regular fairness audits",
            "Implement bias monitoring in production",
            "Document ethical considerations and mitigations",
            "Provide transparency in AI decision-making",
            "Establish ethical review processes"
        ]
        
        risk = self._assess_overall_risk()
        if risk == "high":
            recommendations.extend([
                "Pause deployment until ethical concerns are addressed",
                "Engage ethics experts for review",
                "Consider alternative approaches with lower ethical risk"
            ])
        elif risk == "medium":
            recommendations.extend([
                "Implement additional monitoring and controls",
                "Develop mitigation strategies for identified issues",
                "Increase transparency and explainability"
            ])
        
        return recommendations
    
    def save_ethics_report(self, filepath: str):
        """Save ethics report to file."""
        report = self.generate_ethics_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Ethics report saved to {filepath}")


# Global ethics monitor instance
ethics_monitor = AIEthicsMonitor()


def assess_model_ethics(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    predictions: np.ndarray,
    protected_attributes: Optional[List[str]] = None,
    model_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Comprehensive ethics assessment for a model.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test targets
        predictions: Model predictions
        protected_attributes: List of protected attributes
        model_info: Model information
    
    Returns:
        Ethics assessment results
    """
    monitor = AIEthicsMonitor(protected_attributes)
    
    results = {
        "fairness_assessments": {},
        "bias_detection": {},
        "ethical_assessment": {},
        "overall_summary": {}
    }
    
    # Assess fairness for each protected attribute
    for attr in monitor.protected_attributes:
        if attr in X_test.columns:
            fairness = monitor.assess_model_fairness(model, X_test, y_test, predictions, attr)
            results["fairness_assessments"][attr] = fairness
    
    # Detect bias patterns
    bias_results = monitor.detect_bias_in_predictions(predictions, X_test[monitor.protected_attributes])
    results["bias_detection"] = bias_results
    
    # Assess ethical concerns
    ethical_results = monitor.assess_ethical_concerns(
        model_info or {},
        predictions,
        X_test[monitor.protected_attributes] if monitor.protected_attributes else None
    )
    results["ethical_assessment"] = ethical_results
    
    # Generate summary
    results["overall_summary"] = monitor.generate_ethics_report()["ethics_report"]
    
    return results
