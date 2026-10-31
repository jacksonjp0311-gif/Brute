# Deviation #182 (study-054, v0.51.0): post-run record

Written after the seal and the gates (2026-10-31T18:42:46-04:00, box-local EDT, UTC-4). It changes no threshold, seed, cap or gate, and no frozen
file. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Run (Exact).** source_freeze_054 at 6762f86 (427 files; ledger 1a802a6); main launched once at about 17:53:02 EDT under nohup
   (PID 1428450; scale20t 18 jobs on 4 workers, compat20t 12 jobs on 4 workers; run_start_054 ledger 3c5013f) with the checkpoint
   pusher (PID 1428682). Normal exit at about 18:12 EDT, 30/30 jobs, 12 cases, 1157.8 s of 3600 s; four checkpoint snapshots
   (f0fea94, 5d6c535, b4908e7, 94c52b0); sealed and packed at eb695ff; run_end_054 ledger 2ad16ac. Run once; never relaunched,
   restarted or killed. No cut (#181 item 12): N20T = 6, NC20T = 6.
2. **Scoring commits (Exact).** RECOUNT_054 a0573e7 (ledger 9aa5f85), REFERENCE_054 e02c307 (590db04), API_CHECKS_054 968cb1c
   (d30ef57), TEST_SUITE_054 d69000a (58c6c42; 11 modules, 104 tests, all passed), GATES_054 6d9574f (b1bdb42);
   make_gates_054 --check reproduces it.
3. **Session interruptions (Observed).** The agent session was interrupted twice after the run (about 18:28 and 18:30 EDT). The
   reference ledger entry and the api_checks launch were in the interrupted command; both completed. api_checks_054 ran exactly
   once (PID 1449175, started 18:28 EDT under timeout 1800, finished about 18:39 EDT) and its output is committed as written.
4. **Gates (Exact). 12 of 13 gated pass; GS20T_gain54 fails; certified_20t_N20 false; sound_not_certified_20t true.** Intervals
   are Wilson 95%.
   - GDET54: 6/6 scale20t cases canon16e equal and conflicts identical across API20T and API20T_b [0.61, 1.00] (2000448, 2000053,
     2023343, 2000021, 2000050, 2003490); 0 hard kills on 30 records.
   - GFID54: 18/18 gated API20T / API20T_b records replay exactly [0.82, 1.00]; 12/12 certify/16e records also exact (reported).
   - GS20T_sound54: WRONG 0 on all 30 records [0.00, 0.12 for 30].
   - **GS20T_gain54 FAIL:** API20T ID+IDF 0/6 [0.00, 0.39]; API20T_b 0/6 [0.00, 0.39]; API16E20 0/6 [0.00, 0.39] (5 IDU budget
     spent, 1 AMB K_spent on 12170004). Needed >= 2/6 and > API16E20.
   - GCOMPAT20T54: 6/6 [0.61, 1.00] under the plan 052 rule (5 ID with the same machine from state 0; 12190004 IDF on both arms with
     the same machine from the current state). canon16e equal 4/6 (informational; H4 allows M2 to differ).
   - GHOST54 (frozen API and 16e / 16n / 16s closures unchanged; certify20t sha bound to freeze 054; 0 sockets), GS_ref (not
     vacuous: 6/6 decided compat20t API20T records audited, 0 mismatches, 20/20 mutations, 421.1 s of 2400 s; scale20t had 0
     decided API20T records), G_sound (389 words, 0 unsound), G_recount, GTI, GTEST, G_PROC, G_RT (1157.8 s).
5. **Secondary (Observed, not gated).** GS20T_rate54: API20T 7956 conflicts/s (max case wall 358.6 s), API20T_b 7472/s, API16E20
   9780/s. GS20T_paired54: every scale20t record of both encodings stopped at about 2.0M conflicts (API16E20 12170004 at 1686301,
   AMB). GCOST54: API20T scale20t 12.03M conflicts (125 capped calls), API16E20 11.70M (101 capped calls); compat20t API20T 4.86M vs
   API16E 5.24M conflicts.
6. **Projection (Inferred, checked).** #181 projected a worst case of 2270.7 s; observed 1157.8 s.
7. **Reading (Inferred).** Asking the rival once at size N (certify/20t) is sound and deterministic at 20 states, and agrees with
   certify/16e at 16 states, but it decided nothing at 20 states under B20 2M, the same as certify/16e. Both encodings ran out
   of budget on every case with conflict counts identical across passes, so a larger budget on the same search is not expected
   to change the outcome. Smoke (#181 item 11) gave the same signal before the freeze.
8. **Claim scope (Inferred).** Every ID / IDF is conditional on the declared N. A larger machine can copy the true machine on every
   visited state and differ only on states the trace never reached, so no finite trace rules it out. Nothing at 20 states is
   certified.
9. **Branch (Exact).** Plan 054a next_if_fail, gain branch: "asking the rival once at size N does not raise decisions at 20 states;
   next try a different search at the same budget (cube-and-conquer over distinguishing-word prefixes with a deterministic cube
   order)". certify/20t is published as sound but not certified. certify/16n and certify/16e are unchanged.
