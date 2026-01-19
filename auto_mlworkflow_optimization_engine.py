import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import time

class AutoMLWorkflowOptimizationEngine:
    def __init__(self, data, target_column):
        """
        Initialize the Auto ML workflow optimization engine.
        Args:
            data (pd.DataFrame): Input data for training.
            target_column (str): Column name of the target variable.
        """
        self.data = data
        self.target_column = target_column
        self.best_model = None
        self.leaderboard = pd.DataFrame()

        # Define a space of models and their hyperparameters to search
        self.model_space = [
            {
                'model': LogisticRegression(random_state=42, max_iter=1000),
                'params': {
                    'model__C': [0.1, 1.0, 10],
                    'model__solver': ['liblinear'],
                    'model__class_weight': ['balanced']
                }
            },
            {
                'model': RandomForestClassifier(random_state=42),
                'params': {
                    'model__n_estimators': [50, 100],
                    'model__max_depth': [10, 20],
                    'model__min_samples_split': [2, 5],
                    'model__class_weight': ['balanced']
                }
            },
            {
                'model': GradientBoostingClassifier(random_state=42),
                'params': {
                    'model__n_estimators': [50, 100],
                    'model__learning_rate': [0.05, 0.1],
                    'model__max_depth': [3, 5]
                }
            }
        ]

    def _get_preprocessor(self, X: pd.DataFrame):
        """
        Creates a preprocessor pipeline to handle numeric and categorical features.
        """
        numeric_features = X.select_dtypes(include=np.number).columns.tolist()
        categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()

        numeric_transformer = StandardScaler()
        categorical_transformer = OneHotEncoder(handle_unknown='ignore', sparse_output=False)

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ],
            remainder='passthrough'
        )
        return preprocessor

    def optimize_workflow(self):
        """
        Optimize the ML workflow by searching through multiple models and their
        hyperparameters, then ranking them on a leaderboard.
        """
        if self.target_column not in self.data.columns:
            raise ValueError(f"Target column '{self.target_column}' not found in data.")

        X = self.data.drop(columns=[self.target_column])
        y = self.data[self.target_column]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )

        preprocessor = self._get_preprocessor(X_train)
        results = []

        for model_config in self.model_space:
            model_name = model_config['model'].__class__.__name__
            print(f"--- Starting optimization for {model_name} ---")

            pipeline = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('model', model_config['model'])
            ])

            start_time = time.time()
            grid_search = GridSearchCV(
                pipeline, model_config['params'], cv=3, n_jobs=-1, verbose=1, scoring='accuracy'
            )

            try:
                grid_search.fit(X_train, y_train)

                best_estimator = grid_search.best_estimator_
                y_pred = best_estimator.predict(X_test)
                test_accuracy = accuracy_score(y_test, y_pred)

                results.append({
                    'model': model_name,
                    'best_cv_score': grid_search.best_score_,
                    'test_accuracy': test_accuracy,
                    'best_params': grid_search.best_params_,
                    'estimator': best_estimator
                })

                print(f"Completed {model_name} in {time.time() - start_time:.2f} seconds. Best CV Score: {grid_search.best_score_:.4f}")

            except Exception as e:
                print(f"Could not train {model_name}. Error: {e}")

        if not results:
            print("No models were successfully trained.")
            return

        # Create and sort the leaderboard
        self.leaderboard = pd.DataFrame(results).sort_values(by='test_accuracy', ascending=False).reset_index(drop=True)

        # Store the best overall model
        self.best_model = self.leaderboard.loc[0, 'estimator']

        print("\n--- AutoML Workflow Optimization Complete ---")
        print("\nLeaderboard:")
        print(self.leaderboard[['model', 'best_cv_score', 'test_accuracy', 'best_params']].to_string())

        print("\nBest Performing Model Details:")
        best_model_name = self.leaderboard.loc[0, 'model']
        best_model_pipeline = self.leaderboard.loc[0, 'estimator']

        print(f"Model Type: {best_model_name}")
        print("Pipeline Steps:", [step[0] for step in best_model_pipeline.steps])

        y_pred_best = self.best_model.predict(X_test)
        print("\nClassification Report for the Best Model on Test Set:")
        print(classification_report(y_test, y_pred_best))


    def get_best_model(self):
        """
        Get the best model (pipeline) found during optimization.
        Returns:
            Pipeline: The best performing Scikit-learn Pipeline object.
        """
        return self.best_model

    def get_leaderboard(self):
        """
        Get a summary of the performance of models tested.
        Returns:
            pd.DataFrame: A leaderboard of models and their scores.
        """
        return self.leaderboard


if __name__ == '__main__':
    # --- Create a synthetic dataset for demonstration ---
    np.random.seed(42)
    num_samples = 500
    data = {
        'age': np.random.randint(20, 71, num_samples),
        'income': np.random.uniform(30000, 150000, num_samples),
        'city': np.random.choice(['New York', 'London', 'Tokyo', 'Sydney'], num_samples),
        'gender': np.random.choice(['Male', 'Female', 'Other'], num_samples),
        'previous_purchases': np.random.randint(0, 50, num_samples),
        'churn': np.random.choice([0, 1], num_samples, p=[0.7, 0.3])
    }
    df = pd.DataFrame(data)

    print("--- Synthetic Data Generated ---")
    print(df.head())
    print("\nTarget variable distribution:")
    print(df['churn'].value_counts())
    print("-" * 30)

    # --- Initialize and run the AutoML engine ---
    target_column = 'churn'
    automl_engine = AutoMLWorkflowOptimizationEngine(data=df, target_column=target_column)

    # This will run the full optimization process and print the results
    automl_engine.optimize_workflow()

    # --- Get and inspect the results ---
    print("\n\n--- Accessing Results from the Engine ---")

    # Get the final leaderboard
    leaderboard = automl_engine.get_leaderboard()
    print("\nFinal Leaderboard:")
    if not leaderboard.empty:
        # Displaying without the 'estimator' column for clarity
        print(leaderboard[['model', 'best_cv_score', 'test_accuracy', 'best_params']].to_string())
    else:
        print("Leaderboard is empty, something went wrong.")

    # Get the best model pipeline
    best_pipeline = automl_engine.get_best_model()
    print(f"\nBest model pipeline retrieved: {best_pipeline.__class__.__name__}")
    if best_pipeline:
        print(f"Type of the best model inside the pipeline: {best_pipeline.named_steps['model'].__class__.__name__}")

        # --- Demonstrate prediction with the best model ---
        print("\n--- Demonstrating Prediction on New Data ---")
        new_customer = pd.DataFrame({
            'age': [45],
            'income': [85000.0],
            'city': ['London'],
            'gender': ['Female'],
            'previous_purchases': [22]
        })

        prediction = best_pipeline.predict(new_customer)
        prediction_proba = best_pipeline.predict_proba(new_customer)

        print(f"Prediction for new customer: {'Churn' if prediction[0] == 1 else 'No Churn'}")
        print(f"Prediction probabilities (No Churn, Churn): {prediction_proba[0]}")
