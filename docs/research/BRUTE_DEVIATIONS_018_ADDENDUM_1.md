# BRUTE study-018 deviations, addendum 1 (BRUTE-0160-NOISY-OBSERVATION-018)

Written after the smoke dry runs (smoke seeds only, blocks smoke-transfer / smoke-drill) and BEFORE the study-018 source
freeze, the scoring freeze and run_start_018. No held-out seed (8410001-8440048) has been generated, simulated or
inspected. `BRUTE_DEVIATIONS_018.md` (#97) is ledger-hashed and unchanged; this file adds #98 and #99.

## #98 Process: parallel GTI and stream budgets

1. **Clean-tag GTI children run in parallel.** In smoke dry run 1 (`/tmp/s18/dry1`, Observed) the per-module test
   children finished in 457 s, but the clean-tag re-runs (each a detached git worktree of an earlier release tag) ran one
   after another, because `scripts/run_tests_0160.py` held its git lock around the whole child. Each took about 100-150 s,
   and GTI was still running at 928 s, so the run was stopped by hand. Dry run 1 left no TEST_SUITE_018.json. The fix
   locks only `git worktree add --detach` and `git worktree remove --force`. The child itself runs outside the lock.
   This re-implements the frozen `run_tests_0150.clean_run` method unchanged; that file is not edited.
2. **as_completed.** A module that needs a clean-tag child is queued for it as soon as the module finishes
   (`as_completed` over a future->module map), not after all modules. The result order is still the module order.
3. **Workers / budgets.** `STREAMS = transfer (4, 1800 s), gti (4, 4800 s), repro (2, 1200 s), g11 (2, 1200 s)`, the gti
   stream raised from 3 to 4 workers. Phase 1 runs transfer + gti (8 workers on 8 CPUs). Phase 2 runs gti + repro + g11
   (8 workers). The budgets are checked by `docs/research/v0.16.0/RATE_MATH_018.md`, which uses dry run 2 timings. If the
   rate math shows a budget does not fit, the STREAMS change is recorded there before the freeze.
4. **g11 / GS_ref6 split (restating #97).** The second implementation audits every gated case it is given. GS_ref6
   scores the main-block cases at eps 0 and 0.02 (`gated_cases_expected == gated_cases_audited ==` that count). Stress
   (eps 0.05) and smoke cases are audited and reported but are not in the GS_ref6 denominator.

## #99 Scoring: the exact meaning of GNS (b)

The plan's `metrics.clopper_pearson` asks for an exact one-sided 95% Clopper-Pearson upper bound on the RGN4
false-certificate rate over the 240 noisy main cases (eps 0.01 and 0.02). scipy is not installed. So `cp_upper(k, n)` is
computed by bisection on the binomial CDF, the p at which P[X <= k; n, p] = 0.05, using 200 halvings. For k = 0 it
equals the closed form 1 - 0.05^(1/n). `tests/test_scoring_018.py` checks both the closed form and the CDF identity.
GNS (b) passes iff `cp_upper(k, 240) <= 0.05`, where k is the number of noisy main cases with at least one false RGN4
certificate. With k = 0 the bound is 0.0124. The threshold is unchanged.

## Smoke observations disclosed before the freeze (Observed, smoke seeds only; no criterion changed)

- RGN4 coverage in smoke was low (C about 0.05 at eps 0, 0.065 at eps 0.02, 0.075 at stress), below the GNS (c) 0.10
  floor. RGN4_0 was about 0.49 and RGN4_or about 0.31-0.46. If this holds on the held-out seeds, GNS fails on (c).
- GN0 in smoke: one slot differed between RGN4_0 and RG4 (cycle3 / 8490002, eps 0, step 7, inside the burn-in), as
  #97 anticipated. GN0 is scored exactly as registered. The burn-in / post-burn-in split is reported only.
- RG4 issued false certificates on noisy smoke cases (2 of 8 at eps 0.02, 3 of 8 at 0.05). RGN4 issued none.
