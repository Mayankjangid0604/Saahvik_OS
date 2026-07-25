from abc import ABC, abstractmethod

from enterprise_os.domain.research.evidence import Evidence
from enterprise_os.domain.research.plan import ResearchPlan


class ResearchProviderPort(ABC):
    @abstractmethod
    def gather_evidence(self, plan: ResearchPlan) -> tuple[Evidence, ...]:
        """Gathers evidence for the given research plan."""
        pass
