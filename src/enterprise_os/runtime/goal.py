from dataclasses import dataclass

@dataclass(frozen=True)
class Goal:
    id: str
    description: str
    success_criteria: str
