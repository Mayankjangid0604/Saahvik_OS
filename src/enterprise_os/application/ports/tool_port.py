from typing import Protocol, Any
from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.response import ToolResponse

from enterprise_os.providers.tools.capability import ToolCapability

class ToolPort(Protocol):
    def execute_tool(self, capability: ToolCapability, arguments: dict[str, Any] = None) -> ToolResponse:
        """
        The primary mechanism for the CEO to request tool execution.
        The underlying Tool Platform routes this to the correct provider.
        """
        ...
