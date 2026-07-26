import hashlib
import json
from time import time
from typing import Optional, Dict

from enterprise_os.providers.ai.request import AIRequest
from enterprise_os.providers.ai.response import AIResponse

class ResponseCache:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._cache: Dict[str, tuple[AIResponse, float]] = {}
        
    def _generate_key(self, provider: str, model: str, request: AIRequest) -> str:
        data = {
            "p": provider,
            "m": model,
            "pr": request.prompt,
            "sp": request.system_prompt,
            "msg": request.messages,
            "temp": request.temperature,
            "cap": request.capability.name
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        
    def get(self, provider: str, model: str, request: AIRequest) -> Optional[AIResponse]:
        key = self._generate_key(provider, model, request)
        if key in self._cache:
            response, timestamp = self._cache[key]
            if time() - timestamp <= self._ttl:
                return response
            else:
                del self._cache[key]
        return None
        
    def set(self, provider: str, model: str, request: AIRequest, response: AIResponse) -> None:
        key = self._generate_key(provider, model, request)
        self._cache[key] = (response, time())
