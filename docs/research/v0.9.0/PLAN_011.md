# BRUTE_PLAN_011 (study-011, v0.9.0): readable summary

The JSON (`experiments/BRUTE_PLAN_011.json`) wins if this page differs. Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

## What is being tested

J9 (SP8 certification and LU-C, every kept certificate additionally checked against the jump-WINDOW hull: one optional silent state jump into any of the observations T-K+1 .. T-1, K = 4) issues 0 non-drift false certificates at lag >= 2 on fresh drift4 seeds, because a jump into an observation at least one step before the forecast is inside the region the hull covers (Inferred; exact containment is checked by GH).

The window hull costs far less coverage than the J8 last-transition hull because it keeps the transition into the last observation constrained (Inferred). Size of the loss vs SP8: Open.

Lag-1 false certificates (jump into the last observation) remain: a hull sound against them is the J8 hull, whose coverage was 0 in study-010 (Observed). Strict G3-prime (0 non-drift false certificates at any lag) is therefore predicted to FAIL for J9 (Inferred).

## J9, the jump-window hull

- **region**: JumpWindowRegionK(n,k,m,masks,actions,K) = RegionK (same variables, symmetry clause, state bound, first state 0) with at most ONE free transition: for each t in J(T) = {max(1, T-K+1), ..., T-1} a selector j_t (at most one true); the transition clause into observation t holds unless j_t; a transition whose selector is true is not a traversal (Tr counts transition t+1 out of x[t] only if j_{t+1} is false; transitions out of t with t+1 not in J always count). The transition into the LAST observation T is always constrained (lag-1 jumps are NOT covered). With J(T) empty (T <= 1) the region equals RegionK. JW contains every machine of RegionK (all selectors false), so Y1kW contains Y1k (Exact by construction).
- **lag_mapping**: a certificate for step s is issued after T = s-1 observations; a drift4 jump at drift step d is the transition into observation d; lag L = s - d; the jump is inside J(T) iff 2 <= L <= K (Exact arithmetic).
- **hull**: Y1kW(b, mask) = RegionK.y1k evaluated on JumpWindowRegionK with mask = mask of observation T. UNKNOWN feasibility -> every code (never certifies); y1k UNKNOWN codes count as possible (frozen tri-state semantics).
- **J9**: brute.jumpwindow.WindowSyncLearner: brute.align.AlignedSyncLearner (SP8: SyncEventLearner rule CTR + LU-C) unchanged, plus: a certificate c that SP8 keeps (taken or counterfactual action) is kept only if Y1kW(action, mask_T) == {c} (cert_rule <SP8 path> + "+whull"), else ABSTAIN / RESYNC_AMBIGUOUS with cert_rule "whull-downgraded". Hull queries go through RegionSpace._q (memo key ("y1kW", action, mask)) so their unknowns count toward SOLVER_BUDGET. The LU-C lookahead is NOT changed (it counts what SP8 would certify, not what J9 keeps; disclosed). hull_union / hull_unknown are recorded per step while the family is supported (as J8).
- **not_selective_by_surprise**: NEXT_ITERATION proposed applying the hull only after an unsurprising observation; the seen data had no event between drift and certificate in 28/28, so that condition would almost always hold. J9 is selective by POSITION (window excluding the last transition), not by surprise (Inferred, disclosed).

## Arms

- **J9**: brute.jumpwindow.WindowSyncLearner, as jump_window_definition.J9 (new)
- **SP8**: brute.align.AlignedSyncLearner: the frozen SyncEventLearner(rule="CTR") (SC7 certification unchanged) with the action policy LU-C: for each action a and each code c in the support, N(a,c) = number of actions b such that, after the hypothetical full observation (a,c): family support for b is a single code s, the extended region is feasible and not saturated, the margin support for b equals s, and EITHER step t+1 is calm (no event u with (t+1) - u < W, and t+1 >= burn_in; the condition under which SC7 would certify s via "tracked-calm") OR Y1k of the extended region for b with mask {c} equals s (the LU-R condition). Score(a) = mean over c of N(a,c); ties -> passive action (as LU-R). Any solver budget hit -> 0 for that branch (as LU-R). Frozen v0.8.0 brute/align.py, run through the frozen study-010 trajectory code (experiments/brute_study_010.trajectory_2x2). Comparator.
- **A4**: frozen brute.resume.ResumeBruteLearner (v0.4.0) through the frozen study-006 trajectory code; v0.90 control for G3-prime
- **A2**: frozen brute.active.ActiveBruteLearner (v0.2.0, tau 1.4331), slim trace; G6b baseline

