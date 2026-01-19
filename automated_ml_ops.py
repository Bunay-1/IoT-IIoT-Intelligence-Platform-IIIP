import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
import shutil
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.datasets import make_classification
from scipy.stats import ks_2samp


class AutomatedMLOps:
    def __init__(self, experiment_name, tracking_uri="mlruns"):
        """
        Инициализира системата за автоматизирано управление на ML цикъл на живот.
        Args:
            experiment_name (str): Име на експеримента в MLflow.
            tracking_uri (str): URI за съхранение на MLflow артефакти.
        """
        self.experiment_name = experiment_name
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        self.client = mlflow.tracking.MlflowClient()
        self.training_data_reference = None

    def train_and_log(self, data, params, run_name="training_run"):
        """
        Обучава, оценява и логва модел в MLflow.
        Args:
            data (pd.DataFrame): Данни за обучение с колона 'label'.
            params (dict): Хиперпараметри за модела RandomForestClassifier.
            run_name (str): Име за текущото изпълнение в MLflow.
        """
        with mlflow.start_run(run_name=run_name) as run:
            run_id = run.info.run_id
            print(f"--- Starting Run: {run_name} ({run_id}) ---")

            # 1. Подготовка на данни и съхранение на референция
            X = data.drop("label", axis=1)
            y = data["label"]
            if self.training_data_reference is None:
                self.training_data_reference = X.copy()
                print("  Saved reference to original training data distribution.")

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # 2. Обучение на реален модел
            model = RandomForestClassifier(**params, random_state=42)
            model.fit(X_train, y_train)

            # 3. Оценка на модела
            predictions = model.predict(X_test)
            accuracy = accuracy_score(y_test, predictions)
            metrics = {"accuracy": accuracy}

            print(f"  Logged Params: {params}")
            print(f"  Logged Metrics: {metrics}")

            # 4. Логиране в MLflow
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            mlflow.set_tag("run_type", "training")

            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                registered_model_name="automated_ml_model"
            )

            print(f"--- Run {run_name} finished. Model logged. ---")
            return run_id

    def check_for_data_drift(self, new_data, reference_data, feature, p_value_threshold=0.05):
        """
        Проверява за дрейф в данните за определен feature чрез Kolmogorov-Smirnov тест.
        Args:
            new_data (pd.DataFrame): Нови данни за проверка.
            reference_data (pd.DataFrame): Референтни (тренировъчни) данни.
            feature (str): Колоната (feature) за проверка.
            p_value_threshold (float): Праг за p-стойността, под който се счита, че има дрейф.
        Returns:
            bool: True, ако е засечен дрейф, иначе False.
        """
        ks_statistic, p_value = ks_2samp(reference_data[feature], new_data[feature])
        print(f"  Drift check for '{feature}': KS Statistic={ks_statistic:.4f}, P-Value={p_value:.4f}")
        if p_value < p_value_threshold:
            print(f"  -> Data drift detected for feature '{feature}'! (p < {p_value_threshold})")
            return True
        return False

    def monitor_and_retrain_if_needed(self, new_data, params):
        """
        Следи за дрейф и ако го засече, стартира преобучение.
        """
        print("\n--- Monitoring for Data Drift ---")
        drift_detected = False
        if self.training_data_reference is None:
            print("No training data reference available. Skipping drift check.")
            return

        for feature in self.training_data_reference.columns:
            if self.check_for_data_drift(new_data, self.training_data_reference, feature):
                drift_detected = True

        if drift_detected:
            print("--- Data drift confirmed. Triggering model retraining... ---")
            self.train_and_log(new_data, params, run_name="retraining_run_due_to_drift")
            # След преобучение, новите данни стават референтни
            self.training_data_reference = new_data.drop("label", axis=1, errors='ignore').copy()
            print("  Updated training data reference to new data distribution.")
        else:
            print("--- No significant data drift detected. No retraining needed. ---")

    def transition_model_stage(self, model_name, model_version, stage):
        """Премества определена версия на модел в нов етап."""
        print(f"Transitioning model version {model_version} of '{model_name}' to '{stage}'...")
        # MLflow не позволява архивиране на съществуващи версии, когато се преминава към неактивен етап
        should_archive = False if stage in ["Archived", "None"] else True
        self.client.transition_model_version_stage(
            name=model_name,
            version=model_version,
            stage=stage,
            archive_existing_versions=should_archive
        )
        print("Transition complete.")

    def load_production_model(self, model_name="automated_ml_model"):
        """Зарежда 'Production' версията на модела."""
        try:
            model_uri = f"models:/{model_name}/Production"
            print(f"\n--- Loading model from '{model_uri}' for inference ---")
            prod_model = mlflow.sklearn.load_model(model_uri)
            print("Production model loaded successfully.")
            return prod_model
        except Exception as e:
            print(f"Could not load Production model: {e}")
            return None

    def predict_with_production_model(self, model, inference_data):
        """Прави прогноза с 'Production' модела."""
        if model is None:
            print("Cannot predict, model is not loaded.")
            return None
        print(f"--- Making predictions on {len(inference_data)} new data points ---")
        predictions = model.predict(inference_data)
        print(f"  Example predictions: {predictions[:5]}")
        return predictions

    def promote_model_to_production(self, model_name="automated_ml_model"):
        """
        Сравнява най-новия 'Staging' модел с текущия 'Production' модел
        и го повишава, ако е по-добър.
        """
        print(f"\n--- Checking for model promotion for '{model_name}' ---")
        latest_staging_versions = self.client.get_latest_versions(model_name, stages=["Staging"])
        latest_prod_versions = self.client.get_latest_versions(model_name, stages=["Production"])

        if not latest_staging_versions:
            print("No models found in Staging. Nothing to promote.")
            return

        staging_version = latest_staging_versions[0]
        staging_run = self.client.get_run(staging_version.run_id)
        staging_accuracy = staging_run.data.metrics.get("accuracy", 0)
        print(f"Found model in Staging (Version: {staging_version.version}, Accuracy: {staging_accuracy:.4f})")

        if not latest_prod_versions:
            print("No model in Production. Promoting Staging model automatically.")
            self.transition_model_stage(model_name, staging_version.version, "Production")
            return

        prod_version = latest_prod_versions[0]
        prod_run = self.client.get_run(prod_version.run_id)
        prod_accuracy = prod_run.data.metrics.get("accuracy", 0)
        print(f"Found model in Production (Version: {prod_version.version}, Accuracy: {prod_accuracy:.4f})")

        if staging_accuracy > prod_accuracy:
            print("Staging model is better. Promoting to Production.")
            self.transition_model_stage(model_name, staging_version.version, "Production")
        else:
            print("Staging model is not better than Production model. Archiving Staging model.")
            self.transition_model_stage(model_name, staging_version.version, "Archived")


