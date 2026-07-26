# EnterpriseOS

EnterpriseOS is a Digital CEO operating system. It is not a chatbot, agent swarm,
workflow engine, or hardcoded company simulator.

The CEO is the only permanent intelligent entity. The Founder/Owner always has authority
above the CEO, and the CEO must request approval before financial, privacy sensitive,
legal, destructive, or irreversible actions — enforced today by a real, tested governance
gate: a failed step resolves to a queued approval, not a silent stall (see
[`GOVERNANCE.md`](GOVERNANCE.md)).

## What actually exists (v1.0 RC)

A FastAPI reasoning-loop server (`enterprise_os.interfaces.api.ceo_api:app`) drives the
real, current execution path:

`Goal → Plan (via a real or gracefully-degrading AI backend) → WorkItem → governed tool
execution → Decision (PROCEED or a queued, resolvable SEEK_APPROVAL) → reflection`

This is not aspirational — it's tested end-to-end, including the failure/degradation paths,
and hardened against a real, reproduced set of bugs and security issues across two audit
passes. See:

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — how the pieces fit together
- [`RUNTIME.md`](RUNTIME.md) — the reasoning loop's state machine
- [`WORKERS.md`](WORKERS.md) — how a step becomes a tool call
- [`PROVIDERS.md`](PROVIDERS.md) — the AI and tool provider platforms
- [`GOVERNANCE.md`](GOVERNANCE.md) — the policy engine and approval queue
- [`API.md`](API.md) — the REST/WebSocket surface
- [`SECURITY.md`](SECURITY.md) — what's hardened and what's a disclosed, open limitation
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — how to actually run it, including the entrypoints that
  are easy to conflate
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — dev setup and conventions

## Project status and audit trail

This codebase has been through two evidence-first hardening passes — nothing here is
asserted without a passing test, a reproduced exploit, or a measurement:

- [`CURRENT_STATE.md`](CURRENT_STATE.md) — the living architectural audit
- [`V1_RELEASE_PLAN.md`](V1_RELEASE_PLAN.md) / [`V1_RELEASE_REPORT.md`](V1_RELEASE_REPORT.md) — round 1
- [`TECHNICAL_DEBT.md`](TECHNICAL_DEBT.md) / [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md) /
  [`PERFORMANCE_REPORT.md`](PERFORMANCE_REPORT.md) / [`TEST_REPORT.md`](TEST_REPORT.md) /
  [`RELEASE_READINESS.md`](RELEASE_READINESS.md) / [`FINAL_RELEASE_REPORT.md`](FINAL_RELEASE_REPORT.md) — round 2
- [`RELEASE_NOTES.md`](RELEASE_NOTES.md) — the changelog across both passes

Known, disclosed limitations (not hidden) are listed in `SECURITY.md` and
`RELEASE_READINESS.md` — most notably that `PYTHON_EXECUTE` has no governance policy
coverage by design (a naive blocklist would be worse than none — see `SECURITY_AUDIT.md`
SEC-11), and that no CI pipeline currently exists in this repository.

## A separate, earlier cognitive-loop entrypoint

`python main.py` boots a different, earlier "Digital CEO" cognitive loop
(`bootstrap/ceo_bootstrap.py`) built for the 8 "milestone" domain orchestrators
(strategy, operations, organisation, research, knowledge, optimisation, growth, evolution).
It predates the FastAPI reasoning loop above, reads its own config files directly, and does
**not** share an execution path with it — see `DEPLOYMENT.md` for the full explanation of
both entrypoints and why they shouldn't be conflated.
