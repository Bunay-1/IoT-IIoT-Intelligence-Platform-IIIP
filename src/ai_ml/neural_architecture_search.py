"""
Neural Architecture Search for IoT IIoT Platform
Automated neural network architecture optimization
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class NetworkBlock(nn.Module):
    """Basic building block for neural networks."""

    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3):
        super().__init__()
        self.conv = nn.Conv1d(in_channels, out_channels, kernel_size, padding=kernel_size//2)
        self.bn = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU()

    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))


class SearchedNetwork(nn.Module):
    """Neural network with searched architecture."""

    def __init__(self, architecture: Dict[str, Any], input_dim: int, output_dim: int):
        super().__init__()
        self.architecture = architecture

        layers = []
        current_dim = input_dim

        # Build layers based on architecture
        for layer_config in architecture['layers']:
            layer_type = layer_config['type']
            if layer_type == 'conv':
                out_channels = layer_config['out_channels']
                kernel_size = layer_config.get('kernel_size', 3)
                layers.append(NetworkBlock(current_dim, out_channels, kernel_size))
                current_dim = out_channels
            elif layer_type == 'linear':
                out_features = layer_config['out_features']
                layers.append(nn.Linear(current_dim, out_features))
                layers.append(nn.ReLU())
                current_dim = out_features
            elif layer_type == 'dropout':
                rate = layer_config.get('rate', 0.5)
                layers.append(nn.Dropout(rate))

        self.layers = nn.Sequential(*layers)

        # Output layer
        self.output = nn.Linear(current_dim, output_dim)

    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)  # Add channel dimension for 1D conv
        x = self.layers(x)
        if x.dim() > 2:
            x = x.mean(dim=-1)  # Global average pooling
        return self.output(x)


class ArchitectureSearchSpace:
    """Search space for neural architectures."""

    def __init__(self):
        self.layer_types = ['conv', 'linear', 'dropout']
        self.max_layers = 10
        self.max_channels = 256
        self.max_features = 1024

    def sample_architecture(self) -> Dict[str, Any]:
        """Sample a random architecture."""
        num_layers = np.random.randint(2, self.max_layers + 1)

        layers = []
        for i in range(num_layers):
            layer_type = np.random.choice(self.layer_types, p=[0.4, 0.4, 0.2])

            if layer_type == 'conv':
                out_channels = np.random.randint(16, self.max_channels + 1)
                kernel_size = np.random.choice([1, 3, 5])
                layers.append({
                    'type': 'conv',
                    'out_channels': int(out_channels),
                    'kernel_size': int(kernel_size)
                })
            elif layer_type == 'linear':
                out_features = np.random.randint(32, self.max_features + 1)
                layers.append({
                    'type': 'linear',
                    'out_features': int(out_features)
                })
            elif layer_type == 'dropout':
                rate = np.random.uniform(0.1, 0.5)
                layers.append({
                    'type': 'dropout',
                    'rate': float(rate)
                })

        return {'layers': layers}

    def mutate_architecture(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Mutate an existing architecture."""
        new_arch = json.loads(json.dumps(architecture))  # Deep copy

        # Random mutation
        mutation_type = np.random.choice(['add_layer', 'remove_layer', 'modify_layer'])

        if mutation_type == 'add_layer' and len(new_arch['layers']) < self.max_layers:
            # Add random layer
            position = np.random.randint(0, len(new_arch['layers']) + 1)
            new_layer = self.sample_architecture()['layers'][0]
            new_arch['layers'].insert(position, new_layer)

        elif mutation_type == 'remove_layer' and len(new_arch['layers']) > 2:
            # Remove random layer
            position = np.random.randint(0, len(new_arch['layers']))
            new_arch['layers'].pop(position)

        elif mutation_type == 'modify_layer' and new_arch['layers']:
            # Modify random layer
            position = np.random.randint(0, len(new_arch['layers']))
            layer = new_arch['layers'][position]

            if layer['type'] == 'conv':
                if np.random.random() < 0.5:
                    layer['out_channels'] = int(np.random.randint(16, self.max_channels + 1))
                else:
                    layer['kernel_size'] = int(np.random.choice([1, 3, 5]))
            elif layer['type'] == 'linear':
                layer['out_features'] = int(np.random.randint(32, self.max_features + 1))
            elif layer['type'] == 'dropout':
                layer['rate'] = float(np.random.uniform(0.1, 0.5))

        return new_arch


