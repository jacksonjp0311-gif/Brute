# Deviation #117: how the study-024 scoring scripts apply BRUTE_PLAN_024 (v0.21.0)

Label: **Exact** for each rule (it is code in the scoring freeze). Declared before the scoring freeze and before
run_start; no study-024 held-out result has been seen.

1. **Bootstrap registration (GLS c, d, e3).** BRUTE_PLAN_024 says "paired-bootstrap CI95" and sets stop_rule "as
   BRUTE_PLAN_023". It does not repeat the resample count or seed. `scripts/make_paired_024.py` takes them from the
   BRUTE_PLAN_023 metrics string ("paired bootstrap (10000 resamples, seed 23) over cases, as study-021") and checks
   that string is present before it runs. No new seed was chosen.
2. **GS_a10 arm.** The carried GS_a10 gate ("0 false at eps 0") is applied to the new arm, RGL5, on the 120 eps-0 main
   cases. The RGL4, RGNA4 and RG4 eps-0 counts are reported in the same gate but do not decide it.
3. **GAS_frozen_control interval source.** The study-023 interval for C_late(RGL4, eps 0.02) is read from the tracked
   file `results/study-023/PAIRED_ANALYSIS_023.json` (key `C_late_RGL4_eps2`, CI [0.376039, 0.458523], mean 0.41714),
   and that file's sha256 is embedded in the gate. It is not retyped.
4. **G_PROC evidence files.**
   - (a) `tests/test_scripts_024.py` (Launcher024 tests) must be all ok inside GTI; at run_start a live launch with
     `SMOKE=1` must exit 3 (`results/study-024/LIVE_REFUSAL_024.json`, `hook` = SMOKE); `LAUNCH_024.json` must exist.
   - (b) The first line of `RUN_024.log` must carry `study_dir …/results/study-024` and the same RUN_T0 as the RUN_T0 file.
   - (c) Commit order is read only from `experiments/COMMIT_ORDER_024.json`, whose sha256 is bound in the source freeze.
   - (d) Ledger note times from `preregistration_024` through the first `run_start_024` must parse as ISO-8601, be
     non-decreasing, and the run_start note must be within 120 s of RUN_T0. Later ledger entries are not read, so the
     clean clone sees the same inputs.
5. **Carried RGL4 prefix check.** The 023 GLR (e) comparison for RGL4's prefix28 record is kept as the report
   `R_prefix28_RGL4`, not as a gate. The 024 gate is GLS (e1) on prefix28_rgl5.
6. **Early-window diagnostic definition.** `scripts/early_window_024.py` defines "needed" as m_arm(t) + 1 readings of a
   bit and "supplied" as the unmasked readings of that bit in readings 0..t. "Needed" is an Inferred necessary
   condition only. The report is Open and never gated.
7. **Rate-math cut (written before the source freeze).** BRUTE_PLAN_024 `runtime_estimate`: "If the path at x1.75 does
   not fit the cap, the cut is pre-declared in the rate-math file before the run." On the dry run the plan layout
   projects a mean path of 7041.6 s (×1.75: 14499.1 s), and the transfer mean (6169.8 s) is over its 6000 s budget
   (Simulated; `docs/research/v0.21.0/RATE_MATH_024.md`). The cut: **reproset 60 → 30** (`main[::12]`, a subset of the
   plan's `main[::6]`, family weights 1:1:1:2 kept, sha256 `6f85ca4c…d6bfcba`) and **STREAMS re-split** to transfer
   7/6400, gti 1/7000, repro 3/800, g11 4/800. The post-cut mean path is 6751.0 s. The ×1.75 path (13833.1 s) still
   does not fit, as in 021 and 023, and that is published. Files changed to match, before the freeze:
   `experiments/brute_study_024.jobs_for` and its docstring, `scripts/run_study_024.STREAMS` and its docstring,
   `tests/test_study_0210.py` (30, `[::12]`), the `scripts/rate_math_024.py` docstring, and in the scoring set
   `make_gates_024.REPRO_EXPECTED` = 30, `tests/test_scoring_024.py` and the `make_reproducibility_024` docstring.
   PLAN_024.md and BRUTE_PLAN_024.json still say 60 and are not edited. G12 power drops to 30 byte-identical cases;
   main, stress, arms, seeds and every threshold are unchanged.
8. **Smoke g11 mutation step (Observed; tooling scope, not changed).** On the dry run the g11 audit was clean (32/32,
   0 mismatches), but the stream exited 1 with "no case for the prefix28_rgl5 mutation".
   `experiments/v0210_reference.mutate` picks 20 of the 24 smoke main cases, and all 8 eps 0.02 smoke cases fell in
   the picks, so no eligible case was left for the prefix28_rgl5 kind. The held-out run has 360 main cases (120 at
   eps 0.02), so the selection cannot exhaust them in the same way (Inferred). The reference and `run_reference_024`
   are not changed. If it did recur, GS_ref10 would FAIL and the failure would be published.
