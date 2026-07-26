from typing import Any, Optional, Protocol
from enterprise_os.providers.tools.response import ToolResponse

from enterprise_os.providers.tools.capability import ToolCapability

class ToolPort(Protocol):
    def execute_tool(self, capability: ToolCapability, arguments: Optional[dict[str, Any]] = None) -> ToolResponse:
        """
        The primary mechanism for the CEO to request tool execution.
        The underlying Tool Platform routes this to the correct provider.
        """
        ...
