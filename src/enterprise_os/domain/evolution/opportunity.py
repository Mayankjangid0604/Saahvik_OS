from dataclasses import dataclass
from enterprise_os.domain.evolution.observation import EnterpriseObservation

@dataclass(frozen=True)
class EvolutionOpportunity:
    identifier: str
    title: str
    description: str
    expected_benefit: str
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]
    supporting_observations: tuple[EnterpriseObservation, ...]
