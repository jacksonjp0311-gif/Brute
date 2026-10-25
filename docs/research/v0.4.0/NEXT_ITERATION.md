# Brute v0.4.0: next iteration (proposal, not pre-registered)

Earlier notes are kept at `docs/research/v0.3.0/NEXT_ITERATION.md`, `docs/research/v0.2.0/` and `docs/research/v0.1.0/`.
Labels are the same as in the README.

## Where v0.3.0 leaves things (Observed, study-005)

- **Stale certificates are fixed on the gated block.** Certifying on the fibre over the latest observation (Y1k) gives
  0 non-drift and 0 stale false certificates on drift4 (G3′ passes); 0 false certificates in family and on ood5.
- **At a price.** Dual coverage A3 0.121 against v0.2.0's 0.220 (−0.098, G6b fails as pre-registered); still +0.064
  over its own passive arm (G6).
- **Not perfect beyond the gated block.** Extended drift4: 4 stale false certificates (v0.2.0: 15) — jumps into states
  whose edge is still unknown.
- **The D7 = D8 hypothesis is OPEN** (forced checks restored counterfactual knowledge but not safety; the certificate
  geometry did the work).
- **The τ alarm misfires on 5 of 72 held-out ood4 cases** (G5 fails; same in v0.1.1), and certification never
  resumes after an alarm.

## Recommendation for v0.4.0: toward a general geometric reasoner

The aim is a reasoner whose core operations are geometric (a region, its projections and fibres, cuts that shrink
them) and that scales beyond enumeration and beyond one toy domain. Three tracks, one study:

1. **Depth: re-certification through a multi-step fibre (primary; targets G6b).** Replace the one-observation fibre
   with the fibre over the last w observations, shrinking as consistent evidence accumulates, and make the lookahead
   two steps deep on the fibre (score the pair of actions that most shrinks it). Gate: G3′ unchanged, stale = 0 on the
   extended block, and coverage non-inferior to v0.2.0 within −0.03. *Inferred:* D12's gap is mostly fibre points that
   later evidence rules out.
2. **Representation beyond enumeration (enabling).** Represent the region as a partition-refinement / quotient
   automaton or a SAT/BDD encoding with projection and fibre queries, verified to give identical decisions to
   enumeration on the sealed study-004/005 traces before any new study (an exactness gate, not a coverage gate). This
   is the gate for n≤6, two-step lookahead within budget, and larger alphabets.
3. **Breadth (first step).** Add one new domain family with a different geometry (e.g. 3 actions × 3-bit sensors, or
   stochastic emissions with a credal region) to the held-out set, with its own soundness gate, so that no claim rests
   on one toy domain. Keep the language adapter template-only until the core generalises.
4. **Fix the alarm (hygiene).** Pre-register a recalibrated τ on new calibration seeds that bounds the held-out tail,
   and a rule for resuming certification after an alarm once the region re-collapses.
5. **Keep the discipline:** new seed blocks, criteria frozen before code, v0.3.0 A3/P3 and v0.2.0 A2 as control arms,
   independent reference, byte-identical reproducibility, failures reported as failures.
