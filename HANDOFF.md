# HANDOFF — pick this project up cold

_Kept current on the working branch during a release and on `main` at release. Last updated 2026-10-25 02:48 EDT (v0.4.0 implementation, branch `plan/v0.4.0`)._

## Current version and state

- **Released: v0.3.0** (tag `v0.3.0` = `73a3a5a`, unchanged). 12 of 14 gates pass; G5 and G6b fail (on the record);
  G14 OPEN. **v0.3.0 errata** on `main` (`8e6d323`, `8222e0e`; `docs/research/v0.3.0/ERRATA.md`): G11 is called a
  *second implementation by the same author (no `brute` import)*, not an independent audit; full-scan count
  **0/3,168** arm traces plus a mutation test; tamper-by-version tests; order check; numpy pin. GitHub releases
  v0.2.0/v0.3.0 were created with notes that point to the errata.
- **In progress: v0.4.0 / study BRUTE-040-GEOMETRY-006** on `plan/v0.4.0`.

## Branches (origin `github.com/jacksonjp0311-gif/Brute`, private)

| Branch | Head | State |
| --- | --- | --- |
| `main` | `8222e0e` (v0.3.0 merge + errata) | Released code and record |
| `plan/v0.4.0` | see `git log` | v0.4.0 working branch |
| `bridge/v0.2`, `bridge/v0.1` | `cced586`, `9c88a3a` | Bridge work; **unmerged; do not edit or merge without a decision** |

## v0.4.0 progress (commit order is the chronology evidence)

1. DONE `5fa3628`: `experiments/BRUTE_PLAN_006.json` pre-registered with design probes (Simulated, sealed 004/005
   seeds only, hashed in the plan). Ledger `preregistration_006` (appended after the errata merge to keep the chain linear).
2. DONE `2eba00b`: clean-room second implementation `experiments/v040_reference.py` (written from the plan only,
   before any `brute/` v0.4.0 code; counts mismatches and has a mutation test). Ledger `reference_006`.
3. DONE `2811904` (+ pre-freeze fix `b5e7077`): implementation `brute/resume.py` (A4/P4 resume, D2 depth-2, F2 fibre), `brute/geometry.py`
   (constraint region = H-representation of the version space; pysat Glucose3), `experiments/worlds_006.py` (perm4),
   `brute_common_006.py`, `brute_study_006.py`, `brute_calibrate_006.py`. Smoke (96 cases, placeholder tau6):
   reference count 0/80 traces then 0 on the larger smoke; mutation 20/20 detected.
4. Pre-freeze disclosure (for DEVIATIONS_006): the GR2 smoke on smoke2 hung (one SAT `support` query at n=10/12 ran
   >6 min). Fix before the freeze: `ConstraintRegion(conf_budget=None)` stays exact by default (GR1/GR1b unchanged);
   GR2 only uses `GR2_CONF_BUDGET=20000` conflicts per query and counts `unknown_steps/queries` (excluded from
   enum-vs-SAT agreement). Smoke after fix: 12 cases in 13 s, 0 disagreements, 1 case with unknowns at n=10 and n=12.
5. DONE: source freeze `70a3c43` (ledgered `94c80b2`).
6. DONE `d9ddbe6` (03:08 EDT): scoring scripts `make_gates_006.py`, `make_paired_006.py`, `make_reproducibility_006.py`
   in a separate commit (mechanically smoke-tested on /tmp smoke data only, not study data). Ledger `scoring_scripts_006`.
   RUN DONE 03:32:58 EDT, sealed (commit 'study-006 sealed'). Earlier note: RUN STARTED 2026-10-25T03:20:15-04:00 (ledger `run_start_006`); if interrupted rerun the script (resumes). Then: ledger `run_start`, nohup calibrate -> study -> pack (outputs refuse to overwrite;
   rerun of a step skips if its output exists). Logs in /tmp/p6/run006.log.
7. DONE: SECOND_IMPLEMENTATION_COUNT (2880 traces, 0 mismatching, mutation 20/20, 0 false flags) and GR1B (470,318 items, 0
   mismatches). PAIRED_ANALYSIS done (D78 R=0.632 CI [0.418,0.907], S(A2)=76). GR1 done (778,840 items over 2016 sealed 004/005 traces, 0 mismatches); GR2 done (84 cases, 0 enum-vs-SAT disagreements). repro DONE (all_byte_identical). GATES DONE (f6d9014; passed 15 gated incl G5/G6/G11/G12/G13/GR1/GR1b; failed G6b' only (pre-registered); G14' OPEN; G15/G16 candidates fail). DONE: DEVIATIONS_006 (7be6373), RELEASE.json + pyproject 0.4.0 (30776e2), README v0.4.0 (test count placeholder until full run). CHANGELOG, DISCOVERIES D17-D21, ROADMAP, NEXT_ITERATION v0.5.0 (old one -> docs/research/v0.4.0/) DONE. Release freeze fdd08d7 + ledger a6e84c5; verify --fast passes; test_release_040 5/5; full suite 196 (4 frozen-version errors); fresh clone verified. RELEASED: merge 5c02a7b on main, annotated tag v0.4.0 -> 5c02a7b (verified), pushed; GitHub release https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.4.0 (05:11 EDT). v0.4.0 COMPLETE. Next work: v0.5.0 per NEXT_ITERATION.md (pre-register BRUTE_PLAN_007 first on a new branch from main). Old list was: MANIFEST, verify, fresh clone, merge, tag, gh release (started 03:40 EDT, background, log /tmp/p6/score006.log, script /tmp/p6/score006.sh = count -> gr1b -> gr2 -> gr1,
   each skipped if its output exists): scoring in order SECOND_IMPLEMENTATION_COUNT (v040_reference --mutate 20), GR1, GR1B, GR2 (exactness_006),
   PAIRED (make_paired_006), REPRODUCIBILITY (make_reproducibility_006), GATES (make_gates_006). Raw JSON is gitignored:
   `python scripts/study006_storage.py restore` first on a fresh clone. Each output refuses to overwrite: skip if present.
   Original list: exactness, API 1.4, storage, tests,
   pins → `BRUTE_SOURCE_FREEZE_006.json` → scoring scripts in a separate commit ≥ 10 min before the run → ledger
   `run_start` → calibrate (twice, G13) → run → seal → `run_end` → gates/paired/count/repro/GR → docs → release freeze,
   MANIFEST, fresh-clone verify → `--no-ff` merge, tag v0.4.0 on the merge commit, gh release.

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
