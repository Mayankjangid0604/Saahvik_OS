# Contributing

## Setup

```bash
git clone <repo>
cd Saahvik_OS
pip install -e .[dev]
pytest
```

`pyproject.toml`'s `dev` extra installs `pytest`/`pytest-cov` — everything needed to run the
test suite. There is no linter or type-checker configured in this repository today (no
`ruff`/`mypy`/`flake8` config found anywhere); don't assume one runs in CI.

## Running tests

```bash
pytest                                    # full suite
pytest -q --cov=enterprise_os --cov-report=term-missing   # with coverage
pytest tests/unit/governance/             # a subdirectory
pytest tests/unit/runtime/test_runtime.py -v              # one file, verbose
```

At v1.0: 115 passed, 1 skipped, 91% coverage. See `CURRENT_STATE.md`/`V1_RELEASE_PLAN.md`
for exactly what's covered and what isn't.

Some tests (`tests/unit/interfaces/*`) import `enterprise_os.interfaces.api.ceo_api`, which
has module-level side effects — it creates `sessions/` and `logs/` directories relative to
the current working directory. Both are gitignored; running the suite from the repo root is
expected to leave (empty or near-empty) `sessions/`/`logs/` directories behind. This is a
known, accepted side effect, not a bug to work around.

## Code conventions actually used in this codebase

These are observed conventions from reading the existing code, not aspirational rules —
follow what's already here rather than introducing a new style:

- **Capability enums, not strings, for tool/AI dispatch.** See `ARCHITECTURE.md`. If you're
  adding a new tool or AI capability, add it to `ToolCapability`/`Capability`
  (`providers/tools/capability.py` / `providers/ai/capability.py`) — don't introduce a new
  string-based identifier.
- **Dataclasses for data, `Protocol`/`ABC` for ports.** Domain and DTO types are
  `@dataclass` (often `frozen=True`); interfaces between layers are `Protocol` or `ABC`
  classes in `application/ports/` or alongside the concrete implementations they gate
  (`governance/policy_engine.py`'s `Policy` `Protocol`, `providers/tools/provider.py`'s
  `ToolProvider` `Protocol`).
- **No DI container.** Wiring is explicit and procedural (see `ceo_api.py`). Don't introduce
  one for a small addition — pass dependencies through constructors as the rest of the
  codebase does.
- **Fail loud, not silent, on unparseable/unexpected input** — a v1.0 fix (P1-3) replaced a
  silent-fallback pattern with an explicit `FAILED` status and a dispatched event. If you're
  adding a new parsing/AI-response-handling path, follow that pattern rather than
  reintroducing a silent placeholder.
- **Graceful degradation over exceptions crossing a runtime boundary.** `WorkerLoop` and
  `LiveAIPort` both catch their own internal failures and return a failure-shaped result
  (`StructuredResult`/`AIResponse` with an error marker) rather than letting exceptions
  propagate into `ReasoningLoop`. Match this if you're adding a new provider or port
  implementation that the reasoning loop calls directly.

## Adding a new Tool Provider

1. Add the new capability constant(s) to `ToolCapability` in
   `providers/tools/capability.py`.
2. Create a class in `providers/tools/implementations/` satisfying the `ToolProvider`
   `Protocol`: a `name` property, a `capabilities` property returning the enum members it
   handles, and `execute(request: ToolRequest) -> ToolResponse`.
3. Match on `request.tool_name` against the capability's `.name` (uppercase enum member
   name) — see any existing provider for the pattern.
4. It will be picked up automatically by `ToolRegistry.auto_discover()` at server startup —
   no manual registration needed, as long as its constructor's required parameters are
   satisfiable from the `**kwargs` passed to `auto_discover` (currently just
   `workspace_root`).
5. Add unit tests under `tests/unit/providers/tools/` — the existing provider test files are
   the closest reference for what to cover (success path, and any security-relevant
   boundary the provider enforces).

## Adding a new governance policy

Implement the `Policy` `Protocol` in `governance/policy_engine.py` (a `name` property and
`evaluate(request: ToolRequest) -> (bool, str)`), register it in `ceo_api.py`'s
`policy_engine.register_policy(...)` calls. See `GOVERNANCE.md` and the existing policies in
`governance/policies/` for the pattern, and — given the v1.0 lesson from P2-2 — write a
regression test for the exact bypass you're trying to prevent, not just the happy path.

## Commit/PR expectations

This codebase's v1.0 hardening pass followed a strict discipline worth continuing:
inspect → validate → complete → harden, with tests added or updated alongside every fix,
and the test suite green before considering a change done. See `V1_RELEASE_PLAN.md` for
examples of that process applied to real findings, including two cases where a claim made
earlier in this project's own documentation was re-verified and found wrong — treat
"looks right" and "verified with a test" as different things.
