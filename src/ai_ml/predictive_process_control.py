class PredictiveProcessControl:
    def __init__(self, process_data):
        self.process_data = process_data

    def control_process(self):
        print("Controlling process using AI")
        results = self.process_data.apply_controls()
        print(f"Process controlled: {results}")
        return results
