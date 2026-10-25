# HANDOFF — pick this project up cold

_Kept current on the working branch during a release and on `main` at release. Last updated 2026-10-25 02:15 EDT (v0.4.0 design probes, branch `plan/v0.4.0`)._

## Current version and state

- **Released: v0.3.0** (tag `v0.3.0` on the `--no-ff` merge of `plan/v0.3.0` into `main`). Study
  BRUTE-030-CHANGEPOINT-005: fibre-robust certification (Y1k) + LU-R lookahead. Earlier tags `v0.2.0`, `v0.1.1`… stay
  as they are (never force-push).
  - Gates (Observed, `results/study-005/GATES.json`): 12 of 14 pass; **G5** (ood4 false alarms 5/72) and **G6b**
    (coverage −0.098 vs v0.2.0, pre-registered as expected) **fail and stay on the record**. G3′ (stale certificates),
    which failed in v0.2.0, passes. G14 (D7 = D8 single-mechanism test) is **OPEN**.
  - `python -m scripts.verify_release_030 --frozen` (full, reruns the independent reference, ~16 min) passed on a fresh
    clone. Tests: 170, 3 errors by construction after `python scripts/study004_storage.py restore` (4 without it;
    `BRUTE_DEVIATIONS_005.md` N1).
- **Next version:** v0.4.0, not started (proposal in `NEXT_ITERATION.md`; no pre-registration yet).

## Branches (origin `github.com/jacksonjp0311-gif/Brute`, private)

| Branch | Head | State |
| --- | --- | --- |
| `main` | v0.3.0 merge commit (= tag `v0.3.0`) | Released code and record |
| `plan/v0.3.0` | merged into `main` | v0.3.0 working branch (historical now) |
| `bridge/v0.2` | `cced586` | Bridge work (separate worktree `/workspace/brute-bridge`); **unmerged; do not edit or merge without a decision** |
| `bridge/v0.1` | `9c88a3a` | Older bridge protocol; unmerged |
| `plan/v0.2.0`, `plan/v0.1.1` | — | Historical release branches (merged) |

## In progress

v0.4.0 / study-006 on branch `plan/v0.4.0` (from main 73a3a5a). Design probes (Simulated, study-004/005 sealed seeds
only) are running in `docs/research/v0.4.0/design_probe/` (uncommitted until the plan commit, which discloses their
hashes). Next: commit `experiments/BRUTE_PLAN_006.json` + ledger `preregistration`, then implementation.

## Exact next steps

1. Create `plan/v0.4.0` from `main`. Write `experiments/BRUTE_PLAN_006.json` from `NEXT_ITERATION.md`: new seed blocks,
   arms (v0.4.0 active/passive + v0.3.0 A3/P3 + v0.2.0 A2 controls), gates with numeric thresholds, and the
   representation-exactness gate (the compact region gives decisions identical to enumeration on the sealed study-004/005
   traces). Commit it, append the `preregistration` ledger receipt and push — **before any code**.
2. Design probes (Simulated) go only on earlier sealed traces and are disclosed in `BRUTE_DEVIATIONS_006.md`.
3. Implement in new files only. Write `BRUTE_SOURCE_FREEZE_006.json`, commit and ledger the scoring scripts before the
   run, run study-006, and seal it. Then the same release sequence as v0.3.0: paired analysis, gates, independent audit,
   reproducibility, docs, release freeze, MANIFEST, fresh-clone tests, `--no-ff` merge, tag on the merge commit (check it
   with `git rev-parse`), push.
4. Keep this file current at every step.

## Standing discipline rules

- **Pre-registration first:** criteria, seeds, arms and scoring are committed and ledgered before any code for a study.
  Source is frozen before the run. Scoring scripts are committed before results are inspected.
- **Evidence labels on every claim:** Exact / Observed / Simulated / Inferred / Rejected / Open.
- **Never tune after the fact:** frozen criteria, thresholds, scoring scripts and frozen files (every `*FREEZE*.json`,
  `brute/core/*`, earlier `release_version*`, `api/service*.py`, schemas v1–v1_3, `brute/api/refusals.py`) are never edited.
  New behaviour goes in new files.
- **Failures stay on the record:** a failed gate is reported as failed, with a deviation entry; it is never rerun or
  redefined to pass.
- **The ledger is append-only** (`scripts/append_ledger.py EVENT SOURCE --note … --commit <short>`). A changed
  artifact gets a new receipt that supersedes the old one.
- Every step is committed and pushed. Never modify `/workspace/bgr/BGR-v0.90.0` or `/workspace/brute-bridge`. The repo
  stays private. Bridge observations are diagnostic only.

## Roadmap goal

A **general-intelligence geometric reasoning system**: its core operations are on regions (projections, fibres, cuts),
it certifies only what every surviving explanation agrees on, and it chooses experiments that shrink regions. Next it
needs depth (multi-step lookahead and re-certification), a representation beyond enumeration, and breadth (new domains,
larger alphabets, n ≥ 6). It is not AGI now; see `docs/ROADMAP.md`, `NEXT_ITERATION.md`, `docs/research/DISCOVERIES.md`.

## How to resume

```bash
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute && git checkout main
python -m venv venv && venv/bin/pip install -r requirements.txt          # box venv: /workspace/bgr/venv/bin/python
python scripts/study005_storage.py restore                              # rebuild gzip-stored traces (verifiers do this too)
python -m scripts.verify_release_030 --fast --frozen                    # must print "status": "passed"
python -m unittest discover -s tests
```

Then read, in this order: this file, `RELEASE.json`, `README.md` (Status, gate table, "What Brute can't do yet"),
`docs/research/BRUTE_DEVIATIONS_005.md`, `NEXT_ITERATION.md`, and the tail of `results/RESEARCH_LEDGER.jsonl`.
