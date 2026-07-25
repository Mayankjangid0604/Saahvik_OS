from dataclasses import dataclass

@dataclass
class ApprovalRequest:
    id: str
    decision_justification: str
    approved: bool = False
    feedback: str = ""
