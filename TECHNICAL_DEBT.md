# Technical Debt

This is a specialized cut of `CURRENT_STATE.md`/`V1_RELEASE_PLAN.md` focused specifically
on debt — duplicated logic, dead code, architectural inconsistencies, and design gaps —
current as of the round-2 hardening pass. Everything here is either fixed (marked ✅, with
the commit that fixed it) or open and explicitly justified as out of scope, not silently
carried forward.

## Fixed this round

- **Orphaned third FastAPI app.** `interfaces/api/main.py` was a completely separate,
  ungoverned app (hardcoded/mocked responses, zero auth, zero policy enforcement) with no
  references anywhere in the repo. Deleted. This is the most significant debt item found in
  round 2 — an entire unreferenced API surface that round 1's audit missed.
- **6 dead tool-stub subclasses** in `domain/operations/tools.py` (round 1, P5-2).
- **A misplaced test fixture** (`DummyResearchProvider`) living in production
  `infrastructure/` instead of `tests/` (round 1, P5-2).
- **25 unused imports** across 15 files (round 2), removed via `ruff --select F401 --fix`
  and verified with the full suite.
- **A dead computed value** (`analysis` in `OrganisationalOrchestrator.execute_cycle`) and
  its now-orphaned private method (round 2).
- **Duplicate imports** (`StaticFiles`, `os` each imported twice in `ceo_api.py`) (round 2).

## Open, with reasoning (not silently carried forward)

### Architectural inconsistency: three independent, uncoordinated execution paths
1. `ceo_api.py`'s `ReasoningLoop` — the real, governed, tested loop this whole doc suite
   describes.
2. `main.py`'s `boot_ceo()` cognitive loop — a separate "Digital CEO" loop for the 8
   milestone domains, reading its own config files, with its own persistence
   (`FileActionLogger`/`FileThoughtLogger`).
3. (Removed) the orphaned third FastAPI app above.

Two of these remain, and they don't coordinate — a goal submitted to one has no effect on
the other. This is architecturally confusing for a new contributor and is exactly the kind
of thing `DEPLOYMENT.md` now calls out explicitly rather than leaving implicit. **Not fixed**:
unifying these would mean deciding which one is canonical and either deleting or
re-architecting the other, which is a product decision this hardening pass isn't positioned
to make unilaterally ("do not redesign the architecture").

### The 8 milestone-domain orchestrators are tested in isolation but not wired to the runtime
`application/services/*_orchestrator.py` (strategy, operations, organisation, research,
knowledge, optimisation, growth, evolution) each have passing unit tests and return
plausible-looking output, but none of them are called from `ReasoningLoop`. They represent
a broader design surface than what the system actually does today. Two concrete symptoms
found in round 2, left unfixed and documented rather than guessed at:
- `operational_orchestrator.py:26` passes `resp.required_capabilities[0] if
  resp.required_capabilities else None` into a `Task.required_capability` field typed as
  non-Optional `Capability` (mypy-flagged). Fixing this correctly requires knowing intent
  (should the field become `Optional`, or should the orchestrator guarantee a value?) —
  not guessed at.
- `boot_ceo.py:99` passes `cognitive_engine.complete_cycle` (returns `CognitiveCycle`) as
  `CEORuntime.loop_step`, typed `Callable[[], None] | None` (mypy-flagged). The annotation
  is stricter than actual production usage; the correct fix (widen the annotation vs.
  change the call site) again depends on intent.

Both are narrow, low-severity, and confined to the milestone-domain layer that isn't in the
live execution path — not ignored, just correctly scoped as "needs a decision, not a guess."

### Mixed return types assigned to one variable in `FilesystemProvider.execute()`
`result` is assigned `str` in two branches and `list[str]` in the third (mypy-flagged,
harmless at runtime since Python is dynamically typed, but a real type-accuracy gap).
**Partially addressed**: an explicit `result: str | list[str]` annotation was added to make
the actual behavior legible to type checkers; splitting into differently-typed variables per
branch would be a larger, not-clearly-justified refactor of working code.

### `ToolRegistry.auto_discover()`'s dynamic reflection isn't statically type-checkable
mypy flags `register_provider(provider_instance)` because `attr_val(**init_kwargs)`'s return
type can't be verified without running it — inherent to doing runtime reflection over a
package. Documented in place with an explained `# type: ignore[arg-type]` rather than
either suppressing it silently or forcing a redesign of the discovery mechanism.

### `ApprovalEngine._queue` and other shared dicts accessed across threads
`ApprovalEngine`, `EventDispatcher`, and `ToolRegistry` all hold plain `dict`/`list`
attributes that are read from the FastAPI event loop thread and written from background-task
worker threads (goal execution runs via `BackgroundTasks`). CPython's GIL makes individual
dict/list operations atomic, so this does not crash or corrupt memory, and no evidence of
incorrect behavior was found or reproduced. **Not fixed**: adding locks here would be
unjustified complexity without a proven bug — consistent with "if an issue cannot be proven,
do not change the code." Documented so it's a reviewed, accepted characteristic rather than
an unexamined risk.

### No linter/type-checker configured in the project itself
`ruff`/`mypy` were installed and run ad hoc for this audit (see `SECURITY_AUDIT.md`/
`TEST_REPORT.md`) but are not part of `pyproject.toml`'s `dev` extra or any CI
configuration — because no CI exists in this repository at all (see `RELEASE_READINESS.md`).
Every finding from this pass is fixed or documented, but nothing currently prevents
regression on the next change. **Not fixed**: adding a permanent lint/type-check config and
CI pipeline is a real, valuable next step, but is itself a process/tooling addition beyond
"harden what exists" — flagged here rather than added unilaterally without the user
confirming they want an enforced lint/CI policy going forward.

### Two independent, ungoverned domains have no policy coverage at all
`PYTHON_EXECUTE` has zero governance policy applied to it — arbitrary Python code
(`os.system(...)`, `shutil.rmtree(...)`) runs completely unchecked. See `SECURITY_AUDIT.md`
for the full reasoning on why this was deliberately not given a fake/weak fix.
