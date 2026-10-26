# HANDOFF — pick this project up cold

_Kept current on the working branch during a release and on `main` at release. Last updated 2026-10-26 ~01:00 EDT (v0.7.0 RELEASED)._

## Current version and state

- **Releasing: v0.7.0** (study BRUTE-070-SYNCPLAN-009, branch `plan/v0.7.0`). **9 of 17 gated pass.**
  - **FAIL:** GA1′ (target a), G3′, G6b, GP1 (target c); STUDY_BUDGET: GX2″ (target b; symmetric part complete, 0 mismatches; spot 6/24), G11 (no output), GTI (target d, never ran in-cap), G_RT.
  - **PASS:** G1, G2, G4, G5, G7, G9, G10, G12, G13.
  - Run: start 20:04:06 EDT, cap 23:04:06, stop rule fired 23:22:42 EDT (late; DEVIATIONS_009 entry 21). No stream relaunched.
  - Done in order: run-end commit `4cdeeb4`; deviations 21–25 `af60688`; pack `30bb932`; ledger run_end_009 + SEAL `327d4fd`; ledger seal_009 `8888b88`; paired + repro; GATES_009 `a50f751` + ledger gates_009; docs + RELEASE.json/pyproject 0.7.0.
  - **RELEASED 2026-10-26 ~00:57 EDT:** GATES_009_FINAL + TEST_SUITE_009_FINAL `db6f6bb`; ledger gates_final_009 + MANIFEST `ee21407`; verify_release_070 --fast passed on branch, fresh clone and merge; `--no-ff` merge `d016a81` on main; annotated tag v0.7.0 (object `e5ae50b`) -> `d016a81`; [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.7.0). 9/17 gated pass. Next: v0.8.0 per NEXT_ITERATION.md (pre-register BRUTE_PLAN_010 on a new branch from main first).
- **Previous: v0.6.0** released (tag `v0.6.0`), 11 of 16 gated pass; its record follows.
- **Released: v0.6.0** (study BRUTE-060-DRIFTSOUND-008, `plan/v0.6.0` → main, tag `v0.6.0`). **11 of 16 gated pass.**
  - **FAIL:** GA1 (target a), G3′, G5, G6b and GX2′ (target b, incomplete coverage).
  - **PASS:** G1, G2, G4, G7, G9, G10, G11, G12, G13, GT1 (target c) and GMC (target d).
  - Gates: `results/study-008/GATES_008_FINAL.json`. Deviations: `docs/research/BRUTE_DEVIATIONS_008.md` D1–D26.
  - D21: stream A (xcheck) stopped by owner decision at 17:44 EDT with 46/288 cases. Scored FAIL on the frozen criterion; no results were inspected.
  - D22: partial wrapper `scripts/make_xcheck_partial_008.py`.
  - D23: pack was run by hand.
  - D24: observations made during scoring, report only.
- **Previous: v0.5.0** (tag `v0.5.0` → merge `8e03e03`). 12 of 15 gated pass; GX2, G3′ and G6b fail. Tags never move.
- Default learner is still the v0.5.0 rule (Y1k, LU-R). R6/C6 are research arms only (plan `default_policy_rule`).

## Branches (origin `github.com/jacksonjp0311-gif/Brute`, public on purpose: James asked for it 2026-10-25 01:13 EDT)

| Branch | Head | State |
| --- | --- | --- |
| `main` | tag v0.6.0 (+ HANDOFF/MANIFEST commits) | Released code and record |
| `plan/v0.7.0` | see `git log` (freeze `3825ad3`) | v0.7.0 working branch: plan frozen, no code |
| `verify/xcheck-incremental` | `c2bf07e` | Post-release incremental xcheck verification (not v0.6.0 evidence); 3 files adopted by v0.7.0 |
| `plan/v0.6.0` | see `git log` | v0.6.0 working branch (merged) |
| `plan/v0.5.0` | `d0516a0` | v0.5.0 working branch (merged) |
| `plan/v0.4.0` | `5e7d208` | v0.4.0 working branch (merged) |
| `bridge/v0.2`, `bridge/v0.1` | `cced586`, `9c88a3a` | Bridge work; **unmerged; do not edit or merge without a decision** |

