import pytest
from enterprise_os.runtime.executive_session import ExecutiveSession
from enterprise_os.runtime.executive_state import ExecutiveState
from enterprise_os.runtime.goal import Goal
from enterprise_os.runtime.decision import DecisionOutcome
from enterprise_os.runtime.reasoning_loop import ReasoningLoop
from enterprise_os.runtime.events import EventDispatcher
from enterprise_os.runtime.persistence import SessionRepository
from enterprise_os.providers.ai.response import AIResponse
from enterprise_os.providers.tools.response import ToolResponse

class MockAIPort:
    def request_capability(self, capability, prompt, system_prompt="", kwargs=None):
        if "PLANNING" in str(capability):
            text = '{"steps": [{"id": "1", "description": "Step 1"}]}'
        elif "TOOL_SELECTION" in str(capability):
            text = '{"capability": "PYTHON_EXECUTE", "arguments": {}}'
        else:
            text = "mock"
        return AIResponse(text=text, provider="mock", model="mock", capability=capability, finish_reason="stop", duration=0.1, prompt_tokens=1, completion_tokens=1, total_tokens=2)

class MockToolPort:
    def execute_tool(self, tool_name, arguments=None):
        return ToolResponse(success=True, result="mock_result", execution_time=0.1)

class MockSessionRepo(SessionRepository):
    def save(self, session: ExecutiveSession) -> None:
        pass
    def load(self, session_id: str) -> ExecutiveSession:
        return ExecutiveSession(id=session_id)

def test_executive_session_initialization():
    session = ExecutiveSession()
    assert session.context.state == ExecutiveState.IDLE
    assert session.context.session_id == session.id

def test_reasoning_loop_execution():
    ai = MockAIPort()
    tools = MockToolPort()
    dispatcher = EventDispatcher()
    repo = MockSessionRepo()
    loop = ReasoningLoop(ai, tools, dispatcher, repo)
    
    session = ExecutiveSession()
    goal = Goal("g1", "Do something", "Done")
    
    decision = loop.execute_goal(session, goal)
    
    assert decision.outcome == DecisionOutcome.PROCEED
    assert session.context.state == ExecutiveState.EVALUATING