J8, SC7 (2x2) and the whole breadth block (B5, BSC7, BSP8; GX2 cross-check) are not rerun: they were scored in study-010 and nothing in v0.9.0 changes them. The cap is spent on doubling drift4 (G3L power), the G11 audit of J9 and the feasibility block. GD (the H_c silent-jump diagnostic) is retired: H_c was refuted in study-010 and the seen-data lag diagnostic replaces it. Disclosed weakening: breadth soundness (BSP8) is not re-tested in v0.9.0.

## Seeds

- cycle3: 4010001-4010024
- switch3: 4020001-4020024
- unstructured3: 4030001-4030024
- unaliased2: 4040001-4040024
- ood4: 4050001-4050024
- perm4: 4060001-4060024
- ood5: 4070001-4070024
- drift4: 4080001-4080096
- smoke: 4190001-4190030
- feasibility: n6 4200001-012, n7 4210001-012, n8 4220001-012

## Gated criteria

- **GA1_011_window_drift_and_coverage**: PASS iff J9 passes G1, G2, G3L and G6b on the same held-out run (only J9 can pass GA1_011; SP8 is the comparator). *Prediction: Open (G3L Inferred PASS; G6b Open).*
- **G1_in_family_soundness**: J9 and SP8 (2x2): 0 false conditional and 0 false public certificates on every in-family case; all steps incl. burn-in, every action *Prediction: Inferred: PASS (SP8 0 in study-010; J9 certifies a subset of what SP8 certifies on the same evidence).*
- **G2_ood_soundness**: J9 and SP8: 0 false conditional certificates on ood5; all steps, every action *Prediction: Inferred: PASS.*
- **G3L_drift4_lag_ge_2**: J9 on the 288 drift4 cases: (a) 0 non-drift false certificates with lag >= 2 (lag = step - last drift step < step), taken AND counterfactual action; (b) total taken-action false certificates <= 0.5 x the A4 v0.90 control false certificates on the same cases. The SP8 lag >= 2 count is reported next to it (power check: if SP8 also has 0 lag >= 2 false certificates, the PASS is labelled UNINFORMATIVE in the report; it is still scored PASS). *Prediction: Inferred: PASS (exact containment when the jump is inside the window); power Open.*
- **G3_prime_strict_drift4**: unchanged v0.8.0 definition applied to J9: taken action, 288 drift4 cases: non-drift false certificates (any lag) = 0 AND total <= 0.5 x A4 v0.90 control false certificates *Prediction: Inferred: FAIL (lag-1 jumps, H_lag1). Reported with the same prominence as GA1_011.*
- **G6b_coverage_vs_v020**: J9: pooled in_family_original_2x2 dual coverage J9 - A2 >= -0.03 AND 95% CI lower bound >= -0.05 (unchanged). J9 - SP8 is reported with CI. *Prediction: Open (SP8 -0.0167 in study-010; J9 <= SP8 by construction up to action-sequence effects).*
- **GH_window_hull_containment**: J9 on drift4: at every step s in {14, 15, 16} (lags 2..4 after the first drift at 12; the only steps where the true world is guaranteed to be in the window region, since later jumps stack) where the family is supported before the forecast and hull_unknown == 0, the realised code of BOTH actions is in the recorded hull_union. 0 exceptions; missing hull_union while supported = exception. Non-vacuity (steps where the hull is not all codes) is reported. *Prediction: Inferred: PASS (Exact by construction if the implementation is right; this is an implementation check).*
- **G4_public_safety**: J9, SP8: 0 public certificates on ood5 and drift4; 0 wrong public certificates anywhere; no public certificate after the first alarm of a session *Prediction: Inferred: PASS.*
- **G5_false_alarm_limit**: unchanged: for EACH arm J9, SP8 and EACH in-family 2x2 family: fraction of cases with >= 1 RESIDUAL_SURPRISE alarm <= 0.05 *Prediction: Inferred: PASS; perm4 Open (shared tau6 alarm; 0/72 in study-009).*
- **G7_open_world**: mean post-burn-in taken-action log-loss: J9, SP8 <= ln 4 on ood5 and drift4; min probability >= eps/4 = 0.005 on every step of every case for J9 and SP8 *Prediction: Inferred: PASS.*
- **G9_retraction_resume**: every resume (J9, SP8) only after W=8 consecutive residuals <= tau6 with family and margin supported; no certified RESYNC_AMBIGUOUS forecast; retraction reasons equal the reference; no duplicate issued/retraction pairs *Prediction: Inferred: PASS.*
- **G10_compute**: all 792 2x2 cases complete and sealed, every trace has 44 steps; production arms J9, SP8: forecasts with solver_unknown > 0 <= 1% *Prediction: Inferred: PASS.*
- **G12_reproducibility**: a second run of every 2x2 case whose run index is divisible by 3 to a new path gives byte-identical scientific JSON (timing keys stripped) *Prediction: Inferred: PASS.*
- **G13_frozen_controls_reproduce**: SP8, A4, A2 run frozen code (sha256 checked against BRUTE_SOURCE_FREEZE_00[5-9], BRUTE_SOURCE_FREEZE_010 and BRUTE_RELEASE_FREEZE_070_R1/080 via check_freeze before run_start); tau6, tau7 equal this plan; every case records the plan tau6 *Prediction: Inferred: PASS.*
- **G11_second_implementation**: experiments/v090_reference.py audits (i) EVERY trace of g11_mandatory_2x2 (J9, SP8) with 0 mismatching traces; (ii) every audited rest trace with 0 mismatches; (iii) mutation test: 20 injected single-field errors in 20 distinct mandatory traces (random.Random(20261026); >= 4 in J9 certificate/hull fields and >= 4 in SP8 or J9 action choices) detected 20/20, 0 flagged not injected; (iv) the mandatory audit finishes inside the g11 stream budget (1500 s) and the audited RESULTS.json sha256 equals the block SEAL. Labelled "second implementation by the same author". *Prediction: Inferred: PASS.*
- **GTI_test_isolation**: scripts/run_tests_090.py (the run_tests_070 method: every tests/test*.py module in its own fresh interpreter, pinned venv) on the frozen v0.9.0 tree, run INSIDE the cap, writing results/study-011/TEST_SUITE_011.json. PASS iff: (i) every failing or erroring test id is in known_failing_allowed (the 14 study-009 K_frozen ids) or allowed by K_060_rule or K_070_rule; (ii) the 6 tests of test_study_005 pass; (iii) per-module test count equals the plain `unittest discover -s tests` count and skipped sets agree; (iv) no frozen file changed; (v) every new v0.9.0 test passes. Known failures carried from v0.8.0 are allowed by the same rules (K_frozen, K_060_rule, K_070_rule); any new failure outside them fails GTI. *Prediction: Inferred: PASS (v0.8.0 in-cap run passed).*
- **G_RT_study_runtime**: NEW SEMANTICS (pre-registered here, NOT retroactive; v0.8.0 G_RT stays FAIL). PASS iff ALL of: (i) MANDATORY work completes inside the cap: streams 2x2, repro_2x2 and gti have completed_at <= RUN_T0 + 7200 s and were not stopped, and stream g11_2x2 recorded its mandatory_done event at wall <= RUN_T0 + 7200 s and inside its own 1500 s budget and was not stopped before writing its report; (ii) the watchdog ran for the whole run (heartbeat from <= RUN_T0 + 60 s to >= end - 10 s); (iii) the smoke kill drill latency <= 15 s with no survivors. OPTIONAL phases (the g11 rest audit and the feasibility stream "feas") are REPORTED (completed or stopped by their own budget, with times) and do not affect G_RT. A stop of ANY stream by the cap or by an error fails clause (i) if that stream is mandatory. The v0.8.0 strict reading (every stream complete, none stopped) is reported as R_G_RT_strict. *Prediction: Inferred: PASS.*

