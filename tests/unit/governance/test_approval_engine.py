from enterprise_os.governance.approval_engine import ApprovalEngine, ApprovalRequested, ApprovalGranted, ApprovalRejected
from enterprise_os.runtime.events import EventDispatcher, Event

def test_approval_engine():
    dispatcher = EventDispatcher()
    engine = ApprovalEngine(dispatcher)
    events = []
    
    def handler(evt: Event):
        events.append(evt)
        
    dispatcher.subscribe(ApprovalRequested, handler)
    dispatcher.subscribe(ApprovalGranted, handler)
    dispatcher.subscribe(ApprovalRejected, handler)
    
    # Request approval
    approval_id = engine.request_approval("Need to delete DB", "Context")
    assert len(engine.get_pending_approvals()) == 1
    assert len(events) == 1
    assert isinstance(events[0], ApprovalRequested)
    
    # Resolve approval
    engine.resolve_approval(approval_id, False, "Too dangerous")
    assert len(engine.get_pending_approvals()) == 0
    assert len(events) == 2
    assert isinstance(events[1], ApprovalRejected)
    assert events[1].feedback == "Too dangerous"