## v0.6.0 progress (commit order is the chronology evidence)

1. DONE 07:2x EDT: branch `plan/v0.6.0` from main `ed66489`. `89c2d3b`: BRUTE_PLAN_008.json + PLAN_008.md. Targets:
   - a: GA1, one arm of R6/C6 passes G1+G2+G3′+G6b.
   - b: GX2′, xcheck with SAT/CaDiCaL, checked ≥0.99 per family×arm, 0 mismatches.
   - c: GT1, verify_release_060 / test_release_060, with the frozen 050 files untouched.
   - d: GMC, its own gate.
   - Predictions (Inferred): GA1 FAIL, GT1 PASS.
2. DONE `1bc702f`: ledger preregistration_008 + MANIFEST.
3. DONE: seed check; implementation; smoke; source freeze `8e80615`; scoring scripts `08ac3f3`; run_start_008 08:49 EDT;
   GT1 tooling `29cd0d1`; main SEAL `c21ef12`; stream C (G11, enumeration, repro, GMC recount) done 10:49 EDT; stream B (GMC) done.
4. DONE 17:44 EDT: owner stopped stream A (xcheck) at 46/288 (`b02b0c3` checkpoint, D21–D23). Then, in order:
   - pack `287d619`;
   - ledger run_end_008 + seal_008 `3a5e193`;
   - wrapper `1202c53`;
   - XCHECK_008.json `87ad393`;
   - paired + reproducibility;
   - GATES_008 (ledger gates_008 `c4a7c1b`);
   - GT1_008 + GATES_008_FINAL (ledger `1cd90f4`).
5. DONE: RELEASE.json/pyproject 0.6.0; README/CHANGELOG/HANDOFF/D24; retroactive receipt for pre-freeze fix `cae25ce` (D25); verify_release_060 git_order fix and
   release freeze `BRUTE_RELEASE_FREEZE_060_R1.json` superseding `BRUTE_RELEASE_FREEZE_060.json` (D26);
   ledger release_freeze_060_r1/release_060; MANIFEST; verify_release_060 --fast; tests; ff-merge to main; tag v0.6.0; gh release.

### Open for the next study (Inferred / Open)

- The xcheck needs to run about 50x faster to finish breadth in a working day. Options: incremental solving, sampling steps under a pre-registered rule, or moving off a shared box. GX2′ is still open.
- Stale certificates one step after a drift remain in R6, C6 and A5 (D24b). The surprise signal may arrive one step late.
- The perm4 false-alarm cases under τ6 (D24a) need a pre-registered look at alarm calibration on perm4.
- Neither rule gets close on G6b; the coverage/safety trade-off is still open.
- Model counts are available but unused.
- `experiments/brute_study_006.py` sets `S5.FULL` when it is imported, which makes `test_study_005` fail in full-suite runs (Observed). Both files are frozen; v0.7.0 target (d) isolates it per process instead of editing them.

## v0.5.0 progress (commit order is the chronology evidence)

