from dataclasses import dataclass

from enterprise_os.domain.research.finding import Finding
from enterprise_os.domain.strategy.decision import ExecutiveDecision


@dataclass(frozen=True)
class FounderRecommendation:
    executive_summary: str
    decision: ExecutiveDecision
    benefits: tuple[str, ...]
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]
    confidence: str
    supporting_findings: tuple[Finding, ...]
    open_questions: tuple[str, ...]

    def __post_init__(self):
        # Traceability validation
        if not self.supporting_findings:
            raise ValueError("FounderRecommendation must have supporting findings to preserve traceability.")
