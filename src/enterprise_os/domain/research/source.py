from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Source:
    name: str
    type: str
    authority: str
    reliability: str
    retrieval_time: datetime
    freshness: str
