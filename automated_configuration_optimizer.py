import datetime
import numpy as np
from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args
import matplotlib.pyplot as plt
from skopt.plots import plot_convergence, plot_objective


class SimulatedSystem:
    """
    A mock system to simulate a real-world application whose performance
    we want to optimize. The performance is a function of several configuration
    parameters.
    """
    def __init__(self):
        # Define the 'secret' optimal parameters for this system
        self.optimal_params = {
            'learning_rate': 0.05,
            'num_layers': 4,
            'dropout': 0.2,
            'optimizer': 'Adam'
        }
        print(f"Simulated system initialized. The hidden optimal is near {self.optimal_params}")

    def evaluate_performance(self, learning_rate, num_layers, dropout, optimizer):
        """
        Evaluates the performance for a given set of parameters.
        The function is designed to have a global minimum that the optimizer should find.
        Lower return values mean better performance.
        """
        # A complex quadratic function to simulate performance response
        # The function is -( (x-x_opt)^2 + (y-y_opt)^2 + ... )
        # We negate it because gp_minimize finds a minimum.

        # Penalty for choosing a sub-optimal optimizer
        optimizer_penalty = 0 if optimizer == self.optimal_params['optimizer'] else 1.5

        # Calculate squared error from optimal values
        error = (
            ((learning_rate - self.optimal_params['learning_rate']) * 20)**2 +
            ((num_layers - self.optimal_params['num_layers']) * 0.5)**2 +
            ((dropout - self.optimal_params['dropout']) * 10)**2 +
            optimizer_penalty
        )

        # Add some random noise to make it more realistic
        noise = np.random.normal(0, 0.05)

        performance_score = error + noise

        # Simulate time delay for evaluation
        import time
        time.sleep(np.random.uniform(0.1, 0.3))

        return performance_score


class AutomatedConfigurationOptimizer:
    """
    An engine that uses Bayesian Optimization to find the best configuration
    for a given system.
    """
    def __init__(self, system_to_optimize, search_space):
        """
        Args:
            system_to_optimize: An object with an 'evaluate_performance' method.
            search_space (list): A list of skopt dimensions (Real, Integer, Categorical).
        """
        self.system = system_to_optimize
        self.search_space = search_space
        self.result = None
        self.best_config = None
        self.best_performance = float('inf')

    def optimize_configuration(self, n_calls=50):
        """
        Runs the Bayesian Optimization process.

        Args:
            n_calls (int): The number of evaluations to perform.
        """
        print(f"--- Starting Bayesian Optimization with {n_calls} calls ---")

        # use_named_args decorator allows passing keyword arguments to the objective function
        dimensions = [dim for dim in self.search_space]

        @use_named_args(dimensions=dimensions)
        def objective(**params):
            """
            The objective function that gp_minimize will try to minimize.
            It calls the system's evaluation function and returns the performance score.
            """
            performance = self.system.evaluate_performance(**params)
            print(f"Tested params: {params} -> Performance: {performance:.4f}")
            return performance

        # Run the optimization
        self.result = gp_minimize(
            objective,
            self.search_space,
            n_calls=n_calls,
            random_state=42,
            n_random_starts=10
        )

        # Extract best results
        self.best_performance = self.result.fun
        best_params_list = self.result.x

        param_names = [dim.name for dim in self.search_space]
        self.best_config = dict(zip(param_names, best_params_list))

        print("\n--- Optimization Complete ---")
        print(f"Best performance score found: {self.best_performance:.4f}")
        print(f"Best configuration: {self.best_config}")

        return self.best_config

    def get_best_configuration(self):
        """
        Returns the best configuration found after optimization.
        """
        return self.best_config

    def plot_results(self):
        """
        Generates and saves plots visualizing the optimization process.
        """
        if self.result is None:
            print("Optimization has not been run yet. No results to plot.")
            return

        print("\n--- Generating Optimization Plots ---")

        # Plot convergence
        plt.figure(figsize=(10, 6))
        plot_convergence(self.result)
        plt.title('Convergence Plot')
        plt.xlabel('Number of Calls')
        plt.ylabel('Objective Function Value (Performance Score)')
        plt.grid(True)
        convergence_plot_file = 'optimization_convergence.png'
        plt.savefig(convergence_plot_file)
        plt.close()
        print(f"Convergence plot saved to {convergence_plot_file}")

        # Plot objective function (and partial dependence plots)
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            plot_objective(self.result, dimensions=[dim.name for dim in self.search_space])
            fig.suptitle('Objective Function Landscape')
            objective_plot_file = 'optimization_objective.png'
            plt.savefig(objective_plot_file)
            plt.close(fig)
            print(f"Objective plot saved to {objective_plot_file}")
        except Exception as e:
            print(f"Could not generate objective plot. This may happen with categorical variables. Error: {e}")


if __name__ == '__main__':
    # 1. Define the search space for the system's parameters
    search_space = [
        Real(0.001, 0.2, name='learning_rate', prior='log-uniform'),
        Integer(1, 8, name='num_layers'),
        Real(0.1, 0.5, name='dropout'),
        Categorical(['Adam', 'SGD', 'RMSprop'], name='optimizer')
    ]

    # 2. Initialize the system we want to optimize
    simulated_system = SimulatedSystem()

    # 3. Initialize the optimizer with the system and its search space
    optimizer = AutomatedConfigurationOptimizer(
        system_to_optimize=simulated_system,
        search_space=search_space
    )

    # 4. Run the optimization process
    # Using a smaller number of calls for a quick demonstration
    best_config = optimizer.optimize_configuration(n_calls=30)

    # 5. Generate and save the visualization plots
    optimizer.plot_results()

    print("\n--- Main script finished ---")
    print(f"The best overall configuration found is: {best_config}")
