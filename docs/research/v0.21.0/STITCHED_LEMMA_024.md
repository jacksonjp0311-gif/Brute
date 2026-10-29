# STITCHED_LEMMA_024: the stitched likelihood-ratio region (RGL5)

Study BRUTE-0210-STITCHED-LR-024. Written after the plan freeze (`preregistration_024`) and the build authorisation
(`build_authorization_024`), and BEFORE `experiments/v0210_reference.py`, `brute/stitchedregion.py`,
`brute/api/certify10.py` and the study-024 runner existed. Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

## Reading of the plan text (disclosed as deviation #115, lemma-level spec)
The plan says: within epoch k "apply the planned-horizon LR threshold for H_k". RGL4's bound is
T = min(m_a(b), T_L(b)) with two parts (LR_LEMMA_023):
- the LR witness part T_L (Ville's inequality over a prior on H). Ville is already anytime; a fixed-horizon (Markov)
  version has the same 1/δ_L threshold, so a planned horizon cannot tighten it. It is kept **unchanged**, at δ_L = 0.005.
- the count part m_a(b; 0.02, 0.005), the frozen horizon-free AnytimeBoundary. This is the part a planned horizon can
  tighten (it is what RGNB4 uses with a planned B). RGL5 **replaces m_a by the stitched planned-horizon boundary** below.
This is the only reading under which "planned-horizon threshold" changes anything; it is stated here before any code.

## Definitions
- eps_bar = 0.02, δ = 0.01 = δ_L + δ_a with δ_L = δ_a = 0.005 (as RGL4). D_n = {1: 3, 2: 4, 3: 5, 4: 7} (as RGL4).
- **Epochs.** Step i (1-based; the support for action i is computed on readings 0..i−1, so i readings) is in epoch
  k(i) = 0 for i ≤ 28, and otherwise the least k with i ≤ 28·2^k. H_k = 28·2^k, B_k = 2·H_k (the most observed bits that
  i ≤ H_k readings of 2 bits can hold), δ_k = δ_a / ((k+1)(k+2)) as an exact rational.
  Horizon 88 uses k = 0 (steps 1–28, B 56, δ 1/400), k = 1 (29–56, B 112, δ 1/1200), k = 2 (57–88, B 224, δ 1/2400).
- **Planned-horizon test.** bd_k = the frozen `brute.seqmargin.boundary(B_k, 0.02, δ_k)` (linear alpha spending over
  B_k bits, exact DP; the RGNB4 function, unchanged).
- **Stitched margin.** With b_i = observed bits in readings 0..i−1: M(i) = max(M(i−1), bd_{k(i)}[b_i]), M(0) = 0.
- **Bound.** T5(i) = min(M(i), min over exhibited witnesses g_n of (w_n + D_n − 1)).

## Lemma (Exact)
Assume the noise is iid Bernoulli(e), e ≤ eps_bar, independent of the actions and of the mask (as RGL4).
1. **Per epoch.** Let E_k = {the running flip count over the observed-bit sequence exceeds bd_k[b] at some b ≤ B_k}.
   By the frozen v0.17.0 DP, P(E_k) ≤ δ_k (the observed flips are iid Bernoulli(e) in observed-bit order because the
   mask is predictable; e ≤ eps_bar is stochastically dominated). Fewer than B_k observed bits only shrinks E_k.
2. **Union.** Σ_{k≥0} δ_k = δ_a · Σ 1/((k+1)(k+2)) = δ_a · Σ (1/(k+1) − 1/(k+2)) = δ_a, and every finite partial sum
   is δ_a(1 − 1/(K+2)) < δ_a. So P(∪_k E_k) < δ_a = 0.005, for every horizon (anytime; no planned length is read).
3. **Coverage.** On the complement of ∪E_k: at step i, b_i ≤ 2i ≤ B_{k(i)}, so F(b_i) ≤ bd_{k(i)}[b_i] ≤ M(i). Taking the
   running max only enlarges M, so F ≤ M at every step.
4. **LR part.** Exactly LR_LEMMA_023 statements 1–3 and 5: P(the true world is ever removed by T_L) ≤ δ_L = 0.005.
5. **Total.** P(the true machine ever has more than T5 flips) < δ_L + δ_a = 0.01; on the complement every singleton
   support after burn-in is the latent code (v0.17.0 conditional soundness with T5 in place of m).
6. **"Kept only while every later epoch's test holds."** Certificates are recomputed every step from the current
   region; a later epoch can only enlarge M (step 3), so no extra rule is needed. **Prefix-stable:** M(i) and T5(i)
   depend only on readings 0..i−1 and i (Exact).
7. **Stress (eps 0.05 > eps_bar).** Outside the assumption; false certificates are possible and are reported (GLS b
   gates them at 0 as the plan says; a failure is published, not excused).

## Exact per-step rule (implementation spec)
At step i: b = observed bits in readings 0..i−1; k = k(i); cap = M(i) as above. Then the RGL4 search of LR_LEMMA_023
rule 2 unchanged (n = 1..4, start points s_n carried, `tolerant_region` feasibility while m + D_n − 1 < cap, SAT
lowers cap to m + D_n − 1, UNSAT/UNKNOWN never lower; unknowns counted). T5 = cap. `attain` = n of the last witness
found at this step, or None if T5 = M(i). The region is the frozen tolerant region (n = 4, m_bound = T5).
- **Monotone** (Exact): M is a running max and s_n never decreases.
- **Equal to the uncapped rule** when cumulative witness_unknowns = 0: T5 = min(M(i), min_n (fmin_n + D_n) − 1).
- **Record** `lr5` per case: delta_L, delta_a, D, epochs [{k, H, B, delta "p/q"}], epoch [k(i)], M [M(i)], T, attain,
  witnesses, witness_unknowns, witness_calls.

## Second implementation (experiments/v0210_reference.py; same author, not independent)
No `brute` import. Recomputes δ_k as exact rationals, bd_k with the frozen reference `ref_boundary`, M(i), the exact
fmin_n for n ≤ 4 by enumeration (frozen `v0200_reference.fmin_tables`), T5_ref = min(M, min_n(fmin_n + D_n) − 1);
checks T5 exactly when cumulative unknowns are 0, else T5 ≥ T5_ref; re-simulates every witness; recomputes RGL5 supports
and certificates from the frozen full-table costs. The carried arms are audited by the frozen `v0200_reference.audit_main`
on the case with the RGL5 fields removed. Mutation test: 20 single-field errors in 20 cases, all must be caught.

## GLS (e): pre-declared bound (the plan allows "identical, or a pre-declared bound")
RGL5 cannot be identical to RGL4 on steps 1–28 by design (M(28) = bd_0[b] is below m_a). (e) holds iff all three:
- e1: on every eps-0.02 main case, a separate RGL5 run on the first 28 actions equals the 88-step RGL5 run on steps
  1–28 (supports, unknowns, T, certificates) (prefix stability, Exact claim tested);
- e2: 0 false RGL5 certificates on steps 1–28 over the eps-0.02 main cases;
- e3: paired mean of C_early28(RGL5) − C_early28(RGL4) over eps-0.02 main cases ≥ −0.005.

## Smoke seeds (plan 024 does not list them; chosen here, before any draw)
9090001–9090030, following the study-number convention (023 used 8990001–8990030): 9090001–008 smoke targets (two per
family), 009–012 API test, 013–015 kill drill, 016–030 spare. Checked disjoint by `scripts/check_seeds_024.py`.

## Expectations (Simulated from the boundaries only; no trace was run)
At b = 2i: m_a / bd_k / RGNB4 boundary = step 28: 7 / 5 / 5; step 45: 9 / 8 / 6; step 88: 14 / 12 / 9.
So M sits 1–2 flips below m_a but 2–3 above RGNB4's planned boundary (Simulated). The late gain over RGL4 depends on how
often m_a (not T_L) was the binding term in RGL4; GLS c (≥ +0.04) is **Open** and may fail.
