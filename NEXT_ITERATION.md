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

1. **Make `ConstraintRegion` the production backend, gated on continued exactness.** Route support, margin,
   saturation and fibre queries through it; keep enumeration as the frozen reference and gate decision identity again
   (GR1-style on study-004..006 traces, plus the new study wherever n ≤ 5 enumeration is still feasible). SAT unknowns
   become ABSTAIN with a reason, never a certificate, and their rate is reported. Use incremental solving (assumptions,
   no rebuild per step) to bound time; GR2 shows SAT time is the noisy part, not size.
2. **Scale breadth as pre-registered families.** More states (n = 5–8 family, n + 1 margin), more than 2 sensors and
   more than 2 actions, each family and its generator pre-registered before its data, as perm4 was. These are the
   regimes enumeration cannot reach (GR2: 10 of 84 cases exhausted 160,000 rows at n = 6), so they test the
   representation, not just reuse it.
3. **Replace the experiment policy with region-volume / model-count selection.** Score each action by the expected
   reduction of the region (exact #SAT or approximate counting, or projection cuts on the next-reading coordinates)
   computed on the fibre-robust region, aimed at recovering G6b′ coverage (A4 − A2 −0.104) **without** breaking
   G1/G2/G3′. Caveat from the data: deeper certification-count lookahead (D2) *lowered* coverage (−0.071), so a
   counting policy is a different hypothesis, not "more depth"; gate it against A4 and A2 with the G6b′ rule unchanged.
4. **Fix the F2 unsoundness** (treat an unknown edge at any step of the multi-step fibre as any reading) before any
   multi-step fibre returns as a candidate.
5. Secondary: an exercised resume (0 certificates after resume in v0.4.0); D7/D8 at a larger N or closed as OPEN;
   a third-party replication of GATES.json.

Deferred from v0.4.0 and still **Open**: learner on the representation; n ≥ 6 certification; bounded-time SAT at
n ≥ 8; effective resume; the cause of D2's lower coverage; independent audit.
