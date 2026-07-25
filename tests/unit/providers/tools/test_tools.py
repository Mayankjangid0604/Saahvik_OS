import pytest
from enterprise_os.providers.tools.registry import ToolRegistry
from enterprise_os.providers.tools.router import ToolRouter
from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.response import ToolResponse
from enterprise_os.providers.tools.exceptions import ToolNotFoundError

class MockFilesystemProvider:
    @property
    def name(self) -> str:
        return "filesystem"
        
    def can_handle(self, tool_name: str) -> bool:
        return tool_name in ["read_file", "write_file"]
        
    def execute(self, request: ToolRequest) -> ToolResponse:
        return ToolResponse(success=True, result="content", execution_time=0.1)

class MockShellProvider:
    @property
    def name(self) -> str:
        return "shell"
        
    def can_handle(self, tool_name: str) -> bool:
        return tool_name == "execute_command"
        
    def execute(self, request: ToolRequest) -> ToolResponse:
        return ToolResponse(success=True, result="output", execution_time=0.5)

def test_tool_registry():
    registry = ToolRegistry()
    registry.register_provider(MockFilesystemProvider())
    registry.register_provider(MockShellProvider())
    
    assert len(registry.list_providers()) == 2
    assert registry.get_provider("filesystem") is not None
    assert registry.get_provider("shell") is not None
    assert registry.get_provider("unknown") is None
    
    registry.clear()
    assert len(registry.list_providers()) == 0

def test_tool_router():
    registry = ToolRegistry()
    registry.register_provider(MockFilesystemProvider())
    registry.register_provider(MockShellProvider())
    
    router = ToolRouter(registry)
    
    provider1 = router.route("read_file")
    assert provider1.name == "filesystem"
    
    provider2 = router.route("execute_command")
    assert provider2.name == "shell"
    
    with pytest.raises(ToolNotFoundError):
        router.route("send_email")
