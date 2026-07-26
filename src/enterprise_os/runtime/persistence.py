import json
import logging
from pathlib import Path
from typing import Protocol, Any, Optional
from enterprise_os.runtime.events import EventDispatcher, Event
from enterprise_os.runtime.executive_session import ExecutiveSession
from enterprise_os.runtime.executive_state import ExecutiveState
from enterprise_os.runtime.plan import Plan
from enterprise_os.runtime.step import Step, StepStatus
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
            "memory": session.context.memory,
            "plan": self._serialize_plan(session.context.plan) if session.context.plan else None,
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, session_id: str) -> ExecutiveSession:
        path = self.storage_dir / f"{session_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        with open(path, "r") as f:
            data = json.load(f)

        session = ExecutiveSession(id=session_id)
        session.context.state = ExecutiveState[data["state"]]
        session.context.memory = data.get("memory", {})
        plan_data = data.get("plan")
        session.context.plan = self._deserialize_plan(plan_data) if plan_data else None
        return session

    @staticmethod
    def _serialize_plan(plan: Plan) -> dict[str, Any]:
        return {
            "id": plan.id,
            "goal_id": plan.goal_id,
            "current_step_index": plan.current_step_index,
            "steps": [
                {"id": s.id, "description": s.description, "status": s.status.name, "result": s.result}
                for s in plan.steps
            ],
        }

    @staticmethod
    def _deserialize_plan(data: dict[str, Any]) -> Plan:
        steps = [
            Step(id=s["id"], description=s["description"], status=StepStatus[s["status"]], result=s.get("result"))
            for s in data["steps"]
        ]
        return Plan(id=data["id"], goal_id=data["goal_id"], steps=steps, current_step_index=data["current_step_index"])

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
