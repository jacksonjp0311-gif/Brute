# Deviation #130 (study-029, v0.26.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_029 or its amendment
A1 (BRUTE_PLAN_029_A1.json). Each item records a choice the plan left open, or a reading of a criterion, made before any
main seed was run. Smoke seeds 9590001-9590030 only. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Definitions (Exact).** As in scripts/make_gates_029.py: U(arm, case) = UNKNOWN queries / planned queries, where an
   unrun query counts UNKNOWN; X = cases with U_count 0; TP(arm, case) = exact answers / arm wall seconds, with identify
   excluded; GQB = S4 max(query_max, observe_max) <= 10.5 s on every main case; GSC4 b = paired mean over the 12 scale12
   eps-0 seeds of U(S4) - U(S1) <= -0.08, with the seed-bootstrap 95% CI upper end < 0 (Random(29), 10000 resamples);
   GTP = median per-seed TP(S4)/TP(S1) >= 2 and bootstrap CI lower end of the mean ratio > 1.5 (scale12).
2. **S4 build (Exact).** brute/scalesearch4.py: S1's RegionSpace(16) model and S1's first-visit symmetry (A1 says S4 =
   S1 plus throughput ideas). One RegionK per step is reused across all queries of that step; witnesses from earlier
   models (pool <= 32) answer queries without a solve; several queries are decided in one solve through a batched OR
   selector; every solve runs in conflict chunks with a wall check before each chunk, a 10 s per-query cap (QUERY_S) and
   S1's per-solve conflict budget (CONF 100000).
3. **Solver g3 (Observed; pre-declared rule: lowest summed U on scale12 smoke seeds 9590004-9590006).** g3 gave U counts
   75/95/42 (sum 212); m22 gave 87/157/76 (sum 320). Chosen: g3, the same engine as S1. Runs were on a shared box (scratch
   logs, not kept).
4. **S1 overrun (Observed; not fixed).** The frozen S1 cannot be interrupted inside predict_support, so its arm wall can
   exceed its 55 s budget (73.5 s observed on smoke). TP uses the measured wall, so an overrun lowers TP(S1) and favours
   GTP slightly. S1 stays frozen, as A1 requires.
5. **Smoke reading (Observed; Inferred forecast).** On 7 smoke cases S4 U was about equal to S1 (scale12 9590003: 168 vs
   167; scale8 9590005: 122 vs 123; scale16 9590001: 217 vs 222) and below S3 (244/212/256). TP ratio S4/S1 was 1.03-1.36.
   GSC4 b and GTP are therefore likely to FAIL (Inferred). S4_nosym (descriptive) was much lower (18/2/145). This matches
   the scratch diagnosis (symmetry clauses are the cost) but is not gated. Nothing was tuned after this reading. The run
   goes ahead as locked and the result will be published.
6. **Runtime risk (Inferred).** The estimate from the contended smoke run is 1470-1750 s for 51 cases with 8 workers,
   against the 1800 s G_RT cap. If the cap is hit, the runner seals the partial block, G_RT fails and the data gates read
   INCOMPLETE. There is no relaunch.
7. **Identify nit (Open).** On a trace whose search did not finish, identify_trace reports the lower bound n_min that it
   proved within its 10 s budget. This can be below the true state count. ID is still scored only as an exact match.
8. **Pre-freeze gates test (Observed).** make_gates_029 was run on the sealed smoke block (sealed_input_verified True,
   no crash; data gates INCOMPLETE as expected). The same cases were then relabelled main/stress, re-sealed with the
   runner's _write and gated; make_gates_029 --check reproduced the output. tests/test_scripts_029 repeats this on a
   synthetic 51-case block. Source: results/diag-029/PREFREEZE_SMOKE_GATES_029.json.
