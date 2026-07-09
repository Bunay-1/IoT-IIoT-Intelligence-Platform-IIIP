import numpy as np
import heapq
import random
import time
import os

class AutonomousVehicle:
    """Represents a single autonomous vehicle in the fleet."""
    def __init__(self, v_id, position):
        self.id = v_id
        self.position = position
        self.status = "idle"  # idle, en_route, charging
        self.route = []
        self.job_id = None
        self.battery = 100.0

    def move(self):
        """Moves the vehicle one step along its route."""
        if self.status == "en_route" and self.route:
            self.position = self.route.pop(0)
            self.battery -= 0.5 # Simulate battery consumption
            if not self.route:
                self.status = "idle"
                print(f"{self.id} reached its destination at {self.position}.")

    def __repr__(self):
        return f"{self.id} @ {self.position} ({self.status})"

class TransportationManager:
    """
    Manages a fleet of autonomous vehicles, optimizes routes, and simulates a dynamic transportation environment.
    """
    def __init__(self, map_size=(20, 20), num_vehicles=5):
        self.map_size = map_size
        self.grid = np.zeros(map_size)  # 0: empty, 1: obstacle/heavy traffic
        self.vehicles = {}
        self.jobs = {}

        self._initialize_environment()
        self._initialize_vehicles(num_vehicles)

    def _initialize_environment(self):
        """Creates a random environment with some obstacles."""
        for _ in range(int(self.map_size[0] * self.map_size[1] * 0.1)): # 10% obstacles
            x, y = random.randint(0, self.map_size[0] - 1), random.randint(0, self.map_size[1] - 1)
            self.grid[x][y] = 1
        print("Initialized transportation grid with random obstacles.")

    def _initialize_vehicles(self, num_vehicles):
        """Deploys a fleet of autonomous vehicles at random locations."""
        for i in range(num_vehicles):
            v_id = f"AV-{i+1}"
            while True:
                start_pos = (random.randint(0, self.map_size[0] - 1), random.randint(0, self.map_size[1] - 1))
                if self.grid[start_pos[0]][start_pos[1]] == 0:
                    break
            self.vehicles[v_id] = AutonomousVehicle(v_id, start_pos)
        print(f"Deployed {num_vehicles} autonomous vehicles.")

    def optimize_route_a_star(self, start, end):
        """Finds the shortest path using the A* algorithm."""
        rows, cols = self.map_size

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = { (r, c): float('inf') for r in range(rows) for c in range(cols) }
        g_score[start] = 0
        f_score = { (r, c): float('inf') for r in range(rows) for c in range(cols) }
        f_score[start] = heuristic(start, end)

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dr, current[1] + dc)

                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                    if self.grid[neighbor[0]][neighbor[1]] == 1: # Obstacle
                        continue

                    tentative_g_score = g_score[current] + 1
                    if tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + heuristic(neighbor, end)
                        if neighbor not in [i[1] for i in open_set]:
                            heapq.heappush(open_set, (f_score[neighbor], neighbor))
        return None # No path found

    def create_job(self, start, end):
        """Creates a new transportation job."""
        job_id = f"job-{random.randint(1000, 9999)}"
        self.jobs[job_id] = {"start": start, "end": end, "status": "pending"}
        print(f"Created job {job_id}: {start} -> {end}")
        self.assign_job_to_vehicle(job_id)
        return job_id

    def assign_job_to_vehicle(self, job_id):
        """Finds the best vehicle for a job and assigns it."""
        if job_id not in self.jobs:
            return

        job = self.jobs[job_id]
        best_vehicle = None
        min_dist = float('inf')

        # Find the closest idle vehicle
        for v in self.vehicles.values():
            if v.status == 'idle':
                dist = abs(v.position[0] - job['start'][0]) + abs(v.position[1] - job['start'][1])
                if dist < min_dist:
                    min_dist = dist
                    best_vehicle = v

        if best_vehicle:
            # Route to pick-up location, then to destination
            pickup_route = self.optimize_route_a_star(best_vehicle.position, job['start'])
            if pickup_route:
                delivery_route = self.optimize_route_a_star(job['start'], job['end'])
                if delivery_route:
                    best_vehicle.route = pickup_route + delivery_route
                    best_vehicle.status = 'en_route'
                    best_vehicle.job_id = job_id
                    self.jobs[job_id]['status'] = 'in_progress'
                    print(f"Assigned job {job_id} to {best_vehicle.id}. Route length: {len(best_vehicle.route)} steps.")
                    return True
        print(f"No available vehicles for job {job_id}.")
        return False

    def _update_environment(self):
        """Simulates dynamic changes in the environment, like new traffic jams."""
        # 1% chance to add a new obstacle
        if random.random() < 0.01:
            x, y = random.randint(0, self.map_size[0] - 1), random.randint(0, self.map_size[1] - 1)
            if self.grid[x][y] == 0:
                self.grid[x][y] = 1
                print(f"Event: New traffic jam/obstacle at ({x}, {y}).")
                # Trigger re-routing for affected vehicles
                for v in self.vehicles.values():
                    if v.status == 'en_route' and (x, y) in v.route:
                        print(f"Rerouting {v.id} due to new obstacle.")
                        job = self.jobs[v.job_id]
                        new_route = self.optimize_route_a_star(v.position, job['end'])
                        if new_route:
                            v.route = new_route
                        else:
                            print(f"Could not find a new route for {v.id}. Vehicle is stuck.")
                            v.status = 'stuck'

    def display_grid(self):
        """Prints a text-based representation of the grid."""
        grid_copy = self.grid.astype(str)
        grid_copy[self.grid == 0] = '.'
        grid_copy[self.grid == 1] = '#'

        for v in self.vehicles.values():
            x, y = v.position
            grid_copy[x][y] = v.id[-1]

        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n".join(" ".join(row) for row in grid_copy))
        print("-" * self.map_size[1] * 2)

    def run_simulation(self, steps=50):
        """Runs the main simulation loop."""
        for i in range(steps):
            print(f"--- Simulation Step {i+1}/{steps} ---")

            # Update environment
            self._update_environment()

            # Move each vehicle
            for v in self.vehicles.values():
                v.move()

            # Display grid
            self.display_grid()

            # Print vehicle statuses
            for v in self.vehicles.values():
                print(f"- {v.id}: Pos={v.position}, Status={v.status}, Battery={v.battery:.1f}%, Job={v.job_id}")

            time.sleep(0.5)

if __name__ == "__main__":
    manager = TransportationManager(map_size=(20, 30), num_vehicles=5)

    # Create some initial jobs
    manager.create_job(start=(1, 1), end=(18, 28))
    manager.create_job(start=(5, 25), end=(15, 2))

    # Run the simulation
    manager.run_simulation(steps=100)

    print("\n--- Simulation Finished ---")
    print("Final vehicle statuses:")
    for v in manager.vehicles.values():
        print(f"- {v}")