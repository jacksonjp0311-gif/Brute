# Study-010 (v0.8.0) deviations and disclosures

Numbering continues from study-009 (#26). Each item says what differs from the frozen plan (`experiments/BRUTE_PLAN_010.json`, commit 881f0a6) or what the plan left open and how it was decided before data. Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

**#27: source freeze list.** `BRUTE_SOURCE_FREEZE_010.json` also freezes `tests/test_run_tests_080.py`, `tests/test_v080_xcheck.py` and `tests/test_diag_stale_010.py`, which the plan's freeze_rule list does not name. `scripts/verify_release_080.py` and `tests/test_release_080.py` are in that list but are written at release, after the run. They descend from 881f0a6 but are not frozen before the run. (Exact)

**#28: the watchdog was changed after a kill drill.** In smoke-2 (seeds 3190025-30, cap 20 s), the orchestrator started `repro_breadth` at t0 + 18 s. That was after the watchdog's last 2 s read of RUN_STATE, so the stream was never killed and finished at t0 + 26.4 s (Observed). Fix, made before the source freeze (commit 438a496):
- At the deadline the watchdog SIGSTOPs the orchestrator, re-reads the state, and adds the process group of every descendant (found through the /proc ppid chain).
- The orchestrator writes RUN_STATE immediately after each start.
- A unit test now covers an untracked child.

The re-drill (smoke-3) killed all 8 groups in 0.239 s, with no SIGKILL and no survivors (Observed). The held-out runner was therefore changed after a smoke result. This is a harness change, not a learner change.

**#29: G_RT (iii) evidence.** The drill latency is taken from the smoke-3 drill. Its STOP_010.json is copied verbatim to `results/study-010/KILL_DRILL_010.json` before run_start. The held-out run itself is not killed on purpose. (Exact)

**#30: scoring readings fixed in `scripts/make_gates_010.py` before data.** Its docstring holds the full list. The main ones:
- **GD:** INSUFFICIENT_EVENTS is a FAIL. A missing hull_union counts as a clause (ii) exception.
- **G7:** the min-probability floor applies to the production arms J8, SP8 and BSP8. SC7, A4, B5 and BSC7 are reported.
- **G11 (iv):** passes when `mandatory_done.wall_since_start` is ≤ 1500 s and the g11 stream was not stopped by the cap or an error. A budget stop of the rest phase after mandatory_done is allowed.
- **G_RT (i):** fails if any stream was stopped for any reason, its own budget included.
- **G_RT (ii):** the last heartbeat must be within 10 s of the run end.
- **GX2 (iii):** fails if gx2_sym is stopped for any reason.

**#31: mutation test scope.** The 20 injections are drawn from the 2x2 mandatory traces only (J8, SP8, SC7). Breadth has no mutation test. That matches the plan's (iii), which names J8 and SP8 fields. Injected fields are counted from a per-step trace diff, which merges the taken action's forecast certificate and status. (Exact)

**#32: implementation readings.**
- At T=0 the jump hull equals Y1k.
- An UNKNOWN solver result in the jump hull gives all codes.
- hull_union is recorded after the predicts and never changes a forecast.
- The LU-C non-calm branch is LU-R.
- The spot truncation restricts end-of-trace fields to the 24-step prefix.
- Kill latency is measured until every tracked pid is gone.

(Inferred: each is the natural reading of the plan text.)
