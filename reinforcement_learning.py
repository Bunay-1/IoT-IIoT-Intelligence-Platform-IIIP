"""
Reinforcement Learning Engine for IoT process optimization
"""

import json
import logging
import os
import random
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ProcessEnvironment:
    """Environment for reinforcement learning in manufacturing processes."""

    def __init__(
        self,
        parameter_ranges: Dict[str, Tuple[float, float]],
        target_metrics: List[str],
    ):
        """
        Initialize the manufacturing process environment.

        Args:
            parameter_ranges: Dict of parameter names to (min, max) ranges
            target_metrics: List of metrics to optimize
        """
        self.parameter_ranges = parameter_ranges
        self.target_metrics = target_metrics
        self.current_state = {}
        self.episode_history = []

    def reset(self) -> Dict[str, float]:
        """Reset environment to initial state."""
        self.current_state = {}
        for param, (min_val, max_val) in self.parameter_ranges.items():
            self.current_state[param] = (min_val + max_val) / 2  # Start at middle

        self.episode_history = []
        return self.current_state.copy()

    def step(self, action: Dict[str, float]) -> Tuple[Dict[str, float], float, bool]:
        """
        Take an action and return next state, reward, and done flag.

        Args:
            action: Dictionary of parameter adjustments

        Returns:
            Tuple of (next_state, reward, done)
        """
        # Apply action to current state
        next_state = self.current_state.copy()
        for param, adjustment in action.items():
            if param in next_state:
                min_val, max_val = self.parameter_ranges[param]
                next_state[param] = np.clip(
                    next_state[param] + adjustment, min_val, max_val
                )

        # Simulate process outcome (in real implementation, this would call actual process)
        reward = self._calculate_reward(next_state)

        # Check if episode is done (e.g., reached target or max steps)
        done = len(self.episode_history) >= 100  # Max steps per episode

        # Store transition
        self.episode_history.append(
            {
                "state": self.current_state.copy(),
                "action": action,
                "next_state": next_state.copy(),
                "reward": reward,
            }
        )

        self.current_state = next_state
        return next_state.copy(), reward, done

    def _calculate_reward(self, state: Dict[str, float]) -> float:
        """Calculate reward based on process state."""
        # This is a simplified reward function
        # In real implementation, this would be based on actual process metrics

        reward = 0

        # Reward for staying within optimal ranges
        optimal_ranges = {
            "speed": (100, 200),  # RPM
            "feed_rate": (0.1, 0.5),  # mm/rev
            "temperature": (20, 80),  # Celsius
            "vibration": (0, 2.0),  # mm/s
        }

        for param, value in state.items():
            if param in optimal_ranges:
                min_opt, max_opt = optimal_ranges[param]
                if min_opt <= value <= max_opt:
                    reward += 10  # Bonus for optimal range
                elif value < min_opt or value > max_opt:
                    reward -= 5  # Penalty for out of range

        # Additional rewards/penalties based on parameter combinations
        if "speed" in state and "feed_rate" in state:
            speed_feed_ratio = state["speed"] / max(state["feed_rate"], 0.01)
            if 100 <= speed_feed_ratio <= 500:  # Optimal ratio
                reward += 15
            else:
                reward -= 10

        return reward

    def get_state_space_size(self) -> int:
        """Get the size of the state space."""
        return len(self.parameter_ranges)

    def get_action_space_size(self) -> int:
        """Get the size of the action space."""
        return (
            len(self.parameter_ranges) * 3
        )  # 3 actions per parameter: decrease, maintain, increase


