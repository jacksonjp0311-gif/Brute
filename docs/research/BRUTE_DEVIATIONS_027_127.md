# Deviation #127 (study-027, v0.24.0): process events after the source freeze

Written after the run. Nothing here changes a gate, a threshold, a frozen file or a sealed result. Labels: Exact,
Observed, Inferred as in #126.

1. **First run_start ledger attempt failed before launch (Observed).** At 10:55:45 EDT the run_start_027 ledger append
   was given a directory as its artifact and raised FileNotFoundError; the shell chain stopped, so no ledger line was
   written and the runner was NOT launched (no process, no checkpoint; checked with pgrep and git status). The append was
   repeated with a file artifact (experiments/BRUTE_SOURCE_FREEZE_027.json, ledger d119d25) and the runner launched once,
   at about 10:55:50 EDT. This is not a relaunch: no run had started.
2. **Run completed without interruption (Observed).** 93/93 cases, runner wall 1454.3 s (cap 1800 s), normal exit; the
   snapshot pusher pushed 5 snapshots (24, 42, 60, 78, 93 cases) and stopped after the runner exited. The
   resume-after-reboot clause was never needed and remained NOT approved.
3. **Post-hoc diagnosis script (Exact; informational).** make_gates_027's `diagnosis_eps0` reads SCIENTIFIC.json, which
   drops the `*_informational` wall fields, so its `arm_wall_eps0` reports null and `query_max_eps0` reports 0. This is
   a reporting defect in a frozen script and is left as is. scripts/diagnose_027.py (new, written after the results were
   seen) reads the sealed RESULTS.json instead and writes results/study-027/DIAGNOSIS_027.json. It gates nothing.
4. **GAPI12 api_check run (Observed).** The first api_check_027 call ran under a 230 s tool timeout, was killed before
   writing anything, and left no file. It was started once more in the background under `timeout 1200` and not
   restarted after that. api_check is a scoring script, not the live run. It finished in 667.4 s with 6/6 cases
   equal (API_CHECK_027.json).
5. **S1 false certificates (Observed).** The recount finds F(S1) = 3 on main eps-0.02 cases: control_cycle3/9340001 (2)
   and scale16/9330006 (1). S1 has no noise model; clause d gates F for S2 and RGB6 only. This is published, not
   gated.
