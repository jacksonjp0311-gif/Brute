# Deviation #174 (study-050, v0.47.0): post-run record

Written after the seal and the gates (2026-10-31, box-local EDT, UTC-4). It changes no threshold, seed, cap or gate, and no frozen
file. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Run (Exact).** source_freeze_050 at c9bb238 (308 files; ledger 0f5e355, 10:26:22 EDT); main launched 10:26:31 EDT under
   nohup setsid (PID 1120523, 8 workers; run_start_050 ledger 6690a64, 10:26:56 EDT). Normal exit at 11:14 EDT, 78/78 jobs
   (24 + 12 scale20, 12 + 12 noise12, 6 + 6 controls, 6 part c) in 2611.5 s of 3600 s; ten checkpoint snapshots (1d2b107 to
   9ea2308); sealed and packed at f96649a; run_end_050 ledger efdadc5 (11:15:26 EDT). Run once; never relaunched, restarted or
   killed; the resume clause was not used. No cut (#173 item 8).
2. **Agent interruptions during scoring (Exact).** The session was interrupted three times (during the run, during the reference
   and during api_checks). No process was touched: the run, the reference (started 11:19 EDT, terminated by its own 2400 s budget
   at 11:59 EDT) and api_checks_050 (PID 1177656, started 11:59 EDT, exited about 12:35 EDT) each ran once to their own end, and
   each output was committed as-is. Nothing was rerun.
3. **Scoring commits (Exact).** RECOUNT_050 889d697 (ledger 1f73893), REFERENCE_050 083d758 (860c9d5), API_CHECKS_050 a39c0d9
   (ad5dd0a), TEST_SUITE_050 4cb7765 (f13b2e0; 9 modules, 92 tests, all passed), GATES_050 5dd2299 (f3af5bd).
4. **Gates (Exact). 9 of 15 gated pass; 6 fail.**
   - FAIL GDET50: 20/30 canon equal [0.49, 0.81] (scale20 2/12, control 6/6, noise12 12/12); the wall guard fired on 29 records
     (all scale20). The 10 scale20 canon differences are all IDU/IDU pairs that hit the 600 s case guard.
   - FAIL GFID50: 21/42 exact [0.36, 0.64] (scale20 3/24, control 6/6, noise12 12/12).
   - FAIL GS20_sound50: non-vacuity met (API16E 1/24 decided [0.01, 0.20], seed 11730008 ID, both passes; WRONG 0), but the
     reference did not audit either decided scale20 record within its budget, so the audit clause fails.
   - FAIL G10: 5/6 controls ID on both passes; control 11750001 is IDU on both (1500135 conflicts, budget spent, no guard).
   - FAIL GQB25: 26 chunks over 30 s (max 90.5 s) and 25 case walls over 600 s (max 615.1 s).
   - FAIL GS_ref: complete false (2400.1 s), 32/34 decided audited, 0 mismatches, 20/20 mutations; not audited:
     scale20/11730008 API16E and API16E_b.
   - PASS GN12_sound (WRONG 0 on 24 noise records, 0 majority errors; API16N 11/12 ID+IDF [0.65, 0.99]), GCOMPAT16N 6/6
     [0.61, 1.00], GHOST50 (new module brute.api.certify16n, 0 sockets), G_sound (811 words, 0 unsound), G_recount, GTI, GTEST,
     G_PROC, G_RT (2611.5 s).
5. **Secondary (Observed, not gated).** GS20_rate50 1/24 [0.01, 0.20] beside 049's 0/8 [0.00, 0.32] (GS20_vs49). GN12_rate 11/12,
   2532 observations, 53.65 reads per observation, k 27 to 61. GCOST50: scale20 API16E 24 records, 12492 s arm wall, 82.8M
   conflicts, 443 capped calls, 6 budget-spent.
6. **Rates (Observed).** Slowest scale20 rate 4503 conflicts/s (API16E 11730023, guard 22, 607.5 s, 2.74M conflicts); among the 7
   scale20 records with no guard firing, 9563 to 20323 conflicts/s. The declared projection rate was 8766/s (#173 item 8).
   Chunk walls up to 90.5 s for 50000 conflicts, so the per-chunk rate fell to about 550 conflicts/s on some chunks.
7. **Reading (Inferred).** The failures share one cause: at B20 4000000 on this host the scale20 cases run into the wall-time guard
   (600 s per case). A guard firing makes a record depend on wall time, which breaks determinism (GDET50), self-replay (GFID50,
   whose replays run under the same guard and load) and the chunk/case bounds (GQB25); the one decided scale20 case (3.25M
   conflicts) is too heavy for the CNF reference in 2400 s (GS_ref, GS20_sound50). Conflicts do not predict wall time at 20
   states: rates vary by more than 4x between cases. Separately, G10 fails because control 11750001 needs more than 1.5M
   conflicts. Soundness held everywhere it was checked: WRONG 0, 0 reference mismatches, 0 majority errors. The noise front end
   (certify/16n) passed every gate it owns, but it is not certified, because the release's gate set did not pass as a whole.
   The guarantee is conditional on the declared N: a larger machine can copy the true machine on every visited state, so no
   finite test separates them.
8. **Branch (per plan 050 next_if_fail, Exact).** "GDET50 or GQB25 fails on guard firings: B20 is too large for the case guard
   on this host; re-plan B20 from this run's slowest rate." Plan 051 (v0.48.0) does that and also makes the scale20 runtime
   wall-independent (Open until it is run).
