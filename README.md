<p align="center">
  <img src="assets/brand/lockup.png" alt="Brute" width="520">
</p>

<p align="center"><b>A reasoner that abstains on what it cannot verify.</b><br>
<sub>Brute v0.1.1 · forked from BGR v0.90.0 · research preview · not AGI</sub></p>

---

## Overview

Brute is a small, exact reasoner for hidden finite-state worlds. It watches actions and masked sensor readings, keeps every hidden machine that is still consistent with the evidence, and predicts the next reading **only** when every surviving explanation agrees.

v0.1.0 made Brute abstain when it could not verify a prediction, but it then forecast *worse than guessing* on 5-state worlds (study-002, C6 failed: ood5 1.504767 > ln 4). **v0.1.1 fixes the forecast without loosening certification:** after the n≤4 family is contradicted it forecasts from the n≤5 margin support when that is still consistent, else from a one-step suffix-frequency table. Before a contradiction it is byte-for-byte the v0.1.0 learner. On the pre-registered study-003 **all 11 gated criteria pass**, with G3′ (the owner-chosen drift criterion) in place of the original G3, which would have failed.

Brute is a fork of **BGR (Bitwork Geometric Reasoning) v0.90.0**, and that research is credited in full ([`FORK.md`](FORK.md)).

## Status

| | |
| --- | --- |
| Version | 0.1.1 (`RELEASE.json`, `brute.version.RELEASE_VERSION`). `brute.__version__` stays `0.1.0` because `brute/__init__.py` is in the study-002 freeze (amendment A3) |
| Tests | `python -m unittest discover -s tests`: **127 tests: 126 pass, 1 expected error** (the frozen v0.1.0 `test_verify_fails_under_tampered_results`, which fails on the RELEASE.json bump by construction, amendment A3; see deviation D2) |
| Study | `BRUTE-011-FALLBACK-003`: pre-registered at commit `1585a77` before any v0.1.1 code. 7 families × 24 new held-out seeds × 3 mask rates = 504 cases, v0.1.1 and a v0.1.0 control run in lockstep |
| Gates | **11 of 11 gated criteria pass** ([`results/study-003/GATES.json`](results/study-003/GATES.json)). The original G3 (drift4 false certificates = 0) was not gated and would fail: 4 |
| Verifier | `python -m scripts.verify_release_011` (full: re-runs the independent reference) or `--fast`; `--frozen-v010` also runs the frozen v0.1.0 verifier on `git archive v0.1.0` |
| Interface | `brute.api` 1.0 (unchanged) and 1.1 (`BruteServiceV011`: `forecast_source`, retraction reasons). Template-only language adapter. No language model is connected |

Every claim in this README carries a label:

- **Exact**: proved or verified by the tests or by exact computation in this repository.
- **Observed**: measured in study-003 (`results/study-003/SCIENTIFIC.json`, sealed), or in study-002 / study-001 where stated.
- **Simulated**: a counterfactual predictor rescored on earlier sealed traces (design evidence, not pre-registered evidence).
- **Inferred**: reasoning, not measured.
- **Rejected**: considered and dropped, with the reason given (see [`BRUTE_v0.1.1_PLAN.md`](BRUTE_v0.1.1_PLAN.md) §2).
- **Open**: unresolved.

## Study-003 against the pre-registered criteria (*Observed*)

Arms on the same 504 cases: **v0.1.1**, **v0.1.0** control (frozen learner), **v0.90** control.

| Criterion | Result | v0.1.1 | v0.1.0 | v0.90 |
| --- | --- | --- | --- | --- |
| G1 in-family soundness (cycle3, switch3, unstructured3, unaliased2, ood4) | PASS | 0 false of 1,430 certificates; 0 public false | 0 of 1,430 | 0 of 5,962 |
| G2 ood5 false certificates = 0 | PASS | 0 of 2 | 0 of 2 | 83 of 218 |
| G3′ drift4: 0 wrong at non-perturbation steps and total ≤ 50% of v0.90 | PASS | 4 of 24, all at perturbation steps 12/34; 0 elsewhere; limit 35.5 | 4 of 24 | 71 of 307 (23 at perturbation steps) |
| G4 public safety | PASS | 0 public certificates on ood5/drift4; 0 public false anywhere | | |
| G5 in-family false-alarm cases ≤ 5% | PASS | max 3 of 72 (ood4, 4.2%); 0 in the other four | | |
| **G6 open-world log-loss** ≤ ln 4 = 1.386294; drift4 ≤ v0.1.0; min p ≥ 0.005 | PASS | **ood5 0.624547; drift4 1.155589**; min p 0.005 | ood5 1.480828; drift4 1.298329 | ood5 2.294628; drift4 2.164106 |
| G7 in-family unchanged: (a) ≤ v0.90 + 0.05, (b) identical to v0.1.0 before contradiction, (c) τ reproduces | PASS | largest cost +0.0140 (unaliased2); 15,840 in-family steps identical; τ = 1.433141502274 | | |
| G8 retraction semantics | PASS | 26 retractions: 4 falsified (= 4 wrong), 18 scope withdrawn, 4 unverifiable (masked); 0 wrong certificates in never-contradicted cases | | |
| G9 compute budget | PASS | peak 102,806 of 160,000 rows; 0 exhaustions; wall clock 0.994 × v0.1.0 | | |
| G10 independent audit | PASS | 504 cases, 22,176 steps, 0 mismatches (no `brute` import) | | |
| G11 reproducibility | PASS | rerun `CALIBRATION_CHECK.json` and `SCIENTIFIC.json` byte-identical | | |

