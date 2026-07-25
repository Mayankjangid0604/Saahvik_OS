import json
import logging
from pathlib import Path
from typing import Protocol, Any
from enterprise_os.runtime.events import EventDispatcher, Event
from enterprise_os.runtime.executive_session import ExecutiveSession
from dataclasses import asdict

class SessionRepository(Protocol):
    def save(self, session: ExecutiveSession) -> None:
        ...
        
    def load(self, session_id: str) -> ExecutiveSession:
        ...

class AuditLog(Protocol):
    def log_event(self, event: Event) -> None:
        ...

class FileSessionRepository(SessionRepository):
    def __init__(self, storage_dir: str = "sessions") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def save(self, session: ExecutiveSession) -> None:
        path = self.storage_dir / f"{session.id}.json"
        data = {
            "id": session.id,
            "state": session.context.state.name,
            "memory": session.context.memory
        }
        with open(path, "w") as f:
            json.dump(data, f)
            
    def load(self, session_id: str) -> ExecutiveSession:
        path = self.storage_dir / f"{session_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Session {session_id} not found")
        # Minimal loading for demonstration
        return ExecutiveSession(id=session_id)

class FileAuditLog(AuditLog):
    def __init__(self, log_dir: str = "logs") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("AuditLog")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(self.log_dir / "audit.log")
            formatter = logging.Formatter('%(message)s') # Timestamp is in the event already
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            
    def bind_to(self, dispatcher: EventDispatcher, event_types: list[type]) -> None:
        for etype in event_types:
            dispatcher.subscribe(etype, self.log_event)

    def log_event(self, event: Event) -> None:
        event_name = type(event).__name__
        payload = asdict(event)
        self.logger.info(f"{event_name}: {json.dumps(payload)}")
