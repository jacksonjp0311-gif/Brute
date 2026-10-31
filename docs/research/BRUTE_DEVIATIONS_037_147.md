# Deviation #147 (study-037, v0.34.0): run record, clock and post-run findings

Written after the main run. It changes no threshold, gate or label. Times are box-local EDT (UTC-4). Labels used:
Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **One main run (Observed).** run_start_037 was ledgered at about 20:39 EDT (730e9b3) on frozen source d9402a1
   (ledger 115b0cc). The runner (pid 465698, 8 workers) ran the 42 main cases once from an empty checkpoint and exited
   normally at about 20:46:44 EDT; total_elapsed_informational 443.1 s of the 1800 s cap. push_checkpoint_037 (period
   300 s) pushed two snapshots: 4bb4b36 (24 cases) and e2b381c (42). Seal 116e9e9, run_end_037 ledger 47654af. No rerun,
   no resume, no tuning. The pre-freeze projection (488 s greedy makespan, #146 item 12) was about 10% high.
2. **Headline failure (Observed).** GR12 fails on b, c and d; a passes (recounted WRONG 0 for A12_r5 and A12_r3 on all
   42 gated cases, no label mismatch). b: mean IDU(A11_r3) - IDU(A12_r3) on noisy12 0.00, seed bootstrap [0.00, 0.00]
   (both 12/12 IDU; bar 0.25). c: ID + IDF(A12_r5, noisy12) 0/12 (bar 5). d: ID(A12_r5) 0/12 against ID(A11_r5) 5/12,
   paired -0.42 [-0.67, -0.17].
3. **GNR12 failure (Observed).** 20 label differences on clean_scale12 (10 per arm for A12_r5 and A12_r3): A12 IDU
   where A11_r3 is ID or IDF. B_final is 0 everywhere. A12_r3_nostop has no differences. Example clean_scale12
   10330001: A12_r5 reached B 0, future and start mode UNSAT at n = 12, then the sound-stop confirmation at B_max (2)
   hit the 9 s query cap (stop 'unknown'); A12_r3_nostop on the same case stopped ID with a 0.36 s maximum query.
4. **Diagnosis (Observed, then Inferred).** Confirmations: A12_r5 clean12 'unknown' on 10/12, noisy12 on 5/12 (the
   other 7 ended in a capped least-B probe with no confirmation); A12_r3 clean12 'unknown' 10/12, noisy8 'unknown'
   9/12. A12_r5 on noisy8 confirmed (ID 4, IDF 7, AMB 2 + 24 AMB rounds that executed words). Least-B: A12_r3 first probe
   capped on 6/12 noisy12 searches against 12/12 for A11_r3 (GPR12 secondary passes: 11 capped probes against 12), but
   every A12_r3 noisy12 case still had a capped probe. Inferred: the bmin12 doubling order helps the first probe, but a
   per-B UNSAT chain still times out at 12 states; and the confirmation, one cardinality-constrained SAT query at B_max
   over all n = 1..N, costs more than the 9 s cap at 12 states even when the least B is 0.
5. **Named branch (Inferred).** Plan 037 next_if_fail: b failed with the first probe still capped on half of the
   searches, so the incremental-totalizer or MaxSAT least-B branch fires. c failed, but not through AMB (1 AMB of 12),
   so the 'separating words cost too much against K' branch does not fire; c failed through capped least-B and capped
   confirmations, which is the same solver-cost cause as b. a did not fail, so the noise-likelihood branch does not fire.
6. **What passed (Observed).** GSAFE12 (Exact: the sealed 036 trace 10210002 now gives AMB: future UNSAT for n = 1..7,
   SAT at n = 8), G_sound (678 words, 18 from confirmations, 0 unsound, 0 unfit), G10 (6/6 controls ID, all arms),
   GS_ref (A12_r3 noisy8: 240 decided, 225 at raised B, 54 confirmation items, 0 mismatches, mutations 20/20), GTI (8
   modules, 57 tests), G_PROC, G_RT (443.1 s), G_recount (42 cases, 0 mismatches), GQB12 (max 10.332 s, S7).
7. **Not gated (Observed).** A12_r3_nostop ID 21, IDF 5, AMB 1, WRONG 0, IDU 15 over 42 cases (smoke had one WRONG on
   10390001; the main block had none). A11_r5 remains the best arm on noisy12 (ID 5, IDU 6) but has no sound stop.
8. **Clock (Observed).** 20:39:09 EDT box against 00:39:04 GMT GitHub (box about 5 s ahead); no stall seen during the
   run (push log, ledger and runner times agree).
