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
