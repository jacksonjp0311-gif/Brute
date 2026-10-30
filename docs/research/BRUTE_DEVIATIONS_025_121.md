# Deviation #121 (study-025, v0.22.0): API-check script t0 bug, fixed in a new r1 file

Logged 2026-10-30 EDT, after run_end_025 and before any gate was computed.

1. **What happened (Observed).** `scripts/api_check_025.py` (frozen in BRUTE_SOURCE_FREEZE_025) crashed with
   `NameError: name 't0' is not defined` after computing the 4-case comparison. When the A2 lean case selection was added,
   the statement `t0=time.time()` ended up inside the trailing comment of the same line. The crash happened while
   building the output, so no API_CHECK_025.json was written.
2. **Fix.** A new file, `scripts/api_check_025_r1.py`, is byte-identical except that `t0=time.time()` is moved to its own
   line, plus one docstring sentence. The frozen original is not edited. The case selection, the comparison and the
   `passed` rule are unchanged. It writes `results/study-025/API_CHECK_025.json`, which GS_a11 reads.
3. **Effect on gates (Inferred).** None on the criteria: t0 feeds only `wall_informational`. Caught because the
   fake-pipeline smoke ran a case set that the A2 line edit was made after.
