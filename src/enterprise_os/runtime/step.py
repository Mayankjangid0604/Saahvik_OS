from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

class StepStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class Step:
    id: str
    description: str
    status: StepStatus = StepStatus.PENDING
    result: Any = None
