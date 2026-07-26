import logging
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from pydantic import BaseModel
from typing import Any, Optional

from enterprise_os.runtime.events import EventDispatcher
from enterprise_os.runtime.persistence import FileSessionRepository, FileAuditLog
from enterprise_os.governance.approval_engine import ApprovalEngine
from enterprise_os.runtime.reasoning_loop import ReasoningLoop
from enterprise_os.runtime.executive_session import ExecutiveSession
from enterprise_os.runtime.goal import Goal

from enterprise_os.application.ports.ai_port import AIPort
from enterprise_os.application.ports.tool_port import ToolPort
from enterprise_os.providers.ai.capability import Capability
from enterprise_os.providers.ai.response import AIResponse
from enterprise_os.providers.ai.request import AIRequest
from enterprise_os.providers.ai.router import AIRouter
from enterprise_os.providers.ai.registry import ModelRegistry
from enterprise_os.providers.ai.config import AIConfig
from enterprise_os.providers.ai.ollama_provider import OllamaProvider
from enterprise_os.providers.ai.ollama_client import OllamaClient
from enterprise_os.providers.ai.exceptions import AIPlatformError, ProviderUnavailableError

from enterprise_os.providers.tools.router import ToolRouter
from enterprise_os.providers.tools.registry import ToolRegistry
from enterprise_os.providers.tools.response import ToolResponse
from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.exceptions import ToolNotFoundError
from enterprise_os.providers.tools.capability import ToolCapability

logger = logging.getLogger(__name__)

class LiveAIPort(AIPort):
    """Routes capability requests through the real AIRouter/ModelRegistry to
    whichever provider (e.g. OllamaProvider) is actually registered and
    healthy for that capability.

    If routing fails (no suitable/healthy model, e.g. no Ollama server
    running or no models pulled yet) or the provider call itself fails, this
    returns an AIResponse carrying an error marker instead of raising --
    ReasoningLoop/WorkerLoop already treat unparseable AI output as a graceful
    step/plan failure that surfaces via SEEK_APPROVAL (see reasoning_loop.py),
    so a down AI backend degrades the same way rather than crashing the
    reasoning loop with an unhandled exception.
    """

    def __init__(self, router: AIRouter, registry: ModelRegistry):
        self.router = router
        self.registry = registry

    def request_capability(self, capability: Capability, prompt: str, system_prompt: str = "", kwargs=None) -> AIResponse:
        try:
            plan = self.router.route(capability)
            provider = self.registry.get_provider(plan.provider_name)
            if provider is None:
                raise ProviderUnavailableError(f"No AI provider registered for '{plan.provider_name}'")

            request = AIRequest(
                prompt=prompt,
                system_prompt=system_prompt,
                capability=capability,
                temperature=plan.temperature,
                max_tokens=plan.max_tokens,
                json_mode=plan.json_mode,
                metadata={"model_name": plan.model_name},
            )
            return provider.generate(request)
        except AIPlatformError as e:
            return AIResponse(
                text=f"AI_PROVIDER_ERROR: {e}",
                provider="none",
                model="none",
                capability=capability,
                finish_reason="error",
                duration=0.0,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            )

class LiveToolPort(ToolPort):
    def __init__(self, router: ToolRouter):
        self.router = router

    def execute_tool(self, capability: ToolCapability, arguments: Optional[dict[str, Any]] = None) -> ToolResponse:
        try:
            provider = self.router.route(capability)
            req = ToolRequest(tool_name=capability.name, arguments=arguments or {})
            return provider.execute(req)
        except ToolNotFoundError as e:
            return ToolResponse(success=False, result="", error_message=str(e), execution_time=0.0)

from enterprise_os.governance.policy_engine import PolicyEngine
from enterprise_os.governance.policies.workspace_confinement import WorkspaceConfinementPolicy
from enterprise_os.governance.policies.command_restriction import CommandRestrictionPolicy

class PolicyEnforcedToolPort(ToolPort):
    def __init__(self, base_port: ToolPort, policy_engine: PolicyEngine):
        self.base = base_port
        self.engine = policy_engine

    def execute_tool(self, capability: ToolCapability, arguments: Optional[dict[str, Any]] = None) -> ToolResponse:
        req = ToolRequest(tool_name=capability.name, arguments=arguments or {})
        approved, reason = self.engine.evaluate(req)
        if not approved:
            return ToolResponse(success=False, result="", error_message=reason, execution_time=0.0)
        return self.base.execute_tool(capability, arguments)