if __name__ == "__main__":
    EXPERIMENT_NAME = "Automated_ML_Ops_Lifecycle_Demo"
    TRACKING_URI = "mlruns"
    MODEL_NAME = "automated_ml_model"

    if TRACKING_URI and "mlruns" in TRACKING_URI:
        print(f"Cleaning up MLflow tracking directory: {TRACKING_URI}")
        shutil.rmtree(TRACKING_URI, ignore_errors=True)

    X, y = make_classification(n_samples=1000, n_features=10, n_informative=5, n_redundant=0, random_state=42)
    data = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(10)])
    data["label"] = y

    ml_ops = AutomatedMLOps(experiment_name=EXPERIMENT_NAME, tracking_uri=TRACKING_URI)

    print("\n\n--- Scenario 1: Training and deploying initial model version ---")
    base_params = {"n_estimators": 50, "max_depth": 5}
    ml_ops.train_and_log(data, base_params, run_name="baseline_model_run")
    initial_version = ml_ops.client.get_latest_versions(MODEL_NAME, stages=["None"])[0]
    ml_ops.transition_model_stage(MODEL_NAME, initial_version.version, "Staging")
    print("\nInitial model passed tests, promoting to Production for the first time.")
    ml_ops.promote_model_to_production(MODEL_NAME)

    print("\n\n--- Scenario 2: Training an improved model ---")
    improved_params = {"n_estimators": 100, "max_depth": 10}
    ml_ops.train_and_log(data, improved_params, run_name="improved_model_run")
    improved_version = ml_ops.client.get_latest_versions(MODEL_NAME, stages=["None"])[0]
    ml_ops.transition_model_stage(MODEL_NAME, improved_version.version, "Staging")
    ml_ops.promote_model_to_production(MODEL_NAME)

    print("\n\n--- Scenario 3: Training a weaker model ---")
    weaker_params = {"n_estimators": 10, "max_depth": 3}
    ml_ops.train_and_log(data, weaker_params, run_name="weaker_model_run")
    weaker_version = ml_ops.client.get_latest_versions(MODEL_NAME, stages=["None"])[0]
    ml_ops.transition_model_stage(MODEL_NAME, weaker_version.version, "Staging")
    ml_ops.promote_model_to_production(MODEL_NAME)

    print("\n\n--- Scenario 4: Inference with Production Model ---")
    prod_model = ml_ops.load_production_model(MODEL_NAME)
    inference_data = pd.DataFrame(np.random.rand(10, 10), columns=[f"feature_{i}" for i in range(10)])
    ml_ops.predict_with_production_model(prod_model, inference_data)

    print("\n\n--- Scenario 5: Simulating and Detecting Data Drift ---")
    # Създаване на "дрейфнали" данни чрез промяна на разпределението на feature_0
    X_drifted, y_drifted = make_classification(n_samples=1000, n_features=10, n_informative=5, n_redundant=0, random_state=123, shift=3.0)
    drifted_data = pd.DataFrame(X_drifted, columns=[f"feature_{i}" for i in range(10)])
    drifted_data["label"] = y_drifted

    # Мониторинг, който трябва да засече дрейфа и да стартира преобучение
    ml_ops.monitor_and_retrain_if_needed(drifted_data, improved_params)

    # Проверяваме дали е регистриран нов модел и го преместваме в Staging
    retrained_version = ml_ops.client.get_latest_versions(MODEL_NAME, stages=["None"])
    if retrained_version:
        ml_ops.transition_model_stage(MODEL_NAME, retrained_version[0].version, "Staging")
        # Опитваме се да го повишим в продукция
        ml_ops.promote_model_to_production(MODEL_NAME)
    else:
        print("No new model was trained, so no promotion check is needed.")

    print("\n\n--- MLOps Lifecycle Simulation Complete ---")