## Release gates

- **GCC_clean_clone**: scripts/clean_clone_011.py PASS (clean_clone.clean_clone_check) and tests/test_release_090 tracked-files test PASS; reported in RELEASE.json and the release notes; it cannot be inside GATES_011.json because it re-checks that file.
- **GLV_long_verify**: verify_release_090 --long PASS (0 mismatches on the 33-case sample inside 900 s); reported in RELEASE.json.

## Stop rule

- **cap**: 2 h 00 min (7200 s) wall clock from RUN_T0 (the epoch written with the run_start_011 ledger entry); smoke, seed check, diagnostic and plan steps are outside the cap
- **streams_and_budgets**: MANDATORY: 2x2 (J9, SP8, A4, A2) 4 workers 1800 s (starts at t0); gti 2 workers 2400 s (starts at t0); repro_2x2 2 workers 900 s (after 2x2); g11_2x2 2 workers 1500 s (after 2x2; mandatory sample first, then the optional rest). OPTIONAL: feas 1 worker 1200 s (starts at t0). At most 8 worker processes at once (watchdog and orchestrator not counted).
- **rate_math**: before the source freeze the smoke timings are converted into a projected per-stream wall time (ledger rate_math_011, docs/research/v0.9.0/RATE_MATH_011.md); if a mandatory stream projects above 70% of its budget, the budget/worker split may be changed ONCE before the freeze as a disclosed deviation; nothing after run_start.
- **projection**: at RUN_T0 + 360 s the orchestrator writes PROGRESS_011.json (cases done, rate, projected finish); reported, nothing changes.
- **watchdog**: scripts/watchdog_011.py started by the operator (nohup, own session) right after RUN_T0; HEARTBEAT_011.jsonl every 2 s; at RUN_T0 + 7200 s SIGTERM to the orchestrator and every stream process group in RUN_STATE_011.json, SIGKILL after 20 s, STOP_011.json with kill wall time and latency; the orchestrator also enforces the cap itself.
- **at_cap**: every unfinished stream is stopped; its checkpoint is sealed as it is (outside the cap); ledger stop_011; NO extension and NO rerun
- **scoring**: every gate whose inputs are incomplete at the cap or whose mandatory stream completed after RUN_T0 + 7200 s is FAIL (reason STUDY_BUDGET)

