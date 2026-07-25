from dataclasses import dataclass, field
from typing import Any

from enterprise_os.providers.ai.capability import Capability

@dataclass(frozen=True)
class AIRequest:
    prompt: str
    system_prompt: str = ""
    messages: list[dict[str, str]] = field(default_factory=list)
    capability: Capability = Capability.GENERAL_CHAT
    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float = 1.0
    stop: list[str] | None = None
    json_mode: bool = False
    attachments: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
