# Deviation #135 (study-031, v0.28.0): post-run events

Written after the run. Nothing here changes a threshold or a gate result in BRUTE_PLAN_031; GATES_031.json is the
record. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Run (Exact).** One pass, 54/54 cases, 1028.1 s of the 1800 s cap, normal exit (run_start 1ba5397, 15:23 EDT;
   run_end a976182, 15:41 EDT). Four checkpoint snapshots were pushed. No relaunch; the resume clause was not approved
   and was not needed.
2. **Headline fails (Observed).** GSC6 b: mean U(S6) - U(S5) at 16 states = +0.0042, CI [-0.0075, 0.0164] (bar <= -0.06,
   CI upper < 0). GSC6 c: X(S6, scale16) = 0/18 [0, 0.176] (bar 4/18). Clause a (0 mismatches) and d (F = 0) pass.
   S6_noorder is indistinguishable from S6 (U diff -0.0036 [-0.0166, 0.0066]).
3. **Why S6 gave nothing (Inferred from counters_mean and timing_mean_s).** The incremental solver removed the rebuild
   cost (mean build time at scale16: S5 2.39 s, S6 0.14 s), but build was a small share of the time; solve time did not
   fall (S5 51.4 s, S6 54.2 s per case at scale16). The persistent solver hit the hard per-query cap more often (cap stops
   per case at scale16: S5 1.3, S6 45.8; solver UNKNOWNs: S5 8.1, S6 49.9). The plan's premise, that per-query rebuild
   was the 16-state bottleneck, is Rejected by this run. Per-query hardness under the cap is the bottleneck (Inferred).
4. **GQB6 fails (Observed).** One query took 10.857 s, on stress/scale16/9730003 (bound 10.5 s). The main-block maximum
   for S6 was 9.98 s. The cap is checked between solver chunks, so one chunk can overrun it under 8-worker contention
   (Inferred, not measured this run).
5. **GID6 fails on b (Observed).** ID(S6, scale12) = 0/12 [0, 0.242]; AMB 11/12, NR 1/12. WRONG = 0 for every arm. The
   trace-only probe shows unexercised truth pairs in 11/12 scale12 cases and 18/18 scale16 cases, so a second least
   machine exists. This is a limit of the trace's information, not of the search (Inferred). S5 got ID 1/12 at scale12
   because S5 finished the one case that the probe labels ID and S6 did not (NR).
6. **Noise (Observed, descriptive).** Stress U over both stress scales: S1 0.370 [0.147, 0.578], S5 0.568 [0.455, 0.666],
   S6 0.568 [0.451, 0.667], S6_noorder 0.566. U(S6) - U(S1) on stress = +0.198 [-0.038, 0.445]. At stress scale16, S1
   finishes 2/3 cases and S5/S6 finish 0/3. The noise weakness of the symmetry-free line seen in study-030 is still there.
7. **Process notes (Exact).** The build pieces (runner, gates, recount, reference, release tooling) were committed
   without a ledger entry per piece, under the lean process; the source freeze (e74469a, ledger e29bdba) hashes all 37
   files. One Shell call returned "Command failed to spawn: Aborted" after the reference run had finished (exit 0); the
   output was intact and was committed normally (4f2c9fc). In TEST_SUITE_031, test_scripts_031 ran 10 tests but the
   parser counted 9 (one test has a docstring line); all 7 modules returned 0.
