from datetime import datetime, timezone
from enterprise_os.application.ports.knowledge import KnowledgeIndexPort
from enterprise_os.domain.knowledge.asset import KnowledgeAsset
from enterprise_os.domain.knowledge.lesson import Lesson
from enterprise_os.domain.knowledge.retrieval import RetrievalRequest, MemoryLayer
from enterprise_os.domain.knowledge.work_item import WorkItem
from enterprise_os.domain.research.evidence import Evidence


class KnowledgeOrchestrator:
    def __init__(self, knowledge_index: KnowledgeIndexPort):
        self.knowledge_index = knowledge_index
        self.work_items: list[WorkItem] = []

    def store_work_item(self, item: WorkItem) -> None:
        self.work_items.append(item)

    def derive_lessons(self, item: WorkItem, evidence: tuple[Evidence, ...]) -> tuple[Lesson, ...]:
        return (
            Lesson(
                identifier=f"lesson-{item.identifier}",
                title=f"Lesson from {item.title}",
                summary="Derived summary.",
                supporting_work_items=(item,),
                supporting_evidence=evidence,
                confidence="High",
                recommendations=("Do this again",),
                created_timestamp=datetime.now(timezone.utc)
            ),
        )

    def create_knowledge_asset(self, lessons: tuple[Lesson, ...], evidence: tuple[Evidence, ...]) -> KnowledgeAsset:
        asset = KnowledgeAsset(
            identifier="asset-1",
            title="Strategic Asset",
            description="Captured organizational memory.",
            category="Best Practices",
            lessons=lessons,
            supporting_evidence=evidence,
            strategic_relevance="High",
            confidence="High",
            provenance="Derived via completed work items."
        )
        self.knowledge_index.index_asset(asset)
        return asset

    def retrieve_knowledge(self, query: str) -> tuple[KnowledgeAsset, ...]:
        request = RetrievalRequest(
            query=query,
            target_layer=MemoryLayer.ENTERPRISE,
            search_criteria=("category:Best Practices",)
        )
        return self.knowledge_index.retrieve(request)
