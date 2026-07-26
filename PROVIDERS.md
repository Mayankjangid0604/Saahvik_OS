# Providers

EnterpriseOS has two independent provider platforms, both built on the same pattern:
a capability enum, a registry, a router, and self-registering concrete implementations.

## Tool Providers (`src/enterprise_os/providers/tools/`)

- **`ToolCapability`** (`capability.py`) — the enum: `FILE_READ`, `FILE_WRITE`, `FILE_LIST`,
  `SHELL_EXECUTE`, `PYTHON_EXECUTE`, `GIT_EXECUTE`, `BROWSER_NAVIGATE`, `BROWSER_CLICK`,
  `BROWSER_READ`.
- **`ToolProvider`** (`provider.py`) — the `Protocol` every implementation satisfies:
  `name`, `capabilities: list[ToolCapability]`, `execute(request: ToolRequest) ->
  ToolResponse`.
- **`ToolRegistry`** (`registry.py`) — `register_provider()`, `get_provider(name)`,
  `list_providers()`, and `auto_discover(module_name, **kwargs)`, which reflects over a
  package (in practice, `providers.tools.implementations`), instantiates any class exposing
  `name`/`capabilities`/`execute` whose constructor's required parameters it can satisfy
  from `**kwargs`, and registers it. This is how `ceo_api.py` wires up all five
  implementations from a single call:
  `tool_registry.auto_discover('enterprise_os.providers.tools.implementations', workspace_root=".")`.
- **`ToolRouter`** (`router.py`) — `route(capability)` linear-scans registered providers for
  one whose `capabilities` contains the requested enum member; raises `ToolNotFoundError` if
  none do.

### Implementations (`implementations/`)

| Provider | Capabilities | Notes |
|---|---|---|
| `FilesystemProvider` | `FILE_READ`, `FILE_WRITE`, `FILE_LIST` | Confined to `workspace_root` via `Path.is_relative_to()` (hardened in v1.0 — see `SECURITY.md`). |
| `ShellProvider` | `SHELL_EXECUTE` | `subprocess.run(shell=True)`; gated by `CommandRestrictionPolicy` (see `GOVERNANCE.md`). |
| `PythonProvider` | `PYTHON_EXECUTE` | Executes Python scripts. |
| `GitProvider` | `GIT_EXECUTE` | Git command execution. |
| `BrowserProvider` | `BROWSER_NAVIGATE`, `BROWSER_CLICK`, `BROWSER_READ` | Browser automation. |

A `ToolRequest.tool_name` is always the enum member's `.name` (e.g. `"FILE_READ"`), set by
whichever `ToolPort` implementation constructs the request (`LiveToolPort`/
`PolicyEnforcedToolPort` in `ceo_api.py`) — never a free-form string. Providers match on
these exact uppercase names.

## AI Providers (`src/enterprise_os/providers/ai/`)

- **`Capability`** (`capability.py`) — the enum: `GENERAL_CHAT`, `REASONING`,
  `DEEP_REASONING`, `CODING`, `DEBUGGING`, `PLANNING`, `ARCHITECTURE`, `RESEARCH`,
  `SUMMARISATION`, `EXTRACTION`, `CLASSIFICATION`, `EMBEDDING`, `TOOL_SELECTION`,
  `REFLECTION`.
- **`AIProvider`** (`provider.py`) — the `Protocol`: `name`, `health()`, and
  `chat`/`generate`/`analyse`/`summarise`/`embed(request: AIRequest) -> AIResponse`.
- **`ModelRegistry`** (`registry.py`) — `register_provider`/`register_model`, `get_model`,
  `get_provider`, `list_models`.
- **`AIRouter`** (`router.py`) — `route(capability) -> AIExecutionPlan`. Filters registered
  models by capability support, `AIConfig`'s per-capability `PolicyRule` (local-only,
  minimum context window, JSON/tool support, health), scores survivors (preferred-model
  bonus + context-window size), and falls back to `AIConfig.fallback_models` if nothing
  qualifies. Raises `RoutingError` if nothing works at all.

### `OllamaProvider` (`ollama_provider.py` + `ollama_client.py`)

The only live AI backend. `discover_models()` calls the Ollama `/api/tags` endpoint and
derives rough capability sets from model name heuristics (e.g. `"coder"` in the name adds
`CODING`/`DEBUGGING`/`ARCHITECTURE`; `"deepseek-r1"` or `"reasoning"` adds
`REASONING`/`DEEP_REASONING`/`PLANNING`). `chat`/`generate`/`analyse`/`summarise` all route
through a shared `_execute()` that expects `request.metadata["model_name"]` to be set.
Failures surface as `ProviderUnavailableError`.

### `LiveAIPort` (`interfaces/api/ceo_api.py`)

The `AIPort` implementation `ReasoningLoop`/`WorkerLoop` actually use in the running app:
`request_capability(capability, prompt, ...)` calls `router.route(capability)`, looks up the
provider by `plan.provider_name`, builds an `AIRequest`, and calls `provider.generate()`.
As of v1.0 this is real — earlier it ignored the router entirely and returned scripted text
keyed on prompt substrings (see `V1_RELEASE_PLAN.md` P1-4 for the fix and its disclosed
testing limitation: no live Ollama server has been exercised against this code in CI/dev so
far — validate against a real instance before depending on it in production). Routing or
provider failures are caught and turned into an `AIResponse` with an `AI_PROVIDER_ERROR:`
marker rather than raised, so a down AI backend degrades the same way a malformed response
does (gracefully, into `SEEK_APPROVAL`) instead of crashing the reasoning loop.

## Provider isolation

Both platforms are in-process — there's no sandboxing between "providers" beyond what
`WorkspaceConfinementPolicy`/`CommandRestrictionPolicy` enforce for tools, or what
`ProviderUnavailableError` handling provides for AI backends. See `SECURITY.md`.
