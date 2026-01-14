"""
AI Ethics Monitor Module

This module provides a comprehensive framework for AI ethics monitoring, including:
1.  LLM Guardrails: Pre-analysis of prompts and post-analysis of responses for
    risks like toxicity, bias triggers, and jailbreak attempts.
2.  Classical ML Fairness Auditing: A simulation environment to audit a
    classification model (e.g., for loan approvals) for fairness issues like
    disparate impact across protected demographic groups.
"""

import json
import logging
import re
import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Core AIEthicsMonitor Class (Existing Logic) ---

class AIEthicsMonitor:
    """Comprehensive AI ethics monitoring system."""
    
    def __init__(self, protected_attributes: Optional[List[str]] = None):
        self.protected_attributes = protected_attributes or []
        self.fairness_metrics = {}
        self.bias_checks = []
        self.ethical_concerns = []

    def analyze_prompt_for_risks(self, prompt: str) -> Dict[str, Any]:
        """Analyzes an input prompt for potential ethical risks before sending it to an LLM."""
        risks = []
        prompt_lower = prompt.lower()
        bias_keywords = {'gender': ['man', 'woman'], 'race': ['asian', 'black', 'white']}
        for bias_type, keywords in bias_keywords.items():
            if any(re.search(r'\b' + kw + r'\b', prompt_lower) for kw in keywords):
                risks.append({"type": f"potential_{bias_type}_bias_trigger", "severity": "low"})
        toxic_keywords = ['kill', 'hate', 'stupid']
        if any(re.search(r'\b' + kw + r'\b', prompt_lower) for kw in toxic_keywords):
            risks.append({"type": "potential_toxicity", "severity": "medium"})
        jailbreak_patterns = ["ignore all previous instructions"]
        if any(p in prompt_lower for p in jailbreak_patterns):
            risks.append({"type": "jailbreak_attempt", "severity": "high"})
        risk_level = "low"
        if any(r['severity'] == 'high' for r in risks): risk_level = "high"
        elif any(r['severity'] == 'medium' for r in risks): risk_level = "medium"
        return {"prompt": prompt, "detected_risks": risks, "overall_risk_level": risk_level}

    def analyze_llm_response(self, response: str, prompt_risks: Dict) -> Dict[str, Any]:
        """Analyzes an LLM's response for ethical concerns."""
        concerns = []
        response_lower = response.lower()
        harmful_phrases = ["i hate", "how to build a bomb"]
        if any(p in response_lower for p in harmful_phrases):
            concerns.append({"type": "harmful_content_generated", "severity": "high"})
        if any("bias_trigger" in r['type'] for r in prompt_risks.get("detected_risks", [])):
            if re.search(r'\b' + "stereotype" + r'\b', response_lower):
                 concerns.append({"type": "biased_statement", "severity": "medium"})
        risk_level = "low"
        if any(c['severity'] == 'high' for c in concerns): risk_level = "high"
        report = {"response": response, "detected_concerns": concerns, "response_risk_level": risk_level}
        self.ethical_concerns.extend(concerns)
        return report

    def assess_model_fairness(self, X_test: pd.DataFrame, y_test: pd.Series, predictions: np.ndarray, protected_attribute: str) -> Dict[str, Any]:
        """Assess model fairness for a protected attribute. (Simplified for simulation)"""
        # This is a placeholder for a real implementation
        pass

    def detect_bias_in_predictions(self, predictions: np.ndarray, protected_data: pd.DataFrame) -> Dict[str, Any]:
        """Detects bias by calculating disparate impact."""
        bias_results = {"disparate_impact": {}}
        for column in protected_data.columns:
            if protected_data[column].dtype in ['object', 'category']:
                unique_groups = protected_data[column].unique()
                group_rates = {}
                for group in unique_groups:
                    mask = protected_data[column] == group
                    group_predictions = predictions[mask]
                    group_rates[group] = np.mean(group_predictions) if len(group_predictions) > 0 else 0
                
                if group_rates:
                    privileged_group = max(group_rates, key=group_rates.get)
                    privileged_rate = group_rates[privileged_group]
                    
                    di_scores = {}
                    for group, rate in group_rates.items():
                        if group != privileged_group:
                            di_scores[f"{group}_vs_{privileged_group}"] = rate / privileged_rate if privileged_rate > 0 else float('inf')
                    bias_results["disparate_impact"][column] = di_scores
        
        self.bias_checks.append(bias_results)
        return bias_results
    
    def assess_ethical_concerns(self, model_info: Dict, predictions: np.ndarray) -> Dict[str, Any]:
        """Assess ethical concerns like high-stakes usage."""
        assessment = {"concerns": [], "risk_level": "low"}
        if "credit" in model_info.get("purpose", "").lower():
            assessment["concerns"].append({
                "type": "high_stakes_application",
                "description": "Model is used for credit scoring, a high-stakes financial decision.",
                "severity": "high"
            })
            assessment["risk_level"] = "high"
        self.ethical_concerns.extend(assessment["concerns"])
        return assessment

    def generate_ethics_report(self, report_title: str) -> Dict[str, Any]:
        """Generate a comprehensive ethics report."""
        report = {
            "title": report_title,
            "generated_at": datetime.now().isoformat(),
            "fairness_metrics": self.fairness_metrics,
            "bias_detections": self.bias_checks,
            "ethical_concerns": self.ethical_concerns,
        }
        return {"ethics_report": report}

    def save_ethics_report(self, filepath: str, report_title: str):
        report = self.generate_ethics_report(report_title)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Ethics report '{report_title}' saved to {filepath}")

