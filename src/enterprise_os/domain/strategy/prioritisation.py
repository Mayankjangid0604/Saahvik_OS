from dataclasses import dataclass

from enterprise_os.domain.research.finding import Finding
from enterprise_os.domain.strategy.option import StrategicOption
from enterprise_os.domain.strategy.tradeoff import TradeOffProfile


@dataclass(frozen=True)
class Prioritisation:
    option: StrategicOption
    relative_priority: int
    reasoning: str
    supporting_findings: tuple[Finding, ...]
    assumptions: tuple[str, ...]
    tradeoff_profile: TradeOffProfile