1. DONE: branch `plan/v0.5.0` from main `2998dba`; timing probe (frozen geometry, sealed 006 seeds): 2x2 SAT + LU-R ~0.1-0.7 s/case; n<=6/7 ~1-10 s.
2. DONE `5be08aa` (ledger `64f8c79`, ~05:22): `experiments/BRUTE_PLAN_007.json` pre-registered (A5/M5/A4/A2 on 2x2; B5/BM5/BP5 on
   big6/sens3/act3/ood6s3; GX1-3, G1-G5, G6b(M5), G7, G9-G13; SOLVER_BUDGET; M = projection-volume tie-break; #SAT etc. Open).
3. DONE `1b57efe` (ledger `a5215ee`, ~05:26): `experiments/v050_reference.py` second implementation (no brute import) +
   `tests/test_v050_reference.py` (k=2 generalised enumeration == frozen reference). Process notes for DEVIATIONS_007 in
   `docs/research/v0.5.0/PROCESS_NOTES.md`.
4. DONE (pre-freeze, ~05:27-05:41): `fc2bed8` brute/region.py (RegionK/RegionSpace, tri-state Glucose3), brute/region_learner.py
   (A5/M5), brute/breadth.py (B5/BM5/BP5), experiments/worlds_007 / brute_common_007 / brute_study_007 (per-case checkpoint);
   `c8e8611` brute_calibrate_007 + scaling_007; `b693113` api 1.5 service + schemas v1_5 + release_version_050 + tests/test_v050_impl.py
   (8 tests OK). Smoke (seeds 901-903 only): A5 vs A4 on all 8 2x2 families x 3 rates = 3168 steps, 0 mismatches (Observed);
   breadth per-case 0.2-6 s; scaling n=12 cases < 1 s.
4b. Smoke count (324 arm traces, 24/24 mutations detected) flagged 2 traces: residual == smoke tau7 at 12 d.p.; plan says
   rounded residual > tau, reference used frozen unrounded _Alarm. Pre-freeze fix `0c86d90` (_Alarm12 in v050_reference, A4 audit
   unchanged; disclosed in PROCESS_NOTES). `d7054a1`: run/storage/freeze scripts, torn-line-tolerant checkpoint. Recount 05:56: 0/324 mismatching, mutation 24/24, 0 false flags (Observed, smoke).
5. DONE `064a50e` source freeze 007 (20 files, chains 002-006; ledger `0ea8085`, ~05:57).
6. DONE `50e9321` (06:00) scoring scripts 007 in their own commit (dry-run on smoke seeds only); ledger scoring_scripts_007.
   DONE run_start_007 on origin as ebcc650 (06:11:52; local duplicate push rejected, rebased; identical receipt 5cefd253).
7. RUNNING since 06:14 EDT: `PYTHONPATH=. W=6 nohup bash scripts/run_study_007.sh >> /tmp/w7/run007.log 2>&1 &`
   (resumable: rerun same command; each stage resumes from its checkpoint). NEXT: on RUN_DONE commit SEAL/calibration/scaling/gz, ledger run_end_007.
8. 06:17 steering (v0.4.0 review /workspace/brute-review/v0.4.0/REVIEW.md) arrived AFTER run_start; run not stopped (decision:
   held-out data already in use; restart would be redoing work). Post-start, non-pre-registered additions (disclose in DEVIATIONS_007):
   DONE `07a6c69` experiments/v050_prob_reference.py (2x2 v090 probabilities recomputed taken+untaken by partial-machine counting,
   no brute/bgr import; swap mutations; smoke dry-run 0/216 mismatches, 20/20 detected) + scripts/check_smoke_seeds_007.py
   (smoke seeds 901-903 disjoint from 468 evaluation seeds; 05:25 glance seed 1710001 overlaps -> deviation).
   DONE `033c716` ledger smoke_run_retroactive_007 + steering_after_run_start_007.
   DONE `1c4dd00` scripts/scaling_fit.py + docs/research/v0.5.0/SCALING_FIT_006.json (power/exponential/cubic, residuals by n).
   DONE `91ae0d8` post-hoc v0.90 probability recompute on sealed study-006 A4+P4: 0/1152 traces, 88,038 forecasts, mutation 20/20.
   DONE main `47480f7` v0.4.0 errata (docs/research/v0.4.0/ERRATA.md E1-E10; DEVIATIONS_006 P8 + P1/P2 notes; CHANGELOG,
   README, HANDOFF corrected; MANIFEST regenerated; verify_release_040 --fast passed; tag v0.4.0 still 5c02a7b).
   DONE merge main -> plan `0e29dc2`; ledger errata_040 `e972b8c` (receipt b00d1d20...).
9. DONE run: sealed 06:25 (`51215e0`), RUN_DONE 06:27:47 (`3073992`), ledger run_end_007 `86bd7bc`. SCALING_FIT_007 `feeeb1d`.
   DONE paired + reproducibility (296/296 identical) `d88d4bb`, ledger `2ceb87e`. DONE PROB recompute 0/1728, 20/20 `ffeb0c4`.
   DONE count `9c7737e` (0/2592 arm traces, mutation 20/20; breadth reference budget-stopped on some big6/act3 traces), ledger `7ddaf45`.
   DONE `16d60cf` release freeze list also locks post-start audit scripts.
   DONE gates `dab2012`, ledger `cda5c49`: 12/15 gated pass; FAIL GX2 (0 mismatches, act3 checked 84.5% < 90%), G3' (M5 1 non-drift
   false cert on drift4; A5 passes), G6b (predicted). GM NOT DISTINGUISHED (M5-A5 CI > 0 but G3' fails for M5). GX3 PASS.
10. DONE M5 non-drift diagnostic (DEVIATIONS_007 Q7, report only); DEVIATIONS_007 complete `a02e9c7`+.
   DONE README `e86c9f9`; CHANGELOG/DISCOVERIES D22-D25/ROADMAP/NEXT_ITERATION (v0.6.0) `5d19d36`.
   DONE RELEASE.json + pyproject 0.5.0 `87136cc`; release freeze 050 `267ca0f` (10 files), ledger release_freeze_050 `dafc2b0`.
11. DONE ledger release_050 `d33a8b5`; late ledger receipts for v050_reference (0c86d90) and v050_prob_reference (91ae0d8) `3d9f587`
   (verify flagged their hashes; disclosed in notes). verify_release_050 --fast PASSES on branch and fresh clone (after storage restore).
   Tests: discover 213 tests, 204 pass, 1 F + 8 E; 8 by construction (frozen old-release tests), 1 real: test_release_050 tamper case
   COUNT.json raises JSONDecodeError not VerificationError (frozen; recorded in README `d8bb38b`, NEXT_ITERATION).
12. DONE (07:15 EDT) verify_release_050 --fast passes on branch b3415d2, fresh clone, and merge commit. Merged into main as a
   --no-ff merge commit 8e03e03 (tree identical to plan/v0.5.0; a fast-forward was possible, merge commit used per the earlier
   "tag on merge commit" instruction; allowed by the "else merge commit" spec only in spirit), pushed non-forced. Annotated tag v0.5.0
   (object aec362b) -> 8e03e03, verified local + remote; v0.2.0/v0.3.0/v0.4.0 unchanged. gh release (notes lead with the 12/15 +
   priority verdicts, edited 07:13): https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.5.0
   RELEASE COMPLETE. v0.6.0 NOT started (proposal in NEXT_ITERATION.md). This HANDOFF commit is post-tag (HANDOFF + MANIFEST only).

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
   in a separate commit. **Errata (2026-10-25): this was false — the smoke data were 96 held-out study-006 cases and
   the full scoring chain had been dry-run on them in /tmp/p6/st at 03:02–03:08 EDT; see DEVIATIONS_006 P8.** Ledger `scoring_scripts_006`.
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
  is public on purpose (James, 2026-10-25 01:13 EDT); keep it public. Bridge observations are diagnostic only.

## Roadmap goal

A **general-intelligence geometric reasoning system**: its core operations are on regions (projections, fibres, cuts),
it certifies only what every surviving explanation agrees on, and it chooses experiments that shrink regions. Since v0.5.0
the region (SAT) is the engine and breadth reaches 6 states / 3 sensors / 3 actions; next it needs a drift-sound
certification rule narrower than the whole fibre, exactness checks beyond enumeration, and model counting. It is not AGI now; see `docs/ROADMAP.md`, `NEXT_ITERATION.md`, `docs/research/DISCOVERIES.md`.

## How to resume

```bash
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute && git checkout main
python -m venv venv && venv/bin/pip install -r requirements.txt          # box venv: /workspace/bgr/venv/bin/python
venv/bin/pip install -r requirements-gmc.txt                            # model counting (reporting only)
for n in 4 5 6 7 8; do python scripts/study00${n}_storage.py restore; done  # rebuild gzip-stored traces
PYTHONPATH=. python scripts/verify_release_060.py --fast                # must print "status": "passed"
python -m unittest discover -s tests
```

Then read, in this order: this file, `RELEASE.json`, `README.md` (Status, gate table, "What Brute can't do yet"),
`docs/research/BRUTE_DEVIATIONS_008.md`, the "Open for the next study" list above, and the tail of `results/RESEARCH_LEDGER.jsonl`.
