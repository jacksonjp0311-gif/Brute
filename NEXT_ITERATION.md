# Brute v0.71.0 → v0.72.0: next iteration

Previous: v0.71.0 study-075 (NOT CERTIFIED, 4/15). Same certify/34h; plan raised JOB_KILL 420→900 s. **Incomplete:** host reboot lost all per-job records (0/50 sealed). Separately, inherited `GUARD_CASE_S=600` meant the 900 s question was never the effective engine wall (deviation #215).

## Locked direction for v0.72.0 (plan 076) — draft until LOCKED

**Measurement fix, not another pure wall bump:** keep certify/34h; construct it with an explicit `wall_guard_case_s` equal to the runner `JOB_KILL_S` (900 s), so the outer kill and the inherited 16d case guard agree. Disclose in the plan that study 075 did not apply 900 s. Gate or record that the configured guard matches the plan. Same targets/seeds pattern as 075 with fresh seeds; thresholds unchanged (6/20 cells, ≥3 targets, held-out ≥1). Prefer this honest re-test of the timeout-vs-algorithm question over raising the clock again without fixing the guard. Standing go t143s742, t133s553, t139s684.
