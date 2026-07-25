from dataclasses import dataclass
from enum import Enum


class GapStatus(Enum):
    IDENTIFIED = "identified"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    UNRESOLVABLE = "unresolvable"


@dataclass(frozen=True)
class KnowledgeGap:
    identifier: str
    description: str
    reason: str
    priority: str
    required_evidence: tuple[str, ...]
    status: GapStatus
