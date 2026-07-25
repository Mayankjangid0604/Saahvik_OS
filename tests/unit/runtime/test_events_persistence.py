import pytest
import os
from pathlib import Path
from enterprise_os.runtime.events import EventDispatcher, GoalCreated, Event
from enterprise_os.runtime.persistence import FileSessionRepository, FileAuditLog
from enterprise_os.runtime.executive_session import ExecutiveSession
from enterprise_os.runtime.executive_state import ExecutiveState

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

def test_file_session_repository(tmp_path: Path):
    repo = FileSessionRepository(storage_dir=str(tmp_path))
    session = ExecutiveSession(id="test_session")
    session.context.transition(ExecutiveState.PLANNING)
    
    repo.save(session)
    
    file_path = tmp_path / "test_session.json"
    assert file_path.exists()
    
    loaded_session = repo.load("test_session")
    assert loaded_session.id == "test_session"

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
