from dataclasses import dataclass, field
from typing import Optional
from enterprise_os.runtime.executive_state import ExecutiveState
from enterprise_os.runtime.plan import Plan

@dataclass
class ExecutiveContext:
    session_id: str
    state: ExecutiveState = ExecutiveState.IDLE
    memory: dict[str, str] = field(default_factory=dict)
    active_capabilities: list[str] = field(default_factory=list)
    active_tools: list[str] = field(default_factory=list)
    plan: Optional[Plan] = None

    def transition(self, new_state: ExecutiveState) -> None:
        self.state = new_state
