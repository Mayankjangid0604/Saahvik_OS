from datetime import datetime, timezone
from enterprise_os.application.services.evolution_orchestrator import EvolutionOrchestrator
from enterprise_os.application.services.evolution_engine import EvolutionEngine
from enterprise_os.domain.evolution.observation import EnterpriseObservation

def test_evolution_orchestrator_cycle():
    observation = EnterpriseObservation("o1", "Title", "Desc", (), "High", datetime.now(timezone.utc))
    
    engine = EvolutionEngine()
    orchestrator = EvolutionOrchestrator(engine)
    
    amendments = orchestrator.orchestrate_evolution((observation,))
    
    assert len(amendments) == 0  # Engine mock returns () for identify_opportunities
