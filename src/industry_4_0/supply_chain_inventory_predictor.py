class SupplyChainInventoryPredictor:
    def __init__(self, model, inventory_data):
        self.model = model
        self.inventory_data = inventory_data

    def predict_inventory(self):
        print("Predicting inventory needs")
        predictions = self.model.forecast(self.inventory_data)
        print(f"Inventory predictions: {predictions}")
        return predictions

    def optimize_supply_chain(self):
        print("Optimizing supply chain based on predictions")
        optimization_plan = self.model.optimize(self.inventory_data)
        print(f"Supply chain optimization plan: {optimization_plan}")
        return optimization_plan
