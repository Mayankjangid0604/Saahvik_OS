# EnterpriseOS v1.0 Release Plan

Derived directly from `CURRENT_STATE.md`. Every item below traces to a specific finding —
no speculative work. Effort is rough sizing for a single engineer familiar with the codebase,
not a schedule commitment.

Scoring context: 79 tests / 85% coverage / 6 failing at audit time.

---

## P0 — Critical Bugs (block release)

### P0-1 — Fix 6 failing tests (pre-migration string convention)
- **Reason:** `FilesystemProvider`, `ToolRouter`, `WorkerLoop`, and `ReasoningLoop`'s
  production code all correctly use the `ToolCapability`/`Capability` enum contract. Six
  tests were never updated after that migration and still use lowercase string tool names
  and the old `"tool_name"` JSON key.
- **Impact:** CI is red on a clean checkout; nobody can trust the suite as a regression gate
  until this is fixed. Blocks everything else.
- **Effort:** S (~30 min). No production code changes — this is a test-only fix.

### P0-2 — Wire `SEEK_APPROVAL` decisions to `ApprovalEngine` — ✅ FIXED
- **Reason:** `ReasoningLoop` computes `DecisionOutcome.SEEK_APPROVAL` but never calls
  `ApprovalEngine.request_approval()`. The engine, the `/approvals` REST endpoints, and the
  dashboard polling all exist and work in isolation but are never invoked in the real flow.
- **Impact:** The product's core governance promise ("CEO requests approval before risky
  actions") does not function. A stuck goal is invisible to the owner and unrecoverable
  without reading raw event logs.
- **Effort:** M (~2-3h).
- **Resolution:** `ReasoningLoop` now takes an optional `approval_engine: ApprovalEngine`
  and calls `request_approval(justification, context)` in the `SEEK_APPROVAL` branch,
  storing the resulting `approval_id` in `session.context.memory["pending_approval_id"]`.
  `ceo_api.py` wires the app's real `approval_engine` in, and `ApprovalRequested` /
  `ApprovalGranted` / `ApprovalRejected` are now bound to the audit log alongside the
  existing event types. Added
  `test_reasoning_loop_seeks_approval_on_step_failure` driving a real step failure through
  to a resolvable pending approval. `approval_engine` defaults to `None` so existing
  callers/tests that don't pass one are unaffected.

### P0-3 — Fix `FileSessionRepository.load()` to actually restore state — ✅ FIXED
- **Reason:** `load()` checked the file exists, then discarded its contents and returned a
  blank `ExecutiveSession(id=session_id)`. This was explicitly commented "Minimal loading for
  demonstration" in the source.
- **Impact:** Session Recovery (explicit reliability checklist item) was non-functional.
- **Effort:** M (~2h).
- **Resolution:** `load()` now reads back the JSON `save()` already writes and restores
  `context.state` (via `ExecutiveState[data["state"]]`) and `context.memory`.
  Strengthened `test_file_session_repository` to assert the restored state/memory actually
  round-trip (it previously only checked `loaded_session.id`, which would have passed even
  against the old stub), and added `test_file_session_repository_load_missing_session` for
  the not-found path.

---

## P1 — Reliability

### P1-1 — Consolidate duplicated Mock AI/Tool ports into shared test fixtures
- **Reason:** `MockAIPort`/`MockToolPort` are redefined with slightly different signatures
  in multiple test files instead of a single fixture in `tests/support.py`.
- **Impact:** Divergent mocks are exactly how P0-1 happened — a production API change
  updates one mock but not the others, and failures surface late.
- **Effort:** S (~1-2h).

### P1-2 — Fix cross-thread `asyncio.Queue.put_nowait()` in `EventStreamer` — ✅ FIXED
- **Reason:** `ReasoningLoop.execute_goal` runs via FastAPI `BackgroundTasks` (worker
  thread); `EventStreamer._handle_event` pushes onto an `asyncio.Queue` not owned by that
  thread.
- **Impact:** Latent race that could silently drop or corrupt dashboard events under load.
- **Effort:** S (~1h).
- **Resolution:** `broadcast_loop()` now captures the running loop (`self._loop =
  asyncio.get_running_loop()`); `_handle_event` uses `self._loop.call_soon_threadsafe(...)`
  once that loop is known, falling back to a direct `put_nowait` only when no loop has
  started yet (e.g. in tests). Added `tests/unit/interfaces/test_websocket.py` with a real
  cross-thread regression test (`test_handle_event_from_worker_thread_is_delivered_safely`)
  that dispatches from a `threading.Thread` while `broadcast_loop` is running and asserts
  the message is delivered to a fake WebSocket connection.

### P0-4 — `EventDispatcher.dispatch()` never matched wildcard subscribers (found while fixing P1-2) — ✅ FIXED
- **Reason:** Writing the P1-2 regression test surfaced a more severe, previously-untested
  bug: `dispatch()` matched subscribers by exact `type(event)`, not `isinstance`. Every
  concrete event dispatched in production is a subclass of `Event` (`GoalCreated`,
  `StepCompleted`, `DecisionMade`, ...) — the base `Event` class itself is never
  instantiated directly. `EventStreamer.__init__` subscribes to the base `Event` class with
  the explicit comment `# Subscribe to all events`, matching the clear design intent of a
  wildcard subscription — but under exact-type matching, that subscription **never matched
  a single real event**.
