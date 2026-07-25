from dataclasses import dataclass

from enterprise_os.domain.research.finding import Finding
from enterprise_os.domain.strategy.goal import StrategicGoal


@dataclass(frozen=True)
class StrategicOption:
    identifier: str
    title: str
    description: str
    related_goal: StrategicGoal
    assumptions: tuple[str, ...]
    required_findings: tuple[Finding, ...]
    expected_benefits: tuple[str, ...]
    expected_costs: tuple[str, ...]
    risks: tuple[str, ...]
    opportunities: tuple[str, ...]
    confidence: str
