from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ApprovalRequest:
    identifier: str
    description: str
    reason: str
    created_at: datetime
    is_approved: bool = False
