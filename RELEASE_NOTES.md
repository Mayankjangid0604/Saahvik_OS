# Release Notes

## v1.0 RC — Second Hardening Pass (Round 2)

A second pass, this time starting from static analysis (`ruff`, `mypy`) and a dependency
audit (`pip-audit`) rather than manual reading — none of which had been run before. Full
detail in [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md), [`TECHNICAL_DEBT.md`](TECHNICAL_DEBT.md),
[`PERFORMANCE_REPORT.md`](PERFORMANCE_REPORT.md), [`TEST_REPORT.md`](TEST_REPORT.md), and
[`RELEASE_READINESS.md`](RELEASE_READINESS.md).

Test suite: **115 passed / 0 failed / 1 skipped, 91% coverage → 124 passed / 0 failed / 1
skipped, 92% coverage.**

**Two findings beyond round 1's scope, both severity-worthy:**
- **`GIT_EXECUTE` completely bypassed `CommandRestrictionPolicy`.** `GitProvider` runs the
  identical `subprocess.run(shell=True)` injection surface as `ShellProvider`, but the policy
  hardened in round 1 only ever checked `SHELL_EXECUTE` requests. Found via
  `ruff check --select S602`, reproduced live, fixed by widening the policy's gated tool
  names — reusing all of round 1's hardened logic unchanged.
- **A real regression in round 1's own P1-7 fix.** That fix scoped `FileAuditLog`'s logger
  name with `id(self)` to stop instances from sharing a handler — but `id()` is only unique
  among simultaneously-alive objects, not across time, and a construct-and-discard pattern
  can make CPython reuse a freed instance's address, silently reintroducing the exact bug
  the fix was meant to prevent. Reproduced live with a 50-iteration churn test. Fixed with a
  monotonic counter instead.

**Also found and fixed:**
- A genuinely orphaned third FastAPI app (`interfaces/api/main.py`) — hardcoded/mocked
  responses, zero auth, zero policy enforcement, referenced nowhere in the repo. Deleted.
- An `asyncio.create_task()` call with no stored reference in `startup_event()` — a
  documented asyncio gotcha where the WebSocket broadcast task could be garbage-collected
  mid-execution. Fixed by storing the task reference.
- `ToolRegistry.auto_discover()` silently swallowed any exception from constructing a tool
  provider, meaning the tool platform could silently register fewer capabilities than
  expected with zero trace. Now logs a warning and still registers every other provider.
- `OllamaProvider.embed()` didn't validate `model_name` was present before use, unlike every
  other method on the same class — found via `mypy`. Fixed with the same guard.
- 5 `raise-without-from` exception-chaining bugs, 2 duplicate imports, 1 dead computed value
  (and its now-orphaned private method), 25 unused imports, and 6 implicit-`Optional` type
  hints — all mechanical, all verified with the full suite after each change.
- README.md was rewritten: it described a "Milestone 01/02" state that predated the entire
  v1.0 RC codebase, explicitly claiming no tool usage and no model calls existed — both
  false for the actual current system.

**Deliberately not fixed, and why:** `PYTHON_EXECUTE` has zero governance policy coverage —
arbitrary Python code is at least as powerful as unrestricted shell access. This was **not**
given a blocklist-style fix: Python's own introspection defeats string/AST blocklisting far
more easily than shell commands do, so a naive check would create false confidence while
adding real complexity — assessed as worse than no check at all. A real fix needs actual
sandboxing, out of scope for a hardening pass explicitly told not to redesign the
architecture. See `SECURITY_AUDIT.md` SEC-11.

**Also newly documented, not silently accepted:** no CI pipeline exists in this repository
at all — confirmed via the PR's check-runs API returning zero checks. Linting, type
checking, and the dependency audit were all run ad hoc for this pass, not wired into any
automated gate. See `RELEASE_READINESS.md`.

## v1.0 RC — Hardening Pass

This release closes every P0 (critical) and P1/P2/P3 (reliability/security/performance)
item identified in a full architectural audit, without redesigning the existing
architecture. Full details, reasoning, and effort estimates for every item are in
[`V1_RELEASE_PLAN.md`](V1_RELEASE_PLAN.md); the audit itself is in
[`CURRENT_STATE.md`](CURRENT_STATE.md), kept updated in place as findings were fixed or, in
two cases, corrected after turning out to be wrong.

Test suite: **72 passed / 6 failed / 1 skipped, 85% coverage → 115 passed / 0 failed / 1
skipped, 91% coverage.**

### Critical fixes (P0)

- **6 failing tests fixed.** All six predated a `ToolCapability`/`Capability` enum
  migration and still used the old string-based API; production code was already correct.
- **Governance approval loop reconnected.** `ReasoningLoop` computed `SEEK_APPROVAL`
  decisions but never queued them in `ApprovalEngine` — the `/approvals` API and dashboard
  worked in isolation but were never actually invoked. Now wired end-to-end.
