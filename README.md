<p align="center">
  <img src="assets/brand/lockup.png" alt="Brute" width="520">
</p>

<p align="center"><b>A reasoner that abstains on what it cannot verify, and now chooses experiments that let it verify more.</b><br>
<sub>Brute v0.2.0 · forked from BGR v0.90.0 · research preview · not AGI</sub></p>

---

## Overview

Brute is a small, exact reasoner for hidden finite-state worlds. It watches actions and masked sensor readings, keeps every hidden machine that is still consistent with the evidence (the *version space*, a region), and predicts the next reading **only** when every surviving explanation agrees (the region's projection onto that reading is a single point, and an n≤5 margin agrees).

v0.1.x only watched. **v0.2.0 also acts:** `ActiveBruteLearner` picks the next action by a one-step lookahead (LU) that scores each action by how many next-step certificates its possible answers would allow. The certification rule is unchanged. After a contradiction a new `window_n4` tier forecasts from an n≤4 learner restarted at each contradiction. On the pre-registered study-004 (504 held-out cases) **12 of 13 gated criteria pass. G3′ (drift4) fails for the active arm:** 3 wrong certificates one step after an unannounced change. The failure is kept on the record; no threshold was changed.

Brute is a fork of **BGR (Bitwork Geometric Reasoning) v0.90.0**, and that research is credited in full ([`FORK.md`](FORK.md)).

## Status

| | |
| --- | --- |
| Version | 0.2.0 (`RELEASE.json`, `brute.release_version.RELEASE_VERSION`). `brute.version.RELEASE_VERSION` stays `0.1.1` and `brute.__version__` stays `0.1.0`, because those files are in earlier freezes |
| Tests | `python -m unittest discover -s tests`: **@@TESTS@@** |
| Study | `BRUTE-020-ACTIVE-004`: criteria frozen at commit `c0ac594` before any v0.2.0 code; source frozen at `8bf8759` before the run. 7 families × 24 new held-out seeds × 3 mask rates = 504 cases. Arms: **A** active, **P** passive (same learner, fixed actions), **C** frozen v0.1.1 on P's sequence, plus the v0.90 control |
| Gates | **12 of 13 pass; G3′ fails** ([`results/study-004/GATES.json`](results/study-004/GATES.json)) |
| Verifier | `python -m scripts.verify_release_020 --fast` (seals, freezes, regenerated gates and paired analysis, ledger, manifest, git order); without `--fast` it re-runs the independent reference; `--frozen` also runs the frozen v0.1.1 and v0.1.0 verifiers on their own blobs |
| Interface | `brute.api` 1.0, 1.1 and **1.2** (`BruteServiceV020`: an `experiment` op and field). Template-only language adapter. No language model is connected |
| Storage | The two 133 MB sealed traces are committed as deterministic gzip (`*.json.gz`); `python scripts/study004_storage.py restore` rebuilds them and checks them against `SEAL.json` (deviation D1) |

Every claim in this README carries a label:

- **Exact**: proved or verified by the tests or by exact computation in this repository.
- **Observed**: measured in study-004 (`results/study-004/SCIENTIFIC.json`, sealed), or in earlier studies where stated.
- **Simulated**: a counterfactual predictor rescored on earlier sealed traces (design evidence, not pre-registered evidence).
- **Inferred**: reasoning, not measured.
- **Rejected**: considered and dropped, with the reason given.
- **Open**: unresolved.

## Study-004 against the pre-registered criteria (*Observed*)

| Criterion | Result | Key numbers |
| --- | --- | --- |
| G1 in-family soundness, A and P, taken and counterfactual action, public | PASS | 0 false of 5,233 taken + 510 counterfactual certificates (A); 0 of 1,336 + 1,379 (P); 0 public false |
| G2 ood5 false certificates = 0 | PASS | A 0 of 112 (+1 counterfactual); P 0 of 5; v0.90 control 74 of 193 |
| **G3′ drift4: 0 wrong at non-drift steps and total ≤ 50% of v0.90** | **FAIL (A); P passes** | **A 24 of 221, 3 at non-drift step 13** (seeds 1390010, 1390011 at mask 0.1; 1390016 at 0.35); total within limit 40.5. P 1 of 16 (drift step 23). v0.90: 81 |
| G4 public safety | PASS | 0 public certificates on ood5/drift4; 0 public false anywhere |
| G5 in-family false-alarm cases ≤ 5% | PASS | 0 of 72 in every in-family family, both arms |
| **G6 active coverage gain** (pooled A − P ≥ 0.05, CI > 0, no family < −0.01) | PASS | **+0.115355, CI95 [0.10409, 0.127123]**; every family CI excludes 0 |
| G7 open-world no regression (A, P ≤ C on ood5 and drift4; ≤ ln 4; min p ≥ 0.005) | PASS | ood5 A 0.665014 / P 0.67712 / C 0.67712; drift4 A 1.034239 / P 1.056963 / C 1.06755; min p 0.005 |
| G8 passive equivalence (P ≡ C except window steps; A in-family ≤ C + 0.05) | PASS | 0 differing steps in 22,176; A in-family log-loss below C in every family |
| G9 retraction semantics + de-duplication | PASS | 145 retractions (20 falsified = 20 wrong with a contradicting bit, 83 scope withdrawn, 42 unverifiable); 0 duplicate pairs; dedup unit tests pass |
| G10 compute budget | PASS | peak 103,814 of 160,000 rows; 0 lookahead budget hits; 0 exhaustions; wall clock A/C 1.19 |
| G11 independent audit | PASS | 504 cases, 22,176 steps per arm, 0 mismatches (no `brute` import) |
| G12 reproducibility | PASS | rerun `CALIBRATION_CHECK.json` and `SCIENTIFIC.json` byte-identical |
| G13 τ reproduces | PASS | τ = 1.433141502274 from P and C |

Paired, seed-clustered bootstrap (2,000 resamples, seed 20261025; [`PAIRED_ANALYSIS.json`](results/study-004/PAIRED_ANALYSIS.json)). Both D2 tooling edits are storage-only and the pre-results scripts reproduce `GATES.json` and `PAIRED_ANALYSIS.json` byte for byte ([deviations](docs/research/BRUTE_DEVIATIONS_004.md)).

### Coverage and log-loss after burn-in (*Observed*)

| Family | Dual coverage P → A | On-policy A | Counterfactual certs P → A | Log-loss C / P / A |
| --- | --- | ---: | --- | --- |
| cycle3 | 0.193 → **0.314** | 0.539 | 495 → 233 | 0.2303 / 0.2303 / **0.1991** |
| switch3 | 0.162 → **0.293** | 0.515 | 439 → 184 | 0.2380 / 0.2380 / **0.1958** |
| unstructured3 | 0.086 → **0.205** | 0.391 | 228 → 51 | 0.1175 / 0.1175 / **0.0984** |
| unaliased2 | 0.072 → **0.236** | 0.461 | 206 → 29 | 0.0967 / 0.0967 / **0.0842** |
| ood4 | 0.004 → **0.046** | 0.088 | 11 → 13 | 0.3547 / 0.3547 / **0.3303** |
| ood5 | 0.001 → 0.021 | 0.042 | 3 → 1 | 0.6771 / 0.6771 / **0.6650** |
| drift4 | 0.006 → 0.039 | 0.076 | 22 → 7 | 1.0676 / 1.0570 / **1.0342** |

drift4 P − suffix-1 = −0.1243, CI95 [−0.2612, −0.0006]: the first drift forecast whose interval excludes the frequency-table baseline. P − C on drift4 is −0.0106 [−0.0372, +0.0163], not distinguishable. Findings and their math are in [`docs/research/DISCOVERIES.md`](docs/research/DISCOVERIES.md) (D6–D10).

## What Brute can't do yet

- **It certifies on a stale model right after the rules change, more often when it acts.** On drift4 the active arm issued 221 certificates and 24 were wrong (selective risk 0.122), against 1 of 16 for the passive arm. 21 came at the drift steps (12, 23, 34), which no causal learner can avoid, but **3 came one step later (step 13)**, which is why G3′ fails. All 24 were later withdrawn. A change-point test that withholds certification just after a surprise is not implemented. *Observed* (errors), *Inferred* (remedy).
- **Its experiments are greedy and one step deep.** LU exploits what it already knows: on-policy coverage is about twice dual coverage, and certificates for the action not taken fall (cycle3 495 → 233). It has no multi-step or information-value objective. *Observed.*
- **It still certifies far less than v0.90 in places.** Active dual coverage is 0.21–0.31 in family and 0.046 on ood4, against v0.90's 0.34–0.58 (study-003). The gate is unchanged; every margin abstention in study-003 had a verified n≤5 witness. *Observed.*
- **Its drift forecasts only just beat a frequency table.** drift4 1.0342 (A) and 1.0570 (P) against suffix-1 1.1812; P's interval upper end is −0.0006. The margin over v0.1.1 is not significant. *Observed.*
- **It gets 5-state worlds right only up to 5 states.** No n≤6 margin or 5-state certificates (R4 not attempted: the n≤5 margin already peaks at 103,814 rows). *Observed* (budget), *Inferred* (n≤6 would not fit).
- **It still pays ln 200 = 5.298 on every contradiction step.** *Exact* (ε reserve design).
- **It does not grow its own model class or representation.** Regions are enumerated rows. *Exact.*
- **Public certificates need an outside attestation.** *Exact.*
- **It only works on a toy domain:** 2 actions, 2 binary sensors, deterministic Moore machines, an n≤4 family with an n≤5 margin. *Exact.*
- **The language adapter is templates only.** No free-form questions. *Exact.*
- **It is not AGI,** and nothing here shows general intelligence. *Open.*

The plan for v0.3.0 is in [`NEXT_ITERATION.md`](NEXT_ITERATION.md); the longer path is in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Quickstart

Requires Python 3.11+ and NumPy. No GPU, network, or model weights.

```bash
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute
python -m pip install -r requirements.txt
python -m unittest discover -s tests            # see Status for the count
python -m scripts.verify_release_020 --fast      # restores the study-004 traces, then seals, freezes, gates, ledger, manifest, git order
python -m scripts.verify_release_020             # also re-runs the study-004 independent reference (long)
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

An active experiment through API 1.2 (read-only; it changes no evidence):

```python
from brute.api.service_v020 import BruteServiceV020
s = BruteServiceV020()
s.handle({"api_version": "brute.api/1.2", "session_id": "demo", "op": "initialize",
          "observation": {"x": 0, "y": 0}, "family": {"max_states": 4}})
print(s.handle({"api_version": "brute.api/1.2", "session_id": "demo", "op": "experiment"}))
```

To rerun the calibration check and study-004 in a scratch directory and compare bytes with the sealed files (long-running):

```bash
python scripts/make_reproducibility_004.py --workers 4
```

## How it works

1. **Family support** (`brute/core`, `BruteLearner`): the exact symbolic support over n≤4 Moore machines (inherited from `bgr90`).
2. **Margin gate:** an n≤5 support must agree before Brute certifies. If the two disagree, it abstains with MARGIN_DISAGREES.
3. **Saturation check:** if every surviving explanation uses all 4 states, the bound may be the reason they agree, so Brute abstains with BOUND_SATURATED.
4. **Residual surprise:** a windowed (W=8) surprise test, with τ = 1.433141502274 calibrated on separate seeds (`CALIBRATION.json`), raises OUT_OF_FAMILY.
5. **Contradiction and retraction:** when no machine fits, Brute answers OUT_OF_FAMILY and withdraws issued certificates with a reason (falsified by observation, scope withdrawn, or unverifiable because masked).
6. **Fallback forecast (v0.1.1, `brute/fallback.py`):** after contradiction it forecasts from the n≤5 margin support (uniform over it, with the ε reserve) while that support is consistent, otherwise from a one-step suffix-frequency table. `forecast_source` names which.
7. **Active experiment (v0.2.0, `brute/active.py`):** for each action a and each possible reading c in the n≤4 support, intersect copies of the n≤4 and n≤5 regions with obs(a)=c and count the actions b that would then be CERTIFIED; take the action with the highest mean count (ties: the default action). Certification is unchanged.
8. **Window rebuild (v0.2.0):** after a contradiction, a fresh n≤4 learner restarted at each contradiction restricts the suffix-1 forecast (`forecast_source = window_n4`) when the margin support is gone.
9. **Open-world reserve:** ε = 0.02 is spread over all readings, so no probability falls below 0.005.
10. **`brute.api`:** versioned JSON request and response schemas (`brute/api/schema/*.v1.json`) and a service that never raises.
11. **Language adapter:** template rendering plus a checker that rejects any sentence not grounded in a response field.

## Repository

| Path | Contents |
| --- | --- |
| `brute/core`, `brute/evaluation.py` | The v0.1.0 learner and evaluator (study-002 freeze) |
| `brute/api`, `adapters/language` | The API contract, service, and template language adapter (release freeze) |
| `brute/fallback.py`, `brute/api/service_v011.py` | v0.1.1 learner and API 1.1 (study-003 freeze) |
| `brute/active.py`, `brute/api/service_v020.py`, `brute/release_version.py` | v0.2.0 learner and API 1.2 (study-004 freeze) |
| `experiments/BRUTE_PLAN_004.json` | The study-004 pre-registration (`c0ac594`); `BRUTE_SOURCE_FREEZE_004.json` and `BRUTE_RELEASE_FREEZE_020.json` lock v0.2.0 code |
| `results/study-004/` | Sealed traces (gzip), seal, calibration check, independent audit, gates, paired analysis, reproducibility |
| `experiments/BRUTE_PLAN_003.json` | The study-003 pre-registration; `BRUTE_SOURCE_FREEZE_003.json` and `BRUTE_RELEASE_FREEZE_011.json` lock v0.1.1 code. Earlier plans and locks are kept |
| `results/study-003/` | Sealed results, calibration check, independent audit, gates, paired analysis, reproducibility, witness audit, drift stress |
| `results/study-002/` | Sealed results, calibration, audit, gates, paired analysis, reproducibility, API replay, exploratory |
| `results/study-001/`, `bgr*/` | Inherited BGR v0.90 evidence and code, byte-identical |
| `results/RESEARCH_LEDGER.jsonl` | Local unsigned SHA chain of research events |
| `docs/research/` | Inherited research record, [`BRUTE_DEVIATIONS_002.md`](docs/research/BRUTE_DEVIATIONS_002.md), [`BRUTE_DEVIATIONS_003.md`](docs/research/BRUTE_DEVIATIONS_003.md), [`BRUTE_DEVIATIONS_004.md`](docs/research/BRUTE_DEVIATIONS_004.md), [`DISCOVERIES.md`](docs/research/DISCOVERIES.md) |

## Credit and provenance

Brute is derived from BGR v0.90.0 (Bitwork Geometric Reasoning). The original README, CHANGELOG, RELEASE.json, and NEXT_ITERATION are preserved under [`docs/research/bgr-v0.90.0/`](docs/research/bgr-v0.90.0/). Study-001 results and ledger entries are unchanged.
