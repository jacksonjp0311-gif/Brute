# Brute v0.1.1 plan (scoping only, no code)

Status: **DRAFT plan**, branch `plan/v0.1.1`, written 2026-10-24 (EDT). Nothing under `brute/`, `adapters/`, `experiments/brute_*.py` or `tests/` has been changed. No gated study was run.

Evidence labels used on every claim:
- **Exact**: read straight from sealed files or code, or follows by construction.
- **Observed**: from the sealed study-002 gates and results.
- **Observed-post-hoc**: re-tabulated from sealed traces by the new read-only `scripts/explore_v011.py`. Output: `docs/research/v0.1.1/POSTHOC_V011.json`, reproducible with `--check`.
- **Simulated**: a counterfactual predictor scored again on the sealed study-002 traces. This is design evidence, not pre-registered evidence.
- **Inferred**: reasoning, not measured.
- **Rejected**: considered and dropped, with the reason given.
- **Open**: not known yet.

Study-002 traces are now **design data**. Every claim about v0.1.1 performance must be re-earned on study-003's new seeds (`experiments/BRUTE_PLAN_003.DRAFT.json`).

## 0. Correction: drift4 passes C6, ood5 fails it

C6 needs a mean post-burn-in log-loss ≤ ln 4 = 1.386294 on each out-of-family world.

- **Observed:** drift4 scores **1.204857**, so it passes. ood5 scores **1.504767**, so it fails. ood5 is the **only** failing component of C6, and C6 is the only failing gate (`results/study-002/GATES.json`: `failed: ["C6_open_world_logloss"]`).
- **Observed-post-hoc:** drift4 is still worse than the suffix-1 frequency baseline (1.166383).
- **Observed-post-hoc:** ood5 is above ln 4 at **every** mask rate: 1.392825 / 1.479279 / 1.642196 at mask 0.1 / 0.35 / 0.6.

So "worse than guessing" is true for the 5-state world, not for the rule-changing world.

## 1. Failure modes from study-002

### 1.1 Log-loss per family and mask

Post-burn-in steps 9..44, 864 steps per mask and 2,592 per family. Values are Observed for the `all` rows and Observed-post-hoc for the per-mask rows.

| family@mask | Brute | v0.90 | uniform | suffix1 | v0.89 on its valid steps (n) | Brute on the same steps | cov Brute / v0.90 |
|---|---|---|---|---|---|---|---|
| ood5@0.1 | 1.392825 | 1.883699 | 1.386294 | 1.175994 | 10.627316 (13) | 1.331393 | .002315 / .070602 |
| ood5@0.35 | 1.479279 | 2.360629 | 1.386294 | 1.342401 | 11.341371 (63) | 1.919456 | 0 / .069444 |
| ood5@0.6 | 1.642196 | 3.280378 | 1.386294 | 1.377162 | 8.459893 (200) | 1.894222 | 0 / .086806 |
| **ood5@all** | **1.504767** | 2.508235 | 1.386294 | 1.298519 | 9.21971 (276) | 1.873472 | .000772 / .075617 |
| drift4@0.1 | 1.272232 | 1.918631 | 1.386294 | 0.946554 | 5.277522 (138) | 0.965741 | .002315 / .130787 |
| drift4@0.35 | 1.166013 | 1.942646 | 1.386294 | 1.221932 | 4.124854 (240) | 0.825005 | .001157 / .152778 |
| drift4@0.6 | 1.176327 | 2.190841 | 1.386294 | 1.330662 | 3.954944 (398) | 0.994366 | 0 / .134259 |
| **drift4@all** | **1.204857** | 2.017373 | 1.386294 | 1.166383 | 4.242694 (776) | 0.936896 | .001157 / .139275 |
| ood4@all | 0.398164 | 0.392647 | 1.386294 | 1.238765 | 5.777456 (484) | 1.168993 | .002315 / .61767 |
| cycle3@all | 0.185798 | 0.173636 | 1.386294 | 1.245066 | 0.172912 (2592) | 0.185798 | .201389 / .524306 |
| switch3@all | 0.209745 | 0.198959 | 1.386294 | 1.161544 | 0.213687 (2592) | 0.209745 | .201389 / .479552 |
| unstructured3@all | 0.105546 | 0.091611 | 1.386294 | 1.009399 | 0.063542 (2592) | 0.105546 | .096451 / .330633 |
| unaliased2@all | 0.111583 | 0.097559 | 1.386294 | 1.151816 | 0.06696 (2592) | 0.111583 | .051698 / .320216 |

