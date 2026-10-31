# Deviation #152 (study-040, v0.37.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold or gate in BRUTE_PLAN_040. Each
item records a choice the plan left open, a reading of a criterion, or an observation made before any main case was run.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4).

1. **Authorization and seeds (Exact).** preregistration_040 (ledger a9219a1, 23:08:30 EDT) and build_authorization_040
   (ledger 43b9592, 23:08:41 EDT) under James's STANDING GO t133s553 (ledger 76b30d5), plan BRUTE_PLAN_040 at
   plan/v0.37.0 401172b. seedcheck_040 PASS (results/diag-040/SEEDCHECK_040.json, commit 7d4317b, ledger 7de9f3a,
   23:20:50 EDT: 792 files scanned, 0 standalone tokens in the 040 ranges, 120 embedded only, 0 overlaps with 302 prior
   ranges, 42 cases) before any 040 seed was used. Targets: scale16 10610001-12, scale14 10620001-12, lowobs12 10630001-12,
   control 10660001-06; smoke 10680001-10680012 (declared in the plan, never gated). Box clock checked against GitHub's
   Date header at 23:36:18 EDT (GitHub 03:36:08 GMT = 23:36:08 EDT; box 10 s ahead).
   The first seedcheck attempt was killed before it wrote anything (no output file); it was relaunched once as a pre-data
   tooling check and the stale duplicate process was stopped so only one writer could create the file.
2. **Worlds (Exact).** experiments/worlds_040: scale16/scale14 = worlds_026.scale_world(seed, n); control = worlds_026
   control_cycle3; lowobs12 = 12 states, k 3, uniform random transitions, emissions in {0, 1} only, accepted iff strongly
   connected and minimal, rng Random(seed*140040+40040+n). N = nominal size.
