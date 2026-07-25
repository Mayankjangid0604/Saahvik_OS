from typing import Protocol, runtime_checkable
from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.response import ToolResponse

from enterprise_os.providers.tools.capability import ToolCapability

@runtime_checkable
class ToolProvider(Protocol):
    @property
    def name(self) -> str:
        ...

    @property
    def capabilities(self) -> list[ToolCapability]:
        """Returns the list of capabilities this provider supports."""
        ...

    def execute(self, request: ToolRequest) -> ToolResponse:
        """Executes the tool request and returns the response."""
        ...
