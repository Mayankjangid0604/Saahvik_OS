from dataclasses import dataclass, field
from typing import Any

from enterprise_os.providers.ai.capability import Capability

@dataclass(frozen=True)
class AIResponse:
    text: str
    provider: str
    model: str
    capability: Capability
    finish_reason: str
    duration: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    metadata: dict[str, Any] = field(default_factory=dict)
