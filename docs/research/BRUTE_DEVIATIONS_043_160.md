# Deviation #160 (study-043, v0.40.0): post-run record

Written after the gates (2026-10-31T02:59:10-04:00, box-local EDT). Nothing here changes a gate outcome, threshold or seed. Labels: Exact, Observed,
Simulated, Inferred, Rejected, Open. Times are EDT (UTC-4).

1. **Run (Exact).** run_start_043 (ledger 4490ba8, 02:49 EDT); one main run, 60/60 arm jobs, 30 cases, 159.7 s of 1800 s, normal
   exit about 02:51:49 EDT; one checkpoint snapshot (e7bae0d); seal 122f7a1; run_end_043 (ledger 340be32). Nothing relaunched;
   the resume clause was not used. No deviation from the frozen code during the run.
2. **Outcome (Exact).** 10 of 11 gates pass. GLO FAILS: A16 ID+IDF 0/12 [0.00, 0.24] on fresh lowobs12, A14 0/12 [0.00, 0.24],
   gain 0 (bars: >= 4/12 and gain >= 3). GREP16 PASS: A16 ID 9/12 [0.47, 0.91] on fresh scale16_rep, A14 1/12 [0.01, 0.35]
   (A16 also IDF 1, IDU 2). The 042 scale16 result (8/12) replicated on new seeds. WRONG 0 everywhere; 354 words, 0 unsound.
3. **Branch taken (Exact).** Plan next_if_fail: "GLO fails with GREP16 passing: one-bit observations need a different experiment
   policy, not a new encoding; plan a lowobs budget/K audit using GLO_cause". The N-free stop does not start next.
4. **GLO_cause (Observed).** All 24 lowobs12 arm runs stopped "unknown" after a capped call (9.0 s cap). A14: 12/12 stop in
   the first least-model phase with 0 experiments used. A16: 9/12 last phase least, 3/12 future; 7/12 used 0 experiments; used
   at most 16 of K = 128; n_min reached 11 or 12 in 3 cases. Longest lowobs arm wall 62.6 s of the 240 s budget (mean 23.4 s).
5. **Reading (Inferred).** Neither K nor the 240 s case budget bound the lowobs runs; the binding limit was the per-call 9.0 s cap
   in the least-model search, reached before experiments start. This is a reading of the secondary record, not a gate.
6. **Secondary (Observed).** GT17 call wall A16/A14 0.81 [0.72, 0.90] (lowobs12 0.88 [0.80, 0.97], scale16_rep 0.57 [0.49, 0.66],
   control 1.13 [1.05, 1.24]); H3 upper < 2 holds. GPH18: lowobs12 capped calls A14 least 12/114; A16 cube 15/160, least 11/141,
   rival 4/21. GQB18 max call 9.596 s (bound 10.5 s), 0 hard kills in 1643 calls.
7. **Prefreeze PASS term (Exact).** As declared before the run in #159 item 8; the release verifier chain does not require an
   exception count.

What this deviation does not do: no rerun, no tuning, no gate change. Lowobs identification stays Open.
