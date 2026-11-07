# Deviation #216: study 076 (BRUTE-0720-GUARD-076), post-run disclosure

Written 2026-11-07 at about 08:28 EST by Grok Bot (Brute executor). The agent drafted this note; James has not reviewed it. All times are America/New_York (EST, UTC-5). Standing go t143s742, t133s553, t139s684.

1. **Main parent process died after 1 of 50 jobs; sealed post-mortem from persisted jobs/.** Ledger `run_start_076` `aafa2ea` / HANDOFF `a36aac6`; main launched once ~08:21 EST. First job `KR:12760101:C3` finished IDF at 08:22:39 (~68 s, wall_guard_case_s=900, wall_guard events=0). By ~08:26 EST no `brute_study_076` process remained; `RESULTS`/`SEAL` were never written by the runner. dmesg around box lifetime showed virtio TX timeout and `crng reseeded due to virtual machine fork`. **No relaunch.** Post-mortem seal recovered **1** JSON from `results/study-076/main/jobs/` (the plan-076 persistence path); `complete=false`, `missing_job_keys`=49.

2. **Measurement fix observed on the recovered record.** The recovered C3 record has `wall_guard_case_s=900.0` and `wall_guard=0` (guard did not fire). That is the intended contrast with study 075's inherited `GUARD_CASE_S=600` IDU walls. It does **not** certify the headline (1 of 20 cells sealed).

3. **Recount.** 1 sealed record, label IDF, 0 WRONG. Gates: GLIVE76 fails; data gates `INCOMPLETE_INPUT` by the incomplete rule (including GGUARD76 despite the recovered record matching 900).

4. **What this does not show.** Full 50-job outcome at wall_guard 900; whether 900 s decides more loose-N cells than 420 s; that the parent-death root cause is fixed. Next plan should make the runner **resume-safe**: skip keys that already have `jobs/*.json`, allow one orchestrator restart to finish missing keys only (never re-run finished), then seal — so a VM/box kill does not waste the version.