3. **A15 / A15_cube (Exact).** brute/scalesearch15: A14's logic with the plan's one CNF change (apartness clauses for
   every pair of trace positions apart on the trace; fixed colours x[c_i] = i for a greedy clique containing position 0;
   size search from max(A14's lower bound, clique size)). Pool15 keeps one incremental instance per size; apartness clauses
   are added as the trace grows. A15_cube: when a size-n least or rival query returns capped, it is re-solved as up to n
   cubes under x[t*][q], t* = cube_pos (first trace position not in the clique); each cube is one 9.0 s call; SAT if any
   cube SAT, UNSAT if all UNSAT, unknown otherwise; bounded by the 240 s case deadline.
4. **Gate d reading (Exact; literal).** "capped cases (any capped call)" counts a case as capped if ANY call in it hit the
   9.0 s cap, INCLUDING the initial capped call that A15_cube then splits into cubes (o.capped counts it). So a case that
   is rescued by the cube split still counts as capped for d. This is the strict, literal reading; the count of cases whose
   final stop was 'unknown' on a cap is reported beside it (secondary GCAP15), not gated.
5. **Jobs (Exact; build choice).** One job per (case, arm), arms dispatched A15_cube, A15, A14, families longest first
   (scale16, scale14, lowobs12, control); 126 main jobs, 36 smoke jobs, 8 workers; the main block refuses a non-empty
   checkpoint (no resume).
6. **Runtime projection (Inferred) and the pre-declared reduction (not taken).** The smoke (36 jobs, 124.9 s on 8
   workers) gives an LPT makespan over the 126 main jobs of 391.6 s (serial 3116.9 s); with A15 on scale16 only, 346.4 s.
   Both are under the plan's 1500 s threshold, so the runtime rule does NOT trigger and A15 runs on every family.
   (results/diag-040/PREFREEZE_SMOKE_GATES_040.json, commit d80c798.)
7. **Smoke observations (Observed; no change made).** 12 smoke cases (recount PASS, 0 mismatches, 271 words checked,
   0 unsound): A15_cube ID 4, IDF 1, IDU 7, WRONG 0; A15 ID 4, IDU 8; A14 ID 5, IDU 7. On scale16 (4 smoke cases) A15_cube
   1 IDF, 3 IDU; A15 4 IDU; A14 4 IDU. On lowobs12 (3 cases) every arm is IDU; A15_cube used 111-125 s per case there.
   Reference on the smoke: 3 cases, 2 decided, 38 verdicts, 52 words, 0 mismatches, 20/20 mutations, 50.3 s.
   This suggests (Inferred, few cases) that GC15 b and GFAM15 may fail; no arm, cap or budget was changed.
8. **GINC15 observed failing before the freeze (Observed; no change made).** tests/test_scalesearch15_0370
   test_GINC15_sealed_039_traces (the plan's Exact GINC15 test, 30 sealed 039 cases x {A15, A15_cube} = 60 checks) was run
   twice before the freeze. Second run (unloaded, 177.3 s): 3/60 mismatches, all of the form stored A14 [ID, 12] vs
   [unknown, 12]: perm12 10540007 (A15), perm12 10540008 (A15 and A15_cube). The first run (under load from the
   seedcheck) also failed. No mismatch is a different DECIDED verdict: A15 never returned a verdict A14 contradicts; it ran
   out of the 9.0 s cap where A14 did not. Single-case check on perm12 10540008, unloaded: A14 stop_check14 ID in 7.3 s;
   A15 (no cube) unknown after 15.7 s (1 capped call); A15_cube unknown after 24.4 s and 24.2 s (2 capped calls). So on
   these 12-state permutation traces the apartness and fixed-colour encoding is SLOWER than A14's, and the cube split does
   not rescue it inside the cap. The result is timing-dependent (which cases fail can change with load). Per the plan
   ("failures are published, not tuned") the encoding, cap and test were NOT changed; GINC15 is expected to fail in the
   official suite, which also fails GTI. Plan 040 next_if_fail: if GINC15 fails, an encoding audit, not a new arm.
9. **Test change before the freeze (Exact).** test_ID_stop_checked_by_enumeration first used Random(4005), which drew only
   2 ID stops in 40 worlds, below its coverage threshold (> 5). A14, A15 and A15_cube all gave the same stop on all 40
   worlds (2/2/2 ID), so the low count is the draw, not the arm. It now uses Random(3903), the seed of the frozen
   test_scalesearch14_0360 test (9/9/9 ID, identical stops). The check (every ID stop confirmed by enumeration) is unchanged.
10. **Cube path test (Exact).** The cube path is not reached on instances small enough to enumerate, so the test forces it:
    a ForcedCube subclass makes the first solve of each query return capped, and the test requires more cubes than
    comparisons and the same stop and n_min as stop_check14 on every comparison.
11. **Reference, recount, gates (Exact; readings).** run_reference_040 audits A15_cube on scale14 (N 14, K 128) against the
    independent exhaustive-region check plus 20 mutations. recount_040 regenerates each world and trajectory, re-labels
    (K 128 for every arm), re-checks every executed word and flags any stored field that differs. make_gates_040 implements
    the plan's gates; counts use Wilson CIs, GC15 c the paired per-seed ID difference with a seed bootstrap CI
    (10000 resamples, Random(34)); GFAM15 is NOT_EXERCISED (pass None) if A15_cube's mean extra actions on lowobs12 < 3;
    GQB15 reads the max single-call wall of A15 and A15_cube (10.5 s); GSYM15 and GCAP15 are secondary (reported only).
12. **G_PROC order (Exact; reading).** preregistration -> build_authorization -> seedcheck -> source_freeze -> run_start ->
    run_end -> recount -> reference -> tests (all _040), non-decreasing ledger times, commit-order file, main sealed.
13. **Tests and release tooling (Exact).** python -m unittest (no pytest). scripts/run_tests_0370 runs
    test_scalesearch15_0370, the frozen 0360/0350/0340/0330/0320/0310/0300/0230 search tests, test_scripts_040 and
    test_release_0370 in subprocesses; the GTI input is written only with --official. verify_release_0370,
    release_version_0370, study040_storage and push_checkpoint_040 follow the 0360 pattern (new files).
14. **Open.** Whether the apartness/cube encoding moves scale16 off the query cap is what the main run answers; the smoke
    (item 7) and item 8 are not evidence for any gate.
