# Deployment

There is currently **no containerization, cloud manifest, or production deployment
tooling** in this repository — the ROADMAP names Docker/cloud-ready manifests as a `v1.0`
goal, but nothing beyond a local Python process exists today. This document describes how
to actually run EnterpriseOS as it exists now, not an aspirational deployment story.

## Running the API server

```bash
pip install -e .
uvicorn enterprise_os.interfaces.api.ceo_api:app --host 0.0.0.0 --port 8000
```

On import, `ceo_api.py` (as a module-level side effect, not behind an explicit startup
function):
- Creates `sessions/` and `logs/` directories relative to the current working directory
  (via `FileSessionRepository()`/`FileAuditLog()` defaults).
- Registers all tool providers found under `providers/tools/implementations/` via
  `ToolRegistry.auto_discover()`, with `workspace_root="."` — i.e. the tool sandbox root is
  the server's current working directory. Run the server from a directory you're comfortable
  giving file/shell tool access to (see `SECURITY.md`).
- Attempts to construct an `OllamaProvider` and discover its models; failures here are
  caught and swallowed (`discover_models()` returns `[]` on error), so the server starts
  fine with no Ollama instance reachable — `LiveAIPort` then degrades gracefully per-request
  instead (see `PROVIDERS.md`).

## Configuration

| Setting | Mechanism | Default |
|---|---|---|
| API auth token | `ENTERPRISE_OS_API_TOKEN` env var | unset (no auth) — see `SECURITY.md` |
| Session storage dir | `FileSessionRepository(storage_dir=...)` constructor arg | `"sessions"` (relative to CWD) — not currently exposed as an env var |
| Audit log dir | `FileAuditLog(log_dir=...)` constructor arg | `"logs"` (relative to CWD) — not currently exposed as an env var |
| Workspace root (tool confinement) | `workspace_root` passed to `auto_discover`/policies in `ceo_api.py` | `"."` — hardcoded, not currently exposed as an env var |

None of the storage-dir/workspace-root values are currently configurable without editing
`ceo_api.py` directly — there's no config-file or env-var indirection for them yet, despite
`config/system.json` existing as a partially-used config file (`runtime_name`, `log_level`,
`loop_interval_seconds` — consumed by the separate `main.py`/`ceo_bootstrap.py` cognitive
loop, not by `ceo_api.py`). Worth flagging as a real gap for anyone trying to run multiple
instances or deploy to a shared filesystem, not glossed over.

## The two separate entrypoints

This repository actually has two independent runnable things that are easy to conflate:

1. **`uvicorn enterprise_os.interfaces.api.ceo_api:app`** — the FastAPI reasoning-loop
   server described above and throughout this doc suite. This is what `RUNTIME.md`,
   `API.md`, `WORKERS.md`, `PROVIDERS.md`, `GOVERNANCE.md` describe.
2. **`python main.py`** — boots a separate "Digital CEO" cognitive loop
   (`bootstrap/ceo_bootstrap.py`, `boot_ceo()`) built for the 8 "milestone" domain
   orchestrators under `domain`/`application/services`. It reads `config/system.json`,
   `config/owner_profile.json`, `config/company_state.json`, `config/memory.json`, and
   `config/constitution.md` directly from the filesystem. This loop is **not** the same code
   path as the FastAPI app's `ReasoningLoop` — they share the domain model's spirit but not
   an execution path. Don't run both expecting them to coordinate; they don't today.

## Demo driver script

`drive_ceo.py` is a demo script that submits a goal to a running API server and polls
`/approvals`. It depends on the `requests` package, which is **not** a core dependency —
install it via the `demo` extra: `pip install -e .[demo]`. (This was an undeclared
dependency gap found and fixed while writing this document — `requests` was imported by
`drive_ceo.py` but listed nowhere in `pyproject.toml`.)

## Development install

```bash
pip install -e .[dev]
pytest
```

See `CONTRIBUTING.md` for the full development workflow.

## Not yet available

- Docker image / Dockerfile
- Any cloud deployment manifest (Kubernetes, ECS, etc.)
- Health-check-based readiness gating (`/health` is a liveness check only — see `API.md`)
- Multi-instance/horizontal-scaling guidance (the file-based session/audit storage and
  hardcoded relative-path directories make this non-trivial as-is)
- Structured application logging configuration beyond the audit log (no log level env var
  wired into `ceo_api.py`, despite `config/system.json` having a `log_level` field that the
  separate `main.py` loop reads)
