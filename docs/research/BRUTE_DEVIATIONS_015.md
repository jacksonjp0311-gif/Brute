# Study-015 (v0.13.0) deviations and disclosures

Numbering continues project-wide. Study-014 ended at #63 (docs/research/BRUTE_DEVIATIONS_014_ADDENDUM.md).
Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open. All entries below were written before the
source freeze and before any study run.

**#64: RSX on unavailable or singleton supports.** transfer_definition.RSX_trajectory says "argmax over b of
|bounded_support[4][b]|; ties by the SP8 LU-R choice, then the lower index; if every size == 1, the SP8 choice". It does
not say what a None support (region not 'supported') counts as, or what happens when the sizes are {0, 1}. The
implementation counts None as size 0 and uses the SP8 choice whenever max size <= 1. With two actions a tie between the
maximisers is k_0 == k_1, so the "lower index" tie-break is never reached. Exact: brute/regionsplit.rsx_choose and
experiments/v0130_reference.rsx_choice agree on every (step, k_0, k_1, sp8_action) in tests/test_regionsplit_015.

**#65: reference amendment before the core existed.** The first v0130_reference commit (f95a176) recomputed the RSX
sizes from the exact enumeration. The plan counts UNKNOWN codes as possible, so a budget-limited (unknown > 0) support
can be a strict superset of the exact one, and the exact sizes would flag a correct trajectory. Commit 305b739 (ledger
8122531) takes the sizes from the recorded n = 4 RSX supports, which audit_bounded checks against enumeration (equal
where unknown == 0, superset otherwise). Both commits precede brute/regionsplit.py and brute/api/certify3.py (Exact:
git log).

**#66: no tau7 in plan 015.** The 014 runner asserted plan['tau7']; plan 015 has no tau7 and no arm uses it.
experiments/brute_common_015.learner_plan asserts tau6, burn_in, actions per case and mask rates equal to plan 013; the
runner asserts tau6 == 1.645215321642 and that tau7 is absent.

**#67: EB "region non-empty".** n_E = min{n in 1..4 : the RegionSpace(n) support for action 0 is not None}. A region
whose status is 'budget_exhausted' (feasibility UNKNOWN) reports None and counts as empty, which can only raise n_E
(a tighter-looking but larger bound, not a looser one). Identical in brute/regionsplit and v0130_reference.

**#68: certify/3 suggest_action argument.** api_definition writes suggest_action() and suggest3(observations, actions).
SP8's LU-R choice needs the host's default (passive) action as its tie-break, so the implementation takes an optional
default_action=0 (suggest3 takes it as an optional third argument). With the argument omitted the plan's signatures
work unchanged. Exact: tests/test_api_certify3_0130 (ii) passes the study's passive action and reproduces every RSX
action on two smoke-api cases.

**#69: smoke-transfer layout.** The smoke-transfer block runs 8190001-8190008 (two per family) and the ood5 smoke
targets 8190016-8190017 (10 jobs), so the smoke dry run exercises the ood5 path of the single transfer stream.

**#70: transfer stream = main + ood5 in one job list.** jobs_for('transfer') lists the 288 main jobs then the 72 ood5
jobs; the repro selection index % 3 == 0 over this list gives 96 main + 24 ood5 = 120 jobs, as G12 requires (Exact:
tests/test_study_015.test_jobs).

**#71: watchdog_015 = frozen watchdog_014 bytes with study path tokens substituted at import (step 4).** watchdog_014 writes its file names as literals (`RUN_STATE_014.json`, `HEARTBEAT_014.jsonl`, `STOP_014.json`, `RUN_DONE_014.json`, `results/study-014`), so a wrapper cannot redirect them by passing a directory alone. `scripts/watchdog_015.py` reads `scripts/watchdog_014.py`, refuses unless its sha256 equals the BRUTE_SOURCE_FREEZE_014 digest (972a7fc6…), replaces only `_014`→`_015` and `study-014`→`study-015`, and executes that text as the module. No logic line changes; the frozen file is not edited. Effect on gates: none (G_HB / G_RT read HEARTBEAT_015 / STOP_015). Label: Exact (sha256 asserted at import).

**#72: g11 reference stream at 4 workers (rate math, before the source freeze).** The plan registers g11 at 2 workers /
2,400 s. RATE_MATH_015 projects 1,501 s (63%) uncontended and 2,252 s (94%) at x1.5 contention, above the plan's 70%
line. Using the plan's single allowed budget / worker change, g11 runs with 4 workers (budget unchanged at 2,400 s).
scripts/run_study_015.py is ledger-hashed and is not edited: the new file scripts/run_study_015_R1.py pins the base
file's sha256, changes only g11's worker count, and is the orchestrator launched at run_start. The worker ceiling
holds: after transfer ends, 2 (gti) + 2 (repro) + 4 (g11) = 8. Effect on gates: G_RT checks the unchanged budgets; no
science changes. Label: Exact (tests/test_run_study_015_R1 expects g11 (4, 2400, ['transfer']); smoke
results/smoke-015/SMOKE_R1_015.json shows g11 starting with 4 workers).

**#73: run_study_015.py changed after its ledger receipt.** The process_scripts_015 receipt (commit 3cd15e4) hashes
scripts/run_study_015.py at 59144b5f…. Commit 0f95f92 (smoke dry run) then changed two docstring lines (the g11 line
copied from study 014 said "4w … 288 cases … deviation #61"; it now matches the code: 2w, 360 cases). No code line
changed (Exact: git diff 3cd15e4 0f95f92). The ledger rule (verify_release_020.ledger_020, deviation D3) needs the LAST
receipt of each source to match its current bytes, so HEAD 426db81 would fail release verification. A new receipt
process_scripts_015b records the current bytes (9fa73b8c…); the 3cd15e4 receipt becomes superseded and still matches
its commit's blob. The file is not edited again (see #72). Label: Exact.
