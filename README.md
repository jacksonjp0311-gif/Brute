<p align="center">
  <img src="assets/brand/lockup.png" alt="Brute" width="520">
</p>

<p align="center"><b>A reasoner that abstains on what it cannot verify.</b><br>
<sub>Brute v0.1.0 (planning) · forked from BGR v0.90.0 · research preview · not AGI</sub></p>

---

## Overview

Brute is a small, exact reasoner for hidden finite-state worlds. It watches actions and masked sensor readings, keeps every hidden machine that is still consistent with the evidence, and predicts the next reading **only** when every surviving explanation agrees.

Brute's goal for v0.1.0 is narrow: **when it cannot verify a prediction, it must say so instead of certifying it.**

Brute is a fork of **BGR (Bitwork Geometric Reasoning) v0.90.0**, and that research is credited in full. The code in this repository is currently BGR v0.90.0 unchanged (tag `bgr-v0.90.0-fork`). Provenance is in [`FORK.md`](FORK.md), and the fixes are planned in [`BRUTE_v0.1.0_PLAN.md`](BRUTE_v0.1.0_PLAN.md).

## Status

| | |
| --- | --- |
| Code | BGR v0.90.0, unmodified. **No Brute fixes are implemented yet** |
| Tests | `python -m unittest discover -s tests`: 69 tests pass in this fork |
| Release verifier | `python -m scripts.verify_release` **fails in this fork** because the nested baseline zip was intentionally left out (`FORK.md`; plan F12) |
| Evidence base | BGR study-001: 7 families × 24 held-out seeds × 3 mask rates = 504 cases and 22,176 observations ([`docs/research/`](docs/research/README.md)) |

Every claim in this README carries a label:

- **Exact**: proved or verified by the tests or by exact computation in this repository.
- **Observed**: measured in study-001. The numbers come from `results/study-001/RESULTS.json`, or from a re-analysis of `SCIENTIFIC.json`.
- **Open**: unresolved.

## What Brute can't do yet

- **It certifies wrong answers outside its family.** It made 140 false certifications on worlds outside its 4-state model: 64 of 213 certificates on 5-state worlds (about 30%) and 76 of 293 on rule-changing worlds (about 26%). *Observed.*
- **It can't detect that it is out of family.** It has no misspecification check and doesn't abstain when its model class is wrong. 102 of the 140 wrong certificates were issued on the very step whose observation then ruled out every 4-state machine. *Observed.*
- **It never issues a public certificate.** `scope_verified=False` is hard-coded, so the zero public certificates in the study come from a switch, not from verification. *Exact.*
- **It certifies less often than v0.89 on in-family worlds.** It issued about 48% fewer certificates on the 1–3 state families: 4,068 vs 7,860. *Observed.*
- **It scores worse than guessing on 5-state and rule-changing worlds.** Mean log-loss is 2.289 and 2.189 against 1.386 for uniform. The cause is a 1e-12 probability floor: 95 and 99 steps put almost no probability on what actually happened. *Observed.*
- **There is no predictive-score comparison with v0.89.** The per-step v0.89 score is never recorded. *Exact.*
- **Some reported numbers can't be regenerated.** `PAIRED_ANALYSIS.json` and `GATES.json` have no generator scripts, and the release verifier checks hard-coded values. *Exact.*
- **It only works on a toy domain:** 2 actions, 2 binary sensors, up to 4 hidden states (6 at most in code). *Exact.*
- **There is no language interface.** An API and adapter are specified in the plan but not built. *Exact.*
- **It is not AGI,** and nothing here shows progress toward it. *Open.*

How these get fixed is in [`BRUTE_v0.1.0_PLAN.md`](BRUTE_v0.1.0_PLAN.md).

## What it does do

