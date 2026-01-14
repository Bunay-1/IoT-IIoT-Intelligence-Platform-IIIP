"""
Module: AI Explanation Layer using SHAP

This module provides a complete, end-to-end demonstration of generating
interpretable explanations for a machine learning model's decisions using the
SHAP (SHapley Additive exPlanations) technique. It trains a model to predict
customer churn and then explains individual predictions.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import shap
import logging
from typing import List, Dict, Optional

# Use a basic logger for this standalone example
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChurnPredictionExplainer:
    """
    Orchestrates the process of training a churn prediction model and
    generating SHAP explanations for its predictions.
    """
    def __init__(self, num_samples: int = 1000):
        self.num_samples = num_samples
        self.data: pd.DataFrame = None
        self.model: RandomForestClassifier = None
        self.explainer: shap.TreeExplainer = None
        self.features: List[str] = []

        self._prepare_environment()

    def _prepare_environment(self):
        """Generates data, trains the model, and initializes the SHAP explainer."""
        logger.info("Preparing explanation environment...")
        self._generate_synthetic_data()
        self._train_model()
        self._initialize_shap_explainer()
        logger.info("Environment ready. Model trained and SHAP explainer initialized.")

    def _generate_synthetic_data(self):
        """
        Creates a synthetic dataset for a customer churn prediction scenario.
        """
        logger.info(f"Generating {self.num_samples} synthetic customer profiles...")
        np.random.seed(42)

        data = {
            'tenure': np.random.randint(1, 73, self.num_samples),
            'monthly_charges': np.random.uniform(20, 120, self.num_samples),
            'contract_type': np.random.choice(['Month-to-month', 'One year', 'Two year'], self.num_samples, p=[0.6, 0.2, 0.2]),
            'total_charges': None, # Will be calculated
            'churn': 0 # Target variable
        }
        self.data = pd.DataFrame(data)

        # Calculate total charges with some noise
        self.data['total_charges'] = self.data['tenure'] * self.data['monthly_charges'] + np.random.uniform(-100, 100, self.num_samples)
        self.data['total_charges'] = self.data['total_charges'].clip(lower=0)

        # Create a churn rule
        # High churn for short tenure, high monthly charges, and month-to-month contracts
        churn_probability = (
            -0.1 * (self.data['tenure'] / 12) +
            0.2 * (self.data['monthly_charges'] / 100) +
            (self.data['contract_type'] == 'Month-to-month') * 0.4 +
            np.random.normal(0, 0.1, self.num_samples) # noise
        )

        # Convert probability to binary churn label
        churn_threshold = np.percentile(churn_probability, 70) # Target ~30% churn rate
        self.data['churn'] = (churn_probability > churn_threshold).astype(int)

        logger.info(f"Data generation complete. Churn rate: {self.data['churn'].mean():.2%}")

    def _train_model(self):
        """Trains a RandomForestClassifier on the generated data."""
        logger.info("Training churn prediction model...")

        # One-hot encode categorical features
        df_processed = pd.get_dummies(self.data, columns=['contract_type'], drop_first=True)

        X = df_processed.drop('churn', axis=1)
        y = df_processed['churn']
        self.features = X.columns.tolist()

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        self.model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        self.model.fit(X_train, y_train)

        accuracy = self.model.score(X_test, y_test)
        logger.info(f"Model training complete. Accuracy: {accuracy:.2%}")

    def _initialize_shap_explainer(self):
        """Initializes the SHAP explainer for the trained model."""
        if self.model is None:
            raise ValueError("Model must be trained before initializing the SHAP explainer.")

        # SHAP's TreeExplainer is optimized for tree-based models like RandomForest
        self.explainer = shap.TreeExplainer(self.model)
        logger.info("SHAP TreeExplainer initialized.")

    def explain_prediction(self, customer_index: int) -> Optional[Dict]:
        """
        Generates a detailed SHAP explanation for a single customer prediction.

        Args:
            customer_index: The index of the customer in the original dataframe.

        Returns:
            A dictionary containing the prediction and a human-readable explanation, or None if error.
        """
        if customer_index >= len(self.data):
            logger.error(f"Customer index {customer_index} is out of bounds.")
            return None

        # Prepare the specific customer's data (with one-hot encoding)
        customer_data_raw = self.data.iloc[[customer_index]]
        df_processed = pd.get_dummies(customer_data_raw, columns=['contract_type'], drop_first=True)
        customer_data_encoded = df_processed.reindex(columns=self.features, fill_value=0)

        # Get SHAP values for this specific prediction
        shap_values = self.explainer.shap_values(customer_data_encoded)

        # For binary classifiers, shap_values is a list of two arrays (one for each class).
        # We are interested in the explanation for the "Churn" class (class 1).
        if isinstance(shap_values, list) and len(shap_values) > 1:
            shap_values_for_positive_class = shap_values[1]
        else:
            shap_values_for_positive_class = shap_values

        # For a binary classifier, this will have shape (num_samples, num_features, 2).
        # We want the SHAP values for the positive class (Churn), which is at index 1.
        shap_values_for_churn = shap_values_for_positive_class[:, :, 1]

        # Since we are explaining a single prediction, we take the first row.
        shap_values_for_churn = shap_values_for_churn[0]

        # Get the model's prediction probability
        prediction_proba = self.model.predict_proba(customer_data_encoded)[0][1]
        prediction_label = "Churn" if prediction_proba > 0.5 else "No Churn"

        # Create a DataFrame for easier analysis
        feature_names = customer_data_encoded.columns
        feature_values = customer_data_encoded.iloc[0].values
        shap_df = pd.DataFrame({
            'feature': feature_names,
            'value': feature_values,
            'shap_value': shap_values_for_churn
        })

        # Separate features that push the prediction towards churn (positive SHAP)
        # from those that push it towards staying (negative SHAP)
        positive_contributors = shap_df[shap_df['shap_value'] > 0].sort_values('shap_value', ascending=False)
        negative_contributors = shap_df[shap_df['shap_value'] < 0].sort_values('shap_value', ascending=True)

        return {
            "customer_index": customer_index,
            "prediction_label": prediction_label,
            "prediction_probability": prediction_proba,
            "positive_contributors": positive_contributors.to_dict('records'),
            "negative_contributors": negative_contributors.to_dict('records')
        }

    def format_explanation_for_display(self, explanation: Dict) -> str:
        """Formats the SHAP explanation into a human-readable string."""
        report = []
        report.append("="*50)
        report.append(f"AI Decision Explanation for Customer #{explanation['customer_index']}")
        report.append("="*50)
        report.append(f"Prediction: {explanation['prediction_label']} (Probability: {explanation['prediction_probability']:.2%})")
        report.append("\n--- Key Factors ---")

        report.append("\n[+] Factors INCREASING churn risk:")
        if not explanation['positive_contributors']:
            report.append("  - None")
        for item in explanation['positive_contributors'][:3]:
            report.append(f"  - {item['feature']} = {item['value']:.2f} (Contribution: +{item['shap_value']:.3f})")

        report.append("\n[-] Factors DECREASING churn risk:")
        if not explanation['negative_contributors']:
            report.append("  - None")
        for item in explanation['negative_contributors'][:3]:
            report.append(f"  - {item['feature']} = {item['value']:.2f} (Contribution: {item['shap_value']:.3f})")

        report.append("\n" + "="*50)
        return "\n".join(report)


if __name__ == '__main__':
    # Initialize the explainer system (trains model, etc.)
    explainer_service = ChurnPredictionExplainer()

    # Find two interesting cases to explain: one likely to churn, one not
    churn_probabilities = explainer_service.model.predict_proba(
        pd.get_dummies(explainer_service.data, columns=['contract_type'], drop_first=True).drop('churn', axis=1)
    )[:, 1]

    high_churn_risk_customer_idx = np.argmax(churn_probabilities)
    low_churn_risk_customer_idx = np.argmin(churn_probabilities)

    # --- Case 1: High Churn Risk Customer ---
    explanation1 = explainer_service.explain_prediction(high_churn_risk_customer_idx)
    if explanation1:
        print(explainer_service.format_explanation_for_display(explanation1))

    # --- Case 2: Low Churn Risk Customer ---
    explanation2 = explainer_service.explain_prediction(low_churn_risk_customer_idx)
    if explanation2:
        print(explainer_service.format_explanation_for_display(explanation2))

