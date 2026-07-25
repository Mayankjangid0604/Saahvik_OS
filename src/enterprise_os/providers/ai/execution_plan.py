from dataclasses import dataclass, field
from typing import Optional

@dataclass(frozen=True)
class AIExecutionPlan:
    provider_name: str
    model_name: str
    temperature: float = 0.7
    json_mode: bool = False
    max_tokens: Optional[int] = None
    retry_policy: int = 3
    fallback_models: list[str] = field(default_factory=list)
