import pytest
from enterprise_os.providers.tools.registry import ToolRegistry
import os

def test_auto_discovery():
    registry = ToolRegistry()
    registry.auto_discover('enterprise_os.providers.tools.implementations', workspace_root=".")
    
    assert registry.get_provider("shell") is not None
    assert registry.get_provider("filesystem") is not None
    assert registry.get_provider("python") is not None
    assert registry.get_provider("browser") is not None
    assert registry.get_provider("git") is not None