- **Impact:** This is more severe than the race it was found alongside: the WebSocket
  dashboard's live event stream was completely non-functional in this codebase — not
  degraded, not racy, but silently dead. No test caught it because no test previously
  exercised `EventStreamer` at all (§13 of `CURRENT_STATE.md`, "Missing Tests"). Retroactively
  reclassified as P0 given it breaks an entire explicit reliability-checklist item
  ("WebSocket Events", "Dashboard") outright, not just partially.
- **Effort:** S (~1h, found opportunistically while doing P1-2's ~2h of work).
- **Resolution:** `EventDispatcher.dispatch()` now iterates registered subscriber types and
  delivers to any where `isinstance(event, event_type)`, matching both exact-type
  subscribers (like `FileAuditLog.bind_to`, which lists concrete event classes — unaffected,
  since `isinstance` reduces to exact-type matching for leaf classes) and wildcard
  subscribers (`EventStreamer`, `Event`). Added
  `test_event_dispatcher_wildcard_subscription_receives_subclass_events`.

### P1-3 — Make `_create_plan()` fail loud on unparseable AI output
- **Reason:** A malformed PLANNING response currently degrades silently to a single
  placeholder step ("Fallback Step due to parsing error") that then runs as if it were a
  real plan.
- **Impact:** Confusing failure mode — a broken AI response looks like a deliberately tiny
  plan rather than an error, making debugging harder and potentially wasting a tool
  execution on a nonsense step.
- **Effort:** S (~1h): dispatch a distinguishable event (or route straight to
  `SEEK_APPROVAL`) instead of silently substituting a fake step.

### P1-4 — Wire `LiveAIPort` to the actual `AIRouter`/Ollama backend, or rename it
- **Reason:** `LiveAIPort.request_capability` is fully scripted (canned text keyed on
  prompt substrings) despite the router/registry/Ollama client all being constructed and
  passed in. It never calls `self.router`.
- **Impact:** Misleading naming aside, no code path in this repo currently performs a real
  model call, which means "AI Routing" and "Provider Discovery" reliability checklist items
  are unverified against a real backend.
- **Effort:** M (~3-4h): either implement the real routing call (route capability → model →
  `OllamaProvider.generate()`) behind a feature flag, with the scripted version kept only for
  demo/offline mode, or explicitly rename it `ScriptedDemoAIPort` so nobody mistakes it for
  production wiring. Recommend the former given the ROADMAP's "Real project validation" goal
  for this RC stage.

### P1-5 — Test the `ApprovalEngine` end-to-end (depends on P0-2) — ✅ DONE
- **Reason:** No test currently drives a goal from step failure through to a queued,
  resolvable approval.
- **Impact:** Without this, P0-2 can regress silently.
- **Effort:** S (~1h), bundled with P0-2's implementation.
- **Resolution:** Landed together with P0-2 as
  `test_reasoning_loop_seeks_approval_on_step_failure`.

### P1-6 — Persist and restore `plan`/`step` history, not just `state`/`memory`
- **Reason:** Discovered while fixing P0-3: `FileSessionRepository.save()` only ever wrote
  `{id, state, memory}` — it never captured the in-flight `Plan`/`Step` objects that
  `ReasoningLoop` is working through. Fixing `load()` to correctly restore what `save()`
  writes (P0-3) makes this gap visible rather than silent: a recovered session now correctly
  resumes at the right `ExecutiveState` with its memory, but a session recovered mid-`EXECUTING`
  has no record of which step it was on or what the remaining plan was.
- **Impact:** True session recovery (resuming a goal after a crash/restart mid-execution) is
  still not possible — only state/memory recovery is. Lower severity than P0-3 was, since no
  caller currently invokes recovery at all yet, but it's the next thing that will break the
  moment recovery is wired into a real restart path.
- **Effort:** M (~2-3h): extend the saved payload with the current `Plan` (id, goal_id, steps
  with status/result, current_step_index) and reconstruct it in `load()`; add a round-trip
  test that saves mid-plan and resumes from the exact step.

---

## P2 — Security

### P2-1 — Replace shell command blocklist with an allowlist
- **Reason:** `CommandRestrictionPolicy` blocks 5 substrings (`rm -rf`, `sudo`, `mkfs`,
  `chown`, `chmod`) via plain `in` checks against a command that is then run with
  `subprocess.run(shell=True)`. Trivially bypassed by whitespace, absolute paths, piping to
  an interpreter, or any destructive command simply not on the list.
- **Impact:** This is the sharpest edge in the security checklist — "arbitrary shell
  execution" is currently possible for anything not matching 5 fixed strings.
- **Effort:** M (~3-4h): design an explicit allowlist of permitted command *shapes* (or
  restrict to non-`shell=True` argv execution for a fixed tool set), add security tests that
  attempt the bypass strings identified in the audit and confirm they're now blocked.

### P2-2 — Switch path-containment checks to `Path.is_relative_to()`
- **Reason:** `WorkspaceConfinementPolicy` and `FilesystemProvider._resolve_safe_path()`
  both use `str(target).startswith(str(root))`, a string-prefix pattern that's fragile even
  though it isn't currently exploitable here (verified during audit).
- **Impact:** Low active risk today, but this is exactly the kind of check that becomes
  exploitable after an unrelated refactor. Cheap to harden now.
- **Effort:** S (~1h) across both call sites, plus a regression test for the sibling-directory
  case (`workspace-evil/` vs `workspace/`).

### P2-3 — Add minimal auth to approval-resolution and goal-submission endpoints
- **Reason:** `/ceo/goal`, `/approvals/{id}` (approve/reject) are unauthenticated.
  Acceptable for a local single-owner MVP but should be a documented, deliberate decision,
  not a silent gap, before calling this v1.0.
- **Impact:** Anyone with network access to the API can submit goals or approve/reject
  pending governance decisions on the owner's behalf.
- **Effort:** M (~2-3h) for a simple shared-secret/bearer-token gate; document as a known
  limitation if deferred rather than silently shipped.

---

## P3 — Performance

### P3-1 — Remove the unconditional `time.sleep(0.5)` in `ReasoningLoop`
- **Reason:** Every iteration of the main execution loop sleeps 0.5s for no functional
  reason (no rate limit, no debounce documented).
- **Impact:** Directly slows every goal execution and every test that exercises the loop.
  A 3-step goal loses 1.5s doing nothing.
- **Effort:** XS (~15 min): delete it (or replace with an explicit, configurable pacing
  hook if it turns out to exist for dashboard-visibility reasons — confirm with the user
  before deleting if intent is unclear).

### P3-2 — Add a minimal performance baseline harness
- **Reason:** The mission asks to measure startup/planning/worker-creation/routing/API
  latency, and none of that is currently measured anywhere in the repo.
- **Impact:** Without a baseline, "performance improved" can't be substantiated.
- **Effort:** M (~3h): a small pytest-benchmark or manual timing script covering the
  metrics named in the mission brief, run against the (currently scripted) AI path so it's
  deterministic.

---

## P4 — Documentation

### P4-1 — Write the missing doc suite
- **Reason:** `ARCHITECTURE.md`, `API.md`, `PROVIDERS.md`, `GOVERNANCE.md`, `RUNTIME.md`,
  `WORKERS.md`, `SECURITY.md`, `DEPLOYMENT.md`, `CONTRIBUTING.md`, `RELEASE_NOTES.md` do not
  exist. `docs/` currently holds only internal milestone/build logs.
- **Impact:** No external-facing documentation exists for a "v1.0" release.
- **Effort:** L (~1-2 days total across all 10 docs) — best done incrementally, one doc per
  completed subsystem fix (e.g. write `GOVERNANCE.md` right after P0-2 lands, so it
  describes the real, working flow rather than the aspirational one).

---

## P5 — Developer Experience

### P5-1 — Pin dev tooling (pytest, coverage, lint, type-check) in `pyproject.toml`
- **Reason:** `pyproject.toml` declares only `fastapi`/`uvicorn`; pytest/coverage aren't
  listed as dependencies anywhere, so a fresh clone can't run the test suite without
  guessing what to install.
- **Impact:** Contributor friction; this audit itself required manually installing pytest.
- **Effort:** S (~1h): add a `[project.optional-dependencies] dev` group.

### P5-2 — Delete confirmed dead code
- **Reason:** `domain/operations/tools.py` (empty `pass` tool stubs, unreferenced),
  `infrastructure/dummy_provider.py` (test fixture misplaced in production infra),
  `infrastructure/config/file_document_loader.py` (no importers found in `src/`).
- **Impact:** Reduces surface area to maintain; matches the mission's explicit "prefer
  deleting code over adding code."
- **Effort:** S (~1h): delete `domain/operations/tools.py` outright; move
  `dummy_provider.py` to `tests/fixtures/`; either wire up `file_document_loader.py` to an
  actual config load path or delete it — confirm which with a quick grep before deleting in
  case something outside `src/` (e.g. a script) depends on it.

---

## Suggested Execution Order

P0-1 → P0-2 (+P1-5) → P0-3 → P1-2 → P1-3 → P2-1 → P2-2 → P1-4 → P2-3 → P3-1 → P3-2 → P4-1 → P5-1 → P5-2

P0-1 unblocks a trustworthy CI signal for everything after it. P0-2/P0-3 restore the two
features most central to the product's stated purpose. P1-2/P1-3 are cheap reliability wins
before touching security-sensitive code. P2-1 (shell allowlist) is the highest-severity
security item and should land before any performance or doc work. P4-1 is sequenced late
per-subsystem so documentation describes the *actual* fixed behavior, not the pre-fix state.
