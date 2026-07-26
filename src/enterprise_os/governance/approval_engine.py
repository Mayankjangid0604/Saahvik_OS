import uuid
from dataclasses import dataclass
from enterprise_os.runtime.events import EventDispatcher, Event

@dataclass(frozen=True, kw_only=True)
class ApprovalRequested(Event):
    approval_id: str
    justification: str
    context: str

@dataclass(frozen=True, kw_only=True)
class ApprovalGranted(Event):
    approval_id: str
    feedback: str

@dataclass(frozen=True, kw_only=True)
class ApprovalRejected(Event):
    approval_id: str
    feedback: str

@dataclass
class ApprovalItem:
    id: str
    justification: str
    context: str
    status: str = "PENDING"
    feedback: str = ""

class ApprovalEngine:
    def __init__(self, dispatcher: EventDispatcher) -> None:
        self.dispatcher = dispatcher
        self._queue: dict[str, ApprovalItem] = {}

    def request_approval(self, justification: str, context: str) -> str:
        approval_id = str(uuid.uuid4())
        item = ApprovalItem(id=approval_id, justification=justification, context=context)
        self._queue[approval_id] = item
        self.dispatcher.dispatch(ApprovalRequested(
            approval_id=approval_id,
            justification=justification,
            context=context
        ))
        return approval_id

    def resolve_approval(self, approval_id: str, approved: bool, feedback: str = "") -> None:
        if approval_id not in self._queue:
            raise ValueError(f"Approval {approval_id} not found.")
            
        item = self._queue[approval_id]
        if item.status != "PENDING":
            raise ValueError(f"Approval {approval_id} already resolved.")
            
        item.status = "APPROVED" if approved else "REJECTED"
        item.feedback = feedback
        
        if approved:
            self.dispatcher.dispatch(ApprovalGranted(approval_id=approval_id, feedback=feedback))
        else:
            self.dispatcher.dispatch(ApprovalRejected(approval_id=approval_id, feedback=feedback))

    def get_pending_approvals(self) -> list[ApprovalItem]:
        return [item for item in self._queue.values() if item.status == "PENDING"]
