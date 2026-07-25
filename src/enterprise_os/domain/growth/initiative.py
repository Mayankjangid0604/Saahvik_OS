from dataclasses import dataclass
from enterprise_os.domain.optimisation.proposal import ImprovementProposal

@dataclass(frozen=True)
class StrategicInitiative:
    identifier: str
    title: str
    objective: str
    originating_proposal: ImprovementProposal
    expected_outcomes: tuple[str, ...]
    success_metrics: tuple[str, ...]
    strategic_goals: tuple[str, ...]
    confidence: str
    dependencies: tuple[str, ...]
