from typing import Any, Optional, Protocol
from enterprise_os.providers.ai.capability import Capability
from enterprise_os.providers.ai.response import AIResponse

class AIPort(Protocol):
    def request_capability(self, capability: Capability, prompt: str, system_prompt: str = "", kwargs: Optional[dict[str, Any]] = None) -> AIResponse:
        """
        The primary mechanism for the CEO to request cognitive processing.
        The underlying AI Platform is responsible for routing to the appropriate provider and model.
        """
        ...
