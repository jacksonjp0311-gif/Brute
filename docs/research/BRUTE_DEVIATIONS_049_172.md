# Deviation #172 (study-049, v0.46.0): post-run record

Written after the seal and the gates (2026-10-31, box-local EDT, UTC-4). It changes no threshold, seed, cap or gate, and no frozen
file. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Run (Exact).** source_freeze_049 at 66e6778 (278 files; ledger 60ffcb8, 09:00:31 EDT); run_start_049 (ledger 3dae68c, 09:00:43
   EDT; PID 1055981, 8 workers); normal exit, 104/104 jobs (52 fresh arm jobs on 26 cases, 26 part-r and 26 part-c replays) in
   606.8 s of 3600 s; three checkpoint snapshots (93550e6, e8b7bbe, e39383a); sealed and packed at 11fb943; run_end_049 ledger
   02b7332 (09:13:17 EDT). Run once; never relaunched, restarted or killed; the resume clause was not used. No cut (#171 item 7).
2. **Agent interruption during scoring (Exact).** The reference audit (scripts/run_reference_049.py, started 09:16 EDT under nohup
   setsid) was running when the agent session was interrupted. The process was not touched; it finished on its own at 09:22:27 EDT
   (333.1 s of 2400 s) and wrote REFERENCE_049.json, which was committed as-is at fa677b8 (ledger 8b43d52). It was not rerun. The
   api_checks_049 command was issued once around the interruption; its tool call reported a spawn abort, but the process ran to
   completion and wrote API_CHECKS_049.json at 09:24:46 EDT, which was inspected (complete, PASS) and committed as-is at e9bd777
   (ledger 3a878fb). It was not rerun. Both outputs are content-checked by the gates against the sealed results sha.
3. **Scoring commits (Exact).** RECOUNT_049 e08c8af (ledger c4e5636), REFERENCE_049 fa677b8 (8b43d52), API_CHECKS_049 e9bd777
   (3a878fb), TEST_SUITE_049 656eae4 (8935151; 8 modules, 81 tests, all passed), GATES_049 9b1285c (4846271).
4. **Gates (Exact).** 15 of 15 gated pass. GDET49 26/26 canon16e identical [0.87, 1.00], 0 guard firings. GFID49 26/26 [0.87, 1.00].
   GCOMPAT16D 26/26 part-c records canon16d byte-equal to sealed 048 [0.87, 1.00]. **GAPI16E_fresh49 7/12 [0.32, 0.81], exactly at
   the bar of 7** (6 ID, 1 IDF; 4 IDU budget-spent, 1 AMB K_spent; WRONG 0; API16E_b identical). GS20_sound49 PASS **vacuously**:
   0 of 8 scale20 decided (all IDU, budget spent), WRONG 0; no N <= 20 claim. GR49_sound 0 contradictions, 0 WRONG on 26 replays.
   GHOST49 (new modules brute.api, brute.api.certify16e; 0 sockets). G10 6/6 controls ID. GQB24 max chunk wall 14.4 s (bound 30),
   max case wall 153.2 s (bound 600). GS_ref 28 decided audited, 0 mismatches, 20/20 mutations. G_sound (1077 words, 0 unsound),
   G_recount, GTI, G_PROC, G_RT (606.8 s) pass.
5. **Secondary (Observed, not gated).** GREP16f: 7/12 beside 048's 0/12 (C 50000, no resume) and 047's 10/12 (C 294000). GR_gain:
   part r gains 5 scale16 decisions over sealed 048 (classes none 11, cap-timing 5, word-divergence 10, infidelity 0). GS20_rate49
   0/8 [0.00, 0.32]; scale20 spent its 1.0M budget on all 8 (313 chunks, 8.0M conflicts per arm).
6. **Reading (Inferred).** Chunked continuation recovers decisions that the fixed per-call cap lost (0/12 -> 7/12) without any
   soundness cost (WRONG 0 everywhere, 0 contradictions, 0 reference mismatches), but the margin is thin: the gate passed at its bar
   and the CI is wide. At scale20 the case budget, not the chunk cap, is binding. certify/16e is certified for N <= 16 under these
   caps; N <= 20 is not certified because GS20 is vacuous. The guarantee is conditional on the declared N: a larger machine can copy
   the true machine on every visited state, so no finite test separates them.
7. **Next (per plan 049 next_if_pass, Exact).** Plan 050 pre-registers the 24-world scale20 replication and a noise study at 12
   states; since GS20 passed only vacuously, plan 050 must also give scale20 enough budget to decide cases (Open).
