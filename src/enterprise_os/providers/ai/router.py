from enterprise_os.providers.ai.registry import ModelRegistry
from enterprise_os.providers.ai.model import AIModel
from enterprise_os.providers.ai.capability import Capability
from enterprise_os.providers.ai.config import AIConfig, PolicyRule
from enterprise_os.providers.ai.exceptions import RoutingError
from enterprise_os.providers.ai.execution_plan import AIExecutionPlan

class AIRouter:
    def __init__(self, registry: ModelRegistry, config: AIConfig) -> None:
        self._registry = registry
        self._config = config
        
    def _get_policy_for_capability(self, capability: Capability) -> PolicyRule:
        return self._config.routing_policies.get(capability.name, PolicyRule())
        
    def _get_candidates(self, capability: Capability, policy: PolicyRule) -> list[AIModel]:
        candidates = []
        for model in self._registry.list_models():
            if capability not in model.capabilities:
                continue
            if policy.require_local and model.provider != "ollama":
                continue
            if model.context_window < policy.min_context:
                continue
            if policy.require_json and not model.supports_json:
                continue
            if policy.require_tools and not model.supports_tools:
                continue
            if model.health != "healthy":
                continue
            candidates.append(model)
        return candidates
        
    def _score_model(self, model: AIModel) -> int:
        score = 0
        if model.name in self._config.preferred_models:
            score += 100
        score += min(model.context_window // 1000, 10)
        return score
        
    def route(self, capability: Capability) -> AIExecutionPlan:
        policy = self._get_policy_for_capability(capability)
        candidates = self._get_candidates(capability, policy)
        
        best_model = None
        if not candidates:
            # Check fallbacks
            for fallback in self._config.fallback_models:
                m = self._registry.get_model(fallback)
                if m and m.health == "healthy":
                    best_model = m
                    break
            if not best_model:
                raise RoutingError(f"No suitable model found for capability {capability.name}")
        else:
            best_model = max(candidates, key=self._score_model)
            
        return AIExecutionPlan(
            provider_name=best_model.provider,
            model_name=best_model.name,
            temperature=self._config.temperature_defaults,
            json_mode=policy.require_json,
            max_tokens=None,
            retry_policy=self._config.retry_policy,
            fallback_models=self._config.fallback_models
        )
