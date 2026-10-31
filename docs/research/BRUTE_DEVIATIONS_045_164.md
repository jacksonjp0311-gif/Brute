# Deviation #164 (study-045, v0.42.0): post-run record

Written after the gates (2026-10-31T05:33-04:00, box-local EDT). Nothing here changes a gate outcome, threshold or seed. Labels: Exact,
Observed, Simulated, Inferred, Rejected, Open. Times are EDT (UTC-4).

1. **Run (Exact).** source_freeze_045 (ledger e2ebff5, 05:10:24 EDT, freeze commit e7f5b03, 164 files); run_start_045 (ledger
   ce28a01, 05:10:36 EDT); one main run, 54/54 arm jobs, 18 cases, 443.0 s of 3600 s, normal exit about 05:18:04 EDT; two
   checkpoint snapshots (ec3f718, c70c6c3); seal eff7182; run_end_045 (ledger 1c0ef0b, 05:19:34 EDT). Nothing relaunched; the
   resume clause was not used. No edit to frozen code during the run.
2. **Outcome (Exact).** 10 of 12 gates pass. GNF_agree FAILS: A16_nf2 scale16 ID+IDF 0/12 [0.00, 0.24] (bar 8/12); A16_N decided
   10/12, and A16_nf2 agreed on 0 of those 10 [0.00, 0.28] (bar 90%). G10 FAILS: A16_N ID on 6/6 controls; A16_nf1 and A16_nf2
   IDF (not ID) on 6/6 controls, as predicted before the freeze (#163 item 10). GNF_bound PASSES (21 nf decided records, all
   audited at bound n_min + delta, 0 mismatches, 20/20 mutations). GNF_misfire PASSES (A16_nf2 0 misfires over 6 ID/IDF
   [0.00, 0.39]; A16_nf1 0 over 6 [0.00, 0.39], reported). GLO_sem, GQB20 (max call 9.225 / 9.337 / 9.331 s against 10.5 s,
   4170 calls, 0 hard kills), GS_ref, GTI, G_PROC, G_RT, G_recount, G_sound pass.
3. **Branch taken (Exact).** Plan 045 next_if_fail, third clause: "GNF_agree fails with GNF_bound and GNF_misfire passing: the
   nf stop is sound but weaker; record it and move to certify/16 with A16_N". G10 also fails; plan 045 names no branch for G10,
   and its failure (IDF instead of ID on controls) is the same weakness, not a soundness fault.
4. **Scale16 detail (Observed).** A16_nf2 on 12 scale16 cases: AMB at K_spent 4, unknown 8 (last phase future on all 8). A16_nf1:
   AMB at K_spent 5, unknown 7 (future 6, least 1). On every nf case but two (n_min 14 and 15) the least-model search reached
   n_min = 16, the true size; the run then stalled in the future rival search at sizes 17-18 or spent K. A16_N: ID 9, IDF 1,
   unknown 2 (future). Arm wall summed over scale16 (GNF_cost, Observed): A16_N 538 s, A16_nf1 1362.7 s, A16_nf2 1374.1 s; rival
   phase 379 s, 1105 s and 1168 s.
5. **Reading (Inferred).** Once n_min equals the true size, a bound of n_min + delta is larger than the true machine. A bigger
   machine can copy the true one on every visited state and differ on states the trace never pins down, so future rivals keep
   existing (AMB until K runs out) or the search above 16 states times out at the 9 s cap. On controls the future rival search
   at n + 1 and n + 2 was empty, but a larger machine with a different start existed, hence IDF. The N-free stop at delta 1 or 2
   is sound (the bounded claim was never false) but it is weaker than the declared-N stop on these worlds. The mechanism of the
   stall above 16 states is Open.
6. **Reference and GS_ref (Exact).** REFERENCE_045 (f1eae80, ledger f7c61da): 54 records, 37 decided (A16_N 16, A16_nf1 11,
   A16_nf2 10), all audited; complete = true; not_audited empty; 0 mismatches, 0 misfires; 20/20 mutations; 373 s of the 1800 s
   budget. The scope of #163 item 4 was declared but did not bind.
7. **Ledger order of tests (Exact).** TEST_SUITE_045 (61fa56b) was run and ledgered (tests_045, f66f105) after reference_045, as
   in 044. G_PROC does not include tests in its subsequence.
8. **GREP16b (Observed).** A16_N scale16 ID+IDF 10/12 [0.55, 0.95], beside 043 GREP16 9/12 [0.47, 0.91]: replicated.

What this deviation does not do: no rerun, no tuning, no gate change, no new delta. Full N-freedom stays Open.
