from dataclasses import dataclass
from enterprise_os.domain.optimisation.observation import Observation
from enterprise_os.domain.knowledge.lesson import Lesson

@dataclass(frozen=True)
class ImprovementOpportunity:
    identifier: str
    title: str
    description: str
    expected_benefit: str
    implementation_cost: str
    implementation_complexity: str
    confidence: str
    supporting_observations: tuple[Observation, ...]
    supporting_lessons: tuple[Lesson, ...]
