# Brute changelog

## v0.8.0: jump-hull certification, aligned lookahead, a silent-jump diagnostic, a hard 2 h cap with a watchdog (study BRUTE-080-ALIGN-010)

**12 of 17 gated criteria pass.** Five fail: GA1_010 (target a), G3′, G6b, GD and G_RT. **G11, GX2_010 and GTI pass, inside the cap.** *Observed*; scoring rules were fixed before the data (*Exact*).

### Timeline

All times are the author's clock, EDT.

- **Pre-registration and preparation.**
  - Criteria pre-registered at `881f0a6` (`experiments/BRUTE_PLAN_010.json`).
  - Seed check `c80bdd7`.
  - GD classifier replay on sealed study-009 `299babf`.
  - Second implementation `experiments/v080_reference.py` `385ea23`.
  - Implementation `2360559`…`8c7fdf2`.
  - Smoke runs and kill drills smoke-1/2/3. The watchdog fix is in DEVIATIONS_010 #28.
- **Freezes.** Source frozen at `5470c48`. Scoring scripts frozen at `39d255b` (ledger scoring_freeze_010, 04:52:47 EDT).
- **Held-out run** (`scripts/run_study_010.py` + independent `scripts/watchdog_010.py`).
  - Started 05:03:17 EDT under a hard 2 h cap (07:03:17 EDT).
  - RUN_DONE at 05:36:07 EDT (1,970 s). The watchdog did not need to fire.
