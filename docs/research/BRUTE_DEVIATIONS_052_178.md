# Deviation #178 (study-052, v0.49.0): post-run record

Written after the seal and the gates (2026-10-31T14:57:22-04:00, box-local EDT, UTC-4). It changes no threshold, seed, cap or gate, and no frozen
file. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **IDF-equivalence rule (Exact).** Plan 052's IDF-equivalence rule for GCOMPAT16N52 (for IDF: future_match on both records and the
   same machine rooted at the current state s1) was introduced after study-051's GCOMPAT16S and G10 IDF failures. It is applied
   only to study-052 data and not retroactively: GATES_051 (e7138c5) and every earlier gate file stand as published, failures
   included.
2. **Run (Exact).** source_freeze_052 at fa0b559 (366 files; ledger a3e3360); main launched once at about 14:50:45 EDT under
   nohup (PID 1299198; one phase, 72 jobs on 8 workers; run_start_052 ledger fb6b2d1), with the checkpoint pusher (PID 1299661).
   Normal exit at about 14:52 EDT, 72/72 jobs, 42 cases, 70.8 s of 3600 s; one checkpoint snapshot (79952f2); sealed and packed at
   36c1b44; run_end_052 ledger cb3f6e9. Run once; never relaunched, restarted or killed; the resume clause was not used. No cut
   (#177 item 4), N12BAR = 12.
3. **Scoring commits (Exact).** RECOUNT_052 c292813 (ledger ac40d54), REFERENCE_052 d841758 (404565d), API_CHECKS_052 f711fb9
   (03fd03f), TEST_SUITE_052 da3c407 (be64060; 8 gated modules, 81 tests, all passed; 2 reported modules, 17 tests, passed),
   GATES_052 6c47f36 (28a8663); make_gates_052 --check reproduces it.
4. **Gates (Exact). 13 of 13 gated pass.** Intervals are Wilson 95%.
   - GDET52: 24/24 canon16n equal [0.86, 1.00], 0 guard firings.
   - GFID52: 72/72 exact replays [0.95, 1.00] (API16N 24, API16N_b 24, API16N_bar 12, API16N_c 6, API16E 6).
   - GN12_sound52: WRONG 0 on 60 noise records (48 noise12 + 12 noise12_bar; 0/60, [0.00, 0.06]), 0 majority errors; eps-0.05
     API16N ID+IDF 23/24 [0.80, 0.99] (12 ID, 11 IDF, 1 IDU: 11930015 spent B = 1500000 on both passes), >= 8/24 so non-vacuous;
     eps-0.10 API16N_bar 12/12 [0.76, 1.00] (5 ID, 7 IDF).
   - GCOMPAT16N52: 6/6 [0.61, 1.00] (4 ID with the same machine from state 0; 2 IDF, 11970002 and 11970005, with future_match
     true on both and the same machine from s1); canon16e also equal 6/6 (informational).
   - GHOST52 (16e, 16n, 16s closures unchanged; certify16n sha equal to the 050 and 052 freezes; 0 sockets), GQB26 (max chunk
     7.6 s, max case 47.7 s), GS_ref (70/70 decided records audited, 0 mismatches, 0 IDF future mismatches, 20/20 mutations; pool
     128 s of 2400 s), G_sound (687 words, 0 unsound, 0 compat WRONG), G_recount, GTI, GTEST, G_PROC, G_RT (70.8 s).
5. **Secondary (Observed, not gated).** GN12_rate52: eps 0.05, 23/24, 53.7 reads per observation, k 27 to 61; eps 0.10, 12/12,
   53.6 reads per observation. GN12_pool (050 + 051 + 052 eps-0.05 API16N): 45/48 ID+IDF [0.83, 0.98], WRONG 0 of 96 records
   [0.00, 0.04]; different cases, not a paired comparison. GCOST52: API16N 3.70M conflicts and 273708 reads over 24 records;
   API16N_bar 2.42M conflicts, 134363 reads over 12.
6. **Pre-freeze tooling fix (Exact; see #177 item 11).** One gate-script bug (arm order) was fixed before the freeze; nothing
   after the freeze was changed.
7. **Reading (Inferred).** certify/16n met every gate of plan 052. Under plan 052's next_if_pass, certify/16n is certified for
   declared N <= 12 under iid flips with eps <= eps_bar = 0.10, with per-record failure probability <= delta = 0.001 (Exact
   conditional on the model and the declared N). certify/16e keeps N <= 16. Not shown: correlated or adversarial noise, N > 12
   with noise, or any 20-state result.
8. **Claim scope (Inferred).** Every ID / IDF is conditional on the declared N = 12 and on iid flips with eps <= eps_bar. A larger
   machine can copy the true machine on every visited state and differ only on states the trace never reached, so no finite trace
   rules it out.
9. **Branch (Exact).** All gated pass, so v0.50.0 follows next_if_pass: noise at 16 states with certify/16n over certify/16e, plus
   the deferred scale20 follow-up in its own part (1 worker with a conflict-only stop, or a different encoding).
