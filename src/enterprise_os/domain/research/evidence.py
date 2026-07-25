from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Evidence:
    identifier: str
    source: str
    source_type: str
    retrieval_timestamp: datetime
    confidence: str
    reliability: str
    supporting_facts: tuple[str, ...]
    contradictions: tuple[str, ...]
    notes: str
