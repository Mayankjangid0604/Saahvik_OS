from dataclasses import dataclass
from typing import Dict

@dataclass
class ProviderHealth:
    provider_name: str
    status: str # "online", "offline", "degraded"
    failures: int = 0
    
class HealthMonitor:
    def __init__(self) -> None:
        self._provider_health: Dict[str, ProviderHealth] = {}
        
    def record_success(self, provider_name: str) -> None:
        if provider_name not in self._provider_health:
            self._provider_health[provider_name] = ProviderHealth(provider_name, "online")
        self._provider_health[provider_name].status = "online"
        self._provider_health[provider_name].failures = 0
        
    def record_failure(self, provider_name: str) -> None:
        if provider_name not in self._provider_health:
            self._provider_health[provider_name] = ProviderHealth(provider_name, "degraded")
        health = self._provider_health[provider_name]
        health.failures += 1
        if health.failures > 3:
            health.status = "offline"
        else:
            health.status = "degraded"
            
    def get_health(self, provider_name: str) -> str:
        return self._provider_health.get(provider_name, ProviderHealth(provider_name, "online")).status
