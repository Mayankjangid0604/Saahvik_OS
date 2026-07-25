from dataclasses import dataclass, field
from typing import Any

from enterprise_os.providers.tools.capability import ToolCapability

@dataclass(frozen=True)
class WorkItem:
    id: str
    objective: str
    allowed_tools: list[ToolCapability] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class StructuredResult:
    work_item_id: str
    success: bool
    findings: str
    artifacts: dict[str, Any] = field(default_factory=dict)
