import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


class ObjectAnatomyAI:
    def __init__(self, data):
        """
        Initialize the Object Anatomy AI module.
        Args:
            data (DataFrame): Data containing object attributes and labels.
        """
        self.data = data
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def train_model(self):
        """
        Train the model to analyze object attributes.
        """
        X = self.data.drop(columns=["label"])
        y = self.data["label"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)

        print("Classification Report:")
        print(classification_report(y_test, y_pred))

    def analyze_object(self, object_data):
        """
        Analyze an object and provide AI-driven recommendations.
        Args:
            object_data (dict): Dictionary containing object attributes.
        Returns:
            dict: Analysis and recommendations for the object.
        """
        df = pd.DataFrame([object_data])
        recommendation = self.model.predict(df)[0]
        return {"input": object_data, "recommendation": recommendation}

    def run(self):
        """
        Run the training and analysis process.
        """
        self.train_model()
