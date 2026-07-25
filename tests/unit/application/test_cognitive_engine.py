from datetime import UTC, datetime

from enterprise_os.application.services.cognitive_engine import CognitiveEngine
from enterprise_os.application.use_cases.boot_ceo import BootCEO
from enterprise_os.domain.cognition.cycle import CognitiveCycle
from enterprise_os.domain.cognition.reasoning import ExecutiveReasoner
from tests.support import InMemoryActionLogger, InMemoryDocumentStore, InMemoryThoughtLogger


def test_cognitive_engine_completes_one_deterministic_cycle() -> None:
    action_logger = InMemoryActionLogger()
    thought_logger = InMemoryThoughtLogger()
    runtime = BootCEO(
        document_loader=InMemoryDocumentStore(),
        action_logger=action_logger,
        thought_logger=thought_logger,
    ).execute()
    engine = CognitiveEngine(
        context=runtime.context,
        reasoner=ExecutiveReasoner(),
        thought_logger=thought_logger,
        action_logger=action_logger,
        clock=lambda: datetime(2026, 7, 26, tzinfo=UTC),
    )

    first_cycle = engine.complete_cycle()
    second_cycle = engine.complete_cycle()

    assert first_cycle.cycle_id == "cognitive-cycle-1"
    assert second_cycle.cycle_id == "cognitive-cycle-2"
    assert first_cycle.decision.chosen_strategy.title == second_cycle.decision.chosen_strategy.title
    assert first_cycle.benefits_evaluation
    assert first_cycle.challenged_assumptions
    assert first_cycle.decision.reasoning
    assert first_cycle.reflection.learned
    assert len(thought_logger.cycles) == 2


def test_cognitive_engine_rejects_weak_ideas() -> None:
    action_logger = InMemoryActionLogger()
    thought_logger = InMemoryThoughtLogger()
    runtime = BootCEO(
        document_loader=InMemoryDocumentStore(),
        action_logger=action_logger,
        thought_logger=thought_logger,
    ).execute()
    engine = CognitiveEngine(
        context=runtime.context,
        reasoner=ExecutiveReasoner(),
        thought_logger=thought_logger,
        action_logger=action_logger,
        clock=lambda: datetime(2026, 7, 26, tzinfo=UTC),
    )

    cycle = engine.complete_cycle()

    rejected = [strategy for strategy in cycle.strategies if strategy.rejection_reason]
    assert rejected
    assert "waiting for future capabilities" in rejected[0].rejection_reason
    assert cycle.prioritised_strategies[0].recommendation == "Recommended"


def test_cognitive_engine_logs_failures_before_runtime_recovery() -> None:
    class FailingThoughtLogger:
        def log_cycle(self, cycle: CognitiveCycle) -> None:
            raise RuntimeError("thought log unavailable")

    action_logger = InMemoryActionLogger()
    runtime = BootCEO(
        document_loader=InMemoryDocumentStore(),
        action_logger=action_logger,
        thought_logger=InMemoryThoughtLogger(),
    ).execute()
    engine = CognitiveEngine(
        context=runtime.context,
        reasoner=ExecutiveReasoner(),
        thought_logger=FailingThoughtLogger(),
        action_logger=action_logger,
        clock=lambda: datetime(2026, 7, 26, tzinfo=UTC),
    )

    try:
        engine.complete_cycle()
    except RuntimeError:
        pass
    else:
        raise AssertionError("CognitiveEngine should re-raise thought logging failures")

    failure_events = [
        event for event in action_logger.events if event["action"] == "cognitive_cycle_failed"
    ]
    assert len(failure_events) == 1
    assert failure_events[0]["result"] == "failure"
    assert failure_events[0]["error"] == "RuntimeError: thought log unavailable"
