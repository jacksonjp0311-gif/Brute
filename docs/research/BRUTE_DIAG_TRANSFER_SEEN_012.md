# Transfer diagnostic on seen data (study 012, EXPLORATORY)

**Label: Observed on seen data, so it is exploratory and not v0.10.0 evidence.** The frozen BRUTE_PLAN_012 is unchanged.

## How it was run

- The frozen TR rule (transfer_definition.TR_arm) was recomputed by `experiments/v0100_reference.py` on the sealed SP8 traces of study 011.
- The traces cover cycle3, switch3, unaliased2 and ood4: 72 cases each, 44 steps.
- Libraries were learned from the smoke source seeds 5190021–5190030, never from held-out seeds.
- Script: `scripts/diag_transfer_seen_012.py`. Output: `results/diag-012/TRANSFER_DIAG_SEEN.json`.

## Results

S is the number of steps by which TR certifies sooner than SP8 on the taken action: S = T_cert(SP8) − T_cert(TR).

| family | TRp mean S | TRp false | TRn mean S | TRn false (cases) | TRn eliminated |
|---|---|---|---|---|---|
| cycle3 | 17.8 | 0 | 8.8 | 113 (25) | 72/72 |
| switch3 | 16.4 | 0 | 4.8 | 46 (13) | 72/72 |
| unaliased2 | 19.0 | 0 | 3.2 | 34 (8) | 72/72 |
| ood4 | 32.3 | 0 | 5.9 | 53 (13) | 72/72 |

## Reading (Inferred)

- **Same-family transfer works.** TRp gives a large speed-up and issued no false certificates on these traces.
- **A wrong-family motif library is not sound.** The target evidence eventually removes every TRn hypothesis (72/72 cases), but in 59 of the 288 cases it first issues false certificates. The SP8 support guard does not stop this.
- **"Eventually eliminated" is not the same as "sound".** A transfer prior restricts the version space soundly only if the target is actually in the prior's class, and these 44-step traces cannot confirm that in advance.
- **Predictions under the frozen plan:**
  - GT_a fails (on its TRn part).
  - GT_c(i) fails.
  - GT_c(ii) probably fails too, since TRn mean S > 0.
  - All three will be published as failures. The plan already listed TRn soundness as Open.
