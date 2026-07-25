from enterprise_os.application.use_cases.boot_ceo import BootCEO
from tests.support import InMemoryActionLogger, InMemoryDocumentStore, InMemoryThoughtLogger


def test_ceo_runtime_can_execute_a_bounded_cycle() -> None:
    logger = InMemoryActionLogger()
    runtime = BootCEO(
        document_loader=InMemoryDocumentStore(),
        action_logger=logger,
        thought_logger=InMemoryThoughtLogger(),
    ).execute()

    runtime.run(max_cycles=1)

    assert "ceo_loop_started" in logger.actions
    assert "ceo_loop_cycle_started" in logger.actions
    assert "cognitive_cycle_started" in logger.actions
    assert "cognitive_cycle_completed" in logger.actions
    assert "ceo_loop_cycle_completed" in logger.actions


def test_ceo_runtime_recovers_from_iteration_errors() -> None:
    logger = InMemoryActionLogger()
    runtime = BootCEO(
        document_loader=InMemoryDocumentStore(),
        action_logger=logger,
        thought_logger=InMemoryThoughtLogger(),
    ).execute()

    def failing_step() -> None:
        raise RuntimeError("recoverable failure")

    runtime_with_failure = type(runtime)(
        context=runtime.context,
        action_logger=logger,
        loop_step=failing_step,
        sleeper=lambda seconds: None,
    )

    runtime_with_failure.run(max_cycles=1)

    recovery_events = [
        event for event in logger.events if event["action"] == "ceo_loop_cycle_recovered"
    ]
    assert len(recovery_events) == 1
    assert recovery_events[0]["result"] == "recovered"
    assert "RuntimeError: recoverable failure" == recovery_events[0]["error"]
