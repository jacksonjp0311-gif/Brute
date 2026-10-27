# Brute license diagnostic 014, part b: the library-free baseline

Label: **Observed on SEEN data** (the sealed study-013 transfer traces, 288 cases, already scored for v0.11.0). Exploratory, run before BRUTE_PLAN_014 was written. Not v0.12.0 evidence. Part a is in `BRUTE_DIAG_LICENSE_014.md`; that file is ledger-hashed and is not edited, so this note is a separate file.

Script: `scripts/diag_license_014b.py`. Output: `results/diag-014/LICENSE_DIAG_SEEN_B.json`. Wall time 74.6 s (informational).

## Question

Part a found that the bounded-region license DL1 was sound and fast (mean S 11.12). It also found that the region-only ablation BR1p matched DL1p exactly. So the question here is whether DL1's speedup comes from the library at all.

## Arms

All arms run post hoc on the SP8 trace. A non-SP8 certificate is issued only after burn-in, and only for a code inside the SP8 published support.

- **RGn** (library-free): certify c when every complete Moore machine with at most n states that is consistent with the evidence predicts c.
- **DLF**: if RG4 certifies c, certify c. Otherwise, certify c when the library is alive and unanimous on c **and** the region at min(n_L + margin, 4) states is {c}.
- **DLF0**: the same rule with margin 0.

| Arm | False certs | Cases with false | Mean S vs SP8 | cycle3 | switch3 | unaliased2 | ood4 |
|---|---|---|---|---|---|---|---|
| RG2 | 373 | 91 | 13.08 | 7.43 | 12.10 | 19.40 | 13.40 |
| RG3 | 142 | 48 | 15.69 | 11.96 | 14.10 | 15.96 | 20.74 |
| **RG4** | **0** | 0 | **11.16** [9.63, 13.01] | 6.74 | 6.61 | 8.21 | 23.08 |
| RG5 | 0 | 0 | 4.56 | 1.54 | 1.38 | 0.13 | 15.18 |
| **DLFp** | **0** | 0 | **13.10** [11.46, 14.86] | 6.74 | 6.61 | 15.96 | 23.08 |
| DLFn | 0 | 0 | 11.16 | 6.74 | 6.61 | 8.21 | 23.08 |
| DLF0p | 0 | 0 | 17.14 | 11.96 | 14.10 | 19.40 | 23.08 |
| DLF0n | 9 | 3 | 11.54 | 6.94 | 6.72 | 8.21 | 24.28 |

## Transfer value over RG4

The transfer value is TV = S(X) − S(RG4). The CI is a seed-clustered bootstrap with 2000 resamples and seed 20261026.

| Arm | Mean TV | 95% CI | Library-licensed certs |
|---|---|---|---|
| DLFp | 1.94 | [1.20, 2.70] | 1725 |
| DLFn | 0.00 | [0.00, 0.00] | 0 |
| DLF0p | 5.98 | [5.01, 6.91] | 6019 |
| DLF0n | 0.38 | [0.11, 0.72] | 34 |

## Aliasing stress

The stress test covers all 72 wrong-family libraries per case, 20,736 pairs in total. A stress pair is one where AT6 licenses at least one transfer certificate; there are 600 of them.

- **AT6** issued 1,080 false certificates on the stress pairs.
- **DLF** issued 0 false certificates on the stress pairs and 0 on all pairs. That includes 912 library-licensed certificates.
- **DLF outside the Exact bound** (1,728 pairs): 0 false.

## Reading

**Observed:**
- RG4 has no library, yet it gives the whole DL1 / DLFn speedup.
- The SP8 certificate rule is conservative compared with the bounded region at its own declared family bound.

**Exact:**
- RG4 is sound for every target with at most 4 states.
- DLF is sound whenever the target has at most min(n_L + 1, 4) states.

**Observed:**
- DLF's only real transfer value over RG4 is in unaliased2 (+7.75 steps there). There the library's state bound (n_L = 2, so 3 states) is tighter than 4.
- In the other families DLFp equals RG4.

**Inferred:** the transfer is a state-count prior plus a veto. It is not content-level transfer.

**Rejected:** margin 0, which was unsound under stress in part a (3,216 false).

**Pre-registration consequence:** BRUTE_PLAN_014 uses DLF as the headline. GS_d and GS_c score it on the transfer value over RG4, not on speedup over SP8. RG4's speedup is a separate, non-transfer gate (GS_rg).
