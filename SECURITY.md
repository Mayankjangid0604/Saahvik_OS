# Security

This document is the honest, evidence-based security posture of EnterpriseOS v1.0 — what
was verified, what was fixed, and what remains a real, disclosed limitation rather than an
overclaimed non-issue. It has been through two hardening passes now; the underlying
investigation for every item below (including cases where an earlier claim in this
project's own audit turned out to be wrong on actual testing) is recorded in full in
[`SECURITY_AUDIT.md`](SECURITY_AUDIT.md), which is the definitive working record — this
file is the operator-facing summary.

## Fixed in v1.0

**Workspace path traversal (was a real, working exploit, not a theoretical one).**
`WorkspaceConfinementPolicy` and `FilesystemProvider._resolve_safe_path()` used to check
`str(target).startswith(str(root))` for containment. A sibling directory like
`workspace-evil/` next to `workspace/` passes that check, because
`"/workspace-evil/x".startswith("/workspace")` is `True` in plain string terms. This was
tested directly and confirmed to actually leak a sibling directory's file contents through
`FilesystemProvider.execute()`. Fixed to use `Path.is_relative_to()`. Symlink escape was
also tested directly (not just reasoned about) and confirmed safe: `.resolve()` runs before
the containment check, so a symlink pointing outside the workspace resolves to its real
target and is correctly rejected.

**Shell command policy hardened against blocklist bypass.** `CommandRestrictionPolicy` used
to block 5 fixed substrings (`rm -rf`, `sudo`, `mkfs`, `chown`, `chmod`) via plain `in`
checks against the raw command string passed to `subprocess.run(shell=True)`. Trivially
bypassed by whitespace variants, absolute paths, or chaining a forbidden command after an
allowed one. Now parses each `;`/`&&`/`||`/`|`-separated segment with `shlex` and checks the
actual invoked executable name; rejects command substitution (`$(...)`/backticks) outright.
**This is still a blocklist, not a sandbox — see "Known, disclosed limitations" below.**

**`GIT_EXECUTE` fully bypassed the above (round 2).** `GitProvider` runs its `command`
argument through `subprocess.run(shell=True, ...)` exactly like `ShellProvider`, but
`CommandRestrictionPolicy` originally only ever checked `SHELL_EXECUTE` requests — a
complete, unguarded duplicate of the same injection surface. Found via static analysis
(`ruff check --select S602`) and reproduced live: a command blocked when routed as
`SHELL_EXECUTE` sailed through unchecked when routed as `GIT_EXECUTE`. Fixed by widening the
policy to gate both tool names. See `GOVERNANCE.md`.

**An orphaned, fully ungoverned third API surface existed and was deleted (round 2).**
`interfaces/api/main.py` was a separate FastAPI app with hardcoded/mocked responses, zero
authentication, and zero policy enforcement — unreferenced by any import, test, script, or
doc anywhere in the repository. Deleted; see `TECHNICAL_DEBT.md`.

**No API authentication → bearer-token gate.** `/ceo/goal`, `/approvals`, and
`/approvals/{id}` (approve/reject!) were completely unauthenticated. Now gated by
`require_api_token` when `ENTERPRISE_OS_API_TOKEN` is set. See `API.md`.

**Audit log integrity bug.** `FileAuditLog` used a fixed, process-wide logger name, so the
first instance constructed in a process would silently claim the shared handler and every
later instance would write to *its* log directory regardless of its own. Fixed by scoping
the logger name per instance. This matters for the "audit integrity" checklist item because
a multi-instance process (or anything that constructs `FileAuditLog` more than once) could
otherwise lose audit events to the wrong file, or silently.

**Approval bypass (the governance gate was disconnected, not just imperfect).**
`ReasoningLoop` computed `SEEK_APPROVAL` decisions but never called
`ApprovalEngine.request_approval()` — the approval queue the dashboard and `/approvals`
API depend on was never populated by real execution. See `GOVERNANCE.md`.

## Known, disclosed limitations (not fixed — stated plainly, not hidden)

- **`PYTHON_EXECUTE` has zero policy coverage at all (round 2, high severity, deliberate).**
  Reproduced live: `PolicyEngine.evaluate()` approves a `PYTHON_EXECUTE` request whose script
  is `"import os; os.system('rm -rf /tmp/x')"` unconditionally. `PythonProvider` executes
  arbitrary Python, which is at least as powerful as unrestricted shell access. **This was
  not given a blocklist-style fix on purpose**: unlike shell commands, Python source is
  trivially able to defeat string/AST-based blocklisting via its own introspection
  (`__import__('o'+'s')`, dynamic `getattr` on builtins, etc.), so a naive check would create
  a false sense of security while adding real complexity and false positives — assessed as
  worse than no check at all. A real fix requires actual sandboxing (a restricted execution
  environment or container/seccomp isolation), out of scope for a hardening pass explicitly
  instructed not to redesign the architecture. See `SECURITY_AUDIT.md` SEC-11 for the full
  reasoning.
- **`CommandRestrictionPolicy` is an executable-name blocklist, not a full shell sandbox.**
  `curl ... | sh`, `python -c "import os; os.remove(...)"`, or any destructive action
  performed through a generically "safe" interpreter is still possible. Closing this would
  require real sandboxing (containers, seccomp) or turning `ShellProvider` into a
  fixed-command allowlist — a change to what the tool fundamentally is, out of scope for a
  hardening pass that's explicitly not meant to redesign the architecture.
- **No worker/process isolation.** Tool execution (including arbitrary shell commands) runs
  directly on the host process, gated only by the policies above. There is no
  container/VM/restricted-user boundary. See `WORKERS.md`.
- **No proactive, risk-based approval gate.** Approval is currently reactive — it only
  triggers after a step has already failed, not before a classified-as-risky action (e.g. a
  large file write, a destructive-looking but policy-legal shell command) is attempted. See
  `GOVERNANCE.md`.
- **Prompt injection surface, now live rather than theoretical.** `GoalRequest.description`
  is free text with no length or content validation, and flows directly into AI prompts.
  Before v1.0, `LiveAIPort` was scripted, so this was a theoretical concern; as of v1.0
  (`LiveAIPort` now calls a real model, see `PROVIDERS.md`), it's a real one. Not addressed
  in this pass.
- **No WebSocket authentication.** `WS /ceo/events/ws` streams every runtime event to any
  connection; it is not gated by `require_api_token`. Explicitly out of scope for the P2-3
  auth work (which targeted the three REST endpoints named in the original audit finding) —
  not an oversight, but also not solved.
- **No rate limiting, request size limits, or CORS configuration** beyond FastAPI/Pydantic
  defaults.
- **`FileSessionRepository` persists to plain JSON files with no encryption, ACID
  guarantees, or access control** beyond filesystem permissions. Session recovery (P0-3,
  P1-6) restores state/memory/plan correctly, but the storage layer itself is an MVP.

## Verified-safe, not just assumed

- Symlink escape from the workspace (see above) — tested with a real exploit attempt, not
  just read and reasoned about.
- The path-traversal fix and the command-policy hardening both have dedicated regression
  tests reproducing the exact bypass strings found during the v1.0 audit
  (`tests/unit/governance/test_workspace_confinement_policy.py`,
  `tests/unit/governance/test_command_restriction_policy.py`,
  `tests/unit/providers/tools/test_filesystem_provider.py`).

## Reporting

There is no formal security disclosure process for this project yet. If you find an issue,
open one against the repository with clear reproduction steps.
