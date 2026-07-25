from datetime import datetime, timezone
from enterprise_os.application.ports.knowledge import KnowledgeIndexPort
from enterprise_os.application.services.knowledge_orchestrator import KnowledgeOrchestrator
from enterprise_os.domain.knowledge.asset import KnowledgeAsset
from enterprise_os.domain.knowledge.retrieval import RetrievalRequest
from enterprise_os.domain.knowledge.work_item import WorkItem
from enterprise_os.domain.strategy.goal import StrategicGoal

class MockKnowledgeIndex(KnowledgeIndexPort):
    def __init__(self):
        self.assets = []
        
    def index_asset(self, asset: KnowledgeAsset) -> None:
        self.assets.append(asset)
        
    def retrieve(self, request: RetrievalRequest) -> tuple[KnowledgeAsset, ...]:
        return tuple(self.assets)

def test_knowledge_orchestrator_cycle():
    goal = StrategicGoal("g1", "T", "D", "C", "O", "P", (), (), "Owner", datetime.now(timezone.utc))
    work_item = WorkItem("w1", "Title", "Desc", goal, (), (), (), "State", datetime.now(timezone.utc))
    
    index = MockKnowledgeIndex()
    orchestrator = KnowledgeOrchestrator(index)
    
    orchestrator.store_work_item(work_item)
    assert len(orchestrator.work_items) == 1
    
    lessons = orchestrator.derive_lessons(work_item, ())
    asset = orchestrator.create_knowledge_asset(lessons, ())
    
    assert asset.title == "Strategic Asset"
    assert len(index.assets) == 1
    
    retrieved = orchestrator.retrieve_knowledge("test query")
    assert len(retrieved) == 1
