# v0.5.0 design probe (before BRUTE_PLAN_007) — Observed, informational

Run 2026-10-25 ~05:30 EDT on the box (8 CPUs), with the FROZEN v0.4.0 `brute/geometry.py` (per-step rebuild of
ConstraintRegion, exact, no conflict budget) on sealed study-006 seeds only (perm4 1600001-1600002; the ood5 generator
called with the same two seed numbers). No study-007 seed was generated. Wall-clock seconds per 44-step case
(core queries + LU-R lookahead for both actions at every step):

| family bound / margin | perm4 (0.1, 0.6 masks) | ood5 world |
| --- | --- | --- |
| <=4 / <=5 (rate 0.35) | 0.27, 0.31 | 0.10, 0.16 |
| <=6 / <=7 | 0.97-4.99 (max step 0.44) | 0.71-8.47 (max step 1.26) |
| <=7 / <=8 | 1.58-7.33 (max step 0.78) | 1.22-10.29 (max step 2.23) |

cycle3 at <=4/<=5: 0.41, 0.65 s. Use: sizing study-007 (breadth n<=6 with lookahead is affordable; per-step rebuild is
kept, cross-step incremental solving is left Open).
