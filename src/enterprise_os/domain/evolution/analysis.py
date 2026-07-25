from dataclasses import dataclass
from enterprise_os.domain.evolution.opportunity import EvolutionOpportunity

@dataclass(frozen=True)
class EvolutionAnalysis:
    opportunity: EvolutionOpportunity
    strategic_impact: str
    organisational_impact: str
    governance_impact: str
    operational_impact: str
    cultural_impact: str
    uncertainty: str
    confidence: str