Further findings:
- **Observed:** v0.90 conditional false certificates over all steps: ood5 79, drift4 77. Over post-burn-in steps only: ood5 74, drift4 77. Brute has 0 false certificates on all 7 families.
- **Observed:** Brute's in-family log-loss is +0.006 to +0.014 nats above v0.90 (paired-bootstrap CI > 0). This is inside C7's +0.05 allowance.

### 1.2 Failure modes

| # | Failure mode | Families | Size | Label |
|---|---|---|---|---|
| FM1 | **Contradiction-step floor.** On the step the n≤4 family is contradicted, the actual code was outside the support every time, so it got exactly ε/4 = 0.005, a loss of −ln 0.005 = 5.298317. | ood5: 64 post-burn-in steps (+8 in burn-in). drift4: 60. | ood5 contributes +0.0966 nats to the mean; drift4 +0.0906. | Observed-post-hoc |
| FM2 | **Uniform after contradiction.** After contradiction the forecast is uniform (exactly ln 4), although the n≤5 margin learner is still alive and correct on ood5. | ood5: 1,945 steps. drift4: 1,262 steps. | 0 excess over ln 4, but it is the largest **avoidable** block: 1.0402 of ood5's 1.5048. | Observed-post-hoc |
| FM3 | **Pre-contradiction overconfidence.** POSSIBLE_SET and MARGIN_DISAGREES forecasts on ood5 put mass on wrong n≤4 supports. | ood5: 412 POSSIBLE_SET steps at a mean 1.682858; 82 MARGIN_DISAGREES steps at 1.754705. | +0.0471 and +0.0117 to the mean. | Observed-post-hoc |
| FM4 | **Residual alarm without a forecast change.** The alarm suppresses certificates but leaves probabilities unchanged. | ood5: 76 alarm steps (64 before contradiction, 12 on the contradiction step). No alarm on drift4 or in-family. | Mean loss on these steps is 1.196 (0.427 for the 64 pre-contradiction steps). They hold 10 wrong n≤4 singletons, which the alarm blocked. | Observed-post-hoc |
| FM5 | **Drift-step false certificates.** The study-002 seeds had none. Replaying the frozen v0.1.0 learner on the **study-001** drift4 seeds gives 19 conditional certs, **6 of them wrong**. All 6 fall exactly on perturbation steps: step 12 five times, step 23 once. In all 6 the margin agreed, saturation was false, and the residual was 0.04–0.49, well below τ = 1.433. | drift4 | 6 of 19 | Observed-post-hoc (exact replay) |
| FM6 | **Retraction mislabel.** `brute/api/service.py::_retractions` returns *every* issued certificate with reason `falsified_by_observation` once the family is contradicted, including certificates that were correct. Study-002: drift4 had 10 certs, 0 wrong, all reported as "falsified"; ood5 had 2 certs, 0 wrong. The schema enforces this: `response.v1.json` has `reason: {"const": "falsified_by_observation"}`. | API | 12 mislabelled retractions | Exact |
| FM7 | **Coverage collapse.** Brute certifies 1,443 post-burn-in in-family steps against v0.90's 5,936. MARGIN_DISAGREES steps per in-family family: cycle3 837, ood4 836, switch3 721, unaliased2 696, unstructured3 607. Every one of the 3,697 had a **correct** n≤4 singleton, so in-family this gate is pure coverage cost. Out of family, the same gate blocked 137 **wrong** singletons (ood5 64, drift4 73). | all | as stated | Observed / Observed-post-hoc |
| FM8 | **Bound saturation on ood4.** 759 steps abstain with BOUND_SATURATED and 0 of them had a wrong singleton. The gate still protects: on drift4 it blocked 4 wrong singletons in study-002, and it caught v0.90-style errors in the study-001 replay. | ood4, drift4 | as stated | Observed-post-hoc |
| FM9 | **Exploratory-script definition bug.** `scripts/explore_v020.py` filters `step < burn_in`, so it includes step 8. That gives 1,951 ood5 post-contradiction steps against the sealed 1,945. The script is release-frozen, so it is not edited. `explore_v011.py` uses the plan's `step > burn_in`. | docs | ±6 steps | Exact |
| FM10 | **Hygiene.** The local branch `v0.1.0` (at 4e26104, fully merged into main 3c26f69) has the same name as tag `v0.1.0`, so git warns `refname 'v0.1.0' is ambiguous`. `scripts/package_release.py` has never been run. F14 (`learner_witness_audit`) was not done. | repo | — | Exact |

