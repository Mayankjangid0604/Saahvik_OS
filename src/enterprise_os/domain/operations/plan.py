from dataclasses import dataclass
from enterprise_os.domain.operations.task import Task

@dataclass(frozen=True)
class TaskPlan:
    ordered_tasks: tuple[Task, ...]
    dependencies: tuple[str, ...]
    execution_order: tuple[str, ...]
    completion_criteria: tuple[str, ...]
    estimated_complexity: str
