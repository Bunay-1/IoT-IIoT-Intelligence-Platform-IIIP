import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split


class PredictiveQuality:
    def __init__(self, data):
        """
        Инициализира модула за предскажане на качество.
        Args:
            data (DataFrame): Данни за качество на продукцията.
        """
        self.data = data
        self.model = LinearRegression()

    def train_model(self):
        """
        Обучава модела за предскажане на качество.
        """
        X = self.data.drop(columns=["quality"])
        y = self.data["quality"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"Model MSE: {mse}")

    def predict_quality(self, input_data):
        """
        Предсказва качеството на нови данни.
        Args:
            input_data (DataFrame): Нови данни за предскажане.
        Returns:
            Series: Предскажано качество.
        """
        return self.model.predict(input_data)

    def run(self):
        """
        Стартира процеса на обучение и предскажане.
        """
        self.train_model()


# Пример данни за демонстрация
data = pd.DataFrame(
    {
        "feature_1": [1, 2, 3, 4, 5],
        "feature_2": [5, 4, 3, 2, 1],
        "quality": [80, 85, 90, 75, 95],
    }
)

# Създаване и стартиране на модула
quality_predictor = PredictiveQuality(data)
quality_predictor.run()
