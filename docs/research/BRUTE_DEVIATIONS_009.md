# BRUTE study-009 (v0.7.0): deviations and implementation choices

Plan: `experiments/BRUTE_PLAN_009.json` (frozen, preregistration_009 at 3825ad3). Each entry says what changed or what
the plan left open, when it was decided (EDT, author-set), and whether held-out data had been seen. Section A and B
entries were all decided **before any held-out data were generated** (run_start_009). Section C is written during and
after the held-out run and says so per entry. Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

## A. Before the source freeze (f9b94e7, ledger source_freeze_009)

1. **Adopted incremental-xcheck files** (brute/xcheck_sat_incremental.py, experiments/v060_xcheck_incremental.py,
   tests/test_xcheck_sat_incremental.py) checked out byte-identical at 3a31e3b; sha256 equal the plan pins (Exact).
2. **Frozen cosmetic timeout label.** The planner's fallback reason says "timeout (10 s per count)"; the counting limit
   actually applied is 2 s per count (the plan's planning_rule). Label kept because brute/planner.py is frozen (Observed).
3. **Checkpoint torn-tail repair** (brute_common_009.Checkpoint.repair_torn_tail, also before reading the xcheck
   checkpoint): a partial last JSONL line left by a SIGKILL is truncated on resume; that case/step is recomputed.
4. **GX2'' symmetric ordering**: v070_xcheck checks B5 through the frozen v060_xcheck.audit and BS7/BSC7 with the
   adopted IncOracle/IncSolver; per family/arm results are reported in one file.
5. **Forked planning isolation**: P7 planner counts run in forked children (per-count 2 s limit, 150 s per case budget);
   the GP1(iv) replay re-runs cases in fresh processes.
6. **SC7 initial state**: SC7's tracked component starts from the CT->CTR initial state as the frozen R6/C6 lineage does.
7. **Diagnostic note wording** (diagnostic_009): wording only; no rule change followed the diagnostic (Exact, ledger).
8. **A2 slim trace**: the v0.2.0 comparator A2 records a slim trace (fields needed for coverage and soundness only).
9. **A5/A4 E1 approximation**: for the non-event arms the lag report (R_lag_heldout, R_diag_lag_008) uses the
   diagnostic's E1 approximation; S7/SC7 use their recorded E1 event steps.
10. **P['region']** added to the planner record (reporting only).
11. **Per-stream budget kill + seal-partial**: a stream stopped by its own budget is SIGTERMed (SIGKILL after 60 s) and
    sealed as it is (brute_study_009 --seal-partial; SEAL gains complete / expected_case_count / missing_job_keys).
12. **GP1(v) recount limit 30 s** per count (independent recount), sampled with random.Random(20261028).
13. **GTI run twice**: in-cap (process step 8, gated GTI) and final-tree (GATES_009_FINAL.json); release statement
    "GTI PASS" needs both.
14. **NEW_TESTS** in scripts/run_tests_070.py = tests/test*.py modules absent from tag v0.6.0 (new_tests(): planner,
    run_tests_070, seeds_009, syncevent, v070_reference, the adopted xcheck_sat_incremental, and release_070 once it
    exists); K060 allowed failures are the three
    Release060 tests (class name Release060).
15. **Python orchestrator** scripts/run_study_009.py instead of shell job control (nohup, RUN_T0, RUN_STATE resume).
16. **Superseded 060 freeze**: also_requires lists BRUTE_RELEASE_FREEZE_060 and _R1; both are verified.
17. **Smoke spot path not exercised**: SPOT_SAMPLE_009 holds held-out seeds, so the gx2_spot stream exits 1 on smoke
    data (expected). The spot path is first exercised in the held-out run (Observed, smoke-2).
18. **Smoke planning comparator**: smoke planning seeds have no A5 trace in the smoke 2x2 block, so make_paired_009
    --smoke substitutes P7 for A5 (dry run only; the held-out run uses the A5 trace of the main 2x2 block).

## B. Scoring choices (scripts/make_gates_009.py, make_paired_009.py, make_reproducibility_009.py; ledger scoring_freeze_009 at b49cc37)

19. All scoring choices are listed in the make_gates_009 docstring. Highlights:
    - **G_RT conservative reading**: PASS only if STOP_009 is absent, RUN_DONE elapsed <= 10800 s and no stream was
      stopped for any reason (own budget, error or cap).
    - **INCOMPLETE_INPUT**: a gate whose inputs are incomplete because a stream hit its own budget or failed (cap not
      reached) is FAIL with reason INCOMPLETE_INPUT (...); at the cap the reason is STUDY_BUDGET (...).
    - **GX2'' (iii)**: a gx2_sym stop by its own 30 min budget is allowed (unreached steps unchecked; clause (ii)
      decides); a cap or error stop, or any gx2_spot stop, makes GX2'' incomplete -> FAIL.
    - **G12 P7 rule**: P7 traces may differ between main and rerun only from the first per-count/budget fallback
      (wall-clock dependent) onward; everything else must be byte-identical.
    - **2-step tiebreak count** (R_planning_detail): a planned decision counts as decided by E2 when E2 was computed and
      E1 is tied at its minimum.

## C. Held-out run (written during/after the run)

20. **Session interruption before run_start** (19:52 EDT): the operating session was interrupted after the source
    freeze; it resumed from the pushed state (f3be0bf, tree clean, nothing running). No held-out data existed. The
    only change after resuming was the GX2'' incomplete-input rule simplification (entry 19), committed before
    scoring_freeze_009 (Exact).
21. **3 h cap fired late** (written 2026-10-25 ~23:30 EDT, after the run; held-out data existed, no scored output had
    been inspected). RUN_T0 20:04:06 EDT, so the cap was 23:04:06 EDT. RUN_009.log records "3 h CAP reached" at
    23:22:42 EDT and STOP_009.json `stopped_at` 23:22:44 EDT, about 18 min 36 s after the cap (Observed). The
    orchestrator loop checks the deadline every ~2 s (scripts/run_study_009.py, frozen); why it did not act at 23:04 is
    not known. The box uptime shows no reboot; a paused process or paused session is possible but not shown (Open).
    Effect: g11 ran ~18 min past the cap and was then stopped; it wrote no output in either case, so no gate result
    differs (Inferred: g11 writes SECOND_IMPLEMENTATION_009.json only at the end and has no checkpoint). The cap is
    scored as it fired: G_RT FAIL, and gates that need g11 or GTI are FAIL STUDY_BUDGET (Exact, make_gates_009).
22. **g11 (second implementation, G11) produced nothing in 9229 s** (Observed: logs/g11.log is empty,
    SECOND_IMPLEMENTATION_009.json absent). The g11 stream had no stream budget, no checkpoint and no seal-partial
    path, so a stop left no partial evidence. G11 is FAIL STUDY_BUDGET. Its run time was not projected before the run
    (Rejected as an excuse; recorded as a design gap for v0.8.0: every stream needs a checkpoint and a projection).
23. **GTI never ran in-cap** (Observed): the gti stream depends on g11 and gp1_audit; g11 never finished, so GTI never
    started. GTI (gated) is FAIL STUDY_BUDGET. The final-tree test run (TEST_SUITE_009_FINAL.json, entry 13) was run
    after the cap on the release tree; it is reported as non-gate Observed information only and cannot make GTI pass.
    The release statement is therefore "GTI FAIL" whatever the final-tree run shows (Exact, make_gates_final_009).
24. **gx2_spot stopped by its own 1800 s stream budget** at 21:18:56 EDT with 6 of 24 spot cases checked (0 mismatches
    on those; one big6 case took 1386 s) and sealed as it is (Observed). Under make_gates_009 a gx2_spot stop makes
    GX2'' incomplete, so GX2'' scores FAIL (Exact, scoring rule fixed before data; entry 19).
25. **Release steps after the cap were run by the operating agent under a deadline of 2026-10-26 01:00 EDT** set by the
    owner's session; no study stream was relaunched or extended (Exact). Large raw files packed with
    scripts/study009_storage.py pack (deterministic gzip) before the study SEAL, as study-008.
26. **Release verifier fixed after the release freeze; freeze superseded by BRUTE_RELEASE_FREEZE_070_R1.json.** The
    first final-tree test run (23:29–23:44 EDT, kept as results/study-009/TEST_SUITE_009_FINAL_ATTEMPT1.json, not
    used by any gate) failed 3 tests of tests/test_release_070.py because scripts/verify_release_070.py had two defects
    (Observed): (a) it required a 'schema' key on every study-009 JSON, but the frozen orchestrator writes
    PROGRESS_009.json (sealed) without one; REQUIRED_KEYS now maps PROGRESS_009.json to 'streams'; (b) it re-checked
    experiments/BRUTE_RELEASE_FREEZE_060.json, which _060_R1 superseded before the v0.6.0 tag (verify_release_060.py
    is unchanged since tag v0.6.0, Exact by git diff); that freeze is no longer re-checked. No study output, scoring
    script, plan or source-freeze file changed (Exact). The fix was written after seeing the failure, by the same agent,
    and is release tooling only; RELEASE.json release_freeze now points to _070_R1. The final-tree test run was
    repeated on the fixed tree; GATES_009_FINAL uses that second run. GATES_009 is unchanged (Exact).
