# Study-012 rate math (before the source freeze)

BRUTE_PLAN_012 stop_rule.rate_math: turn the smoke timings into a projected wall time per stream before the source
freeze. If a mandatory stream projects above 70% of its budget, the budget/worker split, the big78 count or the optional
list may be changed ONCE, as a disclosed deviation. Nothing changes after run_start.

Timings are from the shared 8-CPU box (Observed). Projections are Inferred. Streams at t0: 2x2 (3 workers), big78 (2),
transfer (1), gti (2) = 8 workers; repro (2) and g11 (2) start when 2x2 (and, for g11, transfer) finish.

| stream | measurement (Observed) | projection (Inferred) | budget | share |
|---|---|---|---|---|
| 2x2 (3 w, mandatory) | smoke 16 cases: 1.59 s CPU per case (J10 0.50, J9 0.52, SP8 0.45, A4/A2 0.06); study-011 2x2 spent 304 s with 4 workers for 4 arms | 792 x 1.59 / 3 = 420 s; ~530 s under contention | 2400 s | ~22% |
| big78 (2 w, mandatory) | smoke1 4 cases, case wall (J10_78 + SP8_78): 31.4, 5.9, 2.5, 36.0 s (mean 18.9 s; J10_78 9.7, SP8_78 9.2 per arm); 6 timed smoke cases incl. 2 scratch timings: mean 19.3 s | 144 x 19.3 / 2 = 1390 s | 1800 s (frozen) | **~77%** |
| transfer (1 w, mandatory) | smoke 8 cases: case wall mean 0.63 s (SP8 0.62 s; library learning and TRp/TRn tracking ~0.001 s each) | 288 x 0.63 = 181 s | 1200 s | ~15% |
| gti (2 w, mandatory) | GTI smoke at 1c43d68 (08:32-08:51 EDT, idle box): 1149 s wall, 359 tests (results/study-012/GTI_SMOKE_012.json); study-011 gti spent 1165 s under run load | ~1200-1400 s | 2400 s | ~50-58% |
| repro (2 w, after 2x2) | 264 2x2 + 96 transfer cases at the rates above | ~215 s with contention | 1200 s | ~18% |
| g11 (2 w, after 2x2 + transfer) | smoke: mandatory_done at 2.1 s / 32 traces; seen-data timing (EXPLORATORY, 27 study-011 cases, scratch only): reference audit J10 mean 6.37 s per trace (max 74.8 s, drift4 4080002), SP8 3.26 s. J10/SP8 = 2.0 = the study-011 J9/SP8 ratio, so the study-011 g11 mandatory time (694.7 s) carries over | mandatory ~695 s + transfer audit (seconds) + optional ~105 s = ~800 s | 1500 s | ~53% (mandatory ~46%) |

Critical path (Inferred): max(2x2 + max(repro, g11), big78, gti) ~ 1330-1400 s, about 20% of the 7200 s cap.

## Decision (deviation #49)

big78 is mandatory and projects ~77% of its frozen 1800 s budget, above the 70% trigger. The single permitted change is
used: **big78 stream budget 1800 s -> 2700 s** (projected ~51%). The sample (48 seeds x 3 masks = 144 cases), workers
(2) and every other budget are unchanged; big78 runs in parallel at t0, so the change cannot push any other stream past
the cap (Inferred). Exact: scripts/run_study_012.py budgets equal stop_rule.streams_and_budgets except big78 = 2700.

Tail risk (Inferred): mask 0.10 and 0.60 were not timed; if the masked cases were 2x slower the projection would be
~2000 s, still inside 2700 s.

## What the smokes showed (Observed, smoke seeds only)

- **big78: 0 certificates.** J10_78 and SP8_78 issued 0 certificates on all 6 timed big78 smoke cases (44 steps,
  mask 0.35). At a state bound of 8 the region stays too unconstrained in 44 steps for any forecast to be unique.
  G78_soundness is therefore expected to pass vacuously (power 'VACUOUS' is reported by make_gates_012).
- **Transfer.** TRp certified earlier than SP8 on 7 of 8 smoke targets (S histogram 0,1,10,12,13,21,23,36) with 0 false
  certificates. TRn issued 4 false certificates on 2 of 8 smoke targets (all transfer-rule, before the wrong library was
  eliminated) and certified earlier than SP8 on 2 of 8. This matches the exploratory seen-data diagnostic (TRn 246 false
  before elimination). GT_a / GT_c are therefore at risk; the rule is frozen as pre-registered and the result will be
  reported as observed.
- **g11 smoke:** 32/32 mandatory traces, 0 mismatches; mutation 20/20 (J10 cert/hull 5, action 7); transfer audit 8/8,
  0 mismatches; stamp optional_done.
- **Kill drill** (08:27:26 EDT, cap 20 s): watchdog fired 0.002 s after the deadline, 6 process groups stopped, kill
  latency 0.257 s, no SIGKILL, no survivors, no heartbeat gaps (results/study-012/KILL_DRILL_012.json).
- **GTI smoke** (Observed, 1c43d68, clean tree): 359 tests, counts match plain discover, frozen files unchanged, new
  tests (test_seeds_012, test_study_012, test_v0100_reference) all pass, test_study_005 6/6. Verdict FAIL on clause (i):
  6 undeclared failures, test_brute_repro.test_manifest_matches_tracked_files and the release_080 / release_090 verify
  tests. Cause (Inferred): MANIFEST.sha256 was stale (commits 2564201 and 1c43d68 were not yet manifested). The
  held-out run starts after make_manifest on a committed tree; this is re-checked before run_start.
