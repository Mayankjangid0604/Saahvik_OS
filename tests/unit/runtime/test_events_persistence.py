import pytest
import os
from pathlib import Path
from enterprise_os.runtime.events import EventDispatcher, GoalCreated, Event
from enterprise_os.runtime.persistence import FileSessionRepository, FileAuditLog
from enterprise_os.runtime.executive_session import ExecutiveSession
from enterprise_os.runtime.executive_state import ExecutiveState
from enterprise_os.runtime.plan import Plan
from enterprise_os.runtime.step import Step, StepStatus

def test_event_dispatcher():
    dispatcher = EventDispatcher()
    received_events = []
    
    def handler(event: Event):
        received_events.append(event)
        
    dispatcher.subscribe(GoalCreated, handler)
    
    evt = GoalCreated(session_id="s1", goal_id="g1", description="Desc")
    dispatcher.dispatch(evt)
    
    assert len(received_events) == 1
    assert received_events[0].goal_id == "g1"

def test_event_dispatcher_wildcard_subscription_receives_subclass_events():
    """Regression test: EventDispatcher previously matched subscribers by exact
    type(event), so subscribing to the base Event class (as EventStreamer does,
    to receive every event for the WebSocket dashboard) never matched any
    concrete event, since only subclasses like GoalCreated are ever dispatched."""
    dispatcher = EventDispatcher()
    received_events = []

    dispatcher.subscribe(Event, lambda evt: received_events.append(evt))

    dispatcher.dispatch(GoalCreated(session_id="s3", goal_id="g3", description="Desc"))

    assert len(received_events) == 1
    assert received_events[0].goal_id == "g3"

def test_file_session_repository(tmp_path: Path):
    repo = FileSessionRepository(storage_dir=str(tmp_path))
    session = ExecutiveSession(id="test_session")
    session.context.transition(ExecutiveState.PLANNING)
    session.context.memory["pending_approval_id"] = "approval-123"

    repo.save(session)

    file_path = tmp_path / "test_session.json"
    assert file_path.exists()

    loaded_session = repo.load("test_session")
    assert loaded_session.id == "test_session"
    assert loaded_session.context.state == ExecutiveState.PLANNING
    assert loaded_session.context.memory == {"pending_approval_id": "approval-123"}

def test_file_session_repository_round_trips_mid_execution_plan(tmp_path: Path):
    """Regression test for P1-6: save()/load() previously only round-tripped
    state/memory, silently dropping the in-flight Plan/Step history. A session
    recovered mid-EXECUTING had no record of which step it was on or what the
    remaining plan was."""
    repo = FileSessionRepository(storage_dir=str(tmp_path))
    session = ExecutiveSession(id="mid_plan_session")
    session.context.transition(ExecutiveState.EXECUTING)
    session.context.plan = Plan(
        id="plan-g1",
        goal_id="g1",
        steps=[
            Step(id="1", description="Create workspace", status=StepStatus.COMPLETED, result="ok"),
            Step(id="2", description="Write app.py", status=StepStatus.IN_PROGRESS),
            Step(id="3", description="Run tests", status=StepStatus.PENDING),
        ],
        current_step_index=1,
    )

    repo.save(session)
    loaded_session = repo.load("mid_plan_session")

    assert loaded_session.context.state == ExecutiveState.EXECUTING
    restored_plan = loaded_session.context.plan
    assert restored_plan is not None
    assert restored_plan.id == "plan-g1"
    assert restored_plan.goal_id == "g1"
    assert restored_plan.current_step_index == 1
    assert [s.status for s in restored_plan.steps] == [
        StepStatus.COMPLETED, StepStatus.IN_PROGRESS, StepStatus.PENDING,
    ]
    assert restored_plan.steps[0].result == "ok"
    # The recovered session resumes at exactly the step it was on.
    assert restored_plan.get_next_step().id == "2"

def test_file_session_repository_load_missing_session(tmp_path: Path):
    repo = FileSessionRepository(storage_dir=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        repo.load("does-not-exist")

def test_file_audit_log(tmp_path: Path):
    dispatcher = EventDispatcher()
    audit = FileAuditLog(log_dir=str(tmp_path))
    audit.bind_to(dispatcher, [GoalCreated])

    evt = GoalCreated(session_id="s2", goal_id="g2", description="Audit Desc")
    dispatcher.dispatch(evt)

    log_file = tmp_path / "audit.log"
    assert log_file.exists()
    with open(log_file, "r") as f:
        content = f.read()
        assert "GoalCreated" in content
        assert "Audit Desc" in content

def test_file_audit_log_instances_do_not_share_a_handler(tmp_path: Path):
    """Regression test: FileAuditLog used a fixed logger name ("AuditLog"),
    which is a process-wide singleton in the logging module. The first
    instance created in the process would win the "if not handlers" guard,
    and every later instance would silently write to *that* instance's
    log_dir regardless of its own -- confirmed by importing ceo_api (which
    constructs its own FileAuditLog first) before this test previously made
    it fail."""
    dispatcher_a = EventDispatcher()
    dir_a = tmp_path / "a"
    audit_a = FileAuditLog(log_dir=str(dir_a))
    audit_a.bind_to(dispatcher_a, [GoalCreated])

    dispatcher_b = EventDispatcher()
    dir_b = tmp_path / "b"
    audit_b = FileAuditLog(log_dir=str(dir_b))
    audit_b.bind_to(dispatcher_b, [GoalCreated])

    dispatcher_a.dispatch(GoalCreated(session_id="sa", goal_id="ga", description="A"))
    dispatcher_b.dispatch(GoalCreated(session_id="sb", goal_id="gb", description="B"))

    log_a = (dir_a / "audit.log").read_text()
    log_b = (dir_b / "audit.log").read_text()
    assert "ga" in log_a and "gb" not in log_a
    assert "gb" in log_b and "ga" not in log_b

def test_file_audit_log_survives_construct_and_discard_churn(tmp_path: Path):
    """Regression test for a second-order bug in the P1-7 fix itself: the
    first fix scoped the logger name with id(self), but id() is only
    guaranteed unique among *simultaneously alive* objects, not across time.
    A tight construct-and-immediately-discard loop lets CPython reuse a freed
    instance's memory address for a later instance, so id() collides and the
    later instance silently inherits the earlier (unrelated, wrong-directory)
    instance's logger and handler -- reproduced directly during a round-2
    audit before switching to a monotonic counter."""
    churn_dir = tmp_path / "churn"
    for _ in range(50):
        FileAuditLog(log_dir=str(churn_dir))  # constructed and immediately discarded

    real_dir = tmp_path / "real"
    audit = FileAuditLog(log_dir=str(real_dir))
    dispatcher = EventDispatcher()
    audit.bind_to(dispatcher, [GoalCreated])
    dispatcher.dispatch(GoalCreated(session_id="s", goal_id="should-be-in-real-dir", description="d"))

    real_log = real_dir / "audit.log"
    assert real_log.exists()
    assert "should-be-in-real-dir" in real_log.read_text()
    churn_log = churn_dir / "audit.log"
    assert not churn_log.exists() or "should-be-in-real-dir" not in churn_log.read_text()

def test_file_audit_log_close_releases_its_handler(tmp_path: Path):
    audit = FileAuditLog(log_dir=str(tmp_path))
    assert len(audit.logger.handlers) == 1
    audit.close()
    assert len(audit.logger.handlers) == 0
