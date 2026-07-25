from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from enterprise_os.domain.organisation.blueprint import RoleBlueprint
from enterprise_os.domain.organisation.capability import Capability
from enterprise_os.domain.operations.responsibility import Responsibility


class WorkerStatus(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class Worker:
    identifier: str
    name: str
    purpose: str
    assigned_role: RoleBlueprint
    assigned_responsibilities: tuple[Responsibility, ...]
    available_capabilities: tuple[Capability, ...]
    current_workload: str
    status: WorkerStatus
    creation_timestamp: datetime
