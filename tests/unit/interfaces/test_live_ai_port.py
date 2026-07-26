from enterprise_os.interfaces.api.ceo_api import LiveAIPort
from enterprise_os.providers.ai.capability import Capability
from enterprise_os.providers.ai.execution_plan import AIExecutionPlan
from enterprise_os.providers.ai.exceptions import RoutingError, ProviderUnavailableError
from enterprise_os.providers.ai.response import AIResponse
from enterprise_os.providers.ai.request import AIRequest


class StubRouter:
    def __init__(self, plan=None, error=None):
        self._plan = plan
        self._error = error

    def route(self, capability):
        if self._error:
            raise self._error
        return self._plan


class StubProvider:
    def __init__(self, response=None, error=None):
        self.name = "stub"
        self._response = response
        self._error = error
        self.last_request = None

    def generate(self, request: AIRequest) -> AIResponse:
        self.last_request = request
        if self._error:
            raise self._error
        return self._response


class StubRegistry:
    def __init__(self, providers: dict):
        self._providers = providers

    def get_provider(self, name):
        return self._providers.get(name)


def test_routes_through_the_real_router_and_provider():
    plan = AIExecutionPlan(provider_name="stub", model_name="stub-model", temperature=0.3, json_mode=True, max_tokens=512)
    expected = AIResponse(text="real response", provider="stub", model="stub-model", capability=Capability.PLANNING, finish_reason="stop", duration=0.1, prompt_tokens=1, completion_tokens=1, total_tokens=2)
    provider = StubProvider(response=expected)
    port = LiveAIPort(router=StubRouter(plan=plan), registry=StubRegistry({"stub": provider}))

    result = port.request_capability(Capability.PLANNING, "do the thing", system_prompt="sys")

    assert result is expected
    assert provider.last_request.prompt == "do the thing"
    assert provider.last_request.system_prompt == "sys"
    assert provider.last_request.metadata["model_name"] == "stub-model"
    assert provider.last_request.temperature == 0.3
    assert provider.last_request.json_mode is True
    assert provider.last_request.max_tokens == 512


def test_degrades_gracefully_when_routing_fails():
    port = LiveAIPort(router=StubRouter(error=RoutingError("no healthy model")), registry=StubRegistry({}))

    result = port.request_capability(Capability.PLANNING, "prompt")

    assert result.finish_reason == "error"
    assert result.text.startswith("AI_PROVIDER_ERROR:")


def test_degrades_gracefully_when_no_provider_registered_for_the_plan():
    plan = AIExecutionPlan(provider_name="missing-provider", model_name="m")
    port = LiveAIPort(router=StubRouter(plan=plan), registry=StubRegistry({}))

    result = port.request_capability(Capability.TOOL_SELECTION, "prompt")

    assert result.finish_reason == "error"
    assert "missing-provider" in result.text


def test_degrades_gracefully_when_the_provider_call_itself_fails():
    plan = AIExecutionPlan(provider_name="stub", model_name="stub-model")
    provider = StubProvider(error=ProviderUnavailableError("ollama is offline"))
    port = LiveAIPort(router=StubRouter(plan=plan), registry=StubRegistry({"stub": provider}))

    result = port.request_capability(Capability.REFLECTION, "prompt")

    assert result.finish_reason == "error"
    assert "ollama is offline" in result.text


def test_full_goal_execution_degrades_gracefully_with_no_ai_backend_available():
    """End-to-end regression test for the exact scenario this codebase's own
    CI/dev environment is actually in: no Ollama server running, so
    ModelRegistry has zero models and every AIRouter.route() call raises
    RoutingError. Before P1-4, LiveAIPort ignored the router/registry
    entirely and always returned scripted text, so this path was never
    exercised for real. Confirms the whole ReasoningLoop resolves to a
    well-formed SEEK_APPROVAL instead of raising an unhandled exception when
    the AI backend is unavailable."""
    from enterprise_os.runtime.reasoning_loop import ReasoningLoop
    from enterprise_os.runtime.executive_session import ExecutiveSession
    from enterprise_os.runtime.executive_state import ExecutiveState
    from enterprise_os.runtime.goal import Goal
    from enterprise_os.runtime.events import EventDispatcher
    from enterprise_os.runtime.decision import DecisionOutcome
    from enterprise_os.governance.approval_engine import ApprovalEngine
    from enterprise_os.providers.ai.router import AIRouter
    from enterprise_os.providers.ai.registry import ModelRegistry
    from enterprise_os.providers.ai.config import AIConfig

    class NoOpToolPort:
        def execute_tool(self, capability, arguments=None):
            raise AssertionError("no tool should be invoked when planning already failed")

    empty_registry = ModelRegistry()  # no models registered -- simulates no Ollama server
    router = AIRouter(empty_registry, AIConfig())
    ai_port = LiveAIPort(router=router, registry=empty_registry)
    dispatcher = EventDispatcher()
    approval_engine = ApprovalEngine(dispatcher)

    class InMemorySessionRepo:
        def save(self, session):
            pass
        def load(self, session_id):
            raise NotImplementedError

    loop = ReasoningLoop(ai_port, NoOpToolPort(), dispatcher, InMemorySessionRepo(), approval_engine=approval_engine)
    session = ExecutiveSession()
    goal = Goal(id="g-no-backend", description="Build something", success_criteria="done")

    decision = loop.execute_goal(session, goal)

    assert decision.outcome == DecisionOutcome.SEEK_APPROVAL
    assert session.context.state == ExecutiveState.EVALUATING
    assert len(approval_engine.get_pending_approvals()) == 1
