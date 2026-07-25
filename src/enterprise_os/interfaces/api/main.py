from fastapi import FastAPI
from datetime import datetime, timezone

from enterprise_os.application.use_cases.boot_ceo import BootCEO
from enterprise_os.domain.ceo.company_state import CompanyState
from enterprise_os.domain.ceo.runtime_configuration import RuntimeConfiguration

from enterprise_os.application.services.strategic_orchestrator import StrategicOrchestrator
from enterprise_os.domain.research.evidence import Evidence
from enterprise_os.domain.research.source import Source

from enterprise_os.application.services.evolution_orchestrator import EvolutionOrchestrator
from enterprise_os.application.services.evolution_engine import EvolutionEngine
from enterprise_os.domain.evolution.observation import EnterpriseObservation

app = FastAPI(title="EnterpriseOS Digital CEO Runtime API", version="0.1.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "EnterpriseOS CEO is online."}

@app.get("/ceo/state")
def get_ceo_state():
    return {
        "company_state": {
            "name": "EnterpriseOS Digital CEO",
            "mission": "To autonomously manage and grow the enterprise.",
            "founder": "Founder"
        },
        "runtime_configuration": {
            "mode": "autonomous",
            "allowed_operations": ["all"]
        }
    }

@app.post("/strategy/plan")
def generate_strategic_plan():
    # Mocking response directly to avoid complex domain dependencies for the demo
    return {
        "strategic_goals": [
            {
                "identifier": "g1",
                "title": "Expand to new markets",
                "objective": "Grow revenue by 20%",
                "state": "proposed"
            }
        ]
    }

@app.post("/evolution/analyze")
def analyze_evolution():
    # Mocking input data for demonstration
    obs = EnterpriseObservation("obs1", "Long-term trend", "The market is shifting", (), "High", datetime.now(timezone.utc))
    
    engine = EvolutionEngine()
    orchestrator = EvolutionOrchestrator(engine)
    amendments = orchestrator.orchestrate_evolution((obs,))
    
    return {
        "constitution_amendments": [
            {
                "identifier": a.identifier,
                "proposed_amendment": a.proposed_amendment,
                "justification": a.justification,
                "confidence": a.confidence
            }
            for a in amendments
        ]
    }