class QLearningAgent:
    """Q-Learning agent for process optimization."""

    def __init__(
        self,
        state_space: int,
        action_space: int,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        exploration_rate: float = 1.0,
        exploration_decay: float = 0.995,
    ):
        """
        Initialize Q-Learning agent.

        Args:
            state_space: Number of state variables
            action_space: Number of possible actions
            learning_rate: Learning rate (alpha)
            discount_factor: Discount factor (gamma)
            exploration_rate: Initial exploration rate (epsilon)
            exploration_decay: Exploration rate decay
        """
        self.state_space = state_space
        self.action_space = action_space
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.min_exploration_rate = 0.01

        # Q-table: state -> action -> q_value
        self.q_table = defaultdict(lambda: defaultdict(float))

        # Action mappings for continuous parameters
        self.action_mappings = {
            0: -1.0,  # Decrease
            1: 0.0,  # Maintain
            2: 1.0,  # Increase
        }

    def discretize_state(self, state: Dict[str, float]) -> str:
        """Convert continuous state to discrete state key."""
        # Simple discretization: round to nearest integer
        discrete_state = {}
        for param, value in state.items():
            discrete_state[param] = round(value, 1)  # Round to 1 decimal place

        return json.dumps(discrete_state, sort_keys=True)

    def get_action(self, state: Dict[str, float]) -> Dict[str, float]:
        """Choose action using epsilon-greedy policy."""
        state_key = self.discretize_state(state)

        if random.random() < self.exploration_rate:
            # Explore: random action
            action = {}
            for param in state.keys():
                action[param] = random.choice(list(self.action_mappings.values()))
        else:
            # Exploit: best action
            action = self._get_best_action(state_key)

        return action

    def _get_best_action(self, state_key: str) -> Dict[str, float]:
        """Get the best action for a state."""
        best_action = {}
        max_q = float("-inf")

        # Try all possible action combinations (simplified)
        for action_combo in self._generate_action_combinations(
            len(self.q_table[state_key])
        ):
            q_value = self.q_table[state_key][json.dumps(action_combo, sort_keys=True)]
            if q_value > max_q:
                max_q = q_value
                best_action = action_combo

        # If no actions explored, return default
        if not best_action:
            best_action = {f"param_{i}": 0.0 for i in range(self.state_space)}

        return best_action

    def _generate_action_combinations(self, n_params: int) -> List[Dict[str, float]]:
        """Generate possible action combinations."""
        # Simplified: only try maintain action for all parameters
        return [{f"param_{i}": 0.0 for i in range(n_params)}]

    def update_q_table(
        self,
        state: Dict[str, float],
        action: Dict[str, float],
        reward: float,
        next_state: Dict[str, float],
    ):
        """Update Q-table using Q-learning update rule."""
        state_key = self.discretize_state(state)
        next_state_key = self.discretize_state(next_state)
        action_key = json.dumps(action, sort_keys=True)

        # Get current Q value
        current_q = self.q_table[state_key][action_key]

        # Get max Q value for next state
        next_max_q = (
            max(self.q_table[next_state_key].values())
            if self.q_table[next_state_key]
            else 0
        )

        # Q-learning update
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * next_max_q - current_q
        )

        self.q_table[state_key][action_key] = new_q

        # Decay exploration rate
        self.exploration_rate = max(
            self.min_exploration_rate, self.exploration_rate * self.exploration_decay
        )

    def get_policy(self) -> Dict[str, Any]:
        """Get the learned policy."""
        policy = {}
        for state_key, actions in self.q_table.items():
            if actions:
                best_action = max(actions.items(), key=lambda x: x[1])
                policy[state_key] = {
                    "action": json.loads(best_action[0]),
                    "q_value": best_action[1],
                }

        return policy


