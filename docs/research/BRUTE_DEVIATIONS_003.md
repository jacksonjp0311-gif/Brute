# Recorded deviations: Brute v0.1.1 / study BRUTE-011-FALLBACK-003

Pre-registration: `experiments/BRUTE_PLAN_003.json`. Owner decisions and pre-freeze amendments (D1, D2, A1–A6) are in
`BRUTE_v0.1.1_PLAN.md` §7 and are part of the pre-registration. This file lists only notes and changes made **after** the
freeze commit. Criteria are never changed here; an original criterion is always reported as registered.

## Notes carried from v0.1.0

- **FM9 (Exact), study-002 definition mismatch.** `scripts/explore_v020.py` (release-frozen) filters `step < burn_in`,
  so it includes step 8. It reports 1,951 ood5 post-contradiction steps where the sealed status breakdown has 1,945.
  `results/study-002/EXPLORATORY_V020.json` is left as is. All v0.1.1 tooling uses `step > burn_in` (steps 9..44).

## Deviations after the freeze

(none yet)
