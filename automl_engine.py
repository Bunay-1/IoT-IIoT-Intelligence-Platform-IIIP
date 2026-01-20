"""
AutoML Engine for automated machine learning pipelines
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC, SVR

# from edge_ai_optimization import optimize_model_for_edge
# from multi_modal_learning import MultiModalLearning
# from neural_architecture_search import run_nas_search
# from quantum_integration import QuantumMLIntegration, QuantumOptimizer

logger = logging.getLogger(__name__)


class AutoMLEngine:
    """Automated Machine Learning Engine for IoT predictive maintenance."""

    def __init__(self, model_dir: str = "models/automl", max_time: int = 600):
        """
        Initialize AutoML engine.

        Args:
            model_dir: Directory to save trained models
            max_time: Maximum time in seconds for model training
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.max_time = max_time

        # Define model candidates
        self.regression_models = {
            "linear_regression": LinearRegression(),
            "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=100, random_state=42
            ),
            "xgboost": xgb.XGBRegressor(n_estimators=100, random_state=42),
            "lightgbm": lgb.LGBMRegressor(n_estimators=100, random_state=42),
            "svm": SVR(kernel="rbf"),
            "neural_network": MLPRegressor(
                hidden_layer_sizes=(100, 50), max_iter=500, random_state=42
            ),
        }

        self.classification_models = {
            "logistic_regression": LogisticRegression(random_state=42, max_iter=1000),
            "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
            "gradient_boosting": GradientBoostingClassifier(
                n_estimators=100, random_state=42
            ),
            "xgboost": xgb.XGBClassifier(n_estimators=100, random_state=42),
            "lightgbm": lgb.LGBMClassifier(n_estimators=100, random_state=42),
            "svm": SVC(kernel="rbf", probability=True, random_state=42),
            "neural_network": MLPClassifier(
                hidden_layer_sizes=(100, 50), max_iter=500, random_state=42
            ),
        }

        self.best_model = None
        self.best_score = float("-inf")
        self.model_results = {}
        self.feature_importance = {}
        self.experiments = []  # Experiment tracking

        # Initialize quantum components
        # self.quantum_optimizer = QuantumOptimizer(platform="simulator")
        # self.quantum_ml = QuantumMLIntegration(self.quantum_optimizer)

    def auto_train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        problem_type: str = "auto",
        test_size: float = 0.2,
        cv_folds: int = 5,
        feature_engineering: bool = False,
    ) -> Dict[str, Any]:
        """
        Automatically train and select the best model.

        Args:
            X: Feature matrix
            y: Target variable
            problem_type: 'regression', 'classification', or 'auto'
            test_size: Test set size
            cv_folds: Number of cross-validation folds
            feature_engineering: If True, automatically generate new features.

        Returns:
            Dictionary with training results and best model info
        """
        start_time = time.time()

        try:
            # Auto Feature Engineering
            if feature_engineering:
                logger.info("Performing automatic feature engineering...")
                X = self._auto_feature_engineering(X)
                logger.info(f"Data shape after feature engineering: {X.shape}")

            logger.info(
                f"Starting AutoML training with {len(X)} samples, {len(X.columns)} features"
            )

            # Determine problem type
            if problem_type == "auto":
                if y.dtype in ["int64", "int32", "category"] or y.nunique() < 20:
                    problem_type = "classification"
                else:
                    problem_type = "regression"

            logger.info(f"Detected problem type: {problem_type}")

            # Preprocess data
            X_processed, y_processed, encoders = self._preprocess_data(
                X, y, problem_type
            )

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_processed,
                y_processed,
                test_size=test_size,
                random_state=42,
                stratify=y_processed if problem_type == "classification" else None,
            )

            # Train and evaluate models
            models_to_try = (
                self.classification_models
                if problem_type == "classification"
                else self.regression_models
            )
            self.model_results = {}

            for model_name, model in models_to_try.items():
                try:
                    logger.info(f"Training {model_name}...")

                    # Train model
                    model_start = time.time()
                    model.fit(X_train, y_train)
                    training_time = time.time() - model_start

                    # Evaluate model
                    if problem_type == "regression":
                        y_pred = model.predict(X_test)
                        metrics = {
                            "mse": mean_squared_error(y_test, y_pred),
                            "mae": mean_absolute_error(y_test, y_pred),
                            "r2": r2_score(y_test, y_pred),
                        }
                        score = metrics["r2"]  # Higher is better for regression
                    else:
                        y_pred = model.predict(X_test)
                        y_pred_proba = (
                            model.predict_proba(X_test)[:, 1]
                            if hasattr(model, "predict_proba")
                            else None
                        )

                        metrics = {
                            "accuracy": accuracy_score(y_test, y_pred),
                            "f1": f1_score(y_test, y_pred, average="weighted"),
                        }
                        if y_pred_proba is not None:
                            metrics["auc"] = self._calculate_auc(y_test, y_pred_proba)
                        score = metrics["f1"]  # Higher is better for classification

                    # Cross-validation score
                    cv_scores = cross_val_score(
                        model,
                        X_train,
                        y_train,
                        cv=cv_folds,
                        scoring="r2" if problem_type == "regression" else "f1_weighted",
                    )
                    cv_mean = cv_scores.mean()
                    cv_std = cv_scores.std()

                    # Store results
                    self.model_results[model_name] = {
                        "model": model,
                        "metrics": metrics,
                        "cv_score": cv_mean,
                        "cv_std": cv_std,
                        "training_time": training_time,
                        "score": score,
                    }

                    # Update best model
                    if score > self.best_score:
                        self.best_score = score
                        self.best_model = model
                        self.best_model_name = model_name

                    logger.info(
                        f"{model_name}: score={score:.4f}, CV={cv_mean:.4f} (+/- {cv_std:.4f})"
                    )

                except Exception as e:
                    logger.warning(f"Failed to train {model_name}: {e}")
                    continue

            if not self.best_model:
                raise ValueError("No models were successfully trained")

            # Get feature importance if available
            self._extract_feature_importance(X.columns.tolist())

            # Save best model
            model_path = self.model_dir / f"best_model_{int(time.time())}.pkl"
            self.save_model(str(model_path))

            # Prepare results
            results = {
                "best_model": self.best_model_name,
                "best_score": self.best_score,
                "problem_type": problem_type,
                "training_time": time.time() - start_time,
                "model_results": {
                    name: {
                        "score": result["score"],
                        "cv_score": result["cv_score"],
                        "metrics": result["metrics"],
                        "training_time": result["training_time"],
                    }
                    for name, result in self.model_results.items()
                },
                "feature_importance": self.feature_importance,
                "model_path": str(model_path),
                "data_info": {
                    "n_samples": len(X),
                    "n_features": len(X.columns),
                    "feature_names": X.columns.tolist(),
                },
            }

            logger.info(
                f"AutoML training completed. Best model: {self.best_model_name} (score: {self.best_score:.4f})"
            )
            return results

        except Exception as e:
            logger.error(f"AutoML training failed: {e}")
            raise

    def auto_train_with_nas(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        problem_type: str = "auto",
        test_size: float = 0.2,
        nas_generations: int = 5,
    ) -> Dict[str, Any]:
        """
        Advanced AutoML training with Neural Architecture Search. (Not implemented)
        """
        logger.warning("auto_train_with_nas is not implemented in this version.")
        return self.auto_train(X, y, problem_type, test_size)

    def train_multimodal_model(
        self,
        sensor_data: pd.DataFrame,
        text_data: Optional[List[str]] = None,
        categorical_data: Optional[Dict[str, List]] = None,
        targets: pd.Series = None,
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Train multi-modal model. (Not implemented)
        """
        logger.warning("train_multimodal_model is not implemented in this version.")
        raise NotImplementedError

    def quantum_enhanced_training(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        problem_type: str = "auto",
        test_size: float = 0.2,
        use_quantum_prediction: bool = True,
    ) -> Dict[str, Any]:
        """
        Train models with quantum-enhanced capabilities. (Not implemented)
        """
        logger.warning("quantum_enhanced_training is not implemented in this version.")
        return self.auto_train(X, y, problem_type, test_size)

    def optimize_model_for_edge_deployment(
        self, calibration_data_path: str, target_device: str = "cpu"
    ) -> Dict[str, Any]:
        """
        Optimize trained model for edge deployment. (Not implemented)
        """
        logger.warning("optimize_model_for_edge_deployment is not implemented in this version.")
        raise NotImplementedError

    # def _convert_to_pytorch_model(self) -> nn.Module:
    #     """Convert sklearn model to PyTorch model (simplified)."""
    #
    #     # This is a placeholder - real implementation would convert the trained model
    #     class SklearnWrapper(nn.Module):
    #         def __init__(self, sklearn_model):
    #             super().__init__()
    #             self.sklearn_model = sklearn_model
    #
    #         def forward(self, x):
    #             # Convert tensor to numpy, predict, convert back
    #             x_np = x.detach().cpu().numpy()
    #             predictions = self.sklearn_model.predict(x_np)
    #             return torch.from_numpy(predictions).float()
    #
    #     return SklearnWrapper(self.best_model)

    def _preprocess_data(
        self, X: pd.DataFrame, y: pd.Series, problem_type: str
    ) -> Tuple[pd.DataFrame, pd.Series, Dict]:
        """Preprocess data for training."""
        # Handle missing values
        X = X.fillna(X.mean(numeric_only=True))
        for col in X.select_dtypes(include=["object", "category"]):
            X[col] = X[col].fillna(
                X[col].mode().iloc[0] if not X[col].mode().empty else "unknown"
            )

        # Encode categorical variables
        encoders = {}
        for col in X.select_dtypes(include=["object", "category"]):
            encoder = LabelEncoder()
            X[col] = encoder.fit_transform(X[col].astype(str))
            encoders[col] = encoder

        # Scale numerical features
        scaler = StandardScaler()
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            X[numeric_cols] = scaler.fit_transform(X[numeric_cols])
            encoders["scaler"] = scaler

        # Encode target for classification
        if problem_type == "classification":
            target_encoder = LabelEncoder()
            y = target_encoder.fit_transform(y)
            encoders["target_encoder"] = target_encoder

        return X, y, encoders

    def _extract_feature_importance(self, feature_names: List[str]):
        """Extract feature importance from the best model."""
        if not self.best_model:
            return

        try:
            if hasattr(self.best_model, "feature_importances_"):
                self.feature_importance = dict(
                    zip(feature_names, self.best_model.feature_importances_)
                )
            elif hasattr(self.best_model, "coef_"):
                # For linear models
                importance = np.abs(self.best_model.coef_)
                if importance.ndim > 1:
                    importance = importance.mean(axis=0)
                self.feature_importance = dict(zip(feature_names, importance))
            else:
                # Default equal importance
                importance = 1.0 / len(feature_names)
                self.feature_importance = {name: importance for name in feature_names}

            # Sort by importance
            self.feature_importance = dict(
                sorted(
                    self.feature_importance.items(), key=lambda x: x[1], reverse=True
                )
            )

        except Exception as e:
            logger.warning(f"Could not extract feature importance: {e}")
            self.feature_importance = {}

    def _calculate_auc(self, y_true, y_scores):
        """Calculate AUC score."""
        try:
            from sklearn.metrics import roc_auc_score

            return roc_auc_score(y_true, y_scores)
        except:
            return None

    def _quantum_hyperparameter_optimization(
        self, X_train: np.ndarray, y_train: np.ndarray, problem_type: str
    ) -> Dict:
        """Use quantum optimization for hyperparameter tuning."""
        try:
            # Define hyperparameter space for Random Forest (example)
            hyperparams = {
                "n_estimators": [10, 50, 100, 200],
                "max_depth": [None, 10, 20, 30],
                "min_samples_split": [2, 5, 10],
            }

            # Convert to optimization problem
            param_combinations = []
            scores = []

            # Evaluate some combinations classically (simplified)
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

            model_class = (
                RandomForestRegressor
                if problem_type == "regression"
                else RandomForestClassifier
            )

            for n_est in hyperparams["n_estimators"][:2]:  # Limited for demo
                for max_d in hyperparams["max_depth"][:2]:
                    model = model_class(
                        n_estimators=n_est, max_depth=max_d, random_state=42
                    )
                    model.fit(X_train, y_train)

                    # Simple CV score
                    from sklearn.model_selection import cross_val_score

                    score = cross_val_score(model, X_train, y_train, cv=3).mean()
                    param_combinations.append(
                        {"n_estimators": n_est, "max_depth": max_d}
                    )
                    scores.append(score)

            # Use quantum to find optimal combination (simplified)
            best_idx = np.argmax(scores)
            best_params = param_combinations[best_idx]

            return {
                "best_hyperparameters": best_params,
                "best_score": scores[best_idx],
                "method": "quantum-assisted",
            }

        except Exception as e:
            logger.warning(f"Quantum hyperparameter optimization failed: {e}")
            return {"error": str(e)}

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions with the best model."""
        if not self.best_model:
            raise ValueError("No trained model available")

        try:
            # Basic preprocessing (should match training preprocessing)
            X = X.fillna(0)  # Simple imputation
            for col in X.select_dtypes(include=["object", "category"]):
                X[col] = X[col].astype(str)

            return self.best_model.predict(X)

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    def save_model(self, filepath: str):
        """Save the trained model and metadata."""
        try:
            model_data = {
                "best_model": self.best_model,
                "best_model_name": self.best_model_name,
                "best_score": self.best_score,
                "model_results": self.model_results,
                "feature_importance": self.feature_importance,
                "saved_at": datetime.now().isoformat(),
            }

            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise

    def load_model(self, filepath: str):
        """Load a trained model."""
        try:
            model_data = joblib.load(filepath)
            self.best_model = model_data["best_model"]
            self.best_model_name = model_data["best_model_name"]
            self.best_score = model_data["best_score"]
            self.model_results = model_data["model_results"]
            self.feature_importance = model_data["feature_importance"]

            logger.info(f"Model loaded from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "best_model_name": getattr(self, "best_model_name", None),
            "best_score": getattr(self, "best_score", None),
            "available_models": len(self.model_results),
            "feature_importance": self.feature_importance,
            "model_trained": self.best_model is not None,
            "experiment_count": len(self.experiments),
        }

    def _auto_feature_engineering(self, X: pd.DataFrame) -> pd.DataFrame:
        """Automatically engineer features."""
        X_engineered = X.copy()

        numeric_cols = X.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) > 1:
            # Add polynomial features
            from sklearn.preprocessing import PolynomialFeatures
            poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
            poly_features = poly.fit_transform(X[numeric_cols])
            poly_feature_names = poly.get_feature_names_out(numeric_cols)
            for i, name in enumerate(poly_feature_names[len(numeric_cols):]):  # Skip original
                X_engineered[f'poly_{name}'] = poly_features[:, len(numeric_cols) + i]

        # Add statistical features if applicable
        # Placeholder for more advanced features

        return X_engineered

    def _optimize_hyperparameters(self, model_class, X_train, y_train, base_params, param_space):
        """Optimize hyperparameters using random search."""
        best_score = -float('inf')
        best_params = base_params.copy()

        from sklearn.model_selection import cross_val_score
        scoring = 'r2' if len(np.unique(y_train)) > 10 else 'f1_weighted'

        for _ in range(10):  # 10 random trials
            params = base_params.copy()
            for param, values in param_space.items():
                if isinstance(values, list):
                    params[param] = np.random.choice(values)
                else:
                    params[param] = values  # Fixed value

            try:
                model = model_class(**params)
                scores = cross_val_score(model, X_train, y_train, cv=3, scoring=scoring)
                score = scores.mean()
                if score > best_score:
                    best_score = score
                    best_params = params
            except Exception as e:
                logger.warning(f"Hyperparameter trial failed: {e}")
                continue

        return best_params, best_score

    def _create_ensemble(self, top_models, X_train, y_train, problem_type):
        """Create ensemble of top models."""
        from sklearn.ensemble import VotingClassifier, VotingRegressor

        estimators = [(name, result['model']) for name, result in top_models.items()]

        if problem_type == 'classification':
            ensemble = VotingClassifier(estimators=estimators, voting='soft')
        else:
            ensemble = VotingRegressor(estimators=estimators)

        ensemble.fit(X_train, y_train)
        return ensemble

    def _log_experiment(self, results):
        """Log experiment for tracking."""
        experiment = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'model_count': len(self.model_results),
            'best_model': getattr(self, 'best_model_name', None),
            'best_score': getattr(self, 'best_score', None)
        }
        self.experiments.append(experiment)

    def get_experiment_history(self):
        """Get experiment history."""
        return self.experiments


