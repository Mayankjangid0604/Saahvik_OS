from dataclasses import dataclass

@dataclass(frozen=True)
class Reflection:
    step_id: str
    outcome_met_expectations: bool
    learnings: str
