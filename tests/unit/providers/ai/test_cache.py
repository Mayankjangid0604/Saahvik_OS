
from enterprise_os.providers.ai.cache import ResponseCache
from enterprise_os.providers.ai.request import AIRequest
from enterprise_os.providers.ai.response import AIResponse
from enterprise_os.providers.ai.capability import Capability

def test_response_cache():
    cache = ResponseCache(ttl_seconds=10)
    
    req = AIRequest(prompt="Hello", capability=Capability.GENERAL_CHAT)
    resp = AIResponse("Hi", "ollama", "llama3", Capability.GENERAL_CHAT, "stop", 1.0, 10, 10, 20)
    
    # Not in cache yet
    assert cache.get("ollama", "llama3", req) is None
    
    # Set cache
    cache.set("ollama", "llama3", req, resp)
    
    # Get cache
    cached_resp = cache.get("ollama", "llama3", req)
    assert cached_resp is not None
    assert cached_resp.text == "Hi"
    
    # Different prompt misses cache
    req2 = AIRequest(prompt="Hello there", capability=Capability.GENERAL_CHAT)
    assert cache.get("ollama", "llama3", req2) is None
