import json
import urllib.request
from typing import Any, Dict

class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434") -> None:
        self.base_url = base_url.rstrip("/")
        
    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode('utf-8'))
            
    def _get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))

    def generate(self, model: str, prompt: str, system: str = "", options: Dict[str, Any] = None) -> Dict[str, Any]:
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        if options:
            payload["options"] = options
        return self._post("api/generate", payload)
        
    def chat(self, model: str, messages: list[dict[str, str]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if options:
            payload["options"] = options
        return self._post("api/chat", payload)
        
    def embeddings(self, model: str, prompt: str) -> Dict[str, Any]:
        payload = {
            "model": model,
            "prompt": prompt
        }
        return self._post("api/embeddings", payload)
        
    def list_models(self) -> Dict[str, Any]:
        return self._get("api/tags")
        
    def health(self) -> bool:
        try:
            url = f"{self.base_url}/"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False
