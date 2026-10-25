# Brute v0.5.0: next iteration (proposal, not pre-registered)

Earlier notes are kept at `docs/research/v0.4.0/NEXT_ITERATION.md`, `docs/research/v0.3.0/`, `docs/research/v0.2.0/` and
`docs/research/v0.1.0/`. Labels are the same as in the README.

## Where v0.4.0 leaves things (Observed, study-006)

- **Soundness holds on new seeds and a new family.** 0 false certificates in family (A4 2,686 taken + 736
  counterfactual), 0 on ood5, drift4 13 false all at drift steps with 0 stale (G1, G2, G3′); perm4 0 false.
- **The coverage price is unchanged.** A4 − A2 = −0.104 [−0.116, −0.092] (G6b′ fails, pre-registered); A4 = A3 exactly.
- **Depth did not buy coverage back.** D2 (two-step lookahead) −0.071 vs A2 and sound; F2 (two-step fibre) −0.033 but
  unsound (2 non-drift, 2 stale false certificates on drift4).
- **The geometric representation is exact.** `ConstraintRegion` (CNF over complete ≤n Moore machines, symmetry-broken)
  agrees with enumeration on 778,840 + 470,318 items. Size grows ~n^1.6 (clauses) vs ~n^8.5 (rows); SAT time is noisy
  and has budget unknowns at n ≥ 8 (17 steps). **The learner does not use it.**
- **Alarm.** τ6 = 1.645: G5 passes (ood4 1/72, perm4 2/72; the v0.3.0 τ gives perm4 14/72). Detection drops (ood5 25
  vs 40 cases). Resume happened 3 times per arm and produced 0 certificates.
- **D7 = D8 is OPEN at N = 384** (R = 0.63 [0.42, 0.91]).

## Recommendation for v0.5.0 (Inferred; to be pre-registered before any v0.5.0 code)

1. **Make the representation the engine (priority).** Route the learner's support, margin, saturation and fibre
   queries through `ConstraintRegion` behind a switch, with enumeration kept as the frozen reference; gate exact
   decision identity on study-004..006 traces (as GR1) and then raise the margin to n ≤ 6 and the family to n ≤ 5,
   which enumeration cannot reach (GR2: 10 of 84 cases exhausted the 160,000-row budget at n = 6). Handle SAT unknowns as ABSTAIN with
   a reason (never as a certificate) and report the unknown rate. Consider incremental solving (assumptions, no
   rebuild per step) and a BDD/d-DNNF compilation for counting-based lookahead.
2. **Fix the F2 unsoundness before any coverage claim.** The two-step fibre must treat an unknown edge on any of the
   steps as any reading (as Y1k does for one step); re-test against G3′ on the sealed drift4 seeds as a design probe.
3. **Coverage: understand the price, do not tune around it.** A pre-registered decomposition of A2's extra coverage
   into fibre-ambiguous vs genuinely-unknown predictions (the RESYNC_AMBIGUOUS count is the measurable part).
4. **Resume that can recover.** A resume rule that is exercised: measure post-alarm coverage on in-family cases with
   injected transient noise, pre-registered.
5. **D7/D8 at a sharper N.** CI width ~0.49 at N = 384; the power analysis method of plan 006 should be rerun with the
   observed R to choose N (or accept OPEN and close the question).
6. **Breadth.** One stochastic family (credal region) or a 3-action alphabet, pre-registered before seeing data.
7. **Independence.** A third-party replication of GATES.json from the sealed traces.

Deferred from v0.4.0 and still **Open**: learner on the representation; n ≥ 6 certification; bounded-time SAT at
n ≥ 8; effective resume; the cause of D2's lower coverage; independent audit.
