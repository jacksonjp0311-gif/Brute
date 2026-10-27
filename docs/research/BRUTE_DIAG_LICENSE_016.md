# Diagnosis of the study-015 DLF false certificate (seen data, before any v0.14.0 code)

BRUTE_PLAN_016 process_controls step 3, report R_diag_license. Script: `scripts/diag_license_016.py`; output:
`results/diag-016/DIAG_LICENSE_016.json`. Inputs are only the sealed, already-scored transfer blocks of studies 014 and
015. **This changes no v0.14.0 criterion.** Every number here is *Observed* on seen data unless it is marked otherwise.

## The case

| Field | Value |
| --- | --- |
| Target | study-015 main block, ood4 seed 8140016, mask 0.35; true state count n* = 4 (evaluator only) |
| Wrong-family library | unaliased2 source 8150064, one 2-state motif, so n_L = 2 and license bound min(n_L + 1, 4) = 3 |
| Step / action | step 9 (the first step after the burn-in of 8), counterfactual action 0 |
| Certificate | 0; the true reading was 1 |
| Bounded support for action 0 at step 9 | n = 1, 2, 3: {0}; n = 4, 5: {0, 1} |
| SP8 support | {0, 1} (no SP8 certificate) |
| Library | 1 hypothesis alive before step 9, predicting 0; refuted by the step-9 observation (disabled_step 9) |
| Same step, same action | RG2 and RG3 also certified 0 (wrong); RG4 and RG5 did not certify |
| RSXn | the same false certificate at the same step (RSX and SP8 trajectories agree up to step 9) |
| License region (n = 3) empty | first at step 22, 13 steps after the false certificate |

## Mechanism (*Exact* from the rule, *Observed* on the case)

DLF licenses a certificate when the frozen library is alive and predicts c, c is in the SP8 support, and every Moore
machine with at most n_L + 1 states that is consistent with the evidence predicts c. The BRUTE_PLAN_014 lemma makes
this sound only when the true machine has at most n_L + 1 states. The library's own state count n_L sets the bound,
not the target's. A wrong-family library with a small motif (n_L = 2) therefore sets the bound to 3 on a 4-state ood4
target. That is outside the guarantee, so the license is then just RG3 gated by a library that happens to agree. Here
the 3-state region and the 2-state motif agreed, and both were wrong.

## How often the license ran outside its guarantee

| Study | Arm | License certificates inside the guarantee (n* ≤ bound) | False | Outside (n* > bound) | False |
| --- | --- | --- | --- | --- | --- |
| 015 | DLFp | 1,542 | 0 | 0 | 0 |
| 015 | DLFn | 0 | 0 | 3 | **1** |
| 015 | RSXp | 1,854 | 0 | 0 | 0 |
| 015 | RSXn | 0 | 0 | 2 | **1** |
| 014 | DLFp | 1,625 | 0 | 0 | 0 |
| 014 | DLFn | 0 | 0 | 1 | 0 |

On the 72 DLFn cases per study where the bound was below n* (every ood4 target with an unaliased2 library), RG at the
license bound issued 173 false certificates in 015 and 130 in 014. Library agreement filtered all but 1 of them in 015
and all of them in 014.

## What this means

- *Observed:* every license certificate issued inside the Exact guarantee (5,021 across both studies) was correct.
  Every false one came from outside it.
- *Inferred:* the license is not a soundness mechanism for wrong libraries. It is RG_{n_L+1} plus a filter, and the
  filter was nearly, but not fully, effective. Soundness needs the bound to be attested for the target (FB), not read
  from the library.
- *Exact:* margin 2 (DLF2) gives min(n_L + 2, 4) = 4 = FB whenever n_L ≥ 2, so it equals RG4 here and is not a license
  fix (BRUTE_PLAN_016 pre_freeze_disclosure (c)).
- *Exact:* the empty-region signal arrived 13 steps late, so an empty-region detector cannot block this certificate at
  the step it is issued.
- *Open:* whether the v0.14.0 doubled ood4 block reproduces a DLFn false certificate. GS_a4 and GS_c4 gate it as
  pre-registered; the prediction stays Open.
