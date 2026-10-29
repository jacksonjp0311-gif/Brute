# Deviation #113: the frozen release verifier rejects a dual-role commit (v0.20.0)

Labels: **Exact** means checked by code in this repo; **Observed** means run and recorded.

- **What happened (Observed, 2026-10-28 ~22:48 EDT).**
  - `python scripts/verify_release_0200.py` stopped with `VERIFICATION FAILED: reference_1 and implementation_0 are the
    same commit`.
  - `scripts/verify_release_0200.py` was frozen by BRUTE_RELEASE_FREEZE_0200 (`3a30555`).
- **Cause (Exact).**
  - In `experiments/BRUTE_SOURCE_FREEZE_023.json`, `reference_commits[-1]` and `implementation_commits[0]` are both
    `9e0ca70`.
  - That one commit landed the second implementation (`v0200_reference`) together with the RGL4 code.
  - The new `git_order` required every adjacent pair of the process chain to be distinct commits. Earlier releases never
    had a dual-role commit, so the check was never exercised.
  - This is a bug in post-run release tooling. It is not a study defect: no gate input, seal, or study artifact is
    involved.
- **What was done.**
  - Nothing frozen was edited.
  - New `scripts/verify_release_0200_r1.py` runs the frozen `_verify` unchanged, with one replacement for `git_order`. A
    repeated commit is accepted only at the reference→implementation boundary, and only when the source freeze itself
    lists the same hash in both roles.
  - All other ancestry and strictness checks are kept. `tests/test_release_0200_r1.py` shows that any other duplicate is
    still rejected.
  - The new files are locked by `experiments/BRUTE_RELEASE_FREEZE_0200_R1.json`.
  - This follows the earlier `_R1` release-freeze pattern (0.6.0, 0.7.0, 0.9.0).
- **Effect.**
  - `tests/test_release_0200.py::test_short_verify_passes` fails by design: it calls the frozen verifier. Recorded, not
    hidden.
  - The release is verified with the r1 verifier, short and `--long`.
  - Gates are unchanged: 12 of 13 gated pass, G_HB FAIL, GCC FAIL (#112).
