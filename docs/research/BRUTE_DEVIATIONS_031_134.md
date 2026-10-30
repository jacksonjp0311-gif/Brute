# Deviation #134 (study-031, v0.28.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_031. Each item records
a choice the plan left open, or a reading of a criterion, made before any main seed was run. Only smoke seeds
9790001-9790030 and the scratch-diagnosis replays of published study-030 seeds were run. Labels: Exact, Observed,
Simulated, Inferred, Rejected, Open.

1. **Definitions (Exact).** As in scripts/make_gates_031.py: U(arm, case) = UNKNOWN queries / planned queries, where an
   unrun query counts UNKNOWN; X = cases with U_count 0; GSC6 b = paired mean over the 18 scale16 eps-0 seeds of
   U(S6) - U(S5) <= -0.06, with the seed-bootstrap 95% CI upper end < 0 (Random(31), 10000 resamples); GSC6 c =
   X(S6, scale16) >= 4 of 18; GSC6 d = recounted F(S6) = 0 over main and stress; GID6 b/c on the 12 scale12 eps-0 cases;
   GQB6 = S6 max(query_max, observe_max) <= 10.5 s on every main and stress case; G10 = S6 U 0 and label ID on every
   control case; GS_ref = REFERENCE_031 on arm S6 (scale8): 0 mismatches and mutations 20/20.
2. **Overlap concern (Exact).** seedcheck_031 (059fe1a code, 1ff404d ledger) passed before any main seed was drawn: 671
   files scanned, 0 standalone tokens, 0 overlaps.
3. **Incremental solver (Exact; reading of the plan).** The plan says "one incremental solver per step, with each
   query's region clauses guarded by an activation literal and solved under assumptions". S6 keeps one persistent solver
   for the whole trace (brute/scalesearch6._Inc): each step adds its x rows, transitions and masks; the step's
   next-code clauses are guarded by a fresh activation literal and the previous one is retired by the unit clause -act.
   Learned clauses therefore carry across queries and steps. The A/V/Tr definitional auxiliaries of the S1 RegionK
   encoding are omitted; the encoding is equisatisfiable, so exact answers are unchanged (tests/test_scalesearch6_0280:
   S6 equals S1 on random small cases and equals S5 on smoke world 9790001). The same S5 hard cap bounds every solve.
4. **Ordering (Exact; reading).** "Ascending candidate-region size" is read as ascending count of codes not yet
   witnessed for the query (witness-memo hits count 0), ties broken by action index. S6_noorder is S6 without it.
5. **Identify probe (Exact; reading).** The probe depends on the trace only. It runs once per eps-0 case on the full
   trace (177 readings, 176 actions) with a 60 s deadline (brute.scalesearch6.identify6, no conflict limit), and its
   label is given to every arm whose run finished all 176 steps; an arm that did not finish gets NR, counted as IDU in
   GID6 c. Labels: IDU = deadline hit; AMB = a second least machine was found; ID = unique least machine equal to the
   truth up to state renaming; WRONG otherwise (per the plan: a single class not equal to the truth, or no model). A
   WRONG can be an identifiability effect (least machine smaller than the truth), not only a soundness failure, so the
   gates file also reports WRONG_sound (WRONG and the model is inconsistent with the trace) and per-case diagnostics
   (truth_pairs_unexercised, truth_reachable, states_visited). GID6 a is scored on WRONG as the plan defines it.
6. **Budgets (Exact; reading).** "55 s per step" is read as the 55 s per-arm budget at eps 0 (40 s at eps > 0) used in
   studies 028-030, which the plan cites as the same budget.
7. **Stress arms (Exact).** The 6 stress cases (first 3 seeds of scale12 and scale16 at eps 0.05) run all four arms;
   stress U is reported for every arm, F is gated for S6.
8. **Dispatch and workers (Exact).** Longest families first: scale16, scale12, stress, scale8, control; 8 workers on
   the 8-core box. BOOT_SEED 31.
9. **Process note (Observed).** Smoke seeds 9790001, 9790012, 9790013, 9790020 and 9790029 were used in unit tests and a
   standalone timing check before the seedcheck_031 ledger entry. They are smoke-range only; no main seed was touched.
10. **G_PROC events (Exact).** preregistration_031, build_authorization_031, seedcheck_031, scratch_diag_031,
    source_freeze_031, run_start_031, in that order.
11. **Smoke reading (Observed; Inferred forecast).** 6 smoke cases, 6 workers, 251 s. eps 0 U counts (of 528): scale16
    9790001 S6 124, S6_noorder 119, S5 117, S1 123 (no S6 gain under contention, although a standalone check on 9790020
    gave S6 37.9 s vs S5 50.7 s for all 176 steps); scale12 9790003 S6/S6_noorder/S5 1, S1 94; scale8 and control 0
    for S6. S6 max query 8.27 s eps 0, 8.64 s eps 0.05. Identify labels: control ID (n_min 3); scale8, scale12, scale16
    AMB, each with 1-5 truth pairs never exercised by the trace. Noisy stress: all arms near 308-326 UNKNOWN; S1 gave 1
    false certificate on 9790004 (eps 0.05; S1 had F 3 on study-028 stress; S1 F is not gated). Inferred forecast:
    GSC6 b/c may FAIL; GID6 b (ID >= 4 of 12 at scale12) looks unlikely, since scratch_diag_031 found unexercised
    truth pairs in 10 of 12 study-030 scale12 traces, and identify6 labels 3 of 3 such traces AMB. Nothing was tuned.
12. **Runtime risk (Inferred).** About 18 x 250 s + 12 x 200 s + 6 x 150 s + 12 x 72 s + 6 x 24 s over 8 workers = 1100 s,
    against the 1800 s G_RT cap. If the cap is hit, the runner seals the partial block and G_RT fails. There is no relaunch.
13. **Pre-freeze gates test (Observed).** results/diag-031/PREFREEZE_SMOKE_GATES_031.json: make_gates_031 on the sealed
    smoke block and on a main/stress relabel (re-sealed with the runner _write and a stand-in freeze hash): no crash,
    --check reproduces both, data gates INCOMPLETE_INPUT as expected (6 of 54 cases).
