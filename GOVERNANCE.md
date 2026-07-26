# Governance

Two independent mechanisms make up governance in EnterpriseOS: the **Policy Engine**, which
gates individual tool executions before they run, and the **Approval Engine**, which queues
whole-goal decisions for a human owner when the executive can't proceed on its own. As of
v1.0, both are actually wired into the runtime — that wasn't always true (see below).

## Policy Engine (`governance/policy_engine.py`)

`PolicyEngine.evaluate(request: ToolRequest) -> (approved: bool, reason: str)` runs every
registered `Policy` in order and short-circuits on the first rejection. It's invoked by
`PolicyEnforcedToolPort.execute_tool()`, which wraps the real `ToolPort` — every tool call
made through `WorkerLoop` passes through this gate before the underlying provider ever runs.

### `WorkspaceConfinementPolicy`

Applies only to `FILE_READ`/`FILE_WRITE`/`FILE_LIST` requests. Resolves the target path
against `workspace_root` and checks `target_path.is_relative_to(workspace_root)`. **v1.0
change:** this used to check `str(target).startswith(str(root))`, a string-prefix pattern —
verified during the v1.0 hardening pass to be a real, working path-traversal bypass (a
sibling directory like `workspace-evil/` passed the check against a `workspace/` root), not
just a theoretical fragility as an earlier audit pass had assumed. Now uses
`Path.is_relative_to()`. Symlink escapes were tested directly and confirmed safe (`.resolve()`
runs before the containment check, so a symlink pointing outside the workspace resolves to
its real, out-of-bounds target and is correctly rejected).

### `CommandRestrictionPolicy`

Applies to both `SHELL_EXECUTE` and `GIT_EXECUTE` requests. **Round-2 fix:** `GitProvider`
runs its `command` argument through `subprocess.run(shell=True, ...)` exactly like
`ShellProvider` does, but this policy originally only ever inspected `SHELL_EXECUTE`
requests — a full, unguarded bypass of the same injection surface, found via `ruff check
--select S602` and reproduced live before fixing (see `SECURITY_AUDIT.md` SEC-1). Both tool
names now share the same gate. **v1.0 change (round 1):** rewritten from a plain substring
blocklist (`if "sudo" in command`) to an argv-aware one: the command is split on
`;`/`&&`/`||`/`|` into the sub-commands it could actually invoke, each parsed with
`shlex.split()`, and the *actual invoked executable name* (path-stripped) is checked against
a forbidden set (`rm`, `sudo`, `su`, `mkfs`, `chown`, `chmod`, `dd`, `shutdown`, `reboot`,
`halt`, `poweroff`, `kill`, `killall`, `userdel`, `passwd`, `visudo`). Command substitution
(`$(...)`/backticks) is rejected outright, since it can hide a sub-command from this
segment-level view.

**This is a hardened blocklist, not a sandbox — say so plainly.** `ShellProvider` is a
general-purpose shell tool (the CEO/worker use it for arbitrary build/test/file commands),
so a strict argument allowlist would break its intended use. Something like `curl ... | sh`
is **not** blocked by this policy, because `curl` and `sh` are themselves legitimate tools —
closing that class of risk would require real sandboxing (containers, seccomp) or turning
the tool into a fixed-command allowlist, neither of which was in scope for this hardening
pass. See `SECURITY.md`.

## Approval Engine (`governance/approval_engine.py`)

`ApprovalEngine.request_approval(justification, context) -> approval_id` queues an
`ApprovalItem` (`PENDING` by default) and dispatches `ApprovalRequested`.
`resolve_approval(approval_id, approved, feedback)` marks it `APPROVED`/`REJECTED` and
dispatches `ApprovalGranted`/`ApprovalRejected`. `get_pending_approvals()` lists everything
still `PENDING`.

**v1.0 fix — this is the single most important governance fix in this release.** Before
v1.0, `ReasoningLoop` computed a `Decision(SEEK_APPROVAL, ...)` whenever a step failed, but
never actually called `request_approval()` — the engine, the `GET/POST /approvals`
endpoints, and the dashboard's polling all worked in isolation but were never invoked by the
real execution path. A stuck goal was invisible to the owner and unrecoverable without
reading raw event logs. `ReasoningLoop` now takes an `approval_engine` and calls
`request_approval()` in the `SEEK_APPROVAL` branch, storing the resulting `approval_id` in
`session.context.memory["pending_approval_id"]`. See `V1_RELEASE_PLAN.md` P0-2.

## What triggers `SEEK_APPROVAL` today

Only one condition: at least one `Step` in the current plan has `StepStatus.FAILED` by the
time the loop reaches `DECIDING`. That covers both "the worker failed to execute a tool" and
"the AI's planning response couldn't be parsed" (which — as of v1.0's P1-3 fix — is marked
`FAILED` up front rather than silently substituted with a fake runnable step). There is
**no** proactive approval gate today for "this action is inherently risky" (e.g. a
`SHELL_EXECUTE` that passes the command policy but is still destructive, or a large
`FILE_WRITE`) — approval is reactive (something already failed), not preventive. The
README's stated intent — "the CEO must request approval before financial, privacy
sensitive, legal, destructive, or irreversible actions" — is not yet fully realized; that
would require classifying actions by risk *before* execution, which doesn't exist in this
codebase yet. Worth tracking as real future work, not glossed over as done.

## API surface

`GET /approvals` and `POST /approvals/{approval_id}` (see `API.md`) are the human owner's
interface to this queue. Both are gated by the same bearer-token auth as goal submission —
see `API.md`/`SECURITY.md`.
