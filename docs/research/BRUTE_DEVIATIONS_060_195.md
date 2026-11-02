# Deviation #195 (study-060, v0.57.0): post-run record

Written after the gates (box-local EST, UTC-5, Nov 2 2026). It changes no threshold, seed, cap or gate and no sealed output.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** This is a **TARGET CHANGE**: 4-bit random readings, declared N raised from 20 to 24 (gated)
   and 32 (reported). It says nothing new about the original 2-bit problem: **2-bit readings at 20 states stay Open.**
1. **Process (Exact).** preregistration_060 455f215, build_authorization_060 ca2d11d, seedcheck_060 e0b7125,
   prefreeze_smoke_060 268f2a5 (attempt 1 3d7190c), deviation_194 4eb533a, freeze_060 e1237fd (caa854f, 624 files),
   main_run_060 6d7d02b (launched once with nohup at 13:58:06 EST, pid 1931849, never relaunched), seal ac95e8c
   (run_end_060 4b779dc, 14:34:53 EST), recount 38da546 / 8bc5bec, reference 442cff4 / ae2300b, tests 31f3c17 / 3867b71,
   api_checks fde59e8 / 309de44, gates da88bdd / c622d9c.
2. **Launch-time wording (Observed; disclosed).** The run_end_060 ledger note says "launched once 14:00 EST"; that was a
   rounded figure. The authoritative launch time is the main_run_060 note, 13:58:06 EST. Same run, same pid.
3. **Aborted tool call around the tests (Observed; disclosed).** The shell call that launched the official run_tests_060
   together with a long sleep came back "Aborted". The test process still ran to completion and wrote
   results/study-060/TEST_SUITE_060.json (13 modules, 11 gated, 2 reported, 131 tests, all returncode 0). The file was checked
   for completeness, committed as-is and was **not rerun**. Later launches were split (nohup launch, then separate sleeps).
4. **Walls slower than the probe (Observed).** S24 IDU jobs took 376-599 s against the budget probe's lower estimates; S32
   jobs took 507-1955 s. Runner total_elapsed_informational 2075.9 s, inside the 60 min cap and the 3300 s smoke projection
   (3262.4 s). No cut was needed (N24 = 12, N32 = 6). Walls are informational, not gated.
5. **Result (Observed; labels from the independent recount).** S24 decided 8/12 (7 ID, 1 IDF) Wilson 95% [0.39, 0.86]; S24b
   identical 12/12 [0.76, 1.00]. The four IDU seeds (12600101, 102, 103, 109) hit the 8M conflict budget with n_min 23, 23, 24,
   23. Decided records used 2.86-5.59M conflicts. WRONG 0 of 30 records [0.00, 0.11].
6. **S32 (Observed; Open).** 0/6 decided [0.00, 0.39]; every record IDU at about 8.0-8.7M conflicts, n_min 29-32. Declared N 32
   is not supported by this budget; it stays Open.
7. **Gates (Exact).** All 9 gated criteria pass: GS60_sound, GN24_60 (8 >= 6 of 12), GDET60, GFID60 (16/16 exact),
   GHOST60, GS_ref (16/16 audited, 0 mismatches, 20/20 mutations, 94.1 s), G_recount, GTEST, G_PROC.
   certified_readbits4_N24 true, sound_not_certified_N24 false; status phrase "certified (read_bits 4, N <= 24)".
   G_RT is checked at release.
8. **Scope (Exact + Inferred).** An ID/IDF is exact only conditional on noise-free readings and a true size at most the
   declared N = 24. Reason (Inferred): a larger machine can copy the true machine on every visited state. Random 4-bit
   emissions only, one transition-graph family, 12 seeds; the 8M budget leaves 4/12 undecided.
