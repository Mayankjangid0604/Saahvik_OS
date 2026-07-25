from datetime import datetime, timezone
from enterprise_os.domain.strategy.goal import StrategicGoal
from enterprise_os.application.services.organisational_orchestrator import OrganisationalOrchestrator


def test_organisational_orchestrator_cycle():
    goal = StrategicGoal(
        identifier="g1",
        title="Scale",
        description="Scale company",
        category="Growth",
        desired_outcome="Win",
        priority="High",
        constraints=(),
        success_metrics=(),
        owner="CEO",
        created_timestamp=datetime.now(timezone.utc)
    )

    orchestrator = OrganisationalOrchestrator()
    recommendation = orchestrator.execute_cycle((goal,))
    
    assert recommendation is not None
    assert "Organisation structured" in recommendation.executive_summary
    assert recommendation.blueprint.strategic_goals[0].identifier == "g1"
    assert len(recommendation.blueprint.departments) > 0
    assert len(recommendation.blueprint.roles) > 0
