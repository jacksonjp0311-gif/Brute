# Brute v0.6.0: next iteration (proposal, not pre-registered)

Earlier notes are kept at `docs/research/v0.5.0/NEXT_ITERATION_FROM_v0.4.0.md`, `docs/research/v0.4.0/`,
`docs/research/v0.3.0/`, `docs/research/v0.2.0/` and `docs/research/v0.1.0/`. Labels are the same as in the README.

## Where v0.5.0 leaves things (Observed, study-007)

- **The constraint region is the engine and changes no decision.** A5 = A4 on 25,344 steps (GX1); 0 solver UNKNOWNs in
  production; budget exhaustion abstains (GX3, 257 of 257).
- **Breadth is sound.** big6 / sens3 / act3: 0 false certificates; ood6s3 0 of 1,271; experiments beat passive by
  +0.045. Exactness there is checked only as far as enumeration reaches (GX2 fails on act3: 84.5% < 90%, 0 mismatches).
- **The volume tie-break M helps coverage but is not shown safe.** +0.026 (2x2), +0.039 (breadth); 1 non-drift false
  certificate on drift4 (G3′ fails for M5) → GM NOT DISTINGUISHED.
- **The coverage price stays.** M5 − A2 −0.080 (G6b fails, third release in a row); the rule, not the policy, holds it.
- **Scaling.** Clauses 2.3k → 15k (n = 4 → 12), 0 UNKNOWN; time noisy, non-monotone; 5 bounds × 6 cases.

## Recommendation for v0.6.0 (Inferred; pre-register before any v0.6.0 code)

1. **A drift-aware certification rule (target G6b and G3′ together).** Replace "constant on the whole fibre over the
   latest observation" by "constant on the fibre over the evidence since the last step at which a jump is still
   consistent", computed on the region (a projection with a time cut), with a frozen counterfactual check that every
   A2 certificate it admits survives drift4. Gate: G1/G2/G3′ unchanged, G6b unchanged thresholds. Prediction to register:
   recovers part of the −0.08; whether it can be sound at all is the question (F2 in v0.4.0 was not).
2. **An exactness reference that reaches breadth.** A second, independent encoding (different variable layout, e.g.
   transition-function bits without symmetry breaking, or a BDD) checked against `RegionK` on every step of big6 and
   act3, so GX2-style exactness no longer depends on enumeration's row budget. Keep enumeration where it fits.
3. **M on probation, with the soundness question powered.** Re-run M only with a pre-registered drift block large
   enough to estimate its non-drift false-certificate rate against A5 (one event is not a rate), plus its interaction
   with rule 1.
4. **Model counting, incremental SAT.** Approximate #SAT (or exact projected counting on the reading coordinates) for M,
   and assumption-based incremental solving to cut per-step rebuild time; report timing with repeated runs and
   quantiles, not single wall clocks.
5. **Process.** Recompute breadth-arm probabilities in the second implementation (2x2 only so far); smoke seeds checked
   by code **before** the first run; a third-party replication of `GATES.json` from a fresh clone.

Deferred and still **Open**: stochastic worlds (credal regions); effective resume (2 resumes in study-007); D7/D8;
learned family selection; grounding beyond templates; independent audit.
