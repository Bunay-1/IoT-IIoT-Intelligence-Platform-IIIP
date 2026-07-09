"""
Intelligent Task Scheduler
A dependency-aware, priority-driven task scheduler.
"""
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Set, Dict, Optional, Callable
from collections import deque

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class Task:
    """Represents a single unit of work."""
    id: int
    name: str
    action: Callable[[], None]
    priority: int = 1  # Lower number means higher priority
    dependencies: Set[int] = field(default_factory=set)
    deadline: Optional[datetime] = None
    creation_time: datetime = field(default_factory=datetime.utcnow)

    # Internal state for the scheduler
    dynamic_priority: float = 0.0

    def __repr__(self):
        return f"Task(id={self.id}, name='{self.name}', priority={self.priority}, deps={self.dependencies})"

class IntelligentTaskScheduler:
    """
    A scheduler that executes tasks based on dependencies and a dynamically calculated priority.
    """
    def __init__(self):
        self.tasks: Dict[int, Task] = {}
        self.task_dependents: Dict[int, Set[int]] = {}

    def add_task(self, task: Task):
        """Adds a task to the scheduler."""
        if task.id in self.tasks:
            raise ValueError(f"Task with ID {task.id} already exists.")
        self.tasks[task.id] = task
        logger.info(f"Added: {task}")

        # Build the reverse dependency graph (who depends on this task)
        self.task_dependents.setdefault(task.id, set())
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                raise ValueError(f"Dependency task with ID {dep_id} not found for task {task.id}.")
            self.task_dependents.setdefault(dep_id, set()).add(task.id)

    def _topological_sort(self) -> List[int]:
        """
        Sorts tasks based on their dependencies.
        Returns a list of task IDs in a valid execution order.
        Raises an exception if a circular dependency is detected.
        """
        in_degree = {task_id: len(task.dependencies) for task_id, task in self.tasks.items()}
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        sorted_order = []

        while queue:
            task_id = queue.popleft()
            sorted_order.append(task_id)

            for dependent_id in self.task_dependents.get(task_id, []):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        if len(sorted_order) != len(self.tasks):
            raise ValueError("Circular dependency detected in tasks.")

        return sorted_order

    def _calculate_dynamic_priorities(self):
        """
        Calculates a dynamic priority score for each task.
        The score is a combination of base priority, deadline urgency, and impact (number of dependents).
        """
        now = datetime.utcnow()
        for task in self.tasks.values():
            # 1. Base priority score (lower is better, so we use its inverse)
            priority_score = 1.0 / task.priority

            # 2. Deadline score (higher score for urgent tasks)
            deadline_score = 0.0
            if task.deadline:
                time_left = (task.deadline - now).total_seconds()
                if time_left < 0:
                    deadline_score = 100.0  # Overdue
                elif time_left < 3600: # Less than 1 hour
                    deadline_score = 50.0
                else:
                    deadline_score = max(0, 1.0 / (time_left / 3600.0)) # Scale by hours left

            # 3. Impact score (higher score for tasks with more dependents)
            impact_score = len(self.task_dependents.get(task.id, set()))

            # Combine scores with weights
            task.dynamic_priority = (priority_score * 0.4) + (deadline_score * 0.4) + (impact_score * 0.2)

    def run(self):
        """
        Creates and executes a plan based on dependencies and priorities.
        """
        logger.info("Starting task execution...")

        try:
            # 1. Get a valid execution order respecting dependencies
            execution_order = self._topological_sort()
            logger.info(f"Topological sort successful. Valid execution order: {execution_order}")

            # 2. Calculate dynamic priorities for all tasks
            self._calculate_dynamic_priorities()

            # 3. Create a prioritized list of tasks that are ready to run
            ready_to_run = [self.tasks[tid] for tid in execution_order]

            # 4. Sort the ready tasks by their dynamic priority (higher is better)
            prioritized_plan = sorted(ready_to_run, key=lambda t: t.dynamic_priority, reverse=True)

            logger.info("Execution plan created based on dynamic priorities:")
            for i, task in enumerate(prioritized_plan):
                logger.info(f"  {i+1}. {task.name} (DynPri: {task.dynamic_priority:.2f})")

            # 5. Execute the plan
            print("\n--- Executing Tasks ---")
            for task in prioritized_plan:
                logger.info(f"Executing task: {task.name}")
                try:
                    task.action()
                    logger.info(f"SUCCESS: {task.name} finished.")
                except Exception as e:
                    logger.error(f"FAILURE: {task.name} failed with error: {e}")
                    # Decide on error handling: stop all or continue? For now, continue.
            print("--- Task Execution Finished ---\n")

        except ValueError as e:
            logger.error(f"Could not run scheduler: {e}")

if __name__ == '__main__':
    # --- Демонстрация на интелигентния диспечер на задачи ---
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ НА ИНТЕЛИГЕНТЕН ДИСПЕЧЕР НА ЗАДАЧИ")
    print("="*50 + "\n")

    # 1. Инициализация на диспечера
    scheduler = IntelligentTaskScheduler()

    # 2. Дефиниране на примерни действия за задачите
    def simple_action(name):
        def action():
            print(f"  -> Изпълнява се '{name}'...")
            time.sleep(0.1) # Симулация на работа
        return action

    # 3. Добавяне на задачи със зависимости и различни приоритети
    print("--- Добавяне на задачи ---")
    try:
        scheduler.add_task(Task(id=1, name="Компилиране на код", action=simple_action("Компилиране"), priority=2))
        scheduler.add_task(Task(id=2, name="Изпълнение на unit тестове", action=simple_action("Unit тестове"), dependencies={1}))
        scheduler.add_task(Task(id=3, name="Създаване на Docker image", action=simple_action("Docker build"), dependencies={1}))
        scheduler.add_task(Task(id=4, name="Изпълнение на integration тестове", action=simple_action("Integration тестове"), dependencies={2, 3}))
        scheduler.add_task(Task(id=5, name="Deploy в staging среда", action=simple_action("Deploy to Staging"), dependencies={4}, deadline=datetime.utcnow() + timedelta(seconds=10)))
        scheduler.add_task(Task(id=6, name="Генериране на документация", action=simple_action("Генериране на docs"), priority=3))
        scheduler.add_task(Task(id=7, name="Спешен security patch", action=simple_action("HOTFIX: Security Patch"), priority=1, deadline=datetime.utcnow() + timedelta(seconds=5)))
        scheduler.add_task(Task(id=8, name="Архивиране на логове", action=simple_action("Архивиране"), priority=4, dependencies={5, 7}))

    except ValueError as e:
        logger.error(f"Грешка при добавяне на задача: {e}")

    print("--- Всички задачи са добавени ---\n")

    # 4. Изпълнение на задачите
    scheduler.run()

    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯТА ПРИКЛЮЧИ")
    print("="*50 + "\n")
