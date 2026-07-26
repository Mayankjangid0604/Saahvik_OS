import pytest
from enterprise_os.runtime.executive_session import ExecutiveSession
from enterprise_os.runtime.executive_state import ExecutiveState
from enterprise_os.runtime.goal import Goal
from enterprise_os.runtime.decision import DecisionOutcome
from enterprise_os.runtime.reasoning_loop import ReasoningLoop
from enterprise_os.runtime.events import EventDispatcher
from enterprise_os.runtime.persistence import SessionRepository
from enterprise_os.governance.approval_engine import ApprovalEngine
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

def test_reasoning_loop_seeks_approval_on_step_failure():
    class FailingToolSelectionAIPort(MockAIPort):
        def request_capability(self, capability, prompt, system_prompt="", kwargs=None):
            if "TOOL_SELECTION" in str(capability):
                text = '{"capability": "GIT_EXECUTE", "arguments": {}}'  # not in allowed_tools -> step fails
                return AIResponse(text=text, provider="mock", model="mock", capability=capability, finish_reason="stop", duration=0.1, prompt_tokens=1, completion_tokens=1, total_tokens=2)
            return super().request_capability(capability, prompt, system_prompt, kwargs)

    ai = FailingToolSelectionAIPort()
    tools = MockToolPort()
    dispatcher = EventDispatcher()
    repo = MockSessionRepo()
    approval_engine = ApprovalEngine(dispatcher)
    loop = ReasoningLoop(ai, tools, dispatcher, repo, approval_engine=approval_engine)

    session = ExecutiveSession()
    goal = Goal("g2", "Do something that fails", "Done")

    decision = loop.execute_goal(session, goal)

    assert decision.outcome == DecisionOutcome.SEEK_APPROVAL
    pending = approval_engine.get_pending_approvals()
    assert len(pending) == 1
    assert session.context.memory["pending_approval_id"] == pending[0].id

def test_reasoning_loop_fails_loud_on_unparseable_plan():
    """Regression test for P1-3: an unparseable PLANNING response must not be
    silently substituted with a fake step that then actually executes -- it
    should fail immediately, without ever invoking a tool, and the goal should
    still resolve to a well-formed SEEK_APPROVAL decision."""

    class BadPlanningAIPort:
        def request_capability(self, capability, prompt, system_prompt="", kwargs=None):
            text = "this is not valid json"
            return AIResponse(text=text, provider="mock", model="mock", capability=capability, finish_reason="stop", duration=0.1, prompt_tokens=1, completion_tokens=1, total_tokens=2)

    class CountingToolPort:
        def __init__(self):
            self.calls = 0
        def execute_tool(self, tool_name, arguments=None):
            self.calls += 1
            return ToolResponse(success=True, result="mock_result", execution_time=0.1)

    ai = BadPlanningAIPort()
    tools = CountingToolPort()
    dispatcher = EventDispatcher()
    repo = MockSessionRepo()
    approval_engine = ApprovalEngine(dispatcher)
    loop = ReasoningLoop(ai, tools, dispatcher, repo, approval_engine=approval_engine)

    session = ExecutiveSession()
    goal = Goal("g3", "Do something unplannable", "Done")

    decision = loop.execute_goal(session, goal)

    assert decision.outcome == DecisionOutcome.SEEK_APPROVAL
    assert tools.calls == 0
    assert len(approval_engine.get_pending_approvals()) == 1
