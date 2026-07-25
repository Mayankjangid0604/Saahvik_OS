from dataclasses import dataclass, field
from enterprise_os.runtime.executive_state import ExecutiveState

@dataclass
class ExecutiveContext:
    session_id: str
    state: ExecutiveState = ExecutiveState.IDLE
    memory: dict[str, str] = field(default_factory=dict)
    active_capabilities: list[str] = field(default_factory=list)
    active_tools: list[str] = field(default_factory=list)
    
    def transition(self, new_state: ExecutiveState) -> None:
        self.state = new_state
