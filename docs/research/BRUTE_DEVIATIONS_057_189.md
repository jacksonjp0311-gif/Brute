# Deviation #189 (study-057, v0.54.0): post-run record

Written after the run, from the sealed outputs (GATES_057 7718a2a). Times are box-local EST (UTC-5), 2026-11-02. It changes no
gate, threshold, seed, cap or label. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Process (Exact).** prefreeze_smoke_057_attempt1 then prefreeze_smoke_057 (attempt 1 PASS); deviation_188 (6749c67); source
   freeze 3db1525 (527 files, ledger ea1af1a); run_start_057 (2a2f9a8; launched once with nohup 09:01:55 EST, pid 1742858, 60 jobs
   on 8 workers); 7 checkpoint snapshots (8591b45 .. 28cba98); seal 9f9b477 (ledger c5e3fc9; 60/60 jobs, 12 cases, 1936.5 s);
   recount cfdc43c; reference fd3695c; api_checks f4e8300; tests 3bd09eb; gates 7718a2a. The main run went once and was never
   relaunched.
2. **Run_start note (Exact).** The run_start_057 ledger note carries its timestamp twice (the ledger helper already prefixes the
   time and the note text repeated it). The ledger is append-only, so it is left as written; G_PROC parses it.
3. **Tests ran concurrently with api_checks (Exact).** run_tests_0540 --official ran once from about 09:52 EST while
   api_checks_057 (09:50-10:11 EST) was still running on the same box. Both passed. Neither depends on the other's output; the
   ledger events are in the order G_PROC requires (api_checks_057 before tests_057).
4. **Results (Exact, recount labels; Wilson 95%).** 12 of 14 gated pass. GPRE57 FAILS: COV_O ID+IDF 1/12 [0.01, 0.35] vs LEN_R
   0/12 [0.00, 0.24]; the rule needs >= 3/12 and a lead of >= 2 (McNemar discordant 1/0, p = 1.00, reported). GX_gain57 FAILS:
   COV_X 0/12 [0.00, 0.24] vs API16E20 0/12 [0.00, 0.24]. Every soundness gate passes: WRONG 0 of 60 records, G_sound 527 words
   0 unsound, GS_ref 0 mismatches 20/20 mutations, GTI57 0. GDET57 12/12 [0.76, 1.00], GFID57 12/12 [0.76, 1.00], 0 hard kills.
   certified_20v_N20 false, sound_not_certified_20v true: certify/20v is 'sound but not certified'.
5. **What COV_O is (Exact).** COV_O is an oracle arm, not an API: it reads the TRUE machine and walks until every transition
   reachable from the post-prefix state has been exercised, then hands the trace to certify/16e. It cannot be deployed and is
   never certified. LEN_R is the control: a random walk of exactly COV_O's length.
6. **The coverage lead is refuted as sufficient (Observed, on 12 seeds).** GMATCH57 confirms COV_O reached 0 unexercised
   reachable pairs on all 12 seeds, yet certify/16e still decided only 1 of them (12410008, ID); the other 11 spent B = 2M as
   IDU. The 056 lead (both decided records had 0 unexercised transitions) was therefore an effect of decided runs, not a cause:
   full coverage at this budget is not enough. The 1-vs-0 difference against LEN_R is not evidence of a coverage effect (p = 1.00).
   Per plan next_if_fail, coverage is published as not causal at this budget.
7. **cover20 did not reach coverage (Observed).** COV_X's hand-off left a mean 4.3 reachable pairs unexercised (full on 1/12);
   COV_X decided 0/12 and its only non-IDU record was AMB/K_spent (12410008), as were API16E20 and LEN_R on that seed.
8. **Smoke early warning confirmed (Exact).** #188 item 11 (Inferred) said GPRE57 and GX_gain57 would likely fail. They did.
9. **No 'first' claim (Exact).** 12410008 (COV_O, ID) is not the first decided 20-state world: study 050 decided 11730008 at B 4M
   and study 056 decided 12330005 at B 2M.
10. **Seven versions at 20 states (Observed).** v0.47.0 to v0.54.0 tried more budget, a wider encoding, cube-and-conquer, L*
    tables and coverage-first walks; across them certify/16e-style identification at 20 states decided 4 of about 70 fresh
    records. The plan for v0.55.0 changes the target instead of trying an eighth identifier.
11. **Claim scope (Exact; reason Inferred).** Every ID / IDF is exact only conditional on the declared N; a larger machine can copy
    the true machine on every visited state.
