# Brute changelog

## v0.3.0: fibre-robust certification (study BRUTE-030-CHANGEPOINT-005)

Criteria pre-registered at `25fa47b` before any v0.3.0 code (pre-freeze probe code disclosed, deviation P0); source
frozen at `f7f3bd3` before the run; scoring scripts committed at `a1889b6` before results were inspected. Criteria were
not changed afterwards. Deviations are in `docs/research/BRUTE_DEVIATIONS_005.md`.

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
  τ calibration check, independent reference (no `brute` import), gates/paired/reproducibility generators with
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
  - Independent audit 0 mismatches (139,392 arm-steps); reproducibility byte-identical; τ reproduces.
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
- **Study tooling:** three-arm runner (A active, P passive, C frozen v0.1.1), τ calibration check, independent reference
  (no `brute` import), gates/paired/reproducibility generators with `--check`, `verify_release_020` (runs the frozen
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
- **Study tooling:** a two-arm lockstep runner, a τ calibration check, an independent reference (no `brute` import),
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
