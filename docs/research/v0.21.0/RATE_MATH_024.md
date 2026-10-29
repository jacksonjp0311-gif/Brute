# Study-024 rate math (before the source freeze)

Measured on the orchestrator dry run `/tmp/s24/dry`: `SMOKE=1`, the held-out stream layout, RUN_T0 04:38:46 EDT on
2026-10-29, clean tracked tree. RUN_DONE came 3630 s after t0. Transfer finished 32 smoke cases in 624 s (7 workers),
repro in 448 s, GTI in 3630 s (158 modules + plain discovery 1033.8 s; every clause true except v_new_tests_pass,
because `tests/test_scoring_024.py` was still untracked, as #107 requires before the scoring freeze). The smoke g11
stream exited 1 after a clean audit (32/32, 0 mismatches). See #117 item 8. The watchdog logged no heartbeat gap over
10 s. Rules are the plan's: transfer and repro cost each held-out cell at its slowest smoke case, g11 at its slowest
smoke audit, GTI = max(sum of module walls / workers, slowest module); ×1.75; fill ≤ 0.8. The mean path is reported
beside it. Per-cell inputs are in `RATE_MATH_024.json` (post-cut) and `RATE_MATH_024_PRECUT.json`.
Labels: dry-run walls are Observed; projections are Simulated.

## Before the cut (plan layout; `RATE_MATH_024_PRECUT.json`)
| stream | workers | budget (s) | mean path (s) | slowest raw (s) | x1.75 (s) | fill | fits |
|---|---|---|---|---|---|---|---|
| transfer | 7 | 6000 | 6169.8 | 7143.5 | 12501.2 | 2.084 | no |
| repro | 4 | 1200 | 871.8 | 1141.7 | 1997.9 | 1.665 | no |
| g11 | 3 | 1200 | 774.7 | 794.3 | 1390.0 | 1.158 | no |
| gti | 1 | 7000 | 3589.3 | 3589.3 | 6281.3 | 0.897 | no |

The mean path is **7041.6 s**, which leaves 158 s under the 7200 s cap, and the transfer mean (6169.8 s) is over its
6000 s budget. The ×1.75 path is 14499.1 s. The plan's `runtime_estimate` requires the cut to be declared here, before
the run. That is deviation #117 item 7.

## The cut (#117 item 7; Exact)
- **Reproset 60 → 30.** `jobs_for(plan, 'reproset')` = `main[::12]` (every 4th seed, eps 0). It is a subset of the plan's
  `main[::6]`, with family counts cycle3 6, switch3 6, unaliased2 6 and ood4 12 (the same 1:1:1:2 weights). sha256 of
  the 30-job list as JSON: `6f85ca4c3e42b3e94605d29dbe2c73735a94f1ed2a49b2c0e3c7b1eb8d6bfcba`.
- **STREAMS re-split** (within 8 workers and 7200 s): transfer 7/6400, gti 1/7000, repro 3/800, g11 4/800.
- Main (360), stress (30, fixed by the plan), the arms, the bound, the seeds and every gate threshold are unchanged.

## After the cut (frozen)
| stream | workers | budget (s) | mean path (s) | slowest raw (s) | x1.75 (s) | fill | fits |
|---|---|---|---|---|---|---|---|
| transfer | 7 | 6400 | 6169.8 | 7143.5 | 12501.2 | 1.953 | no |
| repro | 3 | 800 | 581.2 | 761.1 | 1331.9 | 1.665 | no |
| g11 | 4 | 800 | 581.0 | 595.7 | 1042.5 | 1.303 | no |
| gti | 1 | 7000 | 3589.3 | 3589.3 | 6281.3 | 0.897 | no |

The mean path is **6751.0 s**, leaving 449 s under the cap. Under the ×1.75 slowest-case rule the path is 13833.1 s, so
the layout **does not fit** that rule. Studies 021 and 023 did not fit it either. In study 023 the actual-to-mean
ratio was transfer 0.911 (4475 / 4909.6 s), g11 1.054 and repro 0.976. Applied here, that gives about 5620 s +
max(567, 612) s ≈ 6230 s (Inferred). The run goes ahead under the stop rule: a 7200 s cap, no extension and no rerun.
Any gate whose inputs are incomplete FAILs (STUDY_BUDGET). The transfer margin is thin (mean 6169.8 s against a
6400 s budget), and that is published, not hidden.
