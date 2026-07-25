import pytest

from enterprise_os.providers.ai.metrics import MetricsCollector

def test_metrics_collector():
    collector = MetricsCollector()
    
    collector.record_request("ollama", "llama3", latency=2.5, p_tokens=10, c_tokens=20)
    collector.record_request("ollama", "llama3", latency=1.0, p_tokens=5, c_tokens=10, failed=True)
    
    p_metrics = collector._get_provider("ollama")
    assert p_metrics.total_requests == 2
    assert p_metrics.total_failures == 1
    assert p_metrics.total_latency_seconds == 3.5
    assert p_metrics.total_prompt_tokens == 15
    assert p_metrics.total_completion_tokens == 30
    
    m_metrics = collector._get_model("llama3")
    assert m_metrics.total_requests == 2
