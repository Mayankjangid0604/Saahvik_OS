from dataclasses import dataclass, field
from typing import Dict

@dataclass
class AIMetrics:
    total_requests: int = 0
    total_failures: int = 0
    total_retries: int = 0
    total_latency_seconds: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    
class MetricsCollector:
    def __init__(self) -> None:
        self._provider_metrics: Dict[str, AIMetrics] = {}
        self._model_metrics: Dict[str, AIMetrics] = {}
        
    def _get_provider(self, name: str) -> AIMetrics:
        if name not in self._provider_metrics:
            self._provider_metrics[name] = AIMetrics()
        return self._provider_metrics[name]

    def _get_model(self, name: str) -> AIMetrics:
        if name not in self._model_metrics:
            self._model_metrics[name] = AIMetrics()
        return self._model_metrics[name]

    def record_request(self, provider: str, model: str, latency: float, p_tokens: int, c_tokens: int, retries: int = 0, failed: bool = False) -> None:
        for metrics in (self._get_provider(provider), self._get_model(model)):
            metrics.total_requests += 1
            if failed:
                metrics.total_failures += 1
            metrics.total_retries += retries
            metrics.total_latency_seconds += latency
            metrics.total_prompt_tokens += p_tokens
            metrics.total_completion_tokens += c_tokens
