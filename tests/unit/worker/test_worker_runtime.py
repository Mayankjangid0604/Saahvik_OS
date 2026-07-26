import pytest
from enterprise_os.worker.worker_models import WorkItem
from enterprise_os.worker.worker_session import WorkerSession
from enterprise_os.worker.worker_loop import WorkerLoop
from enterprise_os.providers.tools.response import ToolResponse
from enterprise_os.providers.tools.capability import ToolCapability
from enterprise_os.providers.ai.response import AIResponse

class MockToolPort:
    def execute_tool(self, capability, arguments=None):
        if capability == ToolCapability.FILE_READ:
            return ToolResponse(success=True, result="good", execution_time=0.1)
        return ToolResponse(success=False, error_message="failed", execution_time=0.1, result="")

class MockAIPort:
    def __init__(self, json_resp):
        self.json_resp = json_resp
    def request_capability(self, capability, prompt, system_prompt="", kwargs=None):
        return AIResponse(text=self.json_resp, provider="mock", model="mock", capability=capability, finish_reason="stop", duration=0.1, prompt_tokens=1, completion_tokens=1, total_tokens=2)

def test_worker_loop_success():
    port = MockToolPort()
    ai = MockAIPort('{"capability": "FILE_READ", "arguments": {}}')
    loop = WorkerLoop(ai, port)
    session = WorkerSession(objective="Do work")
    wi = WorkItem(id="wi1", objective="Do work", allowed_tools=[ToolCapability.FILE_READ], parameters={})

    result = loop.execute_work_item(session, wi)

    assert result.success is True
    assert result.findings == "good"
    assert result.work_item_id == "wi1"

def test_worker_loop_unauthorized_tool():
    port = MockToolPort()
    ai = MockAIPort('{"capability": "SHELL_EXECUTE", "arguments": {}}')
    loop = WorkerLoop(ai, port)
    session = WorkerSession(objective="Do work")
    wi = WorkItem(id="wi2", objective="Do work", allowed_tools=[ToolCapability.FILE_READ], parameters={})

    result = loop.execute_work_item(session, wi)

    assert result.success is False
    assert "not in allowed capabilities" in result.findings
