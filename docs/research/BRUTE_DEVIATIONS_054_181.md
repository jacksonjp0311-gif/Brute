# Deviation #181 (study-054, v0.51.0): pre-run declarations

Written before the source freeze (2026-10-31T17:52:50-04:00, box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_054 (plan/v0.51.0, commit
29e8697) as superseded by amendment BRUTE_PLAN_054a (commit 76c1e29, ledger preregistration_054a 76b10fd) that the plans leave
open. It changes no threshold, seed, cap or gate. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Clique decision (Exact citation; Inferred reasoning).** Plan 054 fixed a maximum clique of pairwise-apart trace nodes to the
   first colours. This is the same mechanism that study-041 (v0.38.0 encoding audit, GATES_041 at 40d1484) isolated as encaudit16 E2:
   E2 decided 28/30 against 30/30 for the encoding without the clique, at a call-wall ratio of 4.18 [2.53, 6.46] (deviations #154,
   #155), and A16 dropped it (#157). Same mechanism, so the plan was superseded pre-data, before any build code or seed use, by
   amendment 054a (the original plan file untouched). certify/20t drops the clique and keeps A16's first-visit symmetry, apartness
   and conflict resume; its one search change is that the rival queries ('future', then 'start') are asked ONCE at size N.
2. **Single rival at N (Exact argument; Simulated check).** A rival with n' <= N states consistent with the trace that separates from
   M1 becomes an N-state rival by adding N - n' unvisited states; first-visit numbering and apartness constrain only visited states,
   so the size-N query is UNSAT iff every size n_min..N query is UNSAT. Verdicts equal certify/16e's; M2 (and so the next
   experiment) may differ. tests/test_certify20t.py checks verdict and n_min equality on a 3-state development world at N 3, 4, 5.
3. **Process (Exact).** preregistration_054 (29e8697), preregistration_054a (ledger 76b10fd), build_authorization_054 (ledger
   f054c36, James's STANDING GO t133s553, ledger 76b30d5), seedcheck_054 (SEEDCHECK_054 at 99375a5, ledger f090315; also scans
   compressed files), then prefreeze_smoke_054, source_freeze_054, run_start_054, run_end_054, recount_054, reference_054,
   api_checks_054, tests_054, gates_054. Lean process; an interrupted run is never relaunched; a partial block is sealed as such.
4. **Arms and caps (Exact).** scale20t: 6 worlds 12170001-12170006 (first N20T), API20T and API20T_b (certify/20t, two passes) and
   API16E20 (certify/16e) at bound 20, C = 50000, B = 2000000. compat20t: 6 eps-0 controls 12190001-12190006 (first NC20T), API20T
   against API16E (certify/16e) at bound 16, C = 50000, B = 3000000. The compat arm is named API20T as in the plan (one name per
   API, the key separates the blocks). max_chunks None everywhere.
5. **Conflict-only stop for ALL arms (Exact, from code).** hook None on every arm; wall_guard_case_s = 900 s is a safety net only;
   the runner asserts hook_arms == 0 on every record and records hard_kill_s = 900. A 900 s firing is a hard kill (fails GDET54)
   and never a label.
6. **Two concurrent 4-worker pools (Exact, from code).** scale20t on 4 workers, compat20t on 4 workers, max_tasks_per_child 1.
7. **GDET54 rule (Exact).** canon16e(API20T) == canon16e(API20T_b) and equal conflicts_spent on 6/6 scale20t cases, and 0 hard kills
   (kill = wall_guard firing).
8. **GFID54 scope (Exact).** api_checks_054 replays every record; the API20T records (12 scale20t + 6 compat20t = 18) are gated, the
   certify/16e records (API16E20, API16E) are replayed and reported. GS_ref audits the API20T arms only (2400 s budget, 20/20
   mutations); if no API20T record is decided the reference passes vacuously (recorded as vacuous true), as in 053.
9. **Runner fix before the freeze (Exact; Observed).** Prefreeze attempt 1 on smoke block 1 FAILED (published as-is,
   results/diag-054/PREFREEZE_SMOKE_GATES_054_attempt1.json, 2df545e): the runner overwrote the record's full api_result with its
   API name, so the GFID54 self-replay was exact on 0/10 records ('api_result' diff on every record). Fix 32b3bae keeps the full
   api_result in a['api'] (the 047 convention) and adds a test. Smoke was rerun once as smoke block 2 (/tmp/s54/smoke2) on the
   fixed runner; nothing else changed. Smoke block 1 labels and conflicts equal smoke block 2's on all 10 records.
10. **Smoke layout (Exact).** Smoke uses 12210001-02 (scale20t, three arms) and 12210003-04 (compat20t, two arms); 12210005-06 are
    declared in the smoke range and unused. Smoke is never gated and never sets C or B.
11. **Smoke observation (Observed; Inferred risk to H5).** In both smoke blocks every scale20t record (12210001-02, API20T, API20T_b
    and API16E20) spent its whole 2M budget undecided (IDU, stop unknown). compat20t: all four records ID, compat equal 2/2.
    H5 (gain) may fail; this is recorded, not acted on: no cap, seed or rule changes.
12. **Cut (Exact rule; Observed decision).** Rule: N20T 6 -> 4 if the projected run > 3300 s, then NC20T 6 -> 4. Projection
    (Inferred, PREFREEZE_SMOKE_GATES_054): r_min = min(slowest smoke rate 4722.1/s, declared 4503/s) = 4503/s; every job's worst case B / r_min + 10 s; LPT per
    4-worker pool: scale20t 18 jobs worst 2270.7 s (mean 1858.9 s), compat20t 12 jobs worst 2028.7 s; run = max = 2270.7 s <= 3300 s.
    No cut: N20T = 6, NC20T = 6 (runner agrees, cut_consistent true).
13. **Names (Exact).** The study name in the JSON is unchanged (BRUTE-0510-SCALE20-TREECOLOR-054, as the plan); code docstrings call
    the design SINGLERIVAL-054a. Prefreeze result on smoke block 2: PASS (aa1a9d2, ledger f7651b1): recount and reference rc 0 (reference smoke 2/2 decided audited, 0 mismatches, 20/20
    mutations); synthetic fidelity self-replay 6/6 gated + 4/4 reported exact; gates reproduce byte for byte; smoke determinism 2/2;
    hook_arms 0 on all 10; verifier chain passes with 0 authorization exceptions. GS20T_gain54 fails on smoke (0 decided at 20 states),
    recorded not required.
