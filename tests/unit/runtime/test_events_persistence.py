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
