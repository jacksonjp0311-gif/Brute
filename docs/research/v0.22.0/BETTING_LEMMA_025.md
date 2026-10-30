# BETTING_LEMMA_025: the betting-test eps-adaptive LR region (RGB6)

Study BRUTE-0220-BETTING-CS-025. Written after the plan freeze (`preregistration_025`), the build authorisation
(`build_authorization_025`, card t128s531) and plan amendment A1 (`plan_amendment_025_A1`), and BEFORE
`experiments/v0220_reference.py`, `brute/bettingregion.py`, `brute/api/certify11.py` and the study-025 runner existed.
Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

## 1. The plan text and why it cannot be built as written (deviation #119, lemma-level spec)
The plan: "maintain a predictable-plug-in betting confidence sequence (hedged capital, alpha = delta/2) for eps on
**observed mismatches under the leading hypothesis**; at each step use its upper end eps_hat_u (capped at eps_bar) in
place of eps_bar in the RGL4 LR threshold at confidence delta/2."

- **Rejected as unsound (Exact).** The mismatch count of the leading (least-mismatch) hypothesis is w_min ≤ F, the
  true flip count, at every step (the true machine is one of the candidates). A confidence sequence fed w_min instead
  of F is fed a count that can be arbitrarily below the truth (worst case: the data are explained by a wrong machine
  with zero mismatches), so its upper end has no coverage guarantee. Plugging it into the LR threshold would void
  the soundness lemma. This reading is not implemented.
- **Rejected as not computable (Exact).** A predictable plug-in bet λ_t needs the flip indicator of every past bit; only
  an upper bound on the total count is available, never the per-bit flips. A fixed finite λ-mixture needs only the
  total, because the wealth of a product of per-bit factors depends on the count, not the order.
- **Sound reading built (this lemma).** The betting test is fed a count that upper-bounds F on the good event (the
  level-0 bound T_0 below), the "upper end" is taken on a finite grid of rates, and each grid rate gets its own LR
  witness offsets at its own delta. The split is delta/2 for the count/betting side and delta/2 for the LR side,
  as the plan asks.

## 2. Definitions (all deltas exact rationals)
- eps_bar = 0.02, delta = 0.01. Observed bits b (as RGL4). Family bound N = 4, |H_n| = n·n^(2n)·4^n (as RGL4).
- **Level 0 (rate p_0 = eps_bar = 0.02).** m_a0(b) = frozen `AnytimeBoundary(0.02, delta_a0)` with delta_a0 = 1/400.
  D0_n = least D with ((1−p_0)/p_0)^D ≥ N|H_n| / delta_L0, delta_L0 = 1/400. T_0 = min(m_a0(b), min over exhibited
  witnesses g of (w_g + D0_{n(g)} − 1)).
- **Adaptive levels j = 1, 2: p_1 = 1/100, p_2 = 1/200.** Betting test of H_j: e ≥ p_j with the fixed mixture
  λ_l = l / (4(1 − p_j)), l = 1..4:
  K_j(t, b) = (1/4) Σ_l (1 + λ_l p_j)^(b − t) · (1 − λ_l(1 − p_j))^t (exact Fraction).
  Level j is **active** at step i if K_j(T_0(i'), b(i')) ≥ 1/delta_cj at some step i' ≤ i (sticky), delta_cj = 1/800.
  Active level j has offsets Dj_n = least D with ((1−p_j)/p_j)^D ≥ N|H_n| / delta_Lj, delta_Lj = 1/800.
