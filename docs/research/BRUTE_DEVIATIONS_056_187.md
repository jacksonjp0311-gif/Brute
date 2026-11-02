# Deviation #187 (study-056, v0.53.0): post-run record

Written after the run, from the sealed outputs (GATES_056 6f0dc9e). Times are box-local: EDT (UTC-4) until 02:00 EDT on 2026-11-01,
EST (UTC-5) after the DST change. It changes no gate, threshold, seed, cap or label. Labels: Exact, Observed, Simulated, Inferred,
Rejected, Open.

1. **Numbering (Exact).** The pre-run deviation is filed as #185 (the name make_freeze_056 freezes); the instructions called it
   "#186". No #186 file exists. This post-run record is #187, as instructed.
2. **Process (Exact).** prefreeze_smoke_056_attempt1..4 then prefreeze_smoke_056 (d74de10, attempt 4's receipt); deviation_185
   (4fc4c4f); source_freeze_056 (bf24a96, ledger 2b329d9; 496 files); run_start_056 (6a51e28; launched once 00:53:57 EDT, pid
   1657528); 3 snapshots (198fd32, 97a36b2, c5c8c10); seal 4bf2056 (ledger eed51f3; 30/30 jobs, 12 cases, 695.8 s); recount 9ffd0e0;
   reference 5c0c423; api_checks 41d98a5; tests 0a33012; gates 6f0dc9e. The main run went once and was never relaunched.
3. **Fix E disclosure (Exact; repeated from #185 item 16, as instructed).** Fix E (aa266bb) loosened a prefreeze PASS clause and was
   made AFTER prefreeze attempt 3 failed on that clause. It is acceptable only because plan 056 says the smoke is never gated: it
   would have hidden nothing gated, since GCOMPAT20L56 is scored on the 6 main controls only under the unchanged rule and threshold.
   The smoke compat results were AMB vs ID (12370003) and AMB vs IDF (12370004): an early warning that GCOMPAT20L56 would likely fail
   in main. It did fail (2/6, item 5).
4. **K finding confirmed (Observed).** API20L spent 126-128 of K = 128 on table filling in 17 of its 18 records (scale20t both passes
   and compat20t): one hypothesis, 0 counterexamples, then AMB/K_spent (16 records) or IDU at B (12330004, both passes). The one
   exception, compat20t 12350002 (fill 24, 9 counterexamples, 10 hypotheses), ended IDF, equal to certify/16e. K was not changed.
   Per plan next_if_fail, the table is what runs out: 20 states are out of reach for certify/20l at B 2M, K 128 on this family.
5. **Results (Exact, recount labels; Wilson 95%).** 12 of 14 gated pass. GS20L_gain56 FAILS: API20L ID+IDF 0/6 [0.00, 0.39] in both
   passes, API16E20 1/6 [0.03, 0.56] (12330005 ID). GCOMPAT20L56 FAILS: 2/6 [0.10, 0.70] (12350002 IDF same machine; 12350006 AMB both).
   Every soundness gate passes: WRONG 0 of 30 records [0.00, 0.11], GS_ref 16/16 decided audited 0 mismatches 20/20 mutations,
   GTABLE56 18 records 1467 entries, G_sound 226 words 0 unsound. GDET56 6/6 [0.61, 1.00], GFID56 18/18 [0.82, 1.00], 0 hard kills.
   certified_20l_N20 false, sound_not_certified_20l false: certify/20l is 'not certified, no certification status' (failing gates:
   GS20L_gain56, GCOMPAT20L56).
6. **No 'first' claim (Exact).** 12330005 is not the first decided 20-state world: study 050 (v0.47.0) decided 11730008 as ID with
   certify/16e at B 4M.
7. **Exploratory lead (Observed, exploratory, not gated, not pre-registered).** results/diag-056/WORLD_FEATURES_056.json (282b14f,
   read-only over sealed 050-056 RESULTS): of 42 certify/16e records at 20 states, the only 2 decided (050 11730008 at B 4M, 056
   12330005 at B 2M) are both among the 6 records with 0 unexercised transitions; the other 36 decided 0. Caveat (Inferred): the
   feature is measured on the run's own trace, so it may be a consequence of a long run rather than a cause; 2 of 6 is small.
8. **api_checks launch (Exact).** The first api_checks_056 command (about 01:42 EDT) stopped at argparse (`--study` needs a path)
   before any check ran (log kept in /tmp only). The one real run used `--study results/study-056/main` (01:42-01:49 EDT).
9. **Tests (Exact).** run_tests_0530 --official ran once, started about 01:53 EDT; the file was written 01:00 EST (after DST) and the
   session was interrupted before the commit. It was committed and ledgered as-is on 2026-11-02 (08:0x EST), not rerun.
10. **#185 cross-reference (Exact).** #185 item 6 says "item 17" for the K finding; it is item 18. #185 is ledger-hashed and frozen,
    so it is left as written.
11. **compat_rule_056 (Exact).** Introduced after the 055 compat failure; not retroactive. RECHECK_055 (reported only) finds both
    055 pairs 12270003 and 12270005 equal under it; GATES_055 and every 055 file are unchanged.
12. **Claim scope (Exact; reason Inferred).** Every ID / IDF is exact only conditional on the declared N; a larger machine can copy
    the true machine on every visited state.
