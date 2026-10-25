<p align="center">
  <img src="assets/brand/lockup.png" alt="Brute" width="520">
</p>

<p align="center"><b>A reasoner that abstains on what it cannot verify, chooses experiments that let it verify more, and now certifies only what holds on every place the world could have jumped to.</b><br>
<sub>Brute v0.3.0 · forked from BGR v0.90.0 · research preview · not AGI</sub></p>

---

## Overview

Brute is a small, exact reasoner for hidden finite-state worlds. It watches actions and masked sensor readings, keeps every hidden machine that is still consistent with the evidence (the *version space*, a region), and predicts the next reading **only** when every surviving explanation agrees (the region's projection onto that reading is a single point, and an n≤5 margin agrees). Since v0.2.0 it also acts: it picks the action whose answers would let it certify most (a one-step lookahead).

**v0.3.0 makes certification robust to silent change.** A certificate must also be constant on the *fibre* of the region over the latest observation: every state the world could be in if it had jumped unseen at that step (rule Y1k; otherwise ABSTAIN with `RESYNC_AMBIGUOUS`). The lookahead scores with the same test (LU-R). On the pre-registered study-005 (504 held-out cases plus a 216-case extended drift block) **12 of 14 gated criteria pass, and G3′ — v0.2.0's failure — now passes**: 0 stale certificates on the gated drift block. **Two gates fail and stay on the record:** G6b (coverage is 0.098 below v0.2.0; pre-registered as the expected price) and G5 (the unchanged residual-surprise alarm misfires on 5 of 72 held-out ood4 cases, as it does in v0.1.1). The pre-registered test of whether D7 and D8 share one mechanism is **OPEN**.

Brute is a fork of **BGR (Bitwork Geometric Reasoning) v0.90.0**, and that research is credited in full ([`FORK.md`](FORK.md)).

## Status

| | |
| --- | --- |
| Version | 0.3.0 (`RELEASE.json`, `brute.release_version_030.RELEASE_VERSION`). `brute.release_version` stays `0.2.0`, `brute.version` `0.1.1` and `brute.__version__` `0.1.0`, because those files are in earlier freezes |
| Tests | `python -m unittest discover -s tests`: **TESTCOUNT** |
| Study | `BRUTE-030-CHANGEPOINT-005`: criteria frozen at `25fa47b` before any v0.3.0 code (pre-freeze probe code disclosed, deviation P0); source frozen at `f7f3bd3`; scoring scripts committed at `a1889b6` before results were inspected. 7 families × 24 new held-out seeds × 3 mask rates = 504 cases, plus 216 extended drift4 cases. Arms: **A3** v0.3.0 active, **P3** v0.3.0 passive, **A2**/**P2** frozen v0.2.0 active/passive, **E2** v0.2.0 + forced untaken-branch checks (mechanism arm), **C** frozen v0.1.1, plus the v0.90 control |
| Gates | **12 of 14 pass; G5 and G6b fail; G14 OPEN** ([`results/study-005/GATES.json`](results/study-005/GATES.json)) |
| Verifier | `python -m scripts.verify_release_030 --fast` (seals, freezes, regenerated gates and paired analysis, ledger, manifest, git order); without `--fast` it re-runs the independent reference; `--frozen` also runs the unmodified v0.2.0 verifier on the raw v0.2.0 tree |
| Interface | `brute.api` 1.0–1.2 and **1.3** (`BruteServiceV030`: `RESYNC_AMBIGUOUS`, `experiment.check`, `proposal`/`no_proposal_reason`). Template-only language adapter. No language model is connected |
| Storage | Sealed traces for study-004 and study-005 are committed as deterministic gzip; `python scripts/study005_storage.py restore` (and `study004_storage.py`) rebuild them and check them against `SEAL.json` |

Every claim in this README carries a label:

- **Exact**: proved or verified by the tests or by exact computation in this repository.
- **Observed**: measured in study-005 (`results/study-005/SCIENTIFIC.json`, sealed), or in earlier studies where stated.
- **Simulated**: a counterfactual predictor rescored on earlier sealed traces (design evidence, not pre-registered evidence).
- **Inferred**: reasoning, not measured.
- **Rejected**: considered and dropped, with the reason given.
- **Open**: unresolved.

## Study-005 against the pre-registered criteria (*Observed*)

| Criterion | Result | Key numbers |
| --- | --- | --- |
| G1 in-family soundness, A3 and P3, taken + counterfactual, public | PASS | 0 false of 2,635 taken + 574 counterfactual certificates (A3); 0 of 729 + 771 (P3); 0 public false. Every other arm also 0 |
| G2 ood5 false certificates = 0 | PASS | A3 0 of 113 (+4 counterfactual); P3 0 of 8; v0.90 control 85 of 174 |
| **G3′ drift4: 0 wrong at non-drift steps and total ≤ 50% of v0.90** | **PASS** (failed in v0.2.0) | A3 9 of 62, all at drift steps, 0 stale; P3 0 of 6; limit 44.5 (v0.90: 89). v0.2.0 A2 on the same seeds: 15, 1 non-drift, 2 stale |
| G4 public safety | PASS | 0 public certificates on ood5/drift4; 0 public false anywhere |
| **G5 in-family false-alarm cases ≤ 5%** | **FAIL** | ood4 5 of 72 (0.069) in A3 and P3; identical in frozen v0.1.1, A2, P2 (unchanged alarm rule and τ). Other families 0 |
| G6 active coverage gain (A3 − P3 ≥ 0.05, CI > 0, no family < −0.01) | PASS | **+0.064352, CI95 [0.055054, 0.073922]**; every family CI excludes 0 |
| **G6b coverage non-inferiority vs v0.2.0 (A3 − A2 ≥ −0.03, CI lower ≥ −0.05)** | **FAIL** (pre-registered as expected) | **−0.098264, CI95 [−0.110885, −0.087267]** (design −0.094) |
| G7 open-world no regression (A3, P3 ≤ C; ≤ ln 4; min p ≥ 0.005; A3 ≤ A2 + 0.05) | PASS | ood5 A3 0.63875 / P3 = C 0.648728 / A2 0.628252; drift4 A3 1.162304 / P3 1.163681 / A2 1.170786 / C 1.181917 |
| G8 passive equivalence (P3 ≡ P2 except RESYNC; A3 in-family ≤ C + 0.05) | PASS | A3 in-family log-loss below C in every family |
| G9 retraction semantics + de-duplication | PASS | 81 retractions (9 falsified, 47 scope withdrawn, 25 unverifiable); 0 duplicates; 0 RESYNC_AMBIGUOUS issued |
| G10 compute budget | PASS | peak 100,230 of 160,000 rows; 0 exhaustions; wall clock A3/C 1.19 |
| G11 independent audit | PASS | 504 + 216 cases, 139,392 arm-steps, 0 mismatches (no `brute` import) |
| G12 reproducibility | PASS | rerun `CALIBRATION_CHECK.json` and `SCIENTIFIC.json` byte-identical |
| G13 τ reproduces | PASS | τ = 1.433141502274 |
| G14 D7/D8 single-mechanism test (decision, not gated) | **OPEN** | S(A2) 17, S(E2) 14, S(A3) 4 (stale false certificates, main + extended); CONFIRMED needed S(E2) ≤ 8.5, FALSIFIED S(E2) ≥ 17. S(E2) − S(A2) −3 [−12, +6] |

Paired, seed-clustered bootstrap (2,000 resamples, seed 20261025; [`PAIRED_ANALYSIS.json`](results/study-005/PAIRED_ANALYSIS.json)). Deviations: [`BRUTE_DEVIATIONS_005.md`](docs/research/BRUTE_DEVIATIONS_005.md).

### Coverage after burn-in (*Observed*)

| Family | Dual coverage P3 / A3 / A2 (v0.2.0) / E2 | RESYNC abstentions (A3) | Log-loss C / A3 |
| --- | --- | ---: | --- |
| cycle3 | 0.075 / **0.143** / 0.331 / 0.289 | 608 | 0.1846 / **0.1764** |
| switch3 | 0.115 / **0.180** / 0.289 / 0.277 | 397 | 0.2169 / **0.1939** |
| unstructured3 | 0.052 / **0.122** / 0.190 / 0.139 | 113 | 0.1619 / **0.1475** |
| unaliased2 | 0.041 / **0.129** / 0.218 / 0.137 | 170 | 0.0954 / **0.0877** |
| ood4 | 0.004 / **0.032** / 0.070 / 0.117 | 67 | 0.3755 / **0.3666** |

Findings and their math: [`docs/research/DISCOVERIES.md`](docs/research/DISCOVERIES.md) D11–D16.

## What Brute can't do yet

- **It pays for safety with coverage.** Fibre-robust certification abstains wherever an unseen jump cannot be ruled out: dual coverage A3 0.121 against v0.2.0's 0.220 in family (G6b fails). The fibre uses only the latest observation, so later evidence that no jump happened is not used. *Observed* (cost), *Inferred* (cause).
- **It can still certify on a stale model after a jump into an unexplored state.** On the extended drift4 block (not gated) A3 has 38 false certificates, 2 at non-drift steps and 4 stale (v0.2.0: 62 / 14 / 15). Y1k does not cover jumps into a state whose edge for the queried action is still unknown. *Observed*, *Inferred* (cause; a registered limitation).
- **Its surprise alarm misfires and never recovers.** 5 of 72 held-out ood4 cases raise a false residual-surprise alarm at mask ≥ 0.35 (G5 fails; same in v0.1.1), and certification never resumes in that session. *Observed.*
- **Its experiments are greedy and one step deep.** Forcing it to check the untaken branch restores counterfactual knowledge but not safety (G14 OPEN, D13); it has no multi-step or information-value objective. *Observed*, *Inferred.*
- **Its drift forecasts still do not beat a frequency table clearly.** drift4 A3 − suffix-1 −0.013, CI [−0.120, +0.091]. *Observed.*
- **It gets 5-state worlds right only up to 5 states.** No n≤6 margin or 5-state certificates; peak 100,230 of 160,000 rows. *Observed* (budget), *Inferred* (n≤6 or a two-step lookahead would not fit enumeration).
- **It still pays ln 200 = 5.298 on every contradiction step.** *Exact* (ε reserve design).
- **It does not grow its own model class or representation.** Regions are enumerated rows. *Exact.*
- **Public certificates need an outside attestation.** *Exact.*
- **It only works on a toy domain:** 2 actions, 2 binary sensors, deterministic Moore machines, an n≤4 family with an n≤5 margin. *Exact.*
- **The language adapter is templates only.** No free-form questions. *Exact.*
- **It is not AGI,** and nothing here shows general intelligence. *Open.*

The plan for v0.4.0 is in [`NEXT_ITERATION.md`](NEXT_ITERATION.md); the longer path is in [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Quickstart

Requires Python 3.11+ and NumPy. No GPU, network, or model weights.

```bash
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute
python -m pip install -r requirements.txt
python -m unittest discover -s tests            # see Status for the count
python -m scripts.verify_release_030 --fast      # restores the study-004/005 traces, then seals, freezes, gates, ledger, manifest, git order
python -m scripts.verify_release_030             # also re-runs the study-005 independent reference (long)
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

A v0.3.0 session through API 1.3 (experiment responses now carry `check`, `proposal` and `no_proposal_reason`; a certificate that fails the fibre test comes back from `predict` as ABSTAIN / RESYNC_AMBIGUOUS):

```python
from brute.api.service_v030 import BruteServiceV030
s = BruteServiceV030()
s.handle({"api_version": "brute.api/1.3", "session_id": "demo", "op": "initialize",
          "observation": {"x": 0, "y": 0}, "family": {"max_states": 4}})
print(s.handle({"api_version": "brute.api/1.3", "session_id": "demo", "op": "experiment"}))
```

To rerun the calibration check and study-005 in a scratch directory and compare bytes with the sealed files (about 4 minutes on 4 workers):

```bash
python scripts/make_reproducibility_005.py --workers 4
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
9. **Fibre-robust certification (v0.3.0, `brute/changepoint.py`, rule Y1k):** a CERTIFIED forecast for action b must also be constant on the union, over every surviving n≤4 machine and every visited state that matches the latest observation, of that state's known successor reading under b (an unknown edge from the current state counts as any reading). Otherwise ABSTAIN with `RESYNC_AMBIGUOUS`, never issued.
10. **LU-R (v0.3.0):** the lookahead of step 7 with the step-9 test applied to each hypothetical answer.
11. **Open-world reserve:** ε = 0.02 is spread over all readings, so no probability falls below 0.005.
12. **`brute.api`:** versioned JSON request and response schemas (`brute/api/schema/*.v1.json`) and a service that never raises.
13. **Language adapter:** template rendering plus a checker that rejects any sentence not grounded in a response field.

## Repository

| Path | Contents |
| --- | --- |
| `brute/core`, `brute/evaluation.py` | The v0.1.0 learner and evaluator (study-002 freeze) |
| `brute/api`, `adapters/language` | The API contract, service, and template language adapter (release freeze) |
| `brute/fallback.py`, `brute/api/service_v011.py` | v0.1.1 learner and API 1.1 (study-003 freeze) |
| `brute/active.py`, `brute/api/service_v020.py`, `brute/release_version.py` | v0.2.0 learner and API 1.2 (study-004 freeze) |
| `brute/changepoint.py`, `brute/api/service_v030.py`, `brute/release_version_030.py` | v0.3.0 learner and API 1.3 (study-005 freeze) |
| `experiments/BRUTE_PLAN_005.json` | The study-005 pre-registration (`25fa47b`); `BRUTE_SOURCE_FREEZE_005.json` and `BRUTE_RELEASE_FREEZE_030.json` lock v0.3.0 code |
| `results/study-005/` | Sealed traces (gzip), seal, calibration check, independent audit, gates, paired analysis, reproducibility |
| `experiments/BRUTE_PLAN_004.json` | The study-004 pre-registration (`c0ac594`); `BRUTE_SOURCE_FREEZE_004.json` and `BRUTE_RELEASE_FREEZE_020.json` lock v0.2.0 code |
| `results/study-004/` | Sealed traces (gzip), seal, calibration check, independent audit, gates, paired analysis, reproducibility |
| `experiments/BRUTE_PLAN_003.json` | The study-003 pre-registration; `BRUTE_SOURCE_FREEZE_003.json` and `BRUTE_RELEASE_FREEZE_011.json` lock v0.1.1 code. Earlier plans and locks are kept |
| `results/study-003/` | Sealed results, calibration check, independent audit, gates, paired analysis, reproducibility, witness audit, drift stress |
| `results/study-002/` | Sealed results, calibration, audit, gates, paired analysis, reproducibility, API replay, exploratory |
| `results/study-001/`, `bgr*/` | Inherited BGR v0.90 evidence and code, byte-identical |
| `results/RESEARCH_LEDGER.jsonl` | Local unsigned SHA chain of research events |
| `docs/research/` | Inherited research record, [`BRUTE_DEVIATIONS_002.md`](docs/research/BRUTE_DEVIATIONS_002.md), [`BRUTE_DEVIATIONS_003.md`](docs/research/BRUTE_DEVIATIONS_003.md), [`BRUTE_DEVIATIONS_004.md`](docs/research/BRUTE_DEVIATIONS_004.md), [`BRUTE_DEVIATIONS_005.md`](docs/research/BRUTE_DEVIATIONS_005.md), [`DISCOVERIES.md`](docs/research/DISCOVERIES.md) |

## Credit and provenance

Brute is derived from BGR v0.90.0 (Bitwork Geometric Reasoning). The original README, CHANGELOG, RELEASE.json, and NEXT_ITERATION are preserved under [`docs/research/bgr-v0.90.0/`](docs/research/bgr-v0.90.0/). Study-001 results and ledger entries are unchanged.
