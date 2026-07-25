from dataclasses import dataclass
from typing import Set

from enterprise_os.providers.ai.capability import Capability

@dataclass(frozen=True)
class AIModel:
    name: str
    provider: str
    context_window: int
    supports_tools: bool
    supports_json: bool
    supports_embeddings: bool
    supports_vision: bool
    supports_streaming: bool
    capabilities: Set[Capability]
    health: str  # "healthy", "degraded", "offline"
