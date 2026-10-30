# Deviation #126 (study-027, v0.24.0): implementation details fixed before the source freeze

Written after the code and one smoke run (seeds 9390001-9390011, written to a scratch directory outside results/) and
**before** `source_freeze_027` and `run_start_027`. No target-range seed has been run. Nothing here changes a GSC
threshold, a gated budget, a family, a seed or the case count of BRUTE_PLAN_027; it records how the frozen code
realises the plan's new items. Deviation #123 definitions and #124 items 1-8 carry over unchanged. Labels: Exact = holds
by construction of the code; Observed = seen in the smoke only (not gated evidence); Inferred = projection.

1. **Reused frozen arms (Exact).** experiments/brute_study_027.py imports the frozen study-026 arms (S1, S2, RGB6),
   truth, identify and clause-a code from experiments/brute_study_026.py and experiments/worlds_026.py; those files
   stay covered by BRUTE_SOURCE_FREEZE_026 and are re-checked by check_freeze. Case schema brute.case.v24_0.
2. **S2_tight scope and budget (Exact; informational only).** S2_tight is ScaleRegion with n_max equal to the true
   state count n (8, 12 or 16; control 3), the same 10 s query budget, an arm budget of 25 s and a 10 s identify. It runs
   on eps-0 main cases only (42 cases), never in stress, and is never gated. At scale16 n_max is 16 for both S2 and
   S2_tight, so there S2_tight differs from S2 only in its shorter arm budget; the cap contrast is informative at
   scale8 and scale12 only.
3. **Dispatch order (Exact).** Jobs are sorted stably by family rank: control_cycle3, scale8, stress, scale12,
   scale16 (93 jobs, 8 workers). This changes no case's inputs.
4. **U split and diagnosis reports (Exact; informational).** make_gates_027 adds `diagnosis_eps0`: per arm (S1, S2,
   S2_tight) and family, X and U with Wilson 95% CIs, the UNKNOWN split into not_run (unk -1, arm deadline) and
   solver_unknown (unk >= 1, query budget), steps done, certificates, ID, the final proven lower bound n_lo, solver
   calls, mean arm wall and max query time. These feed the v0.25.0 bottleneck diagnosis; none is gated.
5. **Durable checkpoint (Exact).** scripts/push_checkpoint_027.py is a separate host process. Every 300 s while the
   runner PID is alive (and once after it exits) it writes the complete lines of main/CHECKPOINT.jsonl to a
   deterministic gzip, results/study-027/snapshots/ckpt_snapshot.jsonl.gz, commits only that path and pushes the branch
   without force under env -u GITHUB_TOKEN -u GH_TOKEN. Snapshot commits carry no ledger entry; the operator makes no
   other git operation while the run is live.
6. **Interruption rule (Exact).** The resume-after-reboot clause of the plan was NOT approved before the run. The
   existing rule applies: never relaunch; on interruption, seal what exists with `--seal-partial` (merging a restored
   pushed snapshot with `--snapshot` if the local checkpoint is shorter; overlapping cases must be byte-identical in
   content), and every data gate fails INCOMPLETE_INPUT. The runner refuses to start on a non-empty main checkpoint.
7. **Smoke range and G_PROC order (Exact).** Smoke seeds are 9390001-9390030 (11 used). G_PROC order is
   preregistration_027 < build_authorization_027 < seedcheck_027 < source_freeze_027 < run_start_027 (no s2_code step:
   the S2 code is unchanged from v0.23.0).
8. **Release tooling inside the source freeze (Exact).** study027_storage, verify_release_0240, test_release_0240 and
   release_version_0240 are frozen with the source, so there is no separate release freeze. Raw RESULTS.json and
   SCIENTIFIC.json are git-ignored and committed as deterministic .json.gz bound to the block SEAL; CHECKPOINT files
   are git-ignored.
9. **GS_ref12 mutation seed (Exact).** run_reference_027 is run_reference_026 with mutation seed 240 (026 used 230).
10. **GAPI12 unchanged-API check (Exact).** certify.py ... certify12.py (11 files) must be unchanged against the 026
    freeze.
11. **Smoke timing and projection (Observed / Inferred).** Smoke case walls: scale8 eps0 54 s, scale12 eps0 140 s,
    scale16 eps0 145 s (each including S2_tight 25 s + identify), control eps0 36 s, eps > 0 cases 117-135 s.
    Projected total for 93 cases on 8 workers: about 1350 s of packed work plus a tail, about 1450-1500 s (Inferred),
    below the 1700 s cut line, so stress is kept. In the smoke S2_tight did not reach full steps at scale12 or
    scale16 within 25 s, and S2 hit the solver budget on 1 query at scale12 and scale16 while most UNKNOWNs were
    not_run (Observed, one case each).
