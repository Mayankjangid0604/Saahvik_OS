from dataclasses import dataclass, field
from enterprise_os.runtime.step import Step

@dataclass
class Plan:
    id: str
    goal_id: str
    steps: list[Step] = field(default_factory=list)
    current_step_index: int = 0
    
    def get_next_step(self) -> Step | None:
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
        
    def advance(self) -> None:
        self.current_step_index += 1
