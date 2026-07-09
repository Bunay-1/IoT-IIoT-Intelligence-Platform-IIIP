"""
Module: Churn Prediction

This module provides a complete workflow for predicting customer churn using a machine learning model.
It includes functionalities for data generation, preprocessing, model training, evaluation,
and prediction.
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

class ChurnPrediction:
    """
    A class to handle the churn prediction workflow.
    """
    def __init__(self, model_path="churn_model.joblib"):
        """
        Initializes the ChurnPrediction class.

        Args:
            model_path (str): The path to save/load the trained model.
        """
        self.model_path = model_path
        self.model = None
        self.preprocessor = None
        self._numeric_features = ['tenure', 'monthly_charges', 'total_charges']
        self._categorical_features = ['gender', 'contract', 'payment_method']

    def _generate_synthetic_data(self, n_samples=1000):
        """
        Generates a synthetic dataset for churn prediction.

        Args:
            n_samples (int): The number of samples to generate.

        Returns:
            pandas.DataFrame: A DataFrame with synthetic customer data.
        """
        print(f"Generating {n_samples} samples of synthetic data...")
        data = {
            'gender': np.random.choice(['Male', 'Female'], n_samples),
            'tenure': np.random.randint(1, 73, n_samples),
            'contract': np.random.choice(['Month-to-month', 'One year', 'Two year'], n_samples),
            'payment_method': np.random.choice(['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)'], n_samples),
            'monthly_charges': np.random.uniform(20, 120, n_samples).round(2),
            'total_charges': lambda df: df['monthly_charges'] * df['tenure'] * np.random.uniform(0.8, 1.2, n_samples),
            'churn': lambda df: (df['monthly_charges'] > 70) | (df['tenure'] < 12)
        }

        df = pd.DataFrame(data)
        # Create total_charges based on other columns
        df['total_charges'] = df['monthly_charges'] * df['tenure'] * np.random.uniform(0.9, 1.1, n_samples)

        # Refine churn logic
        churn_prob = (df['monthly_charges'] / 120) - (df['tenure'] / 72) * 0.5 + np.random.normal(0, 0.1, n_samples)
        df['churn'] = (churn_prob > 0.4).astype(int)

        # Introduce some missing values
        df.loc[df.sample(frac=0.05).index, 'total_charges'] = np.nan

        print("Synthetic data generated successfully.")
        return df

    def _create_preprocessor(self):
        """
        Creates a preprocessing pipeline for numeric and categorical features.
        """
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())])

        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(handle_unknown='ignore'))])

        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, self._numeric_features),
                ('cat', categorical_transformer, self._categorical_features)])

        return self.preprocessor

    def train_model(self, data):
        """
        Trains the churn prediction model.

        Args:
            data (pandas.DataFrame): The input data for training.
        """
        print("Starting model training process...")

        # Handle missing total_charges by imputing with the mean of the tenure group
        data['total_charges'] = data['total_charges'].fillna(data.groupby('tenure')['total_charges'].transform('mean'))
        # If any NaNs still exist (e.g., tenure group had all NaNs), fill with global mean
        if data['total_charges'].isnull().any():
            data['total_charges'] = data['total_charges'].fillna(data['total_charges'].mean())

        X = data.drop('churn', axis=1)
        y = data['churn']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        self.preprocessor = self._create_preprocessor()

        self.model = Pipeline(steps=[('preprocessor', self.preprocessor),
                                     ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))])

        self.model.fit(X_train, y_train)
        print("Model training completed.")

        # Evaluate the model on the test set
        y_pred = self.model.predict(X_test)
        self.evaluate_model(y_test, y_pred)
        self.plot_feature_importance(X_train.columns)


    def evaluate_model(self, y_true, y_pred):
        """
        Evaluates the model and prints classification metrics.

        Args:
            y_true (array-like): The true labels.
            y_pred (array-like): The predicted labels.
        """
        print("\n--- Model Evaluation ---")
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)

        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1-Score: {f1:.4f}")

        # Plot confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['No Churn', 'Churn'], yticklabels=['No Churn', 'Churn'])
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title('Confusion Matrix')
        plot_path = 'churn_confusion_matrix.png'
        plt.savefig(plot_path)
        plt.close()
        print(f"Confusion matrix plot saved to {plot_path}")

    def plot_feature_importance(self, columns):
        """
        Plots the feature importances of the trained model.

        Args:
            columns (list): The list of column names before one-hot encoding.
        """
        if self.model is None or not hasattr(self.model.named_steps['classifier'], 'feature_importances_'):
            print("Model not trained yet. Cannot plot feature importance.")
            return

        # Get feature importances from the classifier
        importances = self.model.named_steps['classifier'].feature_importances_

        # Get feature names from the preprocessor
        ohe_feature_names = self.model.named_steps['preprocessor'].transformers_[1][1]\
            .named_steps['onehot'].get_feature_names_out(self._categorical_features)

        feature_names = self._numeric_features + list(ohe_feature_names)

        feature_importance_df = pd.DataFrame({'feature': feature_names, 'importance': importances})
        feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)

        plt.figure(figsize=(12, 8))
        sns.barplot(x='importance', y='feature', data=feature_importance_df)
        plt.title('Feature Importance')
        plt.tight_layout()
        plot_path = 'churn_feature_importance.png'
        plt.savefig(plot_path)
        plt.close()
        print(f"Feature importance plot saved to {plot_path}")


    def predict_churn(self, new_data):
        """
        Predicts churn for new customer data.

        Args:
            new_data (pandas.DataFrame): A DataFrame with new customer data.

        Returns:
            numpy.ndarray: An array of predictions (1 for churn, 0 for no churn).
        """
        if self.model is None:
            raise RuntimeError("Model is not trained. Please train the model before making predictions.")

        print("\nPredicting churn for new data...")
        predictions = self.model.predict(new_data)
        probabilities = self.model.predict_proba(new_data)[:, 1] # Probability of churn

        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            print(f"Customer {i+1}: Predicted Churn = {'Yes' if pred == 1 else 'No'}, Probability = {prob:.2f}")

        return predictions

    def save_model(self):
        """Saves the trained model to a file."""
        if self.model:
            print(f"Saving model to {self.model_path}...")
            joblib.dump(self.model, self.model_path)
            print("Model saved successfully.")
        else:
            print("No model to save.")

    def load_model(self):
        """Loads a trained model from a file."""
        if os.path.exists(self.model_path):
            print(f"Loading model from {self.model_path}...")
            self.model = joblib.load(self.model_path)
            print("Model loaded successfully.")
        else:
            print(f"No model found at {self.model_path}.")

if __name__ == "__main__":
    # Initialize the churn prediction system
    churn_predictor = ChurnPrediction(model_path="churn_model_v1.joblib")

    # Generate synthetic data
    customer_data = churn_predictor._generate_synthetic_data(n_samples=2000)

    # Train the model
    churn_predictor.train_model(customer_data)

    # Save the trained model
    churn_predictor.save_model()

    # --- Example of loading and predicting ---
    # Create a new instance to simulate a different process/day
    new_churn_predictor = ChurnPrediction(model_path="churn_model_v1.joblib")
    new_churn_predictor.load_model()

    # Create some new sample data for prediction
    new_customers = pd.DataFrame({
        'gender': ['Female', 'Male', 'Male'],
        'tenure': [1, 5, 60],
        'contract': ['Month-to-month', 'One year', 'Two year'],
        'payment_method': ['Electronic check', 'Mailed check', 'Credit card (automatic)'],
        'monthly_charges': [75.50, 50.00, 105.75],
        'total_charges': [75.50, 250.00, 6345.00]
    })

    # Predict churn for the new customers
    new_churn_predictor.predict_churn(new_customers)