class EvolutionarySearch:
    """Evolutionary algorithm for architecture search."""

    def __init__(self, population_size: int = 20, generations: int = 10):
        self.population_size = population_size
        self.generations = generations
        self.search_space = ArchitectureSearchSpace()
        self.population = []
        self.fitness_scores = []

    def initialize_population(self):
        """Initialize random population."""
        self.population = [
            self.search_space.sample_architecture()
            for _ in range(self.population_size)
        ]
        self.fitness_scores = [0.0] * self.population_size

    def evolve(self, fitness_function):
        """Run evolutionary search."""
        self.initialize_population()

        for generation in range(self.generations):
            logger.info(f"Generation {generation + 1}/{self.generations}")

            # Evaluate fitness
            for i, architecture in enumerate(self.population):
                if self.fitness_scores[i] == 0.0:  # Not evaluated yet
                    self.fitness_scores[i] = fitness_function(architecture)

            # Sort by fitness (higher is better)
            indices = np.argsort(self.fitness_scores)[::-1]
            self.population = [self.population[i] for i in indices]
            self.fitness_scores = [self.fitness_scores[i] for i in indices]

            logger.info(f"Best fitness: {self.fitness_scores[0]:.4f}")

            # Create next generation
            new_population = self.population[:self.population_size // 2]  # Elitism

            while len(new_population) < self.population_size:
                # Select parent
                parent_idx = np.random.choice(
                    len(self.population) // 2,
                    p=np.array(self.fitness_scores[:len(self.population) // 2]) /
                      sum(self.fitness_scores[:len(self.population) // 2])
                )
                parent = self.population[parent_idx]

                # Mutate
                child = self.search_space.mutate_architecture(parent)
                new_population.append(child)

            self.population = new_population
            self.fitness_scores = [0.0] * self.population_size

        return self.population[0], self.fitness_scores[0]


class ReinforcementLearningSearch:
    """Reinforcement Learning-based Neural Architecture Search."""

    def __init__(self, state_dim: int = 50, action_dim: int = 20, hidden_dim: int = 128,
                 learning_rate: float = 0.001, gamma: float = 0.99, epsilon: float = 0.1):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon

        # Neural network for policy
        self.policy_net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1)
        )

        # Neural network for value function
        self.value_net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

        self.policy_optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.value_optimizer = torch.optim.Adam(self.value_net.parameters(), lr=learning_rate)

        self.search_space = ArchitectureSearchSpace()
        self.memory = []

    def get_state_representation(self, architecture: Dict[str, Any]) -> torch.Tensor:
        """Convert architecture to state representation."""
        # Simple encoding: flatten layer parameters
        state = []
        for layer in architecture['layers']:
            if layer['type'] == 'conv':
                state.extend([1, layer.get('out_channels', 32) / 256, layer.get('kernel_size', 3) / 5])
            elif layer['type'] == 'linear':
                state.extend([2, layer.get('out_features', 64) / 1024, 0])
            elif layer['type'] == 'dropout':
                state.extend([3, layer.get('rate', 0.5), 0])

        # Pad or truncate to fixed size
        if len(state) < self.state_dim:
            state.extend([0] * (self.state_dim - len(state)))
        else:
            state = state[:self.state_dim]

        return torch.FloatTensor(state)

    def select_action(self, state: torch.Tensor) -> int:
        """Select action using epsilon-greedy policy."""
        if np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)

        with torch.no_grad():
            probs = self.policy_net(state)
            return torch.multinomial(probs, 1).item()

    def get_action_meaning(self, action: int) -> Dict[str, Any]:
        """Convert action index to architecture modification."""
        actions = [
            {'type': 'add_conv', 'params': {'out_channels': 32, 'kernel_size': 3}},
            {'type': 'add_conv', 'params': {'out_channels': 64, 'kernel_size': 3}},
            {'type': 'add_conv', 'params': {'out_channels': 128, 'kernel_size': 5}},
            {'type': 'add_linear', 'params': {'out_features': 128}},
            {'type': 'add_linear', 'params': {'out_features': 256}},
            {'type': 'add_linear', 'params': {'out_features': 512}},
            {'type': 'add_dropout', 'params': {'rate': 0.2}},
            {'type': 'add_dropout', 'params': {'rate': 0.5}},
            {'type': 'modify_channels', 'params': {'factor': 1.5}},
            {'type': 'modify_channels', 'params': {'factor': 0.7}},
            {'type': 'modify_features', 'params': {'factor': 1.5}},
            {'type': 'modify_features', 'params': {'factor': 0.7}},
            {'type': 'remove_layer', 'params': {}},
            {'type': 'swap_layers', 'params': {}},
            {'type': 'increase_kernel', 'params': {}},
            {'type': 'decrease_kernel', 'params': {}},
            {'type': 'optimize_depth', 'params': {}},
            {'type': 'optimize_width', 'params': {}}
        ]
        return actions[action % len(actions)]

    def apply_action(self, architecture: Dict[str, Any], action: int) -> Dict[str, Any]:
        """Apply action to architecture."""
        action_meaning = self.get_action_meaning(action)
        new_arch = json.loads(json.dumps(architecture))  # Deep copy

        if action_meaning['type'] == 'add_conv':
            params = action_meaning['params']
            new_layer = {
                'type': 'conv',
                'out_channels': params['out_channels'],
                'kernel_size': params['kernel_size']
            }
            new_arch['layers'].append(new_layer)

        elif action_meaning['type'] == 'add_linear':
            params = action_meaning['params']
            new_layer = {
                'type': 'linear',
                'out_features': params['out_features']
            }
            new_arch['layers'].append(new_layer)

        elif action_meaning['type'] == 'add_dropout':
            params = action_meaning['params']
            new_layer = {
                'type': 'dropout',
                'rate': params['rate']
            }
            new_arch['layers'].append(new_layer)

        elif action_meaning['type'] == 'modify_channels':
            factor = action_meaning['params']['factor']
            for layer in new_arch['layers']:
                if layer['type'] == 'conv' and 'out_channels' in layer:
                    layer['out_channels'] = max(16, int(layer['out_channels'] * factor))

        elif action_meaning['type'] == 'modify_features':
            factor = action_meaning['params']['factor']
            for layer in new_arch['layers']:
                if layer['type'] == 'linear' and 'out_features' in layer:
                    layer['out_features'] = max(32, int(layer['out_features'] * factor))

        elif action_meaning['type'] == 'remove_layer' and len(new_arch['layers']) > 2:
            new_arch['layers'].pop()

        elif action_meaning['type'] == 'swap_layers' and len(new_arch['layers']) > 1:
            idx1, idx2 = np.random.choice(len(new_arch['layers']), 2, replace=False)
            new_arch['layers'][idx1], new_arch['layers'][idx2] = new_arch['layers'][idx2], new_arch['layers'][idx1]

        elif action_meaning['type'] == 'increase_kernel':
            for layer in new_arch['layers']:
                if layer['type'] == 'conv' and 'kernel_size' in layer:
                    layer['kernel_size'] = min(7, layer['kernel_size'] + 2)

        elif action_meaning['type'] == 'decrease_kernel':
            for layer in new_arch['layers']:
                if layer['type'] == 'conv' and 'kernel_size' in layer:
                    layer['kernel_size'] = max(1, layer['kernel_size'] - 2)

        elif action_meaning['type'] == 'optimize_depth':
            # Remove redundant layers
            optimized_layers = []
            prev_type = None
            for layer in new_arch['layers']:
                if layer['type'] != prev_type or layer['type'] == 'dropout':
                    optimized_layers.append(layer)
                prev_type = layer['type']
            new_arch['layers'] = optimized_layers

        elif action_meaning['type'] == 'optimize_width':
            # Gradually increase width
            for i, layer in enumerate(new_arch['layers']):
                if layer['type'] == 'conv':
                    layer['out_channels'] = min(512, layer['out_channels'] + i * 16)
                elif layer['type'] == 'linear':
                    layer['out_features'] = min(2048, layer['out_features'] + i * 32)

        return new_arch

    def learn(self, state: torch.Tensor, action: int, reward: float, next_state: torch.Tensor, done: bool):
        """Update policy and value networks."""
        # Compute TD target
        with torch.no_grad():
            next_value = self.value_net(next_state) if not done else torch.tensor([0.0])
            td_target = reward + self.gamma * next_value

        # Update value network
        current_value = self.value_net(state)
        value_loss = nn.MSELoss()(current_value, td_target)
        self.value_optimizer.zero_grad()
        value_loss.backward()
        self.value_optimizer.step()

        # Update policy network
        probs = self.policy_net(state)
        action_prob = probs[action]
        advantage = td_target - current_value.detach()

        policy_loss = -torch.log(action_prob) * advantage
        self.policy_optimizer.zero_grad()
        policy_loss.backward()
        self.policy_optimizer.step()

    def search(self, fitness_function, episodes: int = 100, max_steps: int = 50) -> Dict[str, Any]:
        """Run RL-based architecture search."""
        logger.info("Starting RL-based Neural Architecture Search")

        best_architecture = None
        best_fitness = float('-inf')

        for episode in range(episodes):
            # Start with random architecture
            current_arch = self.search_space.sample_architecture()
            current_state = self.get_state_representation(current_arch)
            episode_reward = 0

            for step in range(max_steps):
                # Select action
                action = self.select_action(current_state)

                # Apply action
                next_arch = self.apply_action(current_arch, action)
                next_state = self.get_state_representation(next_arch)

                # Evaluate fitness
                fitness = fitness_function(next_arch)
                reward = fitness - (best_fitness if best_fitness != float('-inf') else 0)

                # Update best
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_architecture = next_arch
                    logger.info(f"New best fitness: {best_fitness:.4f} at episode {episode}, step {step}")

                # Learn
                done = step == max_steps - 1
                self.learn(current_state, action, reward, next_state, done)

                current_arch = next_arch
                current_state = next_state
                episode_reward += reward

            logger.info(f"Episode {episode + 1}/{episodes}, Total Reward: {episode_reward:.4f}, Best Fitness: {best_fitness:.4f}")

        result = {
            'best_architecture': best_architecture,
            'best_fitness': best_fitness,
            'search_method': 'reinforcement_learning',
            'episodes': episodes,
            'max_steps': max_steps,
            'search_timestamp': datetime.now().isoformat()
        }

        logger.info(f"RL-based NAS completed. Best fitness: {best_fitness:.4f}")
        return result


class NeuralArchitectureSearch:
    """
    Neural Architecture Search system.
    Automatically finds optimal neural network architectures.
    """

    def __init__(self, input_dim: int, output_dim: int, device: str = 'cpu', search_method: str = 'evolutionary'):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.device = device
        self.search_method = search_method
        self.search_space = ArchitectureSearchSpace()
        self.evolutionary_search = EvolutionarySearch()
        if search_method == 'rl':
            self.rl_search = ReinforcementLearningSearch()

    def evaluate_architecture(self, architecture: Dict[str, Any],
                            train_data: Tuple[torch.Tensor, torch.Tensor],
                            val_data: Tuple[torch.Tensor, torch.Tensor],
                            max_epochs: int = 10) -> float:
        """Evaluate an architecture's fitness."""
        try:
            # Create model
            model = SearchedNetwork(architecture, self.input_dim, self.output_dim)
            model.to(self.device)

            # Create data loaders
            train_dataset = TensorDataset(*train_data)
            val_dataset = TensorDataset(*val_data)
            train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=32)

            # Training
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.MSELoss() if self.output_dim == 1 else nn.CrossEntropyLoss()

            model.train()
            for epoch in range(max_epochs):
                for inputs, targets in train_loader:
                    inputs, targets = inputs.to(self.device), targets.to(self.device)

                    optimizer.zero_grad()
                    outputs = model(inputs)
                    loss = criterion(outputs.squeeze(), targets)
                    loss.backward()
                    optimizer.step()

            # Evaluation
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for inputs, targets in val_loader:
                    inputs, targets = inputs.to(self.device), targets.to(self.device)
                    outputs = model(inputs)
                    loss = criterion(outputs.squeeze(), targets)
                    val_loss += loss.item()

            val_loss /= len(val_loader)

            # Return negative loss as fitness (higher is better)
            return -val_loss

        except Exception as e:
            logger.error(f"Architecture evaluation failed: {e}")
            return -float('inf')

    async def search(self, train_data: Tuple[np.ndarray, np.ndarray],
                   val_data: Tuple[np.ndarray, np.ndarray]) -> Dict[str, Any]:
        """
        Perform neural architecture search.

        Args:
            train_data: Training data (X, y)
            val_data: Validation data (X, y)

        Returns:
            Best architecture and its performance
        """
        logger.info("Starting Neural Architecture Search")

        # Convert to torch tensors
        X_train = torch.FloatTensor(train_data[0])
        y_train = torch.FloatTensor(train_data[1]) if train_data[1].dtype == np.float32 else torch.LongTensor(train_data[1])
        X_val = torch.FloatTensor(val_data[0])
        y_val = torch.FloatTensor(val_data[1]) if val_data[1].dtype == np.float32 else torch.LongTensor(val_data[1])

        torch_train_data = (X_train, y_train)
        torch_val_data = (X_val, y_val)

        # Define fitness function
        def fitness_func(architecture):
            return self.evaluate_architecture(
                architecture, torch_train_data, torch_val_data
            )

        if self.search_method == 'rl':
            # Run RL search
            result = self.rl_search.search(fitness_func)
            result.update({
                'input_dim': self.input_dim,
                'output_dim': self.output_dim
            })
        else:
            # Run evolutionary search
            best_architecture, best_fitness = self.evolutionary_search.evolve(fitness_func)
            result = {
                'best_architecture': best_architecture,
                'best_fitness': best_fitness,
                'search_method': 'evolutionary',
                'search_timestamp': datetime.now().isoformat(),
                'input_dim': self.input_dim,
                'output_dim': self.output_dim
            }

        logger.info(f"NAS completed. Best fitness: {result['best_fitness']:.4f}")
        return result

    def create_model_from_architecture(self, architecture: Dict[str, Any]) -> SearchedNetwork:
        """Create a model from searched architecture."""
        return SearchedNetwork(architecture, self.input_dim, self.output_dim)


async def run_nas_search(input_dim: int, output_dim: int,
                        train_data: Tuple[np.ndarray, np.ndarray],
                        val_data: Tuple[np.ndarray, np.ndarray],
                        search_method: str = 'evolutionary') -> Dict[str, Any]:
    """
    Run complete NAS search.

    Args:
        input_dim: Input dimension
        output_dim: Output dimension
        train_data: Training data
        val_data: Validation data
        search_method: Search method ('evolutionary' or 'rl')

    Returns:
        Search results
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    nas = NeuralArchitectureSearch(input_dim, output_dim, device, search_method)

    results = await nas.search(train_data, val_data)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"nas_results_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"NAS results saved to {filename}")
    return results


if __name__ == "__main__":
    # Example usage
    import numpy as np

    # Generate sample data
    np.random.seed(42)
    X_train = np.random.randn(1000, 10)
    y_train = np.random.randn(1000, 1)
    X_val = np.random.randn(200, 10)
    y_val = np.random.randn(200, 1)

    async def main():
        results = await run_nas_search(10, 1, (X_train, y_train), (X_val, y_val))
        print(json.dumps(results, indent=2, default=str))

    asyncio.run(main())