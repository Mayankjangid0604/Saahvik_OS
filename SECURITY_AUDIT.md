# Security Audit

This is the definitive, evidence-based security audit as of the round-2 hardening pass. It
supersedes the security narrative scattered across `CURRENT_STATE.md`/`V1_RELEASE_PLAN.md`
for round-1 findings and adds everything found in round 2. Every finding below was either
reproduced with a live exploit attempt or explicitly marked as reasoned-but-unverified — the
two are never conflated. See `SECURITY.md` for the operator-facing summary; this document is
the working audit record.

## Methodology

- **Static analysis**: `ruff check` with a bug/security-focused ruleset
  (`E,F,B,S,ASYNC,C4,SIM,RUF` — the `S` prefix is bandit-equivalent security rules), not the
  maximal `--select ALL` (which is dominated by docstring/style rules and produces ~2,977
  findings of near-zero signal for this codebase).
- **Dependency audit**: `pip-audit` against the actual installed environment.
- **Live reproduction**: every claimed exploit or bypass was demonstrated against the real
  code with a minimal Python repro before being called "confirmed," not inferred from
  reading.

## Findings — Fixed

### SEC-1 (round 2, high) — `GIT_EXECUTE` completely bypassed `CommandRestrictionPolicy`
`GitProvider.execute()` runs `subprocess.run(command, shell=True, ...)` — the identical
injection surface as `ShellProvider` — but `CommandRestrictionPolicy.evaluate()` only ever
inspected `SHELL_EXECUTE` requests. **Reproduced live**: a command policy-blocked when routed
as `SHELL_EXECUTE` (`"rm -rf /tmp/x"`) sailed through unchecked when routed as `GIT_EXECUTE`
(`"log; rm -rf /tmp/x"`). Found via `ruff check --select S602` surfacing the `shell=True`
call site, which prompted checking whether it shared the same policy gate as `ShellProvider`
— it didn't. Fixed by widening `CommandRestrictionPolicy`'s `GATED_TOOL_NAMES` to include
both. See `tests/unit/governance/test_command_restriction_policy.py`.

### SEC-2 (round 1, critical) — Real, working path-traversal exploit in workspace confinement
`WorkspaceConfinementPolicy`/`FilesystemProvider._resolve_safe_path()` used
`str(target).startswith(str(root))`. A sibling directory (`workspace-evil/` next to
`workspace/`) passed this check. **Reproduced live**: confirmed `FilesystemProvider.execute()`
actually returned a sibling directory's file contents before the fix. This was originally
mis-classified as "not exploitable" by an earlier, untested audit pass — corrected on
re-verification. Fixed via `Path.is_relative_to()`.

### SEC-3 (round 1, high) — Shell command policy was a trivially bypassable substring blocklist
Whitespace variants, absolute paths, and command chaining all defeated the original 5-string
substring check. Hardened to an argv-aware, per-segment executable-name check (see
`SECURITY.md` for the exact mechanism and its residual scope).

### SEC-4 (round 1, high) — Governance approval loop was completely disconnected
`ReasoningLoop` computed `SEEK_APPROVAL` but never called `ApprovalEngine.request_approval()`
— not a vulnerability in the traditional sense, but a governance-bypass in effect: risky
outcomes never actually reached the human approval gate the product's stated design depends
on. Fixed by wiring the call through.

### SEC-5 (round 1, high) — API endpoints were completely unauthenticated
`/ceo/goal`, `/approvals`, `/approvals/{id}` (approve/reject!) had no auth. Fixed with a
bearer-token gate, opt-in via `ENTERPRISE_OS_API_TOKEN`.

### SEC-6 (round 1, medium) — WebSocket dashboard event stream was silently non-functional
Not a confidentiality/integrity issue, but an availability/observability one:
`EventDispatcher.dispatch()` matched by exact type, so the dashboard's wildcard event
subscription never received anything. An operator watching the dashboard for signs of a
problem would see nothing, ever — a false sense of visibility. Fixed via `isinstance`-based
dispatch.

### SEC-7 (round 2, medium) — Audit log integrity: cross-instance handler sharing, twice
First occurrence (round 1, P1-7): a fixed logger name meant the first `FileAuditLog`
instantiated in a process claimed the shared handler; every later instance silently wrote to
*its* log directory. Fixed by scoping the logger name with `id(self)`.