Paired, seed-clustered bootstrap (2,000 resamples, seed 20261024; [`PAIRED_ANALYSIS.json`](results/study-003/PAIRED_ANALYSIS.json)), post-burn-in log-loss differences with 95% intervals:

| | ood5 | drift4 |
| --- | --- | --- |
| v0.1.1 − v0.1.0 | −0.8563 [−0.9052, −0.8058] | −0.1427 [−0.1905, −0.0988] |
| v0.1.1 − uniform | −0.7617 [−0.8087, −0.7134] | −0.2307 [−0.4137, −0.0794] |
| v0.1.1 − suffix-1 baseline | −0.6602 [−0.7081, −0.6130] | −0.0123 [−0.1533, +0.1071] (not distinguishable) |

### Coverage and log-loss after burn-in (*Observed*)

| Family | Coverage v0.1.1 (= v0.1.0) | Coverage v0.90 | Log-loss v0.1.1 | Log-loss v0.1.0 | Log-loss v0.90 | Suffix-1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cycle3 | 0.197 | 0.524 | 0.1930 | 0.1930 | 0.1815 | 1.2340 |
| switch3 | 0.164 | 0.456 | 0.2327 | 0.2327 | 0.2224 | 1.1896 |
| unstructured3 | 0.094 | 0.375 | 0.1395 | 0.1395 | 0.1258 | 1.0687 |
| unaliased2 | 0.088 | 0.344 | 0.1131 | 0.1131 | 0.0991 | 1.1312 |
| ood4 | 0.006 | 0.581 | 0.4137 | 0.4137 | 0.4088 | 1.2437 |
| ood5 | 0.001 | 0.075 | **0.6245** | 1.4808 | 2.2946 | 1.2848 |
| drift4 | 0.006 | 0.109 | **1.1556** | 1.2983 | 2.1641 | 1.1679 |

Coverage did not change, by design: v0.1.1 changes only forecasts after a contradiction. Per mask rate, ood5 is 0.3233 / 0.5494 / 1.0009 and drift4 0.9456 / 1.1499 / **1.3713** at mask 0.1 / 0.35 / 0.6. Study-002 numbers for v0.1.0 are in [`results/study-002/GATES.json`](results/study-002/GATES.json).

Reported, not gated: R3 found 0 n≤5 divergent witnesses on 1,456 CERTIFIED steps and a witness on all 4,226 MARGIN_DISAGREES steps ([`WITNESS_AUDIT.json`](results/study-003/WITNESS_AUDIT.json)). R4, replaying the study-001 drift4 design seeds, gives 6 of 19 wrong, all at perturbation steps, log-loss 1.163555 against 1.331950 for v0.1.0 ([`DRIFT_STRESS_R4.json`](results/study-003/DRIFT_STRESS_R4.json)).

## What Brute can't do yet

- **It cannot prevent wrong certificates when the rules change.** On drift4 it issued 24 certificates and 4 were wrong (selective risk 0.27). All 4 came at the moment the world changed (steps 12 and 34), with both learners agreeing and no alarm. Each one was withdrawn at the next observation, falsified by it. The study-001 replay gives 6 of 19. The original zero-error drift criterion G3 would fail. *Observed.*
- **It certifies far less than v0.90.** In-family coverage is 0.09–0.20, against 0.34–0.52 for v0.90. On ood4 it is 0.006 against 0.581. That is 1,430 in-family certificates where v0.90 issued 5,962, unchanged from v0.1.0. Across all 7 families, every one of the 4,226 MARGIN_DISAGREES abstentions has a verified n≤5 machine that predicts differently, so the gate is doing its job. Getting coverage back needs a larger model class, not a looser gate. *Observed.*
- **Its forecasts after a drift are only as good as a frequency table.** drift4 log-loss is 1.1556 against 1.1679 for suffix-1; the paired interval [−0.153, +0.107] includes 0. At mask 0.6 it is 1.3713: slightly *worse* than v0.1.0 (1.3631) and close to uniform (1.3863). On drift4, 60 of 442 margin-forecast steps had a reading outside the margin support. *Observed.*
- **It gets 5-state worlds right only up to 5 states.** The ood5 gain (0.6245, against 1.4808 for v0.1.0) comes from the n≤5 margin, which here is never contradicted and always contains the actual reading. Beyond 5 states it falls back to suffix-1. That case was not tested. *Observed* for ood5, *Inferred* beyond it.
- **It still pays ln 200 = 5.298 on every contradiction step:** 61 steps on ood5 and 65 on drift4, which together are the single largest loss term per step. *Observed.*
- **It does not grow its own model class.** The n≤5 margin is used only as a forecast, never promoted to a certificate. *Exact.*
- **Public certificates need an outside attestation.** Brute cannot validate its own scope. *Exact.*
- **It only works on a toy domain:** 2 actions, 2 binary sensors, deterministic Moore machines, an n≤4 family with an n≤5 margin. *Exact.*
- **The language adapter is templates only.** No free-form questions. *Exact.*
- **It is not AGI,** and nothing here shows general intelligence. *Open.*

