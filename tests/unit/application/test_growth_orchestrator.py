from enterprise_os.application.services.growth_orchestrator import GrowthOrchestrator
from enterprise_os.application.services.growth_engine import GrowthEngine
from enterprise_os.domain.growth.opportunity import GrowthOpportunity

def test_growth_orchestrator_cycle():
    opportunity = GrowthOpportunity("o1", "Title", "Desc", "Market", "Val", "High", (), (), ())
    
    engine = GrowthEngine()
    orchestrator = GrowthOrchestrator(engine)
    
    recommendations = orchestrator.orchestrate_growth((opportunity,))
    
    assert len(recommendations) == 1
    assert recommendations[0].summary == "Recommended"
