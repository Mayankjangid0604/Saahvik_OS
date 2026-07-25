from dataclasses import dataclass
from enum import Enum
from enterprise_os.domain.operations.worker import Worker
from enterprise_os.domain.organisation.capability import Capability

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass(frozen=True)
class Task:
    identifier: str
    objective: str
    description: str
    priority: str
    assigned_worker: Worker
    required_capability: Capability
    dependencies: tuple[str, ...]
    expected_output: str
    status: TaskStatus
