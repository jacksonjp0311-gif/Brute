# GTI smoke note (v0.14.0, BRUTE_PLAN_016)

GTI_SMOKE_016.json is copied unchanged from the smoke run (head fa0a6fe, 2026-10-27 03:36-04:19 EDT, wall 2561 s).

- Clauses i, ii, iv, v passed; 0 undeclared failures (Observed).
- Clause iii (clean-tag count = plain-discover count) failed: 522 vs 533 (Observed).
- Cause (Exact): plain discovery ran in the working tree, which then held the untracked `tests/test_scoring_016.py`
  (11 tests); the clean-tag run used only tracked files. The module set differs by exactly `test_scoring_016`, and
  11 = 533 - 522. No tracked file was dirty.
- Consequence (Inferred): none for the gated GTI run, which happens after `tests/test_scoring_016.py` is committed
  under the scoring freeze. No source or test change was made in response to this smoke.