# --- NEW: Credit Approval Simulation Layer ---

class SimulatedLoanModel:
    """A simulated loan approval model with built-in bias."""
    def __init__(self, bias_factor: float = 0.2):
        self.bias_factor = bias_factor
        logger.info(f"SimulatedLoanModel initialized with bias_factor: {bias_factor}")

    def predict(self, data: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Predicts loan approval (1 for approved, 0 for denied).
        This model is intentionally biased against 'Group_B'.
        """
        predictions = []
        explanations = []

        for _, row in data.iterrows():
            # Base approval score on financial health
            score = 0
            if row['credit_score'] > 650: score += 0.4
            if row['income'] > 50000: score += 0.4
            if row['debt_to_income_ratio'] < 0.4: score += 0.2

            # Apply bias: systematically penalize 'Group_B'
            if row['ethnicity'] == 'Group_B':
                score -= self.bias_factor

            # Decision and explanation
            if score >= 0.7:
                predictions.append(1)
                explanations.append("APPROVED: Strong financial profile.")
            else:
                predictions.append(0)
                reason = "High debt ratio." if row['debt_to_income_ratio'] >= 0.4 else "Low credit score or income."
                explanations.append(f"DENIED: {reason}")

        return np.array(predictions), explanations

class CreditApprovalSimulation:
    """Manages the simulation of generating data, running the model, and auditing."""
    def __init__(self, num_samples: int = 1000):
        self.num_samples = num_samples
        self.data: Optional[pd.DataFrame] = None
        self.model = SimulatedLoanModel(bias_factor=0.25)
        self.monitor = AIEthicsMonitor(protected_attributes=['ethnicity'])

    def _generate_biased_data(self):
        """Generates applicant data with built-in correlations that can lead to bias."""
        np.random.seed(42)
        data = {
            'credit_score': np.random.randint(500, 850, self.num_samples),
            'income': np.random.randint(30000, 150000, self.num_samples),
            'debt_to_income_ratio': np.random.uniform(0.1, 0.7, self.num_samples),
            'ethnicity': np.random.choice(['Group_A', 'Group_B'], self.num_samples, p=[0.7, 0.3])
        }
        df = pd.DataFrame(data)

        # Introduce bias: Group_B has a systematically lower average income
        df.loc[df['ethnicity'] == 'Group_B', 'income'] = (df.loc[df['ethnicity'] == 'Group_B', 'income'] * 0.8).astype(int)
        logger.info("Generated biased dataset for simulation.")
        self.data = df

    def run(self):
        """Runs the full simulation and audit process."""
        logger.info("\n--- Starting Credit Approval Fairness Audit Simulation ---")
        self._generate_biased_data()

        # 1. Get model predictions and explanations
        predictions, explanations = self.model.predict(self.data)
        self.data['predicted_approval'] = predictions
        self.data['explanation'] = explanations

        logger.info("Sample of model decisions:")
        print(self.data.head())

        # 2. Use the AIEthicsMonitor to detect bias
        logger.info("\nRunning bias detection...")
        bias_report = self.monitor.detect_bias_in_predictions(predictions, self.data[['ethnicity']])
        print(json.dumps(bias_report, indent=2))

        # Check for disparate impact (e.g., if the approval rate for one group is less than 80% of another)
        di_score = bias_report['disparate_impact']['ethnicity']['Group_B_vs_Group_A']
        if di_score < 0.8:
            logger.warning(f"DISPARATE IMPACT DETECTED! Score: {di_score:.2f} (below 0.8 threshold)")
            self.monitor.ethical_concerns.append({
                "type": "disparate_impact",
                "description": f"Approval rate for Group_B is only {di_score:.2f} of the rate for Group_A.",
                "severity": "high"
            })

        # 3. Assess overall ethical concerns
        logger.info("\nAssessing overall ethical concerns...")
        model_info = {"purpose": "credit_approval_finance"}
        concerns_report = self.monitor.assess_ethical_concerns(model_info, predictions)
        print(json.dumps(concerns_report, indent=2))

        # 4. Generate and save the final, consolidated report
        logger.info("\nGenerating final ethics report...")
        self.monitor.save_ethics_report("credit_model_ethics_report.json", "Credit Approval Model Fairness Audit")

if __name__ == '__main__':
    # --- Part 1: Demo of LLM Guardrails (existing demo) ---
    llm_monitor = AIEthicsMonitor()
    print("--- 1. Analyzing a safe prompt ---")
    safe_prompt = "Explain the theory of relativity."
    print(llm_monitor.analyze_prompt_for_risks(safe_prompt))
    print(llm_monitor.analyze_llm_response("It's about space and time.", {}))

    print("\n--- 2. Analyzing a risky prompt ---")
    biased_prompt = "Why are men better at programming?"
    print(llm_monitor.analyze_prompt_for_risks(biased_prompt))
    print(llm_monitor.analyze_llm_response("It's a stereotype.", {"detected_risks": [{"type": "bias_trigger"}]}))

    llm_monitor.save_ethics_report("llm_ethics_report.json", "LLM Interaction Audit")

    # --- Part 2: NEW Demo of Classical ML Fairness Audit ---
    simulation = CreditApprovalSimulation()
    simulation.run()
