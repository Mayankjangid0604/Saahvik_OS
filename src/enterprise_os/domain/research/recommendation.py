from dataclasses import dataclass

from enterprise_os.domain.research.finding import Finding


@dataclass(frozen=True)
class ExecutiveRecommendation:
    summary: str
    findings: tuple[Finding, ...]

    def __post_init__(self):
        if not self.findings:
            raise ValueError("Recommendations without evidence (findings) are invalid.")
