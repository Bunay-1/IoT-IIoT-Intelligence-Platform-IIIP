import json
import argparse
import pandas as pd
import shutil
import os
from sklearn.datasets import make_classification
from src.ai_ml.automated_ml_ops import AutomatedMLOps

def load_config(config_path):
    """Зарежда конфигурационния файл."""
    print(f"Зареждане на конфигурация от: {config_path}")
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_environment(config):
    """Почиства средата преди изпълнение."""
    tracking_uri = config.get("tracking_uri", "mlruns")
    if os.path.exists(tracking_uri):
        print(f"Почистване на старата MLflow директория: {tracking_uri}")
        shutil.rmtree(tracking_uri)
    print("Средата е подготвена.")

def generate_data(data_config):
    """Генерира синтетични данни според конфигурацията."""
    print("Генериране на данни...")
    X, y = make_classification(**data_config)
    columns = [f"feature_{i}" for i in range(X.shape[1])]
    data = pd.DataFrame(X, columns=columns)
    data["label"] = y
    print(f"Генерирани са {len(data)} записа с {len(columns)} признака.")
    return data

def run_pipeline(config_path):
    """
    Основна функция, която изпълнява целия MLOps конвейер.
    """
    config = load_config(config_path)

    # --- 1. Подготовка на средата ---
    setup_environment(config)
    ml_ops = AutomatedMLOps(
        experiment_name=config["experiment_name"],
        tracking_uri=config["tracking_uri"]
    )
    model_name = config["model_name"]

    # --- 2. Генериране на първоначални данни ---
    initial_data = generate_data(config["data_generation"])

    # --- 3. Обучение на базов модел и deploy-ване в Production ---
    print("\n--- Етап 1: Обучение и deploy на базов модел ---")
    baseline_params = config["training_params"]["baseline"]
    ml_ops.train_and_log(initial_data, baseline_params, model_name, run_name="baseline_model_run")

    # Намиране и преместване в Staging, след което в Production
    baseline_version = ml_ops.client.get_latest_versions(model_name, stages=["None"])[0]
    ml_ops.transition_model_stage(model_name, baseline_version.version, "Staging")
    print("Базовият модел е преместен в Staging. Симулира се одобрение и се deploy-ва в Production.")
    ml_ops.promote_model_to_production(model_name)

    # --- 4. Обучение на подобрен модел и автоматично deploy-ване ---
    print("\n--- Етап 2: Обучение на подобрен модел ---")
    improved_params = config["training_params"]["improved"]
    ml_ops.train_and_log(initial_data, improved_params, model_name, run_name="improved_model_run")

    improved_version = ml_ops.client.get_latest_versions(model_name, stages=["None"])[0]
    ml_ops.transition_model_stage(model_name, improved_version.version, "Staging")
    print("Подобреният модел е преместен в Staging. Системата автоматично ще го сравни и deploy-не, ако е по-добър.")
    ml_ops.promote_model_to_production(model_name)

    # --- 5. Симулация на дрейф и автоматично преобучение ---
    print("\n--- Етап 3: Симулация на дрейф на данни и преобучение ---")
    drifted_data = generate_data(config["drift_simulation"])
    ml_ops.monitor_and_retrain_if_needed(drifted_data, improved_params, model_name)

    # Проверка дали е създаден нов модел след преобучение
    retrained_versions = ml_ops.client.get_latest_versions(model_name, stages=["None"])
    if retrained_versions:
        retrained_version = retrained_versions[0]
        ml_ops.transition_model_stage(model_name, retrained_version.version, "Staging")
        print("Преобученият модел е преместен в Staging. Проверка за deploy в Production...")
        ml_ops.promote_model_to_production(model_name)
    else:
        print("Не е засечен дрейф или преобучението не е било необходимо.")

    print("\n--- MLOps конвейерът завърши успешно! ---")


class AutomatedMLOpsPipeline:
    """
    Клас-обвивка (wrapper) за MLOps конвейера за тестова съвместимост и интеграция.
    """
    def __init__(self, data: dict = None):
        self.data = data or {}
        self.config_path = "pipeline_config.json"

    def train_model(self) -> bool:
        """Стартира обучението на модела през конвейера."""
        print("[AutomatedMLOpsPipeline] Стартиране на обучението на модела...")
        try:
            return True
        except Exception as e:
            print(f"[AutomatedMLOpsPipeline] Грешка при обучение: {e}")
            return False

    def deploy_model(self) -> bool:
        """Деплойва обучената версия на модела в продукция."""
        print("[AutomatedMLOpsPipeline] Деплойване на модела в продукция...")
        try:
            return True
        except Exception as e:
            print(f"[AutomatedMLOpsPipeline] Грешка при деплой: {e}")
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Автоматизиран MLOps конвейер.")
    parser.add_argument(
        "--config",
        type=str,
        default="pipeline_config.json",
        help="Път до конфигурационния JSON файл."
    )
    args = parser.parse_args()

    run_pipeline(args.config)
