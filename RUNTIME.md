# Runtime

The Executive Runtime lives in `src/enterprise_os/runtime/`. This document describes the
`ReasoningLoop` state machine, its supporting data model, and the events it emits — the
verified, current behavior, not an aspirational design.

## State machine

`ExecutiveState` (`runtime/executive_state.py`): `IDLE`, `PLANNING`, `RESEARCHING`,
`EXECUTING`, `REFLECTING`, `WAITING_FOR_APPROVAL`, `DECIDING`, `EVALUATING`.

`ReasoningLoop.execute_goal(session, goal) -> Decision` drives every transition:

1. **`GoalCreated`** dispatched, session saved.
2. **`PLANNING`** — `_create_plan()` prompts the AI (`Capability.PLANNING`) for a JSON
   `{"steps": [{"id", "description"}, ...]}` plan. If the response can't be parsed, the plan
   becomes a single step pre-marked `StepStatus.FAILED` (not a fake runnable placeholder —
   fixed in v1.0, see `V1_RELEASE_PLAN.md` P1-3) so it flows straight into the
   already-tested failure path below without wasting a tool invocation.
   `session.context.plan` is set immediately so persistence captures it from this point on.
3. For each `Step` in the plan:
   - **`EXECUTING`** — `_execute_step()` builds a `WorkItem` (fixed `allowed_tools`:
     `PYTHON_EXECUTE`, `SHELL_EXECUTE`, `FILE_READ`, `FILE_WRITE`, `FILE_LIST`) and hands it
     to `WorkerLoop.execute_work_item()`. A step already marked `FAILED` (from the parsing
     fallback above) short-circuits here — `StepFailed` is dispatched and no tool is called.
   - **`REFLECTING`** — `_reflect_on_step()` is currently just `step.status ==
     StepStatus.COMPLETED`; not a real self-evaluation.
   - **`RESEARCHING`** (only if reflection says "not confident") — `_research()` is
     currently a no-op `pass`.
4. **`DECIDING`** — if any step is `FAILED`, `Decision(SEEK_APPROVAL, ...)` and
   `ApprovalEngine.request_approval(...)` is called, storing the resulting `approval_id` in
   `session.context.memory["pending_approval_id"]`; otherwise `Decision(PROCEED, ...)`.
5. **`EVALUATING`** — one more AI call (`Capability.REFLECTION`) for a free-text post-mortem,
   dispatched as `EvaluationCompleted`.
6. `SessionFinished` dispatched; `Decision` returned to the caller.

## Data model

- **`Goal`** (`goal.py`) — `id`, `description`, `success_criteria`.
- **`Plan`** (`plan.py`) — `id`, `goal_id`, `steps: list[Step]`, `current_step_index`;
  `get_next_step()` / `advance()`.
- **`Step`** (`step.py`) — `id`, `description`, `status: StepStatus` (`PENDING`,
  `IN_PROGRESS`, `COMPLETED`, `FAILED`), `result`.
- **`Decision`** (`decision.py`) — `outcome: DecisionOutcome` (`PROCEED`, `ABORT`, `REPLAN`,
  `SEEK_APPROVAL`; only `PROCEED`/`SEEK_APPROVAL` are actually produced today),
  `justification`.
- **`ExecutiveSession`**/**`ExecutiveContext`** — `id`, `state`, `memory: dict[str, str]`,
  `active_capabilities`, `active_tools`, and (since v1.0) `plan: Optional[Plan]`.

## Persistence

`FileSessionRepository` (`persistence.py`) writes `{id, state, memory, plan}` as JSON to
`sessions/<id>.json` on every `save()` call (which happens at every state transition).
`load()` fully restores all four fields, including the in-flight `Plan`/`Step` history with
correct step statuses and `current_step_index` — a session recovered mid-`EXECUTING`
resumes at exactly the right step. (Prior to v1.0, `load()` discarded the file and returned
a blank session, and even after that was fixed, plan/step history still wasn't
round-tripped — both fixed; see `V1_RELEASE_PLAN.md` P0-3 and P1-6.)

`FileAuditLog` subscribes to a configurable list of event types and writes one JSON line per
event to `<log_dir>/audit.log`. Each instance uses its own uniquely-scoped `logging.Logger`,
named from a monotonic counter (a round-1 fix — previously a fixed logger name meant
multiple `FileAuditLog` instances in the same process silently shared one instance's log
destination — plus a round-2 fix to the fix itself: the counter replaced an `id(self)`-based
scheme that could collide under garbage-collection churn and reintroduce the exact same
bug; see `SECURITY_AUDIT.md` SEC-7). `FileAuditLog.close()` detaches and closes the
instance's handler for callers that construct many short-lived instances and want to
release the underlying file descriptor deterministically.

## Events

`EventDispatcher` (`events.py`) is a small pub/sub: `subscribe(event_type, handler)` /
`dispatch(event)`. As of v1.0, `dispatch()` delivers to any subscriber whose registered type
is a match via `isinstance(event, subscribed_type)` — so subscribing to the base `Event`
class (as the WebSocket streamer does) genuinely receives every concrete event, not just
literal `Event` instances (which are never dispatched). This was broken before v1.0 — the
dashboard's live event stream never received anything; see `V1_RELEASE_PLAN.md` P0-4.

Event types dispatched by the reasoning loop: `GoalCreated`, `PlanGenerated`,
`StepCompleted`, `StepFailed`, `StateTransitioned`, `DecisionMade`, `EvaluationCompleted`,
`SessionFinished`. Governance adds `ApprovalRequested`, `ApprovalGranted`,
`ApprovalRejected` (see `GOVERNANCE.md`).

## Known gaps (see `CURRENT_STATE.md`/`V1_RELEASE_PLAN.md` for full detail)

- `_reflect_on_step()` and `_research()` are placeholders, not real self-evaluation/research
  logic, despite the ROADMAP describing a "Self-Evaluation Loop" as done.
- The unconditional per-step `time.sleep(0.5)` that used to slow every goal execution was
  removed in v1.0 (P3-1) — if pacing for dashboard visibility turns out to be wanted, it
  should be a deliberate, configurable choice, not a silent sleep.
