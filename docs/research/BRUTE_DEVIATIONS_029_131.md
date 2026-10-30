# Deviation #131 (study-029, v0.26.0): process events after the source freeze

Written after the run. Nothing here changes a gate, a threshold, a frozen file or a sealed result. Labels as in #130.

1. **Run completed without interruption (Observed).** run_start_029 was ledgered at 13:25 EDT and the runner was
   launched once, detached. It finished 51/51 cases in 1345.9 s against the 1800 s cap, with a normal exit. The
   snapshot pusher pushed 5 snapshots, the last one (51 cases) as 4b4955c, then stopped after the runner exited. At
   about 13:46 EDT a monitoring wait was aborted by the host. The run and the pusher were unaffected: the log shows
   51/51 and "done", and SEAL.json has complete True. Nothing was relaunched. The resume clause was not needed and
   remains NOT approved.
2. **GQB fails (Observed; cause Inferred, Open).** S4's max per-query time was 15.33 s, against a 10.5 s bound, on
   3 scale16 cases (9530002: 12.27 s, 9530003: 15.33 s, 9530010: 11.07 s). In brute/scalesearch4.py the wall is
   checked before each chunk. Two things can still overrun it (Inferred):
   - the lazy RegionK build at the first solve of a step runs inside the query with no wall check;
   - a single Glucose chunk can overrun, because Glucose honours conf_budget only at restarts (#128 item 2).
   The fault is not fixed, because S4 is frozen. It is published as a FAIL.
3. **Test count reporting (Exact).** The frozen run_tests_0260 counts "... ok" lines. In test_scripts_029, the
   docstring of test_sealed_block_gates_check moves its "ok" to a second line, so the runner records 10 tests where
   unittest ran 11, all OK. GTI is unaffected (return code 0 for every module). Total: 58 tests run, 57 counted.
4. **S1 false certificates (Observed).** The recount finds F = 0 for every arm on main and stress, including S1.
   In study-028, S1 had F = 3 on stress, on different seeds.
5. **Diagnosis check (Observed; descriptive, not gated).** The scratch diagnosis (scratch_diag_029) named symmetry
   clauses as the cost. The held-out data agree:
   - At scale12, removing them from S4 (S4_nosym) gave U 0.079 [0.020, 0.149] against 0.161 for S4. The paired
     difference was -0.082 [-0.118, -0.046].
   - Compared with S1, S4_nosym's difference was -0.100 [-0.145, -0.059].
   - X(S4_nosym, scale12) was 6/12, against S4 2/12 and S1 1/12.
   - S4_nosym had F = 0 and 0 mismatches with S1 on 17207 compared answers.
   S4_nosym was descriptive in plan A1, so this is a v0.27.0 hypothesis, not a v0.26.0 result.