- **After the run.**
  - Seal `1bdebc9` (47 files).
  - GATES_010 ledgered at `0422ac0`.
  - Sealed run state committed at `7b8a06d`.
  - main merged in at `b1e628d`.
  - Release freeze `BRUTE_RELEASE_FREEZE_080.json`.
  - Deviations are in `docs/research/BRUTE_DEVIATIONS_010.md` (#27–#37).

### Code

- **`brute/jumphull.py`**: J8, which is S7 plus a one-step jump hull. A certificate survives only if Y1k on the region without its last transition gives the same single code. It is a research arm, not the default.
- **`brute/align.py`**: SP8 / BSP8, which is SC7 / BSC7 certification with the aligned lookahead LU-C. It is a research arm, not the default.
- **`experiments/v080_reference.py`, `scripts/run_reference_010.py`**: an independent second implementation with a mutation test.
- **`experiments/v080_xcheck.py`**: incremental symmetric CaDiCaL cross-check plus a spot check.
- **Run control.** `scripts/run_study_010.py` (checkpointed streams, per-stream budgets, hard cap), `scripts/watchdog_010.py` (an independent process that SIGSTOPs the orchestrator and kills its descendants), `scripts/run_tests_080.py` (GTI) and `scripts/seal_010.py`.
- **Release.** `scripts/verify_release_080.py`, `tests/test_release_080.py`, `scripts/study010_storage.py`, `scripts/make_release_freeze_080.py` and `brute/release_version_080.py`.

### Results (*Observed*)

- **Soundness and safety.** G1/G2: 0 false certificates for every arm. G4 passes. G5: max 2/72 on perm4.
- **G3′.** J8 0 non-drift false certificates; SP8 3; SC7 4.
- **G6b.** SP8 − A2 −0.0167 [−0.0228, −0.0113], a pass and the first in the project. J8 − A2 −0.2242 [−0.2381, −0.2110]: J8 coverage is 0.
- **Reported contrasts.** SP8 − SC7 +0.0345 [0.0272, 0.0420]. BSP8 − BSC7 +0.0195 [0.0100, 0.0297].
- **GD.** Clause (i) fails: 1/4 and 1/3 silent-jump class against the 0.8 threshold. Clause (ii) passes.
- **Exactness and second implementation.** G11: 648/648 + 144/144 traces with 0 mismatches; mutation 20/20. GX2_010: 100% of steps, 0 mismatches.
- **Reproducibility.** G12: 216/216 + 96/96.
- **G_RT.** Clause (i) fails: the optional g11_2x2 phase hit its own budget. Clauses (ii) and (iii) pass; kill latency 0.239 s.

## v0.7.0: synchronous drift events, incremental symmetric xcheck, a count planner, per-module test isolation (study BRUTE-070-SYNCPLAN-009)

**9 of 17 gated criteria pass. GA1′ (target a), GP1 (target c), G3′ and G6b fail on the data; GX2″ (target b), GTI (target d), G11 and G_RT fail STUDY_BUDGET** because the 3 h stop rule fired (*Observed*; scoring rule fixed before data, *Exact*).

Timeline (commit and ledger times are the author's clock):

- Criteria pre-registered at `3825ad3` (`experiments/BRUTE_PLAN_009.json`); seed check, lag diagnostic a0 on sealed study-008, second implementation `experiments/v070_reference.py`.
- Source frozen at `f9b94e7`; scoring scripts frozen at `b49cc37` (ledger scoring_freeze_009, 19:53 EDT).
- Held-out run (`scripts/run_study_009.py`) started 20:04:06 EDT; 3 h cap 23:04:06 EDT; the stop rule fired at 23:22:42 EDT (late, DEVIATIONS_009 entry 21). gx2_spot stopped by its 30 min stream budget (6/24 cases); g11 stopped by the cap with no output; GTI never started.
- Pack `30bb932`, ledger run_end_009 + study SEAL `327d4fd`, paired + reproducibility, GATES_009 `a50f751`, final-tree test run and GATES_009_FINAL, release freeze `BRUTE_RELEASE_FREEZE_070.json`. Deviations: `docs/research/BRUTE_DEVIATIONS_009.md` (entries 1–25).

Code:

- **`brute/syncevent.py`**: research arms S7/SC7 (2x2) and BS7/BSC7 (breadth): certificates are withdrawn on synchronous events E1 ∪ E2 ∪ E3. Not the default.
- **`brute/planner.py`**: P7, an experiment planner that scores actions with exact model counts (forked per-count 2 s limit, 150 s per case). Not the default.
- **Adopted byte-identical from `verify/xcheck-incremental` (c2bf07e):** `brute/xcheck_sat_incremental.py`, `experiments/v060_xcheck_incremental.py`, `tests/test_xcheck_sat_incremental.py`; `experiments/v070_xcheck.py`.
- **`scripts/run_tests_070.py`**: GTI runner, one fresh interpreter per test module.
- **`scripts/run_study_009.py`**: Python orchestrator with per-stream budgets, a 3 h cap and seal-partial.
- **`scripts/verify_release_070.py`, `tests/test_release_070.py`, `scripts/make_gates_final_009.py`, `scripts/study009_storage.py`, `brute/release_version_070.py`.**

Results (*Observed*): G1/G2 0 false certificates for every arm; S7 4 / SC7 5 non-drift false certificates on drift4; G6b S7 −0.0989, SC7 −0.0503; GP1 coverage −0.035; GX2″ symmetric check 100% of breadth steps, 0 mismatches, 316 s; G5 0 alarms everywhere; G12 360/360.

## v0.6.0: drift-sound certification rules, a non-enumeration exactness check, a hardened verifier, model counting (study BRUTE-060-DRIFTSOUND-008)

**11 of 16 gated criteria pass. GA1 (target a), GX2′ (target b), G3′, G5 and G6b fail.** GT1 (target c) and GMC
(target d) pass.

Timeline:

- Criteria pre-registered at `89c2d3b` (`experiments/BRUTE_PLAN_008.json`).
- Second implementation `8863f06` (`experiments/v060_reference.py`, same author, no `brute` import).
- Implementation `457db5a`/`6556186`/`ff4d0d8`/`6f6cd22`; pre-freeze fix `cae25ce`.
- Source frozen at `8e80615`.
- Scoring scripts committed alone at `08ac3f3` (08:38:46 EDT); ledger `run_start_008` at 08:49:16 EDT; sealed at `c21ef12`.
- Stream A (xcheck) stopped by owner decision at 17:44 EDT after 46/288 cases.
- Criteria and scoring scripts were not changed afterwards. Deviations are in `docs/research/BRUTE_DEVIATIONS_008.md` (D1–D26). The release freeze is `experiments/BRUTE_RELEASE_FREEZE_060_R1.json`, which supersedes `BRUTE_RELEASE_FREEZE_060.json` (D26).

Code:

- **`brute/driftsound.py`** (`DriftSoundLearner`, research arms R6 = rule RO and C6 = rule CT, breadth BR6/BC6).
  - R6: for W = 8 steps after a surprise, transition edges confirmed only before it are treated as unknown in the Y1k check.
  - C6: also certify on the v0.2.0 tracked-state projection while the session has had no surprise.
  - Not the default. The release default stays the v0.5.0 rule.
- **`brute/xcheck_sat.py`, `experiments/v060_xcheck.py`**: a second CNF encoding solved with CaDiCaL, with witness
  checks, that re-decides breadth traces without enumeration.
- **`brute/modelcount.py`**: exact |R_t| (pyganak 2.8.0), a blocking-clause cross-count, sum checks, and approxmc
  estimates for UNKNOWN counts only. Reporting only; the pins are in `requirements-gmc.txt`.
- **`scripts/verify_release_060.py`, `tests/test_release_060.py`, `scripts/make_gt1_008.py`**: every artifact is
  parsed through one guard that raises `VerificationError`. This fixes the v0.5.0 `JSONDecodeError` defect in the
  new verifier; the frozen v0.5.0 pair is unchanged. `brute.release_version_060`.
- **`scripts/make_xcheck_partial_008.py`** (post-stop wrapper, D22): turns the partial xcheck checkpoint into the
  frozen report schema with full-denominator fractions, so the unchanged gate script scores incomplete coverage as FAIL.

Study-008 results (*Observed*):

- **Failed:**
  - **GA1:** no arm passes G1+G2+G3′+G6b.
  - **G3′:** R6 had 20 false certificates with 1 at a non-drift step; C6 had 26 with 2. Each non-drift event comes one step after a drift. The limit is 86.
  - **G6b:** R6 − A2 −0.101235 [−0.112695, −0.089699]; C6 − A2 −0.072145 [−0.084144, −0.060724].
  - **G5:** perm4 R6 and C6 4/72 = 0.0556. The same 4 cases alarm in A4/A5 (D24).
  - **GX2′:** incomplete coverage, 46/288 cases. On what was checked: 0 mismatching traces, 0 witness failures, 0 disagreements with enumeration. big6 within the checked cases was 0.986 < 0.99.
- **Passed:**
  - G1/G2: 0 false certificates in every arm, including ood5 (R6 0/39, C6 0/44) and ood6s3 (B5 0/505, BR6 0/486, BC6 0/550).
  - G4.
  - G7: log-loss ood5 0.644, drift4 1.095, ood6s3 1.371.
  - G9: 273 retractions, 8 resumes, 0 violations.
  - G10: 0 production forecasts used an UNKNOWN answer.
  - G11: 0/1,872 mismatching traces, mutation 20/20.
  - G12: 312/312 byte-identical; GMC recount 120 cases, 11 timeout-only differences.
  - G13.
  - **GT1:** 56/56 corruptions give `VerificationError`.
  - **GMC:** 3,232/3,240 counted (0.997531), 0 disagreements, 0 sum violations.
- **Reported, not gated:** C6 − A5 coverage +0.023 [0.019, 0.027]; R6 − A5 −0.003; breadth counts 1,881/2,016;
  R_dev_xcheck_007 not run.

## v0.5.0: the constraint region as the engine; breadth families; projection-volume tie-break (study BRUTE-050-REGION-007)

Criteria pre-registered at `5be08aa` (`experiments/BRUTE_PLAN_007.json`); second implementation `1b57efe`
(`experiments/v050_reference.py`, same author, no `brute` import); implementation `fc2bed8`/`c8e8611`/`b693113`;
pre-freeze fix to the reference `0c86d90` and infrastructure `d7054a1`/`b2c4209`; source frozen at `064a50e`; scoring
scripts committed alone at `50e9321` (06:00:43 EDT), ledger `run_start_007` 06:11:52 EDT (11.2 min later), sealed at
`51215e0`. Criteria and scoring scripts unchanged afterwards. Deviations: `docs/research/BRUTE_DEVIATIONS_007.md` (Q0–Q7).

- **`brute/region.py`** (`RegionK`, `RegionSpace`): the constraint region for k actions and s sensors with tri-state
  SAT answers (True / False / UNKNOWN under a per-query conflict budget).
- **`brute/region_learner.py`** (`RegionBruteLearner`, arms A5 and M5): the v0.4.0 rules with every version-space query
  on the region; **SOLVER_BUDGET** overlay — a forecast that used an UNKNOWN answer is ABSTAIN, never CERTIFIED; policy
  `M` (projection-volume tie-break for LU-R ties).
- **`brute/breadth.py`** (B5/BM5/BP5) and pre-registered breadth families big6 (≤6/≤7), sens3 (3 sensors), act3
  (3 actions), ood6s3 (declared out of family); τ7 = 2.07944154168 calibrated on 450 in-family breadth cases.
- **API 1.5** (`brute/api/service_v050.py`, schemas `*.v1_5.json`); `brute.release_version_050`.
- **Study-007 (Observed):** 12 of 15 gated criteria pass. **GX1** A5 = A4 on all 25,344 steps (0 mismatches, 0
  excluded). **GX3** 257 budget-hit forecasts, all abstain. G1/G2 0 false certificates in every arm, incl. breadth
  and ood6s3. **Failed:** GX2 (0 mismatches, act3 only 84.5% of steps checkable by the reference, 90% registered),
  G3′ (M5 1 non-drift false certificate on drift4), G6b (M5 − A2 −0.0796 [−0.0996, −0.0602], predicted).
  **GM NOT DISTINGUISHED:** M5 − A5 +0.0262 [0.0109, 0.0425], BM5 − B5 +0.0391 [0.0204, 0.0579], but G3′ fails for M5.
  Second implementation 0/2,592 arm traces, mutation 20/20. Reproducibility 296/296 byte-identical.
- **GR2′ scaling (Observed raw, Inferred fits, not gated):** 0 UNKNOWN answers at n = 4..12 in three alphabets; clause
  maxima 2,323 → 15,055 (2a2s, n = 4 → 12); cubic fit near-interpolating (5 n values); power exponents 1.57–1.74 with
  curved residuals; enumeration too censored to fit; time noisy and non-monotone.
- **Process (post-start, labelled post hoc; review of v0.4.0):** `scripts/check_smoke_seeds_007.py` (smoke seeds
  901–903 disjoint from all 468 evaluation seeds; one held-out seed's world tables were printed by eye at 05:25, Q0);
  retroactive ledger entry for smoke runs; `experiments/v050_prob_reference.py` recomputes v0.90 forecast probabilities
  on taken and untaken branches (study-007 A4/A5/M5: 0/1,728 traces, 130,602 forecasts, swap mutations 20/20; also
  applied to study-006 as v0.4.0 errata E3); `scripts/scaling_fit.py` (stated models with residuals).
- `BRUTE_RELEASE_FREEZE_050.json` locks the scoring scripts, release verifier/test and the post-start audit scripts.
- `scripts/verify_release_050.py`, `tests/test_release_050.py` (version-parameterised, tamper cases).

## v0.4.0 errata (2026-10-25, docs and new post-hoc checks only; tag `v0.4.0` and sealed results unchanged)

From an external read-only review; details in `docs/research/v0.4.0/ERRATA.md`, new deviation P8 in
`docs/research/BRUTE_DEVIATIONS_006.md`, ledger `errata_040`. No number in the sealed results changed.

- **H1 (high).** Study code and the full scoring chain (incl. PAIRED R = 0.571 on 96 D7/D8 cases) ran on 96 **held-out**
  study-006 cases at 02:29–03:08 EDT, **before** the scoring-script commit `d9ddbe6`. "Committed before any study-006
  run", "smoke data only, not study data" and "before any v0.4.0 code" are withdrawn. GR1b's held-out status is
  weakened for the 16 overlapping cases; 96/576 cases were not blind when the scoring scripts were committed.
- **M1.** GR2 exponents "n^1.6 vs n^8.5" and "O(n^2 T)" withdrawn. Refit with residuals (*Inferred*): enumeration rows
  ≈ exponential (×6.9 per state, n=2..5, censored n=6 excluded); clauses ≈ cubic polynomial, O(T·n² + n³).
- **M2.** G11 checked forecast probabilities only for sum/floor/source in the v0.90 regime. Post-hoc recompute
  (`experiments/v050_prob_reference.py`): 0/1,152 A4+P4 traces mismatching, 88,038 forecasts, mutation 20/20.
- **M3.** GR1 is a development-set check (study-004/005 traces already used by design probes).
- **L1–L6.** P4 had 1 stale counterfactual certificate; n=6 SAT maxima were not budget hits; main D7/D8 block R = 1.5
  with 266/2,000 zero denominators; test suite red by construction; reference-vs-plan order *Open*; "before any code"
  qualified.

## v0.4.0: geometric representation of the version space (study BRUTE-040-GEOMETRY-006)

Criteria pre-registered at `5fa3628` (`experiments/BRUTE_PLAN_006.json`) before any `brute/` v0.4.0 code (design probes
ran earlier, P0); second implementation
`2eba00b`; implementation `2811904` + pre-freeze fix `b5e7077`; source frozen at `70a3c43`; scoring scripts committed
alone at `d9ddbe6` (03:08:51 EDT), ledger `run_start_006` at 03:20:15 EDT (11.4 min later), sealed at `454094c`.
Criteria and scoring scripts unchanged afterwards. **Errata: the scoring chain had been dry-run on 96 held-out cases
before `d9ddbe6` (P8).** Deviations: `docs/research/BRUTE_DEVIATIONS_006.md` (P0–P8).

- **`brute/geometry.py::ConstraintRegion`** — the version space as CNF over complete ≤n Moore machines (pysat Glucose3,
  canonical first-visit symmetry breaking); support = projection, saturation = sub-region emptiness, Y1k = fibre,
  observation = cut. **GR1** 0 mismatches in 778,840 items on 2,016 sealed study-004/005 traces; **GR1b** 0 in 470,318
  on study-006 (*Observed*; GR1 is development-set, GR1b weakened for 16 cases, errata). **GR2** scaling: ~~clauses ~n^1.6 vs enumeration rows ~n^8.5~~ (withdrawn, errata M1); SAT time noisy and
  non-monotone, 17 budget-unknown steps at n = 8–12, slopes on 5–8 points (*Observed*, not gated). Not used by the
  learner (*Exact*).
- **`brute/resume.py`** — A4/P4: v0.3.0 Y1k + LU-R with τ6 = 1.645215321642 (in-family calibration, G13) and a
  resumable alarm; D2 (two-step lookahead) and F2 (two-step fibre) candidates.
- **`brute/api/service_v040.py`** — API 1.4 (`schema/*.v1_4.json`): predict responses gain `resumed` and `alarm_resumes`; `tau` defaults to τ6.
- **perm4** — a new held-out family (each action a permutation of 4 states, one aliased emission pair), pre-registered before its data.
- **Results (*Observed*).** 15 of 16 gated criteria pass; **G6b′ fails** (A4 − A2 −0.104 [−0.116, −0.092],
  pre-registered). G5 passes (ood4 1/72; v0.3.0 τ also 1/72 on these seeds; perm4 2/72 vs 14/72). G15 (D2) and G16 (F2)
  fail; F2 breaks G3′. **G14′ D7/D8 OPEN**: R = 0.632 [0.418, 0.907] at N = 384 (power-analysed). Resume: 3 per arm,
  0 certificates after resume. G11 second implementation by the same author: 0 of 2,880 traces mismatching, mutation
  20/20. G12 byte-identical rerun.
- **Release hygiene.** `pyproject.toml` 0.4.0 with numpy 2.5.4 and python-sat 1.9.dev17 pinned;
  `scripts/verify_release_040.py` and `tests/test_release_040.py` read the version from `RELEASE.json`; fresh-clone
  checks restore the gitignored traces first (`scripts/study006_storage.py restore`).


## v0.3.0 errata (2026-10-25, docs and new checks only; tag `v0.3.0` and sealed results unchanged)

After an independent cold review (`docs/research/v0.3.0/ERRATA.md`). No criterion, scoring script, frozen file or sealed
result changed.

- G11 is reworded everywhere as a **second implementation by the same author, no `brute` import**, not an independent
  audit. New `scripts/audit_count_030.py` reports a real mismatch count (scans every arm trace; the frozen reference stops
  at the first mismatch) and has a mutation test (`tests/test_audit_mutation_030.py`). Result: 0 mismatching of 3,168 arm traces (*Observed*).
- G3′ headline now sits next to the extended-block result (A3 38 false / 2 non-drift / 4 stale on 216 cases).
- Process claims softened to what git shows (parent order, not time); P0 relabelled; DISCOVERIES D13 retitled to the
  OPEN verdict; G5 per-family wording clarified; evidence labels added to the README Status table; "not AGI" is Exact.
- `tests/test_tamper_by_version.py`: each release verifier (v0.1.0–v0.3.0) on its own tag tree passes and catches
  tampering. `scripts/check_order_030.py`: scoring scripts precede the sealed results and are unchanged.
- `requirements.txt` pins numpy 2.5.4 (the tested environment); `pyproject.toml` version 0.3.0. Quickstart restores the
  gitignored traces before the tests.

## v0.3.0: fibre-robust certification (study BRUTE-030-CHANGEPOINT-005)

Criteria pre-registered at `25fa47b` before any v0.3.0 code (pre-freeze probe code disclosed, deviation P0); source
frozen at `f7f3bd3` before the run; scoring scripts committed at `a1889b6`, the git parent of the sealed results (same
timestamp, so "before results were seen" is the author's report, not verifiable; errata E3). Criteria were not changed
afterwards. Deviations are in `docs/research/BRUTE_DEVIATIONS_005.md`.

- **Y1k certification** (`brute/changepoint.py::ChangePointBruteLearner`): a CERTIFIED forecast stays certified only if
  it is constant on the fibre of the n≤4 region over the latest observation (known edges; an unknown edge from the
  current state counts as any code); otherwise ABSTAIN with `RESYNC_AMBIGUOUS` (never issued).
- **LU-R experiments:** the v0.2.0 one-step lookahead scored with the Y1k gate. Optional `CHECK_RUN k` (0 in v0.3.0;
  k=3 only for the mechanism arm E2).
- **brute.api 1.3** (`BruteServiceV030`, `request/response.v1_3.json`): `RESYNC_AMBIGUOUS`, `experiment.check`,
  `proposal: NO_PROPOSAL` with `no_proposal_reason` after OUT_OF_FAMILY (bridge O3).
- **Version:** `brute/release_version_030.py` = 0.3.0 (earlier version files stay frozen).
- **Storage (D1):** sealed traces committed as deterministic gzip; `scripts/study005_storage.py restore`.
- **Study tooling:** five-arm runner (A3, P3, A2, P2, E2 + C and v0.90 controls) plus a 216-case extended drift4 block,
  τ calibration check, second implementation by the same author (no `brute` import), gates/paired/reproducibility generators with
  `--check`, `verify_release_030` (`--frozen` runs the unmodified v0.2.0 verifier on the raw v0.2.0 tree). Locks:
  `BRUTE_SOURCE_FREEZE_005`, `BRUTE_RELEASE_FREEZE_030`.
- **Results (Observed): 12 of 14 gated criteria pass; G5 and G6b fail.**
  - **G3′ passes:** drift4 A3 9 false certificates, all at drift steps, 0 stale (v0.2.0 A2: 15, 1 non-drift, 2 stale;
    v0.90: 89). 0 false certificates in family and on ood5 (taken, counterfactual, public), every arm.
  - G6 dual coverage gain A3 − P3 **+0.064352**, CI95 [0.055054, 0.073922].
  - **G6b fails (pre-registered risk):** A3 − A2 −0.098264, CI95 [−0.110885, −0.087267].
  - **G5 fails:** ood4 5 of 72 cases raise a residual-surprise alarm (0.069 > 0.05), identically in v0.1.1 and v0.2.0.
  - ood5 log-loss A3 0.63875, P3 = C 0.648728; drift4 A3 1.162304, P3 1.163681, A2 1.170786, C 1.181917.
  - G14 (D7/D8 single-mechanism test, not gated): **OPEN** — S(A2) 17, S(E2) 14, S(A3) 4.
  - Second implementation (same author, no `brute` import) ran to completion over 139,392 arm-steps (it stops at the
    first mismatch; errata count in E4); reproducibility byte-identical; τ reproduces.
- **Tests:** see README Status (measured on a fresh clone). Expected errors are frozen earlier-release version checks
  that fail by construction on the RELEASE.json bump (N1).

## v0.2.0: active experimentation and window rebuild (study BRUTE-020-ACTIVE-004)

Criteria pre-registered at `c0ac594` before any v0.2.0 code; source frozen at `8bf8759` before the run. Criteria were not
changed afterwards. Deviations and implementation notes are in `docs/research/BRUTE_DEVIATIONS_004.md`.

- **X1 active experimentation** (`brute/active.py::ActiveBruteLearner.experiment`): a one-step certifiability lookahead
  (LU) over copies of the n≤4 and n≤5 regions. Certification rules are unchanged.
- **X2 window rebuild:** a `window_n4` forecast tier after contradiction (n≤4 learner restarted at each contradiction).
- **X3 issuance de-duplication:** `record_issued` records a (step, certificate) pair once; fixes the bridge
  double-issuance bug (B1). Study-003 had 0 duplicates (Exact check, 504 cases).
- **X4 brute.api 1.2** (`BruteServiceV020`, `request/response.v1_2.json`): a read-only `experiment` op and response field
  (`action`, `score`, `scores`, `rule`, `tie_break`, `tied`, optional per-action `counts`).
- **X5 version:** `brute/release_version.py` = 0.2.0 (`brute.version` 0.1.1 and `brute.__version__` 0.1.0 stay frozen).
- **X6 clone hygiene:** `.gitattributes` `*.ps1 -text` (fixes 2 of the 3 tests failing on a fresh clone of main, B2),
  regenerated MANIFEST, README test count measured on a fresh clone.
- **Storage (D1):** the 133 MB sealed traces are committed as deterministic gzip; `scripts/study004_storage.py`
  restores and checks them against `SEAL.json`.
- **Study tooling:** three-arm runner (A active, P passive, C frozen v0.1.1), τ calibration check, second implementation by the same author (no `brute` import)
  gates/paired/reproducibility generators with `--check`, `verify_release_020` (runs the frozen
  v0.1.1 and v0.1.0 verifiers with `--frozen`). Locks: `BRUTE_SOURCE_FREEZE_004`, `BRUTE_RELEASE_FREEZE_020`.
- **Results (Observed): 12 of 13 gated criteria pass; G3′ fails.**
  - Dual coverage gain A − P pooled **+0.115355**, CI95 [0.10409, 0.127123]; every family CI excludes 0.
  - 0 false certificates in family (taken, counterfactual, public) and on ood5, both arms.
  - **drift4: A 24 wrong of 221, 3 at non-drift step 13 → G3′ fails;** P 1 of 16 (passes); v0.90 81.
  - ood5 log-loss A 0.665014, P = C 0.67712; drift4 A 1.034239, P 1.056963, C 1.06755, suffix-1 1.181247.
  - Independent audit 0 mismatches; reproducibility byte-identical; τ reproduces.
- **Tests:** see README Status (measured on a fresh clone). 2 expected errors are frozen earlier-release version checks
  that fail by construction on the RELEASE.json bump (N1).

## v0.1.1: open-world fallback forecast (study BRUTE-011-FALLBACK-003)

Pre-registered at `1585a77` before any v0.1.1 code. The owner chose G3′ over G3 before the freeze. Criteria were not
changed afterwards. Deviations are listed in `docs/research/BRUTE_DEVIATIONS_003.md`.

- **F0 freeze hygiene:** the study-001, study-002 and v0.1.0 release locks are unchanged. New code is in new files.
  `brute.version.RELEASE_VERSION = '0.1.1'`; `brute.__version__` stays `0.1.0` (amendment A3).
- **F1 fallback forecast** (`brute/fallback.py::FallbackBruteLearner`): after the n≤4 family is contradicted, it
  forecasts from the n≤5 margin support while that support is consistent, otherwise from suffix-1, always with the ε
  reserve. It does not certify more than before. Before a contradiction it is identical to v0.1.0, verified on 15,840
  in-family steps.
- **F3 brute.api 1.1** (`BruteServiceV011`, `request/response.v1_1.json`): `forecast_source` and per-retraction reasons
  (`falsified_by_observation`, `scope_withdrawn`, `unverifiable_masked`).
- **F4 witness audit** (`scripts/witness_audit.py`): n≤5 divergent witnesses, each verified by replay.
- **Study tooling:** a two-arm lockstep runner, a τ calibration check, a second implementation by the same author (no `brute` import),
  gates/paired/reproducibility/R4 generators with `--check`, and `verify_release_011` (pre-registration order check;
  `--frozen-v010` runs the frozen v0.1.0 verifier on `git archive v0.1.0`). Locks: `BRUTE_SOURCE_FREEZE_003`,
  `BRUTE_RELEASE_FREEZE_011`.
- **Results (Observed):** all 11 gated criteria pass.
  - ood5 log-loss 0.624547 (v0.1.0: 1.480828; ln 4 = 1.386294).
  - drift4 log-loss 1.155589 (v0.1.0: 1.298329; suffix-1: 1.167906).
  - False certificates: 0 in family, 0 on ood5, 4 on drift4, all at perturbation steps (v0.90 control: 83 and 71).
  - Coverage is unchanged from v0.1.0.
  - The original G3 would fail (4 wrong drift4 certificates).
- **Tests:** 127 tests, 126 pass. 1 expected error: the frozen v0.1.0 tamper test fails on the version bump (A3, D2)


## v0.1.0: verified abstention (study BRUTE-010-ABSTENTION-002)

Pre-registered at `d402c75` before implementation. Criteria were not changed afterwards; deviations are listed in
`docs/research/BRUTE_DEVIATIONS_002.md`.

- **F1 contradiction and retraction:** OUT_OF_FAMILY when no machine fits; certificates falsified by an observation are
  withdrawn with receipts.
- **F2 margin gate:** a certificate needs an n≤4 family support and an n≤5 margin support that agree.
- **F3 saturation:** abstain when every surviving machine uses the full state bound.
- **F4 residual surprise:** windowed test with W=8 and τ=1.433141502274, calibrated on separate seeds.
- **F5 named family:** an explicit family-contradicted event; every certificate names its family and is checked against
  the surviving belief.
- **F6 coverage:** coverage, selective risk and abstentions by reason per family, with a consistent burn-in.
- **F7 open-world reserve:** ε=0.02, so the minimum probability is 0.005, replacing the 1e-12 floor.
- **F8 v0.89 comparison:** the per-step v0.89 score is recorded and scored on its valid steps.
- **F9 generators:** GATES, PAIRED_ANALYSIS, API_REPLAY and EXPLORATORY each have a generator with `--check`.
  `verify_release` raises `VerificationError` (survives `python -O`) and asserts no study numbers.
- **F10 timing:** all wall-clock fields are `*_informational` and stripped from SCIENTIFIC.json. Calibration and
  scientific results rerun byte-identical (`REPRODUCIBILITY.json`).
- **F11 public path:** a public certificate requires an explicit scope attestation (`ScopeAttestation`).
- **F12 hygiene:** the baseline zip is optional and checked only if present; MANIFEST is built from tracked files;
  `package_release` uses `git archive`; `pyproject.toml` added.
- **F13 defaults:** a single `DEFAULT_MAX_PREFIXES` (160000) is used by the family, the margin and the API.
- **brute.api v1:** JSON request and response schemas, a service, alphabet, refusals.
- **adapters/language:** template-only renderer and grounding checker.
- **Tests:** 104 (69 inherited, 35 new).
- **Results:** 0 false certificates in all 7 families (v0.90 control: 156). Gates C1–C5, C7, C10 and C11 pass.
  **C6 fails** (ood5 log-loss 1.504767 > ln 4). Coverage fell sharply against v0.90.
- Not done: F14 (`learner_witness_audit`, the bounded n≤5 witness audit); its F2 target is covered indirectly by
  the margin gate and the API replay of the study-001 false certificates. No language model is connected.

The BGR v0.90.0 changelog is preserved at `docs/research/bgr-v0.90.0/CHANGELOG.md`.
