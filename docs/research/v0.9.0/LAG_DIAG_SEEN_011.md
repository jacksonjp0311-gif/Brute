# Lag diagnostic on seen data (v0.9.0 step 1)

**Label: Observed on SEEN data, exploratory.** The inputs are sealed studies 008, 009 and 010. They informed v0.6.0–v0.8.0 and are not v0.9.0 evidence. The v0.8.0 lesson applies: a seen-data replay found 9/9 for H_c, and fresh seeds then gave 2/7. This diagnostic was written and run on 2026-10-26 (EDT), before BRUTE_PLAN_011 and before any v0.9.0 learner code. Its only use is to fix the J9 window constant that the plan pre-registers.

- Script: `scripts/diag_lag_011.py`
- Output: `results/diag-011/LAG_DIAG_SEEN.json`
- Test: `tests/test_diag_lag_011.py`

## Definitions

- **lag** = step − d, where d is the last drift step (12, 23 or 34) strictly before the step. In drift4, the hidden state jumps on the transition into the observation of step d.
- **Non-drift** means step > 12 and step ∉ {12, 23, 34}, the same definition as G3′.
- A certificate with lag L was issued after L − 1 observations that followed the jumped observation.

## Result (taken and counterfactual action, all certifying arms, drift4)

| study / arm | non-drift false certificates | lags |
|---|---|---|
| 008 / R6 | 1 | 1 |
| 008 / C6 | 2 | 1, 1 |
| 009 / R6 | 4 | 1 ×4 |
| 009 / C6 | 5 | 1 ×5 |
| 009 / S7 | 4 | 1 ×4 |
| 009 / SC7 | 5 | 1 ×5 |
| 010 / SC7 | 4 | 1, 2, 2, 4 |
| 010 / SP8 | 3 | 1, 2, 4 |
| **total** | **28** (all on the taken action; 12 distinct events) | **1: 23 (82.1%), 2: 3, 4: 2** |

- **Lag coverage.** Cumulatively, lag ≤ 1 is 82.1%, lag ≤ 2 is 92.9% and lag ≤ 4 is 100%. No lag of 3 or ≥ 5 occurs.
- **Rule.** 21 certificates came from `Y1k`, 5 from `tracked-calm` and 2 from `Y1k-recent`. The `tracked-calm` and `Y1k-recent` ones are all from 010.
- **Events.** No recorded event fired between d and the step in any of the 28 (28/28 arms record events). The jumped observation was never surprising enough to trigger anything.
- **Region exit (proxy).** For all 28, the no-jump family region was first contradicted after the certificate: 28 after, 0 before, 0 never. The proxy is `diagnostics.contradiction_step`. The drifted world is not a fixed machine, so "left the region" can only be read through contradiction. So every false certificate was issued while the region was still consistent with the data, as expected for a silent jump.
- **Drift-step false certificates** (step ∈ {12, 23, 34}): 142, reported and not gated. These are excluded by the G3′ definition.

## What this fixes for v0.9.0 (Inferred)

1. **Most failures are lag 1.** 82% of seen non-drift false certificates are lag-1: the jump went into the last observation before the forecast. A hull sound against that jump is the J8 hull, and J8 had 0 coverage (Observed, study-010). Inferred: under a model class that allows a silent jump at the last transition, a certifier that is sound against it is nearly vacuous. Lag-1 failures are therefore treated as irreducible for v0.9.0 and reported, not gated at zero.
2. **J9 window K = 4.** Lags 2–4 cover the remaining 17.9%, which is 100% of the seen lag ≥ 2 cases. So J9 tolerates one jump into an observation T−K+1 … T−1 with K = 4 (lags 2, 3, 4), where T is the last observation before the forecast.
3. **A surprise-triggered hull would be pointless.** No jump triggered an event, so a hull that fires only after a surprise would never fire. J9 applies its window hull to every certificate that SP8 would keep.
4. **Power is low.** Fresh lag ≥ 2 events were rare on seen data: 5 certificates from 3 events, all in study-010. A G3L PASS could happen by chance, so the plan must report the SP8 comparator count next to it.
