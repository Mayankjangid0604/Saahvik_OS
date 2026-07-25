from dataclasses import dataclass
from datetime import datetime
from enterprise_os.domain.strategy.goal import StrategicGoal
from enterprise_os.domain.operations.responsibility import Responsibility
from enterprise_os.domain.operations.plan import TaskPlan
from enterprise_os.domain.operations.result import ExecutionResult

@dataclass(frozen=True)
class WorkItem:
    identifier: str
    title: str
    description: str
    originating_strategic_goal: StrategicGoal
    responsibilities: tuple[Responsibility, ...]
    task_plans: tuple[TaskPlan, ...]
    execution_results: tuple[ExecutionResult, ...]
    current_state: str
    created_timestamp: datetime
    completion_timestamp: datetime | None = None
