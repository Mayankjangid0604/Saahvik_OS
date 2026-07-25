from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from enterprise_os.domain.operations.task import Task
from enterprise_os.domain.operations.worker import Worker

class ActionBoundaryType(Enum):
    FINANCIAL = "financial"
    LEGAL = "legal"
    PRIVACY = "privacy"
    DESTRUCTIVE = "destructive"

@dataclass(frozen=True)
class SafetyBoundary:
    boundary_type: ActionBoundaryType
    requires_approval: bool
    reasoning: str

@dataclass(frozen=True)
class ExecutionResult:
    task: Task
    worker: Worker
    output: str
    evidence: tuple[str, ...]
    success: bool
    issues: tuple[str, ...]
    recommendations: tuple[str, ...]
    completion_timestamp: datetime
    safety_boundaries_checked: tuple[SafetyBoundary, ...]

    def __post_init__(self):
        if self.task.assigned_worker.identifier != self.worker.identifier:
            raise ValueError("ExecutionResult worker must match task's assigned worker.")