The plan for v0.2.0 is in [`NEXT_ITERATION.md`](NEXT_ITERATION.md).

## Quickstart

Requires Python 3.11+ and NumPy. No GPU, network, or model weights.

```bash
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute
python -m pip install -r requirements.txt
python -m unittest discover -s tests            # see Status for the count
python -m scripts.verify_release_011 --fast      # seals, freezes, regenerated gates, ledger, manifest, git order
python -m scripts.verify_release_011             # also re-runs the study-003 independent reference (minutes)
```

A minimal API session:

```python
from brute.api import BruteService
s = BruteService()
s.handle({"api_version": "brute.api/1.0", "session_id": "demo", "op": "initialize",
          "observation": {"x": 0, "y": 0}, "family": {"max_states": 4}})
s.handle({"api_version": "brute.api/1.0", "session_id": "demo", "op": "observe",
          "action": "a", "observation": {"x": 0, "y": None}})
print(s.handle({"api_version": "brute.api/1.0", "session_id": "demo", "op": "predict", "action": "b"}))
```

To rerun the calibration check and study-003 in a scratch directory and compare bytes with the sealed files (long-running):

```bash
python -m scripts.make_reproducibility_003 --check
```

## How it works

1. **Family support** (`brute/core`, `BruteLearner`): the exact symbolic support over n≤4 Moore machines (inherited from `bgr90`).
2. **Margin gate:** an n≤5 support must agree before Brute certifies. If the two disagree, it abstains with MARGIN_DISAGREES.
3. **Saturation check:** if every surviving explanation uses all 4 states, the bound may be the reason they agree, so Brute abstains with BOUND_SATURATED.
4. **Residual surprise:** a windowed (W=8) surprise test, with τ = 1.433141502274 calibrated on separate seeds (`CALIBRATION.json`), raises OUT_OF_FAMILY.
5. **Contradiction and retraction:** when no machine fits, Brute answers OUT_OF_FAMILY and withdraws issued certificates with a reason (falsified by observation, scope withdrawn, or unverifiable because masked).
6. **Fallback forecast (v0.1.1, `brute/fallback.py`):** after contradiction it forecasts from the n≤5 margin support (uniform over it, with the ε reserve) while that support is consistent, otherwise from a one-step suffix-frequency table. `forecast_source` names which.
7. **Open-world reserve:** ε = 0.02 is spread over all readings, so no probability falls below 0.005.
8. **`brute.api`:** versioned JSON request and response schemas (`brute/api/schema/*.v1.json`) and a service that never raises.
9. **Language adapter:** template rendering plus a checker that rejects any sentence not grounded in a response field.

## Repository

| Path | Contents |
| --- | --- |
| `brute/core`, `brute/evaluation.py` | The v0.1.0 learner and evaluator (study-002 freeze) |
| `brute/api`, `adapters/language` | The API contract, service, and template language adapter (release freeze) |
| `brute/fallback.py`, `brute/api/service_v011.py` | v0.1.1 learner and API 1.1 (study-003 freeze) |
| `experiments/BRUTE_PLAN_003.json` | The study-003 pre-registration; `BRUTE_SOURCE_FREEZE_003.json` and `BRUTE_RELEASE_FREEZE_011.json` lock v0.1.1 code. Earlier plans and locks are kept |
| `results/study-003/` | Sealed results, calibration check, independent audit, gates, paired analysis, reproducibility, witness audit, drift stress |
| `results/study-002/` | Sealed results, calibration, audit, gates, paired analysis, reproducibility, API replay, exploratory |
| `results/study-001/`, `bgr*/` | Inherited BGR v0.90 evidence and code, byte-identical |
| `results/RESEARCH_LEDGER.jsonl` | Local unsigned SHA chain of research events |
| `docs/research/` | Inherited research record, [`BRUTE_DEVIATIONS_002.md`](docs/research/BRUTE_DEVIATIONS_002.md), [`BRUTE_DEVIATIONS_003.md`](docs/research/BRUTE_DEVIATIONS_003.md) |

## Credit and provenance

Brute is derived from BGR v0.90.0 (Bitwork Geometric Reasoning). The original README, CHANGELOG, RELEASE.json, and NEXT_ITERATION are preserved under [`docs/research/bgr-v0.90.0/`](docs/research/bgr-v0.90.0/). Study-001 results and ledger entries are unchanged.
