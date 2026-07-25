from datetime import UTC, datetime

from enterprise_os.domain.cognition.decision import DecisionRecord
from enterprise_os.domain.cognition.opportunity import Opportunity
from enterprise_os.domain.cognition.reflection import Reflection
from enterprise_os.domain.cognition.risk import RiskDimension, RiskProfile
from enterprise_os.domain.cognition.strategy import StrategyOption
from enterprise_os.domain.cognition.thought import Thought
from enterprise_os.domain.cognition.cycle import CognitiveCycle


def test_thought_structure_contains_required_fields() -> None:
    thought = Thought(
        observation="Observed state",
        objective="Improve reasoning",
        assumptions=("Internal state is accurate",),
        evidence=("Company state loaded",),
        alternatives=("Option A", "Option B"),
        risks=("Low external evidence",),
        opportunities=("Clarify direction",),
        confidence="High",
        recommendation="Recommended",
        reasoning="The recommendation is explained.",
    )

    assert thought.observation
    assert thought.objective
    assert thought.assumptions
    assert thought.evidence
    assert thought.alternatives
    assert thought.risks
    assert thought.opportunities
    assert thought.confidence
    assert thought.recommendation
    assert thought.reasoning


def test_decision_record_is_valid_and_explained() -> None:
    strategy = StrategyOption(
        title="Reason from current state",
        description="Think before acting.",
        strengths=("Explainable",),
        weaknesses=("No external evidence",),
        risks=("Limited context",),
        benefits=("No premature execution",),
        assumptions=("Loaded state is valid",),
        confidence="High",
        recommendation="Recommended",
    )

    decision = DecisionRecord(
        problem="No active executive initiatives.",
        alternatives=(strategy,),
        reasoning="Chosen because it creates an explained decision without execution.",
        chosen_strategy=strategy,
        confidence="High",
        timestamp=datetime(2026, 7, 26, tzinfo=UTC),
    )

    assert decision.problem
    assert decision.alternatives == (strategy,)
    assert decision.chosen_strategy == strategy
    assert decision.reasoning
    assert decision.confidence == "High"
    assert decision.timestamp.isoformat() == "2026-07-26T00:00:00+00:00"


def test_risk_and_opportunity_frameworks_are_extensible() -> None:
    risk_profile = RiskProfile(
        dimensions=(
            RiskDimension(
                name="technical",
                assessment="Layer boundaries could blur.",
                mitigation="Keep persistence outside the domain.",
                confidence="High",
            ),
        ),
        overall_confidence="High",
    )
    opportunity = Opportunity(
        title="Clarify direction",
        description="Use internal state to reason.",
        expected_value="Better executive focus",
        difficulty="Low",
        uncertainty="Medium",
        assumptions=("No external evidence is available.",),
        recommendation="Proceed internally only.",
    )
    reflection = Reflection(
        learned="Reasoning can be deterministic.",
        missed_anything="External context is absent.",
        should_reconsider="Yes, when new evidence exists.",
        reasoning_improvement="Compare rejected alternatives more deeply.",
    )

    assert risk_profile.dimensions[0].name == "technical"
    assert opportunity.recommendation == "Proceed internally only."
    assert reflection.reasoning_improvement


def test_thought_rejects_unexplained_recommendations() -> None:
    try:
        Thought(
            observation="Observed state",
            objective="Improve reasoning",
            assumptions=("Internal state is accurate",),
            evidence=("Company state loaded",),
            alternatives=("Option A",),
            risks=("Risk exists",),
            opportunities=("Opportunity exists",),
            confidence="High",
            recommendation="Recommended",
            reasoning="",
        )
    except ValueError as exc:
        assert "reasoning" in str(exc)
    else:
        raise AssertionError("Thought should reject empty reasoning")


def test_rejected_strategy_requires_rejection_reason() -> None:
    try:
        StrategyOption(
            title="Wait indefinitely",
            description="Delay all executive reasoning.",
            strengths=("Avoids overconfidence",),
            weaknesses=("No executive direction",),
            risks=("Stagnation",),
            benefits=("Avoids unsupported claims",),
            assumptions=("Future input arrives",),
            confidence="Medium",
            recommendation="Rejected",
        )
    except ValueError as exc:
        assert "rejection_reason" in str(exc)
    else:
        raise AssertionError("Rejected strategy should require a rejection reason")


