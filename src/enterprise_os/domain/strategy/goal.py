from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StrategicGoal:
    identifier: str
    title: str
    description: str
    category: str
    desired_outcome: str
    priority: str
    constraints: tuple[str, ...]
    success_metrics: tuple[str, ...]
    owner: str
    created_timestamp: datetime
