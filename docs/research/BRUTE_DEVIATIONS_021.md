# Study-021 deviations: post-run disclosures (#107)

Written 2026-10-28 ~17:35 EDT, after the run end (`9c2a7fa`), the seal (`ffda8a1`) and scoring (`ff96381`). Nothing frozen is
edited, no verdict is changed, and the ledger stays append-only. Deviation numbering continues after #106.

## #107 Post-run disclosures

1. **Run outcome (Exact, RUN_DONE_021.json).** RUN_T0 was 16:02:34 EDT; RUN_DONE was 17:22:35 EDT, 4801 s after RUN_T0.
   The cap is 7200 s, so 2399 s were unused. Completion after RUN_T0: gti 3639.6 s, transfer 4131.8 s, repro 4375.9 s,
   g11 4800.8 s. No stream was stopped. The maximum watchdog gap was 3.294 s (2401 beats, 0 gaps over 10 s).
   The rate-math projection (RATE_MATH_021, critical path 10309.2 s with the x1.75 rule) did not fit the cap; the
   mean-path figure (4864.9 s) was close to the observed 4801 s. The run went ahead on the mean path (Observed).
2. **GTI FAIL (Exact) and its cause (Exact from the git history).** TEST_SUITE_021 has `passed = false`: clause i (only
   declared failures) and clause v (new tests pass) are false. Six undeclared failures, all in `tests/test_release_0190.py`:
   `test_every_artifact_every_mode_raises_verification_error`, `test_embeddable_api_answers`,
   `test_scoring_inputs_tracked`, `test_short_verify_passes`, `test_untampered_copy_passes`, `test_version_consistent`.
   - The release tooling (`0977173`) was committed before run_start. `make_freeze_021`'s docstring says it is written at
     release, after the run. The release tests therefore ran against the pre-release state (RELEASE.json api certify/7,
     version 0.18.0), where they are expected to fail.
   - 783 tests ran; the tracked tree was clean at start. The dry run (/tmp/s21/dry) passed GTI because those tests did not
     exist yet when it started.
   - Published as FAIL. Not re-run and not re-scored. The fix (a rule on when release tests may enter the tree, or a
     declared-pre-release list) goes into the v0.20.0 plan.
3. **GAH_anytime FAIL on clause (c) (Exact); expected in the plan (Inferred there).** dC_early28(RGNA4 - RGNB4, eps 0.02)
   is -0.004018, CI [-0.006845, -0.001786]; the clause asks for mean > 0 with CI lower > 0. Clauses (a), (b) and (d) pass:
   0 false certificates on 240 noisy cases, CP upper 0.0124; C_late(RGNA4, eps 0.02) 0.265, CI [0.215, 0.317]. The anytime
   margin pays for its guarantee with lower coverage than the planned margin, early and late (dC_late -0.228).
4. **GAPI9 results_file path (Exact).** The gate's `api_check.results_file` points at `/tmp/s21/api/RESULTS.json`, a
   dry-run scratch path that is removed at the end of this step. The gate input is the tracked
   `results/smoke-021/API_CHECK_021.json` with its results_sha256 (0de6dee9...); the path is informational only.
