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

### P1-1 — Consolidate duplicated Mock AI/Tool ports into shared test fixtures — ❌ RE-EVALUATED, NOT DONE
- **Reason (as originally written):** `MockAIPort`/`MockToolPort` are redefined with
  slightly different signatures in multiple test files instead of a single fixture in
  `tests/support.py`.
- **Re-evaluation before implementing:** read both pairs side by side.
  `test_runtime.py`'s `MockAIPort` takes no constructor args and derives its response from
  the requested `capability` (PLANNING vs TOOL_SELECTION); `test_worker_runtime.py`'s takes
  an arbitrary JSON string in its constructor and returns it unconditionally, regardless of
  capability — the point of that test is to control the AI's raw output directly. Same
  story for the two `MockToolPort`s (one always succeeds; the other branches on which
  `ToolCapability` was requested). These are not the *same* fixture accidentally
  reimplemented twice — they're two different, intentionally-small test doubles that
  happen to share a name.
- **Impact if forced anyway:** a shared fixture flexible enough to cover both use cases
  (constructor-injected canned response *and* capability-keyed branching) would need more
  parameters/branches than either individual mock has today — net more complexity, not
  less, and a reader of either test file would now need to open `tests/support.py` to
  understand what the mock in front of them actually does. That's the opposite of this
  release's explicit "do not add unnecessary abstractions" instruction.
