import uuid
from dataclasses import dataclass, field
from enterprise_os.runtime.executive_context import ExecutiveContext

@dataclass
class ExecutiveSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: ExecutiveContext = field(init=False)
    
    def __post_init__(self):
        self.context = ExecutiveContext(session_id=self.id)