app = FastAPI(title="EnterpriseOS API", version="1.0.0")

from enterprise_os.interfaces.api.websocket import EventStreamer
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

# Infrastructure
dispatcher = EventDispatcher()
session_repo = FileSessionRepository()
audit_log = FileAuditLog()
from enterprise_os.runtime.events import GoalCreated, PlanGenerated, StepCompleted, StepFailed, StateTransitioned, DecisionMade, EvaluationCompleted, SessionFinished
from enterprise_os.governance.approval_engine import ApprovalRequested, ApprovalGranted, ApprovalRejected
approval_engine = ApprovalEngine(dispatcher)
audit_log.bind_to(dispatcher, [
    GoalCreated, PlanGenerated, StepCompleted, StepFailed, StateTransitioned,
    DecisionMade, EvaluationCompleted, SessionFinished,
    ApprovalRequested, ApprovalGranted, ApprovalRejected,
])

event_streamer = EventStreamer(dispatcher)
_broadcast_task: Optional[asyncio.Task] = None

@app.on_event("startup")
async def startup_event():
    global _broadcast_task
    # A reference must be kept to the task returned by create_task(), or it
    # can be garbage-collected mid-execution (a documented asyncio gotcha) --
    # silently killing the WebSocket dashboard's event stream with no error.
    _broadcast_task = asyncio.create_task(event_streamer.broadcast_loop())

@app.websocket("/ceo/events/ws")
async def websocket_endpoint(websocket: WebSocket):
    await event_streamer.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_streamer.disconnect(websocket)


# Tool Platform
tool_registry = ToolRegistry()
tool_registry.auto_discover('enterprise_os.providers.tools.implementations', workspace_root=".")
tool_router = ToolRouter(tool_registry)
live_tool_port = LiveToolPort(tool_router)

policy_engine = PolicyEngine()
policy_engine.register_policy(WorkspaceConfinementPolicy(workspace_root="."))
policy_engine.register_policy(CommandRestrictionPolicy())
policy_port = PolicyEnforcedToolPort(live_tool_port, policy_engine)

# AI Platform
ai_registry = ModelRegistry()
ai_config = AIConfig()
# Only enable Qwen 2.5 Coder or similar for now in config, or let auto-discover happen
ollama = OllamaProvider(OllamaClient())
ai_registry.register_provider(ollama)
try:
    for model in ollama.discover_models():
        ai_registry.register_model(model)
except Exception:
    logger.warning("Ollama model discovery/registration failed at startup; continuing with no models registered.", exc_info=True)
ai_router = AIRouter(ai_registry, ai_config)
live_ai_port = LiveAIPort(ai_router, ai_registry)

reasoning_loop = ReasoningLoop(
    ai_port=live_ai_port,
    tool_port=policy_port,
    dispatcher=dispatcher,
    repository=session_repo,
    approval_engine=approval_engine,
)

class GoalRequest(BaseModel):
    id: str
    description: str

class ApprovalDecision(BaseModel):
    approved: bool
    feedback: str = ""

# Governance-sensitive endpoints (submitting goals, approving/rejecting pending
# governance decisions) require a bearer token when ENTERPRISE_OS_API_TOKEN is
# set. Unset is a deliberate, documented default for local single-owner use
# (see SECURITY.md) -- not a silent gap: set the env var to require auth.
API_TOKEN = os.environ.get("ENTERPRISE_OS_API_TOKEN")

async def require_api_token(authorization: Optional[str] = Header(default=None)) -> None:
    if API_TOKEN is None:
        return
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Missing or invalid API token.")

@app.post("/ceo/goal", dependencies=[Depends(require_api_token)])
async def submit_goal(request: GoalRequest, background_tasks: BackgroundTasks):
    goal = Goal(id=request.id, description=request.description, success_criteria="")
    session = ExecutiveSession()

    def run_loop():
        reasoning_loop.execute_goal(session, goal)

    background_tasks.add_task(run_loop)
    return {"message": "Goal accepted", "session_id": session.id}

@app.get("/approvals", dependencies=[Depends(require_api_token)])
async def get_approvals():
    pending = approval_engine.get_pending_approvals()
    return {"pending_approvals": pending}

@app.post("/approvals/{approval_id}", dependencies=[Depends(require_api_token)])
async def resolve_approval(approval_id: str, decision: ApprovalDecision):
    try:
        approval_engine.resolve_approval(approval_id, decision.approved, decision.feedback)
        return {"message": "Approval resolved"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
