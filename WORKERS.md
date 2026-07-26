# Workers

The Worker Runtime (`src/enterprise_os/worker/`) translates one `Step` from the executive's
plan into a concrete tool invocation. It's a much thinner layer than the executive runtime —
one AI call, one tool call, done.

## Flow

`WorkerLoop.execute_work_item(session, work_item) -> StructuredResult`:

1. Builds a prompt listing the `WorkItem`'s `allowed_tools` (by `ToolCapability.name`) and
   the objective, asking the AI (`Capability.TOOL_SELECTION`) to pick one and return strict
   JSON: `{"capability": "CAPABILITY_NAME", "arguments": {...}}`.
2. Parses the response (stripping any ` ```json ` fencing), resolves `capability` via
   `ToolCapability.from_string()`.
3. Rejects the selection if it isn't in `work_item.allowed_tools`
   (`CapabilityResolutionFailed`, returned as a failed `StructuredResult` — this is a
   policy/scope check at the worker level, independent of and in addition to the
   `governance/` policy checks that run when the tool actually executes).
4. Calls `tool_port.execute_tool(selected_capability, tool_args)` and wraps the
   `ToolResponse` into a `StructuredResult`.

Any exception during parsing or execution is caught and returned as a failed
`StructuredResult` with the error in `findings` — the worker loop never lets an exception
propagate up into the executive loop; a failure here becomes a `StepFailed` event and
(as of v1.0) a real, queued approval request, not a crash.

## Data model

- **`WorkItem`** (`worker_models.py`) — `id`, `objective`, `allowed_tools:
  list[ToolCapability]`, `parameters`.
- **`StructuredResult`** — `work_item_id`, `success`, `findings`, `artifacts`.
- **`WorkerSession`** (`worker_session.py`) — `objective` (currently minimal; no
  per-worker-session state beyond this is tracked).

## Where `allowed_tools` comes from today

`ReasoningLoop._execute_step()` currently constructs every `WorkItem` with the same fixed
list: `PYTHON_EXECUTE`, `SHELL_EXECUTE`, `FILE_READ`, `FILE_WRITE`, `FILE_LIST`. There's no
per-step tool scoping yet — every step gets the same broad toolset, and the actual safety
boundary is enforced downstream by the governance policies (workspace confinement, command
restriction), not by narrowing `allowed_tools` per step. If step-level tool scoping is
wanted, `_execute_step()` is the place to change it — this is a real design gap worth
tracking, not something this document should paper over.

## Isolation

There is currently no process/container-level isolation between the worker's tool execution
and the host running EnterpriseOS — `ShellProvider` runs `subprocess.run(..., shell=True)`
directly on the host, gated only by the governance policies described in `GOVERNANCE.md`
and `SECURITY.md`. "Worker isolation" in the sense of a sandboxed execution environment
(container, VM, restricted user) does not exist. This is a known, documented limitation, not
an oversight — see `SECURITY.md` for the full picture and `V1_RELEASE_PLAN.md` P2-1 for what
was and wasn't hardened in v1.0.
