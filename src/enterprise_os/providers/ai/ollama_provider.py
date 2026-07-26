from time import perf_counter
from typing import Any, Set

from enterprise_os.providers.ai.provider import AIProvider
from enterprise_os.providers.ai.request import AIRequest
from enterprise_os.providers.ai.response import AIResponse
from enterprise_os.providers.ai.model import AIModel
from enterprise_os.providers.ai.capability import Capability
from enterprise_os.providers.ai.ollama_client import OllamaClient
from enterprise_os.providers.ai.discovery import ModelDiscovery
from enterprise_os.providers.ai.exceptions import ProviderUnavailableError

class OllamaProvider(AIProvider, ModelDiscovery):
    def __init__(self, client: OllamaClient) -> None:
        self._client = client
        self._name = "ollama"

    @property
    def name(self) -> str:
        return self._name

    def health(self) -> str:
        return "online" if self._client.health() else "offline"

    def discover_models(self) -> list[AIModel]:
        try:
            tags = self._client.list_models()
        except Exception:
            return []
            
        models = []
        for m in tags.get("models", []):
            model_name = m.get("name", "")
            
            # Simple heuristic for capabilities based on model name
            capabilities: Set[Capability] = {Capability.GENERAL_CHAT, Capability.SUMMARISATION, Capability.EXTRACTION}
            
            if "coder" in model_name.lower():
                capabilities.add(Capability.CODING)
                capabilities.add(Capability.DEBUGGING)
                capabilities.add(Capability.ARCHITECTURE)
                
            if "deepseek-r1" in model_name.lower() or "reasoning" in model_name.lower():
                capabilities.add(Capability.REASONING)
                capabilities.add(Capability.DEEP_REASONING)
                capabilities.add(Capability.PLANNING)
                
            if "embed" in model_name.lower():
                capabilities = {Capability.EMBEDDING}
                
            models.append(AIModel(
                name=model_name,
                provider=self.name,
                context_window=8192,  # Default heuristic
                supports_tools=True,
                supports_json=True,
                supports_embeddings=("embed" in model_name.lower()),
                supports_vision=False,
                supports_streaming=True,
                capabilities=capabilities,
                health="healthy"
            ))
        return models

    def _convert_options(self, request: AIRequest) -> dict[str, Any]:
        opts: dict[str, Any] = {}
        if request.temperature is not None:
            opts["temperature"] = request.temperature
        if request.top_p is not None:
            opts["top_p"] = request.top_p
        if request.stop:
            opts["stop"] = request.stop
        if request.max_tokens:
            opts["num_predict"] = request.max_tokens
        return opts

    def _execute(self, request: AIRequest, endpoint: str) -> AIResponse:
        model_name = request.metadata.get("model_name")
        if not model_name:
            raise ValueError("model_name must be provided in metadata for OllamaProvider")
            
        options = self._convert_options(request)
        start_time = perf_counter()
        
        try:
            if endpoint == "chat":
                messages = request.messages
                if not messages:
                    # Construct message from prompt
                    messages = [{"role": "user", "content": request.prompt}]
                    if request.system_prompt:
                        messages.insert(0, {"role": "system", "content": request.system_prompt})
                resp = self._client.chat(model_name, messages, options)
                text = resp.get("message", {}).get("content", "")
            else:
                resp = self._client.generate(model_name, request.prompt, request.system_prompt, options)
                text = resp.get("response", "")
        except Exception as e:
            raise ProviderUnavailableError(f"Ollama request failed: {e}") from e

        duration = perf_counter() - start_time
        
        return AIResponse(
            text=text,
            provider=self.name,
            model=model_name,
            capability=request.capability,
            finish_reason=resp.get("done_reason", "unknown"),
            duration=duration,
            prompt_tokens=resp.get("prompt_eval_count", 0),
            completion_tokens=resp.get("eval_count", 0),
            total_tokens=resp.get("prompt_eval_count", 0) + resp.get("eval_count", 0)
        )

    def chat(self, request: AIRequest) -> AIResponse:
        return self._execute(request, "chat")
        
    def generate(self, request: AIRequest) -> AIResponse:
        return self._execute(request, "generate")
        
    def analyse(self, request: AIRequest) -> AIResponse:
        return self._execute(request, "generate")
        
    def summarise(self, request: AIRequest) -> AIResponse:
        return self._execute(request, "generate")
        
    def embed(self, request: AIRequest) -> AIResponse:
        model_name = request.metadata.get("model_name")
        if not model_name:
            raise ValueError("model_name must be provided in metadata for OllamaProvider")
        start_time = perf_counter()
        try:
            resp = self._client.embeddings(model_name, request.prompt)
        except Exception as e:
            raise ProviderUnavailableError(f"Ollama embeddings failed: {e}") from e

        duration = perf_counter() - start_time
        return AIResponse(
            text="[EMBEDDINGS_RETURNED_IN_METADATA]",
            provider=self.name,
            model=model_name,
            capability=request.capability,
            finish_reason="done",
            duration=duration,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            metadata={"embeddings": resp.get("embedding", [])}
        )
