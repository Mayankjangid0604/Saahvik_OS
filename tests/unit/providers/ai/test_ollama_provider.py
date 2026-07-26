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

def test_ollama_provider_embed_requires_model_name():
    """Regression test: embed() read request.metadata.get("model_name") but,
    unlike _execute() (used by chat/generate/analyse/summarise), never
    validated it was actually present before passing it on to
    OllamaClient.embeddings() -- found via mypy (`Any | None` where `str` was
    expected). A missing model_name would previously fail deep inside the
    HTTP client with a confusing error instead of a clear one."""
    mock_client = MagicMock()
    provider = OllamaProvider(mock_client)

    req = AIRequest(prompt="embed this", capability=Capability.EMBEDDING, metadata={})

    with pytest.raises(ValueError, match="model_name"):
        provider.embed(req)

    mock_client.embeddings.assert_not_called()

def test_ollama_provider_embed_with_model_name():
    mock_client = MagicMock()
    mock_client.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
    provider = OllamaProvider(mock_client)

    req = AIRequest(prompt="embed this", capability=Capability.EMBEDDING, metadata={"model_name": "nomic-embed-text"})

    resp = provider.embed(req)

    assert resp.metadata["embeddings"] == [0.1, 0.2, 0.3]
    mock_client.embeddings.assert_called_once_with("nomic-embed-text", "embed this")
