import pytest
from datetime import datetime, timezone

from enterprise_os.domain.strategy.goal import StrategicGoal
from enterprise_os.domain.strategy.recommendation import FounderRecommendation
from enterprise_os.domain.strategy.decision import ExecutiveDecision


def test_strategic_goal():
    goal = StrategicGoal(
        identifier="g1",
        title="Increase Value",
        description="Expand",
        category="Growth",
        desired_outcome="Double revenue",
        priority="High",
        constraints=("No extra budget",),
        success_metrics=("Revenue",),
        owner="CEO",
        created_timestamp=datetime.now(timezone.utc)
    )
    assert goal.identifier == "g1"

def test_founder_recommendation_requires_findings():
    decision = ExecutiveDecision(
        selected_option=None,
        rejected_alternatives=(),
        reasoning="Because",
        confidence="High",
        expected_impact="High",
        supporting_findings=(),
        assumptions=()
    )
    with pytest.raises(ValueError, match="FounderRecommendation must have supporting findings"):
        FounderRecommendation(
            executive_summary="Sum",
            decision=decision,
            benefits=(),
            risks=(),
            assumptions=(),
            confidence="High",
            supporting_findings=(),
            open_questions=()
        )