Second occurrence (round 2, found during this audit, in the round-1 fix itself): `id(self)`
is only unique among simultaneously-alive objects, not across time — a tight
construct-and-discard pattern lets CPython reuse a freed instance's memory address, so a
later instance can collide with an earlier one's `id()` and silently inherit its logger and
handler. **Reproduced live**: a 50-iteration construct-and-discard loop followed by a normal,
held instance showed the held instance's audit event leaking into the churned instances' log
directory. Fixed by switching to a monotonic `itertools.count()`, which has no
collision-under-churn risk. Also added `FileAuditLog.close()` for callers that need to
release the handler deterministically.

### SEC-8 (round 2, low) — Missing validation: `OllamaProvider.embed()` didn't check `model_name`
Unlike `_execute()` (used by chat/generate/analyse/summarise), `embed()` never validated
`request.metadata.get("model_name")` was present before use — a missing value would fail
deep inside the HTTP client with a confusing error rather than a clear `ValueError`. Found
via mypy (`Any | None` passed where `str` was required). Fixed with the same guard
`_execute()` already has.

### SEC-9 (round 2, low) — Silent exception swallowing across three call sites
`ToolRegistry.auto_discover()`, `ceo_api.py`'s Ollama model discovery, and
`EventStreamer._handle_event()` all had bare `except Exception: pass`. None were exploitable
vulnerabilities on their own, but each meant a real failure (a broken tool provider, a
malformed event, an Ollama registration error) would be invisible with zero trace — which
matters for incident response and audit completeness. All three now log at `warning` level
with `exc_info=True`.

### SEC-10 (round 2, low) — Orphaned, ungoverned third API surface
`interfaces/api/main.py` was a separate FastAPI app with zero auth and zero policy
enforcement, unreferenced anywhere in the repo. An unreferenced-but-present, unauthenticated,
mocked "CEO API" is itself a liability if ever accidentally deployed. Deleted (see
`TECHNICAL_DEBT.md`).

### SEC-17 (round 2, high) — Local file disclosure / SSRF via `BrowserProvider`
`BrowserProvider.execute()` passed `request.arguments["url"]` straight to
`urllib.request.urlopen()` with zero scheme validation. Found via `ruff check --select S310`.
**Reproduced live**: a `file://` URL let the tool read an arbitrary local file (confirmed
reading `/etc/hostname`) and return its contents as the tool result — also a classic SSRF
vector via other schemes (e.g. reaching internal-network or cloud-metadata endpoints).
Fixed with an http(s)-only scheme allowlist checked before opening the URL. Unlike SEC-11
(`PYTHON_EXECUTE`), this is a **complete** fix, not a partial one: there's no equivalent to
Python's introspection-based blocklist evasion for a URL's literal scheme string. Not
currently reachable through the live `ReasoningLoop` (its `allowed_tools` excludes browser
capabilities), but reachable by anything calling the tool port directly, and no governance
policy covers `BROWSER_NAVIGATE`/`BROWSER_READ` either — fixed at the provider level. Added
`tests/unit/providers/tools/test_browser_provider.py` (this provider had zero prior tests).

**Related, reviewed, not changed:** the same `S310` rule also flags 6 `urlopen()` call sites
in `ollama_client.py`. Reviewed and left as-is: `OllamaClient`'s `base_url` is only ever
constructed from a hardcoded default (`ceo_api.py:167`, `OllamaClient()` with no arguments)
— no request- or tool-controlled input reaches it anywhere in the codebase, so unlike
`BrowserProvider`'s directly argument-controlled `url`, there is no reproducible exploit
path here to fix.

## Findings — Open, disclosed, not silently accepted

### SEC-11 (high, by design not oversight) — `PYTHON_EXECUTE` has zero policy coverage
**Reproduced live**: `engine.evaluate(ToolRequest(tool_name="PYTHON_EXECUTE",
arguments={"script": "import os; os.system('rm -rf /tmp/x')"}))` returns `(True, "")` —
completely unchecked. `PythonProvider` executes arbitrary Python via
`subprocess.run(["python", "-c", script])`, and arbitrary Python code can trivially invoke
`os.system`, `subprocess`, `shutil.rmtree`, or anything else — it is at least as powerful as
unrestricted shell access.

