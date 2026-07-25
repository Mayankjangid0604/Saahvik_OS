from typing import Protocol
from enterprise_os.providers.ai.model import AIModel

class ModelDiscovery(Protocol):
    def discover_models(self) -> list[AIModel]:
        """Discovers models and returns their metadata."""
        ...
