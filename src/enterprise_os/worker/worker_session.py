import uuid
from dataclasses import dataclass, field

@dataclass
class WorkerSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    objective: str = ""
    isolated_memory: dict[str, str] = field(default_factory=dict)
