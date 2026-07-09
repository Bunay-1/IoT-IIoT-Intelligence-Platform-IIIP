import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class DigitalTwinIntegration:
    def __init__(self, system_data):
        """
        Инициализира интеграцията на дигитален близнак.
        Args:
            system_data (DataFrame): Данни за системата или машината.
        """
        self.system_data = system_data

    def create_digital_twin(self):
        """
        Създава дигитален близнак на системата.
        Returns:
            dict: Параметри на дигиталния близнак.
        """
        digital_twin = {"parameters": self.system_data.mean().to_dict()}
        return digital_twin

    def simulate_changes(self, digital_twin, changes):
        """
        Симулира промени в дигиталния близнак.
        Args:
            digital_twin (dict): Параметри на дигиталния близнак.
            changes (dict): Промени в параметрите.
        Returns:
            dict: Резултати от симулацията.
        """
        for param, change in changes.items():
            if param in digital_twin:
                digital_twin[param] += change

        # Примерна симулация (може да се разшири)
        simulated_results = {
            "performance": np.random.rand(),
            "efficiency": np.random.rand(),
            "risk": np.random.rand(),
        }
        return simulated_results

    def visualize_simulation(self, simulation_results):
        """
        Визуализира резултатите от симулацията.
        Args:
            simulation_results (dict): Резултати от симулацията.
        """
        plt.figure(figsize=(10, 6))
        plt.bar(simulation_results.keys(), simulation_results.values())
        plt.xlabel("Metric")
        plt.ylabel("Value")
        plt.title("Simulation Results")
        plt.show()

    def run(self, changes):
        """
        Стартира процеса на създаване, симулация и визуализация.
        Args:
            changes (dict): Промени в параметрите.
        """
        digital_twin = self.create_digital_twin()
        simulation_results = self.simulate_changes(digital_twin, changes)
        self.visualize_simulation(simulation_results)


# Пример данни за демонстрация
system_data = pd.DataFrame(
    {
        "param_1": [10, 15, 20, 25, 30],
        "param_2": [30, 25, 20, 15, 10],
        "param_3": [5, 10, 15, 20, 25],
    }
)

# Промени в параметрите
changes = {"param_1": 5, "param_2": -10}

# Създаване и стартиране на интеграцията
integration = DigitalTwinIntegration(system_data)
integration.run(changes)
