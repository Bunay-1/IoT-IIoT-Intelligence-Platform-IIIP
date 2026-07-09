class CentralizedFeatureStore:
    def __init__(self, data):
        self.data = data

    def save_features(self):
        print("Saving features to centralized store")

    def retrieve_features(self, feature_name):
        print(f"Retrieving features: {feature_name}")
        return self.data[feature_name]
