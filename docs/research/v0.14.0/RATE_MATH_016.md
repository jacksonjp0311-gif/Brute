# Study-016 rate math (BRUTE_PLAN_016 stop_rule)

Written before the held-out run, from smoke seeds only. Timings: `results/smoke-016/RATE_TIMINGS_016.json`
(15 cases: smoke seeds 8290001 / 03 / 05 / 07 / 16, one per family, masks 0.1 / 0.35 / 0.6, single process,
measured on the box while one GTI smoke run was going).

| Quantity | Value | Label |
|---|---|---|
| Mean main case (transfer, all 11 arms + 72 stress pairs) | 3.119 s | Observed (12 smoke cases) |
| Mean ood5 case | 0.330 s | Observed (3 smoke cases) |
| Mean reference audit per main case | 14.479 s | Observed (12 smoke cases) |
| Mean reference audit per ood5 case | 3.363 s | Observed (3 smoke cases) |

## Projections (×1.5 contention margin, as study-015)

| Stream | Work | Workers | Projected wall | ×1.5 | Budget | Fraction | Label |
|---|---|---|---|---|---|---|---|
| transfer | 360 × 3.119 + 72 × 0.330 = 1147 s | 4 | 287 s | 430 s | 3000 s | 0.14 | Inferred |
| repro | 120 × 3.119 + 24 × 0.330 = 382 s | 2 | 191 s | 287 s | 1500 s | 0.19 | Inferred |
| g11 (plan: 2 workers) | 360 × 14.479 + 72 × 3.363 = 5455 s | 2 | 2727 s | 4091 s | 2400 s | **1.70** | Inferred |
| g11 (deviation #76: 4 workers) | 5455 s | 4 | 1364 s | 2045 s | 2400 s | 0.85 | Inferred |
| gti | the 015 smoke took about 2384 s | 2 | — | — | 3600 s | about 0.66 | Observed (015) |

At the plan's 2 g11 workers, the g11 stream is projected to overrun its 2400 s budget even before the margin, which would
make GS_ref4 FAIL as STUDY_BUDGET for a reason unrelated to the hypothesis. Deviation #76 runs g11 at 4 workers. Worker count
after transfer: gti 2 + repro 2 + g11 4 = 8 = the plan's maximum of 8. The 7200 s cap is unchanged: transfer about 430 s, then g11
about 2045 s, ends near 2500 s after RUN_T0 (Inferred); gti runs in parallel from t0.

## Smoke checks (Observed, smoke seeds only)

- Dry run (`results/smoke-016/SMOKE_DRYRUN_016.json`): RUN_DONE at 41 s; repro 4 / 4 cases byte-identical; reference audit
  10 / 10 cases, 0 mismatches; heartbeat max gap 2.0 s (the watchdog started 12 s after RUN_T0, within the 60 s clause).
- Kill drill (`results/study-016/KILL_DRILL_016.json`): STOP_016 at the 15 s cap, kill latency 0.223 s, no survivors,
  3 process groups, no SIGKILL.
- Reference mutation smoke (`results/smoke-016/REFERENCE_MUTATION_SMOKE_016.json`) and GTI smoke
  (`results/smoke-016/GTI_SMOKE_016.json`): see those files.
