# PLAN 023: BRUTE-0200-LR-ANYTIME-023 (v0.20.0), likelihood-ratio anytime perception

**PRE-REGISTERED, PLAN ONLY. Build status: NOT AUTHORIZED.** Machine-readable plan: `experiments/BRUTE_PLAN_023.json`
(the JSON wins if they differ); freeze: `experiments/BRUTE_PLAN_FREEZE_023.json`; ledger `preregistration_023`.
This plan replaces the withdrawn BRUTE-0200-FLAT-ANYTIME-022 (`WITHDRAWN_022.md`). Owner request: James, card t125s484,
2026-10-28 17:56 EDT.

## Idea

Every margin rule so far bounds the true model's absolute flip count F(b), and the slack in that bound grows with b. A
rule with no horizon pays for that growth: RGNA4 reached C_late 0.265, while RGNB4 reached 0.493 (Observed, study-021).
RGL4 instead removes a model h only when a prior-weighted witness model g explains the trace 1/δ times better:

    eliminate h  iff  f_h(b) >= w_n(b) + D_n   for some n,   D_n = min{D : 49^D >= 4|H_n|/δ_L}

At eps_bar 0.02 we have r = 1/49 exactly, |H_n| = n·n^(2n)·4^n, and δ_L = 0.005. This gives D = {1: 3, 2: 4, 3: 5, 4: 7}
(Exact, integer arithmetic). The threshold sits at a constant offset above the best fit, so it does not grow with the
horizon. RGL4 also takes the minimum with the frozen anytime margin m_a at δ = 0.005. The total failure probability is
≤ 0.01.

**Lemma (Exact; to be written out as LR_LEMMA_023.md before any code).**
- Assume the noise is iid with e ≤ eps_bar, independent of the actions and the mask, and that the true world h* is in H.
- Then E_t = Σ_g π(g) r^(f_g − f_h*) is a nonnegative supermartingale with E_0 = 1. On each unmasked bit where g and h*
  differ, E[ratio] = 49e + (1−e)/49 ≤ 1.
- By Ville's inequality, P(sup_t E_t ≥ 1/δ_L) ≤ δ_L.
- If h* is eliminated, then E_t ≥ π(g)·49^(D_n) ≥ 1/δ_L.
- Any exhibited witness is valid, so soundness does not rest on UNSAT claims.

## Candidates checked (Simulated scratch; deleted; nothing committed)

The coverage checks used 30 seen study-021 cases at eps 0.02:
- cycle3: 6 cases
- switch3: 6 cases
- unaliased2: 6 cases
- ood4: 12 cases

All runs used the frozen SP8 trajectory and the frozen region engine.

| candidate | check | result | verdict |
|---|---|---|---|
| flat schedule S5 (022) | margins | within 1 flip of RGNA4 | Rejected (tweak) |
| horizon-doubling RGNB4 wrapper (12 variants) | margins | m(88) 8–10, m(176) 12–15; Σ m over bits 89–176 = 901–1120 vs RGNB4 686, RGNA4 982 | Rejected (≈ RGNA4, Inferred) |
| per-model absolute margins | argument | F ~ Bin(b, e) is the same for every model, so they equal the global margin | Rejected (Exact); subsumed by LR |
| eps estimation | argument + data | fmin is only a lower bound on F (cycle3 8710001: fmin_4 = 0, F = 2), so there is no upper confidence bound on eps | Rejected |
| Bayesian posterior | argument | sound only on average over the prior | Rejected; the mixture-LR form is used instead |
| LR alone | 30-case coverage | C_late 0.438 | runner-up |
| **LR + RGNA4 (RGL4)** | 30-case coverage | **C_late 0.463**; RGNA4 0.338 and RGNB4 0.566 on the same cases; paired dC +0.125 (sd 0.131); 0 false | **chosen** |

Two further checks on the chosen rule:
- **Exact rule vs approximation.** On 8 of the cases, the real rule (min over n of witness w_n + D_n) was identical per
  case to the true-n approximation.
- **Gain by family:**

  | family | gain in C_late |
  |---|---|
  | cycle3 | +0.208 |
  | switch3 | +0.176 |
  | unaliased2 | +0.150 (above RGNB4) |
  | ood4 | +0.045 |

- **Projected population value.** Adding these gains to study-021's per-family RGNA4 gives C_late about 0.39
  (Inferred).

## Study

**Cases**
- 360 main cases (eps 0 / 0.01 / 0.02).
- 60 stress cases (eps 0.05).
- Held-out seeds: 8910001–24, 8920001–24, 8930001–24 and 8940001–48.
- Smoke seeds: 8990001–30.

**Arms**
- RGL4: the headline arm.
- RGNA4: comparator.
- RGNB4: reference, eps 0.02 only.
- RGN4_or, RG4, SP8.
- RGL4_prefix28.

## Headline gate GLR (gated)

- (a) 0 false RGL4 certificates on all 240 noisy main cases.
- (b) CP95 upper bound on the case-false rate ≤ 0.05.
- (c) C_late(RGL4, eps 0.02) ≥ 0.35, with 95% CI lower bound > 0.30.
- (d) Paired dC_late(RGL4 − RGNA4, eps 0.02) ≥ 0.08, with CI lower bound > 0.05.
- (e) The prefix-28 run is identical to the full run on all 120 eps-0.02 cases (horizon-free).

**Other gated checks**
- GLR_lemma
- GAS_frozen_control
- GS_a10
- GS_ref10: a numpy reference with exhaustive fmin_n for n ≤ 3
- GAPI10: brute.certify/9
- G_recount, G10, G12, G13, G_RT, G_HB
- GTI, with clause vi (tooling order, from #107)

## Process

- **Cap and failures.** The cap is 2 h (7200 s). At the cap every stream is sealed with no extension and no rerun.
  Failures are published.
- **Runtime estimate (Inferred).** The mean path is about 5800 s. If the smoke rate math projects more than 6000 s, the
  stress block drops to 30 cases before the source freeze. That is the only change allowed.
- **Release tooling.** It is committed only after run_end_023.
- **Deviations.** Numbered from #108.

## Risks

- (c) has thin headroom: the projection is 0.39 against a bar of 0.35.
- ood4 gains little, because D_4 = 7.
- There is no early-window gain. In the scratch check C_early28 was 0.004, vs 0.014 for RGNB4.
- Stress (eps > eps_bar) has no guarantee, and the relative test may produce false certificates there.
- RGL4 costs about 2–3× RGNA4 per case (ood4 is about 60 s), so there is a risk of hitting the cap.
- |H_n| must match the RegionK encoding. This is checked by GLR_lemma.

## What Brute can't do yet

- It cannot certify early: the first 28 steps are information-limited for every arm.
- Its guarantee needs iid noise with a known eps_bar and a true world of at most 4 states.
- The slack grows as log|H_n|, so larger worlds get weaker certificates.
- It has no independent (non-author) second implementation.
- It runs on synthetic worlds only.
