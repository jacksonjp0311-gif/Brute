# Study-013 (v0.11.0) deviations and disclosures

Numbering continues project-wide. Study-012 ended at #51 (docs/research/BRUTE_DEVIATIONS_012.md).
Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

**#52: branch base.** The owner asked for plan/v0.11.0 to come from main `b935fff`. The branch is `b935fff` plus two
commits that came before the plan:

- `e0aa431`: the exploratory applicability diagnostic on SEEN data (scripts/diag_applicability_013.py,
  results/diag-013/APPLICABILITY_DIAG_SEEN.json, docs/research/BRUTE_DIAG_APPLICABILITY_013.md). It calibrates one
  constant, M_app (frozen at 6 = seen boundary 4 + margin 2).
- `373e8d0`: its ledger receipts.

Neither commit adds learner code. Exact: `git merge-base --is-ancestor b935fff <plan commit>`.

**Disclosure (not a deviation): known test failures declared in advance.** K_080 and K_090 (three tests each, the
superseded-release version / verify tests) are part of the frozen GTI criterion (Observed failing on the v0.10.0 tree
at 10:10 EDT before the plan). After the 0.11.0 bump, test_release_0100 is expected to fail the same way
(R_K0100_after_release, not gated).

**#53: retroactive dev-smoke ledger entry.** One development smoke run was ledgered after the fact rather than at the
time it ran. It ran on smoke seeds only, never on held-out seeds (Observed). The entry says it is retroactive.

**#54: study013_storage.py missing from 3871e78.** The orchestrator commit 3871e78 imports scripts/study013_storage.py
but did not include it. The file was committed in 7dc04c8, before the source freeze. BRUTE_SOURCE_FREEZE_013 locks it
(Exact: sha256 518edfd6...).

**#55: scoring_freeze_013 commit-field typo.** Four per-script scoring_freeze_013 receipts (bd8e9e1, 10:59 EDT) give
commit `0e2f0b6`, which is not a git object. The ledger is append-only, so an erratum receipt (aab5046) records the
correct scoring-scripts commit, 22bdb9f. The scripts' content is bound by that commit and by verify_release_0110's git
check (Exact). The last scoring receipt (10:59:50 EDT) came 644 s before run_start_013 (11:10:34 EDT), which meets
the 600 s rule.

**#56: push outage.** From about 10:56 EDT, `git push` failed with "Invalid username or token": the box's GitHub
token was rejected. Commits from 7dc04c8 onward existed only locally until auth was restored. No force push and no
history rewrite happened. Every commit was pushed unchanged once auth came back. Ordering evidence is local git
history plus the SHA-chained ledger (local, unsigned). Remote timestamps after the outage do not establish ordering.

**#57: watchdog/orchestrator start order.** The watchdog started at 11:10:37 EDT, 3 s after T0. Because of a shell
background-launch quirk, the orchestrator started at 11:10:46 EDT, 12 s after T0. The watchdog therefore covered the
whole run (G_RT clause ii PASS). Every stream's time counts from T0.

**Disclosure (not a deviation): GTI stream used 79% of its budget.** The stream took 2135 s of its 2700 s budget,
against RATE_MATH_013's projection of 55-63%. This was observed after the run. It changes no gate and triggers no
rate-math rule. Heartbeat gaps of 335 s and 94 s were also seen (box load). The watchdog does not depend on the
heartbeat for the cap, and the cap was never at risk.

**Disclosure: release tooling.** verify_release_0110, test_release_0110, release_version_0110 and
make_release_freeze_0110 were drafted outside the repo (/tmp) during the run, so the in-cap GTI module count stayed
the same. They were committed after gates_013.

## Addendum (post-release, 2026-10-26 ~22:50 EDT): #56 resolved

The push outage recorded as #56 (~10:56 EDT, "Invalid username or token", stale `GITHUB_TOKEN`) is resolved. git now uses the gh credential helper with `GITHUB_TOKEN`/`GH_TOKEN` unset. The 22 local commits went to `origin/plan/v0.11.0` as a plain fast-forward (7dc04c8..d8b449d). No force-push, no history rewrite, no MCP push_files. The release commit `d8b449d` was verified on a fresh GitHub clone before the tag. This addendum is appended after the tag and changes no criterion or result.
