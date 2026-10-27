# Brute v0.12.0 → v0.13.0: next iteration (proposal; pre-registered as BRUTE_PLAN_015 on `plan/v0.13.0`)

The previous note is in `docs/research/v0.12.0/NEXT_ITERATION_FROM_v0.11.0.md`. Labels are as in the README. Nothing here counts as evidence until it is run on fresh seeds. The longer path is in `docs/ROADMAP_TO_GI.md`.

## Where v0.12.0 leaves things (Observed, study-014, 15 of 16 gated pass)

- **Bounded transfer is sound on the aliasing stress block.** On 600 stress pairs (a wrong-family library that the v0.11.0 AT6 rule lets license transfer), AT6 issued 2,016 false certificates and DLF 0. Over all 20,736 target × wrong-library pairs DLF issued 336 licenses, 0 false. GST2 and G_alias pass.
- **Most of the speedup is the library-free bound, not the library.** RG4 (certify when every ≤4-state machine consistent with the evidence agrees) saves 10.86 [9.83, 11.84] steps over SP8 with 0 false in 9,809. DLFp adds TV 1.64 [1.27, 2.01] on top, **all of it on unaliased2** (6.57; 0.00 in cycle3, switch3 and ood4). A license helps only when the library's own bound n_L + 1 is below the family bound 4.
- **The bound must be right.** RG2 (353 false) and RG3 (130 false, all ood4) are faster and unsound; DLF0 (margin 0) gives S 16.35 but DLF0n issued 6 false on ood4 and 3,576 on the stress pairs. RG5 is sound and slower (TV −6.45).
- **Discriminating experiments did not help (GS_x FAIL).** DX − DLF (positive library) −0.007 [−0.59, 0.57]. The frozen LX action choice confirms the library rather than splitting the bounded region.
- **Clock fixed.** Largest heartbeat gap 2.0 s (v0.11.0: 335 s).
- **API:** `brute.certify/2` (family bound, optional library, reason on UNKNOWN) passes its contract tests.

## Recommendation for v0.13.0 (Inferred; pre-registered as BRUTE_PLAN_015)

1. **Region-split experiments (headline).** Pick the action whose possible next readings split the bounded region RG4 most evenly (expected-collapse of the bounded support), not the library's confirmations. Gate: mean S over RG4 on the RG4 certifier ≥ 1 step with seed-clustered CI lower > 0, 0 false.
2. **Tight per-case bound from the library.** Test whether min(n_L + 1, 4) can be replaced by a bound certified from the evidence (smallest n with a non-empty region, plus margin 1). Prediction: helps only where the true state count is below the family bound (*Inferred*); soundness of a data-derived bound is *Open* and is the main risk, so it is a gated soundness arm with an aliasing stress block.
3. **Scale the family bound to 5.** Re-run RG at bound 5 on a 5-state family to measure cost and value; RG5 was sound but slower at bound 4 targets.
4. **Recount every arm on its own trajectory** (fix of the #62 scorer defect), and declare K_0110 / K_0120 test failures after the bump in advance.

Deferred and still **Open**: sub-machine concepts, stochastic worlds, grounding beyond templates, and independent audit.

Nothing here shows general intelligence.
