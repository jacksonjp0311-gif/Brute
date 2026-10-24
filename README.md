<p align="center">
  <img src="assets/brand/lockup.png" alt="Brute" width="520">
</p>

<p align="center"><b>A reasoner that abstains on what it cannot verify.</b><br>
<sub>Brute v0.1.0 · forked from BGR v0.90.0 · research preview · not AGI</sub></p>

---

## Overview

Brute is a small, exact reasoner for hidden finite-state worlds. It watches actions and masked sensor readings, keeps every hidden machine that is still consistent with the evidence, and predicts the next reading **only** when every surviving explanation agrees.

v0.1.0 has one goal: **when Brute cannot verify a prediction, it must say so instead of certifying it.** On the pre-registered study-002 it made **zero** false certificates in all 7 world families. The control (BGR v0.90 logic on the same worlds) made 156. The price is that Brute certifies far less often. One pre-registered criterion, **C6, failed**.

Brute is a fork of **BGR (Bitwork Geometric Reasoning) v0.90.0**, and that research is credited in full ([`FORK.md`](FORK.md)).

## Status

| | |
| --- | --- |
| Version | 0.1.0 (`RELEASE.json`, `brute.__version__`) |
| Tests | `python -m unittest discover -s tests`: **104 tests** (69 inherited, 35 new) |
| Study | `BRUTE-010-ABSTENTION-002`: pre-registered at commit `d402c75` before any code. 7 families × 24 held-out seeds × 3 mask rates = 504 cases |
| Gates | 8 of 9 gated criteria pass; **C6 fails** ([`results/study-002/GATES.json`](results/study-002/GATES.json)) |
| Verifier | `python -m scripts.verify_release` (full: re-runs both independent audits) or `--fast` |
| Interface | `brute.api` (JSON request/response v1) and a template-only language adapter (`adapters/language`). No language model is connected |

Every claim in this README carries a label:

- **Exact**: proved or verified by the tests or by exact computation in this repository.
- **Observed**: measured in study-002 (`results/study-002/SCIENTIFIC.json`, sealed), or in study-001 where stated.
- **Exploratory**: a post-hoc analysis that is not a criterion.
- **Open**: unresolved.

## Study-002 against the pre-registered criteria

| Criterion | Result | Observed |
| --- | --- | --- |
| C1 in-family soundness (cycle3, switch3, unstructured3, unaliased2, ood4) | PASS | 0 false of 1,443 conditional certificates; 0 public false |
| C2 ood5 false certificates = 0 | PASS | Brute 0 of 2. v0.90 control 79 of 212; v0.89 74 of 130 |
| C3 drift4 false certificates ≤ 50% of control | PASS | Brute 0 of 10, against a limit of 38.5. v0.90 77 of 376; v0.89 80 of 400. The zero stretch goal is also met |
| C4 public safety | PASS | 0 public certificates out of family; 0 public false anywhere |
| C5 in-family false-alarm rate ≤ 5% | PASS | 0 of 360 in-family cases alarmed |
| **C6 open-world log-loss ≤ ln 4 (1.386294)** | **FAIL** | probability floor 0.005 met. drift4 1.204857 passes; **ood5 1.504767 fails** |
| C7 in-family log-loss ≤ v0.90 + 0.05 | PASS | the largest cost is +0.0140 (unaliased2) |
| C8 coverage | reported | see below |
| C9 row budgets | reported | peak family rows 3,996; peak margin rows 99,818 of a 160,000 budget; 0 exhaustions |
| C10 independent audit | PASS | 504 cases, 22,176 steps replayed by a separate implementation |
| C11 reproducibility | PASS | rerun `CALIBRATION.json` and `SCIENTIFIC.json` are byte-identical |

### Coverage and log-loss after burn-in (*Observed*)

