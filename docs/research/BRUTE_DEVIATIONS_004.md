# Recorded deviations: Brute v0.2.0 / study BRUTE-020-ACTIVE-004

Pre-registration: `experiments/BRUTE_PLAN_004.json`, frozen in commit `c0ac594` (ledger receipt `72e177e6…`).
This file lists only notes and changes made **after** that freeze commit. Criteria are never changed here; an
original criterion is always reported as registered. Labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

## Bridge items (owner input, branch `bridge/v0.1` @ `9c88a3a`; the bridge worktree was not edited)

- **B1, double issuance through brute.api/1.1 (Exact).** `service_v011._predict` calls `record_issued` on every CERTIFIED
  predict, and the frozen v0.1.0 `record_issued` appends `(steps+1, certificate)` without checking, so two predicts at one
  step put the same certificate twice in `issued`. At a later contradiction the retraction list then has it twice.
  - Fix: `brute/active.py` `ActiveBruteLearner.record_issued` records each `(step, certificate)` at most once. brute.api/1.2
    (`brute/api/service_v020.py`) uses it. brute.api/1.1 and `brute/fallback.py` are frozen and keep the old behaviour; the
    contract test `tests/test_api_contract_v020.py::test_double_predict_records_once` pins both (1.2 lists the retraction
    once, 1.1 twice).
  - Effect on sealed metrics: **none (Exact)**. `experiments/brute_study_003.py` calls `predict` and `record_issued` once per
    step per learner (code reading). Checked on the sealed `results/study-003/RESULTS.json`: 504 cases, 26 retractions in
    11 cases, 0 duplicate steps, and in every one of the 11 cases the number of retractions equals the number of CERTIFIED
    steps up to the contradiction. Study-004 calls `record_issued` once per step on the taken action only; G9 additionally
    counts duplicate issued / retraction pairs (expected 0).
  - Open: if a client predicts BOTH actions at one step and both are certified with different codes, 1.2 records both
    (they are different `(step, certificate)` pairs). The learner cannot know which action the client takes; a client should
    call predict only for the action it takes, or use `experiment` (read-only) to compare actions.
- **B2, three failing tests on a fresh clone of main (Exact).** Reproduced on a fresh `git clone` of main @ `7a52671`:
  127 tests, 1 failure + 2 errors. `test_manifest_matches_tracked_files` and `test_release_011::test_fast_verify_passes`
  fail because `.gitattributes` said `*.ps1 text eol=crlf`, so checkout writes `BGR-All-One.ps1` with CRLF while
  `MANIFEST.sha256` records the committed LF bytes (study-003 deviation D5 found the same effect for `git archive`).
  `test_verify_fails_under_tampered_results` is the known A3 version error. The development worktree hid the first two
  because its file predates the attribute.
  - Fix: `.gitattributes` now says `*.ps1 -text`, so checkout is byte-identical to the committed blob (which is the BGR
    original byte-for-byte); `MANIFEST.sha256` regenerated. The README test count is corrected at release to the count
    measured on a fresh clone of the release commit.
- **B3, brute.api/1.2 (implementation notes).** New files `brute/api/schema/request.v1_2.json`,
  `brute/api/schema/response.v1_2.json`, `brute/api/service_v020.py`. Differences from the plan's one-line description,
  none of which touches a criterion:
  - `per_action` is an array `[{action, counts}]` (one entry per action symbol, in alphabet order) instead of an object keyed
    by action symbol, because the response schema uses `additionalProperties: false` objects with fixed keys;
    `family_code_rows` is an array of `{value, rows}`.
  - the `experiment` object also carries `tied` (true when both scores are equal and the default action was taken).
  - `default_action` is optional (default: the first action symbol); `counts` defaults to false.
  - the op is read-only: no evidence, certificate or issuance changes (tested).

## Implementation notes (after the freeze; no criterion, threshold, seed, tau or arm changed)

- **N1, release version.** As pre-registered (`release_version_note`): `brute/__init__.py` (0.1.0) and `brute/version.py`
  (0.1.1) stay frozen; `brute/release_version.py` says 0.2.0. `tests/test_release_011.py::test_fast_verify_passes` and
  `tests/test_brute_repro.py::test_verify_fails_under_tampered_results` are expected errors after the RELEASE.json bump
  (version checks, by construction); `scripts/verify_release_020.py` runs the frozen 0.1.1 verifier on the raw v0.1.1 blobs.
- **N2, window peak rows.** `window_peak_rows` is the maximum `max_rows_seen` of the window learner over its restarts,
  updated after each supported window update (a fresh window has 1 row).
- **N3, lazy margin copy.** The lookahead updates the <=5 margin copy only when the <=4 copy already has a single-code
  support for some b; otherwise N(a,c)=0 whatever the margin says, so the score is the same (Exact, by the rule's
  conjunction). `lookahead_copies` counts the copies actually made.
- **N4, independent reference written before the run.** `experiments/v020_independent_reference.py` is written from the plan
  text and frozen in `experiments/BRUTE_SOURCE_FREEZE_004.json` before study-004 is run (as for study-003). Before
  contradiction the v0.89/v0.90 catalogue term inside A's probabilities is checked for sum and floor only (as in studies
  002/003); P's are checked equal to the frozen v0.1.1 control.
- **N5, harness guard.** `aggregate_004` reports per-mask rows only for mask rates present in the case list (needed for the
  unit test on a 3-case subset; the full study has all three mask rates, so the study output is unaffected).

## Deviations after the study run

- **D1, storage of the sealed traces (no data, metric or criterion changed).** The frozen harness wrote `RESULTS.json`
  (133,549,844 bytes) and `SCIENTIFIC.json` (133,460,089 bytes), above GitHub's 100 MB per-file limit, so they could not be
  pushed. They are committed as deterministic gzip files (`*.json.gz`, level 9, mtime 0) of the exact sealed bytes; the raw
  files are git-ignored. `scripts/study004_storage.py restore` (called by the gate, paired and release-verifier scripts)
  rebuilds the raw files and checks them against `SEAL.json`, which is unchanged and still binds the raw bytes. Ledger
  receipts for the traces name the `.gz` files. Done right after the run, before any result was read.
