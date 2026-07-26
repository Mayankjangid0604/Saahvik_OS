# API

The REST/WebSocket API is defined in `src/enterprise_os/interfaces/api/ceo_api.py`, a single
FastAPI app assembled procedurally at module import time (see `ARCHITECTURE.md` — there's no
DI container).

## Authentication

As of v1.0, the three governance-sensitive endpoints (submitting goals; listing and
resolving approvals) are gated by a `require_api_token` dependency:

- If the environment variable `ENTERPRISE_OS_API_TOKEN` is **unset**, these endpoints are
  open — a deliberate default for local, single-owner use, not a silent gap.
- If it **is** set, requests must include `Authorization: Bearer <token>` or get `401
  Unauthorized`.

`GET /health`, the WebSocket endpoint, and the static dashboard mount are intentionally
**not** gated (health checks and static assets don't need auth; WebSocket auth is a
separate, larger concern not addressed in this pass — see `SECURITY.md`).

## Endpoints

### `POST /ceo/goal` 🔒
Submit a goal. Runs `ReasoningLoop.execute_goal()` as a FastAPI background task (a worker
thread, not the event loop — relevant to how events reach the WebSocket, see `RUNTIME.md`).

Request body (`GoalRequest`): `{"id": "string", "description": "string"}`

Response: `{"message": "Goal accepted", "session_id": "<uuid>"}` — immediately, before
execution completes. Track progress via the WebSocket event stream or by polling
`GET /approvals`.

### `GET /approvals` 🔒
List pending approvals: `{"pending_approvals": [ApprovalItem, ...]}`. An `ApprovalItem` has
`id`, `justification`, `context`, `status` (`PENDING`/`APPROVED`/`REJECTED`), `feedback`.

### `POST /approvals/{approval_id}` 🔒
Resolve a pending approval.

Request body (`ApprovalDecision`): `{"approved": true|false, "feedback": "string"}`

Response: `{"message": "Approval resolved"}`, or `400` with the error detail if the
`approval_id` doesn't exist or is already resolved.

### `GET /health`
`{"status": "healthy"}`. No auth, no dependencies checked (it does not verify the AI backend
or tool providers are actually working — it's a liveness check, not a readiness check).

### `WS /ceo/events/ws`
Streams every dispatched runtime event as JSON: `{"type": "<EventClassName>", "data":
{...}}`. Backed by `EventStreamer`, which (as of v1.0) actually receives every event — this
was silently broken before v1.0 (see `RUNTIME.md`/`V1_RELEASE_PLAN.md` P0-4) — and is
thread-safe against events dispatched from the background-task thread that runs goal
execution (P1-2).

### `GET /` and static paths
Serves the dashboard (`interfaces/web/`) — a vanilla-JS chat/event UI consuming the
WebSocket stream.

## What's not here

There's no `TestClient`/`httpx`-based integration test suite exercising these routes over
HTTP in this repo yet (unit tests cover the auth dependency and `LiveAIPort` logic directly,
and `scripts/perf_baseline.py` exercises `/health` and `/` over real HTTP for latency
measurement, but not a full request/response contract test suite) — a reasonable next step,
noted rather than silently skipped. There's also no rate limiting, no request size limits
beyond FastAPI/Pydantic defaults, and no CORS configuration.
