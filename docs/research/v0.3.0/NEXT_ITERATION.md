# Brute v0.3.0: next iteration (proposal, not pre-registered)

The v0.2.0 note is kept at `docs/research/v0.2.0/NEXT_ITERATION.md` (v0.1.0's at `docs/research/v0.1.0/`). Labels are the
same as in the README.

## Where v0.2.0 leaves things (Observed, study-004)

- **Active cuts work.** Dual coverage gain +0.115 pooled (CI [0.104, 0.127]), with 0 false certificates in family and on
  ood5, and in-family log-loss lower than v0.1.1 in every family.
- **The only errors are stale certificates after an unannounced change.** drift4 A: 24 wrong, 21 at drift steps and
  **3 one step later** (G3′ failed). Passive P: 1 wrong.
- **The policy exploits.** On-policy coverage ≈ 2 × dual coverage; certificates for the untaken action fall.
- **The window rebuild clears suffix-1 on drift** (P − suffix-1 CI upper −0.0006) but is not distinguishable from v0.1.1.
- **Budget:** peak 103,814 of 160,000 rows; one-step lookahead fits, deeper lookahead or n≤6 would not (*Inferred*).

## Recommendation for v0.3.0

1. **Change-point-aware certification (primary; targets G3′).** After any residual alarm, family contradiction, or
   window restart, withhold CERTIFIED for k steps, *or* require the certificate to survive a "recent change" margin: the
   n≤4 region rebuilt from only the last w observations must project to the same point. Pre-register k/w on design
   seeds (study-004 seeds are now design data), gate G3′ unchanged, and gate the coverage cost against v0.2.0 A.
   *Inferred:* the 3 step-13 errors are exactly the ones a w-window agreement test can catch; the 21 drift-step errors
   cannot be caught by any causal learner.
2. **Exploration that values the untaken branch.** Score actions by certifiable-pair gain over both actions, or a
   two-step lookahead restricted to the margin-disagreeing rows, and gate dual (not on-policy) coverage. Measure the
   row cost first (D10).
3. **Representation study (measure, do not ship).** Compare enumeration against a partition-refinement (Myhill–Nerode
   style) or SAT/model-counting projection on the study-004 traces: same decisions, fewer rows. This is the gate for
   n≤6 and R4.
4. **Keep the discipline:** new seed blocks, criteria frozen before code, v0.2.0 A and P as control arms, independent
   reference, byte reproducibility, failures kept on the record.

## Not recommended

- Loosening the margin gate or ε to raise coverage. *Rejected* (study-003 witness audit: every margin abstention is real).
- Encoding the drift generator's period. *Rejected* as leakage.
