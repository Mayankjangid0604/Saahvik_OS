from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ToolResponse:
    success: bool
    result: Any
    error_message: str = ""
    execution_time: float = 0.0
