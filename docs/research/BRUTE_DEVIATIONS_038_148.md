# Deviation #148 (study-038, v0.35.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold or gate in BRUTE_PLAN_038. Each
item records a choice the plan left open, a reading of a criterion, or an observation made before any main case was run.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4).

1. **Authorization and seeds (Exact).** build_authorization_038 was ledgered (ledger bbda857, 2026-10-30 20:58:21 EDT) under
   James's STANDING GO t133s553 (ledger 76b30d5), plan BRUTE_PLAN_038 at plan/v0.35.0 e070773 (ledger 23c5a63).
   seedcheck_038 PASS (results/diag-038/SEEDCHECK_038.json, commit 12d0fde, ledger f8aa0e7: 765 files scanned, 0 standalone
   tokens in the 038 ranges, 47 embedded only, 16/16 negative controls refused, 42 cases) before any 038 seed was used.
   The plan declares no smoke range; scripts/check_seeds_038.py declares the smoke range 10490001-10490030 (outside every
   plan range and every earlier range, the 037 smoke range included); the smoke block uses the first 7 (noisy_scale12 x2,
   clean_scale12 x2, noisy_scale8 x2, control x1).
2. **Arms (Exact).** A13_r5 (B_max 2) and A13_r3 (B_max 6) run brute/scalesearch13.active13: A12's stop check, sound stop
   and labels, with the least-B search and the B_max confirmation on one incremental SAT instance per call (pysat
   ITotalizer over the flip literals, 'at most b flips' as an assumption; clauses only added). Least B by unit increments
   from lo (search 'unit_incremental'). Frozen controls: A12_r5, A12_r3 (search 'double', stop 'sound', from
   scalesearch12), A11_r3 (bisect, from scalesearch11), S7 (B 27). Arm order A13_r5, A13_r3, A12_r5, A12_r3, A11_r3, S7.
   QUERY_S 9.0 s per query for every arm (host TimerHook), GQB13 bound 10.5 s, K 64, BUDGET 120 s per arm.
3. **A13 confirmation at n = N (Exact; reading).** confirm13 applies A12's confirm12 verdict rule (future mode first; start
   mode only when future is UNSAT and the check claimed ID), but each mode is ONE query at n = N, not the n = 1..N loop:
   an N-state region contains every machine of <= N states, so the verdict is the same (the rival found may differ).
   The rival clauses are added under a fresh activation literal and retired after the solve. Stored verdicts are a single
   entry [[N, v]]. recount_038 re-derives A13 confirmations with c = N (A12 arms keep c = 1..N); run_reference_038 checks
   that every A13 confirmation entry has n == [N].
4. **Capped confirmation (Exact; definition).** An (arm, case) is a 'capped confirmation' case when any of its B_max
   confirmation verdicts is 'unknown' (a future or start query capped at 9.0 s, or the deadline passed). Recorded per arm
   record as confirmations_capped (count of rounds whose confirmation verdict is 'unknown'); GR13 d and GH2 count cases
   with confirmations_capped > 0. This is the plan's quantity; the record field name is a build choice.
5. **Confirmation walls (Exact; informational field).** For task item 3 the runner stores, per round with a confirmation,
   confirm.walls_informational = the last c entries of that round's query walls, c = the number of confirmation verdicts.
   The key ends in _informational, so brute.evaluation.no_time strips it from SCIENTIFIC.json (no gate reads it). Caveat
   (Inferred): a verdict set to 'unknown' by the arm deadline before a solve starts has no wall, so c may count one wall
   of the preceding least-B probe instead; the smoke reports these walls as Observed with that caveat.
6. **Tests and release tooling (Exact).** scripts/run_tests_0350.py keeps the 0340 scratch default (output in the system
   temp dir; the GTI input is written only with --official). Modules: test_scalesearch13_0350 (GSAFE13, GINC13, incremental
   vs fresh, confirm13 vs confirm12, sound ID by enumeration, host-agnostic), the frozen 0340/0330/0320/0310/0300/0230 search tests, test_scripts_038, test_release_0350.
   GSAFE13 and GINC13 are read by make_gates_038 from TEST_SUITE_038 (inside GTI).
7. **G_PROC order (Exact; reading).** As #146 item 6: make_gates_038 checks preregistration_038 -> build_authorization_038
   -> seedcheck_038 -> source_freeze_038 -> run_start_038 -> run_end_038 -> recount_038 -> reference_038 -> tests_038;
   gates_038 is ledgered after GATES_038.json is written.
8. **Development seeds (Exact).** Development tests use the old published seeds 10050001 (control) and 10090005
   (noisy_scale8). No 038 seed was used before the smoke. Nothing was tuned.
9. **Clock (Observed).** Box clock vs GitHub's Date header at build authorization: 20:58:21 EDT vs 00:58:15 GMT (box about
   6 s ahead).
