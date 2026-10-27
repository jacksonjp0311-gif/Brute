# BRUTE_PLAN_015: region-split experiments and an evidence-derived bound (v0.13.0)

This is a readable summary of `experiments/BRUTE_PLAN_015.json`, which is frozen by `BRUTE_PLAN_FREEZE_015.json`. If the two differ, the JSON wins. Labels follow the project rule.

- **Study:** BRUTE-0130-REGION-SPLIT-015. The parent is study 014 (v0.12.0).
- **Blocks:** the main transfer block (cycle3, switch3, unaliased2, ood4 × 24 seeds × masks 0.1 / 0.35 / 0.6 = 288 cases, 96 source libraries, 20,736 aliasing-stress pairs) and a reported ood5 block (24 seeds × 3 masks = 72 five-state cases).
- **Seeds:** targets 8110001–8140024, sources 8150001–8150096, ood5 8160001–8160024, smoke 8190001–8190030.
- **What came before (Observed, v0.12.0):** RG4 S 10.86 over SP8; the library added 1.64 steps, only on unaliased2; library-guided experiments (DX) added nothing (−0.007); bounds below the true state count are unsound (RG3 130 false on ood4).

## Arms

- **RSX4 (headline):** a new trajectory that picks the action whose RG4 bounded next-code support is largest (the experiment the bounded region is least sure about; ties and all-singleton steps use SP8's LU-R choice), certified by RG4.
- **RSXp / RSXn:** the same trajectory certified by the v0.12.0 license DLF with the right / wrong-family library.
- **EB:** an evidence-derived bound: the smallest n ≤ 4 with a non-empty region, plus 1. Not guaranteed sound; gated on soundness. EB2 (plus 2) is reported.
- **Replication:** RG4, DLFp, DLFn on the SP8 trajectory; RG2 / RG3 / RG5 reported; ood5: RG4 and RG5 reported.

## Gates

| Gate | Threshold | Prediction |
|---|---|---|
| GRS (headline) | RSX4 0 false; S(RSX4) − S(RG4) ≥ 1 step, CI lower > 0 | Open |
| GS_a3 | RG4, RSX4, RSXp, RSXn, DLFp, DLFn: 0 false | Exact (RG4, RSX4); Inferred otherwise |
| GS_b3 | containment and singleton backing | Exact |
| GS_c3 | RSXn 0 false; S(RSXn) − S(RSX4) CI lower ≤ 0 | Inferred PASS |
| GEB | EB 0 false | Open |
| G_alias3 | DLF on RSX trajectory 0 false on stress pairs; ≥ 20 pairs | Inferred PASS |
| G_recount | every arm recounted on its own trajectory equals the recorded count (fixes #62) | Exact |
| GS_ref3 | numpy exhaustive reference 0 mismatches; mutation 20/20 | Inferred PASS |
| GAPI3 | `brute.certify/3` (certify/2 + `suggest_action`) tests pass inside GTI | Inferred PASS |
| G10, G12, G13, GTI, G_RT, G_HB | as study 014; K_060–K_0120 declared in advance | Inferred PASS |

Bootstrap: seed-clustered, 2000 resamples, seed 20261027. S is steps-to-first-certificate saved over SP8, censored at 45.

## Run

2 h cap. transfer (main + ood5) 4 workers 3000 s; gti 2 workers 3600 s; after transfer, repro 2 workers 1500 s and g11 reference 2 workers 2400 s. At most 8 workers. No extensions, no reruns.

## Limits

- Synthetic deterministic worlds. The family bound 4 is a caller attestation.
- EB may be unsound; that is the question it asks.
- Same-author second implementation. Not general intelligence (*Exact*).
