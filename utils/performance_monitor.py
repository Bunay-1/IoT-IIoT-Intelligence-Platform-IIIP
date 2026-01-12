# utils/performance_monitor.py

import time
from functools import wraps

def monitor_operation(operation_name: str):
    """A decorator to monitor the execution time of a function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # In a real system, this would log to a metrics backend (e.g., Prometheus)
            # For this simulation, we'll just print the duration.
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            print(f"[Performance] Operation '{operation_name}' took {end_time - start_time:.4f} seconds.")
            return result
        return wrapper
    return decorator
