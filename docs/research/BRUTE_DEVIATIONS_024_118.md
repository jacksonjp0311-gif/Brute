# Study-024 deviations #118 and the run outcome (written after run_end, seal and gates)

#117 (pre-run) is unchanged. This file records what happened during and after the held-out run. Labels: Exact,
Observed, Inferred, Open.

## #118 item 1: release-tooling drafts sat in the working tree for about one minute while GTI was running

**Evidence (Observed).** About 05:58 to 05:59 EDT, untracked drafts of `tests/test_release_0210.py` and
`scripts/verify_release_0210.py` were in the working tree. They were moved to scratch outside the repository and only
moved back after `run_end_024`. Nothing was committed.

**Effect (Exact, from `results/study-024/TEST_SUITE_024.json`).**
- `head` 3e4e881 and `tracked_tree_dirty` false.
- `per_module` holds 159 modules, and none of them is `test_release_0210`. Plain discovery ran 873 tests, returncode 0,
  and ran last, well after the drafts had been removed.
- Every verdict clause is true, including `vi_tooling_order` and `v_new_tests_pass`.

The drafts did not enter the measured suite. The rule from #107 (no release tooling before run_start) was kept for
commits but not for the untracked working tree.

## #118 item 2: the study-024 .gitignore rules were added after the run

Earlier studies added their raw-result ignore rules before the run. Study 024 added them in the seal commit 612d651.
The rules cover `results/study-024/**/RESULTS.json`, `**/SCIENTIFIC.json`, `**/*CHECKPOINT*` and `logs/`.
`RUN_024.log` is tracked, because clean_clone_024 lists it in TRACKED. This changes no study bytes (Exact): the seal
was written before the commit, and the raw JSON is committed as deterministic gzip.

## #118 item 3: two heartbeat gaps over 10 s, so G_HB fails

**Evidence (Exact, `HEARTBEAT_ATTRIBUTION_024.json`).**

| wall from (EDT) | wall gap (s) | monotonic gap (s) | boottime gap (s) | sentinel stall (s) |
|---|---|---|---|---|
| 06:05:17 | 31.674 | 4.301 | 4.301 | 3.125 |
| 06:54:21 | 35.829 | 6.325 | 6.325 | 4.510 |

Both are classed as clock_step (Inferred). The wall clock moved about 27 to 30 s more than CLOCK_MONOTONIC. Both
coincided with failures to spawn a tool shell on the host. G_HB is not loosened, so it FAILs.

## #118 item 4: notes on how GLS failed (the gate stands as registered)

- **(b) Exact.** There were 3 RGL5 false certificates in one stress case (switch3, seed 9020005). That case has eps 0.05,
  which is above the certifier's eps_bar of 0.02, so it lies outside the attested soundness condition of
  brute.certify/10. The plan still requires 0 on stress, so (b) FAILs. RGL4 had 0 false certificates on stress.
- **(c) Exact.** dC_late(RGL5 − RGL4, eps 0.02) is 0.007576, with CI [0.00322, 0.012784]. The CI is above 0, but the
  mean is below the 0.04 threshold.
- **(d) Exact.** dC_late(RGL5 − RGNB4, eps 0.02) is −0.035795, with CI [−0.065625, −0.007386]. The CI lower bound is
  below −0.06.
- **(a) and (e) pass.** There were 0 false certificates on the 240 noisy main cases, with a one-sided CP upper bound of
  0.0124. The prefix-28 RGL5 bound holds.

No threshold was changed. There is no rerun.
