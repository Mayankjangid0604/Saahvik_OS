from typing import Optional
from enterprise_os.providers.ai.model import AIModel
from enterprise_os.providers.ai.provider import AIProvider

class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, AIModel] = {}
        self._providers: dict[str, AIProvider] = {}
        
    def register_provider(self, provider: AIProvider) -> None:
        self._providers[provider.name] = provider
        
    def register_model(self, model: AIModel) -> None:
        self._models[model.name] = model
        
    def get_model(self, model_name: str) -> Optional[AIModel]:
        return self._models.get(model_name)
        
    def get_provider(self, provider_name: str) -> Optional[AIProvider]:
        return self._providers.get(provider_name)
        
    def list_models(self) -> list[AIModel]:
        return list(self._models.values())
        
    def clear_models(self) -> None:
        self._models.clear()
