from dataclasses import dataclass
from enum import Enum

from enterprise_os.domain.research.evidence import Evidence


class FactStatus(Enum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Fact:
    statement: str
    supporting_evidence: tuple[Evidence, ...]
    confidence: str
    status: FactStatus

    def __post_init__(self):
        if not self.supporting_evidence:
            raise ValueError("Facts must be derived from evidence. No evidence provided.")
