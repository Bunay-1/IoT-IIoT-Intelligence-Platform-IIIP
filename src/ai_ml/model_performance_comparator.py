class ModelPerformanceComparator:
    def __init__(self, models):
        self.models = models

    def compare_performances(self):
        print("Comparing model performances")
        comparison_results = {}
        for model in self.models:
            performance = model.evaluate()
            comparison_results[model.name] = performance
            print(f"Performance of {model.name}: {performance}")
        return comparison_results

    def select_best_model(self):
        print("Selecting best model based on performance")
        comparison_results = self.compare_performances()
        best_model = max(comparison_results, key=comparison_results.get)
        print(f"Best model: {best_model}")
        return best_model
