from dataclasses import dataclass
from enum import Enum, auto

class DecisionOutcome(Enum):
    PROCEED = auto()
    ABORT = auto()
    REPLAN = auto()
    SEEK_APPROVAL = auto()

@dataclass(frozen=True)
class Decision:
    outcome: DecisionOutcome
    justification: str
