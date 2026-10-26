# Downgrade-mechanism diagnostic (EXPLORATORY, seen study-011 data) — input to BRUTE_PLAN_012

Script: `scripts/diag_downgrade_012.py` → `results/diag-012/DOWNGRADE_DIAG_SEEN.json`. Run before the plan was
written. Every number is **Observed on seen seeds** (study-011 held-out seeds, already scored); none is a gate.

## Part A — recorded traces (6,866 SP8 certificates, J9 paired at the same case/step/action; actions identical)
* J9 downgraded 5,840 SP8 certificates; 5,786 of them were TRUE (99.1%). 5,025 of the 5,786 are in stationary
  in-family worlds where no drift ever happens (cycle3 1,151, switch3 1,190, unaliased2 1,108, unstructured3 1,094,
  perm4 491, ood4 195). The coverage cost is paid where drift is impossible.
* SP8's 18 non-drift false certificates: all 18 were downgraded by J9 (Exact on these traces). At all 18 the
  stationary family region was still supported, no event trigger fired in the window, and the window surprise was
  small (max ≤ 0.08 in 14/18).
* **Surprise gate — Rejected (Observed).** "Apply the hull only if some window surprise > θ": at every θ in
  {0.02 … 0.82}, recovering ≥ 4,996 true certificates also keeps ≥ 14 of the 18 non-drift false certificates.
  Family-contradiction and event-trigger gates separate nothing (all 18 false and 5,771/5,786 true look alike).

## Part B — instrumented J9 re-run on the same 792 cases (one decision per case/step/action)
| keep-rule on SP8's kept certificates | kept | false non-drift | false at drift steps | false in-family |
|---|---|---|---|---|
| SP8 (no hull) | 6,866 | 18 | 44 | 0 |
| J9 = Y1kW, K=4 | 1,026 | 0 | 8 | 0 |
| **supW4 = exact jump-window support, K=4** | **1,308** | **0** | 9 | 0 |
| supW6 / supW8 | 1,286 / 1,276 | 0 / 0 | 8 / 8 | 0 |
| Y1kW6 / Y1kW8 | 930 / 850 | 0 / 0 | 7 / 7 | 0 |

* Which window position widens the hull: a single jump at lag 1 widens 10,932 of 11,036 downgrades' lag-1 checks;
  the lag-1 position alone explains 1,311 downgrades and is part of 5,780 of 5,840.
* Mechanism (Inferred): one free transition just before the last observation makes the current state any visited
  state compatible with the last mask, so the next code is ambiguous whenever the mask aliases states — and SP8's
  non-drift false certificates are exactly histories that a stationary machine and a one-jump machine both explain.
  No observable gate can keep the first and drop the second (indistinguishability); only a tighter but still sound
  hull can recover coverage.
* Design consequence for J10 (pre-registered in BRUTE_PLAN_012): replace the fibre hull Y1kW with the exact
  jump-window support projection supW4 (Observed +27.5% kept, 0 non-drift false on seen data). SP8-level coverage
  with J9-level drift safety is not reachable by this family of rules on seen data (Observed: best rule keeps 19% of
  SP8's certificates); the plan predicts J10 < SP8 on coverage and says so.
