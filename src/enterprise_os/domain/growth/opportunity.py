from dataclasses import dataclass
from enterprise_os.domain.research.evidence import Evidence

@dataclass(frozen=True)
class GrowthOpportunity:
    identifier: str
    title: str
    description: str
    market: str
    expected_value: str
    confidence: str
    supporting_evidence: tuple[Evidence, ...]
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]