- **Also worth noting:** the original justification ("divergent mocks are exactly how
  P0-1 happened") doesn't hold up under scrutiny either — P0-1's root cause was that *all*
  of these mocks used the pre-enum-migration string API, i.e. they were stale relative to
  production, not inconsistent with each other. That root cause was already fixed directly
  in P0-1's commit.
- **Disposition:** declined. Leaving these as small, self-contained, per-file test doubles
  — the normal pytest pattern — rather than merging them into a shared abstraction that
  doesn't reduce real risk.

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

### P1-3 — Make `_create_plan()` fail loud on unparseable AI output — ✅ FIXED
- **Reason:** A malformed PLANNING response previously degraded silently to a single
  placeholder step ("Fallback Step due to parsing error") that then ran as if it were a
  real plan.
- **Impact:** Confusing failure mode — a broken AI response looked like a deliberately tiny
  plan rather than an error, making debugging harder and wasting a tool execution on a
  nonsense step.
- **Effort:** S (~1h).
- **Resolution:** On parse failure, `_create_plan()` now produces a single step
  pre-marked `StepStatus.FAILED` with the parse error captured in `result`, instead of a
  runnable placeholder. `_execute_step()` short-circuits on an already-`FAILED` step,
  dispatching `StepFailed` and returning without invoking the worker/tool port at all. This
  reuses the existing `failed_steps` check at the `DECIDING` stage, so the goal correctly
  resolves to `SEEK_APPROVAL` (and now queues a real approval via P0-2) with zero new event
  types or control-flow branches added to `execute_goal`. Added
  `test_reasoning_loop_fails_loud_on_unparseable_plan`, which asserts the tool port's
  `execute_tool` is never called.

### P1-4 — Wire `LiveAIPort` to the actual `AIRouter`/Ollama backend, or rename it — ✅ FIXED (with an honest, disclosed testing limitation)
- **Reason:** `LiveAIPort.request_capability` was fully scripted (canned text keyed on
  prompt substrings) despite the router/registry/Ollama client all being constructed and
  passed in. It never called `self.router`.
- **Impact:** Misleading naming aside, no code path in this repo performed a real model
  call, which meant "AI Routing" and "Provider Discovery" reliability checklist items were
  unverified against a real backend.
- **Effort:** M (~3-4h), actual.
- **Resolution:** `LiveAIPort.request_capability` now calls `self.router.route(capability)`
  to get an `AIExecutionPlan`, looks up the provider by `plan.provider_name` in
  `self.registry`, builds a real `AIRequest` (prompt, system_prompt, temperature,
  max_tokens, json_mode, `metadata["model_name"]`), and calls `provider.generate(request)`
  — exactly the wiring that was already constructed and passed in but unused. If routing
  fails (`RoutingError` — e.g. no healthy model registered) or the provider call itself
  fails (`ProviderUnavailableError` etc., all subclasses of `AIPlatformError`), it's caught
  and turned into an `AIResponse` carrying an `AI_PROVIDER_ERROR:` marker and
  `finish_reason="error"` instead of propagating an exception — `ReasoningLoop`/`WorkerLoop`
  already treat unparseable AI output as a graceful step/plan failure that resolves to
  `SEEK_APPROVAL` (P1-3), so an unavailable AI backend now degrades exactly the same way
  instead of crashing the reasoning loop.
- **What was and wasn't verified, stated plainly:** the routing/error-handling *logic* is
  covered by 5 tests in `tests/unit/interfaces/test_live_ai_port.py`, including one that
  drives a full `ReasoningLoop.execute_goal()` with a real, empty `ModelRegistry` (no
  Ollama server registered) end to end and confirms it resolves to a well-formed
  `SEEK_APPROVAL` rather than an unhandled exception — this is, not coincidentally, exactly
  the state this development environment is actually in (no Ollama server reachable here),
  so it's a real, not simulated, exercise of the "AI backend unavailable" path. **What
  could not be verified in this environment: an actual successful call to a running Ollama
  server with a real model returning real inference output.** No Ollama instance is
  reachable from this sandbox, so the "happy path" through `OllamaProvider.generate()` to a
  live model is implemented per the design already present in `ollama_provider.py`/
  `ollama_client.py` (both pre-existing, unmodified by this change) but has not been
  exercised against a real backend in this session. Before relying on this in production,
  run a real goal against a running Ollama instance with at least one pulled model and
  confirm end-to-end behavior — this is called out explicitly rather than silently claimed
  as fully verified.
- The feature-flag/rename alternative considered in the original item was dropped in favor
  of direct wiring with graceful degradation, since that gives the real behavior (attempt a
  real model, fail safe if unavailable) rather than a permanent demo-mode toggle.

### P1-5 — Test the `ApprovalEngine` end-to-end (depends on P0-2) — ✅ DONE
- **Reason:** No test currently drives a goal from step failure through to a queued,
  resolvable approval.
- **Impact:** Without this, P0-2 can regress silently.
- **Effort:** S (~1h), bundled with P0-2's implementation.
- **Resolution:** Landed together with P0-2 as
  `test_reasoning_loop_seeks_approval_on_step_failure`.

### P1-6 — Persist and restore `plan`/`step` history, not just `state`/`memory` — ✅ FIXED
- **Reason:** Discovered while fixing P0-3: `FileSessionRepository.save()` only ever wrote
  `{id, state, memory}` — it never captured the in-flight `Plan`/`Step` objects that
  `ReasoningLoop` is working through. A session recovered mid-`EXECUTING` had no record of
  which step it was on or what the remaining plan was.
- **Impact:** True session recovery (resuming a goal after a crash/restart mid-execution)
  was still not possible — only state/memory recovery was.
- **Effort:** M (~2-3h).
- **Resolution:** Added an optional `plan: Optional[Plan]` field to `ExecutiveContext`
  (previously the plan was purely a local variable inside `ReasoningLoop.execute_goal`, not
  reachable from the session at all). `ReasoningLoop` now assigns `session.context.plan =
  plan` immediately after creating it, so every `repository.save(session)` call already in
  the loop captures the live plan/step state as it progresses (steps are mutable
  dataclasses, so no extra save calls were needed). `FileSessionRepository` gained
  `_serialize_plan`/`_deserialize_plan` helpers, serializing each step's `id`, `description`,
  `status`, and `result`, plus the plan's `current_step_index`. Added
  `test_file_session_repository_round_trips_mid_execution_plan`, which saves a 3-step plan
  mid-`EXECUTING` (one `COMPLETED`, one `IN_PROGRESS`, one `PENDING`) and asserts the
  recovered session's `plan.get_next_step()` resumes at exactly the right step.

### P1-7 — `FileAuditLog` instances silently shared a single global log destination — ✅ FIXED (found while implementing P2-3)
- **Reason:** `FileAuditLog.__init__` called `logging.getLogger("AuditLog")` — a fixed
  name, which Python's `logging` module treats as a process-wide singleton — then only
  attached a `FileHandler` `if not self.logger.handlers`. The *first* `FileAuditLog`
  constructed in a process wins that check; every subsequently constructed instance in the
  same process reuses the first one's handler and silently writes to *its* `log_dir`,
  ignoring whatever `log_dir` it was itself given.
- **How it was found:** writing `tests/unit/interfaces/test_ceo_api_auth.py` for P2-3
  imports `enterprise_os.interfaces.api.ceo_api`, which constructs its own `FileAuditLog`
  pointed at the repo's real `logs/` directory as a module-level side effect. Because that
  test file sorts before `tests/unit/runtime/test_events_persistence.py` in pytest's
  collection order, the existing `test_file_audit_log` — previously always run first in
  isolation and never observed to fail — started failing: its `FileAuditLog(log_dir=str
  (tmp_path))` silently reused `ceo_api`'s already-registered handler instead of writing to
  `tmp_path`.
- **Impact:** This is an audit-integrity bug (explicit security-checklist item), not just a
  test-ordering artifact. In any real process that constructs more than one `FileAuditLog`
  — or restarts logging setup during a long-running process — audit events could silently
  end up in the wrong file, or a later instance's intended `log_dir` could be ignored
  entirely.
- **Effort:** S (~1h, found and fixed opportunistically alongside P2-3's ~2-3h).
- **Resolution:** Scoped the logger name per instance (`f"AuditLog.{id(self)}"` instead of
  the fixed `"AuditLog"`), so each `FileAuditLog` genuinely owns its own logger and handler
  regardless of instantiation order elsewhere in the process; also set `propagate = False`
  so audit lines can't leak into an ancestor logger's handlers. Added
  `test_file_audit_log_instances_do_not_share_a_handler`, which constructs two
  `FileAuditLog`s with different `log_dir`s in the same process and asserts each only
  contains its own events. Full suite re-verified green regardless of collection order.

---

## P2 — Security

### P2-1 — Harden the shell command policy against blocklist bypass — ✅ FIXED
- **Reason:** `CommandRestrictionPolicy` blocked 5 substrings (`rm -rf`, `sudo`, `mkfs`,
  `chown`, `chmod`) via plain `in` checks against a command that is then run with
  `subprocess.run(shell=True)`. Trivially bypassed by whitespace, absolute paths, or
  chaining a forbidden command after an allowed one.
- **Impact:** This was the sharpest edge in the security checklist — "arbitrary shell
  execution" was possible for anything not matching 5 fixed substrings.
- **Effort:** M (~3-4h).
- **Resolution:** A true allowlist of permitted command *shapes* was considered but
  rejected: `ShellProvider` is a general-purpose shell tool the CEO/worker use for
  arbitrary build/test/file commands (confirmed via `LiveAIPort`'s scripted examples —
  `mkdir`, writing files, running Python), so a strict argument allowlist would break the
  tool's intended use — exactly the kind of redesign this release is not meant to do.
  Instead, hardened the existing blocklist model to close the specific bypasses found in
  the audit: the command is now split on `;`/`&&`/`||`/`|` into the sub-commands it could
  actually invoke, each parsed with `shlex.split()`, and the *actual executable name*
  (path-stripped) is checked against the forbidden set — closing the whitespace,
  absolute-path, and chaining bypasses. Command substitution (`$(...)` / backticks), which
  can hide a sub-command from this segment-level view, is rejected outright. This is **not**
  a full shell sandbox — documented as a residual limitation, not overclaimed as solved.
  Added `tests/unit/governance/test_command_restriction_policy.py` (12 tests): legitimate
  commands still pass, the direct forbidden case still blocks, and all 6 bypass strings
  identified in the audit (extra whitespace, absolute path, `&&`/`;`/`||`/`|`-chained,
  substitution) are now correctly blocked.

### P2-2 — Switch path-containment checks to `Path.is_relative_to()` — ✅ FIXED
- **Reason:** `WorkspaceConfinementPolicy` and `FilesystemProvider._resolve_safe_path()`
  both used `str(target).startswith(str(root))`, a string-prefix pattern.
- **Impact:** **Higher than originally assessed.** The initial audit pass judged this "not
  currently exploitable" from reading the code alone. That was wrong: tested directly with
  a `workspace` root and a `workspace-evil` sibling directory, and confirmed
  `FilesystemProvider.execute()` actually leaked the sibling file's contents before the fix
  — `"/workspace-evil/secret.txt".startswith("/workspace")` is `True` in plain string
  terms. This was a real, working path-traversal bypass of workspace confinement, not a
  theoretical one.
- **Effort:** S (~1h).
- **Resolution:** Both call sites now use `Path.is_relative_to()`. Added
  `tests/unit/governance/test_workspace_confinement_policy.py` (new — this policy had zero
  prior tests) and `test_filesystem_provider_blocks_sibling_directory_with_overlapping_prefix`,
  both confirming the bypass is closed. Also verified the adjacent symlink-escape claim
  from the original audit with an actual exploit attempt rather than leaving it as an
  unverified "confirmed by tracing the code" note — it holds:
  `test_filesystem_provider_blocks_symlink_escape` plants a symlink to an outside directory
  and confirms the read is denied, since `.resolve()` runs before the containment check.

### P2-3 — Add minimal auth to approval-resolution and goal-submission endpoints — ✅ FIXED
- **Reason:** `/ceo/goal`, `/approvals`, `/approvals/{id}` (approve/reject) were
  unauthenticated. Acceptable for a local single-owner MVP but needed to be a documented,
  deliberate decision, not a silent gap, before calling this v1.0.
- **Impact:** Anyone with network access to the API could submit goals or approve/reject
  pending governance decisions on the owner's behalf.
- **Effort:** M (~2-3h).
- **Resolution:** Added a `require_api_token` FastAPI dependency gating `POST /ceo/goal`,
  `GET /approvals`, and `POST /approvals/{approval_id}` — the three governance-sensitive
  routes named in the original finding. `/health`, the WebSocket endpoint, and the static
  dashboard mount are intentionally left ungated (health checks and static assets don't
  need auth; WebSocket auth is a separate, larger concern not in this item's scope). Reads
  an expected token from `ENTERPRISE_OS_API_TOKEN`; if unset, auth is a no-op — a
  deliberate, now-documented default for local single-owner use, not a silent gap. When
  set, requests must send `Authorization: Bearer <token>` or get a 401. Added
  `tests/unit/interfaces/test_ceo_api_auth.py` (6 tests): the dependency's allow/reject
  logic in both auth-disabled and auth-enabled modes, plus a test that inspects the actual
  FastAPI route table to confirm the dependency is wired onto exactly the three intended
  routes (not just defined and unused).
- **Found opportunistically while implementing this (see P1-7 below):** writing this test
  file — which imports `ceo_api` for the first time in the test suite's collection order —
  exposed a real, separate audit-integrity bug in `FileAuditLog`.

---

## P3 — Performance

### P3-1 — Remove the unconditional `time.sleep(0.5)` in `ReasoningLoop` — ✅ FIXED
- **Reason:** Every iteration of the main execution loop slept 0.5s for no functional
  reason (no rate limit, no debounce documented anywhere in the code or docs).
- **Impact:** Directly slowed every goal execution and every test that exercises the loop.
- **Effort:** XS (~15 min).
- **Resolution:** Deleted. Measured effect: the full test suite's wall time dropped from
  ~3.6s to ~0.6s (most of the suite exercises the reasoning loop at least once). No
  behavioral test depended on the delay's existence. If dashboard-visibility pacing turns
  out to be wanted after live model wiring lands (P1-4), that should be a deliberate,
  documented, configurable choice — not a silent unconditional sleep.

### P3-2 — Add a minimal performance baseline harness — ✅ DONE
- **Reason:** The mission asks to measure startup/planning/worker-creation/routing/API
  latency, and none of that was measured anywhere in the repo.
- **Impact:** Without a baseline, "performance improved" can't be substantiated.
- **Effort:** M (~3h), actual.
- **Resolution:** Added `scripts/perf_baseline.py` — a manual timing script (deliberately
  not a pytest suite: performance numbers are environment-dependent and shouldn't be
  asserted as hard pass/fail gates in CI), using only stdlib (`time`, `statistics`,
  `subprocess`, `urllib.request`) and the project's own `uvicorn` dependency, no new
  dependencies added. Covers every metric named in the mission brief, including API and
  dashboard latency measured against a real local `uvicorn` instance actually started by
  the script (not simulated). Actual results from this environment (no live Ollama
  backend — AI routing exercises the graceful-degradation path from P1-4, not live
  inference):

  | Operation | Mean | Median | p95 | n |
  |---|---|---|---|---|
  | Startup (cold import, subprocess) | 122.53ms | — | — | 1 |
  | AI routing (route + degrade, no model registered) | 0.0041ms | 0.0031ms | 0.0045ms | 200 |
  | Planning (`_create_plan`) | 0.0170ms | 0.0140ms | 0.0266ms | 200 |
  | Worker creation (`WorkItem`) | 0.0011ms | 0.0011ms | 0.0017ms | 1000 |
  | Tool routing (`ToolRouter.route`) | 0.0011ms | 0.0011ms | 0.0011ms | 1000 |
  | Serialization — save | 0.2515ms | 0.2077ms | 0.3270ms | 500 |
  | Serialization — load | 0.0394ms | 0.0332ms | 0.0662ms | 500 |
  | Event dispatch | 0.0004ms | 0.0004ms | 0.0007ms | 2000 |
  | API latency (`GET /health`) | 0.9534ms | 0.9585ms | 1.1974ms | 50 |
  | Dashboard latency (`GET /`) | 2.1703ms | 1.9278ms | 2.5266ms | 50 |

  **Reading these honestly:** every in-process operation (routing, planning, serialization,
  event dispatch) is sub-millisecond and not a concern at current scale — none of these are
  bottlenecks worth optimizing pre-v1.0. Startup (~123ms) is dominated by Python import
  time, not application logic. AI routing here measures the *degradation* path (no model
  registered), not real inference latency — that number will be dominated entirely by
  actual model response time once run against a live Ollama backend, which is a
  fundamentally different (and much larger) cost this harness cannot measure without one.
  Nothing here indicates a performance problem; the value of this baseline is having a
  repeatable script and real numbers to compare future changes against, not a "problem
  found and fixed."

---

## P4 — Documentation

### P4-1 — Write the missing doc suite — ✅ DONE
- **Reason:** `ARCHITECTURE.md`, `API.md`, `PROVIDERS.md`, `GOVERNANCE.md`, `RUNTIME.md`,
  `WORKERS.md`, `SECURITY.md`, `DEPLOYMENT.md`, `CONTRIBUTING.md`, `RELEASE_NOTES.md` did
  not exist. `docs/` holds only internal milestone/build logs.
- **Impact:** No external-facing documentation existed for a "v1.0" release.
- **Effort:** L (~1-2 days), actual — done after all code fixes landed, so each doc
  describes the real, fixed behavior rather than the pre-fix state.
- **Resolution:** All 10 docs added at repo root, alongside `README.md`/`CURRENT_STATE.md`.
  Written from the actual, verified current code (cross-referenced against source during
  writing, not from memory of the audit) — including honest disclosure of real, still-open
  gaps found in the process of writing them rather than smoothing them over: no proactive
  risk-based approval gate (`GOVERNANCE.md`), no worker/process isolation
  (`WORKERS.md`/`SECURITY.md`), no WebSocket auth (`API.md`/`SECURITY.md`), and a live
  prompt-injection surface now that `LiveAIPort` calls a real model (`SECURITY.md`).
  **One more small, real bug found and fixed while writing `DEPLOYMENT.md`:** the demo
  script `drive_ceo.py` imports `requests`, which was never declared as a dependency
  anywhere in `pyproject.toml` and isn't installed by default — added a `demo` extra.

---

## P5 — Developer Experience

### P5-1 — Pin dev tooling (pytest, coverage) in `pyproject.toml` — ✅ FIXED
- **Reason:** `pyproject.toml` declared only `fastapi`/`uvicorn`; pytest/coverage weren't
  listed as dependencies anywhere, so a fresh clone couldn't run the test suite without
  guessing what to install.
- **Impact:** Contributor friction; this audit itself required manually installing pytest.
- **Effort:** S (~1h).
- **Resolution:** Added a `[project.optional-dependencies] dev` group with `pytest>=8` and
  `pytest-cov>=5` (the versions actually used to run this session's test suite: pytest
  9.1.1, pytest-cov 7.1.0). `pip install -e .[dev]` now gets a contributor everything
  needed to run `pytest`. Lint/type-check tooling was in the original item's title but no
  such tooling exists anywhere in this repo today (no `mypy`/`ruff`/`flake8` config found
  during the audit) — adding one would be introducing new process, not pinning what's
  already used, so left out of scope here rather than silently added.

### P5-2 — Delete confirmed dead code — ✅ DONE (2 of 3 original claims were wrong)
- **Reason (as originally written):** `domain/operations/tools.py` (empty `pass` tool
  stubs, unreferenced), `infrastructure/dummy_provider.py` (test fixture misplaced in
  production infra), `infrastructure/config/file_document_loader.py` (no importers found).
- **Correction before acting:** re-grepped each claim before touching anything, per the
  lesson from P2-2 (an earlier "not exploitable" claim that turned out wrong on testing).
  Two of the three were also wrong:
  - `infrastructure/dummy_provider.py` is **not dead** — `DummyResearchProvider` is a real
    dependency of `tests/unit/application/test_research_orchestrator.py`. It genuinely was
    misplaced (a test fixture living in `src/`), so the original instinct to relocate it
    was right; "unused" was not.
  - `infrastructure/config/file_document_loader.py` is **not dead** —
    `FileDocumentLoader` is imported and used by `bootstrap/ceo_bootstrap.py`. Original
    grep for this was insufficiently broad. Left untouched.
  - `domain/operations/tools.py` was partially right: the 6 concrete subclasses
    (`FilesystemTool`, `TerminalTool`, `BrowserTool`, `GitTool`, `PythonTool`, `APITool`)
    are genuinely dead (zero call sites, all empty `pass` bodies duplicating
    `providers/tools/implementations/*`), but the file's `ToolInterface` ABC is not — it's
    used as a type in `application/ports/operations.py`'s `ToolProviderPort`. Also, all 6
    were re-exported in `domain/operations/__init__.py`'s `__all__`, so removing them
    required updating that file too, not just the stub file.
- **Effort:** S (~1h), actual.
- **Resolution:** Deleted the 6 dead stub subclasses from `tools.py`, kept `ToolInterface`;
  removed them from `domain/operations/__init__.py`'s imports and `__all__`. Moved
  `DummyResearchProvider` into `tests/support.py` (the existing shared test-fixture module)
  and updated its one call site; deleted the now-empty `infrastructure/dummy_provider.py`.
  Left `file_document_loader.py` alone — it's real, used code.

---

## Suggested Execution Order

P0-1 → P0-2 (+P1-5) → P0-3 → P1-2 → P1-3 → P2-1 → P2-2 → P1-4 → P2-3 → P3-1 → P3-2 → P4-1 → P5-1 → P5-2

P0-1 unblocks a trustworthy CI signal for everything after it. P0-2/P0-3 restore the two
features most central to the product's stated purpose. P1-2/P1-3 are cheap reliability wins
before touching security-sensitive code. P2-1 (shell allowlist) is the highest-severity
security item and should land before any performance or doc work. P4-1 is sequenced late
per-subsystem so documentation describes the *actual* fixed behavior, not the pre-fix state.
