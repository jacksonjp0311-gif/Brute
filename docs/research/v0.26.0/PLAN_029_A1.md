# BRUTE_PLAN_029 amendment A1: S4 on the S1 lineage

Published 2026-10-30, before any study-029 data. The frozen `experiments/BRUTE_PLAN_029.json` (c06bcfe) is not edited.
Authorization: James's STANDING GO (t133s553, ledger 76b30d5); ledger build_authorization_029 (78336bd).

## Why (Observed, studies 027 and 028)
At 8 and 12 states the original S1 search beat S2 and S3. At 12 states S1 got X 3/12 and U 0.158; S3 got X 0/12 and U 0.398.
Building S4 on S3 builds on the losing lineage. So S4 is now S1 plus the throughput ideas, and the headline compares S4 with S1.

## Scratch diagnosis: what in S2/S3 costs more than S1? (Observed, scratch, 3 smoke seeds per family)
Artifact: `results/diag-029/S1_COST_029.json` (`scripts/diag_029.py`, 86856da / ledger 4701cc4).
The earlier check bd587ab ablated S2 internals only. It never compared S2 or S3 with S1.

**Mechanism: the symmetry-breaking clauses.** S2/S3's BFS-canonical clauses (auxiliaries t, p, mm, O(n³k) clauses) slow
the SAT witness solves that answer support queries.

U counts per run (seeds 9590001-003):

| variant | 8 states | 12 states |
|---|---|---|
| S1 | 0, 0, 0 | 20, 54, 174 |
| S1 without first-visit symmetry | 0, 0, 0 | 0, 0, 61 |
| S2 | 2, 4, 74 | 134, 227, 229 |
| S2 without BFS-canonical clauses | 0, 0, 0 | 0, 97, 164 |
| S2 fresh solver per step | 0, 0, 0 | 136, 160, 249 |
| S2 glucose 3 | 0, 50, 60 | 124, 227, 229 |
| S2 without distinguishability | 0, 0, 2 | 130, 247, 255 |
| S3 | 0, 81, 2 | 130, 224, 231 |

What did not matter much:
- **Lower-bound (UNSAT) proofs** were few and cheap. S1 had none, because at a 16-state bound every code stays possible.
- **The support chain** was cheap.
- **A fresh solver per step** helped at 8 states only.

## Effective design
- **S4** (`brute/scalesearch4.py`) is the frozen S1 RegionK encoding plus:
  - one lazily built solver per step;
  - witness reuse: a pool of concrete machines, re-simulated on each reading;
  - several queries decided in one solve (an OR over the codes not yet witnessed);
  - S3's hard 10 s per-query cap via conflict chunks, with S1's 100000-conflict budget kept.
- **Solver** (g3 or m22) is chosen on smoke seeds before the freeze. Deviation #130.
- **Other arms:**
  - S4_nowit: the ablation;
  - S4_nosym: secondary and descriptive; it tests the diagnosis;
  - S1: baseline;
  - S3: frozen control.
- S2 is dropped from the run to save runtime.

## Effective gates
- **GSC4:**
  - a: 0 mismatches against S1, S3 and the truth;
  - b: mean U(S4) − U(S1) at 12 states ≤ −0.08, with the bootstrap CI upper end < 0;
  - c: X(S4, 12 states) ≥ 5/12;
  - d: F(S4) = 0.
- **GTP:** taking the TP ratio S4/S1 per seed at 12 states, the median ratio is ≥ 2 and the CI lower end is > 1.5.
- **Unchanged in substance:** GQB, G10, GAPI14, GS_ref, GTI (including the sealed-smoke gates test), G_PROC, G_RT ≤ 1800 s and G_recount.