| Family | Coverage: Brute | Coverage: v0.90 | Log-loss: Brute | Log-loss: v0.90 | Log-loss: v0.89 (valid steps) |
| --- | ---: | ---: | ---: | ---: | ---: |
| cycle3 | 0.201 | 0.524 | 0.1858 | 0.1736 | 0.1729 |
| switch3 | 0.201 | 0.480 | 0.2097 | 0.1990 | 0.2137 |
| unstructured3 | 0.096 | 0.331 | 0.1055 | 0.0916 | 0.0635 |
| unaliased2 | 0.052 | 0.320 | 0.1116 | 0.0976 | 0.0670 |
| ood4 | 0.002 | 0.618 | 0.3982 | 0.3926 | 5.777 vs Brute 1.169 |
| ood5 | 0.001 | 0.076 | **1.5048** | 2.5082 | 9.220 vs Brute 1.873 |
| drift4 | 0.001 | 0.139 | 1.2049 | 2.0174 | 4.243 vs Brute 0.937 |

Uniform log-loss is 1.386294. The v0.89 score is computed only on steps where v0.89 produced a valid prediction, so that column is not comparable across rows. Selective risk (the error rate among certificates) is 0 for Brute in every family. For v0.90 it is 0.378 on ood5 and 0.213 on drift4. Paired, seed-clustered bootstrap intervals are in [`results/study-002/PAIRED_ANALYSIS.json`](results/study-002/PAIRED_ANALYSIS.json).

### Abstentions by reason after burn-in, 2,592 steps per family (*Observed*)

| Family | Certified | Possible set | Margin disagrees | Bound saturated | Residual alarm | Family contradicted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cycle3 | 522 | 1233 | 837 | 0 | 0 | 0 |
| switch3 | 522 | 1349 | 721 | 0 | 0 | 0 |
| unstructured3 | 250 | 1735 | 607 | 0 | 0 | 0 |
| unaliased2 | 134 | 1762 | 696 | 0 | 0 | 0 |
| ood4 | 6 | 991 | 836 | 759 | 0 | 0 |
| ood5 | 2 | 427 | 119 | 23 | 76 | 1945 |
| drift4 | 3 | 969 | 316 | 42 | 0 | 1262 |

On replay through the API, the 140 study-001 v0.90 false certificates (64 on ood5, 76 on drift4) become:

| Outcome | Count |
| --- | ---: |
| abstentions, margin disagrees | 107 |
| out-of-family responses, residual surprise | 15 |
| abstentions, bound saturated | 12 |
| conditional certificates on drift4, each withdrawn at the next observation | 6 |

Source: [`results/study-002/API_REPLAY.json`](results/study-002/API_REPLAY.json). *Observed.*

## What Brute can't do yet

- **It is worse than guessing on 5-state worlds.** Its ood5 post-burn-in log-loss is 1.5048, above uniform (1.3863) and above a one-step suffix-frequency baseline (1.2985). This is the C6 failure. Brute pays the ε/4 floor (ln 200 = 5.298) on the 64 steps where the 4-state family is contradicted, and then predicts uniform for the remaining 1,945 steps instead of learning. *Observed.*
- **It certifies much less than v0.90.** In-family coverage is 0.05–0.20, against 0.32–0.52 for v0.90. Across the in-family families it issued 1,443 certificates where v0.90 issued 5,936. The main cause is the n≤5 margin gate: 607–837 MARGIN_DISAGREES abstentions per family. On ood4 it also hits 759 BOUND_SATURATED abstentions and certifies on only 0.2% of steps. *Observed.*
- **It pays a small in-family accuracy cost.** Its log-loss is 0.006–0.014 above v0.90 in every in-family family, with all bootstrap intervals above 0 (inside the C7 allowance). *Observed.*
- **It can still issue a wrong-scope conditional certificate briefly.** When the study-001 drift4 cases are replayed, 6 conditional certificates are issued and then withdrawn at the next observation. Withdrawal is guaranteed; prevention is not. *Observed.*
- **It does not grow its own model class.** After a contradiction it falls back to uniform. Post hoc, the n≤5 margin learner stayed consistent on every ood5 contradicted step, and its single-value predictions were 1,435/1,435 correct. That is unused information. *Exploratory* ([`results/study-002/EXPLORATORY_V020.json`](results/study-002/EXPLORATORY_V020.json)).
- **It does not handle rules that change.** On drift4 the n≤5 margin is itself contradicted on 823 of 1,262 post-contradiction steps. *Exploratory.*
- **Public certificates need an outside attestation.** Brute cannot validate its own scope. A public certificate requires an attestation passed to `initialize` or `retry`. *Exact.*
- **It only works on a toy domain:** 2 actions, 2 binary sensors, a family of n≤4 hidden states with an n≤5 margin, and deterministic Moore machines only. *Exact.*
- **The language adapter is templates only.** It renders fixed sentences from API fields and checks that every claim points at an evidence field. It cannot answer free-form questions. *Exact.*
- **It is not AGI,** and nothing here shows general intelligence. *Open.*

