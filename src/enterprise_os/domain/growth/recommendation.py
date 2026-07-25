from dataclasses import dataclass
from enterprise_os.domain.growth.initiative import StrategicInitiative
from enterprise_os.domain.research.evidence import Evidence

@dataclass(frozen=True)
class InvestmentRecommendation:
    summary: str
    initiatives: tuple[StrategicInitiative, ...]
    expected_return: str
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]
    supporting_evidence: tuple[Evidence, ...]
    confidence: str
