# Study-021 rate math (BRUTE_PLAN_021 stop_rule)

Written before the held-out run, from smoke seeds only. Numbers come from `scripts/rate_math_021.py` →
`RATE_MATH_021.json`. Input: the SMOKE=1 orchestrator dry run /tmp/s21/dry (started 14:49:15 EDT 2026-10-28 at HEAD
4d4c9c2, streams as frozen in `scripts/run_study_021.STREAMS`: transfer 7 / gti 1 from t0, then repro 6 / g11 1).
Observed: transfer 32 smoke cases in 314 s, g11 33 audited in 70 s, repro 11 in 164 s, gti 3636 s (verdict passed,
776 = 776 tests, only declared K failures). RUN_DONE 3636 s after t0. Label: Simulated (projection), Observed (dry-run walls).

**The rule-based projection does not fit (published as is).** Under the inherited rule (each held-out cell costed at its
SLOWEST smoke case, x 1.75, fill <= 0.8):

| stream | workers | budget (s) | mean path (s) | slowest raw (s) | x1.75 (s) | fill | fits (<= 0.8) |
|---|---|---|---|---|---|---|---|
| transfer | 7 | 5800 | 4105.5 | 5113.5 | 8948.6 | 1.543 | False |
| repro | 6 | 1400 | 334.4 | 443.1 | 775.4 | 0.554 | True |
| g11 | 1 | 1400 | 759.4 | 777.5 | 1360.6 | 0.972 | False |
| gti | 1 | 6400 | 3589.2 | 3589.2 | 6281.1 | 0.981 | False |

Critical path projected 10309.2 s; mean path 4864.9 s; budget path 7200 s (= cap); max 8 workers at once; fits False.

**Why run anyway, and what to expect (Inferred).** As in study-020, the plan fixes the case counts and the stop rule
(hard 7200 s cap, no extension, no rerun, incomplete gates FAIL with STUDY_BUDGET) is the pre-registered answer to an
over-run. Study-020's slowest-case rule also did not fit and the run completed inside the cap. The mean-based path
(transfer about 4,100 s, then g11 about 760 s; gti about 3,600 s alongside) is about 4,900 s and fits. The tightest
stream on the mean path is transfer (budget 5800 s = 1.41x its mean path). The allocation is unchanged from the runner
commit. If a stream hits its budget or the cap, the affected gates fail and are published.

Dry-run gates (smoke, Observed): G_recount, GAH_prefix_control, GS_a9, GS_ref9, GAPI9, G10, G13, G_RD, G_RT, G_HB passed.
GAH_anytime / GAH_frozen_control / G12 are INCOMPLETE_INPUT by design in a smoke dry run (paired and reproducibility
outputs are print-only with --smoke). GTI failed only clause "tracked tree clean at GTI start": the dry run started at
4d4c9c2 before the drills commit df915e5, with scripts/hbsentinel_021.py and scripts/make_freeze_021.py edited in the
tree. The main run starts from a clean committed tree.

Drills (Observed): `results/smoke-021/KILL_DRILL_021.json` (kill latency 0.224 s, no SIGKILL, no survivors, 3 checkpoint
lines intact, heartbeat max gap 2.003 s); `results/smoke-021/RESUME_DRILL_021.json` (SIGKILL at 45 s, relaunch once, all 4
clauses true, per-case canonical JSON identical to the uninterrupted reference).
