# Study-010 (v0.8.0) deviations and disclosures

Numbering continues from study-009 (#26). Each item says what differs from the frozen plan (`experiments/BRUTE_PLAN_010.json`, commit 881f0a6) or what the plan left open and how it was decided before data. Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

**#27: source freeze list.** `BRUTE_SOURCE_FREEZE_010.json` also freezes `tests/test_run_tests_080.py`, `tests/test_v080_xcheck.py` and `tests/test_diag_stale_010.py`, which the plan's freeze_rule list does not name. `scripts/verify_release_080.py` and `tests/test_release_080.py` are in that list but are written at release, after the run. They descend from 881f0a6 but are not frozen before the run. (Exact)

**#28: the watchdog was changed after a kill drill.** In smoke-2 (seeds 3190025-30, cap 20 s), the orchestrator started `repro_breadth` at t0 + 18 s. That was after the watchdog's last 2 s read of RUN_STATE, so the stream was never killed and finished at t0 + 26.4 s (Observed). Fix, made before the source freeze (commit 438a496):
- At the deadline the watchdog SIGSTOPs the orchestrator, re-reads the state, and adds the process group of every descendant (found through the /proc ppid chain).
- The orchestrator writes RUN_STATE immediately after each start.
- A unit test now covers an untracked child.

The re-drill (smoke-3) killed all 8 groups in 0.239 s, with no SIGKILL and no survivors (Observed). The held-out runner was therefore changed after a smoke result. This is a harness change, not a learner change.

**#29: G_RT (iii) evidence.** The drill latency is taken from the smoke-3 drill. Its STOP_010.json is copied verbatim to `results/study-010/KILL_DRILL_010.json` before run_start. The held-out run itself is not killed on purpose. (Exact)

**#30: scoring readings fixed in `scripts/make_gates_010.py` before data.** Its docstring holds the full list. The main ones:
- **GD:** INSUFFICIENT_EVENTS is a FAIL. A missing hull_union counts as a clause (ii) exception.
- **G7:** the min-probability floor applies to the production arms J8, SP8 and BSP8. SC7, A4, B5 and BSC7 are reported.
- **G11 (iv):** passes when `mandatory_done.wall_since_start` is ≤ 1500 s and the g11 stream was not stopped by the cap or an error. A budget stop of the rest phase after mandatory_done is allowed.
- **G_RT (i):** fails if any stream was stopped for any reason, its own budget included.
- **G_RT (ii):** the last heartbeat must be within 10 s of the run end.
- **GX2 (iii):** fails if gx2_sym is stopped for any reason.

**#31: mutation test scope.** The 20 injections are drawn from the 2x2 mandatory traces only (J8, SP8, SC7). Breadth has no mutation test. That matches the plan's (iii), which names J8 and SP8 fields. Injected fields are counted from a per-step trace diff, which merges the taken action's forecast certificate and status. (Exact)

**#32: implementation readings.**
- At T=0 the jump hull equals Y1k.
- An UNKNOWN solver result in the jump hull gives all codes.
- hull_union is recorded after the predicts and never changes a forecast.
- The LU-C non-calm branch is LU-R.
- The spot truncation restricts end-of-trace fields to the 24-step prefix.
- Kill latency is measured until every tracked pid is gone.

(Inferred: each is the natural reading of the plan text.)

**#33: MANIFEST.sha256 is regenerated just before t0.**
- **What happened:** a GTI dev run (`run_tests_080.py` on the pre-freeze tree, outside any held-out range, 851.5 s wall) failed clause (i) on exactly one undeclared test, `test_brute_repro.BruteRepro.test_manifest_matches_tracked_files` (Observed). The manifest lists every tracked file, the ledger included, so any commit invalidates it. Every other failure was in the 14 K_frozen ids or allowed by K_060/K_070, and both clean-tag runs reproduced.
- **What was done:** `scripts/make_manifest.py` is run and committed after the run_start_010 ledger commit and before RUN_T0 is written, so the in-cap GTI sees a manifest of the tree it tests.
- **Effect on the cap:** the few seconds this takes count against the cap, because t0 is the ledger time.
- **Why this is not tuning:** no test, rule or threshold changed. (Exact)

## Written after the run (release, 2026-10-26 EDT)

Entries #34–#37 were written after the seal. None changes a criterion, a scoring script, a threshold or a sealed byte.

**#34: release-time changes to the repository.**
- **Single verifier mode.** `scripts/verify_release_080.py` has one (fast) mode. It does not re-run the second implementation, the cross-check or GTI. It binds their sealed reports through the study SEAL and the block seals instead, and it regenerates PAIRED_ANALYSIS_010, REPRODUCIBILITY_010 and GATES_010 byte for byte. (Exact)
- **Sealed files that were git-ignored are now committed** (commit 7b8a06d): `RUN_STATE_010.json`, `RUN_010.log` and `logs/*.log`, 116 KB in total. They were sealed (`SEAL.json` lists them) but `.gitignore` excluded them. Without `RUN_STATE_010.json`, `make_gates_010.py --check` failed in a clean clone, because G_RT reads its completion stamps. Their bytes match the SEAL. The CHECKPOINT files stay uncommitted, and the verifier allows only checkpoints and logs to be absent. (Exact / Observed)
- **REQUIRED_KEYS is keyed by path.** It is keyed by the path relative to `results/study-010`, because the block seals and the study SEAL share a file name. (Exact)
- **Merge commit.** `origin/main` (a86298b, README and MANIFEST only) was merged into `plan/v0.8.0` at b1e628d, after the seal and before the release docs. The branch had not changed README, so README came from main and was then edited for v0.8.0. MANIFEST was regenerated. main is fast-forwarded to the release commit. (Exact)

**#35: heartbeat gaps.** The orchestrator heartbeat (`HEARTBEAT_010.jsonl`, 882 beats) has two gaps over 10 s:
- 125.4 s, ending 05:18:51 EDT.
- 84.5 s, ending 05:33:12 EDT.

An independent 1 s shell loop outside the orchestrator (`/tmp/hb010.log`, not committed) shows the same gaps, 123.6 s and 84.5 s. That points to the whole VM being suspended rather than the orchestrator stalling (Inferred). The cap is wall-clock, so the gaps count against it. G_RT (ii) still passes, because the watchdog ran for the whole run and the last heartbeat is within 10 s of the run end (Observed). Stream wall times include the gaps.

**#36: G_RT (i) fails on an optional phase.** `g11_2x2` finished its mandatory set at 640.9 s with mutation 20/20. Its optional "rest" phase (the remaining 432 traces) was then stopped by its own 1,500 s stream budget at 130/432. It therefore has no `completed_at` stamp. The frozen reading (#30) counts any stop as a G_RT (i) failure, so G_RT is scored FAIL. G11 itself passes under its own rule (#30, G11 iv). (Exact)

**#37: ledger omissions.**
- The smoke-1 dry run (`run_start`, 04:39:12 EDT) has no `run_end` entry.
- No `deviation_010` entry was written before the affected runs for #28 or #33, although the plan's ledger_rule asks for one. The deviations were committed to this file before the run (#27–#32 at faa6ac5, #33 at 7705ac9, both before t0) and are now ledgered retroactively as one `deviation_010` entry at release.
- HANDOFF.md was not updated during the v0.8.0 run. It is updated at release.

(Exact)

## 38. Superseding ledger receipt for `experiments/brute_study_010.py` (release, 2026-10-26 ~05:52 EDT)

The smoke-1 `run_start` entry (ledger line 153, commit 2c00b54, 04:39 EDT) used the harness `experiments/brute_study_010.py` as its source, at the pre-drill version. The harness was then changed before the source freeze (2afa269: kill-drill smoke seeds). It is frozen at `5470c48` with sha256 c774b65c…, so the last ledger receipt for that path no longer matched its bytes, and `verify_release_080` failed with "ledger source changed: experiments/brute_study_010.py". Following the ledger's supersede rule, a `source_receipt_010` entry was appended at release for the current bytes, which equal the BRUTE_SOURCE_FREEZE_010 hash. No source changed. The smoke-1 entry stays in the ledger as the record of what ran at 04:39 EDT. Evidence: Exact (hash equality with the freeze).

## 39. Verifier dates note-less ledger receipts from git (release, 2026-10-26 ~06:00 EDT)

The three `scoring_freeze_010` ledger notes have no leading ISO time, so the first `verify_release_080` failed with "Invalid isoformat string: 'scoring'". Before anything was published, the verifier was changed: when a note has no ISO time, the receipt is dated by the commit that first added its line to the ledger (`git log -S<receipt_sha256>`). For the scoring receipts that commit is 154943b at 04:52:45 EDT, 632 s before run_start (05:03:17 EDT). That meets the pre-registered rule of at least 600 s. The release freeze 080 was regenerated and re-ledgered (superseding receipt). Evidence: Exact (git commit times).
