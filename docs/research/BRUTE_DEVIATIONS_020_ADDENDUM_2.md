# Study-020 deviations, addendum 2: box restart during the held-out run (#105)

Written 2026-10-28 ~12:40 EDT, before the orchestrator is restarted. Nothing frozen is edited. Deviation numbering
continues after #104.

## #105 Run interrupted by a box restart; resumed under the frozen resume rule

1. **What happened (Observed).** The held-out run started at RUN_T0 11:51:38 EDT (ledger run_start_020, `2d3351b`).
   The orchestrator (pid 2222187), its transfer and gti stream process groups, `watchdog_020` (pid 2222161) and
   `hbsentinel_020` (pid 2222162) all died when the box restarted. The last records that survived are
   `HEARTBEAT_020.jsonl` wall 1793204382.2 (12:19:42 EDT, 1683 s after RUN_T0) and `RUN_STATE_020.json` heartbeat
   1793204382.6. At 12:35 EDT `uptime` was 15 min, all files in `results/study-020` had the same mtime 12:26:38 EDT,
   and `/tmp` was empty of the operator scratch (Inferred: the box was restored from a disk snapshot taken at about
   12:19:42 EDT). The operator had read 287 transfer checkpoint lines at 12:20:58 EDT; 276 lines survive, all of them
   parse (no torn line). The 11 lost lines are cases that will be recomputed with the same seeds; the study is
   deterministic per case (G12 tests this). `PROGRESS_020.json` (elapsed 361 s) is the single read-only projection the
   orchestrator writes at t0 + 360 s; it is not the last sign of life.
2. **Rule applied (Exact, frozen text).** `scripts/run_study_020.py` (BRUTE_SOURCE_FREEZE_020): "The 2 h cap is
   measured from RUN_T0 and is never extended; a restarted orchestrator resumes every stream from its checkpoint and
   charges each stream budget with the time already spent (RUN_STATE_020.json)." Plan stop_rule: no extension, no
   rerun; gates with incomplete inputs at the cap FAIL (STUDY_BUDGET). The restart is the same held-out run (plan
   process_controls "one held-out run"); no seed, case list, budget, worker count or design changes.
3. **Accounting (Exact by the frozen code).** RUN_T0 is unchanged, so the deadline stays 13:51:38 EDT. The dead time
   (12:19:42 to the restart, about 21 min) counts against the 2 h cap (wall clock from RUN_T0) but is not charged to
   any stream budget: `reap_orphans` charges transfer and gti `heartbeat - since` = 1683 s each. transfer resumes from
   its 276 checkpointed cases; gti has no case checkpoint, so its stream restarts the whole suite (frozen
   `run_tests_0180`) with 6000 - 1683 = 4317 s of budget left; repro and g11 have not started.
4. **Gates this affects (predicted before the restart, Inferred).** G_HB_heartbeat_gap (max gap <= 10 s) will FAIL:
   the heartbeat has a gap of about 1300 s or more across the restart. It is published as FAIL; hb_attribution_020
   will report the gap. G_RT_study_runtime is scored as frozen ("held-out run within the 2 h cap"). If a stream does
   not finish by 13:51:38 EDT, it is sealed as it is and its gates FAIL (STUDY_BUDGET).
5. **Operator change (process only).** The orchestrator, watchdog and sentinel are relaunched with `nohup setsid`, as
   the frozen docstrings prescribe, from a launch script on persistent disk. The kill drill and the first launch used the
   same commands; the launch script was in `/tmp` and was lost in the restart.
6. **Lost operator scratch.** The restart also removed `/tmp/wt-state` and the operator's draft release tooling in
   `/tmp/s20`. Neither is a study input. The `brute-bridge` worktree (`/workspace/brute-bridge`, `bridge/v0.2` at
   `cced586`) survived unchanged.
7. **Python environment rebuilt (Observed).** The restart also removed `/workspace/bgr/venv` (the box venv named in
   HANDOFF). It was recreated at the same path from the repository pins: `python3 -m venv` (CPython 3.13.5) plus
   `requirements.txt` (numpy 2.5.4, python-sat 1.9.dev17) and `requirements-gmc.txt` (pyganak 2.8.0, pyapproxmc
   4.4.0). Equivalence check before the restart (Observed, 2 cases): main/unaliased2/8630010 at eps 0.02 and 0.01
   re-run from scratch in the new venv are identical to their pre-restart checkpoint records (timing keys stripped,
   `make_reproducibility_020._canon`). G12 and GLV test the rest after the run.