### 1.3 Decomposing the ood5 loss: which fix moves which part

The mean is taken over 2,592 post-burn-in steps. Each block's contribution to the mean is (steps × block mean) / 2592.

| Block | Steps | Mean loss, v0.1.0 | Contribution v0.1.0 | Contribution with F1 (Simulated) | Moved by |
|---|---|---|---|---|---|
| before contradiction (all statuses) | 583 | 1.4836 | 0.3337 | 0.3337 (unchanged) | F1 does not touch it. The margin mixture would, but it is Rejected (§2, R2). |
| · POSSIBLE_SET | 412 | 1.682858 | 0.2675 | same | (FM3) v0.2.0 |
| · MARGIN_DISAGREES | 82 | 1.754705 | 0.0555 | same | (FM3) v0.2.0 |
| · RESIDUAL_SURPRISE | 64 | 0.426862 | 0.0105 | same | — |
| · saturated + certified | 25 | 0.015114 | 0.0001 | same | — |
| contradiction step | 64 | 5.298317 | 0.1308 | 0.1308 (unchanged) | Only a larger ε (Rejected, R1) or not being contradicted at all: growth (v0.2.0). |
| after contradiction | 1,945 | 1.386294 | **1.0402** | **0.2005** (mean 0.2672) | **F1, margin fallback** |
| **total** | 2,592 | — | **1.5048** | **0.6650** | |

For drift4, Simulated:
- **v0.1.0:** 1.2049 total. Of that, 0.4073 comes before contradiction, 0.1226 from the contradiction step, and 0.6749 after it, at uniform loss over 1,262 steps.
- **F1, margin tier only:** 1.1199. The after-contradiction mean drops to 1.2119, because the margin is itself contradicted on 823 of those 1,262 steps and they stay uniform.
- **F1, margin then suffix-1 tier:** about 1.0178 (approximate, see F1).

## 2. Candidate fixes: keep / modify / reject

### Ground rule F0: freeze hygiene (Exact, required)

The frozen files must stay byte-identical so that study-001 and study-002 still audit in-tree:
- `experiments/BRUTE_SOURCE_FREEZE_002.json` freezes `brute/core/learner.py`, `brute/evaluation.py`, `experiments/brute_*.py`, `experiments/v90_independent_reference.py` and `tests/test_brute_abstention.py`.
- `experiments/BRUTE_RELEASE_FREEZE_010.json` freezes `brute/api/*`, the response schema, `scripts/make_*`, `scripts/verify_release.py`, `scripts/explore_v020.py`, `scripts/package_release.py` and the `tests/test_*` release tests.

**Decision:** v0.1.1 code goes into **new files** only.
- The learner subclasses `BruteLearner`.
- The API change ships as a new schema version, with the v1 schema and service left in place for the tag.
- New freezes: `BRUTE_SOURCE_FREEZE_003.json` and `BRUTE_RELEASE_FREEZE_011.json`.
- New verifier: `scripts/verify_release_011.py`.

This is the same pattern v0.90 used for `bgr*/` (Inferred: it is the least risky path).

### Kept for v0.1.1

