# Deviation #188 (study-057, v0.54.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 2 2026). It fixes readings of BRUTE_PLAN_057 (plan/v0.54.0, commit
a8dfa1d, ledger preregistration_057 ccae49d; no amendment; the plan is locked) that the plan leaves open. It changes no threshold,
seed, cap (K, B, C), worker count, order or gate. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_057 (a8dfa1d, ledger ccae49d, 08:26 EST), build_authorization_057 (ledger ee31358, James's
   standing go t133s553 and the new standing go t139s684), seedcheck_057 (263bd6b, ledger a83afa1; PASS, 12 cases), study tooling
   (a46876c, b938be8, e073f1d, 206ea78, e8cd2a8, ca52929, b53eb67, 1474d69, 1e452a9), prefreeze smoke attempt 1 (79d6a9d, ledger
   7a9bfaf; also ledgered as prefreeze_smoke_057, 99f69be), then deviation_188, source_freeze_057, run_start_057, run_end_057,
   recount_057, reference_057, api_checks_057, tests_057, gates_057, #189. Lean process; the main run goes once with nohup and is
   never relaunched.
2. **canon57 (Exact rule).** GDET57's canon is canon57(r) = dumps({canon16e(r), ext_len, ext_acts, api}): the frozen 051 canon16e
   plus the extension (length and actions) and the arm's certify/16e api result. No wall field enters it.
3. **Recount 'used' reading (Exact rule; plan G_recount).** For extension arms the frozen recount_047.recount_case emits the tuple
   (arm, 'used', a['used'], len(extra_acts)) because extra_acts holds the extension and then the certifier's words. recount_057 drops
   exactly that tuple iff a['used'] == words_executed_length and len(extra_acts) == ext_len + used (recorded per record as
   used_ok_057); every other recount item, including used_vs_words, is unchanged. Tested both ways (tests/test_scripts_057).
4. **Oracle, LEN_R and cover20 (Exact, from code).** oracle_walk = the plan's oracle_walk (BFS from the true state after the prefix,
   actions in index order, nearest state with an unexercised action, its lowest unexercised action, until every pair reachable from
   the post-prefix state is exercised). LEN_R: L = len(oracle_walk) on the same seed, actions random.Random(seed*7+57).randrange(3).
   COV_X / COV_X_b: brute.cover20/1 with h = 1, STEPS = 120, counts including the passive prefix. recount_057.coverage_case
   recomputes the oracle independently (its own BFS), checks the LEN_R RNG, checks API16E20's extension is empty, and recomputes
   every coverage field from the world.
5. **Coverage fields (Exact).** truth_pairs_unexercised_{prefix, handoff, handoff_reachable, final, final_reachable}: (state, action)
   pairs of the true machine not taken by the walk (prefix; prefix + extension; prefix + extension + certifier words), the
   *_reachable variants counted only over states reachable from the post-prefix state. GMATCH57 uses handoff_reachable.
6. **Cut rule (Exact; applied).** Projection (Inferred) at the slowest smoke rate: r_slow = 6298.7 conflicts/s, worst job =
   B20 / r_slow + 10 s = 327.5 s, LPT of 60 jobs on 8 workers = 2620.2 s <= 3300 s, so no cut: N57 = 12 (cut_consistent true).
7. **GTI57 and SEEDCHECK57 (Exact).** GTI57 gates RECOUNT_057 truth_inconsistent == 0 (bound to the sealed RESULTS sha). The seed
   check is reported as secondary SEEDCHECK57 (seedcheck_057 is already a G_PROC event).
8. **GFID57 scope (Exact).** api_checks_057 fidelity replays only COV_X (12 records): cover20 must re-propose the recorded extension
   from the recorded observations, then certify/16e must reproduce the api result and every round's ROUND_FIELDS on the trace.
9. **GHOST57 no-network loop (Exact).** The socket-disabled subprocess runs cover20 + Certifier16E on smoke seed 12430003 at bound
   20, C 50000, B 2000000 (smoke: IDU, 2000659 conflicts, 120 steps, 0 socket attempts). Frozen-API shas are checked for certify
   14/16/16d/16e/16n/16s/20t/20c/20l against their own freezes (20l against BRUTE_SOURCE_FREEZE_056).
10. **Smoke use (Exact).** 12430001-02, all 5 arms (10 jobs, one 8-worker pool); 12430003 only by the no-network check; 12430004-06
    unused.
11. **Smoke finding (Observed; early warning, not gated).** All 10 smoke records ended IDU/unknown with B spent (about 2.0M
    conflicts each), including COV_O, whose hand-off left 0 unexercised pairs on both seeds (extension 45 and 24 steps). COV_X left
    1 and 3 reachable pairs unexercised at hand-off. Reading (Inferred): full coverage alone did not let certify/16e decide within
    B20 on these two seeds, so GPRE57 and GX_gain57 are likely to fail; per the plan's next_if_fail branch, the bottleneck would then
    be the solver budget rather than missing transitions. This is declared before the freeze; nothing is changed because of it.
12. **Numbering (Exact).** This file is the pre-run deviation #188; the post-run deviation is #189.
