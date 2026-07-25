from dataclasses import dataclass, field

@dataclass
class PolicyRule:
    require_local: bool = False
    min_context: int = 0
    require_json: bool = False
    require_tools: bool = False

@dataclass
class AIConfig:
    preferred_models: list[str] = field(default_factory=list)
    fallback_models: list[str] = field(default_factory=list)
    routing_policies: dict[str, PolicyRule] = field(default_factory=dict) # string mapped to Capability name
    timeouts: int = 60
    retry_policy: int = 3
    cache_ttl_seconds: int = 3600
    streaming: bool = False
    temperature_defaults: float = 0.7