**F1 = candidate (b): non-certifying predictive fallback after contradiction.**
- **Targets:** new `brute/core/fallback.py::FallbackBruteLearner(BruteLearner)`, overriding `predict` and `_v090_probabilities`. It also keeps one `bgr89.baselines.SuffixFrequency(1, 0.7)`, a frozen module imported read-only.
- **Rule:**
  - Once `self.support.status == 'grammar_contradicted'`, the forecast is chosen in this order: the margin forecast `(1−ε)·uniform(margin_support) + ε/4` if `self.margin.predict_support(action)` is not None; otherwise the suffix-1 forecast `(1−ε)·suffix1 + ε/4`; otherwise uniform.
  - `status`, `reason` and `certificate` are unchanged: OUT_OF_FAMILY / FAMILY_CONTRADICTED, no certificate.
  - A new field `forecast_source ∈ {v090, margin_n5, suffix1, uniform}` is exposed.
  - Before contradiction the subclass returns **exactly** the parent's forecast.
- **Why it is honest:** it refuses to certify and improves only the forecast. It falls back to a family that the evidence has not refuted. The n≤5 assumption is stated in `forecast_source`, and nothing is promoted to a certificate.
- **Evidence:**
  - Simulated, margin tier: ood5 1.504767 → **0.664984**; drift4 1.204857 → **1.119949**. Per-mask ood5: 0.323883 / 0.556398 / 1.114672.
  - Simulated (approximate), margin then suffix-1: drift4 → **1.017814** (0.880889 / 1.006502 / 1.166051 per mask). "Approximate" means the suffix-1 baseline's own loss is used without the ε re-mix.
  - Exact: in-family log-loss, coverage and decisions are **unchanged**. In-family worlds were never contradicted in study-002 (0/360 cases), and the override applies only after contradiction.
  - Inferred: residual surprises after contradiction change, but they cannot change any decision, because the contradiction gate is first.
  - Open: on a world with more than 5 states the margin may survive while being wrong. Loss per step is still bounded by 5.298317. Study-003 reports this. A 6-state world is v0.2.0 (§4).
- **Tests:** new file `tests/test_brute_fallback.py`.
  - (i) Identity: before contradiction the forecast equals `BruteLearner.predict` on all study-002 in-family seeds and on a constant learner.
  - (ii) After contradiction: no certificate, and the status reason is FAMILY_CONTRADICTED.
  - (iii) `min(probabilities) ≥ ε/4` on every step.
  - (iv) `forecast_source` order: margin, then suffix1, then uniform.
  - (v) An ood5 seed shows the margin source, and its loss falls below ln 4 after contradiction.

**F2 = candidate (g): cleanup (Exact).**
- Rename or delete the local branch `v0.1.0`. It is local only and fully merged, so `git branch -m v0.1.0 release-branch/v0.1.0`, or `git branch -d v0.1.0`.
- Run `scripts/package_release.py` (`pack(ref='v0.1.0')`) and record the archive sha256 in the ledger.
- Record FM9 as a known definition mismatch in `docs/research/BRUTE_DEVIATIONS_002.md`, as an addendum note. That file is not frozen; the change must be verified with `make_manifest`.
- **Tests:** `tests/test_brute_repro.py` and `verify_release --fast` still pass. The manifest is regenerated.

**F3 = new item from FM6: honest retraction reasons.**
- **Targets:**
  - New `brute/api/service_v011.py::BruteServiceV011(BruteService)`, overriding `_retractions`.
  - New schema `brute/api/schema/response.v1_1.json`, where reason ∈ {`falsified_by_observation`, `scope_withdrawn`, `unverifiable_masked`}.
  - New `brute/core/fallback.py::FallbackBruteLearner.observe`, which records for each issued cert whether the observed bits at that step were compatible with it. It uses the bit-compatibility rule of the existing `brute.core.learner.compatible_mass`.
  - `API_VERSION` becomes `brute.api/1.1`. v1 stays frozen.
- **Rule:**
  - `falsified_by_observation` only when the cert's own step's observation contradicts the certified code.
  - `scope_withdrawn` when the observation was consistent but the family was later contradicted.
  - `unverifiable_masked` when masking hid the bits.
- **Test:** new `tests/test_api_contract_v011.py`. It replays study-002 drift4: the 10 certs give 0 `falsified`, and the 6 study-001 drift4 wrong certs give `falsified_by_observation` unless their bits were masked.

