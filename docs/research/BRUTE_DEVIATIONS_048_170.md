# Deviation #170 (study-048, v0.45.0): post-run record

Written after the seal and the gates (2026-10-31, box-local EDT, UTC-4). It changes no threshold, seed, cap or gate, and no frozen
file. It records what happened between the freeze and the gates and reads the one failure. Labels: Exact, Observed, Simulated,
Inferred, Rejected, Open.

1. **Run (Exact).** source_freeze_048 at 9baedb4 (ledger 8ae5d2e, 08:20:05 EDT); run_start_048 (ledger 0c0d67c, 08:20:42 EDT; PID
   1020216, 8 workers); normal exit, 70/70 jobs (52 fresh arm jobs on 26 cases, 18 part-r replays) in 107.0 s of 3600 s; one
   checkpoint snapshot (7078d94); sealed and packed at 7e2825f; run_end_048 ledger 175ff06 (08:25:23 EDT). Run once; never
   relaunched, restarted or killed; the resume clause was not used.
2. **A launch attempt that did not start (Exact).** The first launch command chained the run after a run_start_048 ledger call
   whose artifact path (a directory) did not exist; the ledger helper refused, so the chain stopped before the runner started and
   nothing ran (no log, no results directory contents, no ledger entry). The ledger entry was then written with the freeze file as
   its artifact (as in 047) and the run launched once. This is not a relaunch: no job had started.
3. **Ledger order for scoring (Exact).** recount, reference, api_checks, tests and gates were each committed first and their ledger
   entries (recount_048 22b5b6e, reference_048 d98fbbc, api_checks_048 ba5aa7f, tests_048 9068673, gates_048 a3d6179) were
   appended together after the gates commit, each citing its own artifact commit. The artifacts were not changed in between.
4. **Gates (Exact; GATES_048 reproduces under --check).** 13 of 14 gated pass. GDET48 PASS: canon16d identical on 26/26
   [0.87, 1.00] and 0 wall-guard firings on all 70 records (parts a, r, d). GWALL_r PASS (0 of 18). GFID48 PASS 26/26 [0.87, 1.00].
   GHOST48 PASS (closure unchanged, certify16d sha unchanged, 0 socket attempts). G10 PASS (6/6 controls ID on both arms). GQB23
   PASS (max call wall 5.95 s part a, 6.40 s part r, 7.79 s part d; bound 30 s). GS_ref PASS (16 decided records audited, 0
   mismatches, 20/20 mutations, 45.0 s of 2400 s). G_sound, G_recount, GTI, G_PROC, G_RT PASS. GS20_sound PASS **vacuously**:
   0 of 8 scale20 records decided, WRONG 0. **GAPI16D_fresh48 FAIL on count only:** scale16 ID+IDF 0/12 [0.00, 0.24] (bar 7/12),
   WRONG 0; 10 IDU (stop unknown) and 2 AMB (K_spent).
5. **Secondary (Observed, not gated).** GREP16e 0/12 [0.00, 0.24] against 047's 10/12 [0.55, 0.95] at C 294000. GS20_rate 0/8
   [0.00, 0.32]. GR_class on 18 replays: none 8 (the 6 controls and 2 sealed IDU), cap-timing 4, word-divergence 6, infidelity 0;
   on the 12 scale16 replays certify/16d at C 50000 decided 0 where the sealed 046 A16_N decided 7 (3 ID, 4 IDF). GCOST48: scale16
   part a 812 calls, 28 capped, 2924393 conflicts over 12 records; scale20 338 calls, 22 capped, 2056082 conflicts over 8 records.
6. **Reading of the failure (Inferred).** The case budget B never bound: the largest scale16 record spent 541496 conflicts of
   1500000 (36 %) and the largest scale20 record 524232 of 1000000; every IDU stopped on a capped call. At C 50000 a single hard
   SAT call in the least-model search returns unknown and certify/16d ends the case there (the single-call reading of #167 item 4).
   The smaller cap bought wall-freedom (0 firings, max call 7.8 s) at the price of every scale16 and scale20 decision. The smoke
   showed the same pattern before the freeze (#169 item 11); nothing was tuned.
7. **Branch taken (Exact, from plan 048 next_if_fail).** "GAPI16D_fresh48 fails on count only: record it; the smaller cap trades
   decided cases for wall-freedom; re-plan B." certify/16d is not certified at C 50000. Per item 6, re-planning B alone would not
   change any label (B was never reached); plan 049 therefore re-plans how B is spent: a capped call is resumed in further C-sized
   chunks on the same query until B is spent (Inferred design, not built here).
8. **Process notes (Exact).** The user's computer was offline during this work; all network access (git push, GitHub) went
   through the box's own network. Box clock checked against GitHub's Date header before the run (skew under 10 s).
