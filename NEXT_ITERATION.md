# Brute v0.2.0: next iteration

Brute v0.1.0 met its safety goal on study-002 (0 false conditional certificates in all 7 families; v0.90 control: 79 on
ood5, 77 on drift4) but **failed C6**: on 5-state worlds (ood5) post-burn-in log-loss is 1.504767, worse than uniform
(1.386294). It also certifies far less: in-family coverage fell from 0.32–0.52 (v0.90) to 0.05–0.20.
The BGR v0.90 next-iteration note is kept at `docs/research/bgr-v0.90.0/NEXT_ITERATION.md`.

## Where the loss comes from (Observed, study-002)

| ood5, post burn-in | steps | mean log-loss |
| --- | ---: | ---: |
| before the n≤4 family is contradicted | 583 | 1.4836 |
| the contradiction step (ε/4 floor, ln 200) | 64 | 5.2983 |
| after contradiction (uniform fallback) | 1945 | 1.3863 |

drift4 shows the same pattern (1270 / 60 / 1262 steps; 0.8312 / 5.2983 / 1.3863). Most out-of-family steps are spent in
the uniform fallback.

## Exploratory evidence (post hoc, not a criterion: `results/study-002/EXPLORATORY_V020.json`)

On post-burn-in steps where the n≤4 family was contradicted:

| | ood5 | drift4 |
| --- | ---: | ---: |
| steps | 1951 | 1262 |
| n≤5 margin learner still supported | 1951 (100%) | 439 (35%) |
| margin support contained the actual reading | 1951 | 427 |
| margin singleton predictions, correct / total | 1435 / 1435 | 223 / 267 |
| log-loss: Brute (uniform) | 1.386294 | 1.386294 |
| log-loss: predicting from the margin support with the ε reserve | 0.269114 | 1.211903 |
| log-loss: suffix-1 baseline | 1.278843 | 1.064114 |

(These step counts come from this script's filter and differ slightly from the sealed status breakdown.)

## Candidates

| | Direction | What the data says |
| --- | --- | --- |
| (a) | Out-of-family detection | Contradiction already catches 72/72 ood5 and 60/72 drift4 cases. The residual alarm fired in 48 ood5 cases and on 0 in-family cases. Detection is not the bottleneck; the response is. |
| (b) | Self-growing families | On ood5 the next-larger family was never contradicted and its singletons were 1435/1435 correct. Growing would replace 1.386 with about 0.27 on those steps and restore coverage. On drift4, growth alone is unsafe: 44 of 267 singletons were wrong and the margin was contradicted on 823 steps. |
| (c) | Active experimentation | Could cut MARGIN_DISAGREES abstentions (in-family: 607–837 steps per family). Needs an action-choice protocol and a new study design first. |
| (d) | Transfer | No current evidence; needs (b) first so that there is something to transfer. |
| (e) | Richer alphabets | Multiplies row cost. Peak margin rows are already 99,818 of the 160,000 budget at n≤5. Premature. |

## Recommended single step: (b) self-growing families, gated by the next-larger margin

On contradiction of the n≤k family, re-scope to n≤k+1 instead of falling back to uniform. Keep the existing certify rule:
certify only when the grown family and an n≤k+2 margin agree, and the grown family is unsaturated and unalarmed. Keep
uniform when the grown margin is also contradicted (the drift4 case). Every re-scope is a receipt, and no earlier certificate
is reused.

Why this one:
1. It targets the only failed criterion (C6 on ood5). The exploratory upper bound is 0.27 against 1.39.
2. It addresses the largest loss block (3,207 uniform post-contradiction steps across ood5 and drift4).
3. It is the first step from a fixed model class to a learner that grows its own model class, which (d) and (e) depend on.

Main risk, to measure and not assume: margin row cost at n≤6. The n≤5 margin peaked at 99,818 rows. If the n≤6 margin
exhausts its budget, the result must be ABSTAIN/BUDGET_EXHAUSTED, never a certificate.

## Study-003 pre-registration sketch (to freeze before any code)

- The same 7 families plus a 6-state family; new seeds; the same masks.
- **Keep** C1–C5 and C7 unchanged.
- **C6:** ood5 post-burn-in log-loss ≤ ln 4 **and** ≤ the suffix-1 baseline.
- **New:** zero false certificates after any re-scope; drift4 false certificates ≤ the v0.1.0 level (0).
- **New:** row budget exhaustion is reported per family.

Not claimed: general intelligence. This is still a bounded deterministic Moore domain with 2 actions and 2 bits.
