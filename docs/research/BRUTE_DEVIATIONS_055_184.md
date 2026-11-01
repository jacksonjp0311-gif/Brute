# Deviation #184 (study-055, v0.52.0): post-run record

Written after the seal and the gates (2026-10-31T21:15:51-04:00, box-local EDT, UTC-4). It changes no threshold, seed, cap, cube depth or gate, no
sealed output and no frozen file. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Numbering: the request of 19:39 EDT
called the pre-run deviation "#184"; the pre-run record is #183 (4c03497) and this post-run record is #184.

1. **Run (Exact).** source_freeze_055 at b0d07ac (463 files; ledger 4c59d8a); main launched once at about 19:57:00 EDT under nohup
   (PID 1508257; scale20t 18 jobs on 4 workers, compat20t 12 jobs on 4 workers; run_start_055 ledger 7828a0b) with the checkpoint
   pusher (PID 1508355). Normal exit at about 20:26 EDT, 30/30 jobs, 12 cases, 1370.7 s of 3600 s; six checkpoint snapshots
   (8454916, 904de51, 6f6da65, 4bb8255, a257bdc, dcc77e7); sealed and packed at 339045e; run_end_055 ledger e495c9d. Run once;
   never relaunched, restarted or killed. No cut (#183 item 10): N20C = 6, NC20C = 6.
2. **Process-start time (Observed).** At 20:07 EDT ps reported the main PID's start as 20:02:00, about five minutes after the
   launch recorded in the ledger (run_start_055 at 19:57:15). The PID, the parent and the log are the launch's; checkpoint
   snapshot 1 (20:02:04) already held 14 cases. Inferred: a box clock or boot-time offset, not a relaunch. Recorded so that no
   reader takes it for a second run.
3. **Scoring commits (Exact).** RECOUNT_055 769c81c (ledger a637864), REFERENCE_055 0a68276 (05628cc), API_CHECKS_055 e7ee538
   (4cea746; ran exactly once, 20:39 to 21:06 EDT), TEST_SUITE_055 4db7a8e (b926974; 12 modules, 113 tests, all passed),
   GATES_055 8a680bc (e311207); make_gates_055 --check reproduces it.
4. **Gates (Exact). 11 of 14 gated pass; GS20C_gain55, GCOMPAT20C55 and G_PROC fail; certified_20c_N20 false;
   sound_not_certified_20c false** (the plan's rule needs every gate except GS20C_gain55 to pass). Intervals are Wilson 95%.
   - GDET55: 6/6 scale20t cases canon20c equal with identical conflicts across API20C and API20C_b [0.61, 1.00] (2000249,
     2000003, 2267394, 2003768, 2000885, 2003091); 0 hard kills on 30 records.
   - GFID55: 18/18 gated API20C / API20C_b records replay exactly [0.82, 1.00]; 12/12 certify/16e records also exact (reported).
   - GS20C_sound55: WRONG 0 on all 30 records [0.00, 0.11].
   - **GS20C_gain55 FAIL:** API20C ID+IDF 0/6 [0.00, 0.39]; API20C_b 0/6 [0.00, 0.39]; API16E20 0/6 [0.00, 0.39] (all IDU,
     budget spent). Needed >= 2/6 and more than API16E20.
   - **GCOMPAT20C55 FAIL:** 4/6 [0.30, 0.90] under the plan 052 rule (unchanged). 12270001, 12270004, 12270006 ID with the same
     machine from state 0; 12270002 IDU on both. 12270003 and 12270005 are IDF on both arms with future_match true on both, but
     "the same machine from the current state s1" is false. Item 5 gives the diagnostic; the gate stands as computed.
   - **G_PROC FAIL:** the order clause needs a ledger event named exactly prefreeze_smoke_055. The pre-freeze smoke was ledgered as
     prefreeze_smoke_055_attempt1 (6d7b208, PASS false on the ghost loop only) and prefreeze_ghost_recheck_055 (8dd7021); by the
     19:39 instruction "Do not rerun anything" no second full prefreeze was run, so no event of the required name exists. No event
     is added after the fact. Every other G_PROC clause passes (order file, parseable non-decreasing times, main sealed).
   - GCUBE55 (independent cube audit: 18 records, 109 capped queries, 4848 cubes, 820 pruned and all 820 checked UNSAT, 0
     mismatches), GHOST55 (frozen API and 16e / 16n / 16s / 20t closures unchanged; certify20c sha bound to freeze 055; 0 socket
     attempts; no-network loop IDU), GS_ref (not vacuous: 5/5 decided compat20t API20C records audited, 0 mismatches, 20/20
     mutations, 428.1 s of 2400 s; scale20t had 0 decided records), G_sound (343 words, 0 unsound), G_recount, GTI, GTEST, G_RT.
5. **GCOMPAT20C55 diagnostic (Observed; reading Inferred; does not change the gate).** The two arms stop at different trace
   lengths on both failing seeds (12270003: 252 vs 265 steps, s1 1 vs 5; 12270005: 209 vs 223, s1 14 vs 3), so the rule compares
   states reached at different times. On 12270003 the two returned machines are identical and equivalent from state 0; they are
   only compared from different current states. On 12270005 the machines differ from state 0 and from each one's s1. Inferred:
   12270003 is a comparison artefact of the IDF rule when the stop step differs; 12270005 is Open (both are labelled IDF with
   future_match true, so each is consistent with its own trace; whether they agree after aligning the stop step was not checked).
   4 of 6 compat cases (12270001, 03, 04, 05) stopped
   at different steps here; Inferred: certify/20c's cube split changes which model is returned first and so the actions chosen.
6. **Secondary (Observed, not gated).** GS20C_rate55: API20C 9119 conflicts/s (max case wall 321.4 s, max chunk 23.3 s),
   API20C_b 6010/s (it ran later, beside the API16E20 jobs), API16E20 7012/s (max chunk 242.8 s). GS20C_paired55: every scale20t
   record of both encodings stopped at about 2.0M conflicts (API20C 12250003 at 2267394). GCUBE_stats55: 109 queries, 4848 cubes,
   820 pruned, 4245 closed UNSAT, 53 SAT, 125 open at stop. GCOST55: API20C scale20t 12.28M conflicts (6 capped calls, 33 cube
   queries, 1321 cubes), API16E20 12.02M (120 capped calls); compat20t API20C 10.12M vs API16E 8.58M conflicts.
7. **Projection (Inferred, checked).** #183 projected a worst case of 2270.7 s; observed 1370.7 s.
8. **Reading (Inferred).** Splitting capped queries into cubes (certify/20c) is sound, deterministic and exactly replayable at 20
   states, and the cube audit closes, but it decided nothing at 20 states under B 2M, the same as certify/16e. Each scale20t record
   hit one capped query and spent the rest of the budget inside its cubes (125 cubes open at stop). Three studies (053, 054, 055)
   and three different searches over the same SAT encoding now give 0/6 at 20 states, so the next step changes the method, not the
   split.
9. **Claim scope (Inferred).** Every ID / IDF is conditional on the declared N. A larger machine can copy the true machine on every
   visited state and differ only on states the trace never reached, so no finite trace rules it out. Nothing at 20 states is
   certified.
10. **Branch (Exact; choice Inferred).** Plan 055 next_if_fail names two triggered branches. Gain branch (every soundness gate
    passed): "stop budget and split variants and change the question ... L*-style counterexample-guided search with the declared N
    bound, pre-registered against certify/16e at the same budget." Compatibility branch: "GCOMPAT20C55 fails: fix the cube encoding
    at 16 states before scaling." v0.53.0 (plan 056) takes the gain branch, as the request asks, and drops the cube split, so no
    cube encoding is scaled. For the compatibility branch it pre-registers (a) a stop-step-aligned IDF comparison rule for its own
    compat gate, declared before data and not applied to study-055, and (b) a read-only re-check of 12270005 on the sealed 055 data.
    certify/20c is published as sound but not certified, and not compatibility-equal on 2/6 IDF cases under the 052 rule;
    certify/20t, certify/16n and certify/16e are unchanged.
