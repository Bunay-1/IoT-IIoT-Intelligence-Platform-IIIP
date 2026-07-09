"""
Advanced Load Balancing Module - Refactored for Dynamic Simulation

This module implements a sophisticated load balancing system and provides a
dynamic simulation environment to observe its behavior under various conditions.
It has been refactored to use a stateful object-oriented design for clarity
and extensibility.
"""

import asyncio
import random
import time
import math
import hashlib
from collections import deque, defaultdict
from enum import Enum
from typing import Dict, List, Optional, Any

# Use the centralized logger from the utils module
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class LoadBalancingAlgorithm(Enum):
    """Enumeration of available load balancing algorithms."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    AI_PREDICTIVE = "ai_predictive"
    ADAPTIVE = "adaptive"


class ServerState(Enum):
    """Enumeration for the state of a server."""
    HEALTHY = "HEALTHY"
    OVERLOADED = "OVERLOADED"
    UNHEALTHY = "UNHEALTHY"
    MAINTENANCE = "MAINTENANCE"


class Server:
    """
    Represents a backend server, encapsulating its state and performance characteristics.
    """
    def __init__(self, server_id: str, host: str, weight: int = 10, max_connections: int = 1000):
        self.id = server_id
        self.host = host
        self.initial_weight = weight
        self.current_weight = weight
        self.max_connections = max_connections

        # State attributes
        self.state = ServerState.HEALTHY
        self.current_connections = 0
        self.cpu_load = 0.0  # 0.0 to 1.0
        self.last_health_check = time.monotonic()

        # Performance metrics
        self.response_times = deque(maxlen=100)
        self.error_rate = 0.0
        self.success_count = 0
        self.failure_count = 0

    def process_request(self, complexity: float):
        """Simulates processing a request, affecting server load and performance."""
        self.current_connections += 1

        # Calculate an *instantaneous* load for this request's processing time
        # This is more realistic than a slowly accumulating load metric.
        instant_cpu_load = self.current_connections / self.max_connections

        # Simulate response time based on the instantaneous load
        base_latency = 0.05
        load_latency = (instant_cpu_load ** 2) * 0.5  # Exponential penalty for high load
        response_time = base_latency + load_latency + random.uniform(-0.01, 0.01)

        # Success is less likely at very high loads
        is_success = instant_cpu_load < 0.95 and random.random() > instant_cpu_load

        # Simulate completion of the request
        asyncio.get_event_loop().call_later(response_time, self.finish_request, is_success, response_time)
        return response_time, is_success

    def finish_request(self, is_success: bool, response_time: float):
        """Callback for when a request is finished."""
        self.current_connections = max(0, self.current_connections - 1)
        self.response_times.append(response_time)
        if is_success:
            self.success_count += 1
        else:
            self.failure_count += 1

        total_requests = self.success_count + self.failure_count
        if total_requests > 0:
            self.error_rate = self.failure_count / total_requests

    def update_health(self):
        """Periodically updates the server's health based on its state."""
        if self.state == ServerState.MAINTENANCE:
            # While in maintenance, gradually reduce connections and load
            self.current_connections = max(0, self.current_connections - 10)
            return

        # CPU load is now a direct reflection of connection count
        self.cpu_load = self.current_connections / self.max_connections
        avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0

        if self.cpu_load > 0.95 or (self.error_rate > 0.2 and (self.success_count + self.failure_count) > 20):
            self.state = ServerState.UNHEALTHY
        elif self.cpu_load > 0.75 or avg_response > 0.3:
            self.state = ServerState.OVERLOADED
        else:
            self.state = ServerState.HEALTHY
        self.last_health_check = time.monotonic()

    def get_performance_score(self) -> float:
        """Calculates a general performance score for decision-making."""
        if self.state == ServerState.UNHEALTHY or self.state == ServerState.MAINTENANCE:
            return 0.0

        # Penalize high load and connections
        load_penalty = (1 - self.cpu_load)
        connection_penalty = 1 - (self.current_connections / self.max_connections)

        # Combine metrics for a score
        score = (load_penalty * 0.6) + (connection_penalty * 0.4)
        return max(0.0, score)

    def __repr__(self):
        return f"Server({self.id}, State: {self.state.value}, CPU: {self.cpu_load:.2%}, Conns: {self.current_connections})"


