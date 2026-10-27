# BRUTE_PLAN_014: bounded transfer (v0.12.0)

This is a readable summary of `experiments/BRUTE_PLAN_014.json`, which is frozen by `BRUTE_PLAN_FREEZE_014.json`. If the two differ, the JSON wins. Labels follow the project rule.

- **Study:** BRUTE-0120-BOUNDED-TRANSFER-014. The parent is study 013 (v0.11.0).
- **Block:** transfer only. There are 288 target cases: 4 families (cycle3, switch3, unaliased2, ood4) × 24 seeds × masks 0.1, 0.35 and 0.6. They draw on 96 source libraries. The 2x2 and big78 blocks are not re-run because no learner they test changed. Their v0.11.0 results are cited, not re-claimed.
- **Seeds:** targets 7110001–7140024, sources 7150001–7150096, smoke 7190001–7190030.
- **What came before (Observed on SEEN 013 data):**
  - Bank unanimity was Rejected (537 false certificates).
  - The library-free bounded region at the family bound, RG4, is sound and gives mean S 11.16 over SP8.
  - So the transfer license is scored on its value over RG4. That value was 1.94 [1.20, 2.70] on seen data.

## Arms

All arms run on the SP8 trajectory unless noted.

- **RGn:** certify c when every complete Moore machine with at most n states that is consistent with the evidence predicts c, and c is in the SP8 support. RG4 is the gated baseline.
- **DLF** (the headline, the disagreement-based license): the SP8 certificate, else RG4, else a library-licensed certificate. A library-licensed certificate requires three things:
  - the library is alive and unanimous on c;
  - c is in the SP8 support;
  - the bounded region at min(n_L + 1, 4) states is {c}.

  It runs with the positive library (DLFp) and the wrong-family library (DLFn). DLF0 is the margin-0 sensitivity arm.
- **DX** (discriminating library experiments): the frozen v0.11.0 LX action choice, certified by DLF on its own trajectory.
- **AT6:** the frozen v0.11.0 control.
- **Stress:** all 72 wrong-family libraries per case. A stress pair is one where AT6 licenses at least one transfer certificate.

## Gates

| Gate | Threshold | Prediction |
|---|---|---|
| GST2 (headline) | GS_a + GS_c + GS_d | Inferred PASS |
| GS_a | RG4, DLFp, DLFn, DXp, DXn: 0 false certificates | Exact inside the bound; Inferred otherwise |
| GS_b | SP8 ⊆ RG4 ⊆ DLF certificates; singleton backing | Exact PASS |
| GS_c | DLFn has 0 false and TV CI lower ≤ 0 | Inferred PASS |
| GS_d | DLFp mean TV ≥ 1 step and CI lower > 0 | Inferred PASS (seen 1.94) |
| GS_rg | RG4 has 0 false, mean S ≥ 1 and CI lower > 0 (not transfer) | Inferred PASS |
| GS_x | DXp − DLFp mean ≥ 1 and CI lower > 0 | Open |
| G_alias | DLF has 0 false on stress pairs; at least 20 pairs | Inferred PASS |
| GS_ref | numpy exhaustive reference (n ≤ 5) has 0 mismatches; mutation test catches 20/20 | Inferred PASS |
| GAPI2 | brute.certify/2 tests pass inside GTI | Inferred PASS |
| G10, G12, G13, GTI, G_RT | as in study 013; K_0100 and K_0110 declared in advance | Inferred PASS |
| G_HB | largest heartbeat gap ≤ 30 s (watchdog_014) | Open |

Here TV = S(X) − S(RG4), and S counts steps-to-certificate saved over SP8, censored at 45. The bootstrap is seed-clustered: 2000 resamples, seed 20261026.

## Run

- The run has a 2 h cap.
- Streams:
  - transfer: 4 workers, 2400 s
  - gti: 2 workers, 3600 s
  - after transfer, repro: 2 workers, 1500 s
  - after transfer, g11 reference: 2 workers, 2400 s
- At most 8 workers run at once. There are no extensions and no reruns.

## Limits

- The measured transfer is a state-count prior plus a veto. Content-level transfer is Open.
- The family bound is a caller attestation.
- The reference implementation is by the same author.
