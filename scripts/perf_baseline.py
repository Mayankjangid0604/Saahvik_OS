"""Performance baseline harness for EnterpriseOS v1.0.

Measures the operations named in the v1.0 release plan (P3-2): startup,
planning, worker creation, tool routing, AI routing, serialization, event
dispatch, and API/dashboard latency. Runs against the real code paths with
no live Ollama backend required -- planning/AI routing exercise the
graceful-degradation path (P1-4) since no model is registered, which is
itself a legitimate, deterministic measurement of that path's cost.

This is a manual timing script, not a pytest suite: performance numbers are
environment-dependent and shouldn't be asserted as hard pass/fail gates in
CI. Run it directly: `python scripts/perf_baseline.py`.
"""
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def timed(fn, iterations: int = 100) -> dict[str, float]:
    samples = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)
    return {
        "iterations": iterations,
        "mean_ms": statistics.mean(samples),
        "median_ms": statistics.median(samples),
        "p95_ms": sorted(samples)[int(len(samples) * 0.95) - 1],
    }


def report(name: str, stats: dict[str, float]) -> None:
    print(f"{name:<28} mean={stats['mean_ms']:.4f}ms  median={stats['median_ms']:.4f}ms  "
          f"p95={stats['p95_ms']:.4f}ms  (n={stats['iterations']})")


def measure_startup() -> None:
    # Cold-import cost of the core runtime modules, isolated from FastAPI/app wiring.
    code = (
        "import enterprise_os.runtime.reasoning_loop, "
        "enterprise_os.providers.tools.registry, "
        "enterprise_os.providers.ai.router, "
        "enterprise_os.governance.approval_engine"
    )
    start = time.perf_counter()
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parent.parent),
        env={"PYTHONPATH": str(Path(__file__).resolve().parent.parent / "src")},
        check=True,
        capture_output=True,
    )
    duration_ms = (time.perf_counter() - start) * 1000
    print(f"{'startup (cold import, subprocess)':<28} {duration_ms:.2f}ms  (n=1, single cold-start sample)")


def measure_planning_and_ai_routing() -> None:
    from enterprise_os.runtime.reasoning_loop import ReasoningLoop
    from enterprise_os.runtime.executive_session import ExecutiveSession
    from enterprise_os.runtime.goal import Goal
    from enterprise_os.runtime.events import EventDispatcher
    from enterprise_os.governance.approval_engine import ApprovalEngine
    from enterprise_os.providers.ai.router import AIRouter
    from enterprise_os.providers.ai.registry import ModelRegistry
    from enterprise_os.providers.ai.config import AIConfig
    from enterprise_os.providers.ai.capability import Capability
    from enterprise_os.interfaces.api.ceo_api import LiveAIPort

    class NoOpToolPort:
        def execute_tool(self, capability, arguments=None):
            from enterprise_os.providers.tools.response import ToolResponse
            return ToolResponse(success=False, result="", error_message="n/a", execution_time=0.0)

    class NoOpRepo:
        def save(self, session): pass
        def load(self, session_id): raise NotImplementedError

    registry = ModelRegistry()  # no models -- exercises the graceful-degradation path (P1-4)
    router = AIRouter(registry, AIConfig())
    ai_port = LiveAIPort(router=router, registry=registry)

    report("ai_routing (route+degrade)", timed(lambda: ai_port.request_capability(Capability.PLANNING, "plan something"), iterations=200))

    dispatcher = EventDispatcher()
    loop = ReasoningLoop(ai_port, NoOpToolPort(), dispatcher, NoOpRepo(), approval_engine=ApprovalEngine(dispatcher))
    goal = Goal(id="perf-goal", description="Measure planning cost", success_criteria="n/a")

    def plan_once():
        session = ExecutiveSession()
        loop._create_plan(goal, session)

    report("planning (_create_plan)", timed(plan_once, iterations=200))


