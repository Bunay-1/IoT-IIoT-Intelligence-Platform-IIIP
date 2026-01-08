"""
Module: Resource Monitor

This module monitors the usage of resources such as CPU, memory, and disk space across the system, providing insights into resource consumption and performance.
"""


class ResourceMonitor:
    def __init__(self):
        self.resource_usage = {"cpu": 0, "memory": 0, "disk": 0}

    def monitor_cpu(self):
        """
        Monitor CPU usage.
        """
        # Implement CPU monitoring logic here
        cpu_usage = 25  # Placeholder for actual CPU usage
        self.resource_usage["cpu"] = cpu_usage
        print(f"CPU usage: {cpu_usage}%")
        return cpu_usage

    def monitor_memory(self):
        """
        Monitor memory usage.
        """
        # Implement memory monitoring logic here
        memory_usage = 50  # Placeholder for actual memory usage
        self.resource_usage["memory"] = memory_usage
        print(f"Memory usage: {memory_usage}%")
        return memory_usage

    def monitor_disk(self):
        """
        Monitor disk usage.
        """
        # Implement disk monitoring logic here
        disk_usage = 70  # Placeholder for actual disk usage
        self.resource_usage["disk"] = disk_usage
        print(f"Disk usage: {disk_usage}%")
        return disk_usage

    def get_resource_usage(self):
        """
        Retrieve the current resource usage.
        """
        print(f"Resource usage: {self.resource_usage}")
        return self.resource_usage

    def alert_high_usage(self, threshold):
        """
        Alert if resource usage exceeds the specified threshold.
        """
        for resource, usage in self.resource_usage.items():
            if usage > threshold:
                print(f"Alert: High usage detected for {resource}: {usage}%")
            else:
                print(f"{resource.capitalize()} usage within limits: {usage}%")
