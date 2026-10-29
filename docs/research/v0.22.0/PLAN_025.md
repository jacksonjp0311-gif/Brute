# v0.22.0 plan: study BRUTE-0220-BETTING-CS-025 (PLAN ONLY; build NOT authorized)

**Status.** Pre-registered at the commit that adds this file and `experiments/BRUTE_PLAN_025.json`. No v0.22.0 arm code, reference code, held-out draw or run exists at that commit. **The build is NOT authorized**; it needs a separate owner instruction.

## Why (from study-024, *Observed*)

- RGL5 (stitched LR) stayed sound on the noisy main set: 0 of 240 false, CP95 0.0124.
- It added almost no late coverage: dC_late RGL5 - RGL4 = +0.0076 [0.0032, 0.0128] at eps 0.02 (bar 0.04).
- It trails RGNB4 by 0.036 and the oracle by 0.417 (ratio 0.501).
- *Inferred:* most of the oracle gap is the cost of planning for the worst-case eps_bar rather than the true flip rate.

## What v0.22.0 would test

- **RGB6 (new, `brute.certify/11`, method `betting`).** A betting confidence sequence for the flip rate (alpha = delta/2) sets an eps-adaptive LR margin (at delta/2), capped at eps_bar. Same family bound, burn-in, eps_bar 0.02 and total delta 0.01 as RGL4.
- Lemma and DP reference first, before any RGB6 code.
- Arms: RGB6, frozen RGL5, RGL4, RGNB4, oracle RGN4_or, RG4, SP8. 360 main + 30 stress cases, 88 steps, reproset 30, fresh held-out ranges 91x0001.

## Gates (headline GBC)

- (a) 0 false on noisy main; CP95 <= 0.02.
- (b) 0 false on stress cases with eps <= eps_bar. Stress with eps > eps_bar is outside the guarantee and reported, not gated. This is declared before any data and is informed by the study-024 clause-b failure (#118).
- (c) dC_late(RGB6 - RGL4) at eps 0.02: mean >= 0.04 and CI lower > 0.
- (d) dC_late(RGB6 - RGNB4) at eps 0.02: CI lower > -0.06.
- (e) no early (steps 1-28) certificate beyond RGL4's that is false.
- G_HB is measured on the monotonic clock; wall-clock-only steps are reported separately.
- Others as in study-024 (G_PROC, GS_ref11, GAPI11, G10, G12, G13, GTI, G_RT, G_recount); release gates GCC and GLV.

## Discipline

Never force-push; no `.github` or workflows; git and gh with `env -u GITHUB_TOKEN -u GH_TOKEN`; push after every step; append-only ledger; frozen files never edited; failures published.
