from dataclasses import dataclass

from enterprise_os.domain.research.finding import Finding
from enterprise_os.domain.strategy.option import StrategicOption


@dataclass(frozen=True)
class ExecutiveDecision:
    selected_option: StrategicOption
    rejected_alternatives: tuple[StrategicOption, ...]
    reasoning: str
    confidence: str
    expected_impact: str
    supporting_findings: tuple[Finding, ...]
    assumptions: tuple[str, ...]