**F4 = candidate (f): the F14 bounded witness audit (Observed-post-hoc tool, reported only).**
- **Target:** new `scripts/witness_audit.py::learner_witness_audit`. `scripts/open_world_counterexample.py` stays as it is.
- For every step where n≤4 certifies or the margin disagrees, it emits a concrete n≤5 machine that matches all the evidence so far but predicts a different code. The machine is taken from `bgr90.symbolic.SymbolicLearner(5)` rows.
- **Expected:**
  - 0 witnesses on CERTIFIED steps (Exact by construction of the margin gate).
  - A witness on each of the 3,697 in-family MARGIN_DISAGREES steps, which turns FM7 from a count into checkable counterexamples.
- **Test:** `tests/test_witness_audit.py`, on 3 small cases.

**F5 = candidate (d), reduced to honest labelling.**
- **Exact:**
  - Each of the 6 drift-step wrong certs was issued on a history that drift4 shares with its own pre-drift stationary 4-state machine, which is in the declared family.
  - On that in-family machine the same cert is correct.
  - So **any** causal certifier that keeps in-family coverage on those histories must issue the same wrong cert.
  - The only cases where it would not are refusing on some histories without evidence, or knowing the generator's period.
- **Kept:** no new gate in the learner. The cert already names `deterministic-moore<=4/stationary`. The fix is reporting:
  - F3 labels these as `falsified_by_observation`;
  - study-003 reports drift-step and non-drift-step false certs separately (§3).

### Modified

**(a) Family growth on contradiction (n≤5 learner, n≤6 margin).** Modified to **prediction-only** growth, which F1 already is. **Certification** after growth is deferred to v0.2.0, for three reasons:
- **Observed-post-hoc:** after contradiction on drift4, the n≤5 margin has 267 singletons and **44 are wrong**. On ood5 it has 1,434 singletons and 0 are wrong.
- So certifying after growth needs a working n≤6 margin. Its row cost is **Open**: the n≤5 peak was 99,818 rows of 160,000 on unstructured3, the n≤4 peak was 3,996, and n≤6 was never measured.
- The residual alarm would also have to be re-armed for the grown family.

**(e) Coverage recovery without new false certs.** Modified to measurement only (F4).
- **Observed-post-hoc:** every relaxation of MARGIN_DISAGREES that was considered would have released the 137 wrong out-of-family singletons, along with the 3,697 correct in-family ones. The gate cannot tell them apart from the evidence.
- Recovery needs new evidence, meaning **active experimentation**: choosing actions that split the margin. Study actions are fixed by `bgr89.worlds.actions`, so this is v0.2.0.

### Rejected

- **R1 = candidate (c): soften the contradiction-step floor by raising ε.**
  - Simulated, without F1: ε = 0.05 / 0.1 / 0.2 gives ood5 1.459246 / 1.42327 / 1.387823. All still fail ln 4.
  - Simulated in-family cost on unaliased2: 0.111583 → 0.13309 / 0.170205 / 0.249477. At ε ≥ 0.1 that is above v0.90 + 0.05 = 0.147559, so C7 fails.
  - With F1 the ε gain is small: ood5 0.665 → 0.634 at ε = 0.05, and every in-family family costs about 0.02.
  - Decision: keep ε = 0.02.
- **R2: margin mixture before contradiction** (fixes FM3). Simulated with λ = 0.1 / 0.25 / 0.5 plus fallback:
  - ood5: 0.567 / 0.523 / 0.495.
  - unaliased2: 0.174 / 0.278 / 0.486. That is > 0.147559 already at λ = 0.1, so C7 fails.
  - Rejected for v0.1.1; v0.2.0 may revisit it with a learned or calibrated λ.
- **R3: post-alarm no-certify window for drift** (part of candidate d). Exact: 0 of the 6 wrong certs had an alarm (residual 0.04–0.49 < τ). Study-002 drift4 had no alarm steps at all. It would change nothing.
- **R4: time-indexed family (state × t mod 11)** (part of candidate d). This encodes the test generator's drift period (`bgr90/worlds.py::step`, `t % 11 == 0`), which is leakage from the evaluator into the learner. A general change-point family with an unknown schedule is v0.2.0, and Open.
- **R5: editing frozen files** (`brute/core/learner.py`, `brute/api/service.py`, `scripts/explore_v020.py`). Doing so would break in-tree reproducibility of studies 001 and 002. See F0.

## 3. Study-003 criteria (DRAFT, not frozen)

