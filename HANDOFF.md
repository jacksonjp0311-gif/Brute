# HANDOFF — pick this project up cold

_Kept current on the working branch during a release and on `main` at release. Last updated 2026-10-26 ~10:25 EDT (v0.11.0 IN PROGRESS on `plan/v0.11.0`)._

## Current version and state

<!-- V0110 -->
- **In progress: v0.11.0** (study BRUTE-0110-SOUND-TRANSFER-013, branch `plan/v0.11.0` from main b935fff + seen-data applicability diagnostic `e0aa431`, deviation #52).
  - Plan frozen at `bb1d96e` (experiments/BRUTE_PLAN_013.json, readable docs/research/v0.11.0/PLAN_013.md). Headline gate GST = sound transfer: AT (applicability test, M_app 6) or LX (library experiment choice) must show 0 false certificates for both the positive and the wrong-family library, no significant help from the wrong family, and a significant speedup. DR (dual region) is Exact-sound and cannot speed up.
  - Also: G6b on SP8 only; big78 SP8_78 288 cases with ≥150 certificates required; K_080/K_090 declared in GTI; GAPI = new brute/api/certify.py with a test.
  - Next step: check_seeds_013 → v0110_reference → implementation + smoke + rate math → source freeze → scoring → run (2 h cap, watchdog).
<!-- /V0110 -->

<!-- V0100 -->
- **Released: v0.10.0** (study BRUTE-0100-SUPPORT-TRANSFER-012, branch `plan/v0.10.0` = main 13daa32 + diagnostic, deviation #48). **18 of 24 gated pass.**
  - **TRANSFER:** GT_b PASS (TRp mean S 20.18 steps, seed-paired CI95 [19.18, 21.17]; 270 helped / 0 hurt; 0 false in 20,027). GT_ref PASS (288/288, 0 mismatches). **GT_a FAIL** (TRn 167 false transfer-rule certificates in 50/288 cases). **GT_c FAIL** (the same certificates, plus S_n 4.53 [3.37, 5.73] > 0).
  - **Other FAIL:** G6b (J10−A2 −0.1657 [−0.1767, −0.1551]), GA1_012 (via G6b), G3′ strict (J10 1 at lag 1), GTI as frozen (3 test_release_080 failures, deviation #50; R_GTI_K080 passes).
  - **PASS:** G1, G2, G3L, GJ10 (+0.0090 [0.0059, 0.0122]), GH, G4, G5, G7, G9, G10, G11, G12, G13, G78_soundness, G78_containment, G_RT (R_G_RT_strict true), GT_b, GT_ref. Release gates: GLV `--long` PASS (33 cases, 0 mismatches, ~21 s); GCC clean clone PASS (`results/study-012/CLEAN_CLONE_012.json`).
  - Run: run_start 09:09:06 EDT, hard cap 11:09:06 EDT, RUN_DONE 09:37:26 EDT (1,700 s of 7,200 s). The watchdog did not fire. Every stream completed (g11 optional 108/108).
  - Chain (Exact, git ancestry): diagnostic `6494a35` → plan + ROADMAP_TO_GI `0cccf0d` → seed check `9f4d4db` → reference `a44a8da` → implementation `2564201`/`1c43d68`/`4628617`/`2fb806c`/`7e77621` → source freeze `b40f263` → scoring `22ce7f7` (ledgered 08:57:44 EDT) → run_start `9b0babe` → seal `c07d773` → run_end/seal ledger `1af2976` → GATES_012 `1080654` → release tooling `be6a4ea` → deviation #51 + release_0100 ledger `90c3d1d` → release freeze `fb4ffd1` → clean clone `173465a`.
  - Deviations #48–#51 and disclosures: `docs/research/BRUTE_DEVIATIONS_012.md`. The pyproject bump to 0.10.0 makes the frozen test_release_090 version and verify tests fail (the K_090 analogue of K_080); v0.11.0 must declare it.
  - **RELEASED 2026-10-26 ~10:03 EDT:** release commit `c2794cf`. `verify_release_0100` passed short and `--long` on the branch (GLV 21 s of 900 s) and on a fresh GitHub clone of `c2794cf` in /tmp/fc0100 (GLV 19 s). `tests.test_release_0100` passed 6/6 on the fresh clone (108 s). main was fast-forwarded 13daa32..c2794cf (not forced). The annotated tag `v0.10.0` (object `7b33add`) points to `c2794cf`. This HANDOFF commit is the only post-tag commit on main. [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.10.0). The default learner is unchanged (Y1k, LU-R); J10, TRp and TRn are research arms. Scratch deleted.
  - **Next: v0.11.0 per `NEXT_ITERATION.md`** (sound transfer: intersect the prior with the full region, or verify the library before it licenses certificates; library for experiment choice; declare K_080 and K_090; big78 power). Pre-register BRUTE_PLAN_013 on `plan/v0.11.0` from main before any code.
<!-- /V0100 -->

- **Previous: v0.9.0** (study BRUTE-090-WINDOW-011, branch `plan/v0.9.0` from origin/main f79c925 ⊃ 70cb351, deviation #40). **15 of 17 gated pass.**
  - **FAIL:** G6b (J9−A2 coverage −0.1918, 95% CI [−0.2073, −0.1772]), GA1_011 (J9 does not reach SP8-level coverage).
  - **PASS:** G1, G2, G3L, G3′ strict (first strict pass: J9 0, SP8 16, control 323 ≤ limit 161.5), GH, G4, G5, G7, G9, G10, G11, G12, G13, GTI, G_RT.
  - Release gates (not in GATES_011): GLV `--long` PASS (33 cases, 66 traces, 0 mismatches, 363 s of 900 s); GCC clean clone PASS (`results/study-011/CLEAN_CLONE_011.json`, 24.9 s).
  - Run: run_start 06:48:41 EDT, hard cap 08:48:41 EDT, RUN_DONE 07:18:53 EDT (1,812 s of 7,200 s). Watchdog did not fire. g11 optional rest stopped at its 1,500 s budget (960/1,152 traces, 0 mismatches), so R_G_RT_strict is false (reported only).
  - Chain (Exact, git ancestry): lag diagnostic `a5ef9c8` → plan `7950513` → seed check `06249f7` → reference `d5c6a54` → implementation `8eeb810`/`4c4800b`/`052ec9d` → scoring scripts `13b12ee` → source freeze `f658e13` → scoring_freeze ledger 06:38:21 EDT → run_start → seal `6ae2cc4` → GATES_011 `ed2b042` → release tooling `34724b9` → release freeze R1 `804a433` → clean clone `9cddb66` → deviation #47 `d737a66`.
  - Deviations #40–#42: `docs/research/BRUTE_DEVIATIONS_011.md`; #43–#47: `docs/research/BRUTE_DEVIATIONS_011_R1.md`.
  - **RELEASED 2026-10-26 ~07:53 EDT:** release commit `05ed794`. `verify_release_090` passed short and `--long` on the branch (GLV 324 s of 900 s) and on a fresh clone of `05ed794` in /tmp/fc090 (GLV 316 s); `tests.test_release_090` 6/6 OK on the fresh clone (74 s). main fast-forwarded f79c925..05ed794 (not forced); annotated tag `v0.9.0` (object `2a9f627`) → `05ed794`; ledger 204 receipts. This HANDOFF commit is the only post-tag commit on main; [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.9.0). Default learner unchanged (Y1k, LU-R); J9 is a research arm.
  - **Next: v0.10.0 per `NEXT_ITERATION.md`** (J10 surprise-gated window hull; seen-data downgrade diagnostic first; 7–8 states in one family; g11 optional-rest stamp). Pre-register BRUTE_PLAN_012 on `plan/v0.10.0` from main before any code.
- **Previous: v0.8.0** released (tag `v0.8.0`), 12 of 17 gated pass; its record follows.
- **Released: v0.8.0** (study BRUTE-080-ALIGN-010, branch `plan/v0.8.0`). **12 of 17 gated pass.**
  - **FAIL:** GA1_010 (target a), G3′ (SP8 3 non-drift false certificates), G6b (J8 coverage 0), GD (clause i, 2/7 silent-jump class), G_RT (clause i: the g11_2x2 optional phase hit its own budget).
  - **PASS:** G1, G2, G4, G5, G7, G9, G10, G11, G12, G13, GX2_010, GTI.
  - Run: start 05:03:17 EDT, hard cap 07:03:17 EDT, RUN_DONE 05:36:07 EDT (1,970 s). The watchdog did not fire.
  - Chain: plan `881f0a6` → source freeze `5470c48` → scoring `39d255b` → run_start `19f3a88`/MANIFEST `687f28a` → run_end `eb85feb` → seal `1bdebc9` → ledger seal/gates `3cfac6c`/`0422ac0` → sealed run state `7b8a06d` → merge of main `b1e628d` → release docs and freeze.
  - **RELEASED 2026-10-26 ~05:55 EDT:**
    - Release commit `3bce08c`.
    - Deviations #38 (superseding ledger receipt for the frozen harness) and #39 (pre-publication verifier fix: note-less receipts dated by commit).
    - Ledger 172 entries; final release commit `70cb351`.
    - `verify_release_080` passed on the branch, on a fresh clone and as main. `tests.test_release_080` 5/5 OK (109 s).
    - main fast-forwarded a86298b..70cb351 (not forced).
    - Annotated tag v0.8.0 (object `9fa656c`) -> `70cb351`.
    - [GitHub release](https://github.com/jacksonjp0311-gif/Brute/releases/tag/v0.8.0).
  - Next: v0.9.0 per `NEXT_ITERATION.md`. First a lag diagnostic on seen data, then pre-register BRUTE_PLAN_011 on a new branch from main.
- **Previous: v0.7.0** released (tag `v0.7.0`), 9 of 17 gated pass; its record follows.
- **Released: v0.7.0** (study BRUTE-070-SYNCPLAN-009, branch `plan/v0.7.0`). **9 of 17 gated pass.**
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
| `main` | tag v0.9.0 (fast-forward of `plan/v0.9.0`) plus this HANDOFF | Released code and record |
| `plan/v0.9.0` | see `git log` | v0.9.0 working branch (merged) |
| `plan/v0.8.0` | see `git log` | v0.8.0 working branch (merged) |
| `plan/v0.7.0` | see `git log` | v0.7.0 working branch (merged) |
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
for k in 004 005 006 007 008 009 010 011; do PYTHONPATH=. python scripts/study${k}_storage.py restore; done  # rebuild gzip-stored traces
PYTHONPATH=. python scripts/verify_release_090.py           # must print "status": "passed"; add --long for GLV (~6 min)
python -m unittest discover -s tests
```

Then read, in this order: this file, `RELEASE.json`, `README.md` (Status, gate table, "What Brute can't do yet"),
`docs/research/BRUTE_DEVIATIONS_011.md` and `_011_R1.md`, `NEXT_ITERATION.md`, and the tail of `results/RESEARCH_LEDGER.jsonl`.
