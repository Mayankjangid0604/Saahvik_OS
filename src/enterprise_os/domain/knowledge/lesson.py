from dataclasses import dataclass
from datetime import datetime
from enterprise_os.domain.knowledge.work_item import WorkItem
from enterprise_os.domain.research.evidence import Evidence

@dataclass(frozen=True)
class Lesson:
    identifier: str
    title: str
    summary: str
    supporting_work_items: tuple[WorkItem, ...]
    supporting_evidence: tuple[Evidence, ...]
    confidence: str
    recommendations: tuple[str, ...]
    created_timestamp: datetime
