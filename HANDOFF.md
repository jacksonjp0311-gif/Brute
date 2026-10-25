# HANDOFF — pick this project up cold

_Kept current on the working branch during a release and on `main` at release. Last updated 2026-10-25 01:15 EDT._

## Current version and state

- **Released:** v0.2.0 (tag `v0.2.0`, on `main` at `31a348e`). Do not move or force-push it.
- **In release:** **v0.3.0** on branch `plan/v0.3.0` (study BRUTE-030-CHANGEPOINT-005: fibre-robust certification Y1k
  + LU-R lookahead). The study is sealed, gated, audited and reproduced; docs are written; the release freeze, ledger and
  MANIFEST are done; `python -m scripts.verify_release_030 --fast --frozen` passes.
  - Gates (Observed, `results/study-005/GATES.json`): 12 of 14 pass; **G5** (ood4 false alarms 5/72) and **G6b**
    (coverage −0.098 vs v0.2.0, pre-registered as expected) **fail and stay on the record**. G3′ (stale certificates),
    which failed in v0.2.0, passes. G14 (D7 = D8 single-mechanism test) is **OPEN**.
  - Test suite: 170 tests, 3 errors, all by construction (frozen earlier-release version checks after the RELEASE.json
    bump; `BRUTE_DEVIATIONS_005.md` N1).

## Branches (origin `github.com/jacksonjp0311-gif/Brute`, private)

| Branch | Head | State |
| --- | --- | --- |
| `main` | `31a348e` | v0.2.0 release merge (tag `v0.2.0`) |
| `plan/v0.3.0` | latest push | v0.3.0 work; to be merged with `--no-ff` into `main` |
| `bridge/v0.2` | `cced586` | Bridge work (separate repo `/workspace/brute-bridge`); **unmerged; do not edit or merge** |
| `bridge/v0.1` | `9c88a3a` | Older bridge protocol; unmerged |
| `plan/v0.2.0`, `plan/v0.1.1` | — | Historical release branches (already merged) |

## In progress

Finishing the v0.3.0 release: a fresh-clone run of the test suite and the full (non-fast) verifier with `--frozen`, then
the merge and tag.

## Exact next steps

1. Fresh clone of `plan/v0.3.0`: `python -m unittest discover -s tests` (expect 170 tests, 3 by-construction errors) and
   `python -m scripts.verify_release_030 --frozen` (full; reruns the independent reference, about 15 min). Put the count
   in the README Status row; then run `python scripts/make_manifest.py` and commit and push.
2. In a `main` worktree: `git merge --no-ff plan/v0.3.0`; `git tag -a v0.3.0 -m "Brute v0.3.0"` on the merge commit;
   check that `git rev-parse v0.3.0^{commit}` equals `git rev-parse HEAD`; push `main`, then push the tag (no force).
3. Start v0.4.0 from `NEXT_ITERATION.md`: write and commit `experiments/BRUTE_PLAN_006.json`, and append its ledger
   receipt, **before any code** (multi-step fibre re-certification with a two-step lookahead; a compact region
   representation verified decision-identical to enumeration; one new domain family; a recalibrated, resumable alarm).

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
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute && git checkout plan/v0.3.0   # or main after release
python -m venv venv && venv/bin/pip install -r requirements.txt          # box venv: /workspace/bgr/venv/bin/python
python scripts/study005_storage.py restore                              # rebuild gzip-stored traces (verifiers do this too)
python -m scripts.verify_release_030 --fast --frozen                    # must print "status": "passed"
python -m unittest discover -s tests
```

Then read, in this order: this file, `RELEASE.json`, `README.md` (Status, gate table, "What Brute can't do yet"),
`docs/research/BRUTE_DEVIATIONS_005.md`, `NEXT_ITERATION.md`, and the tail of `results/RESEARCH_LEDGER.jsonl`.
