from dataclasses import dataclass
from enterprise_os.domain.growth.opportunity import GrowthOpportunity

@dataclass(frozen=True)
class ExpansionAnalysis:
    opportunity: GrowthOpportunity
    market_attractiveness: str
    organisational_readiness: str
    operational_readiness: str
    financial_impact: str
    strategic_alignment: str
    uncertainty: str
