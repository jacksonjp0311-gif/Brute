# Exploratory seen-data diagnostic: applicability-tested transfer (pre-plan, v0.11.0)

**Label: Observed on SEEN data (exploratory).** Source: the sealed study-012 transfer traces (288 target cases, already
scored for v0.10.0). Script: `scripts/diag_applicability_013.py`; output `results/diag-013/APPLICABILITY_DIAG_SEEN.json`.
Committed before `experiments/BRUTE_PLAN_013.json`; disclosed as deviation #52.

Rule replayed: the v0.10.0 transfer rule (`brute.transfer.TransferTracker.decide`) may fire only after the library has
made >= M *confirmed informative* predictions (library unanimous on the taken action's next code, SP8 support for that
action has >= 2 codes, observation fully unmasked, observed code equal to the prediction).

| M | TRp false | TRp mean speedup | TRn false (cases) | TRn transfer certificates |
|---|---|---|---|---|
| 0 (v0.10.0 TR) | 0 | 20.18 | 167 (50) | 322 |
| 2 | 0 | 16.27 | 22 (10) | 44 |
| 3 | 0 | 13.36 | 3 (2) | 8 |
| 4 | 0 | 11.02 | 0 (0) | 0 |
| 6 | 0 | 6.28 | 0 (0) | 0 |
| 8 | 0 | 3.10 | 0 (0) | 0 |

Reading (Inferred): on seen data the smallest M with zero wrong-family transfer certificates is 4. Plan 013 freezes
**M = 6** (a +2 margin above the seen boundary, chosen before any held-out data) for the gated AT arm and reports
AT4 (M = 4) as a non-gated sensitivity arm. Soundness of AT on the wrong family is an empirical claim (Open until
held-out), not an Exact property: a wrong library can survive M confirmations by chance.
