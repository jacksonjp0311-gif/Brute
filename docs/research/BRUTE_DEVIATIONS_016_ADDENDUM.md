# BRUTE_DEVIATIONS_016 addendum (v0.14.0, after run_start)

BRUTE_DEVIATIONS_016.md is ledger-hashed and stays unchanged. This addendum records what was found after run_start_016 (04:34:02 EDT). No gate, budget, seed or scoring script was changed, and nothing was re-run.

## #80 One 285 s heartbeat gap (G_HB FAIL)

- **Observed:** `results/study-016/HEARTBEAT_016` has 1023 beats; one gap of 285.065 s ends at 04:46:23 EDT; every other gap is about 2 s. G_HB fails as pre-registered (no gap > 10 s).
- **Observed:** across the gap, the monotonic and boot-time clocks both advanced by 285 s, the watchdog's CPU time rose by 0.001 s, and no study file (including the g11 checkpoints of 4 workers) was written by any process.
- **Inferred:** the whole box was paused at the host level; the study processes were not killed or restarted and every block is complete (RUN_DONE at 2326 s, 144/144 reproducibility). The pause coincided with the operator waiting with an idle sleep; once the operator waited on a live background process, no further gap occurred. Not shown to be the cause.
- **Scored:** as a FAIL. Not excused.

## #81 GTI smoke counted 522 vs 533 tests

- **Observed:** the pre-run GTI smoke (results/smoke-016/GTI_SMOKE_016.json) found 522 per-module vs 533 plain-discover tests. **Exact** cause: plain discovery picked up the then-untracked draft `tests/test_scoring_016.py` (11 tests). The draft was committed under the scoring freeze; release drafts were moved out of the tree before run_start. The gated GTI run counted 533 = 533 and passed.

## #82 test_release_0130 fails on the 0.14.0 tree (K_0130, declared)

- **Observed:** 4 ids fail after the version bump, as declared in RELEASE.json `R_K0130_after_release`: test_version_consistent, test_embeddable_api_answers (api is now brute.certify/4), test_short_verify_passes, test_untampered_copy_passes (verify_release_0130 checks the 0.13.0 release).

## #83 Carried defect in v0.13.0 RELEASE.json

- **Observed:** v0.13.0 RELEASE.json (and BRUTE_SOURCE_FREEZE_015) record `preregistration_commit` c6bfcb3, which is the "HANDOFF: v0.13.0 pre-registered" commit; BRUTE_PLAN_015.json was first committed at 9642783. Both files are frozen or ledger-hashed and are not edited; disclosed only. The plan bytes at c6bfcb3 equal the plan bytes at 9642783, so the plan-unchanged check still held.
- **Observed:** for v0.14.0, `preregistration_commit` 498d768 is the commit that first added BRUTE_PLAN_016.json.
