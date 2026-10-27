# BRUTE_PLAN_017: bounded-region lookahead before the first certificate (v0.15.0)

This is a readable summary of `experiments/BRUTE_PLAN_017.json`, which is frozen by `BRUTE_PLAN_FREEZE_017.json`. If the two differ, the JSON wins. Labels follow the project rule.

- **Study:** BRUTE-0150-BOUNDED-LOOKAHEAD-017. The parent is study 016 (v0.14.0).
- **Blocks:** the main transfer block (cycle3, switch3, unaliased2 × 24 seeds, ood4 × 48 seeds, × masks 0.1 / 0.35 / 0.6: 360 cases, 96 source libraries) and a reported ood5 block (72 cases, family bound 5 attested).
- **Seeds:** targets 8310001–8340048, sources 8350001–8350096, ood5 8360001–8360024, smoke 8390001–8390030.

## Why the headline moved off the library license

- **Exact lemma.** A license certifies only when the bounded region at n_L + margin forces the answer. If n_L + margin is at least the attested family bound FB, that region contains RG_FB's region, so a license kept inside the attested bound never certifies anything RG_FB does not. *Observed* consistent: DLF2 = RG4 on all 360 study-016 cases.
- **Observed (studies 015–016, seen data).** Every DLF speed or coverage gain came from assuming a bound below FB, and every DLF / RSX / RSXL false certificate (2 ood4 cases; 48 stress pairs) was on a pair where that assumption was wrong. The evidence cannot check the assumption (EB unsound).
- So the only sound lever left inside FB is **which action to take**. v0.13.0 showed that splitting the region evenly from the start is slower; v0.14.0 showed that splitting after the first certificate adds coverage at no cost. v0.15.0 tests a chooser aimed at the first certificate itself.

## Arms

- **RGLX4 (headline):** before RG4's first certificate, take the action that maximises the support-weighted fraction of possible outcomes after which RG4 forces the next reading (ties go to SP8's choice); after it, the frozen RSX choice. Certified by RG4, so soundness is *Exact* in-family.
- **RGL4:** the lookahead for the whole run (reported).
- **RSXL4:** replication of the study-016 headline.
- **DLFa_p / DLFa_n:** attested license (reported; *Exact* = RG4, checked case by case). **DLFp / DLFn:** the study-016 unattested rule (reported).
- **RG5, RSXL5:** ood5 with FB = 5 attested.

## Gates

| Gate | Threshold | Prediction |
|---|---|---|
| GRL (headline) | RGLX4 0 false; TV = S(RGLX4) − S(RG4) ≥ 1.0 step, CI lower > 0 | Open (soundness Exact) |
| GDS2 | RSXL4 0 false; S(RSXL4) = S(RG4) every case; ΔC ≥ 0.03, CI lower > 0 | Inferred PASS |
| GS_a5 | RG4, RGLX4, RGL4, RSXL4, DLFa_p, DLFa_n 0 false (main); RG5, RSXL5 0 false (ood5) | Exact |
| GS_b5 | containment; DLFa = RG4 on every case | Exact |
| G_recount, GS_ref5, GAPI5 (`brute.certify/5`), G10, G12, G13, GTI (K_0130, K_0140 declared), G_RT, G_HB (≤ 30 s) | as study-016 | Inferred PASS; G_HB Open |

Under the same 2 h cap and watchdog as study-016. The release default stays the v0.5.0 rule. Nothing here shows general intelligence.