class AdvancedLoadBalancing:
    """
    Manages server pools and distributes traffic using various algorithms.
    """
    def __init__(self):
        self.server_pools: Dict[str, List[Server]] = defaultdict(list)
        self.algorithm_configs: Dict[str, Dict[str, Any]] = defaultdict(dict)
        # For Epsilon-Greedy in ADAPTIVE mode
        self.algorithm_rewards = defaultdict(lambda: {'count': 0, 'reward': 0.0})
        self.epsilon = 0.1 # 10% exploration chance

    def create_server_pool(self, pool_name: str, server_configs: List[Dict]):
        """Creates a pool of Server objects."""
        pool = [Server(**config) for config in server_configs]
        self.server_pools[pool_name] = pool
        self.algorithm_configs[pool_name] = {
            "algorithm": LoadBalancingAlgorithm.ADAPTIVE,
            "round_robin_index": 0,
            "ip_hash_seed": random.randint(0, 1000),
            # State for Smooth Weighted Round Robin
            "wrr_state": {server.id: {'current_weight': 0} for server in pool}
        }
        logger.info(f"Created server pool '{pool_name}' with {len(pool)} servers.")

    def get_healthy_servers(self, pool_name: str) -> List[Server]:
        """Returns a list of servers in the pool that are not unhealthy."""
        return [s for s in self.server_pools.get(pool_name, []) if s.state != ServerState.UNHEALTHY]

    def select_server(self, pool_name: str, request_context: Dict) -> Optional[Server]:
        """Selects the best server from a pool based on the configured algorithm."""
        healthy_servers = self.get_healthy_servers(pool_name)
        if not healthy_servers:
            logger.warning(f"No healthy servers available in pool '{pool_name}'.")
            return None

        config = self.algorithm_configs[pool_name]
        algorithm = config['algorithm']

        selector = {
            LoadBalancingAlgorithm.ROUND_ROBIN: self._round_robin,
            LoadBalancingAlgorithm.LEAST_CONNECTIONS: self._least_connections,
            LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN: self._weighted_round_robin,
            LoadBalancingAlgorithm.IP_HASH: self._ip_hash,
            LoadBalancingAlgorithm.AI_PREDICTIVE: self._ai_predictive,
            LoadBalancingAlgorithm.ADAPTIVE: self._adaptive
        }

        selection_func = selector.get(algorithm, self._least_connections)
        return selection_func(healthy_servers, config, request_context)

    # --- ALGORITHMS ---
    def _round_robin(self, servers: List[Server], config: Dict, _: Dict) -> Server:
        index = config['round_robin_index']
        server = servers[index % len(servers)]
        config['round_robin_index'] = (index + 1)
        return server

    def _least_connections(self, servers: List[Server], _: Dict, __: Dict) -> Server:
        return min(servers, key=lambda s: s.current_connections)

    def _ip_hash(self, servers: List[Server], config: Dict, context: Dict) -> Server:
        client_ip = context.get('client_ip', '127.0.0.1')
        hash_input = f"{client_ip}:{config['ip_hash_seed']}"
        hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        return servers[hash_val % len(servers)]

    def _weighted_round_robin(self, servers: List[Server], config: Dict, _: Dict) -> Server:
        """Smooth Weighted Round-Robin, inspired by Nginx."""
        wrr_state = config['wrr_state']
        total_weight = sum(s.initial_weight for s in servers)

        best_server = None
        for server in servers:
            state = wrr_state.setdefault(server.id, {'current_weight': 0})
            state['current_weight'] += server.initial_weight
            if best_server is None or state['current_weight'] > wrr_state[best_server.id]['current_weight']:
                best_server = server

        wrr_state[best_server.id]['current_weight'] -= total_weight
        return best_server

    def _ai_predictive(self, servers: List[Server], _: Dict, context: Dict) -> Server:
        """Predicts server performance based on request and server state."""
        best_server = None
        max_score = -1

        for server in servers:
            # Simple predictive model: performance score minus predicted load increase
            predicted_load_increase = context.get('complexity', 0.5) * 0.1
            score = server.get_performance_score() - predicted_load_increase
            if score > max_score:
                max_score = score
                best_server = server
        return best_server or servers[0]

    def _adaptive(self, servers: List[Server], config: Dict, context: Dict) -> Server:
        """Epsilon-Greedy: Explores different algorithms or exploits the best one."""
        # Determine the best-known algorithm (exploit)
        best_alg_name = max(self.algorithm_rewards, key=lambda k: self.algorithm_rewards[k]['reward'], default=None)

        if random.random() < self.epsilon or not best_alg_name:
            # Explore: pick a random algorithm (excluding adaptive itself)
            alg_choices = [alg for alg in LoadBalancingAlgorithm if alg != LoadBalancingAlgorithm.ADAPTIVE]
            chosen_alg = random.choice(alg_choices)
            logger.debug(f"Adaptive choice: EXPLORE -> {chosen_alg.value}")
        else:
            # Exploit: use the best-known algorithm
            chosen_alg = best_alg_name
            logger.debug(f"Adaptive choice: EXPLOIT -> {chosen_alg.value}")

        # Execute the chosen algorithm
        selector = {
            LoadBalancingAlgorithm.ROUND_ROBIN: self._round_robin,
            LoadBalancingAlgorithm.LEAST_CONNECTIONS: self._least_connections,
            LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN: self._weighted_round_robin,
            LoadBalancingAlgorithm.IP_HASH: self._ip_hash,
            LoadBalancingAlgorithm.AI_PREDICTIVE: self._ai_predictive,
        }
        selection_func = selector.get(chosen_alg, self._least_connections)
        server = selection_func(servers, config, context)

        # Store the algorithm choice to calculate reward later
        context['chosen_algorithm'] = chosen_alg
        return server

    def update_algorithm_reward(self, chosen_alg: LoadBalancingAlgorithm, response_time: float, success: bool):
        """Updates the reward for a given algorithm for adaptive selection."""
        if not chosen_alg or chosen_alg == LoadBalancingAlgorithm.ADAPTIVE:
            return

        # Reward function: lower response time and success are better.
        reward = (1.0 / (response_time + 0.01)) * (1 if success else 0)

        stats = self.algorithm_rewards[chosen_alg]
        # Update via moving average
        stats['reward'] = ((stats['reward'] * stats['count']) + reward) / (stats['count'] + 1)
        stats['count'] += 1
        logger.debug(f"Updated reward for {chosen_alg.value}: {stats['reward']:.2f}")

    async def health_check_pools(self, interval: int = 10):
        """Continuously runs health checks on all servers."""
        while True:
            for pool_name, servers in self.server_pools.items():
                for server in servers:
                    server.update_health()
                logger.info(f"Health check for pool '{pool_name}': {self.get_pool_status(pool_name)}")
            await asyncio.sleep(interval)

    def get_pool_status(self, pool_name: str) -> str:
        """Returns a string summary of the pool's status."""
        servers = self.server_pools.get(pool_name, [])
        if not servers: return "Pool not found."

        counts = defaultdict(int)
        for s in servers:
            counts[s.state.value] += 1

        active_alg = self.algorithm_configs[pool_name]['algorithm'].value
        return f"Alg: {active_alg}, Healthy: {counts['HEALTHY']}, Overloaded: {counts['OVERLOADED']}, Unhealthy: {counts['UNHEALTHY']}"


