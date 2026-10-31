# Deviation #180 (study-053, v0.50.0): post-run record

Written after the seal and the gates (2026-10-31T16:39:29-04:00, box-local EDT, UTC-4). It changes no threshold, seed, cap or gate, and no frozen
file. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Run (Exact).** source_freeze_053 at 535aa05 (395 files; ledger 42d6e2f); main launched once at 15:49:39 EDT under nohup (PID
   1346226; part B 6 jobs on a 1-worker pool, part A 42 jobs on a 7-worker pool; run_start_053 ledger 0c685bd), with the
   checkpoint pusher (PID 1346471). Normal exit at about 16:07 EDT, 48/48 jobs, 27 cases, 1048.2 s of 3600 s; four checkpoint
   snapshots (e98c4e8, 280ad98, 40faf24, 7cddeda); sealed and packed at 93a4226; run_end_053 ledger 1ded628. Run once; never
   relaunched, restarted or killed; the resume clause was not used. Cut as declared in #179 item 5: N16BAR = 6, N20C = 3.
   The agent session was interrupted once while main ran (about 15:52 EDT); nothing was touched and the run continued.
2. **Scoring commits (Exact).** RECOUNT_053 5e89d4a (ledger a35e9c0), REFERENCE_053 80f699c (e669fdd), API_CHECKS_053 e366cb1
   (2a15bc5), TEST_SUITE_053 0e04c33 (befbe11; 8 gated modules, 84 tests, all passed; 2 reported modules, 19 tests, passed),
   GATES_053 8725569 (933025c); make_gates_053 --check reproduces it.
3. **Gates (Exact). 13 of 13 gated pass; certified_16n_N16 true.** Intervals are Wilson 95%.
   - GDET53: 12/12 noise16 cases canon16n equal across the two passes [0.76, 1.00]; 0 wall-guard firings on 42 part A records.
   - GFID53: 42/42 part A records replay exactly [0.92, 1.00]; part B 6/6 also exact (reported).
   - GN16_sound53: WRONG 0 of 30 noise records [0.00, 0.11], 0 majority errors. eps 0.05 API16N16 ID+IDF 7/12 [0.32, 0.81]
     (7 ID; 4 IDU budget spent: 12050001, 12050003, 12050004, 12050005; 1 AMB K_spent: 12050002), >= 4/12 so non-vacuous.
     eps 0.10 = eps_bar API16N16_bar 4/6 [0.30, 0.90] (4 ID; 12070002 IDU, 12070005 AMB K_spent).
   - GCOMPAT16N53: 6/6 [0.61, 1.00] (4 ID with the same machine from state 0; 1 IDU and 1 AMB on both sides); canon16e equal 6/6.
   - GHOST53 (16e, 16n, 16s closures unchanged; certify16n sha bound to the 050 freeze; 0 sockets), GQB27 (part A: max chunk
     9.0 s of 30 s, max case 165.9 s of 600 s), GS_ref (31/31 decided part A records audited, 0 mismatches, 20/20 mutations; 782 s
     of 2400 s), G_sound (900 words, 0 unsound, 0 compat WRONG), G_recount, GTI, GTEST, G_PROC, G_RT (1048.2 s).
4. **Non-blocking part B (Exact; not gated).** GS20C_det53 pass: 3/3 scale20c cases canon16e identical [0.44, 1.00], conflict
   counts identical per case (2002403, 2000569, 1558927), 0 hard kills at 900 s, hook_arms 0. GS20C_sound53 pass: WRONG 0 of 6
   records, but 0/3 decided (2 IDU budget spent, 1 AMB K_spent), so it is vacuous. Max part B case wall 226.5 s.
5. **Secondary (Observed, not gated).** GN16_rate53: eps 0.05, 54.3 reads per observation, k 27 to 63; eps 0.10, 54.7 reads per
   observation. GS20C_rate53: about 10.4k and 10.8k conflicts/s on the single worker. GCOST53: API16N16 11.85M conflicts and
   151591 reads over 12 records; compat arms 8.89M conflicts each.
6. **Projection (Inferred, checked).** #179 projected part A worst 2724.9 s and part B worst 2724.9 s at 4503 c/s; observed 1048.2 s
   total. The compat16 uncapped worst case (676.2 s) did not occur: max compat case 144.6 s.
7. **Reading (Inferred).** certify/16n met every gate of plan 053. Under plan 053's next_if_pass, certify/16n is certified for
   declared N <= 16 under iid flips with eps <= eps_bar = 0.10 at per-record failure probability <= delta = 0.001, with C 50000
   and B 1500000 (Exact conditional on the model and the declared N). Decision rates at 16 states are lower than at 12 (7/12 vs
   23/24 at eps 0.05); undecided records spent their budget. Part B: the conflict-only stop removed run-to-run variance at 20
   states on 3 cases (in 051 the 30 s chunk guard fired on 5 scale20 records), but nothing at 20 states was decided at B20 2M.
8. **Claim scope (Inferred).** Every ID / IDF is conditional on the declared N (16) and on iid flips with eps <= eps_bar. A larger
   machine can copy the true machine on every visited state and differ only on states the trace never reached, so no finite trace
   rules it out.
9. **Branch (Exact).** All gated pass and GS20C_det53 passes, so v0.51.0 follows next_if_pass: the conflict-only stop is the fix
   for run-to-run variance at 20 states, and the next scale-20 version raises decisions with a different encoding or search, not
   more budget.
