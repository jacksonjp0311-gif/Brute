# Study-019 rate math (BRUTE_PLAN_019 stop_rule)

Written before the held-out run, using smoke seeds only. The numbers come from `scripts/rate_math_019.py` →
`RATE_MATH_019.json`. Inputs: the SMOKE=1 orchestrator dry run dry2 (commit ece6b32, after deviation #102) for transfer,
repro and g11, and the dry1 smoke GTI (904 s at 4 workers) for gti. Label: Simulated (a projection from smoke timings).

| stream | workers | budget (s) | raw (s) | x1.75 (s) | fill | fits (<= 0.8) |
|---|---|---|---|---|---|---|
| transfer | 4 | 2400 | 865.2 | 1514.2 | 0.631 | True |
| repro | 2 | 1800 | 388.0 | 679.1 | 0.377 | True |
| g11 | 2 | 1800 | 209.3 | 366.3 | 0.204 | True |
| gti | 4 | 4800 | 903.9 | 1581.8 | 0.33 | True |
critical path projected 2193.3 s; budget path 4800 s; fits True

No STREAMS budget changes are needed; `scripts/run_study_019.py` is unchanged. Kill drill (Observed): watchdog_019
fired at the 15 s cap, latency 0.03 s, no SIGKILL, no survivors, 12 checkpoint lines intact, heartbeat max gap 2.0 s.
The dry1 GTI verdict failed only because SMOKE=1 leaked into the GTI env (test_scripts_018 test_streams); see
`results/smoke-019/GTI_SMOKE_019.json`.
