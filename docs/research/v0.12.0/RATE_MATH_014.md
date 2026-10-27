# Rate math for study-014 (stop_rule.rate_math)

Written before the source freeze and before any held-out seed of BRUTE_PLAN_014 was generated. All timings come from
smoke seeds (7190001-7190015) and are labelled. Projections are Inferred.

## Measurements (Observed, smoke seeds)

| Source | What | Result |
|---|---|---|
| results/smoke-014/RATE_TIMINGS_014.json | 1 case + reference audit, seeds 7190001 / 7190005, one process | case s / audit s: mask 0.1: 1.55 / 5.7, 2.17 / 10.4; mask 0.35: 3.72 / 4.7, 3.00 / 12.9; mask 0.6: 10.41 / 13.1, 4.83 / 27.8 |
| results/smoke-014/SMOKE_DRYRUN_014.json | full orchestrator + watchdog, 8 smoke-transfer cases, mask 0.35 | RUN_DONE 46 s; transfer 6 s (4 workers); repro 4 s; g11 40 s (2 workers, 0 mismatches); heartbeat max gap 2.0 s |
| results/smoke-014/GTI_SMOKE_014.json | run_tests_0120 on the branch (84 modules, plain discover, clean-tag runs v0.6.0-v0.10.0) | 1,847.8 s wall |
| results/study-014/KILL_DRILL_014.json | watchdog cap 4 s on smoke-drill | kill latency 0.212 s, no survivors |

Per-case means across the three masks (equal weight, as the plan has 96 cases per mask): case 4.28 s, audit 12.4 s.

## Projections (Inferred)

| Stream | Registered | Projection | Share | Action |
|---|---|---|---|---|
| transfer | 4 w, 2,400 s | 288 x 4.28 / 4 = 308 s (x1.5 contention: 460 s) | 13-19% | none |
| gti | 2 w, 3,600 s | 1,848 s smoke + about 12 s for the scoring tests; under load about 1,900-2,300 s | 53-64% | none |
| repro | 2 w, 1,500 s | 96 x 4.28 / 2 = 205 s (x1.5: 310 s) | 14-21% | none |
| g11 | 2 w, 2,400 s | 288 x 12.4 / 2 + 20 x 12.4 / 2 = 1,910 s | **80%** | **deviation #61: 4 workers** |
| g11 (after #61) | 4 w, 2,400 s | 288 x 12.4 / 4 + 20 x 12.4 / 4 = 955 s (x1.5: 1,430 s) | 40-60% | |

Critical path: transfer (about 460 s), then g11 (about 955-1,430 s) ends near t0 + 1,900 s. gti runs from t0 and ends
near t0 + 2,300 s. Both are far inside the 7,200 s cap. The worker count never exceeds 8: 4 + 2 at t0, then
2 (gti) + 2 (repro) + 4 (g11).

## Smoke GTI note (Observed)

The smoke GTI verdict failed clause iii (431 module tests against 440 in plain discover). The 9 missing tests are
tests/test_scoring_014.py, which was written while the smoke run was going: after the module list was taken and before
plain discover ran. Clauses i, ii, iv and v passed. K_0110 was not needed because test_release_0110 passed on the
branch. The real GTI runs on a fixed tree.

## What this does not cover

- Contention factors (x1.5) are guesses. The smoke ran with at most 2-3 busy cores.
- Mask-0.6 audits vary a lot (13-28 s on two seeds). A heavy tail at mask 0.6 could push g11 toward 1,800 s, which
  would still be 75% of the budget.
