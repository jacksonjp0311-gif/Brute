# Deviation #150 (study-039, v0.36.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold or gate in BRUTE_PLAN_039. Each
item records a choice the plan left open, a reading of a criterion, or an observation made before any main case was run.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4).

1. **Authorization and seeds (Exact).** build_authorization_039 was ledgered (ledger 0f90554, 2026-10-30 22:11:22 EDT; box
   clock 22:11:18 EDT against GitHub's Date header 02:11:15 GMT = 22:11:15 EDT) under James's STANDING GO t133s553 (ledger
   76b30d5), plan BRUTE_PLAN_039 at plan/v0.36.0 d2ebf63. seedcheck_039 PASS (results/diag-039/SEEDCHECK_039.json, commit
   a7212f9, ledger 2587d4c: 778 files scanned, 0 standalone tokens in the 039 ranges, 65 embedded only, 0 overlaps with 295
   prior ranges, 54 cases) before any 039 seed was used. Target ranges: scale12 10510001-12, scale14 10520001-12, scale16
   10530001-12, perm12 10540001-12, control 10560001-06; smoke 10590001-10590012 (declared by scripts/check_seeds_039.py,
   outside every plan and earlier range): scale16 x3, scale14 x3, scale12 x2, perm12 x3, control x1.
2. **Worlds (Exact).** experiments/worlds_039: scale12/14/16 = worlds_026.scale_world at n 12/14/16 (k 3, 2-bit emissions,
   minimal, strongly connected); perm12 = 12 states, k 3, every action a permutation of the states, rejection-sampled until
   minimal and strongly connected; control = worlds_026 control_cycle3. Declared bound N = the nominal size.
3. **A14 (Exact).** brute/scalesearch14.active14 = A9's stop rule, labels, least machine, rival search n_min..N and shortest
   separating word, with ONE incremental SAT instance per candidate size kept across rounds (clauses only added; rival
   clauses under a retired activation literal). Same verdicts as RegionK by construction (definitional variables only);
   GINC14 tests that on the sealed study-034 A9 traces (36 cases, 307 verdicts, 0 mismatches: Exact, test run before the
   freeze). Every solve is capped at QUERY_S14 = 9.0 s by the host TimerHook; one call is one query. A14: K 128, 240 s;
   A14_k64: K 64, 120 s. A14_random: the prefix plus min(used(A14), 128) seeded uniform actions (Random(seed*91039+39)),
   then stop_check14 (fresh pool, 240 s). A9: the frozen brute_study_034.arm_A9 (its own 10 s cap, no hook).
4. **Jobs per (case, group) (Exact; build choice).** The runner dispatches one job per (case, group): groups A14 (A14 then
   A14_random, which needs A14's count), A14_k64 and A9; group-major order (all A14 jobs first), keys longest first
   (scale16, scale14, scale12, perm12, control); 162 main jobs, 36 smoke jobs, 8 workers. The checkpoint holds one line per
   job (key block:key:seed:group); the sealed RESULTS holds one record per case with arms merged. group_walls_informational
   is stripped from SCIENTIFIC.json. The main block refuses a non-empty checkpoint (no resume).
5. **Runtime projection (Inferred) and the pre-declared reduction (not taken).** The smoke (36 jobs, 127.4 s elapsed on 8
   workers) gives an LPT makespan over the 162 main jobs from the mean smoke group wall per (group, key) of 312.1 s
   (serial 2493.3 s); with A14_k64 on scale16 only it would be 282.5 s. Both are far under the plan's 1500 s threshold, so
   the plan's runtime rule does NOT trigger: A14_k64 runs on every family (plan_groups unchanged). G_RT (1800 s cap) is
   evaluated on total_elapsed_informational; the run is not killed at the cap.
6. **Smoke observations (Observed; no change made).** On the 12 smoke cases (recount PASS, 0 mismatches, 321 words checked,
   0 unsound): A14 ID 7, IDF 2, IDU 3, WRONG 0; A14_k64 ID 6, AMB 4, IDU 2; A14_random ID 4, AMB 5, IDU 3; A9 ID 5, IDF 1,
   AMB 3, IDU 3. Every scale16 smoke case is IDU for A14, A14_random and A9 (a capped query makes the stop 'unknown'), and
   AMB or IDU for A14_k64. This suggests (Inferred, 3 cases) that GC14 b may fail with caps dominant; no arm, cap or budget
   was changed (no tuning).
7. **Reference (Exact; reading).** scripts/run_reference_039 audits arm A14 on scale14 (N 14, K 128) against an
   independent exhaustive-region check, plus 20 mutations. On the smoke it decided 3/3 cases, 59 verdicts, 45 words,
   0 mismatches, 20/20 mutations detected, 143.0 s on 3 workers (Observed). GS_ref requires study_results_sha256 to match,
   cases = the scale14 count, 0 mismatches, decided > 0, 20/20 mutations.
8. **Recount (Exact; reading).** scripts/recount_039 regenerates each world and trajectory, re-labels with the 034 rule (K:
   A14 128, A14_k64 64, A9 64), re-derives A14_random's random actions from the seed, re-checks every executed word and
   every extra reading, and flags any stored field that differs.
9. **Gates (Exact; readings).** make_gates_039 implements the plan's gates. 'complete' requires the sealed main block, 54
   cases with the plan counts, and each case's arm SET equal to arms_of(key) (plan_groups). Fix before the freeze: the first
   version compared the ordered arm tuple, which fails on every case because sealed JSON is written with sorted keys; the
   pre-freeze test (tests/test_scripts_039, the #129 lesson) caught it and it now compares sets (commit 02e7a20). GC14 c and
   GCH14 use the paired per-seed ID difference with a seed bootstrap CI (make_gates_034.boot_mean); counts use Wilson CIs.
   GQB14 reads query_max_s of A14, A14_k64 and A14_random (bound 10.5 s); A9 is reported, not gated, as it has its own cap.
   GK14 and GACT14 are secondary (pass None, reported only). GINC14 and GTI read TEST_SUITE_039 (run_tests_0360 --official).
10. **G_PROC order (Exact; reading).** preregistration_039 -> build_authorization_039 -> seedcheck_039 -> source_freeze_039
    -> run_start_039 -> run_end_039 -> recount_039 -> reference_039 -> tests_039, ledger times non-decreasing, the commit
    order file present and the main block sealed.
11. **Test change before the freeze (Exact).** tests/test_scalesearch14_0360 test_ID_stop_checked_by_enumeration first used
    12 random worlds, which gave only 3 ID stops against its own coverage threshold (> 5); it now uses range(40) worlds
    (commit 4a88db4). The check itself (every ID stop confirmed by enumeration) is unchanged; no result was tuned.
12. **Tests and release tooling (Exact).** pytest is not installed on the box, so every suite runs with python -m unittest.
    scripts/run_tests_0360 runs test_scalesearch14_0360, the frozen 0350/0340/0330/0320/0310/0300/0230 search tests,
    test_scripts_039 and test_release_0360 in subprocesses (900 s each); the GTI input is written only with --official.
    scripts/verify_release_0360 and brute/release_version_0360 follow the 0350 pattern (new files; earlier ones frozen).
13. **Storage (Exact).** scripts/study039_storage packs CHECKPOINT/RESULTS/SCIENTIFIC into a checked archive for the repo;
    the raw files are .gitignored. scripts/push_checkpoint_039 --pid pushes checkpoint snapshots while the run is alive.
14. **Open.** Whether 14 or 16 states are within reach of the clean B = 0 line at these caps is the question the main run
    answers; the smoke (item 6) is not evidence for any gate.
