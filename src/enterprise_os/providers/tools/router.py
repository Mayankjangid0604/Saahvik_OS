from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.provider import ToolProvider
from enterprise_os.providers.tools.registry import ToolRegistry
from enterprise_os.providers.tools.exceptions import ToolNotFoundError

from enterprise_os.providers.tools.capability import ToolCapability

class ToolRouter:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry
        
    def route(self, capability: ToolCapability) -> ToolProvider:
        """Finds the appropriate provider for the requested tool."""
        for provider in self._registry.list_providers():
            caps = getattr(provider, "capabilities", None)
            if caps and capability in caps:
                return provider
                
        raise ToolNotFoundError(f"No provider found capable of handling capability '{capability.name}'")
