# LR_LEMMA_023: the likelihood-ratio anytime region (RGL4)

Study BRUTE-0200-LR-ANYTIME-023. Written after the plan freeze (`preregistration_023`) and the build authorisation
(`build_authorization_023`), and BEFORE `brute/lrregion.py`, `brute/api/certify9.py` and the study runner existed.
Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

## Definitions
- **Noise and threshold constants.** eps_bar = 0.02, so r = eps_bar/(1 - eps_bar) = 1/49. δ_L = 0.005 is the budget for
  the likelihood-ratio part, and δ_a = 0.005 is the budget for the anytime part (frozen v0.19.0 boundary m_a with
  delta 0.005). Their sum is 0.01.
- **Hypothesis class.** H_n is the set of tuples (start state s in [n], transition table d: [n]x[2] -> [n], emission
  e: [n] -> {0..3}), so |H_n| = n · n^(2n) · 4^n, and H = H_1 ∪ ... ∪ H_4.
  - **Recount (gated, GLR_lemma).** `scripts/hn_recount_023.py` takes the one-hot groups of the frozen
    `brute.region.RegionK(n, 2, 4, ...)` encoding: x[0] is the start state (n values), there are 2n d[q][a] groups
    (n values each), and n e[q] groups (4 values each). The product of the group sizes is |H_n| = {1: 4, 2: 512,
    3: 139968, 4: 67108864}.
- **Prior.** π(g) = 1/(4|H_n|) for g in H_n, so Σ_g π(g) = 1.
- **Flip count.** f_g(b) is the number of observed (unmasked) bits among the first b observed bits, along the actual
  action history, whose reading differs from g's predicted bit. F(b) is the true number of flips.
- **Threshold offset.** D_n is the least integer D with 49^D ≥ 4|H_n|/δ_L. This is computed in exact integers as
  49^D · 1000 ≥ 4 · |H_n| · 1000 / 5, giving D = {1: 3, 2: 4, 3: 5, 4: 7}. This is recomputed by the reference, gated.

## Lemma (Exact)
Assume the noise is iid Bernoulli(e) with e ≤ eps_bar, independent of the actions and of the mask.

1. **Supermartingale.** E(b) = Σ_g π(g) · r^(f_g(b) − F(b)) is a nonnegative supermartingale over observed bits,
   with E(0) = 1.
   - On a bit where g predicts the true latent bit, f_g and F move together, so the ratio is 1.
   - On a bit where g predicts the other value, f_g − F rises by 1 with probability 1 − e and falls by 1 with
     probability e. The expected ratio is (1 − e)/49 + 49e ≤ 1 for e ≤ 1/50.
   - The actions and the mask may depend on past readings. They are predictable, and the noise is independent of them,
     so the supermartingale holds for adaptive policies.
2. **Ville's inequality.** P(sup_b E(b) ≥ 1/δ_L) ≤ δ_L.
3. **Elimination.** Suppose a model h is removed at bit b because f_h(b) ≥ w + D_n, where some g in H_n has
   f_g(b) ≤ w. If h is the true world h* (so f_h = F), then E(b) ≥ π(g) · 49^(F − f_g) ≥ π(g) · 49^(D_n) ≥ 1/δ_L.
   Therefore P(h* is ever removed by T_L) ≤ δ_L.
   - The true world only needs a representative in RegionK(4). That holds when n* ≤ 4, and every machine has a
     canonical representative with identical predictions.
4. **Union bound.** The anytime event (F ever exceeds m_a(b; 0.02, 0.005)) has probability < 0.005 (ANYTIME_LEMMA_021,
   statement 4). So P(h* ever leaves the RGL4 region) ≤ 0.01.
   - On the complement of both events, every singleton support is the latent code, so every certificate is correct.
     This is the v0.17.0 conditional soundness, with the bound T(b) in place of m(b).
5. **Witnesses only.** Only exhibited witnesses (feasible SAT answers) lower T_L. An UNSAT or UNKNOWN answer never
   lowers anything, so soundness does not rest on UNSAT claims.
6. **Horizon-free.** T depends only on the readings so far, eps_bar and δ. No planned length B is read.

## Exact per-step rule (implementation spec; written before code)
At step i (the support for action i is computed from readings 0..i−1), let b be the number of observed bits in readings
0..i−1.

1. Set cap = m_a(b; 0.02, 0.005).
2. For n = 1, 2, 3, 4 in that order, starting from m = s_n (s_n = 0 at the start of a case and carried between steps):
   - While m + D_n − 1 < cap, ask the frozen `brute.noisyregion.tolerant_region(n, readings, actions, m)` whether it is
     feasible.
     - If True: record the witness (w_n = m, plus the decoded machine: start 0, d, e), set cap = m + D_n − 1, and stop
       searching this n.
     - If False or UNKNOWN: increase m by 1. Each UNKNOWN is counted in `witness_unknowns`.
   - Then set s_n = m.
3. T(b) = cap. Equivalently, T = min(m_a(b), min over the witnesses found at this step of (w_n + D_n − 1)).
4. `attain` is the n of the last witness found at this step, or None if T = m_a.
5. The region is the frozen tolerant region with n = 4 and m_bound = T(b), built on readings 0..i−1. The supports,
   sticky contradiction and budget exhaustion are those of `brute.noisyregion.NoisyRegionSpace`.

**Properties of the rule (Exact).**
- **Monotone.** T is non-decreasing in i, because s_n never decreases and m_a is non-decreasing.
- **Equal to the full rule when there are no UNKNOWNs.** A feasibility search that is not capped would give
  T = min(m_a, min_n (fmin_n + D_n) − 1), where fmin_n is the exact minimum flip count over H_n. The capped search gives
  the same T whenever `witness_unknowns` is 0 up to step i, because s_n ≤ fmin_n(i).
- **Disclosed as #108.** The cap only skips witness searches that cannot lower T. This implementation detail is
  disclosed as deviation #108. The plan text says "smallest w found by feasibility search; any witness is valid".
- **Stronger reference than the plan requires.** The numpy reference (`experiments/v0200_reference.py`) computes fmin_n
  for every n ≤ 4 by exhaustive enumeration of transition tables with start state 0. Per-state optimal emissions give
  the minimum flip count. The plan requires this only for n ≤ 3 plus a witness recheck for n = 4.
  - It checks T exactly on every step with cumulative witness_unknowns = 0. Otherwise it checks T ≥ T_ref.
  - It re-simulates every recorded witness and checks its flips ≤ w.
  - It recomputes the RGL4 supports from the frozen full-table costs at the recorded T, and recomputes the certificates.

## Expectations (Simulated / Inferred, from the plan)
- C_late(RGL4, eps 0.02) ≈ 0.39 (Inferred). The bar is 0.35.
- There is no early gain, because T ≥ 2 at every step (D_1 = 3).
- **Stress (eps 0.05 > eps_bar).** The supermartingale bound fails here. False RGL4 certificates are possible and are
  reported, not gated.
