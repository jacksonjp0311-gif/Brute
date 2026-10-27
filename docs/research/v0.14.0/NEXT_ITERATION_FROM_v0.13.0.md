# Brute v0.13.0 → v0.14.0: next iteration (proposal; pre-registered as BRUTE_PLAN_016 on `plan/v0.14.0`)

The previous note is in `docs/research/v0.13.0/NEXT_ITERATION_FROM_v0.12.0.md`. Labels are as in the README. Nothing here counts as evidence until it runs on fresh seeds. The longer path is in `docs/ROADMAP_TO_GI.md`.

## Where v0.13.0 leaves things (Observed, study-015, 11 of 15 gated pass)

- **Region splitting buys coverage but costs time to first certificate.** RSX4 issued 0 false in 11,005 certificates, and more than RG4 (9,368), but its first certificate came 5.27 [4.59, 5.99] steps later (GRS FAIL). It was later on 220 of 288 cases.
- **The bound cannot be read off the evidence.** EB issued 91 false certificates (switch3 47, ood4 42) and EB2 8. A wrong attested bound also fails: on ood5, RG4 issued 121 false certificates; RG5 issued 0.
- **The license is not airtight.** DLFn and RSXn each issued 1 false certificate on one ood4 case (seed 8140016, mask 0.35). This is the first DLF false certificate in any study.
- **The rest held.** Containment, own-trajectory recount, reference audit 360/360, reproducibility 120/120, `brute.certify/3` contract, heartbeat (max gap 2.03 s).

## Recommendation for v0.14.0 (Inferred; pre-registered as BRUTE_PLAN_016)

1. **Deferred region split (headline).** Follow SP8's action until the first RG4 certificate, then switch to RSX (arm RSXL4). Its time to first certificate equals RG4's by construction (*Exact*). The gate is on coverage: certificates per case up by at least 0.03 over RG4, with the CI lower bound above 0.
2. **Re-test the license.** Diagnose the 8140016 case on the sealed study-015 data (seen data, labelled as such). Then re-gate DLF on fresh seeds with the ood4 block doubled. A margin-2 license equals RG4 whenever n_L ≥ 2 (*Exact*), so it is reported and not offered as a fix.
3. **Measure bound violation on ood5 (reported only).** An RG4 certificate needs a non-empty 4-state region, so an "empty region" detector cannot block any RG4 certificate at issue time (*Exact*). Report the first step at which the region empties and how many false certificates come before it.
4. **Retire EB.** Keep it only as a reported negative control.
5. **Find the #74 cause.** The GTI runner records the dirty file list, so `tracked_tree_dirty` can be explained.
6. **Declare test failures in advance.** Declare the K_0120 / K_0130 frozen-test failures expected after the bump.

Deferred and still **Open**: sub-machine concepts, stochastic worlds, grounding beyond templates, and independent audit.

Nothing here shows general intelligence.
