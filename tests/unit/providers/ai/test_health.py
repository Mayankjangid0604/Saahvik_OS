
from enterprise_os.providers.ai.health import HealthMonitor

def test_health_monitor():
    monitor = HealthMonitor()
    
    monitor.record_success("ollama")
    assert monitor.get_health("ollama") == "online"
    
    monitor.record_failure("ollama")
    assert monitor.get_health("ollama") == "degraded"
    
    monitor.record_failure("ollama")
    monitor.record_failure("ollama")
    monitor.record_failure("ollama") # 4th failure
    assert monitor.get_health("ollama") == "offline"
    
    monitor.record_success("ollama")
    assert monitor.get_health("ollama") == "online"
