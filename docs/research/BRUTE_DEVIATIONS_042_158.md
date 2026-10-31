# Deviation #158 (study-042, v0.39.0): post-run record

Written after the gates (GATES_042 `d774d8c`, ledger `cbed51f`). Nothing here changes a gate, threshold, sealed file or frozen file.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4), 2026-10-31.

1. **Reference invocation error, not a rerun (Observed).** The first launch of `scripts/run_reference_042.py` (about 02:12)
   named `results/study-042` instead of the block directory `results/study-042/main`. It raised FileNotFoundError while
   loading inputs, checked no verdict and wrote no output. It was launched once more with the correct path and `--workers 4`;
   that single run wrote REFERENCE_042 (PASS: 12 records, 9 decided, 18 verdicts, 0 mismatches, 20/20 mutations; `6af5717`,
   ledger `0354cb1`). The main study was not touched.
2. **Interrupted commit chain (Observed).** At about 02:22 a chained tool call (commit REFERENCE_042, ledger, commit
   TEST_SUITE_042, ledger, commit RECOUNT_041B) was reported as aborted. All five commits exist (`6af5717`, `0354cb1`,
   `f33750b`, `35e9d62`, `4655c34`); the last was not yet pushed and was pushed at about 02:23 with no change. Nothing was
   relaunched or recomputed.
3. **G_PROC sees the plan erratum (Exact).** The ledger events read preregistration_042, plan_erratum_042,
   build_authorization_042, ... ; PROC_ORDER is checked as a subsequence (#157 item 7), so the erratum entry is allowed and
   G_PROC passes.
4. **GT16 direction (Exact).** GT16 reports mean per-case call wall A16 / A14 = 0.82, seed-bootstrap [0.71, 0.95]: A16 calls
   are on average cheaper than A14 calls, not dearer. Reported only (secondary).
5. **Release verifier on the real commit order (Observed).** `scripts/verify_release_0390.py` chain on COMMIT_ORDER_042 passes
   with 1 build-authorization exception (the 0380a rule declared in #157 item 9); no addendum is needed.
6. **Next step differs from plan 042 next_if_pass (Exact).** Plan 042 names "API study for brute.certify/16 (A16), then a
   scale-20 replication" if G16 passes. James's v0.39.0 order (01:32) asks instead for a generality step (lowobs or the
   N-free stop) as v0.40.0. Plan 043 follows the order and records the plan-042 text as deferred, not dropped.
