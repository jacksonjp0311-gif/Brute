# BRUTE_PLAN_016: deferred region split and a license replication (v0.14.0)

This is a readable summary of `experiments/BRUTE_PLAN_016.json`, which is frozen by `BRUTE_PLAN_FREEZE_016.json`. If the two differ, the JSON wins. Labels follow the project rule.

- **Study:** BRUTE-0140-DEFERRED-SPLIT-016. The parent is study 015 (v0.13.0).
- **Blocks:** the main transfer block and a reported ood5 block.
  - Main block: cycle3, switch3 and unaliased2 × 24 seeds, plus ood4 × 48 seeds (doubled), × masks 0.1 / 0.35 / 0.6. That is 360 cases with 96 source libraries.
  - ood5 block: 72 cases.
- **Seeds:** targets 8210001–8240048, sources 8250001–8250096, ood5 8260001–8260024, smoke 8290001–8290030.
- **What came before (Observed, v0.13.0):**
  - RSX4 was sound (0 false in 11,005) and issued more certificates than RG4 (coverage 0.434 vs 0.370), but it certified first 5.27 steps later (GRS FAIL).
  - DLFn and RSXn each issued 1 false certificate on ood4 seed 8140016.
  - EB issued 91 false certificates.
  - On ood5, RG4 issued 121 false certificates and RG5 issued 0.

## Arms

- **RSXL4 (headline):** follows SP8's action until RG4 on the same trajectory has issued its first certificate, then switches to the frozen RSX choice. It is certified by RG4.
  - Because the trajectory is SP8's until that first certificate, S(RSXL4) = S(RG4) on every case by construction (*Exact*). The open question is whether RSXL4 issues significantly more certificates afterwards.
- **RSXLp / RSXLn:** the same trajectory, certified by DLF with the right / wrong-family library.
- **Replication:** DLFp and DLFn on the SP8 trajectory, gated again on fresh seeds.
- **Reported:** RSX4; DLF2 (margin 2, which equals RG4 when n_L ≥ 2, *Exact*); EB as a negative control; RG5; and the ood5 bound-violation signal R_BV.
  - R_BV is the first step at which the 4-state region becomes empty. It cannot block an RG4 certificate at issue time (*Exact*), so it is reported only.

## Gates

| Gate | Threshold | Prediction |
|---|---|---|
| GDS (headline) | RSXL4 0 false; S(RSXL4) = S(RG4) on all 360 cases; ΔC = C(RSXL4) − C(RG4) ≥ 0.03, CI lower > 0 | Open (first two clauses Exact) |
| GS_a4 | RG4, RSXL4, RSXLp, RSXLn, DLFp, DLFn: 0 false | Exact (RG4, RSXL4); Open (DLF arms) |
| GS_b4 | containment, singleton backing, RSXL = SP8 up to the first RG4 certificate | Exact |
| GS_c4 | RSXLn and DLFn 0 false; S(DLFn) − S(RG4) CI lower ≤ 0 | Open |
| G_alias4 | DLF on the RSXL trajectory 0 false on stress pairs; ≥ 20 pairs | Inferred PASS |
| G_recount | own-trajectory recount equals the recorded count | Exact |
| GS_ref4 | numpy exhaustive reference 0 mismatches; mutation 20/20 | Inferred PASS |
| GAPI4 | `brute.certify/4` (certify/3 + deferred `suggest_action`) tests pass inside GTI | Inferred PASS |
| G10, G12, G13, GTI, G_RT, G_HB | as study 015; K_060–K_0130 declared in advance; GTI records dirty tracked files (#74) | Inferred PASS |

Bootstrap: seed-clustered, 2000 resamples, seed 20261028. S is steps-to-first-certificate saved over SP8, censored at 45. C is certificates issued per case / 88.

## Run

2 h cap with the study-015 streams and budgets. At most 8 workers. No extensions, no reruns.

## Order

1. This plan and its freeze, then the ledger entry preregistration_016.
2. The seed check.
3. The seen-data diagnostic of the study-015 DLFn false certificate (`scripts/diag_license_016.py`). It changes no criterion.
4. The reference implementation `v0140_reference.py`.
5. The implementation, then smoke runs on smoke seeds only.
6. The source freeze.
7. The scoring freeze, at least 10 minutes before run_start.
8. The held-out run under a 2 h cap.
9. Seal and gates.
10. Release.

Deviations continue at #75.

Nothing here shows general intelligence.
