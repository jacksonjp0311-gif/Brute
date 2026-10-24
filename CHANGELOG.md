# Brute changelog

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
