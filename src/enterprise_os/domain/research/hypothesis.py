from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from enterprise_os.domain.research.fact import Fact


class HypothesisStatus(Enum):
    PROPOSED = "proposed"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class Hypothesis:
    identifier: str
    title: str
    description: str
    supporting_facts: tuple[Fact, ...]
    assumptions: tuple[str, ...]
    confidence: str
    status: HypothesisStatus
    reasoning: str
    created_timestamp: datetime

    def __post_init__(self):
        if not self.supporting_facts:
            raise ValueError("Hypotheses must be derived from facts. No facts provided.")
