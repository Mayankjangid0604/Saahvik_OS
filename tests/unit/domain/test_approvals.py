from datetime import datetime, timezone
from enterprise_os.domain.approvals.request import ApprovalRequest

def test_approval_request():
    req = ApprovalRequest(
        identifier="req-1",
        description="Approve budget",
        reason="Need to buy server",
        created_at=datetime.now(timezone.utc)
    )
    assert req.identifier == "req-1"
    assert not req.is_approved
