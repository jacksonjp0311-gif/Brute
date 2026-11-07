# Brute v0.72.0 → v0.73.0: next iteration

Previous: v0.72.0 study-076 (NOT CERTIFIED, 4/16). Measurement fix `wall_guard_case_s=900` verified on the one recovered record; parent died after 1/50 (deviation #216).

## Locked direction for v0.73.0 (plan 077)

**Resume-safe orchestrator (process fix), keep measurement fix:** same certify/34h + wall_guard_case_s=JOB_KILL_S=900; skip keys that already have `jobs/*.json`; allow **one** orchestrator restart to finish missing keys only (never re-run finished jobs); seal from jobs/. Fresh seeds. Gate thresholds unchanged. Standing go t143s742, t133s553, t139s684.
