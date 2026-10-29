# Study-023 deviation #110 (written before the source freeze; Exact)

**The stress block drops from 60 to 30 cases.** This is the contingency that was declared in advance in
`BRUTE_PLAN_023.json` `runtime_estimate`: "if the smoke rate math projects a mean path > 6000 s, the stress block drops
to 30 cases before the source freeze (numbered deviation); nothing else changes."

- **Trigger (Simulated).** The rate math used the frozen v0.20.0 layout on the orchestrator dry run (`SMOKE=1`, 32 smoke
  transfer cases, HEAD 026da25). It projected a mean path of **7357.7 s** for 60 stress cases with STREAMS
  transfer 7/5800, gti 1/6400, repro 6/1400 and g11 1/1400. That is over 6000 s, so the contingency fires.
  The pre-cut table is at the end of `docs/research/v0.20.0/RATE_MATH_023.md`.
- **Selection (Exact, deterministic).** The 60 stress cases were the first half of each family's seed range. The 30
  are the first quarter of each range: `range(lo, lo + (hi - lo + 1) // 4)` in `experiments/brute_study_023.jobs_for`.
  That gives cycle3 8910001–8910006 (6), switch3 8920001–8920006 (6), unaliased2 8930001–8930006 (6) and ood4
  8940001–8940012 (12). The 30 cases are a subset of the 60 that SEEDCHECK_023 checked. The family weights are the same
  as before (1:1:1:2). The order is still family-major. sha256 of the 30-job list as JSON:
  `dc31f15d760ab725990e42a1f182de1b59947a5f979a59e14db020c4cde687b0`.
- **Scope.** The stress block feeds no gated criterion. GLR uses the 240 noisy main cases and the 120 eps 0.02 main cases.
  Stress appears only in the R_stress report and in the G10 case count (now 390 = 360 main + 30 stress). The main block,
  the arms, the bound, the seeds and every gate threshold are unchanged.
- **Files changed to match (before the freeze).** These are `jobs_for` and its docstring; `make_gates_023` EXPECTED and
  docstring; the `make_paired_023` and `run_study_023` docstrings; `tests/test_study_0200.py` (390, 30, range endpoints);
  and `tests/test_scoring_023.py` (EXPECTED). SEEDCHECK_023 and `check_seeds_023` were committed earlier and still
  describe the 60. They are not edited.
- **Stream table (also set by the rate math, before the freeze).** The STREAMS table is re-split inside the 8-worker and
  7200 s limits: transfer 7/6000, gti 1/7000, repro 4/1200, g11 3/1200. The plan's "nothing else changes" refers to the
  scientific design. The plan's process control sets the STREAMS table from the rate math, and that is done here in the
  open. The post-cut mean path is **5632.1 s** (Simulated). Under the ×1.75 slowest-case rule the layout still does not
  fit (projected 12017.0 s). Study 021 had the same result, and the gap is published, not hidden.

## Tooling fix found by the smoke gates (not a deviation; disclosed)
`make_gates_023` GLR_lemma compared `HN_RECOUNT.D` (stored as `{'1':3,'2':4,'3':5,'4':7}`) to a list, so the
clause always failed. It now normalises the dict to `[3,4,5,7]` (`_dlist`). The rule is unchanged.

## Observed on the dry run (not a deviation; disclosed)
The dry run's watchdog had 4 heartbeat gaps over 10 s, so smoke G_HB = FAIL. In two of them monotonic time and wall
time grew together (21.5 s and 16.7 s) and the watchdog used almost no CPU. Each was followed by a gap of about
45 s wall but under 5 s monotonic, which fits a pause of the whole VM followed by a wall-clock step. That reading is
Inferred. The G_HB rule (max watchdog gap ≤ 10 s) is gated and stays as it is. If the main run has the same pauses,
G_HB fails and the failure is published.
