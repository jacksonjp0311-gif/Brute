# Brute v0.2.0: next iteration (proposal, not pre-registered)

The v0.1.0 note is kept at `docs/research/v0.1.0/NEXT_ITERATION.md`. Labels are the same as in the README.

## Where v0.1.1 leaves things (Observed, study-003)

- **Safety holds.** There are 0 false certificates in family and on ood5. The only errors are 4 on drift4, all at
  perturbation steps, and each was withdrawn and falsified at the next observation.
- **Open-world forecasting is fixed for n≤5 worlds:** ood5 0.6245, down from 1.4808. On drift4 it only matches the
  suffix-1 baseline: 1.1556 against 1.1679, with a paired interval that includes 0. At mask 0.6 it is slightly worse
  than v0.1.0 (1.3713 against 1.3631).
- **Coverage is the main cost:**
  - in family 0.09–0.20, against 0.34–0.52 for v0.90;
  - ood4 0.006, against 0.581;
  - ood5 and drift4 0.001 and 0.006.
- **Every margin abstention is real.** Each of the 4,226 MARGIN_DISAGREES abstentions has a replay-verified n≤5 machine
  that predicts differently. Loosening the gate would be unsound.
- **The largest per-step loss is the contradiction step:** 126 steps at ln 200 = 5.298.

## Recommendation for v0.2.0

1. **Choose actions that disambiguate** (the primary coverage lever). The action sequence is fixed today. When the
   margin disagrees, choose the action whose next reading splits the surviving n≤4 and n≤5 explanations. Certification
   rules stay the same, so soundness carries over by construction (*Inferred*). Measure coverage against a fixed-action
   arm.
2. **Restart at a change point after contradiction** (drift4). When the margin is also contradicted (R5: 60 of 442
   drift4 margin steps were outside its support), rebuild the n≤4/n≤5 supports from a trailing window, with no known
   schedule. Encoding the generator's period of 11 stays *Rejected* as leakage. Target: drift4 log-loss below suffix-1
   with an interval that excludes 0. The first wrong certificate right after an unannounced change cannot be prevented
   by a causal learner (*Inferred*). G3′ stays the gate, and the target is fast withdrawal.
3. **Grow the family to n≤5 certification behind an n≤6 margin**, only if the cost of 1 fits the 160,000-row budget.
   The current peak is 102,806 margin rows, and n≤6 is likely to exceed it (*Inferred*). Measure before planning.
4. **Keep the discipline:**
   - pre-register study-004 on new seed blocks before any code;
   - keep τ fixed, or calibrate it only on in-family calibration seeds;
   - run v0.1.1 as the control arm;
   - keep the independent reference and byte reproducibility.

## Not recommended

- Raising ε to soften the contradiction step. *Rejected* in the v0.1.1 plan, R1.
- Mixing the margin forecast into the forecast before contradiction. *Rejected*, R2: Simulated gain, in-family cost.