| Claim | Label | Evidence |
| --- | --- | --- |
| Zero false conditional certifications on the 1–3-state in-family worlds (288 cases), and zero on the 72 four-state worlds that the v0.89 three-state learner got wrong 78 times | Observed | `results/study-001/RESULTS.json`; independently replayed by `experiments/independent_audit.py` |
| The four-state symbolic support stayed consistent on 72/72 four-state cases; the v0.89 three-state family was contradicted on 71/72 | Observed | same |
| An independent reference replayed all 22,176 observations and reconstructed all 6,103 conditional certificates | Observed / Exact replay | `results/study-001/INDEPENDENT_AUDIT.json` |
| Moore minimization matches an independent all-future-word equivalence check and is invariant to state relabelling (17 of 120 reference worlds had fewer predictive states than labels) | Exact | `bgr90/quotient.py`, `tests/test90.py` |
| After any finite masked history, two larger machines exist that agree with every observation yet disagree on the next one. No finite evidence certifies without a bound. `open_world_counterexample` **passes** | Exact | `scripts/open_world_counterexample.py`, `tests/test90_limit.py` |
| Budget exhaustion and contradictions preserve the evidence and cause abstention, with replay at a larger budget | Exact | `tests/test90.py` |

## Quickstart

Requires Python 3.11+ and NumPy (`requirements.txt`). No GPU, network, or model weights.

```bash
git clone https://github.com/jacksonjp0311-gif/Brute.git && cd Brute
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v          # 69 tests
python -m scripts.open_world_counterexample      # impossibility witness
python -m scripts.demo                           # one four-state run
python -m experiments.independent_audit --results-dir results/study-001
```

To reproduce study-001 without touching the frozen results:

```bash
python -m experiments.run_study --output runs/reproduction-001
python -m experiments.independent_audit --results-dir runs/reproduction-001
```

## How it works

1. **Symbolic support** (`bgr90/symbolic.py`, `SymbolicLearner`): it represents only the states and transitions the evidence has touched, naming states in first-visit order, up to `max_states`. It certifies the next reading when the surviving support is a singleton.
2. **Adequacy boundary** (`bgr90/adequacy.py`, `AdequacyLearner`): it separates *conditional* certificates, which are true if the world is in the family, from *public* ones, which need external scope attestation (not yet possible; see above).
3. **Predictive quotient** (`bgr90/quotient.py`, `minimize_moore`): it merges hidden states only when every future action sequence predicts the same readings.
4. **Impossibility witness** (`scripts/open_world_counterexample.py`): the limit any finite-evidence reasoner faces.

## Roadmap

[`BRUTE_v0.1.0_PLAN.md`](BRUTE_v0.1.0_PLAN.md) covers:

- the ordered fixes F1–F14 (contradiction and retraction, a margin-family gate, a saturation check, a residual-surprise test, coverage reporting, the probability reserve, the v0.89 comparison, generators, the timing fix, an attested public path, and hygiene);
- the architecture changes needed before language;
- the `brute.api` contract for a strictly grounded language adapter.

## Repository

| Path | Contents |
| --- | --- |
| `bgr90/`, `bgr89/` … `bgr60/` | Core algorithms (inherited, unchanged) |
| `experiments/`, `scripts/`, `tests/` | Frozen study runner, independent references, tools, 69 tests |
| `results/` | Study-001 evidence, gates, ledger (unchanged) |
| `docs/research/` | Brute index of the inherited BGR research record |
| `assets/brand/` | Brute symbol, lockup, OG card ([`BRAND.md`](assets/brand/BRAND.md)) |
| `FORK.md`, `BRUTE_v0.1.0_PLAN.md` | Provenance and plan |

## Credit and provenance

Brute is derived from BGR v0.90.0 (Bitwork Geometric Reasoning). The original README is preserved byte-for-byte at [`docs/research/bgr-v0.90.0/README.md`](docs/research/bgr-v0.90.0/README.md). The whitepaper, docs, results and ledger stay at their original paths with their contents unchanged; see [`docs/research/README.md`](docs/research/README.md).
