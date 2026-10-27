# BRUTE study-019 deviations (BRUTE-0170-SEQUENTIAL-MARGIN-019)

Numbering continues project-wide (study-018 ended at #100). Every entry here is written BEFORE the code it governs and
before the source freeze; no held-out seed (8510001-8550048) has been generated, simulated or inspected. Later
deviations go in `BRUTE_DEVIATIONS_019_ADDENDUM_<k>.md` (this file is ledger-hashed and is never edited).

## #101 Pre-code design disclosures (RGNB constraint, boundary, stickiness, alphabet3 worlds, reference method, streams)

Written after the seed check (`seedcheck_019`) and before `experiments/v0170_reference.py`, `brute/seqmargin.py`,
`brute/region3.py` and `brute/api/certify7.py` exist.

1. **RGNB constraint is implemented as written: one cardinality constraint per region build.** At step t the region is
   the frozen tolerant CNF (`brute.noisyregion.tolerant_region`, readings 0..t) with the single constraint
   sum(flips over readings 0..t) <= m(b_t). Earlier prefix constraints (sum over readings 0..t' <= m(b_t') for t' < t)
   are NOT added, although they are also implied by "no crossing" and would shrink the region. The plan text names
   only the current constraint; the prefix-constrained variant is a candidate for a later study. Label: Exact
   (definition); the coverage effect of the omitted prefix constraints is Open.
2. **Boundary.** `brute.seqmargin.boundary(B, eps_bar, delta)` returns m(0..B) by the plan's exact DP (fractions.Fraction
   of the decimal strings, as `m_rule`): keep the distribution of the running count restricted to paths that have not
   crossed; at bit b convolve with Bernoulli(eps_bar), raise m(b) from m(b-1) while crossed + P(count > m(b)) >
   delta*b/B, then move P(count > m(b)) into `crossed` and truncate. It reproduces the plan's B = 46 / 58 / 68 examples
   (computed before this entry; total crossing probabilities 0.008475 / 0.009704 / 0.008709). b_t = observed bits in
   readings 0..t (bit order: reading by reading, bit 0 before bit 1). A **crossing** is recorded per case (Exact) iff
   the running flip count exceeds m(b) at some observed bit b (per bit, not only at reading ends). Label: Exact.
3. **Stickiness (frozen semantics kept).** As in the frozen `NoisyRegionSpace`, 'grammar_contradicted' (region empty)
   and 'budget_exhausted' are sticky: once the region at some step is empty, every later support is None. Because m(b)
   grows, an RGNB region that is empty at step t could become non-empty later; RGNB keeps it closed (certifies nothing
   for the rest of the case). Without a crossing and with n* <= 4 the region is never empty, so this only removes
   certificates and cannot add a false one. The second implementation applies the same rule. Label: Exact (definition).
4. **Arms in the main block.** SP8 and RG4 as study-018 (frozen `rg_arm`, SP8 passthrough). RGN4 = frozen
   `noisy_supports` with m = m_rule(B). RGNB4 = sequential margin with m(.) = boundary(B). RGNB4_0 = the same code with
   the boundary forced to 0 at every bit (the CNF is then identical to RGN4_0 of study-018; Exact). RGN4_or = frozen
   `noisy_supports` with m = realized flips; it shares the RGN4 supports when flips == m and the RGNB4_0 supports when
   flips == 0 (same CNF; recorded as `shared_with`). Main trajectory: the frozen SP8 trajectory on the noisy world as
   study-018, with the flip array `default_rng([seed, round(1000*eps), 19]).random((45, 2)) < eps` (row 0 = initial
   reading; only unmasked bits are flipped). Label: Exact (definition).
5. **rand4a3 worlds (alphabet3 block).** Generator (new, in `experiments/brute_study_019.py`): rng =
   `default_rng([seed, 19, 1])`; draw a 4-state, 3-action transition table and a 4-code output table uniformly
   (start state 0); reject and redraw unless the machine is strongly connected and minimal (Moore partition
   refinement). Every accepted world therefore has **exactly** 4 states (n* = 4 <= FB, Exact by generator); the plan's
   "n* <= 4" is satisfied at its edge. Mask: bit j of reading r is masked iff `default_rng([seed, 19, 2]).random((45,
   2))[r, j] < 0.35` (the frozen two-action worlds' mask code is family-specific and is not reused). Actions:
   `default_rng([seed, 19, 3]).integers(0, 3, 44)`. Flips: the main-block flip array (item 4) on unmasked bits. Truth per
   (step, action b): the latent code of the state reached by b. Label: Exact (definition).
6. **brute/region3.py is a thin layer.** The frozen `RegionK` and `RegionSpace` already take k (number of actions); no
   new CNF is written. `region3` provides `supports_k` (supports for every action 0..k-1 before the next reading,
   unknown counts as in `region_supports`), `rg3_supports` (frozen `RegionSpace(4, k=3)` on the noisy readings, hard
   clauses = noise-unaware) and `rg3_decide` (singleton after burn-in, no SP8 passthrough). RG4_3 uses it; RGN4_3 is
   the frozen `NoisyRegionSpace(4, m_rule(B), k=3)`; RGNB4_3 is the sequential margin with k = 3. C3 = certificates /
   132. Label: Exact (definition).
7. **Second implementation method.** Two-action cases: the study-018 full-table enumeration (4**8 tables, start state
   0, per-state mismatch counts). Three-action cases: canonical partial-machine enumeration (states numbered by first
   visit; an undefined transition branches to every used state or one new state while fewer than 4 are used), with
   per-state mismatch counts, pruned when the least cost (sum over states of the cheapest code) exceeds the largest m
   any arm uses on the case at any step. Costs never decrease along the trajectory, so pruning drops no machine that
   any audited support needs (Exact). At prediction time an undefined transition may go to any used state or to a new
   state (cost = current least cost). Sticky emptiness as item 3. The reference test checks that both methods agree
   on two-action smoke cases. Label: Exact (method); same author, NOT independent.
8. **Streams and blocks.** Stream `transfer` = 360 main + 120 stress + 96 alphabet3 cases (one checkpoint); stream
   `repro` = block `reproset` (main run index % 3 == 0, then alphabet3 run index % 3 == 0); `gti` and `g11`
   (reference audit of every transfer case + mutation test) as study-018. Budgets by `scripts/rate_math_019.py`.
9. **G_recount and G10 "as study-018"** extend to the alphabet3 arms (132 slots) and to RGNB4 / RGNB4_0. GNB (b) and
   GA3 CP95 use the study-018 exact one-sided Clopper-Pearson by bisection (#99). GNB (c) and (d) use the
   seed-clustered paired bootstrap of the plan (seed 20261030, 2000 resamples; clusters = seeds at eps 0.02).
10. **D100 fix.** The new TEST_SUITE writer (`scripts/run_tests_0170.py`) parses `git status --porcelain` lines by
    taking the path after the two status characters and the separating space (`line[3:]`, robust to a leading space)
    instead of stripping first. Label: Exact.
