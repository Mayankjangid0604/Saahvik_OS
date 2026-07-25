from dataclasses import dataclass
from enterprise_os.domain.knowledge.lesson import Lesson
from enterprise_os.domain.research.evidence import Evidence

@dataclass(frozen=True)
class KnowledgeAsset:
    identifier: str
    title: str
    description: str
    category: str
    lessons: tuple[Lesson, ...]
    supporting_evidence: tuple[Evidence, ...]
    strategic_relevance: str
    confidence: str
    provenance: str

    def __post_init__(self):
        if not self.lessons:
            raise ValueError("KnowledgeAsset must be based on at least one Lesson to preserve explainability.")