- **Bound.** D_eff,n(i) = min of Dj_n over level 0 and the active levels. T6(i) = min(m_a0(b_i), min over exhibited
  witnesses g of (w_g + D_eff,n(g)(i) − 1)), with the RGL4 witness search (brute.lrregion rule, #108 cap) started from
  cap = m_a0(b_i) and loop condition m + D_eff,n − 1 < cap.
- **eps_hat_u (reported, not gated).** eps_hat_u(i) = min(p_j over level 0 and the active levels).
- **Delta split (Exact):** count/betting side delta_a0 + delta_c1 + delta_c2 = 1/400 + 2/800 = 1/200 = delta/2;
  LR side delta_L0 + delta_L1 + delta_L2 = 1/200 = delta/2; total = 1/100 = delta.

## 3. Lemma (Exact)
Assume iid Bernoulli(e) flips on observed bits, e ≤ eps_bar, independent of the actions and of the mask (as RGL4).
1. **Count.** P(F(b) > m_a0(b) for some b) < delta_a0 (frozen anytime DP at p = eps_bar ≥ e; monotone in e).
2. **LR at level 0.** P(the true machine's mismatch count ever exceeds w_g + D0_n − 1 for an exhibited g) ≤ delta_L0
   (LR_LEMMA_023 argument: likelihood-ratio supermartingale under e ≤ p_0, prior 1/(N|H_n|), Ville).
3. On G_0 = complement of the events in 1 and 2, F(i) ≤ T_0(i) at every step.
4. **Betting.** For each bit the factor 1 + λ(p_j − x) (x the flip indicator) has mean 1 + λ(p_j − e) ≤ 1 under H_j, and
   is ≥ 0 for λ ≤ 1/(1 − p_j). The product over observed bits is K_j(F, b), a nonnegative supermartingale under H_j, and
   so is the mixture (Ville): P_{H_j}(sup K_j(F, b) ≥ 1/delta_cj) ≤ delta_cj. K_j(t, b) is non-increasing in t, so on
   G_0, K_j(T_0, b) ≤ K_j(F, b). Hence if e ≥ p_j, level j activates on G_0 with probability ≤ delta_cj.
5. **LR at level j.** If e ≤ p_j the level-j witness bound fails with probability ≤ delta_Lj (as 2). If e > p_j, the level
   is active only on the event of 4.
6. **Union.** Except with probability ≤ delta_a0 + delta_L0 + Σ_j (delta_cj + delta_Lj) = delta, F(i) ≤ T6(i) at every
   step i, and every singleton support after the burn-in is the latent code (frozen certifier argument). Horizon-free:
   no planned length is read, so the bound is prefix-stable.
7. **Monotonicity.** T6 is not required to be monotone (a level activation can lower it); the reference checks the
   witness rule and T6_ref per step instead.

## 4. Exact pre-run prediction: no adaptive level can activate at horizon 88
A case has at most 89 readings × 2 bits = 178 observed bits. For any count t ≥ 0 and any λ ≤ 1/(1 − p_j),
K_j(t, b) ≤ K_j(0, b) ≤ (1/(1 − p_j))^b. At b = 178: (100/99)^178 = 5.98 for p_1 and (200/199)^178 = 2.44 for p_2,
far below 1/delta_cj = 800. Reaching 800 needs ≥ 666 bits (p_1) or ≥ 1334 bits (p_2), i.e. ≥ 333 / 667 fully observed
steps. This holds for every λ grid, every predictable plug-in λ_t in [0, 1/(1−p_j)], and even with all of delta/2 on
one test (1/delta = 200 needs ≥ 530 bits). **So within this study RGB6 = T_0 exactly: eps_hat_u = 0.02 at every step.**
D0 = (3, 4, 5, 7), the same as RGL4's (3, 4, 5, 7) at delta_L 0.005 (Exact); m_a0 at 1/400 is ≥ RGL4's m_a at 1/200
(e.g. 10 vs 9 at b = 88). Hence T6 ≥ T_RGL4 at every step and RGB6 certifies at most what RGL4 certifies (Exact, up to
SAT unknowns).
- **Predicted (Inferred, from the above):** GBC c (dC_late(RGB6 − RGL4) ≥ 0.04) FAILS; dC_late is ≤ 0 by
  construction. GBC d likely FAILS (024: RGL4 trailed RGNB4 by ~0.044). GBC e passes trivially. GBC a and the
  strict stress clause b are open (024: RGL4 stress behaviour decides b). The failure is published, not forced.
- For reference: D at p_1 = (3, 4, 5, 6), at p_2 = (2, 3, 4, 5) (Exact); even if a level activated, the gain would be
  ≤ 2 flips of slack.
