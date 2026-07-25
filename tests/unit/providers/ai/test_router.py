import pytest

from enterprise_os.providers.ai.router import AIRouter
from enterprise_os.providers.ai.registry import ModelRegistry
from enterprise_os.providers.ai.config import AIConfig, PolicyRule
from enterprise_os.providers.ai.model import AIModel
from enterprise_os.providers.ai.capability import Capability
from enterprise_os.providers.ai.exceptions import RoutingError

def test_router_scoring_engine():
    registry = ModelRegistry()
    
    # Model 1: Local, 8K context, Coding
    m1 = AIModel("qwen2.5-coder", "ollama", 8192, True, True, False, False, True, {Capability.CODING}, "healthy")
    # Model 2: Local, 32K context, Coding (should score higher due to context if preferred not set)
    m2 = AIModel("deepseek-coder", "ollama", 32768, True, True, False, False, True, {Capability.CODING}, "healthy")
    # Model 3: Local, 8K context, General (no coding)
    m3 = AIModel("llama3.1", "ollama", 8192, True, True, False, False, True, {Capability.GENERAL_CHAT}, "healthy")
    
    registry.register_model(m1)
    registry.register_model(m2)
    registry.register_model(m3)
    
    # Policy for CODING requires local and JSON
    config = AIConfig(
        preferred_models=["qwen2.5-coder"],  # This gets +100 score
        routing_policies={
            "CODING": PolicyRule(require_local=True, min_context=4000, require_json=True)
        }
    )
    
    router = AIRouter(registry, config)
    
    plan = router.route(Capability.CODING)
    
    # qwen2.5-coder should win because it is preferred (+100 score), even though deepseek has larger context
    assert plan.model_name == "qwen2.5-coder"
    assert plan.provider_name == "ollama"
    assert plan.json_mode is True

def test_router_fallback():
    registry = ModelRegistry()
    m1 = AIModel("gpt-4", "openai", 8192, True, True, False, False, True, {Capability.CODING}, "healthy")
    registry.register_model(m1)
    
    # Policy requires local, so gpt-4 will be filtered out. Fallback is gpt-4.
    config = AIConfig(
        fallback_models=["gpt-4"],
        routing_policies={
            "CODING": PolicyRule(require_local=True)
        }
    )
    
    router = AIRouter(registry, config)
    plan = router.route(Capability.CODING)
    
    assert plan.model_name == "gpt-4"

def test_router_no_model():
    registry = ModelRegistry()
    config = AIConfig()
    router = AIRouter(registry, config)
    
    with pytest.raises(RoutingError):
        router.route(Capability.CODING)
