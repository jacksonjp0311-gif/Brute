# Deviation #116: a new declared known failure, K_0200_113, in the study-024 GTI runner (v0.21.0)

Label: **Observed** for the failing run, **Exact** for the rule. Declared before the study-024 source freeze.

- **What was observed (2026-10-29, about 04:20 EDT).** Run in the current tree,
  `python -m unittest tests.test_release_0200 tests.test_release_0200_r1` gives 11 tests and one error:
  `test_release_0200.Release0200.test_short_verify_passes` raises
  `VerificationError: reference_1 and implementation_0 are the same commit`. Every test in `test_release_0200_r1` passes.
- **Cause (Exact).** This is deviation #113. The frozen v0.20.0 verifier rejects the dual-role commit `9e0ca70`, and
  `tests/test_release_0200.py` is frozen and calls it. The test fails by design, and it fails on a clean worktree of
  tag v0.20.0 as well. So the usual clean-tag K pattern (the test must pass at its own tag) cannot cover it.
- **Rule (Exact, `scripts/run_tests_0210.py`).** GTI clause i allows this one test id to fail, and only when both of
  these hold in the same GTI run:
  1. its failure text contains the #113 message;
  2. every test in `tests/test_release_0200_r1.py` passes.

  Any other `test_release_0200` failure stays undeclared, and the gate FAILs on it. Unit tests are in
  `tests/test_scripts_024.py`, RunTests0210.test_k0200_113.
- **What this is not.** It does not loosen G_HB (K_0200 in the plan) or any other gate. The frozen K list from
  run_tests_0200 is unchanged.
- **Why disclose.** BRUTE_PLAN_024 GTI lists only "release tooling after run_end". A new K entry is a change to how the
  carried GTI rule is applied, so it is published here, before the freeze, rather than found after the run.
