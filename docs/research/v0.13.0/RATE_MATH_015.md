# Rate math for study-015 (stop_rule.rate_math)

Written before the source freeze and before any held-out seed of BRUTE_PLAN_015 was generated. All timings come from
smoke seeds (8190001-8190017) and are labelled. Projections are Inferred. The plan allows one budget / worker change
before the source freeze for a mandatory stream that projects above 70% of its budget.

## Measurements (Observed, smoke seeds)

| Source | What | Result |
|---|---|---|
| results/smoke-015/RATE_TIMINGS_015.json | 1 case + reference audit, 12 rows (cycle3, unaliased2, ood4, ood5 x 3 masks), one process, measured while the GTI smoke ran | main: case mean 1.88 s, audit mean 9.02 s (audit max 15.6 s, unaliased2 mask 0.6); ood5: case 0.25 s, audit 3.12 s |
| results/smoke-015/SMOKE_DRYRUN_015.json | full orchestrator + watchdog, 10 smoke-transfer cases (2 ood5), mask 0.35, SKIP_GTI | RUN_DONE 48 s; transfer 4.2 s; repro 8.2 s (4/4 SCIENTIFIC identical); g11 48.2 s; heartbeat max gap 2.0 s |
| results/smoke-015/GTI_SMOKE_015.json | run_tests_0130 on 426db81 (475 tests per module = 475 plain), clean-tag runs | 2,384 s wall, with the rate timings and a test_release_060 worktree check running at the same time |
| results/study-015/KILL_DRILL_015.json (step 4) | watchdog cap on smoke-drill | kill latency 0.209 s, no survivors |
| results/smoke-015/SMOKE_R1_015.json | scripts/run_study_015_R1.py (the #72 orchestrator), same smoke block, SKIP_GTI | RUN_DONE 33 s; transfer 4 s; repro 4 s; g11 28 s with 4 workers (48 s with 2 in the dry run) |

Study-014 reference point (Exact, results/study-014/RUN_DONE_014.json): the real gti stream took 1,655 s against a
1,848 s smoke (ratio 0.90).

## Projections (Inferred)

| Stream | Registered | Projection | Share | Action |
|---|---|---|---|---|
| transfer | 4 w, 3,000 s | (288 x 1.88 + 72 x 0.25) / 4 = 140 s (x1.5 contention: 210 s) | 5-7% | none |
| gti | 2 w, 3,600 s | 2,384 s smoke x 0.90-1.0 = 2,150-2,390 s, plus about 15 s for test_scoring_015 | 60-67% | none (upper tail x1.2 = 2,860 s, 79%: disclosed, not acted on) |
| repro | 2 w, 1,500 s | (96 x 1.88 + 24 x 0.25) / 2 = 93 s (x1.5: 140 s) | 6-9% | none |
| g11 | 2 w, 2,400 s | (288 x 9.02 + 72 x 3.12 + 20 x 9.02) / 2 = 1,501 s (x1.5: 2,252 s) | 63-94% | **deviation #72: 4 workers** |
| g11 (after #72) | 4 w, 2,400 s | 3,003 s CPU / 4 = 751 s (x1.5: 1,126 s) | 31-47% | |

Critical path: transfer (about 140-210 s), then g11 (about 750-1,130 s) ends near t0 + 1,350 s. gti runs from t0 and
ends near t0 + 2,150-2,860 s. Everything ends far inside the 7,200 s cap. Workers never exceed 8: 4 + 2 at t0, then
2 (gti) + 2 (repro) + 4 (g11).

The one allowed change went to g11, whose contention projection (94%) is the only one above 70%. gti's central
projection is under 70%; its x1.2 tail is not, and the plan's single change is spent, so a slow gti is published as is.

## Smoke GTI note (Observed)

The smoke GTI verdict failed clauses i and v. Every listed failure except two is a declared K-rule failure (old
release tests reading the 0.12.0 RELEASE.json, and test_release_0120 seeing the then-uncommitted run_study_015 edit).
The two undeclared failures (tests/test_scripts_015.test_streams and tests/test_study_011.test_smoke_and_heldout_jobs)
came from the smoke-drill environment the smoke GTI inherited: SKIP_GTI=1, SMOKE=1, BRUTE_SMOKE_DRILL=1, CAP_S=600 and
STUDY_DIR_015=/tmp/drill015 were still set in the launching shell (Exact: /proc/1709131/environ). With those variables
unset both modules pass (14 tests OK, Observed 02:05 EDT). The real run is launched with these variables explicitly
removed.

## What this does not cover

- The contention factors (x1.5, x1.2) are guesses.
- The rate timings are one seed per family and mask. A heavy mask-0.6 audit tail could push g11 higher, but at 4 workers
  it would need a 2x tail to reach 70%.
- gti wall time depends on the clean-tag runs, which this math treats as a fixed block.
