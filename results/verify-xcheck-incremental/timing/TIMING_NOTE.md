# Timing probe: incremental harness WITHOUT symmetry breaking (delta-only)

Command: `experiments.v060_xcheck_incremental --cases 681,648,650,683 --workers 4` (no `--symmetry`), started 18:18 EDT 2026-10-25.

| case | family / mask | original wall (s, XCHECK_008_CHECKPOINT) | delta-only incremental (s) |
|---|---|---|---|
| 681 | big6 0.1 | 24.6 | 12.2 |
| 648 | big6 0.1 | 107.0 | 116.9 |
| 650 | big6 0.6 | 1153.4 | 913.7 |
| 683 | big6 0.6 | 18151.3 | not finished after ~17.5 min; killed 18:38 EDT |

Observed: caching the encoding and adding only the per-step delta gives roughly 0.8x-2x. Per-query profiling of case 648 / B5
(delta-only) put ~98% of solver time in UNSAT answers (y1k UNSAT 45.6 s, margin support UNSAT 44.0 s, support UNSAT 21.2 s
of ~118 s); re-encoding cost was negligible. With first-visit symmetry breaking (`--symmetry`) the same arm took 2.4 s.
The full 288-case re-run therefore uses `--symmetry`. Wall times are informational (machine load varied).
