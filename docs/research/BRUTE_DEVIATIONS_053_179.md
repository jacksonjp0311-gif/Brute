# Deviation #179 (study-053, v0.50.0): pre-run declarations

Written before the source freeze (2026-10-31T15:49:08-04:00, box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_053 (plan/v0.50.0, commit 045ca29)
that the plan leaves open. It changes no threshold, seed, cap, eps, eps_bar or delta, and no gate. Labels: Exact, Observed,
Simulated, Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_053 (plan 045ca29, ledger 317b125), build_authorization_053 (ledger e941937, cites James's
   STANDING GO t133s553, ledger 76b30d5), seedcheck_053 (ledger a7a1f28; SEEDCHECK_053 at c887582), then prefreeze_smoke_053,
   source_freeze_053, run_start_053, run_end_053, recount_053, reference_053, api_checks_053, tests_053, gates_053. Lean process.
   The resume clause is not approved: an interrupted run is never relaunched; a partial block is sealed as such.
2. **Arms and caps are the plan's (Exact).** Part A. noise16: 12 worlds (12050001-12050012), API16N16 and API16N16_b
   (certify/16n at bound 16, eps 0.05, eps_bar 0.10, delta 0.001), C = 50000, B = 1500000. noise16_bar: the first N16BAR of 6
   worlds (12070001-12070006) at eps 0.10 = eps_bar, API16N16_bar once, same caps. compat16: 6 controls (12090001-12090006),
   API16N16_c (certify/16n at eps 0, one read per observation) against API16E (certify/16e) at bound 16, C = 50000, B = 3000000.
   Part B (non-blocking). scale20c: the first N20C of 6 worlds (12110001-12110006), API16E20 and API16E20_b (certify/16e at bound
   20, two passes), C = 50000, B = 2000000. max_chunks None everywhere.
3. **Conflict-only stop for part B (Exact, from code).** Part B arms run with hook None: no wall hook is armed, so a part B record
   stops only on its conflict budget or a decision. wall_guard_case_s = 900 s is set as a safety net only; the runner asserts
   hook_arms == 0 on every part B record (experiments/brute_study_053.py, 17c01c1) and records hard_kill_s = 900. Any 900 s firing
   fails GS20C_det53 (non-blocking) and is never a label. Part A keeps the 30 s chunk hook and the 600 s case guard as host safety;
   any firing fails GDET53 / GQB27 and is never a label.
4. **Two pools, 7 + 1 workers (Exact, from code).** One process, WORKERS 8: part B (2 x N20C jobs) on its own 1-worker pool,
   part A (24 noise16 + 12 compat16 + N16BAR noise16_bar jobs) on a 7-worker pool, both running in parallel; max_tasks_per_child 1.
   Job order: scale20c, compat16, noise16 (pass b in reverse seed order), noise16_bar. Gates compare arm sets, not arm order.
5. **Cut (Exact rule; Observed decision).** Rule: N20C 6 -> 3 if projected part B > 3300 s; N16BAR 6 -> 3 if projected part A >
   3300 s; never noise16 or compat16; never after the freeze. Projection (Inferred; scripts/prefreeze_smoke_053.py,
   PREFREEZE_SMOKE_GATES_053 at d3837a0): r_min = min(slowest smoke rate 7610.0/s, declared 4503/s) = 4503/s; every job's worst
   case B / r_min + 10 s with **no guard cap** (more conservative than 052's min(600 s, ...)); part A by LPT on 7 workers, part B
   serial on 1. Worst cases: part B 5449.8 s at N20C = 6 (> 3300 s) and 2724.9 s at N20C = 3; part A 2724.9 s at N16BAR = 6
   (<= 3300 s). So **N20C = 3 (cut applied), N16BAR = 6 (no cut)**; both equal the runner (cut_consistent true, cut_exhausted
   false). The runner refuses a main run unless the freeze's n_noise16_bar and n_scale20c equal N16BAR and N20C. Main: 48 jobs.
6. **Projection caveat (Inferred).** The uncapped worst case for a compat16 job is 676.2 s, above the 600 s part A case guard; at
   the smoke rates (compat16 12130005 spent 2192640 conflicts in about 102 s) it is not expected to fire. If it does, GDET53 /
   GQB27 fail and the failure is published.
7. **GFID53 replays all part A records (Exact).** api_checks_053 replays 2 x 12 noise16 + N16BAR noise16_bar + 2 x 6 compat16 =
   42 part A records (N-arm observations rebuilt from the recorded votes) and requires every one exact. Part B records are also
   replayed through Certifier16E with hook None and reported under part_b; they are not gated.
8. **GQB27 scope (Exact).** GQB27 reads chunk walls on part A only: part B has no chunk hook by design (item 3).
9. **Compat rule (Exact).** recount_053 imports compat_rule, rooted and bfs_form from the frozen recount_052 unchanged (the item 5
   rule of #177), applied to API16N16_c against API16E at bound 16. canon16e equality is reported, not gated.
10. **Pre-freeze tooling notes (Observed).** The first prefreeze_smoke_053 call was run under a 230 s shell timeout and stopped
    during the reference step before writing anything; it was rerun once with nohup and completed (PASS true). No input or
    threshold changed between the two. Synthetic gate failures, all by design or by smoke size: GN16_sound53 (>= 4 of 12 cannot
    hold on 2 smoke cases), GTI (no 053 freeze yet), GTEST (no TEST_SUITE_053 yet), G_PROC.
11. **Smoke (Observed, seeds 12130001-12130006, never gated).** noise16: 12130002 ID on both passes, 12130001 IDU on both passes,
    conflicts identical per pass; noise16_bar: 12130003 ID, 12130004 IDU; compat16 12130005: both arms AMB (K_spent), equal;
    scale20c 12130006: IDU on both passes, 2000689 conflicts each, canon16e identical, hook_arms 0. 0 majority errors, 0 guard
    firings. Smoke wall 512.7 s.
12. **Claim scope (Inferred).** Every ID / IDF is conditional on the declared N (16 in part A, 20 in part B) and, for the noisy
    arms, on iid flips with eps <= eps_bar; it holds with probability >= 1 - delta per record. Without the size bound no finite
    trace suffices: a larger machine can copy the true machine on every visited state and differ only on states the trace never
    reached.