class TrafficSimulator:
    """
    Generates simulated traffic to test the load balancer.
    """
    def __init__(self, lb: AdvancedLoadBalancing, pool_name: str, duration: int = 60):
        self.lb = lb
        self.pool_name = pool_name
        self.duration = duration
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'server_distribution': defaultdict(int)
        }

    def _generate_request(self) -> Dict:
        """Creates a randomized request context."""
        return {
            "pool_name": self.pool_name,
            "client_ip": f"10.0.{random.randint(0, 255)}.{random.randint(0, 255)}",
            "complexity": random.uniform(0.2, 1.0) # How CPU-intensive the request is
        }

    async def run(self):
        """Runs the traffic simulation for the configured duration."""
        logger.info(f"--- Starting Traffic Simulation for {self.duration} seconds ---")
        end_time = time.monotonic() + self.duration

        asyncio.create_task(self.lb.health_check_pools(5))

        while time.monotonic() < end_time:
            # Dynamic requests per second, lowered to avoid immediate overload
            rps = random.randint(10, 30)

            tasks = []
            for _ in range(rps):
                tasks.append(asyncio.create_task(self.send_request()))

            await asyncio.gather(*tasks)
            await asyncio.sleep(1) # Run this loop once per second

            # Random events
            if random.random() < 0.05: # 5% chance per second
                self._inject_event()

        self._print_summary()

    async def send_request(self):
        """Simulates sending a single request and processing the outcome."""
        request_context = self._generate_request()
        self.stats['total_requests'] += 1

        server = self.lb.select_server(self.pool_name, request_context)

        if not server:
            self.stats['failed_requests'] += 1
            return

        self.stats['server_distribution'][server.id] += 1

        response_time, success = server.process_request(request_context['complexity'])

        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1

        # Update adaptive algorithm rewards
        chosen_alg = request_context.get('chosen_algorithm')
        if chosen_alg:
            self.lb.update_algorithm_reward(chosen_alg, response_time, success)

    def _inject_event(self):
        """Injects a random event like a server failure or maintenance."""
        servers = self.lb.server_pools[self.pool_name]
        if not servers: return

        target_server = random.choice(servers)
        if target_server.state == ServerState.HEALTHY:
            target_server.state = ServerState.MAINTENANCE
            logger.warning(f"EVENT: Server {target_server.id} is now in MAINTENANCE.")
            # Schedule recovery
            asyncio.get_event_loop().call_later(20, self._recover_server, target_server)

    def _recover_server(self, server: Server):
        server.state = ServerState.HEALTHY
        logger.warning(f"EVENT: Server {server.id} has recovered from maintenance.")

    def _print_summary(self):
        """Prints a summary of the simulation results."""
        logger.info("--- Simulation Complete: Summary ---")
        logger.info(f"Total Requests: {self.stats['total_requests']}")
        logger.info(f"Successful: {self.stats['successful_requests']} ({self.stats['successful_requests']/self.stats['total_requests']:.2%})")
        logger.info(f"Failed: {self.stats['failed_requests']}")
        logger.info("Server Distribution:")
        for server_id, count in sorted(self.stats['server_distribution'].items()):
            logger.info(f"  - {server_id}: {count} requests ({count/self.stats['total_requests']:.2%})")
        logger.info("Final Algorithm Rewards:")
        for alg, reward_stats in self.lb.algorithm_rewards.items():
            logger.info(f"  - {alg.value}: Avg Reward = {reward_stats['reward']:.2f} (from {reward_stats['count']} samples)")


async def main():
    """Main entry point to set up and run the simulation."""
    lb = AdvancedLoadBalancing()

    # Create a server pool
    pool_name = "api_gateway"
    servers_config = [
        {"server_id": "api-1", "host": "10.0.1.1", "weight": 50},
        {"server_id": "api-2", "host": "10.0.1.2", "weight": 100},
        {"server_id": "api-3", "host": "10.0.1.3", "weight": 75},
        {"server_id": "api-4", "host": "10.0.1.4", "weight": 75},
    ]
    lb.create_server_pool(pool_name, servers_config)

    # Set the pool to use the adaptive algorithm
    lb.algorithm_configs[pool_name]['algorithm'] = LoadBalancingAlgorithm.ADAPTIVE

    # Run the simulation
    simulator = TrafficSimulator(lb, pool_name, duration=60)
    await simulator.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulation cancelled by user.")
