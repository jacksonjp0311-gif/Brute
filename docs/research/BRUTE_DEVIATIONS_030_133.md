# Deviation #133 (study-030, v0.27.0): process events after the source freeze

Written after the run. Nothing here changes a gate, a threshold, a frozen file or a sealed result. Labels as in #132.

1. **Run completed without interruption (Observed).** run_start_030 was ledgered at 14:28 EDT and the runner was
   launched once, detached. It finished 51/51 cases in 978.9 s against the 1800 s cap, with a normal exit. The snapshot
   pusher pushed 4 snapshots, the last one (51 cases) as 189826c, then stopped after the runner exited. At about
   14:47 EDT the host interrupted the agent session. The run and the pusher had already finished: the log shows 51/51 and
   "done", and SEAL.json has complete True and the frozen freeze hash. Nothing was rerun or relaunched. The resume clause
   was not needed and remains NOT approved.
2. **No API check (Exact).** Plan 030 has no API gate and no certify/15 was built (#132 item 8). The post-run sequence
   is run_end, seal, recount, reference, tests and gates only.
3. **Test count reporting (Exact).** The frozen-pattern run_tests_0270 counts "... ok" lines. As in study-029, the
   docstring of one test in test_scripts_030 moves its "ok" to a second line, so the runner records 8 tests where
   unittest ran 9, all OK. GTI is unaffected (return code 0 for every module). Total: 55 tests run, 54 counted.
4. **The hard cap does not explain the gain (Observed; descriptive).** S5 and S5_softcap are almost the same:
   U(S5) - U(S5_softcap) at scale12 is -0.001 [-0.009, 0.006] and at scale16 -0.002 [-0.006, 0.001]. Both have
   X 5/12 at scale12. S5_softcap's max query time was 8.38 s, also under the 10.5 s bound, so in this run the
   029-style overrun did not recur even without the hard cap (S4: 10.16 s). The gain over S1 and S4 comes from removing
   the symmetry clauses (Inferred, consistent with #131 item 5). The hard cap's value as a guarantee is not shown by this
   data (Open).
5. **Noisy stress is worse for S5 at 12 states (Observed; not gated).** Stress U: scale12 S5 0.585 against S4 0.370 and
   S1 0.371; scale8 0.420 against 0.434 / 0.443; scale16 0.522 against 0.529 / 0.533. F = 0 for every arm on stress.
6. **Recovery (Observed).** identify ran on all 12 S5 cases at 12 and 16 states (vs 1 and 0 for S1) but found the exact
   machine on none. At 8 states S5 recovered 6/12 against 4/12 for S1 and S4.
