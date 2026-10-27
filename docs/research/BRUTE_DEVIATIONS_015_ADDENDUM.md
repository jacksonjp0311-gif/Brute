# BRUTE_DEVIATIONS_015 addendum (v0.13.0, after run_start)

BRUTE_DEVIATIONS_015.md (#64-#73) is ledger-hashed and stays unchanged. This addendum records what was found after run_start_015.

## #74 TEST_SUITE_015 records tracked_tree_dirty = true

- **Observed:** `results/study-015/TEST_SUITE_015.json` has `tracked_tree_dirty: true` (study-014: false). `git status --porcelain --untracked-files=no` was clean before run_start (commit 6406522) and after RUN_DONE.
- **Observed:** the same file reports `frozen_files.changed: []` over 488 files, and all five GTI clauses pass.
- **Open:** which tracked file was modified while the suite was running, and whether a test changed it temporarily. No re-run (plan: nothing after run_start). GTI is scored as recorded.
- **Not changed:** gates, budgets, seeds and scoring scripts.
