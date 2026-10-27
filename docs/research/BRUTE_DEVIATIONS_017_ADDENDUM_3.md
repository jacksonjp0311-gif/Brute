# Study-017 deviations, addendum 3 (post-run disclosures, no rescoring)

Written after run_start_017, seal_017 (3e4f0e8) and gates_017 (911f06c). Nothing here changes a gate, a verdict or a
frozen file. BRUTE_DEVIATIONS_017.md (#86-#91), ADDENDUM_1 (#92-#95) and ADDENDUM_2 (#96) are unchanged and stay in force.

## D-g11: the second-implementation audit hit its stream budget (GS_ref5 FAIL)

- g11 started at 07:27:43 EDT (after repro, as #92 scheduled), 6 workers, and was stopped by the frozen 2400 s
  stream budget at 08:07:41 EDT with 308 of 432 cases audited, 0 mismatching, 124 not reached (Exact, from
  results/study-017/SECOND_IMPLEMENTATION_017.json). Not reached: 52 ood4 main cases and all 72 stress cases.
  The mutation check was not reached either.
- GS_ref5_reference_audit is scored FAIL as frozen. "0 mismatches in 308" is reported and is **not** a pass: 124
  cases are unaudited (Exact).
- Why the projection was wrong (Observed): the mean audit cost was 46.4 worker-seconds per case (14303.6 s across
  308 cases) against 27.0 projected in RATE_MATH_017 (11651 s / 432). That is 1.72x. Means per family and mask (s):
  cycle3 18.9/22.2/30.3, switch3 29.4/33.5/43.5, ood4 39.0/35.8/71.6, unaliased2 77.4/72.0/82.7 (mask 0.1/0.35/0.6).
  unaliased2 cost about 2.5x the projection. Inferred causes: the smoke rate was measured on fewer cases and without
  6-way contention next to gti (2 workers) and the heartbeat sentinel; ood4 at mask 0.6 and unaliased2 were
  under-represented in the smoke.
- RATE_MATH_017 already disclosed the risk (1.21 with margin, Inferred). The disclosed risk came true.
- The fix goes in BRUTE_PLAN_018 (stop_rule.g11_rate_projection); see docs/research/v0.16.0/PLAN_018.md.

## D-hb: heartbeat gaps line up with agent idle (G_HB FAIL)

- Two gaps: 425.668 s ending 07:52:20 EDT and 316.47 s ending 08:05:33 EDT; d_boot = d_mono; workers kept using CPU
  and checkpoints kept being written during gap 1 (Observed). hb_attribution classed both as "unattributed" (Exact).
- Both gaps ended within about 1 s of the operating agent's next tool call after a long blocking wait (timing
  Observed; cause Inferred: the host deschedules sleeping processes while the agent is idle). G_HB is scored FAIL as frozen.

## D-gti: GTI failed exactly as #96 predicted

- The only undeclared failure was test_scripts_017.Orchestrator017.test_streams (#96); 586 per-module = 586 plain
  (Exact, results/study-017/TEST_SUITE_017.json). GTI is scored FAIL as frozen.

## D-run: run-time

- RUN_DONE at 08:13:17 EDT, 3463 s after RUN_T0, inside the 7200 s cap; watchdog did not fire (Observed).
  G_RT clause (i) fails because g11 was stopped by its budget; kill drill 0.224 s (Exact).