The plan for v0.2.0 is in [`NEXT_ITERATION.md`](NEXT_ITERATION.md): self-growing families gated by the next-larger margin, chosen from the data above.

## Quickstart

Requires Python 3.11+ and NumPy. No GPU, network, or model weights.

```bash
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute
python -m pip install -r requirements.txt
python -m unittest discover -s tests            # 104 tests
python -m scripts.verify_release --fast          # seals, freezes, regenerated gates, ledger, manifest
python -m scripts.verify_release                 # also re-runs both independent audits (minutes)
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

To rerun calibration and study-002 in a scratch directory and compare bytes with the sealed files (long-running):

```bash
python -m scripts.make_reproducibility --check
```

## How it works

1. **Family support** (`brute/core`, `BruteLearner`): the exact symbolic support over n≤4 Moore machines (inherited from `bgr90`).
2. **Margin gate:** an n≤5 support must agree before Brute certifies. If the two disagree, it abstains with MARGIN_DISAGREES.
3. **Saturation check:** if every surviving explanation uses all 4 states, the bound may be the reason they agree, so Brute abstains with BOUND_SATURATED.
4. **Residual surprise:** a windowed (W=8) surprise test, with τ = 1.433141502274 calibrated on separate seeds (`CALIBRATION.json`), raises OUT_OF_FAMILY.
5. **Contradiction and retraction:** when no machine fits, Brute answers OUT_OF_FAMILY, withdraws any certificate the observation falsified, and predicts uniform.
6. **Open-world reserve:** ε = 0.02 is spread over all readings, so no probability falls below 0.005.
7. **`brute.api`:** versioned JSON request and response schemas (`brute/api/schema/*.v1.json`) and a service that never raises.
8. **Language adapter:** template rendering plus a checker that rejects any sentence not grounded in a response field.

## Repository

| Path | Contents |
| --- | --- |
| `brute/core`, `brute/evaluation.py` | The v0.1.0 learner and evaluator (study-002 freeze) |
| `brute/api`, `adapters/language` | The API contract, service, and template language adapter (release freeze) |
| `experiments/BRUTE_PLAN_002.json` | The pre-registration; `BRUTE_SOURCE_FREEZE_002.json` and `BRUTE_RELEASE_FREEZE_010.json` are the source locks |
| `results/study-002/` | Sealed results, calibration, audit, gates, paired analysis, reproducibility, API replay, exploratory |
| `results/study-001/`, `bgr*/` | Inherited BGR v0.90 evidence and code, byte-identical |
| `results/RESEARCH_LEDGER.jsonl` | Local unsigned SHA chain of research events |
| `docs/research/` | Inherited research record and [`BRUTE_DEVIATIONS_002.md`](docs/research/BRUTE_DEVIATIONS_002.md) |

## Credit and provenance

Brute is derived from BGR v0.90.0 (Bitwork Geometric Reasoning). The original README, CHANGELOG, RELEASE.json, and NEXT_ITERATION are preserved under [`docs/research/bgr-v0.90.0/`](docs/research/bgr-v0.90.0/). Study-001 results and ledger entries are unchanged.
