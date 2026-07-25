from dataclasses import dataclass
from enum import Enum

class MemoryLayer(Enum):
    RUNTIME = "runtime"
    ENTERPRISE = "enterprise"
    HISTORICAL = "historical"

@dataclass(frozen=True)
class RetrievalRequest:
    query: str
    target_layer: MemoryLayer
    search_criteria: tuple[str, ...]
