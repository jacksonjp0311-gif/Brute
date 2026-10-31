# Deviation #149 (study-038, v0.35.0): run record, interruption and post-run findings

Written after the main run. It changes no threshold, gate or label. Times are box-local EDT (UTC-4). Labels used:
Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **One main run (Observed).** run_start_038 was ledgered at 21:40:30 EDT (6000c37) on frozen source e5f45a0 (ledger
   0ca5360). The runner (pid 512209, 8 workers) ran the 42 main cases once from an empty checkpoint, 21:40:42 to
   21:48:03 EDT, and exited normally; total_elapsed_informational 451.0 s of the 1800 s cap. push_checkpoint_038
   (period 300 s) pushed two snapshots: 9d59f40 (21 cases, 21:45:43) and f4d4b79 (42 cases, 21:48:03), then took its
   final snapshot and exited. Seal hashes were re-verified against RESULTS.json, SCIENTIFIC.json, the plan and the freeze
   before run_end_038 (seal commit b78314c, ledger e6cca77). The pre-freeze projection (574 s, #148 item 12) was about
   27% high.
2. **Interruption (Observed; disclosed).** The executing agent session was interrupted (a tool wait aborted) while polling
   the run, at about 21:47-21:48 EDT. The run itself was not affected: it finished on its own, sealed complete, and the
   pusher's last snapshot (f4d4b79) holds all 42 cases. Nothing was relaunched, resumed or rerun; the resume clause was
   not used (it is not approved). The post-run steps (seal check, storage, recount, reference, tests, gates) were done
   after the session was restarted at 21:48 EDT, on the sealed files as they were left.
3. **Headline failure (Observed).** GR13 fails on b, c and d; a passes (recounted WRONG 0 for A13_r5 and A13_r3 on all 42
   gated cases, no label mismatch). b: mean IDU(A12_r3) - IDU(A13_r3) on noisy12 0.00, seed bootstrap [0.00, 0.00] (both
   12/12 IDU; bar 0.25). c: ID + IDF(A13_r5, noisy12) 1/12, Wilson [0.01, 0.35] (bar 5). d: capped confirmations of A13_r5
   on clean12 8/12 [0.39, 0.86] (bar <= 2; A12_r5 also 8/12).
4. **GNR13 failure (Observed).** 18 label differences on clean_scale12 (9 cases x 2 A13 arms): A13 IDU where A11_r3 is ID
   (8) or IDF (1). B_final is 0 on every clean12 A13 case; the differences come from the capped confirmation, not from B.
5. **Clean12 confirmation vs the cap (Observed; confirms #148 item 11).** All 8 clean12 B_max confirmations of A13_r5 and
   all 8 of A13_r3 hit the 9.0 s cap (walls 9.01-9.25 s, verdict 'unknown'); 0 finished under it. A12_r5 the same (8/8).
   The single n = 12 incremental query is no cheaper in practice than A12's n = 1..12 loop at this cap.
6. **A13 against A12 (Observed).** Labels per (arm, key) are identical between A13 and A12 at the same r except A13_r5
   noisy12 (ID 1 vs 0) and B_final means differ slightly. GPR13 (secondary) fails: A13_r3 11 capped least-B probes vs
   A12_r3 10 (first probe capped 2 vs 3). GH2 (secondary) fails: A12 capped-confirmation cases 36 vs A13 34 (diff 2, bar
   6). Inferred: keeping learned clauses across budgets (incremental totalizer) does not change the outcome at 12 states
   with noise; each query (least-B at B > 0, or confirmation at B_max) still exceeds 9 s.
7. **Named branch of plan 038 (Inferred).** a did not fail (no encoding audit). b and d failed with confirmations still
   capped, so plan 038's 'core-guided MaxSAT least-B + cheaper bounded-length rival search' branch fires. c failed with 0
   AMB on noisy12, so the 'separating words cost too much against K' branch does not fire. GNR13 failed with B_final 0
   but WITH caps, so the 'revisit the stop rule' branch does not fire. Under the build task's instruction (21:48 EDT)
   that a GR13 failure pivots v0.36.0 away from noise at 12 states, plan 039 records the MaxSAT branch as Open and
   instead scales the clean B = 0 line (A9/A10) toward 16 states with a second world family.
8. **What passed (Observed).** GSAFE13 (Exact: the sealed 036 trace 10210002 gives AMB under confirm13: future SAT at
   n = 8, rival n 8, same verdict as A12), GINC13 (13 decided items of the sealed 037 reference set, 13 at raised B, 0
   mismatches, 2 skipped where A12 was capped), G_sound (999 words, 82 from confirmations, 0 unsound, 0 unfit), G10 (6/6
   controls ID, all arms), GS_ref (A13_r3 noisy8: 343 decided, 322 at raised B, 25 confirmation items, 0 mismatches,
   mutations 20/20), GTI (9 modules, 64 tests), G_PROC, G_RT (451.0 s), G_recount (42 cases, 0 mismatches), GQB13 (max
   9.711 s, S7; A13 max 9.249 s).
9. **Clock (Observed).** Box clock vs GitHub's Date header, see the release ledger entries; no stall seen.
