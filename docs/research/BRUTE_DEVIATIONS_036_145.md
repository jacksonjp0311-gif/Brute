# Deviation #145 (study-036, v0.33.0): run record, clock and post-run findings

Written after the main run. It changes no threshold, gate or label. Times are box-local EDT (UTC-4). Labels used:
Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **One main run (Observed).** run_start_036 was ledgered at 19:47:07 EDT (e972a23) on frozen source 730aef4. The runner
   (pid 422666, 8 workers) ran the 48 main cases once from an empty checkpoint and exited normally at about 19:54:12 EDT;
   total_elapsed_informational 420.3 s of the 1800 s cap. push_checkpoint_036 (period 150 s) pushed three snapshots:
   43b5e2f (13 cases), 21fdeca (28), 0bfe2b7 (48). run_end_036 ledger bd46789, seal d89c1ea. No rerun, no resume, no
   tuning. The pre-freeze projection (302 s greedy makespan, #144 item 12) was about 28% low.
2. **Ledger slip before the run (Observed).** The first run_start_036 call named results/study-036/main as its artifact;
   the ledger tool needs an existing file and refused, so nothing was appended and, because the launch was chained after
   it, the runner was not started (a checkpoint pusher started without a PID and exited on its argument error). The call
   was repeated with experiments/BRUTE_SOURCE_FREEZE_036.json as the artifact (as run_start_035) and the runner was then
   launched once. No case ran before the ledgered run_start_036.
3. **Headline failure (Observed).** GR11 fails on a, b, c and d. a: A11_r3 has 1 recounted WRONG on a within-budget
   case (noisy_scale8 10210002); A11_r5 and S7 WRONG 0. b: ID(A11_r3) - ID(A10) on noisy12 +0.17, seed-bootstrap
   [0.00, 0.42] (bar 0.25, lower bound > 0). c: ID + IDF(A11_r3, noisy12) 2/12 (bar 4). d: IDU(A11_r3, noisy12) 10/12
   (bar <= 3). GBIS11 fails (IDU r3 10/12 against r3_up 9/12). GQB11 fails: one A11_r3_up query 10.513 s
   (noisy_scale12_extra 10240002; bound 10.5 s). Secondary GRB11 fails.
4. **Diagnosis of A11_r3 IDU (Observed, then Inferred).** The majority of 3 reads cut the truth's flips on the base trace
   from 13-20 (first raw read) to 0-5. But on 9 of the 10 noisy12 IDU cases the very first bmin11 probe, B = B_max = 6 at
   12 states, hit the 9.5 s query cap (probe [6, None]), so the stop was 'unknown' with no word executed. Inferred:
   probing B_max first pays the most expensive SAT query at the start; at r = 5 B_max is 2 and the same probe is cheap,
   which is why A11_r5 did better (ID 4/12, IDU 5/12; ID(A11_r5) - ID(A10) +0.33 [0.08, 0.58], reported, not gated).
5. **The gated WRONG (Observed).** noisy_scale8 10210002: A11_r3 and A11_r3_up stopped ID at B_final 1, while the
   truth needs 2 flips on their final trace (within B_max 6, so the case is gated). The returned machine matches the
   truth's behaviour from the final state (M1_future_match True) but not from the start state, so label9 scores it
   WRONG. Inferred: least-B selection is not sound when the truth's flip count on the fused trace exceeds the least SAT
   budget; a confirmation at B_max (or at the least B plus a margin) before ID is needed. A11_r5 on the same case had 1
   truth flip and was ID.
6. **What passed (Observed).** GNR11 (36 clean comparisons, no label differences, B_final 0 on every clean case),
   G_sound (674 words re-simulated, 0 unsound, 0 unfit models), G10 (controls ID 6/6 for every arm), GS_ref (12
   noisy_scale8 A11_r3 cases: 88 decided items, 75 at raised B, 1 undecided, 0 mismatches, mutations 20/20), GTI (7
   modules, 48 tests), G_PROC, G_RT (420.3 s), G_recount (48 cases, 0 mismatches).
7. **Clock (Observed).** At 19:58:35 EDT the box read about 7 s ahead of GitHub's Date header (23:58:28 GMT); no stall
   during the run (push log, ledger and runner times agree). The pre-freeze wait anomaly is #144 item 13.
