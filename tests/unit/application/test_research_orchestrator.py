from enterprise_os.domain.research.plan import ResearchPlan
from enterprise_os.domain.research.question import ResearchQuestion
from enterprise_os.application.services.research_orchestrator import ResearchOrchestrator
from tests.support import DummyResearchProvider

def test_research_orchestrator():
    provider = DummyResearchProvider()
    orchestrator = ResearchOrchestrator(provider)

    q = ResearchQuestion(
        objective="Find competitors",
        context="Market entry",
        expected_answer="List of companies",
        related_goal="market_analysis",
        priority="High"
    )
    plan = ResearchPlan(
        questions=(q,),
        required_evidence=("competitor_list",),
        preferred_source_types=("Local",),
        stopping_conditions=("Found 5",),
        success_criteria=("Has names",)
    )

    findings = orchestrator.execute_plan(plan)
    assert len(findings) == 1
    assert len(findings[0].hypotheses_used) == 1
    
    # Prove provenance chain:
    hyp = findings[0].hypotheses_used[0]
    fact = hyp.supporting_facts[0]
    ev = fact.supporting_evidence[0]
    
    assert ev.source == "DummyProvider"