def test_decision_must_choose_from_alternatives() -> None:
    chosen = StrategyOption(
        title="Chosen",
        description="A chosen option.",
        strengths=("Clear",),
        weaknesses=("Limited",),
        risks=("Risk",),
        benefits=("Benefit",),
        assumptions=("Assumption",),
        confidence="High",
        recommendation="Recommended",
    )
    alternative = StrategyOption(
        title="Alternative",
        description="Another option.",
        strengths=("Clear",),
        weaknesses=("Limited",),
        risks=("Risk",),
        benefits=("Benefit",),
        assumptions=("Assumption",),
        confidence="High",
        recommendation="Recommended",
    )

    try:
        DecisionRecord(
            problem="Pick a strategy.",
            alternatives=(alternative,),
            reasoning="Chosen strategy must be listed.",
            chosen_strategy=chosen,
            confidence="High",
            timestamp=datetime(2026, 7, 26, tzinfo=UTC),
        )
    except ValueError as exc:
        assert "chosen_strategy" in str(exc)
    else:
        raise AssertionError("Decision should reject a chosen strategy outside alternatives")


def test_cognitive_cycle_serializes_nested_thought_structures() -> None:
    strategy = StrategyOption(
        title="Reason from current state",
        description="Think before acting.",
        strengths=("Explainable",),
        weaknesses=("No external evidence",),
        risks=("Limited context",),
        benefits=("No premature execution",),
        assumptions=("Loaded state is valid",),
        confidence="High",
        recommendation="Recommended",
    )
    decision = DecisionRecord(
        problem="Pick a strategy.",
        alternatives=(strategy,),
        reasoning="Chosen because it keeps cognition internal.",
        chosen_strategy=strategy,
        confidence="High",
        timestamp=datetime(2026, 7, 26, tzinfo=UTC),
    )
    cycle = CognitiveCycle(
        cycle_id="cognitive-cycle-1",
        started_at=datetime(2026, 7, 26, tzinfo=UTC),
        observation="Observed state",
        understanding="Understood state",
        problems=("No active executive initiatives.",),
        internal_objectives=("Improve reasoning.",),
        opportunities=(
            Opportunity(
                title="Clarify direction",
                description="Use internal state to reason.",
                expected_value="Better executive focus",
                difficulty="Low",
                uncertainty="Medium",
                assumptions=("No external evidence is available.",),
                recommendation="Proceed internally only.",
            ),
        ),
        strategies=(strategy,),
        risk_profile=RiskProfile(
            dimensions=(
                RiskDimension(
                    name="technical",
                    assessment="Layer boundaries could blur.",
                    mitigation="Keep persistence outside the domain.",
                    confidence="High",
                ),
            ),
            overall_confidence="High",
        ),
        benefits_evaluation=("Reasoning remains internal.",),
        challenged_assumptions=("Verify the loaded state.",),
        prioritised_strategies=(strategy,),
        decision=decision,
        reflection=Reflection(
            learned="Reasoning can be deterministic.",
            missed_anything="External context is absent.",
            should_reconsider="Yes, when new evidence exists.",
            reasoning_improvement="Compare rejected alternatives more deeply.",
        ),
        thought=Thought(
            observation="Observed state",
            objective="Improve reasoning",
            assumptions=("Internal state is accurate",),
            evidence=("Company state loaded",),
            alternatives=("Option A", "Option B"),
            risks=("Low external evidence",),
            opportunities=("Clarify direction",),
            confidence="High",
            recommendation="Recommended",
            reasoning="The recommendation is explained.",
        ),
        runtime_learning=("Reasoning remains internal until an approved action boundary exists.",),
    )

    mapping = cycle.to_mapping()

    assert mapping["decision"]["chosen_strategy"]["title"] == "Reason from current state"
    assert mapping["thought"]["reasoning"] == "The recommendation is explained."
    assert mapping["risk_profile"]["dimensions"][0]["mitigation"] == (
        "Keep persistence outside the domain."
    )


def test_decision_rejects_naive_timestamps() -> None:
    strategy = StrategyOption(
        title="Reason from current state",
        description="Think before acting.",
        strengths=("Explainable",),
        weaknesses=("No external evidence",),
        risks=("Limited context",),
        benefits=("No premature execution",),
        assumptions=("Loaded state is valid",),
        confidence="High",
        recommendation="Recommended",
    )

    try:
        DecisionRecord(
            problem="Pick a strategy.",
            alternatives=(strategy,),
            reasoning="Chosen because it keeps cognition internal.",
            chosen_strategy=strategy,
            confidence="High",
            timestamp=datetime(2026, 7, 26),
        )
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError("DecisionRecord should reject naive timestamps")
