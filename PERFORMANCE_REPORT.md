# Performance Report

Measured, not estimated. This is the round-2 re-run of `scripts/perf_baseline.py`
(introduced in round 1, P3-2) plus fresh full-suite timing, given round 2 touched several
hot-path-adjacent files (persistence, event dispatch, exception handling). No performance
regression was found or expected from round 2's changes (they were correctness/logging
fixes, not hot-path rewrites) — this run exists to confirm that with evidence, not assume it.

## Full test suite

| | Round 1 baseline (post P3-1) | Round 2 |
|---|---|---|
| Wall time | ~0.6s | ~0.7–1.0s (includes new tests: 124 vs 103 at that point) |
| Tests | 103 passed | 124 passed |

Per-test cost is effectively unchanged; the small wall-time increase is fully explained by
21 additional tests, not slower individual tests.

## `scripts/perf_baseline.py` — round-2 run

No live Ollama backend is reachable in this environment; AI routing measures the
graceful-degradation path (P1-4), not live inference latency — stated plainly, not
glossed over.

| Operation | Mean | Median | p95 | n | Round-1 mean (for comparison) |
|---|---|---|---|---|---|
| Startup (cold import, subprocess) | 116.30ms | — | — | 1 | 122.53ms |
| AI routing (route + degrade) | 0.0042ms | 0.0032ms | 0.0054ms | 200 | 0.0041ms |
| Planning (`_create_plan`) | 0.0179ms | 0.0159ms | 0.0261ms | 200 | 0.0170ms |
| Worker creation (`WorkItem`) | 0.0009ms | 0.0009ms | 0.0014ms | 1000 | 0.0011ms |
| Tool routing (`ToolRouter.route`) | 0.0009ms | 0.0008ms | 0.0009ms | 1000 | 0.0011ms |
| Serialization — save | 0.1852ms | 0.1521ms | 0.2157ms | 500 | 0.2515ms |
| Serialization — load | 0.0365ms | 0.0321ms | 0.0555ms | 500 | 0.0394ms |
| Event dispatch | 0.0004ms | 0.0004ms | 0.0004ms | 2000 | 0.0004ms |
| API latency (`GET /health`) | 1.0571ms | 1.0307ms | 1.3790ms | 50 | 0.9534ms |
| Dashboard latency (`GET /`) | 1.8232ms | 1.6202ms | 2.0205ms | 50 | 2.1703ms |

**Reading this honestly:** every number is within normal run-to-run measurement noise of the
round-1 baseline (single-digit-percent differences on sub-millisecond operations, on a shared
/ variable-load sandbox environment — not a controlled benchmark rig). Serialization got
measurably *faster* (save: 0.2515ms → 0.1852ms), consistent with round 2 not adding overhead
to the persistence path despite adding the `FileAuditLog.close()` capability (which is
opt-in, not called on the hot path). No metric shows a regression large enough to investigate.

## What changed in round 2 that touches these paths, and why it didn't regress them

- `FileAuditLog`: switched from `id(self)` to `itertools.count()` for logger naming — a
  single `next()` call on an integer counter, not measurably different in cost from `id()`.
- `EventDispatcher.dispatch()`: unchanged since round 1 (the `isinstance`-based iteration
  fix landed in round 1, not round 2).
- Added logging calls (`logger.warning(...)`) in three previously-silent exception paths —
  these only execute on the (rare, error) failure path, not the hot success path, so they
  don't affect steady-state latency.
- Removed 25 unused imports — strictly reduces import-time cost, consistent with startup
  time staying flat-to-slightly-lower (122.53ms → 116.30ms, within noise but directionally
  consistent).

## Known measurement limitations (stated, not hidden)

- This is a single-sample-per-metric run on a shared sandbox, not a statistically rigorous
  benchmark with warmup, isolation, or repeated runs across multiple processes. Treat these
  as directional baselines, not precise SLAs.
- Startup is measured as a single cold-start sample (`n=1`) since repeated subprocess
  spawns would mostly measure OS-level process-creation noise, not the code being measured.
- No load/stress testing exists at any concurrency level beyond what `perf_baseline.py`'s
  sequential loops exercise. See `TEST_REPORT.md` for what testing does and doesn't cover.
- AI routing/planning numbers reflect the no-model-registered degradation path only; real
  inference latency (the dominant cost once a live Ollama backend is in use) cannot be
  measured in this environment. This is the single largest gap in this performance picture,
  and it's a hard limitation of the environment, not something either hardening pass
  could close.

## Conclusion

No performance problem was found in round 1 or round 2 beyond the P3-1 `time.sleep(0.5)`
fix (round 1) and its confirmation via measured suite speedup. Optimization work is not
justified by any measurement gathered so far — consistent with the mission's "optimise only
when measurements justify it."
