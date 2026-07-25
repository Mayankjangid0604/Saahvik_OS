from datetime import datetime, timezone
from enterprise_os.application.services.optimisation_orchestrator import OptimisationOrchestrator
from enterprise_os.application.services.review_engine import ReviewEngine
from enterprise_os.domain.knowledge.work_item import WorkItem
from enterprise_os.domain.optimisation.observation import Observation
from enterprise_os.domain.strategy.goal import StrategicGoal

def test_optimisation_orchestrator_cycle():
    goal = StrategicGoal("g1", "T", "D", "C", "O", "P", (), (), "Owner", datetime.now(timezone.utc))
    work_item = WorkItem("w1", "Title", "Desc", goal, (), (), (), "State", datetime.now(timezone.utc))
    observation = Observation("o1", "Title", "Desc", (), (), "High", datetime.now(timezone.utc))
    
    engine = ReviewEngine()
    orchestrator = OptimisationOrchestrator(engine)
    
    proposals = orchestrator.evaluate_performance((work_item,), (observation,))
    
    assert len(proposals) == 1
    assert proposals[0].objective == "Improvement for General"
