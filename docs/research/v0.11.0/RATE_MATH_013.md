# Study-013 rate math (before the source freeze)

BRUTE_PLAN_013 stop_rule.rate_math: turn the smoke timings into a projected wall time per stream before the source
freeze. If a mandatory stream projects above 70% of its budget, ONE change (budget/worker split, big78 count or the
optional list) is allowed, as a disclosed deviation. Nothing changes after run_start.

Timings are from the shared 8-CPU box (Observed). Projections are Inferred. Study-012 spent times are from
results/study-012 (Observed, a different case mix, used only as a scale).

| stream | measurement (Observed) | projection (Inferred) | budget | share |
|---|---|---|---|---|
| 2x2 (3 w, mandatory) | smoke-1 16 cases in 32 s; study-012 2x2 spent 737 s for the same 792-job design | ~740 s | 2400 s | ~31% |
| big78 (2 w, mandatory) | study-012 SP8_78 arm sum 800 s over 144 cases (5.6 s/case); smoke-1 4 cases 12 s | 288 x 5.6 / 2 = ~800 s; ~1000 s under contention | 2700 s | ~30-37% |
| transfer (1 w, mandatory) | smoke 8 cases: SP8 4.7 s, LXp 6.5 s, LXn 4.3 s (total ~3.3x SP8); study-012 SP8 212 s / 288 cases | 212 x 3.3 = ~720 s | 1800 s | ~40% |
| gti (2 w, mandatory) | GTI smoke 10:26-10:50 EDT on the working tree at 3871e78: 1464 s wall, 388 tests (= plain discover), clean-tag runs 060/070/080/090 included (results/study-013/GTI_SMOKE_013.json) | ~1500-1700 s under run load | 2700 s | ~55-63% |
| repro (2 w, after 2x2) | smoke-1 8 s; study-012 228 s | ~400 s | 1500 s | ~27% |
| g11 (2 w, after 2x2 + transfer) | smoke-1 252 s (drift4 6190015 J10 91.8 s / SP8 63.9 s); study-012 961 s | ~1000-1100 s | 1800 s | ~61% |

Critical path (Inferred): max(2x2 + max(repro, g11), big78, gti) ~ 1700-1850 s, about 25% of the 7200 s cap.

## Decision

No mandatory stream projects above 70% of its budget. **No change is made**; the single permitted change is not used.
Exact: scripts/run_study_013.py budgets equal stop_rule.streams_and_budgets.

## GTI smoke (Observed, dev, not evidence)

388 tests, counts match plain discover, frozen files unchanged (393 checked), new tests all pass, test_study_005 6/6,
K_060/K_070/K_080/K_090 declared rules applied (clean-tag runs of those releases pass on their own tags).
Verdict FAIL on clause (i) with 3 undeclared failures: test_brute_repro.test_manifest_matches_tracked_files and
test_release_0100 test_short_verify_passes / test_untampered_copy_passes, all raising "MANIFEST.sha256 does not match
tracked files". Cause (Observed): scripts/study013_storage.py (commit 7dc04c8) was not yet in MANIFEST.sha256 and the
tree was dirty. Same failure mode as the study-012 GTI smoke. The held-out run starts after make_manifest on a
committed clean tree; this is re-checked before run_start.
