# Study-017 rate math (BRUTE_PLAN_017 stop_rule)

Written before the held-out run, from smoke seeds only. Timings: `results/smoke-017/RATE_TIMINGS_017.json`
(15 cases: smoke seeds 8390001 / 03 / 05 / 07 / 16, one per family, masks 0.1 / 0.35 / 0.6, single process,
measured on the box while one GTI smoke run and short unit-test runs were going; load average about 1.5 on 8 CPUs).

| Quantity | Value | Label |
|---|---|---|
| Mean main case (transfer, all 15 arms incl. RGLX / RGL lookahead + stress) | 4.798 s | Observed (12 smoke cases) |
| Mean ood5 case (RG4, RG5, RSXL5) | 0.987 s | Observed (3 smoke cases) |
| Mean reference audit per main case (v0150_reference, exhaustive lookahead) | 30.429 s | Observed (12 smoke cases) |
| Mean reference audit per ood5 case | 9.667 s | Observed (3 smoke cases) |
| Audit mismatches | 0 / 15 | Observed |

The reference audit costs about 2.1x the study-016 audit (14.479 s per main case). Inferred cause: v0150_reference
re-derives the RGLX and RGL lookahead exhaustively per step, independently of brute/boundedlookahead.py.

## Projections (x1.5 contention margin, as study-016)

| Stream | Work | Workers | Projected wall | x1.5 | Budget | Fraction (x1.5) | Label |
|---|---|---|---|---|---|---|---|
| transfer | 360 x 4.798 + 72 x 0.987 = 1798 s | 4 | 450 s | 674 s | 3000 s | 0.22 | Inferred |
| repro | 120 x 4.798 + 24 x 0.987 = 600 s | 2 | 300 s | 450 s | 1500 s | 0.30 | Inferred |
| g11 (plan: 2 workers) | 360 x 30.429 + 72 x 9.667 = 11651 s | 2 | 5826 s | 8738 s | 2400 s | **3.64** | Inferred |
| g11 (study-016 #76: 4 workers) | 11651 s | 4 | 2913 s | 4369 s | 2400 s | **1.82** | Inferred |
| g11 (deviation #92: 6 workers, after repro) | 11651 s | 6 | 1942 s | 2913 s | 2400 s | **1.21** (0.81 without margin) | Inferred |
| gti | the 016 smoke took about 2561 s | 2 | - | - | 3600 s | about 0.71 | Observed (016) |

Deviation #92 runs g11 at 6 workers, the largest count the plan's 8-worker cap allows next to gti's 2. The scheduler starts
g11 only when 6 workers are free, i.e. after repro ends (transfer about 674 s + repro about 450 s with margin). Projected
end of g11: about 1100 + 2913 = 4000 s after RUN_T0, inside the 7200 s cap (Inferred).

**Disclosed risk (Inferred):** even at 6 workers, g11 is projected at 0.81 of its 2400 s budget without margin and 1.21 with
the x1.5 margin. If it overruns, GS_ref5 FAILs as STUDY_BUDGET on the cases audited so far; the budget is not raised.
That is a process outcome, not a hypothesis outcome, and is published as it happens.

## Smoke checks (Observed, smoke seeds only)

See `results/smoke-017/SMOKE_DRYRUN_017.json`, `results/study-017/KILL_DRILL_017.json`,
`results/smoke-017/REFERENCE_MUTATION_SMOKE_017.json` and `results/smoke-017/GTI_SMOKE_017.json` (written after this file).
