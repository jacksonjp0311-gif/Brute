# Study-023 rate math (before the source freeze)

Measured on the orchestrator dry run. It used `SMOKE=1` and the held-out stream layout, and started at 19:24:41 EDT on
2026-10-28 at HEAD 026da25 with a clean tree. RUN_DONE came 3769 s after t0, and no stream stopped. The rules are the
plan's. Transfer and repro cost each held-out cell at its slowest smoke case. g11 costs each cell at its slowest smoke
audit. GTI uses max(sum of module walls / workers, slowest module). Every stream wall is divided by the workers, ×1.75,
with fill ≤ 0.8. The mean path is reported next to it. `RATE_MATH_023.json` holds the per-cell inputs. Labels: dry-run
walls are Observed; projections are Simulated.

## Before the cut (60 stress; `RATE_MATH_023_PRECUT.json`)
| stream | workers | budget (s) | mean path (s) | slowest raw (s) | x1.75 (s) | fill | fits |
|---|---|---|---|---|---|---|---|
| transfer | 7 | 5800 | 5561.9 | 6733.9 | 11784.3 | 2.032 | no |
| repro | 6 | 1400 | 481.7 | 602.4 | 1054.2 | 0.753 | yes |
| g11 | 1 | 1400 | 1795.8 | 1839.1 | 3218.5 | 2.299 | no |
| gti | 1 | 6400 | 3726.4 | 3726.4 | 6521.2 | 1.019 | no |

The mean path is **7357.7 s, which is over 6000 s**, so the pre-declared contingency fires: deviation #110, stress
60 → 30 (`docs/research/BRUTE_DEVIATIONS_023_110.md`).

## After the cut (30 stress, STREAMS re-split; frozen)
| stream | workers | budget (s) | mean path (s) | slowest raw (s) | x1.75 (s) | fill | fits |
|---|---|---|---|---|---|---|---|
| transfer | 7 | 6000 | 4909.6 | 5963.3 | 10435.7 | 1.739 | no |
| repro | 4 | 1200 | 722.5 | 903.6 | 1581.3 | 1.318 | no |
| g11 | 3 | 1200 | 558.6 | 571.1 | 999.5 | 0.833 | no |
| gti | 1 | 7000 | 3726.4 | 3726.4 | 6521.2 | 0.932 | no |

The mean path is **5632.1 s**, under the 6000 s trigger and the 7200 s cap. Under the ×1.75 slowest-case rule the path
is 12017.0 s, so the layout **does not fit** that rule. Study 021 did not fit it either (its mean path predicted 4865 s
and the actual was 4801 s). The run goes ahead under the stop rule: a 7200 s cap, no extension and no rerun, and any
gate whose inputs are incomplete FAILs (STUDY_BUDGET). This is published, not hidden.

## Dry-run observations (Observed)
- Transfer finished 32 smoke cases in 558 s on 7 workers. The slowest cells are cycle3 eps 0.05 (252 s) and ood4 eps
  0.02 (203 s).
- g11 audited 32 cases in 251 s on 1 worker, a mean of 4.14 s per case. Repro took 321 s. GTI ran 164 modules
  (summed wall 3726 s; the slowest is plain discovery at 1183 s). Its verdict passed, every clause including
  vi_tooling_order was true, and the tree was not dirty.
- Drills (`results/smoke-023`): KILL_DRILL kill latency 0.224 s, no survivors, no SIGKILL. RESUME_DRILL: all 4
  clauses true. API_CHECK: 4 cases, passed.
- The smoke gates (make_paired / make_reproducibility / make_gates on the dry directory) are a check of the tooling
  only. With n = 16 noisy smoke cases they are not evidence. G_recount, GLR_lemma (after the `_dlist` fix in #110),
  GAS_frozen_control, GS_a10, GS_ref10, GAPI10, G10, G12, G13, GTI and G_RT pass. GLR fails clauses b and c, as
  expected at n = 16 (CP95 0.171; C_late RGL4 eps 0.02 0.393 [0.253, 0.550]). G_HB fails: max watchdog gap 45.6 s, with
  4 gaps over 10 s that look like VM pauses (Inferred; see #110).
