from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchQuestion:
    objective: str
    context: str
    expected_answer: str
    related_goal: str
    priority: str
