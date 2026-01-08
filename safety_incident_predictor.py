class SafetyIncidentPredictor:
    def __init__(self, model):
        self.model = model

    def predict_incident(self, data):
        print(f"Predicting safety incident for data: {data}")
        return self.model.predict(data)
