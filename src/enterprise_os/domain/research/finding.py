from dataclasses import dataclass

from enterprise_os.domain.research.hypothesis import Hypothesis


@dataclass(frozen=True)
class Finding:
    summary: str
    hypotheses_used: tuple[Hypothesis, ...]
    confidence: str
    unresolved_questions: tuple[str, ...]
    recommendations: tuple[str, ...]

    def __post_init__(self):
        if not self.hypotheses_used:
            raise ValueError("Findings must reference one or more hypotheses.")
