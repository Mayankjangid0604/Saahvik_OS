import pytest
from unittest.mock import MagicMock

from enterprise_os.providers.ai.ollama_provider import OllamaProvider
from enterprise_os.providers.ai.request import AIRequest
from enterprise_os.providers.ai.capability import Capability

def test_ollama_provider_discovery():
    mock_client = MagicMock()
    mock_client.list_models.return_value = {
        "models": [
            {"name": "llama3.1"},
            {"name": "qwen2.5-coder"},
            {"name": "deepseek-r1"}
        ]
    }
    
    provider = OllamaProvider(mock_client)
    models = provider.discover_models()
    
    assert len(models) == 3
    model_names = {m.name for m in models}
    assert "llama3.1" in model_names
    assert "qwen2.5-coder" in model_names
    assert "deepseek-r1" in model_names
    
    # Check heuristics
    coder = next(m for m in models if m.name == "qwen2.5-coder")
    assert Capability.CODING in coder.capabilities
    
    deepseek = next(m for m in models if m.name == "deepseek-r1")
    assert Capability.REASONING in deepseek.capabilities

def test_ollama_provider_execute():
    mock_client = MagicMock()
    mock_client.chat.return_value = {
        "message": {"content": "Hello world!"},
        "done_reason": "stop",
        "prompt_eval_count": 10,
        "eval_count": 5
    }
    
    provider = OllamaProvider(mock_client)
    
    req = AIRequest(
        prompt="Say hello",
        capability=Capability.GENERAL_CHAT,
        metadata={"model_name": "llama3.1"}
    )
    
    resp = provider.chat(req)
    
    assert resp.text == "Hello world!"
    assert resp.provider == "ollama"
    assert resp.model == "llama3.1"
    assert resp.total_tokens == 15
    mock_client.chat.assert_called_once()
