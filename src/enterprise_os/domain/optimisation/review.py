from dataclasses import dataclass
from enterprise_os.domain.knowledge.work_item import WorkItem
from enterprise_os.domain.optimisation.metric import Metric
from enterprise_os.domain.optimisation.observation import Observation

@dataclass(frozen=True)
class PerformanceReview:
    scope: str
    reviewed_work_items: tuple[WorkItem, ...]
    metrics: tuple[Metric, ...]
    observations: tuple[Observation, ...]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    risks: tuple[str, ...]
    opportunities: tuple[str, ...]