Full text: `experiments/BRUTE_PLAN_003.DRAFT.json`.

**Rule:** the criteria are frozen by renaming the file to `BRUTE_PLAN_003.json` and committing it **before any v0.1.1 code**. Any later change is a ledger `deviation`.

Summary of the criteria (G = gated, R = reported):
- G1 in-family 0 false certs, conditional and public.
- G2 ood5 0 false certs.
- G3 drift4 0 false certs.
  - Gated as requested, with a pre-registered risk: Inferred, it is likely to fail on some seed blocks, because FM5 is unavoidable for a causal certifier.
  - An alternative is listed for the owner to choose before freezing: G3′, which gates non-drift-step false certs = 0 and total ≤ 0.5 × v0.90, and reports drift-step certs.
- G4 public safety.
- G5 in-family false-alarm case rate ≤ 0.05.
- G6 ood5 ≤ ln 4 (target 1.0 reported), drift4 ≤ the v0.1.0 arm on the same cases and ≤ ln 4, and minimum probability ≥ ε/4.
- G7 in-family log-loss ≤ v0.90 + 0.05, **and** pre-contradiction forecasts and decisions byte-identical to the v0.1.0 arm.
- G8 retraction reasons match the evaluator's truth.
- G9 compute: no new budget exhaustion, and peak rows ≤ 160,000.
- G10 independent reference (`experiments/v011_independent_reference.py`, new, no brute import).
- G11 byte-identical rerun.
- R1–R6: coverage, per-mask tables, F14 witnesses, the study-001 drift4 stress replay, runtime, and v0.89 paired.

Further rules:
- **Seeds:** new blocks 1230001–1290024, disjoint from study-001 (930001..990024), study-002 (1130001..1190024) and calibration.
- **Calibration:** τ stays 1.433141502274 and is not refit.
  - Exact: v0.1.1's forecasts before contradiction equal v0.1.0's, so the residual statistic on calibration data is unchanged.
  - Gate: rerunning calibration with v0.1.1 code must reproduce τ byte-for-byte.

## 4. Deferred to v0.2.0 (explicit)

1. Growth with certification: n≤5 learner, n≤6 margin, re-armed residual. This needs a pre-registered row-budget probe first, and the n≤6 rows are Open.
2. Active experimentation for coverage (FM7, FM8).
3. A general non-stationary (change-point) family (FM5).
4. Calibrated margin mixture before contradiction (FM3).
5. Alarm-triggered fallback (FM4).
6. A 6-state out-of-family world that tests F1's n≤5 assumption.
7. `NEXT_ITERATION.md`'s self-growing families.

## 5. Recommended order of work

1. Owner review of this plan.
   - Decide G3 vs G3′.
   - Approve pushing `plan/v0.1.1`.
2. **F2 cleanup.** It does not touch science.
3. **Freeze criteria:** commit `experiments/BRUTE_PLAN_003.json`, the DRAFT renamed with the owner's decisions and a pre-registration disclosure. Do this **before any v0.1.1 code**.
4. **F0 + F1:** `brute/core/fallback.py` and `tests/test_brute_fallback.py`.
5. **F3:** `service_v011.py`, schema v1.1 and `tests/test_api_contract_v011.py`.
6. **F4:** `scripts/witness_audit.py` and its test.
7. Study tooling. `experiments/brute_study_003.py` runs the arms v0.1.0 (frozen `BruteLearner`), v0.1.1, v0.90 and v0.89, plus baselines. Then `v011_independent_reference.py`, and the source freeze `BRUTE_SOURCE_FREEZE_003.json`.
8. Calibration reproduction check, then study-003, then gates, reproducibility rerun, independent audit and ledger.
9. Release v0.1.1. If G-criteria fail, publish the failure as is; do not tune again on study-003 seeds.

## 6. Files on this branch

- `BRUTE_v0.1.1_PLAN.md` (this file).
- `experiments/BRUTE_PLAN_003.DRAFT.json` (DRAFT, not frozen).
- `scripts/explore_v011.py` (new, read-only post-hoc).
- `docs/research/v0.1.1/POSTHOC_V011.json`, all labelled Observed-post-hoc or Simulated.
- `MANIFEST.sha256`, regenerated.
