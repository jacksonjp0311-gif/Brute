# Study-020 rate math (BRUTE_PLAN_020 stop_rule)

Written before the held-out run, using smoke seeds only. Numbers come from `scripts/rate_math_020.py` →
`RATE_MATH_020.json`. Input: the SMOKE=1 orchestrator dry run /tmp/s20/dry (commit 2549157, started 11:11:12 EDT
2026-10-28, streams then transfer 6 / gti 2 / repro 4 / g11 2). Transfer 32 smoke cases in 290 s, repro 11 in 166 s,
g11 33 audited in 34 s, gti 1665 s (verdict passed, 724 = 724 tests, only declared failures). Label: Simulated.

**The rule-based projection does not fit (published as is).** Under the inherited rule (each held-out cell costed at
its SLOWEST smoke case, x 1.75, fill <= 0.8), no allocation of 8 workers fits the 7200 s cap: transfer alone needs
34,173 worker-s by the slowest-case rule, i.e. 4,272 s raw even at 8 workers, 7,475 s after x 1.75.

Final allocation (`scripts/run_study_020.STREAMS`, changed from the first draft before the source freeze):

| stream | workers | budget (s) | raw (s) | x1.75 (s) | fill | fits (<= 0.8) |
|---|---|---|---|---|---|---|
| transfer | 7 | 5400 | 4881.9 | 8543.4 | 1.582 | False |
| repro | 5 | 1800 | 1236.9 | 2164.6 | 1.203 | False |
| g11 | 2 | 1800 | 346.1 | 605.7 | 0.337 | True |
| gti | 1 | 6000 | 3231.8 | 5655.6 | 0.943 | False |

critical path projected 10708.0 s; budget path 7200 s (= cap); fits False.

First draft (transfer 6 / 4500, gti 2 / 6000, repro 4 / 2400, g11 2 / 2400): transfer 5695.6 raw / 9967.3 projected,
repro 1546.2 / 2705.8, g11 346.1 / 605.7, gti 1615.9 / 2827.8; critical path 12673.1 s; fits False.

**Why run anyway, and what to expect (Inferred).** The plan fixes the case counts; the stop rule (hard cap, no extension,
no rerun, incomplete gates FAIL with STUDY_BUDGET) is the pre-registered answer to an over-run, and study-019's rule
over-projected actual cost by 1.5-3.1x. The MEAN smoke case cost gives 23,908 worker-s for transfer, about 3,415 s at
7 workers (budget 5400 s = 1.58x that), then repro at 5 workers about 1,200 s; gti at 1 worker about 3,200 s from t0.
That mean-based path (about 4,600 s) fits the cap, but with 2 smoke cases per cell the tail is poorly measured. The
allocation moves workers from gti (off the critical path) to transfer and repro and gives transfer the largest budget
the cap allows. If a stream hits its budget or the cap, the affected gates fail and are published.

Kill drill (Observed): `results/smoke-020/KILL_DRILL_020.json` — watchdog_020 fired at its 15 s cap, kill latency
0.017 s, no SIGKILL, no survivors, 3 checkpoint lines intact, heartbeat max gap 2.004 s.
