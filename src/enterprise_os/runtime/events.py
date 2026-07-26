from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

@dataclass(frozen=True, kw_only=True)
class Event:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass(frozen=True, kw_only=True)
class GoalCreated(Event):
    session_id: str
    goal_id: str
    description: str

@dataclass(frozen=True, kw_only=True)
class PlanGenerated(Event):
    session_id: str
    plan_id: str
    steps_count: int

@dataclass(frozen=True, kw_only=True)
class StepCompleted(Event):
    session_id: str
    step_id: str
    result: str

@dataclass(frozen=True, kw_only=True)
class StepFailed(Event):
    session_id: str
    step_id: str
    error: str

@dataclass(frozen=True, kw_only=True)
class StateTransitioned(Event):
    session_id: str
    old_state: str
    new_state: str

@dataclass(frozen=True, kw_only=True)
class DecisionMade(Event):
    session_id: str
    outcome: str
    justification: str

@dataclass(frozen=True, kw_only=True)
class SessionFinished(Event):
    session_id: str

@dataclass(frozen=True, kw_only=True)
class EvaluationCompleted(Event):
    session_id: str
    reflection: str

class EventDispatcher:
    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable[[Event], None]]] = {}
        
    def subscribe(self, event_type: type, handler: Callable[[Event], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        
    def dispatch(self, event: Event) -> None:
        for event_type, handlers in self._subscribers.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    handler(event)
