# Architecture

EnterpriseOS is a "Digital CEO" runtime: a long-running reasoning loop that takes a `Goal`,
plans it, delegates execution to a worker loop backed by governed tools, and produces a
`Decision` — either `PROCEED` or `SEEK_APPROVAL`, with the latter queued as a real,
resolvable item for the human owner. It follows hexagonal (ports-and-adapters) architecture
fairly strictly in the layers that matter for that loop; see [`CURRENT_STATE.md`](CURRENT_STATE.md)
for a full, evidence-based audit of what's actually implemented versus stubbed.

## Layers

```
src/enterprise_os/
├── domain/          Plain business logic and data, no I/O. 13 subpackages: ceo, cognition,
│                     approvals, employees, departments, projects, workflows, memory, owner,
│                     shared, plus 8 "milestone" domains (strategy, operations, organisation,
│                     research, knowledge, optimisation, growth, evolution).
├── application/      Orchestration behind ports.
│   ├── ports/          Protocol/ABC interfaces domain and infrastructure code depend on.
│   ├── services/        Orchestrators for the 8 milestone domains.
│   └── use_cases/       e.g. BootCEO.
├── governance/       PolicyEngine (gates tool execution) + ApprovalEngine (human-in-the-loop
│                     approval queue). See GOVERNANCE.md.
├── providers/        Concrete adapters.
│   ├── ai/              Capability enum, ModelRegistry, AIRouter, OllamaProvider/Client.
│   └── tools/            ToolCapability enum, ToolRegistry (auto-discovery), ToolRouter,
│                          Filesystem/Shell/Python/Git/Browser implementations.
├── runtime/          ExecutiveSession/Context/State, ReasoningLoop, Goal/Plan/Step/Decision,
│                     EventDispatcher, FileSessionRepository/FileAuditLog.
├── worker/           WorkerLoop, WorkerSession, WorkItem/StructuredResult — translates a
│                     Step into a concrete tool invocation.
├── infrastructure/   Persistence/event-store plumbing, AI config, FileDocumentLoader.
├── interfaces/
│   ├── api/             FastAPI app (ceo_api.py) + WebSocket event streaming.
│   ├── cli/, events/, web/  CLI entrypoint hooks, event interface glue, static dashboard.
└── bootstrap/        Application startup wiring (ceo_bootstrap.py).
```

## The core loop

`ReasoningLoop.execute_goal(session, goal)` (see [RUNTIME.md](RUNTIME.md) for the full state
machine) is the spine of the system:

```
Goal → PLANNING (AI: Capability.PLANNING) → Plan{Step, Step, ...}
  → for each step: EXECUTING → WorkerLoop.execute_work_item() → REFLECTING → (RESEARCHING)
  → DECIDING: any step FAILED? → SEEK_APPROVAL (queued in ApprovalEngine) : PROCEED
  → EVALUATING (AI: Capability.REFLECTION) → SessionFinished
```

Every transition dispatches an event through `EventDispatcher`, consumed by `FileAuditLog`
(persistent audit trail) and `EventStreamer` (WebSocket push to the dashboard).

## The load-bearing design decision: capability enums, not strings

Every tool and AI call in this codebase is identified by an enum, not a string:
`ToolCapability` (`FILE_READ`, `SHELL_EXECUTE`, ...) for tools, `Capability` (`PLANNING`,
`TOOL_SELECTION`, `REFLECTION`, ...) for AI requests. The call chain is:

```
ReasoningLoop/WorkerLoop
  → ToolPort.execute_tool(capability: ToolCapability, arguments)
    → ToolRouter.route(capability) → provider whose .capabilities contains it
      → ToolRequest(tool_name=capability.name, arguments) → Provider.execute(request)
```

Providers self-register their supported capabilities (`@property capabilities`) and are
discovered automatically by `ToolRegistry.auto_discover()`, which reflects over
`providers/tools/implementations/` and instantiates any class exposing
`name`/`capabilities`/`execute`. The AI side mirrors this with `AIRouter.route(capability)`
returning an `AIExecutionPlan` (provider + model + policy), resolved against `ModelRegistry`.

This enum-based contract is used consistently everywhere in production code. The one time
it was violated was in tests written before the migration to it — fixed in v1.0 (see
`V1_RELEASE_PLAN.md` P0-1).

## Governance is a gate, not an afterthought

Tool execution doesn't go straight from `WorkerLoop` to a `Provider` — it's wrapped in
`PolicyEnforcedToolPort`, which runs every request through `PolicyEngine` (workspace
confinement + command restriction policies) before the real port ever executes it. A step
failure surfaces as a `Decision(SEEK_APPROVAL)`, which — as of v1.0 — is actually queued in
`ApprovalEngine` and exposed via `GET/POST /approvals`, not just logged. See
[GOVERNANCE.md](GOVERNANCE.md).

## No dependency injection container

Wiring is procedural, not framework-managed: `ceo_api.py` constructs every concrete object
(registries, routers, policies, the reasoning loop) at module import time and passes them
down by hand. This is a deliberate, simple choice appropriate to the project's current size
— introducing a DI container would be exactly the kind of unnecessary abstraction this
project's v1.0 hardening pass avoided adding. If the object graph grows significantly more
complex, that tradeoff is worth revisiting, but it isn't a problem today.

## What's genuinely complete vs. still scaffolding

See [`CURRENT_STATE.md`](CURRENT_STATE.md) §10 for the full breakdown. In short: the
Executive/Worker/Tool/Governance loop described above is real and tested end-to-end. The
eight "milestone" cognitive domains under `domain/`/`application/` each have an orchestrator
and passing tests but are not wired into the `ReasoningLoop`'s actual execution path — they
represent a broader design surface than what the runtime currently exercises.
