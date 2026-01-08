import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import GridSearchCV, train_test_split


class AutoMLWorkflowOptimizationEngine:
    def __init__(self, data, target_column):
        """
        Initialize the Auto ML workflow optimization engine.
        Args:
            data (DataFrame): Input data for training.
            target_column (str): Column name of the target variable.
        """
        self.data = data
        self.target_column = target_column
        self.best_model = None

    def optimize_workflow(self):
        """
        Optimize the ML workflow by tuning hyperparameters and selecting the best model.
        """
        # Split data into training and testing sets
        X = self.data.drop(columns=[self.target_column])
        y = self.data[self.target_column]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Define the parameter grid for tuning
        param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 10, 20, 30],
            "min_samples_split": [2, 5, 10],
        }

        # Initialize the model
        model = RandomForestClassifier(random_state=42)

        # Perform grid search to find the best parameters
        grid_search = GridSearchCV(
            estimator=model, param_grid=param_grid, cv=3, n_jobs=-1, verbose=2
        )
        try:
            grid_search.fit(X_train, y_train)
        except Exception as e:
            print(f"Error during grid search: {e}")
            self.best_model = None
            return

        # Store the best model
        self.best_model = grid_search.best_estimator_

        # Evaluate the best model
        y_pred = self.best_model.predict(X_test)
        print("Classification Report:")
        try:
            print(classification_report(y_test, y_pred))
        except Exception as e:
            print(f"Error during evaluation: {e}")

    def get_best_model(self):
        """
        Get the best model found during optimization.
        Returns:
            object: The best model.
        """
        return self.best_model