## Feasibility (ungated)

- **gated**: False
- **script**: scripts/feasibility_011.py (stream "feas", optional phase)
- **worlds**: per seed: random.Random(seed) Moore machine with n states (n = 6, 7, 8 from feasibility_seeds), 2 actions, 4 codes (2 bits), transitions and outputs uniform, regenerated until every state is reachable from state 0; 32 uniform random actions; each observation bit hidden with probability 0.35
- **measurement**: at T in {8, 16, 24, 32}: build brute.region.RegionK(n, 2, 4, masks[0..T], actions[0..T-1], conf_budget=100000, symmetry=True) with the state bound = n; time the build, feasible, support(0), support(1), saturated(), y1k(0, mask_T), y1k(1, mask_T); record variables, clauses, unknowns
- **reports**: per n and T: median / p95 / max wall of build + queries, unknown fraction, feasible == True on every case (Exact sanity: the generating machine is in the region); projection of a 2x2 study (44 steps, about 2 x 7 queries per step) at n = 7, 8 per case and per 792 cases; labelled Observed (timing on the shared 8-CPU box) and Inferred (projection)
- **prediction**: Open (Inferred: build stays sub-second; y1k at n = 8, T = 32 may hit the conflict budget on some cases).

## Limitations

- Synthetic deterministic worlds only.
- K = 4 was chosen from seen data (exploratory lag diagnostic, disclosed); held-out seeds of this plan were never touched.
- drift4 is one drift generator with jumps every 11 steps; stacked jumps (lags > 11) and other drift processes are not covered by J9.
- The second implementation and the learners are by the same author.
- Breadth (k > 2, s = 3) is not re-tested in v0.9.0.
- Commit and ledger times are author-set.
- A VM pause cannot be prevented from inside the VM; the cap counts paused time against the study (conservative).

## Open

- Soundness against lag-1 silent jumps with useful coverage: Open (Inferred impossible within worst-case jump semantics without vacuity; would need a probabilistic or announced-drift model)
- A rate- or prior-based (probabilistic) drift model: Open
- Region re-entry after a jump (second region conditioned on one jump in the last W): Open (not attempted; J9 is the hull half of it)
- Stochastic worlds, learned family selection, grounding beyond templates, independent audit: Open
- Cause of VM heartbeat gaps: Open
