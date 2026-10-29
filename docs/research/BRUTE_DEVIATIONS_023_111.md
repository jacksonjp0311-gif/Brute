# Study-023 deviations #111 (false-start orchestrator) and the run outcome (written after run_end)

## #111: the first orchestrator start read leftover dry-run settings and ran nothing

**Evidence (Exact).** These are the first lines of `results/study-023/RUN_023.log`. The file is git-ignored, as RUN_021.log
was, but its sha256 is listed in `results/study-023/SEAL.json`:

```
[2026-10-28T20:45:20-0400] orchestrator start pid 320375; cap 7200 s, deadline 2026-10-28T21:24:41-0400
[2026-10-28T20:45:20-0400] RUN_DONE (4840 s since t0; stopped streams: {})
[2026-10-28T20:46:01-0400] orchestrator start pid 320690; cap 7200 s, deadline 2026-10-28T22:45:20-0400
```

**Cause (Exact).**
- The launching shell still held `SMOKE=1` and `STUDY_DIR_023=/tmp/s23/dry`, left over from the pre-freeze orchestrator
  dry run.
- `run_study_023.py` honours those dry-run hooks, so pid 320375 resolved its study directory to `/tmp/s23/dry`.
- It read that directory's RUN_T0, 1793229881.23 (19:24:41 EDT). That gives the stale deadline of 21:24:41, which is
  19:24:41 plus 7200 s.
- It found the dry run's completed streams and logged RUN_DONE at 4840 s, which is 20:45:20 minus 19:24:41 EDT.
- It exited in the same second. It rewrote only scratch files in `/tmp/s23/dry`, which is not tracked.

**What the false start did not affect (Observed).**
- It computed no held-out case. Nobody saw any held-out output.
- Watchdog_023 (pid 320373) uses literal study paths, and hbsentinel_023 (pid 320374) was given
  `--dir results/study-023`. Both supervised the real directory from 20:45:20 and ran for the whole run.
- `results/study-023/RUN_T0` (1793234720.68, 20:45:20 EDT) was written by launch.sh. It was never rewritten.

**Remedy (Exact).**
- At 20:46:01 EDT the orchestrator was relaunched once with `env -u SMOKE -u STUDY_DIR_023 ...`.
- It used the same RUN_T0 and the same deadline, 22:45:20 EDT. The cap was not extended.
- Transfer and gti started from empty checkpoints. Under the plan this is a restart, not a rerun, because no held-out
  work had been done.

**Does the 41 s matter for the cap? (Exact.)**
- The 41 s counted against the cap, because the cap is measured from RUN_T0 and not from the relaunch.
- RUN_DONE came at 22:12:21 EDT, 5221 s after RUN_T0, with no stream stopped.
- That left 1979 s of the 7200 s cap. So the loss changed no stop-rule outcome and no gate. G_RT clause (i) is measured
  from RUN_T0 and passes.

**Process fix for v0.21.0.**
- The launcher must refuse to start if any dry-run hook is set: SMOKE, STUDY_DIR_*, CAP_S, BUDGET_S, LIMIT, SKIP_GTI or
  BRUTE_SMOKE_DRILL.
- The orchestrator must log the resolved study directory on its first line.

## Run outcome (Exact, from GATES_023.json)

**Gated: 12 pass, 1 fails.**
- Pass: G_recount, GLR, GLR_lemma, GAS_frozen_control, GS_a10, GS_ref10, GAPI10, G10, G12, G13, GTI, G_RT.
- Fail: **G_HB**. The rule is a maximum watchdog heartbeat gap of 10 s or less. Observed: 2511 beats, maximum gap
  47.558 s, 6 gaps over 10 s.

**G_HB attribution.** HEARTBEAT_ATTRIBUTION_023.json classes the 6 gaps as clock_step 4 and unattributed 2; it is a
diagnostic and changes no verdict. A host or VM pause is the likely cause (Inferred). The dry run showed the same pattern
(#110 doc). Per the plan, the failure is published and G_HB is not re-scored, relaxed or rerun.