- **Session recovery fixed.** `FileSessionRepository.load()` discarded the saved session
  and returned a blank one ("Minimal loading for demonstration" in the source). Now
  restores state, memory, and — as a follow-up fix — in-flight plan/step history, so a
  session recovered mid-execution resumes at the exact step it was on.
- **WebSocket dashboard event stream was completely, silently dead.** `EventDispatcher`
  matched subscribers by exact event type, so a wildcard subscription (as the dashboard
  streamer uses, to receive every event) never matched anything, since only event
  *subclasses* are ever dispatched. Found while testing an unrelated fix; now delivers
  correctly via `isinstance` matching.

### Reliability (P1)

- Fixed a cross-thread race where events dispatched from a background-task thread were
  pushed onto an `asyncio.Queue` unsafely.
- Malformed AI planning responses no longer silently execute as a fake step — they fail
  loud and resolve to a real, queued approval instead.
- Persisted session state now round-trips full plan/step history, not just state/memory.
- Fixed a second, independently-discovered audit-log bug: `FileAuditLog` used a
  process-wide singleton logger, so multiple instances in one process could silently share
  (and lose events to) the first instance's log destination.
- `LiveAIPort` now actually routes through the real `AIRouter`/`ModelRegistry` to a
  provider, instead of returning hardcoded scripted text — with graceful degradation (not a
  crash) when no AI backend is available. **Disclosed limitation:** the live-Ollama happy
  path itself has not been exercised against a real running Ollama instance in this
  environment (none was reachable); validate before relying on it in production.
- Evaluated consolidating duplicated test mock classes across files — declined with
  reasoning after determining they're intentionally different test doubles, not
  accidentally duplicated ones; forcing them together would add complexity, not remove it.

### Security (P2)

- **Real, working path-traversal exploit fixed**, not a theoretical one: workspace
  confinement used string-prefix matching (`str(target).startswith(str(root))`), which a
  sibling directory like `workspace-evil/` could pass against a `workspace/` root. An
  earlier pass of this project's own audit had judged this "not exploitable" from reading
  the code alone — re-tested directly and found to actually leak file contents. Fixed to
  use `Path.is_relative_to()`.
- Shell command policy hardened from a substring blocklist (trivially bypassed by
  whitespace/absolute paths/chaining) to an argv-aware one that parses the actual invoked
  executable per command segment. Explicitly documented as a hardened blocklist, not a full
  sandbox — see `SECURITY.md` for exactly what this does and doesn't stop.
- The three governance-sensitive REST endpoints now require a bearer token when
  `ENTERPRISE_OS_API_TOKEN` is set.

### Performance (P3)

- Removed an unconditional `time.sleep(0.5)` per reasoning-loop step that had no functional
  purpose — cut full test suite wall time from ~3.6s to ~0.6s.
- Added `scripts/perf_baseline.py`, a stdlib-only timing harness covering startup, planning,
  worker creation, tool routing, AI routing, serialization, event dispatch, and real
  API/dashboard latency (measured against an actual local `uvicorn` instance). Every
  in-process operation measured sub-millisecond; nothing here indicated a performance
  problem — the value is a repeatable baseline for future comparison.

### Developer experience (P5)

- Pinned `pytest`/`pytest-cov` as a `dev` extra in `pyproject.toml` — previously undeclared,
  requiring guesswork to run the test suite at all.
- Deleted confirmed dead code (6 empty tool-stub subclasses); relocated a misplaced test
  fixture (`DummyResearchProvider`) from production `infrastructure/` into
  `tests/support.py`. **Two of three original dead-code claims turned out wrong on
  re-verification** (`dummy_provider.py` and `file_document_loader.py` were both actually
  in use) and were corrected rather than silently deleted.
- Fixed an undeclared `requests` dependency in the `drive_ceo.py` demo script, found while
  writing `DEPLOYMENT.md`.

### Documentation (P4)

Added the full doc suite: `ARCHITECTURE.md`, `API.md`, `PROVIDERS.md`, `GOVERNANCE.md`,
`RUNTIME.md`, `WORKERS.md`, `SECURITY.md`, `DEPLOYMENT.md`, `CONTRIBUTING.md`, and this
file. Written to describe the codebase as it actually is after the fixes above — including
several real, still-open gaps (no proactive risk-based approval gate, no worker process
isolation, no WebSocket auth, prompt-injection surface now live rather than theoretical)
stated plainly rather than smoothed over.

### Known limitations carried into this release (see `SECURITY.md`/`V1_RELEASE_PLAN.md`)

- `LiveAIPort`'s live-Ollama happy path is unverified in this environment.
- `CommandRestrictionPolicy` is a hardened blocklist, not a shell sandbox.
- No WebSocket authentication, no proactive risk-based approval gate, no worker/process
  isolation, no rate limiting.
- No containerization or cloud deployment tooling.
- The 8 "milestone" cognitive domain orchestrators are tested in isolation but not wired
  into the `ReasoningLoop`'s actual execution path.

See [`V1_RELEASE_REPORT.md`](V1_RELEASE_REPORT.md) for the full scored assessment and
release recommendation.
