# BRUTE deviations 020, addendum 1

Study BRUTE-0180-HORIZON-020. Written before the source freeze and before any held-out case was run. Every observation
here is from smoke seeds (8690001-030) only. No criterion, threshold, seed range, arm or metric changes. Deviation #103
(`BRUTE_DEVIATIONS_020.md`) is frozen and stays in force; this file adds #104.

## #104 Implementation and process notes (disclosure only)

1. **first_cert_step censor is inherited (informational, ungated).** `first_cert_step` uses the inherited
   `brute.soundtransfer.CENSOR = 45` (a 44-step-trace value) for SP8 in `experiments/brute_study_020.summary` and, inside
   the frozen study-018 `cert_arm`, for RG4 / RGN4 / RGNB4 / RGN4_or. On 88-step traces a value of 45 is ambiguous
   (first certificate at step 45, or none), and because the frozen `cert_arm` uses `first == CENSOR` as its "not yet"
   test, a first certificate at step 45 can be overwritten by a later one. The frozen code is not edited. The quantity
   is reported only (R_first_cert) and is used by no gate, no C metric and no CI (Exact, by reading `make_gates_020.py`
   and `make_paired_020.py`). Label for any first_cert_step number: Observed, censor-ambiguous.
2. **Stream allocation.** `scripts/run_study_020.STREAMS` is transfer 7 workers / 5400 s, gti 1 / 6000 s, repro
   5 / 1800 s, g11 2 / 1800 s: at most 8 worker processes at once (transfer + gti = 8, then gti + repro + g11 = 8) and
   transfer + max(repro, g11) = 7200 s = cap. The first draft (6 / 4500, 2 / 6000, 4 / 2400, 2 / 2400; earlier still,
   repro at 6, which broke the 8-worker invariant and was caught by `tests/test_scripts_020.py`) was changed after the
   rate math, before any freeze.
3. **Rate math does not fit (published, Simulated).** `docs/research/v0.18.0/RATE_MATH_020.{md,json}` from the SMOKE=1
   orchestrator dry run (/tmp/s20/dry). Under the inherited slowest-smoke-case rule x 1.75 with fill 0.8, no 8-worker
   allocation fits: the final allocation projects a 10,708 s critical path (transfer 8,543 s against 5,400 s). The plan
   fixes the cases and the stop rule fixes the response (hard cap, no extension, no rerun, incomplete gates FAIL with
   STUDY_BUDGET), so the study runs as frozen. A mean-cost estimate (Inferred) puts the path near 4,600 s.
4. **Kill drill.** `results/smoke-020/KILL_DRILL_020.json` (Observed, block smoke-drill): watchdog_020 fired at its 15 s
   cap. It ran while the dry run's GTI stream was still running, so that stream's smoke wall time includes about 15 s of
   extra load (Inferred: small next to its total).
5. **Version.** `pyproject.toml` stays at 0.17.0 through the study and becomes 0.18.0 in the release tooling commit (as
   in v0.17.0). `brute/release_version_0180.py` carries RELEASE_VERSION = '0.18.0' and is in the source freeze.
6. **Scoring reading of the plan** (fixed in `scripts/make_gates_020.py` before the scoring freeze):
   GLH_early_control "inside [0.04053, 0.065436]" is read as inclusive; G_HB uses the plan's 10 s limit (study-019 used
   30 s); GAPI8 is scored on certify/7 (its study-019 source-freeze hash, `tests/test_api_certify7_0170.py` inside GTI,
   its soundness dictionary, and the absence of `brute/api/certify8.py`), as #103 item 5 states. Smoke-probe prediction
   (Observed, 32 smoke cases, not evidence for the held-out result): C_early28(RGNB4, eps 0.02) is about 0.016, below
   the GLH_early_control interval, so that gate is expected to fail; it will be scored as written.
