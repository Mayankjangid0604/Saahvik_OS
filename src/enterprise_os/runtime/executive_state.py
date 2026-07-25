from enum import Enum, auto

class ExecutiveState(Enum):
    IDLE = auto()
    PLANNING = auto()
    RESEARCHING = auto()
    EXECUTING = auto()
    REFLECTING = auto()
    WAITING_FOR_APPROVAL = auto()
    DECIDING = auto()
    EVALUATING = auto()