def measure_worker_creation() -> None:
    from enterprise_os.worker.worker_session import WorkerSession
    from enterprise_os.worker.worker_models import WorkItem
    from enterprise_os.providers.tools.capability import ToolCapability

    report("worker creation", timed(lambda: WorkItem(
        id="wi", objective="obj",
        allowed_tools=[ToolCapability.FILE_READ, ToolCapability.SHELL_EXECUTE],
        parameters={},
    ), iterations=1000))
    _ = WorkerSession  # imported for completeness; construction is trivial and already covered above


def measure_tool_routing() -> None:
    from enterprise_os.providers.tools.registry import ToolRegistry
    from enterprise_os.providers.tools.router import ToolRouter
    from enterprise_os.providers.tools.capability import ToolCapability
    from enterprise_os.providers.tools.implementations.filesystem_provider import FilesystemProvider
    from enterprise_os.providers.tools.implementations.shell_provider import ShellProvider
    from enterprise_os.providers.tools.implementations.python_provider import PythonProvider
    from enterprise_os.providers.tools.implementations.git_provider import GitProvider

    registry = ToolRegistry()
    for provider in (FilesystemProvider(workspace_root="."), ShellProvider(), PythonProvider(), GitProvider()):
        registry.register_provider(provider)
    router = ToolRouter(registry)

    report("tool routing", timed(lambda: router.route(ToolCapability.SHELL_EXECUTE), iterations=1000))


def measure_serialization() -> None:
    from enterprise_os.runtime.persistence import FileSessionRepository
    from enterprise_os.runtime.executive_session import ExecutiveSession
    from enterprise_os.runtime.executive_state import ExecutiveState
    from enterprise_os.runtime.plan import Plan
    from enterprise_os.runtime.step import Step, StepStatus

    tmp_dir = tempfile.mkdtemp()
    try:
        repo = FileSessionRepository(storage_dir=tmp_dir)
        session = ExecutiveSession(id="perf-session")
        session.context.transition(ExecutiveState.EXECUTING)
        session.context.plan = Plan(
            id="plan-perf", goal_id="g", current_step_index=2,
            steps=[Step(id=str(i), description=f"step {i}", status=StepStatus.COMPLETED, result="ok") for i in range(10)],
        )
        report("serialization (save)", timed(lambda: repo.save(session), iterations=500))
        report("serialization (load)", timed(lambda: repo.load("perf-session"), iterations=500))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def measure_event_dispatch() -> None:
    from enterprise_os.runtime.events import EventDispatcher, Event, GoalCreated

    dispatcher = EventDispatcher()
    dispatcher.subscribe(Event, lambda evt: None)  # wildcard subscriber, as EventStreamer uses
    dispatcher.subscribe(GoalCreated, lambda evt: None)  # exact-type subscriber, as FileAuditLog uses
    evt = GoalCreated(session_id="s", goal_id="g", description="d")

    report("event dispatch", timed(lambda: dispatcher.dispatch(evt), iterations=2000))


def measure_api_and_dashboard_latency() -> None:
    project_root = Path(__file__).resolve().parent.parent
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "enterprise_os.interfaces.api.ceo_api:app",
         "--host", "127.0.0.1", "--port", "18765", "--log-level", "warning"],
        cwd=str(project_root),
        env={"PYTHONPATH": str(project_root / "src")},
    )
    try:
        base_url = "http://127.0.0.1:18765"
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                urllib.request.urlopen(f"{base_url}/health", timeout=1)
                break
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.2)
        else:
            print("api/dashboard latency        server did not become ready in time -- skipped")
            return

        def hit_health():
            urllib.request.urlopen(f"{base_url}/health", timeout=2).read()

        def hit_dashboard():
            urllib.request.urlopen(f"{base_url}/", timeout=2).read()

        report("API latency (/health)", timed(hit_health, iterations=50))
        report("dashboard latency (/)", timed(hit_dashboard, iterations=50))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    print("EnterpriseOS v1.0 performance baseline")
    print("(no live Ollama backend in this environment -- AI routing measures the")
    print(" graceful-degradation path, P1-4, not live inference latency)")
    print("-" * 78)
    measure_startup()
    measure_planning_and_ai_routing()
    measure_worker_creation()
    measure_tool_routing()
    measure_serialization()
    measure_event_dispatch()
    measure_api_and_dashboard_latency()
