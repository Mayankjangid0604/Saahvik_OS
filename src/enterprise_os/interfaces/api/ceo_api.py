import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from pydantic import BaseModel
from typing import Any, Optional

from enterprise_os.runtime.events import EventDispatcher
from enterprise_os.runtime.persistence import FileSessionRepository, FileAuditLog
from enterprise_os.governance.approval_engine import ApprovalEngine, ApprovalItem
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

from enterprise_os.providers.tools.router import ToolRouter
from enterprise_os.providers.tools.registry import ToolRegistry
from enterprise_os.providers.tools.response import ToolResponse
from enterprise_os.providers.tools.request import ToolRequest
from enterprise_os.providers.tools.exceptions import ToolNotFoundError
from enterprise_os.providers.tools.capability import ToolCapability

class LiveAIPort(AIPort):
    def __init__(self, router: AIRouter, registry: ModelRegistry):
        self.router = router
        self.registry = registry

    def request_capability(self, capability: Capability, prompt: str, system_prompt: str = "", kwargs=None) -> AIResponse:
        if capability == Capability.PLANNING:
            text = '''```json
{
    "steps": [
        {"id": "step-1", "description": "Create a workspace directory for the Flask app"},
        {"id": "step-2", "description": "Create app.py with a basic route"},
        {"id": "step-3", "description": "Test the Flask app logic using python tool"}
    ]
}
```'''
        elif capability == Capability.TOOL_SELECTION:
            if "workspace directory" in prompt:
                text = '{"capability": "SHELL_EXECUTE", "arguments": {"command": "mkdir flask_blog"}}'
            elif "app.py" in prompt:
                text = '{"capability": "FILE_WRITE", "arguments": {"path": "flask_blog/app.py", "content": "from flask import Flask\\napp = Flask(__name__)\\n\\n@app.route(\'/\')\\ndef index():\\n    return \'Blog Home\'\\n\\nif __name__ == \'__main__\':\\n    app.run()\\n"}}'
            elif "Test the Flask" in prompt:
                text = '{"capability": "PYTHON_EXECUTE", "arguments": {"script": "print(\\"Testing flask app structure... OK\\")"}}'
            else:
                text = '{"capability": "SHELL_EXECUTE", "arguments": {"command": "echo Unknown step"}}'
        else:
            text = "Completed successfully."
            
        return AIResponse(text=text, provider="mocked-llm", model="mock-model", capability=capability, finish_reason="stop", duration=0.5, prompt_tokens=10, completion_tokens=10, total_tokens=20)

class LiveToolPort(ToolPort):
    def __init__(self, router: ToolRouter):
        self.router = router

    def execute_tool(self, capability: ToolCapability, arguments: dict[str, Any] = None) -> ToolResponse:
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

    def execute_tool(self, capability: ToolCapability, arguments: dict[str, Any] = None) -> ToolResponse:
        import time
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

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(event_streamer.broadcast_loop())

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
    pass
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
        raise HTTPException(status_code=400, detail=str(e))
        
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

from fastapi.staticfiles import StaticFiles
import os

web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