class DeepQLearningAgent:
    """Deep Q-Learning agent using neural network approximation."""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.001,
        memory_size: int = 10000,
    ):
        """
        Initialize Deep Q-Learning agent.

        Args:
            state_dim: Dimension of state space
            action_dim: Dimension of action space
            learning_rate: Learning rate for neural network
            memory_size: Size of experience replay buffer
        """
        try:
            import tensorflow as tf
            from tensorflow.keras.layers import Dense
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.optimizers import Adam

            self.tf = tf
            self.keras = tf.keras

            # Build neural network
            self.model = Sequential(
                [
                    Dense(64, activation="relu", input_shape=(state_dim,)),
                    Dense(64, activation="relu"),
                    Dense(action_dim, activation="linear"),
                ]
            )

            self.model.compile(optimizer=Adam(learning_rate=learning_rate), loss="mse")

            # Target network for stability
            self.target_model = self._build_target_model()

            self.memory = []
            self.memory_size = memory_size
            self.batch_size = 32
            self.gamma = 0.95
            self.epsilon = 1.0
            self.epsilon_decay = 0.995
            self.min_epsilon = 0.01
            self.update_target_freq = 100
            self.step_count = 0

        except ImportError:
            logger.warning("TensorFlow not available. Deep Q-Learning disabled.")
            self.model = None

    def _build_target_model(self):
        """Build target network."""
        if self.model:
            target_model = self.keras.models.clone_model(self.model)
            target_model.set_weights(self.model.get_weights())
            return target_model
        return None

    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer."""
        if len(self.memory) >= self.memory_size:
            self.memory.pop(0)
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        """Choose action based on current state."""
        if np.random.rand() <= self.epsilon:
            return np.random.randint(self.action_dim)

        if self.model:
            q_values = self.model.predict(state.reshape(1, -1), verbose=0)
            return np.argmax(q_values[0])

        return 0

    def replay(self):
        """Train on batch from experience replay."""
        if len(self.memory) < self.batch_size or not self.model:
            return

        batch = np.random.choice(len(self.memory), self.batch_size)
        states, targets = [], []

        for idx in batch:
            state, action, reward, next_state, done = self.memory[idx]

            if done:
                target = reward
            else:
                target = reward + self.gamma * np.max(
                    self.target_model.predict(next_state.reshape(1, -1), verbose=0)[0]
                )

            target_q = self.model.predict(state.reshape(1, -1), verbose=0)[0]
            target_q[action] = target

            states.append(state)
            targets.append(target_q)

        self.model.fit(
            np.array(states),
            np.array(targets),
            epochs=1,
            verbose=0,
            batch_size=self.batch_size,
        )

        # Update epsilon
        if self.epsilon > self.min_epsilon:
            self.epsilon *= self.epsilon_decay

        # Update target network
        self.step_count += 1
        if self.step_count % self.update_target_freq == 0:
            self.target_model.set_weights(self.model.get_weights())


class ReinforcementLearningEngine:
    """Main reinforcement learning engine for process optimization."""

    def __init__(
        self,
        parameter_ranges: Dict[str, Tuple[float, float]],
        target_metrics: List[str],
        use_deep_q: bool = False,
    ):
        """
        Initialize RL engine.

        Args:
            parameter_ranges: Parameter ranges for optimization
            target_metrics: Metrics to optimize
            use_deep_q: Whether to use Deep Q-Learning
        """
        self.environment = ProcessEnvironment(parameter_ranges, target_metrics)
        self.use_deep_q = use_deep_q

        if use_deep_q:
            state_dim = len(parameter_ranges)
            action_dim = len(parameter_ranges) * 3  # 3 actions per parameter
            self.agent = DeepQLearningAgent(state_dim, action_dim)
        else:
            state_space = len(parameter_ranges)
            action_space = len(parameter_ranges) * 3
            self.agent = QLearningAgent(state_space, action_space)

        self.training_history = []
        self.best_parameters = {}

    async def train(self, episodes: int = 1000, max_steps: int = 100) -> Dict[str, Any]:
        """Train the RL agent."""
        logger.info(f"Starting RL training with {episodes} episodes")

        start_time = time.time()
        episode_rewards = []

        for episode in range(episodes):
            state = self.environment.reset()
            episode_reward = 0
            done = False
            steps = 0

            while not done and steps < max_steps:
                # Get action from agent
                if self.use_deep_q:
                    # Convert state dict to array for deep learning
                    state_array = np.array(list(state.values()))
                    action_idx = self.agent.act(state_array)
                    # Convert action index to parameter adjustments
                    action = self._index_to_action(action_idx, state.keys())
                else:
                    action = self.agent.get_action(state)

                # Take action in environment
                next_state, reward, done = self.environment.step(action)
                episode_reward += reward

                # Store experience
                if self.use_deep_q:
                    next_state_array = np.array(list(next_state.values()))
                    self.agent.remember(
                        state_array, action_idx, reward, next_state_array, done
                    )

                # Update agent
                if not self.use_deep_q:
                    self.agent.update_q_table(state, action, reward, next_state)

                state = next_state
                steps += 1

            # Train deep Q network
            if self.use_deep_q:
                self.agent.replay()

            episode_rewards.append(episode_reward)

            if episode % 100 == 0:
                avg_reward = np.mean(episode_rewards[-100:])
                logger.info(f"Episode {episode}: Avg Reward = {avg_reward:.2f}")

        training_time = time.time() - start_time

        # Extract best parameters
        self.best_parameters = self._find_best_parameters()

        results = {
            "episodes": episodes,
            "training_time": training_time,
            "average_reward": np.mean(episode_rewards),
            "best_reward": max(episode_rewards),
            "final_epsilon": getattr(self.agent, "epsilon", None),
            "best_parameters": self.best_parameters,
            "convergence_episode": np.argmax(episode_rewards),
        }

        logger.info(f"RL training completed. Best reward: {results['best_reward']:.2f}")
        return results

    def _index_to_action(
        self, action_idx: int, param_names: List[str]
    ) -> Dict[str, float]:
        """Convert action index to parameter adjustments."""
        action = {}
        n_params = len(param_names)

        for i, param in enumerate(param_names):
            action_type = (action_idx // (3**i)) % 3
            if action_type == 0:
                action[param] = -1.0  # Decrease
            elif action_type == 1:
                action[param] = 0.0  # Maintain
            else:
                action[param] = 1.0  # Increase

        return action

    def _find_best_parameters(self) -> Dict[str, float]:
        """Find the best parameters from training history."""
        if not self.environment.episode_history:
            return {}

        # Find episode with highest reward
        best_episode = max(self.environment.episode_history, key=lambda x: x["reward"])
        return best_episode["next_state"]

    def optimize_parameters(
        self, current_parameters: Dict[str, float]
    ) -> Dict[str, float]:
        """Optimize parameters for given current state."""
        if not self.best_parameters:
            logger.warning("No trained parameters available, returning current")
            return current_parameters

        # Simple optimization: move towards best parameters
        optimized = {}
        for param, current_value in current_parameters.items():
            if param in self.best_parameters:
                best_value = self.best_parameters[param]
                # Gradual adjustment
                adjustment = (best_value - current_value) * 0.1
                optimized[param] = current_value + adjustment
            else:
                optimized[param] = current_value

        return optimized

    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics."""
        return {
            "agent_type": "Deep Q-Learning" if self.use_deep_q else "Q-Learning",
            "best_parameters": self.best_parameters,
            "episodes_trained": len(self.training_history),
            "environment_info": {
                "parameters": list(self.environment.parameter_ranges.keys()),
                "target_metrics": self.environment.target_metrics,
            },
        }

    def save_model(self, filepath: str):
        """Save the trained RL model."""
        try:
            model_data = {
                "agent": self.agent,
                "environment": self.environment,
                "best_parameters": self.best_parameters,
                "use_deep_q": self.use_deep_q,
                "saved_at": datetime.now().isoformat(),
            }

            joblib.dump(model_data, filepath)
            logger.info(f"RL model saved to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save RL model: {e}")
            raise

    def load_model(self, filepath: str):
        """Load a trained RL model."""
        try:
            model_data = joblib.load(filepath)
            self.agent = model_data["agent"]
            self.environment = model_data["environment"]
            self.best_parameters = model_data["best_parameters"]
            self.use_deep_q = model_data["use_deep_q"]

            logger.info(f"RL model loaded from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load RL model: {e}")
            raise


# Global RL engine instance
rl_engine = ReinforcementLearningEngine(
    parameter_ranges={
        "speed": (50, 300),  # RPM
        "feed_rate": (0.05, 1.0),  # mm/rev
        "temperature": (15, 100),  # Celsius
        "vibration": (0, 5.0),  # mm/s
    },
    target_metrics=["efficiency", "quality", "energy_consumption"],
)