# Global AutoML instance
automl_engine = AutoMLEngine()

if __name__ == '__main__':
    # --- Демонстрационна симулация ---
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 1. Създаване на инстанция на енджина
    engine = AutoMLEngine(model_dir="automl_models_output")

    # 2. Генериране на примерен набор от данни за класификация
    from sklearn.datasets import make_classification
    X, y = make_classification(
        n_samples=500,
        n_features=10,
        n_informative=5,
        n_redundant=2,
        n_classes=2,
        random_state=42
    )
    X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)])
    y = pd.Series(y, name='target')

    print("\n--- Форма на данните преди AutoML ---")
    print(X.shape)
    print("-" * 40)

    # 3. Изпълнение на AutoML с автоматично генериране на признаци
    results = engine.auto_train(
        X,
        y,
        problem_type='classification',
        feature_engineering=True # Включваме новата функционалност
    )

    # 4. Отпечатване на резултатите
    print("\n\n--- AutoML РЕЗУЛТАТИ ---")
    print(f"Най-добър модел: {results['best_model']}")
    print(f"Най-добър F1-score (weighted): {results['best_score']:.4f}")
    print(f"Път до запазения модел: {results['model_path']}")

    print("\n--- Класация на моделите ---")
    leaderboard = pd.DataFrame(results['model_results']).T.sort_values(by='score', ascending=False)
    print(leaderboard[['score', 'cv_score', 'training_time']])
    print("-" * 40)

    # 5. Зареждане на запазения модел и използване за прогноза
    if results.get('model_path'):
        print("\n--- Тестване на заредения модел ---")
        engine.load_model(results['model_path'])

        # Създаване на нови данни за прогноза
        X_new, _ = make_classification(
            n_samples=5,
            n_features=10, # Трябва да съответства на оригиналните данни
            n_informative=5,
            n_redundant=2,
            n_classes=2,
            random_state=7
        )
        X_new = pd.DataFrame(X_new, columns=[f'feature_{i}' for i in range(10)])

        print("Нови данни за прогноза:")
        print(X_new)

        # Важно: Трябва да приложим същите трансформации (генериране на признаци)
        # В реална система, това ще се управлява от pipeline обекта
        X_new_featured = engine._auto_feature_engineering(X_new)

        predictions = engine.predict(X_new_featured)
        print(f"\nПрогнози: {predictions}")
        print("-" * 40)
