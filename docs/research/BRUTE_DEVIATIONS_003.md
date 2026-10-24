# Recorded deviations: Brute v0.1.1 / study BRUTE-011-FALLBACK-003

Pre-registration: `experiments/BRUTE_PLAN_003.json`. Owner decisions and pre-freeze amendments (D1, D2, A1–A6) are in
`BRUTE_v0.1.1_PLAN.md` §7 and are part of the pre-registration. This file lists only notes and changes made **after** the
freeze commit. Criteria are never changed here; an original criterion is always reported as registered.

## Notes carried from v0.1.0

- **FM9 (Exact), study-002 definition mismatch.** `scripts/explore_v020.py` (release-frozen) filters `step < burn_in`,
  so it includes step 8. It reports 1,951 ood5 post-contradiction steps where the sealed status breakdown has 1,945.
  `results/study-002/EXPLORATORY_V020.json` is left as is. All v0.1.1 tooling uses `step > burn_in` (steps 9..44).

## Implementation notes (after the freeze; no criterion, threshold, seed, tau or arm changed)

- **N1, request schema v1.1 added.** `brute/api/schema/request.v1_1.json` is a new file the plan's target list did not
  name. It is needed because `request.v1.json` fixes `api_version` as a const, so a v1.1 request could not validate.
  The frozen v1 schema is unchanged.
- **N2, the `uniform` forecast tier is unreachable.** The probability rule lists margin_n5 → suffix1 → uniform.
  Suffix-1 with alpha 0.7 is always defined (on an unseen context it already equals uniform), so `brute/fallback.py`
  never emits `forecast_source='uniform'`. The name stays valid in the schema. Study-003 reports the count, which is
  expected to be 0.
- **N3, standalone v1.1 service class.** `brute/api/service_v011.py` restates the v1.0 handlers in a new class
  (`BruteServiceV011`) instead of subclassing the frozen `brute/api/service.py`. This keeps the frozen file and its
  SOURCE_SHA256 untouched.
- **N4, G10 probability comparison.** The independent reference compares pre-contradiction v0.1.1 probabilities with the
  v0.1.0 control by exact equality. It compares post-contradiction probabilities, recomputed from the plan text, with an
  absolute tolerance of 1e-11, because the recorded values are rounded to 12 decimal places and the reference uses its own
  arithmetic order. Any difference above that counts as a mismatch.
- **N5, per-arm alarm.** Each arm's surprise, residual and alarm come from its own published probabilities. After
  contradiction the v0.1.1 and v0.1.0 alarm flags can differ. This does not change any decision, because the
  contradiction gate comes before the alarm gate. `cases_with_alarm` is reported per arm, and G5 is evaluated on
  in-family cases, which are never contradicted.

## Deviations after the freeze

(none yet)
