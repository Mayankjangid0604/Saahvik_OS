import pytest

from enterprise_os.providers.ai.registry import ModelRegistry
from enterprise_os.providers.ai.model import AIModel
from enterprise_os.providers.ai.provider import AIProvider

class DummyProvider:
    @property
    def name(self) -> str:
        return "dummy"

def test_registry_registration():
    registry = ModelRegistry()
    provider = DummyProvider()
    
    registry.register_provider(provider)
    assert registry.get_provider("dummy") is provider
    
    model = AIModel("test-model", "dummy", 4096, False, False, False, False, False, set(), "healthy")
    registry.register_model(model)
    
    assert registry.get_model("test-model") is model
    assert len(registry.list_models()) == 1
    
    registry.clear_models()
    assert len(registry.list_models()) == 0
