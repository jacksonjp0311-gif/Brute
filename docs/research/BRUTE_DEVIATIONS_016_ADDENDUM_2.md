# BRUTE_DEVIATIONS_016 addendum 2 (#84–#85)

`BRUTE_DEVIATIONS_016_ADDENDUM.md` is ledger-hashed and is not edited. This file corrects it.

## #84 Wrong G_HB threshold quoted in #80

- **Exact:** `experiments/BRUTE_PLAN_016.json` defines G_HB_heartbeat_gap as "largest heartbeat gap <= 30 s". Addendum #80 wrongly quoted it as "no gap > 10 s". (10 s is the threshold for reporting a gap in R_heartbeat_attribution, not the gate.)
- **Exact:** the verdict does not change. The largest gap, 285.065 s, is above 30 s, so G_HB still FAILS. GATES_016.json scored against the plan's 30 s threshold.

## #85 NEXT_ITERATION headline superseded before pre-registration

- **Exact (lemma, from the DLF definition):** the v0.15.0 proposal in `NEXT_ITERATION.md` at the release commit `36d8488` (an attested-bound library license) would certify exactly what RG_FB certifies. A license kept inside the attested bound never certifies more than RG_FB. *Observed* consistent: DLF2 = RG4 on all 360 cases.
- So BRUTE_PLAN_017 puts the headline on a bounded-region lookahead chooser instead. The attested license stays in as a reported equality check.
- This was found while drafting, before the plan was frozen, and no v0.15.0 data existed at the time.
