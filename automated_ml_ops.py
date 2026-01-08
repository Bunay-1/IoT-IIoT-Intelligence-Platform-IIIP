import mlflow
import mlflow.pyfunc
import pandas as pd
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


class AutomatedMLOps:
    def __init__(self, experiment_name):
        """
        Инициализира системата за автоматизирано управление на ML цикъл на живот.
        Args:
            experiment_name (str): Име на експеримента в MLflow.
        """
        self.experiment_name = experiment_name
        self.experiment_id = mlflow.create_experiment(experiment_name)

    def log_model(self, model, input_data, params, metrics):
        """
        Логира модел в MLflow.
        Args:
            model: Обучен модел.
            input_data (DataFrame): Тренировъчни данни.
            params (dict): Хиперпараметри на модела.
            metrics (dict): Метрики за оценка на модела.
        """
        with mlflow.start_run(experiment_id=self.experiment_id) as run:
            # Логиране на модела
            mlflow.pyfunc.log_model(
                artifact_path="model",
                python_model=model,
                artifacts={"input_data": input_data.to_csv()},
                registered_model_name="automated_ml_model",
            )
            # Логиране на хиперпараметри и метрики
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            # Записване на ID на модела
            run_id = run.info.run_id
            mlflow.register_model(
                model_uri=f"runs:/{run_id}/model", name="automated_ml_model"
            )

    def train_and_log(self, data, params):
        """
        Обучава и логва модел.
        Args:
            data (DataFrame): Данни за обучение.
            params (dict): Хиперпараметри на модела.
        """
        # Примерна имплементация на модел (може да се замени с реална)
        X_train, X_test, y_train, y_test = train_test_split(
            data.drop("label", axis=1), data["label"], test_size=0.2, random_state=42
        )
        model = mlflow.pyfunc.PyFuncModel(model_fn=lambda X: X.mean(axis=1))
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)

        # Логиране на модела
        self.log_model(model, X_train, params, {"accuracy": accuracy})

    def deploy_model(self, model_stage="Production"):
        """
        Деплойра модел в определен етап (напр. Production).
        Args:
            model_stage (str): Етап, в който да бъде деплойран модела.
        """
        client = mlflow.tracking.MlflowClient()
        model_name = "automated_ml_model"
        model_version = client.get_latest_versions(model_name, stages=[model_stage])[
            0
        ].version

        # Деплойране на модела
        client.transition_model_version_stage(
            name=model_name,
            version=model_version,
            stage=model_stage,
            archive_existing_versions=True,
        )
        print(
            f"Model {model_name} deployed to stage {model_stage}, version {model_version}"
        )

    def run(self, data, params):
        """
        Стартира процеса на обучение, логване и деплойране.
        Args:
            data (DataFrame): Данни за обучение.
            params (dict): Хиперпараметри на модела.
        """
        self.train_and_log(data, params)
        self.deploy_model()


# Пример данни за демонстрация
data = pd.DataFrame(
    {
        "feature_1": [1, 2, 3, 4, 5],
        "feature_2": [5, 4, 3, 2, 1],
        "label": [0, 1, 0, 1, 0],
    }
)

# Параметри на модела
params = {"learning_rate": 0.01, "num_trees": 100, "max_depth": 5}

# Създаване и стартиране на системата
ml_ops = AutomatedMLOps(experiment_name="Automated_ML_Ops_Experiment")
ml_ops.run(data, params)
