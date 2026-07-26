# Release Notes

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
