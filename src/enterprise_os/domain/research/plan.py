from dataclasses import dataclass

from enterprise_os.domain.research.question import ResearchQuestion


@dataclass(frozen=True)
class ResearchPlan:
    questions: tuple[ResearchQuestion, ...]
    required_evidence: tuple[str, ...]
    preferred_source_types: tuple[str, ...]
    stopping_conditions: tuple[str, ...]
    success_criteria: tuple[str, ...]
