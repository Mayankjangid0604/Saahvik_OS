from dataclasses import dataclass
from datetime import datetime
from enterprise_os.domain.knowledge.asset import KnowledgeAsset

@dataclass(frozen=True)
class EnterpriseObservation:
    identifier: str
    title: str
    description: str
    supporting_knowledge: tuple[KnowledgeAsset, ...]
    confidence: str
    created_timestamp: datetime