**Why this was not given a blocklist-style fix, unlike `CommandRestrictionPolicy`:** a
substring/AST-based blocklist against Python source (`"import os"`, `"eval("`, etc.) would be
trivially defeated by Python's own introspection (`__import__('o'+'s')`,
`getattr(__builtins__, 'ex'+'ec')(...)`, etc.) in a way shell command blocklisting is not,
and would also produce false positives blocking benign scripts that happen to contain common
strings like `"import os"`. Shipping such a check would create a false sense of security
while adding real complexity — assessed as **worse than no check at all**, not better. A
genuine fix requires real sandboxing (a restricted execution environment, AST-validated
subset of Python, or container/seccomp isolation), which is out of scope for a hardening pass
explicitly instructed not to redesign the architecture. Documented here, in `SECURITY.md`,
and in `TECHNICAL_DEBT.md` so it is never mistaken for solved.

### SEC-12 (medium) — `CommandRestrictionPolicy` remains an executable-name blocklist, not a sandbox
Even after SEC-1/SEC-3, `curl ... | sh`, or any destructive action performed through a
generically "safe" interpreter, is not blocked — `curl` and `sh` are themselves legitimate
tools the policy has no reason to forbid outright. Same reasoning as SEC-11: a real fix
requires sandboxing, not a bigger blocklist.

### SEC-13 (low) — No WebSocket authentication
`WS /ceo/events/ws` streams every runtime event to any connection; `require_api_token` was
scoped to the three REST endpoints named in the original finding (SEC-5), not the WebSocket.

### SEC-14 (low) — No proactive, risk-based approval gate
Approval (SEC-4's fix) is reactive — triggered only after a step has already failed — not
preventive. There is no classification of an about-to-run action as "risky enough to require
approval before execution," despite the README's stated design intent. See `GOVERNANCE.md`.

### SEC-15 (low) — Live prompt-injection surface, now real rather than theoretical
`GoalRequest.description` is unbounded free text flowing directly into AI prompts. Before
round 1's P1-4 fix, `LiveAIPort` was scripted, making this a theoretical concern; now that it
calls a real model, it's a real one. Not addressed in either round.

### SEC-16 (informational) — Threading model for shared governance state
See `TECHNICAL_DEBT.md` for `ApprovalEngine`/`EventDispatcher`/`ToolRegistry`'s shared-dict
access across the FastAPI event loop thread and background-task worker threads. Reviewed,
not fixed: CPython's GIL makes this safe from corruption in practice, and no incorrect
behavior was found or reproduced.

## Dependency Audit

`pip-audit` run against the actual installed environment. **Zero vulnerabilities found in any
project-declared dependency**: `fastapi` 0.140.0, `uvicorn` 0.51.0, `requests` 2.34.2,
`pytest` 9.1.1, `pytest-cov` 7.1.0. The only flagged packages (`pip`, `setuptools`) are the
throwaway audit venv's own build tooling, not dependencies this project declares or ships —
irrelevant to the project's actual supply chain.

## Summary Table

| ID | Severity | Status |
|---|---|---|
| SEC-1 GIT_EXECUTE bypass | High | ✅ Fixed |
| SEC-2 Path traversal | Critical | ✅ Fixed |
| SEC-3 Shell blocklist bypass | High | ✅ Fixed |
| SEC-4 Approval loop disconnected | High | ✅ Fixed |
| SEC-5 No API auth | High | ✅ Fixed |
| SEC-6 Dead WebSocket stream | Medium | ✅ Fixed |
| SEC-7 Audit log handler sharing (x2) | Medium | ✅ Fixed |
| SEC-8 embed() missing validation | Low | ✅ Fixed |
| SEC-9 Silent exception swallowing | Low | ✅ Fixed |
| SEC-10 Orphaned ungoverned API | Medium | ✅ Fixed (deleted) |
| SEC-17 Local file disclosure / SSRF (BrowserProvider) | High | ✅ Fixed |
| SEC-11 PYTHON_EXECUTE unrestricted | High | ⚠ Disclosed, not fixed (fake fix would be worse) |
| SEC-12 Shell blocklist residual scope | Medium | ⚠ Disclosed, by design |
| SEC-13 No WebSocket auth | Low | ⚠ Disclosed, out of scope |
| SEC-14 No proactive approval gate | Low | ⚠ Disclosed, design gap |
| SEC-15 Prompt injection surface | Low | ⚠ Disclosed, now live |
| SEC-16 Threading model | Informational | ⚠ Reviewed, accepted |
