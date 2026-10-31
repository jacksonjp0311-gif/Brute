# Deviation #176 (study-051, v0.48.0): post-run record

Written after the seal and the gates (2026-10-31, box-local EDT, UTC-4). It changes no threshold, seed, cap or gate, and no frozen
file. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Run (Exact).** source_freeze_051 at 9c53632 (337 files; ledger 72ac271); main launched 13:11:44 EDT under nohup setsid (PID
   1227129; phase A 24 scale20 jobs on 4 workers, phase B 42 jobs on 8; run_start_051 ledger fc02fe0). Normal exit at 13:39 EDT,
   66/66 jobs in 1656.2 s of 3600 s (phase A 1636.8 s, phase B 19.4 s); six checkpoint snapshots (70911c0 to 221f493); sealed and
   packed at b4cc653; run_end_051 ledger 8a41ded. Run once; never relaunched, restarted or killed; the resume clause was not used.
   No cut (#175 item 11).
2. **Agent interruptions (Exact).** The session was interrupted during the run and during api_checks. No process was touched:
   the run, the reference and api_checks_051 (started 14:08 EDT, exited 14:23 EDT with PASS false) each ran once to their own end,
   and each output was committed as-is. Nothing was rerun.
3. **Scoring commits (Exact).** RECOUNT_051 8c8afad (ledger 5b73278), REFERENCE_051 c2ae74b (d6d0a72), API_CHECKS_051 44a5bb7
   (44e8585), TEST_SUITE_051 e941117 (749c72a; 8 gated modules, 79 tests, all passed; 2 reported modules, 17 tests, passed),
   GATES_051 e7138c5 (82547ed). Post-run diagnostic (informational, not a gate) 76345ac.
4. **Gates (Exact). 9 of 15 gated pass; 6 fail.** Intervals are Wilson 95%.
   - FAIL GDET51: 26/30 canon equal [0.70, 0.95] (scale20 8/12, control 6/6, noise12 12/12); the 30 s per-chunk guard fired on 5
     scale20 records (API16S 11830007, 11830008, 11830009, 11830010; API16S_b 11830010). The 4 unequal scale20 pairs are the 4 seeds
     with a firing; every label pair is equal (IDU/IDU).
   - FAIL GFID51: 25/30 exact [0.66, 0.93] (API16S 7/12, API16E 6/6, API16N 12/12). Why api_checks failed (Observed): the five
     non-exact replays are scale20 API16S 11830006, 07, 08, 09 and 10; 07 to 10 are the records whose chunk guard fired in the run,
     and the diffs are in per-call conflicts, chunks and capped flags (08 also in the trace word); 11830006 had no firing in the
     run, so its replay most likely hit the guard or a different cap (Inferred). The ghost half passed (GHOST51).
   - FAIL GS20_sound51: 0/12 API16S ID or IDF [0.00, 0.24]; 11 IDU (B20 spent) and 1 AMB (11830001, K spent) on both passes.
     WRONG 0; both decided (AMB) scale20 records audited at bound 20 with 0 mismatches. Fails on the non-vacuity clause.
   - FAIL GCOMPAT16S: 5/6 [0.44, 0.97]. 11850004: labels equal (IDF / IDF), machines differ from start state 0. The diagnostic
     (scripts/diag_compat_051.py, Observed) shows the two 12-state machines are isomorphic with a different start state (API16E's
     state 0 maps to API16S_c's state 4), and both match the truth on the future. IDF means identified from the current state,
     not from the start, so the frozen rule (same machine from state 0 for ID and IDF) is stricter than the label promises. The
     gate stays failed as frozen; the reading is Inferred.
   - FAIL G10: 4/6 controls ID on both passes [0.30, 0.90]; 11850001 and 11850004 are IDF on both passes (the frozen rule asks
     for ID). Nothing spent its budget.
   - FAIL GQB25: 5 chunks over 30 s (max 54.3 s, C20 12000) and 0 case walls over 600 s (max 352.2 s).
   - PASS GN12_sound51 (WRONG 0 on 24 noise records, 0 majority errors; API16N 11/12 ID+IDF [0.65, 0.99]; 1 AMB), GHOST51 (new
     module brute.api.certify16s, 0 sockets, 16e and 16n closures unchanged), GS_ref (38/38 decided audited, 0 mismatches, 20/20
     mutations; 12-state pool 29.1 s, scale20 387 s and 403 s), G_sound (608 words, 0 unsound), G_recount, GTI, GTEST, G_PROC,
     G_RT (1656.2 s).
5. **Secondary (Observed, not gated).** GS20_rate51 0/12 [0.00, 0.24] beside 050's certify/16e 1/24 [0.01, 0.20] at B20
   4000000 (GS20_vs50). GRATE51: API16S 7922 conflicts/s per record (5713 to 18530), 7965/s per chunk; API16S_b 8053/s; part c
   36034/s; API16N 40141/s. GN12_rate 11/12, 2456 observations, 53.5 reads per observation, k 27 to 63. GCOST51: API16S 12
   records, 3020 s arm wall, 23.9M conflicts, 217 capped calls, 11 budget-spent.
6. **Reading (Inferred).** Isolating scale20 in phase A on 4 workers did not stop slow chunks: five chunks of 12000 conflicts took
   49 to 54 s (about 220 to 245 conflicts/s), and all five were in phase A's second round. A guard firing makes a record wall-
   dependent, which accounts for GDET51, GFID51 and GQB25. B20 2000000 decides no 20-state case with certify/16s; whether the
   symmetry-breaking clauses help at all is still Open (11 of 12 cases spent B20 at about 8000 conflicts/s). The G10 and GCOMPAT16S
   failures come from IDF labels, which the frozen rules treat as stricter than the label means. Soundness held everywhere it was
   checked: WRONG 0, 0 reference mismatches, 0 majority errors. noise12 replicated: certify/16n 11/12 ID+IDF on fresh worlds, as in
   050 (11/12), with GN12_sound51 passing in both studies. Nothing new is certified, because the gate set did not pass as a whole.
7. **Claim scope (Inferred).** Every ID / IDF is conditional on the declared N (20 for scale20, 12 otherwise) and, for certify/16n,
   on iid flips with eps <= eps_bar. A larger machine can copy the true machine on every visited state and differ only on states
   the trace never reached, so no finite trace rules it out.
8. **Branch (Exact).** noise12 replicated (GN12_sound passed in 050 and 051, 11/12 in both), so plan 052 (v0.49.0) puts
   certifying certify/16n first, as instructed; scale20 work is secondary.
