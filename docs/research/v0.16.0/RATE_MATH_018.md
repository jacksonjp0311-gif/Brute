# Study-018 rate math (BRUTE_PLAN_018 stop_rule)

Written before the held-out run, using smoke seeds only. The numbers come from `scripts/rate_math_018.py` →
`docs/research/v0.16.0/RATE_MATH_018.json`, fed by smoke dry run 2. Dry run 2 ran the orchestrator with the held-out
stream layout (`SMOKE=1 CAP_S=4000`, 2026-10-27 10:09-10:22 EDT, the full layout on 8 CPUs). A 15 s kill drill also ran
alongside it.

Method: for each stream and each (family, eps) cell, take the slowest smoke case, multiply it by the number of
held-out cases in that cell, and divide by the stream's workers. That is the raw projection. The x1.75 margin covers
contention. A stream fits if its projection with margin is at most 0.8 of its budget. GTI runs the same 635 tests as the
held-out run, so its raw figure is the observed dry-run wall time.

| Stream | Workers | Budget (s) | Raw (s) | x1.75 (s) | Fill | Fits (<= 0.8) | Label |
|---|---|---|---|---|---|---|---|
| transfer (360 main + 120 stress) | 4 | 1800 | 562.5 | 984.3 | 0.547 | yes | Inferred (from Observed smoke) |
| repro (120 = main every 3rd) | 2 | 1200 | 215.6 | 377.3 | 0.314 | yes | Inferred |
| g11 (480 audited) | 2 | 1200 | 334.3 | 585.0 | 0.487 | yes | Inferred |
| gti (635 tests, 10 clean-tag runs) | 4 | 4800 | 772.7 | 1352.2 | 0.282 | yes | Observed raw / Inferred margin |

- **Critical path** (transfer, then repro and g11, alongside gti): 1569 s projected. The budget path is 4800 s and the
  cap is 7200 s. Fits (Inferred).
- **Peak load:** 8 workers at once (4+4, then 4+2+2), which equals the plan's cap.
- **STREAMS:** unchanged from #98 (Exact: `scripts/run_study_018.py`).
- **GTI parallel clean-tag runs (#98), Observed:** the 10 clean-tag children took 103-187 s each, running up to 4 at a time.
  GTI finished in 773 s. Dry run 1, with serialized children, had not finished at 928 s.

## Smoke checks (Observed, smoke seeds only)

- `results/smoke-018/SMOKE_DRYRUN_018.json`:
  - transfer: 32/32 cases in 32 s;
  - repro: 11/11 cases;
  - g11: 32/32 audited, 16/16 gated, 0 mismatching, mutation test included.
- `results/smoke-018/GTI_SMOKE_018.json`: the smoke GTI verdict is FAIL, with 6 undeclared failures.
  - Five are `*test_streams` tests. Each asserts `RS.CAP == 7200` and fails only because the dry run exported
    `CAP_S=4000`. This was reproduced: the same tests pass without `CAP_S` (Observed). The held-out run does not set
    `CAP_S`.
  - The sixth is `test_brute_repro.test_manifest_matches_tracked_files`. Its likely cause is that
    `scripts/make_freeze_018.py` was edited in the working tree while the GTI modules ran (Inferred). It is re-checked on
    the committed tree before the freeze.
- `results/smoke-018/KILL_DRILL_018.json`: the watchdog fired at the 15 s cap.
  - The orchestrator and its stream group were stopped in 0.226 s.
  - No SIGKILL was needed, there were no survivors, and the heartbeat had no gaps over 10 s.

**Disclosed risk (Inferred):** the held-out per-case cost scales with the number of flip-tolerant region solves. Stress
cases (eps 0.05) have the largest m, and smoke covers only 8 of them. A transfer overrun would fail G10 as STUDY_BUDGET.
The budget is not raised.
