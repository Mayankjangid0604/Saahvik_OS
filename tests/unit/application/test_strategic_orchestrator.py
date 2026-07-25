from datetime import datetime, timezone
from enterprise_os.domain.strategy.goal import StrategicGoal
from enterprise_os.application.services.strategic_orchestrator import StrategicOrchestrator
from enterprise_os.domain.research.finding import Finding
from enterprise_os.domain.research.hypothesis import Hypothesis, HypothesisStatus
from enterprise_os.domain.research.fact import Fact, FactStatus
from enterprise_os.domain.research.evidence import Evidence


def test_strategic_orchestrator_cycle():
    ev = Evidence("e1", "src", "type", datetime.now(timezone.utc), "High", "High", (), (), "notes")
    fact = Fact("fact", (ev,), "High", FactStatus.VERIFIED)
    hyp = Hypothesis("h1", "t", "d", (fact,), (), "High", HypothesisStatus.SUPPORTED, "r", datetime.now(timezone.utc))
    finding = Finding("sum", (hyp,), "High", (), ())

    goal = StrategicGoal(
        identifier="g1",
        title="Value",
        description="Expand",
        category="Growth",
        desired_outcome="Win",
        priority="High",
        constraints=(),
        success_metrics=(),
        owner="CEO",
        created_timestamp=datetime.now(timezone.utc)
    )

    orchestrator = StrategicOrchestrator()
    recommendation = orchestrator.execute_cycle(goal, (finding,))
    
    assert recommendation is not None
    assert "Recommend" in recommendation.executive_summary
    assert recommendation.decision.selected_option is not None
    assert len(recommendation.decision.rejected_alternatives) > 0
    # Provenance
    assert recommendation.supporting_findings[0].hypotheses_used[0].supporting_facts[0].supporting_evidence[0].identifier == "e1"
