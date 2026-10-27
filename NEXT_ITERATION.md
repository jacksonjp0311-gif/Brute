# Brute v0.15.0 → v0.16.0: next iteration (pre-registered as BRUTE_PLAN_018 on `plan/v0.16.0`)

The previous note is in `docs/research/v0.15.0/NEXT_ITERATION_FROM_v0.14.0.md`. Labels are as in the README. Nothing here counts as evidence until it runs on fresh seeds. The longer path is in `docs/ROADMAP_TO_GI.md`.

## Where v0.15.0 leaves things (Observed, study-017, 9 of 13 gated pass)

- **Bounded-region lookahead before the first certificate works.** RGLX4 0 false in 13,755, TV +2.84 [2.21, 3.46] steps over RG4, positive in every family (GRL PASS).
- **The deferred-split coverage gain replicates** (GDS2: dC +0.037 [0.030, 0.043]).
- **The attested license is RG4** (DLFa = RG4 everywhere), as deviation #85 predicted (Exact).
- **The audit ran out of budget** (GS_ref5 FAIL: 308/432, 0 mismatches, 124 not reached) because the rate math under-projected the per-case cost by 1.72x.
- **GTI failed on the #96 stale literal only; G_HB failed on two gaps** that ended when the operator next acted.

## Breadth or depth (decision recorded in BRUTE_PLAN_018 `breadth_decision`)

Brute's guarantees so far hold only for noiseless 2-bit readings in deterministic worlds. Depth along the same axis (bigger lookahead, more chooser variants) now gives diminishing, already-measured gains; the largest unmeasured risk to the soundness claim is that any real sensor is noisy. So v0.16.0 goes **breadth: noisy observations**. iid bit flips at eps ∈ {0, 0.01, 0.02}, attested bound eps_bar 0.02, and a tolerant region RGN4(m) that allows up to m flips with P(Bin(B, eps_bar) > m) ≤ δ = 0.01. Larger alphabets are deferred to v0.17.0. (*Inferred*, decision.)

## Fixes carried into BRUTE_PLAN_018

1. **g11 rate projection (stop_rule.g11_rate_projection).**
   - Measure the audit cost on smoke seeds in every family × mask cell (≥ 2 cases per cell, plus stress), under the same concurrency as the run.
   - Project the wall time from each cell's slowest smoke case, × 1.75.
   - If the projection exceeds 0.8 of the budget, change the budget, workers (≤ 8) or start time BEFORE the source freeze. Never cut the sample.
   - `scripts/rate_math_018.py` exits non-zero on any overrun and is part of the freeze.
   - g11 writes a PROGRESS ETA every 60 s as a warning only; no mid-run change is allowed.
   - The same rule applies to gti (study-017 used 0.962 of its budget).
2. **Operator waits.** Poll live processes with short blocking checks (≤ 240 s) during the run. Both study-017 gaps ended within about 1 s of the operator's next action after a long idle wait. During the release, a 240 s idle wait advanced the box clock by only 23 s (*Observed*; cause *Open*). G_HB is unchanged.
3. **Declare K_0150 and K_096** in advance in GTI.

## No CI

Brute uses no GitHub Actions and has no `.github` directory. None will be added.

Deferred and still **Open**: larger alphabets, correlated or adversarial noise, stochastic dynamics, content-level transfer and independent audit.

Nothing here shows general intelligence.
