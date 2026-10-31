# Deviation #162 (study-044, v0.41.0): post-run record

Written after the gates (2026-10-31T04:39:42-04:00, box-local EDT). Nothing here changes a gate outcome, threshold or seed. Labels: Exact, Observed,
Simulated, Inferred, Rejected, Open. Times are EDT (UTC-4).

1. **Run (Exact).** source_freeze_044 (ledger 3bb6deb, 03:55:07 EDT, freeze commit 1f7d147); run_start_044 (ledger b620bfc,
   03:55:09 EDT); one main run, 54/54 arm jobs, 18 cases, 490.4 s of 3600 s, normal exit about 04:03:28 EDT; two checkpoint
   snapshots (09229e3, f4c162f); seal db7e84e; run_end_044 (ledger ea27599). Nothing relaunched; the resume clause was not used.
   No edit to frozen code during the run. The A16_c30 cut was not applied (prefreeze projection below the 1800 s trigger, #161 item 8).
2. **Outcome (Exact).** 9 of 11 gates pass. GLO_cap FAILS: A16_c30 ID+IDF 2/12 [0.05, 0.45] (ID 1, IDF 1) against A16_c9 0/12
   [0.00, 0.24], gain 2 (bars: >= 3/12 and gain >= 2). GLO_pol FAILS: A16_xf ID+IDF 2/12 [0.05, 0.45] (ID 2), gain 2 (same bars).
   Both gains meet the gain bar; both totals miss the 3/12 bar by one case. Controls 6/6 ID in every arm. WRONG 0; 83 words, 0 unsound.
3. **Branch taken (Exact).** Plan 044 next_if_fail, first clause: "both GLO_cap and GLO_pol fail: one-bit 12-state worlds are
   beyond A16 at these budgets; publish it and move to the N-free stop as v0.42.0, then certify/16 (maintainer order)".
4. **GLO_cause2 (Observed).** lowobs12 last phase of the undecided runs: c9 least 9, future 3; c30 least 9, future 1; xf least 8,
   future 2. n_min was reached (11 or 12) on 3, 3 and 4 cases. Longest arm walls 58.9 s (c9), 421.7 s (c30), 61.8 s (xf) against
   budgets of 240, 600 and 240 s. A16_xf spent its full 32 schedule experiments.
5. **GQB19 (Observed).** Max call 9.561 s (c9), 30.604 s (c30), 10.009 s (xf) against bounds 10.5, 31.5 and 10.5 s; 1068 calls
   logged; 1 hard kill (A16_xf on 10930004, "hard deadline", recorded unknown). A kill is unknown, not a soundness failure (plan).
6. **Reference and GS_ref (Exact).** REFERENCE_044 (8fd768c, ledger 59e8154): 36 lowobs12 records, 4 decided (c30 2, xf 2),
   0 mismatches, 20/20 mutations; not vacuous. Reference walls were long (informational): 98 s to 1888 s per decided record.
7. **Ledger order of tests (Exact).** TEST_SUITE_044 was committed at e4a3ddf before the reference finished; it was ledgered as
   tests_044 (87a0a83) after reference_044, keeping the 043 event order. G_PROC does not include tests in its subsequence.
8. **Reading (Inferred).** A longer cap and an experiment-first schedule each moved lowobs12 from 0 to 2 of 12, the same small
   gain, and most runs still stop unknown in the least-model search. Neither change is enough at these budgets.
9. **GC9 (Observed).** A16_c9 0/12 replicates the 043 A16 baseline 0/12 on fresh seeds.

What this deviation does not do: no rerun, no tuning, no gate change. Lowobs identification stays Open.
