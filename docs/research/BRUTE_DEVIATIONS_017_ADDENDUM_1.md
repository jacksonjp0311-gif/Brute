# Study-017 deviations, addendum 1 (#92-#95)

Written after implementation_017 and before the source freeze, the scoring freeze and run_start_017. No held-out seed
has been run. BRUTE_DEVIATIONS_017.md (#86-#91) is unchanged and stays in force. Evidence labels as in that file.

**#92 (deviation): g11 at 6 workers.** stop_rule.streams_and_budgets says g11 runs with 2 workers in 2400 s. From smoke
timings (RATE_MATH_017.md) the reference audit costs 30.4 s per main case; at 2 workers g11 is projected at 3.64x its
budget (with margin), at 4 (study-016 #76) at 1.82x. scripts/run_study_017.py sets G11_WORKERS = 6, the most the 8-worker
cap allows next to gti's 2; the scheduler therefore starts g11 only after repro finishes. Budget (2400 s), cap (7200 s),
the 8-worker maximum and every criterion are unchanged. Projected 0.81 of budget without margin, 1.21 with it: a
STUDY_BUDGET fail of GS_ref5 is possible and will be published. Label: Exact (change); Inferred (projection).

**#93 (clarification of #90): attribution class order.** #90 lists clock_step (|d_wall - d_monotonic| > 1 s) before
suspend (d_boottime - d_monotonic > 1 s). In a kernel suspend the wall clock and BOOTTIME both advance while MONOTONIC
stops, so the #90 order would label every suspend as a clock step. scripts/hb_attribution_017.py tests suspend first and
measures clock_step as |d_wall - d_boottime| > 1 s (d_monotonic when BOOTTIME is unavailable). box_pause,
watchdog_stall and unattributed are as in #90. Ungated; G_HB unchanged (<= 30 s). Label: Exact (rule); Inferred (classes).

**#94 (clarification): R_RGL lookahead timing source.** R_RGL reports lookahead cost per step. SCIENTIFIC.json strips every
`*_informational` key, so make_gates_017 reads `lookahead_wall_informational` from the unsealed transfer/RESULTS.json
(restored from gzip in the clean clone) and reports null with a reason if it is absent. Reported only. Label: Exact.

**#95 (clarification): GS_b5 clause 3 includes the switch step.** "The RGLX trajectory equals RSX's rule after RG4's first
certificate" is checked as: rglx.switch_step == RGLX4 first_cert_step + 1 (None if no certificate inside the case),
and every RGLX step at or after the switch takes rsx_choose's action and rule with no lookahead. Without the first part a
moved switch would pass. Label: Exact.
