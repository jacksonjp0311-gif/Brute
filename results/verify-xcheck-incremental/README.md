# Post-release verification: GX2' re-run with an incremental harness (v0.6.0, study-008)

**This is not a v0.6.0 artifact and cannot change the frozen GX2' verdict (FAIL, incomplete coverage; BRUTE_PLAN_008).**
No frozen file, plan, freeze manifest or sealed study-008 artifact was modified. Branch `verify/xcheck-incremental`, not merged.

* Harness: `brute/xcheck_sat_incremental.py` (IncSolver) + `experiments/v060_xcheck_incremental.py` (IncOracle). The frozen
  `audit`/`x_score`/`x_volume`/`x_rule`/`summarize` from `experiments/v060_xcheck.py` are imported unchanged.
* `XCHECK_INCREMENTAL_008.json` / `_CHECKPOINT.jsonl`: all 288 breadth cases x {B5, BR6, BC6}, `--symmetry`, 4 workers,
  started 18:26:43 EDT, report written 18:31 EDT (310.4 s wall). `run.log` is the progress log.
* `EQUIVALENCE_46.json`: per-case/arm comparison with the 46 cases of the stopped frozen run.
* `QUERYLOG_DIFF.json`: query-by-query answers on 5 cases, frozen XRegion vs incremental (with and without symmetry).
* `TAMPER_CHECK.json`: 24 in-memory corruptions of sealed traces, all must be detected.
* `timing/`: delta-only (no symmetry) timing probe, see `timing/TIMING_NOTE.md`.

Wording: second encoding by the same author, no enumeration; not an independent audit.
