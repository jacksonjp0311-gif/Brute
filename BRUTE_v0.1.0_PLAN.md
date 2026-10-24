# Brute v0.1.0: surgical improvement plan

**Base:** tag `bgr-v0.90.0-fork` (the unmodified BGR v0.90.0 source; see `FORK.md`)
**Goal:** the reasoner **abstains on anything it cannot verify** instead of certifying it. Every fix below is ordered, surgical, and testable.
**Status of this document:** this is a plan only. Nothing in it is implemented yet. Every number cites `results/study-001/` (frozen study `BGR-090-OPEN-SCOPE-AND-PREDICTIVE-QUOTIENT-001`: 7 families × 24 held-out seeds × 3 mask rates = 504 cases, 72 per family, 44 actions per case = 22,176 observations, burn-in 8) or a re-analysis of `results/study-001/SCIENTIFIC.json` done on 2026-10-24 (America/New_York). Proposed new names are marked **(new)**. All other names already exist in the code.

**Freeze rule.** `experiments/run_study.py` checks `experiments/SOURCE_FREEZE.json` before it runs, so editing `bgr90/*` in place invalidates study-001 reproduction. v0.1.0 therefore:
1. keeps study-001 reproducible from the git tag `bgr-v0.90.0-fork` (`git worktree add ../brute-v090 bgr-v0.90.0-fork`) rather than from nested zips;
2. makes all changes under a new frozen plan `experiments/PLAN.json` → study id `BRUTE-010-ABSTENTION-002` with a regenerated `SOURCE_FREEZE.json`;
3. pre-registers the success criteria in each fix below in that plan *before* running study-002.

---

## 0. What the review measured (the evidence each fix is tied to)

| Finding | Number | Source |
| --- | --- | --- |
| Out-of-family false conditional certifications | **140** = ood5 64/213 (30.0%) + drift4 76/293 (25.9%) | `results/study-001/RESULTS.json` summary |
| False certs issued **on the step whose observation then contradicts** the n≤4 family | **102 / 140** | re-analysis of SCIENTIFIC.json traces (`model_status_after`) |
| Steps from a false cert to the n≤4 contradiction | 0: 102, 1: 21, 2: 5, 3: 4, 4: 1, 5: 2, 6: 2, ≥10: 2; never contradicted: 1 | same |
| False certs where the masked observation was still compatible with the wrong code (an error that stays invisible at that step) | 38 / 140 | same |
| False certs issued after the nested n≤3 (v0.89) family had already been contradicted | 120 / 140 (20 while n≤3 was still alive) | same (`known_three_state_still_supported` on the previous record) |
| Correct in-grammar certs issued after n≤3 was contradicted (mostly ood4) | 1478 (4119 while n≤3 alive) | same |
| Family contradicted (n≤4) | ood5 72/72, drift4 68/72 | RESULTS summary |
| Public certificates | 0, because `scope_verified=False` is hard-coded | `bgr90/evaluation.py::run_case`, `experiments/independent_audit.py::audit` |
| Mean log-loss (uniform = ln 4 = 1.386) | ood5 **2.288978**, drift4 **2.188867** | RESULTS summary |
| Post-burn-in steps clamped at the 1e-12 floor (>20 nats) | ood5 95, drift4 99 | re-analysis |
| In-family certificates, v0.89 legacy vs v0.90 expanded | 7860 vs **4068** (−48%) | RESULTS summary (cycle3/switch3/unstructured3/unaliased2) |
| Expanded certificates counted inside burn-in | cycle3 11, switch3 6, unstructured3 9, unaliased2 12, ood4 16, ood5 21, drift4 9 | re-analysis |
| v0.89 predictive score per step | not recorded (`legacy_ll=None`) | `bgr90/evaluation.py::run_case` |
| Peak surviving partial rows | 4089 (unstructured3), budget 160000, no exhaustion | RESULTS summary |
| `open_world_counterexample` | **PASSED** (120 witness pairs; `tests/test90_limit.py` 2/2) | `scripts/open_world_counterexample.py::audit_witnesses` |

---

## 1. Ordered surgical fixes

Order: soundness first (F1–F5), then honest reporting (F6–F8), then reproducibility (F9–F11), then hygiene (F12–F13).

### F1. Make "no surviving machine" an explicit refusal, and retract the certificate it falsifies
- **Files:** `bgr90/symbolic.py` (`SymbolicLearner.observe`, `SymbolicLearner.predict_support`, `SymbolicLearner.snapshot`); `bgr90/adequacy.py` (`Forecast`, `AdequacyLearner.predict`, `AdequacyLearner.observe`).
- **Change:**
  - When `observe` catches `GrammarContradiction` (status `grammar_contradicted`), `AdequacyLearner` stops emitting the silent uniform `(.25,)*4` with `conditional_certificate=None`.
  - Instead it returns a typed status `OUT_OF_FAMILY` (new field `Forecast.status_code` **(new)**) plus `contradiction_step` and the evidence index.
  - Add `AdequacyLearner.retractions` **(new)**. When the observation at step t contradicts the family and a certificate was issued at step t, the record is marked `retracted=True` with reason `"falsified_by_observation"`.
  - `BudgetExceeded` maps to `ABSTAIN` with reason `BUDGET_EXHAUSTED`, never to `OUT_OF_FAMILY`.
- **Why:** 102/140 false certs are exactly the step that empties the version space. Today the only signal is a status string in a different field. This fix doesn't prevent those errors (that's F2/F3), but it makes every one of them machine-visible within 0 steps instead of being folded into a uniform forecast.
- **Proves it:** `tests/test_brute_abstention.py::test_contradiction_yields_out_of_family_and_retraction` **(new)**. Replay ood5 seed traces from study-001 and assert every certificate whose step ends in `grammar_contradicted` is retracted, and that the following steps report `OUT_OF_FAMILY`, not a probability vector without status.

### F2. Margin (nested-family) consistency gate: certify only if a larger family agrees
- **Files:** `bgr90/adequacy.py` (`AdequacyLearner.__init__`, `AdequacyLearner.predict`, `AdequacyLearner.observe`, `AdequacyLearner.retry`); reuse `bgr90/symbolic.py::SymbolicLearner` unchanged.
- **Change:**
  - Add a second learner, `self.margin = SymbolicLearner(max_states + 1, max_prefixes)` **(new attribute)**.
  - In `predict`, the conditional certificate is issued only if `support4 == margin_support` and both are singletons. Otherwise return `ABSTAIN` with reason `MARGIN_DISAGREES` and both supports as evidence.
  - `max_states + 1 ≤ 6` is already enforced by `SymbolicLearner.__init__`.
- **Why:** of the 140 false certs, the 64 ood5 errors come from 5-state worlds. A 5-state margin learner is consistent with the truth there by construction, so a singleton under n≤4 that n≤5 does not share is exactly the "unverifiable" case. The re-analysis also shows the nested-ladder signal is real: 120/140 false certs came after n≤3 was already contradicted, meaning the family bound was binding.
- **Not yet measured:** coverage cost and residual error. An exploratory replay (`/workspace/bgr/explore/margin_probe.py`, outside the repo) was stopped before it finished, so **no numbers are claimed**.
- **Pre-registered criteria for study-002:**
  - (a) ood5 false conditional certs fall from 64 toward 0 (n≤5 is in scope for ood5, so the target is 0);
  - (b) in-family false certs stay at 0;
  - (c) in-family coverage loss is reported, not hidden (F6).
  - drift4 is *not* expected to reach 0, because it is nonstationary and no stationary n≤5 family contains it (see F4).
- **Cost:** each margin learner also needs a row budget. Report `peak rows` for both (F6).
- **Proves it:**
  - `tests/test_brute_abstention.py::test_margin_gate_blocks_ood5_false_certificates` **(new)**: a frozen subset of ood5 seeds where study-001 issued wrong certs must now produce `ABSTAIN/MARGIN_DISAGREES` or a correct certificate, with zero wrong ones.
  - `::test_margin_gate_preserves_in_family_soundness` **(new)**.

### F3. Saturation check: abstain when the state bound is binding
- **Files:** `bgr90/symbolic.py` (`Prefix.used`, `SymbolicLearner.predict_support`; new helper `SymbolicLearner.bound_saturated()` **(new)**); `bgr90/adequacy.py::AdequacyLearner.predict`.
- **Change:**
  - `bound_saturated()` returns True when every surviving `Prefix` in `self.belief` has `used == self.max_states`, meaning every explanation already needs the full state budget.
  - A singleton support under a saturated bound is downgraded to `ABSTAIN` with reason `BOUND_SATURATED`, unless the F2 margin learner agrees **and** is itself unsaturated.
- **Why:** this is the cheap, single-learner form of the n-ladder signal above (120/140 false certs came after the smaller family broke). It costs O(|belief|) and needs no second learner, so it is the fallback when the F2 margin budget is too expensive.
- **Proves it:** `tests/test_brute_abstention.py::test_saturated_bound_abstains` **(new)**. Build a 5-state world (reuse `bgr90/worlds.py::world(seed,'ood5')`) and assert no certificate is issued while `bound_saturated()` is True and the margin is unavailable.

### F4. Held-out residual (prequential surprise) test and the drift4 case
- **Files:** `bgr90/adequacy.py` (`AdequacyLearner.observe`, `AdequacyLearner.predict`, new `AdequacyLearner.surprise_window` **(new)**); `bgr90/worlds.py` (docstring only, see below).
- **Change:**
  - Keep a sliding window (pre-registered W, for example 8) of `-log p(observed bits)` under the *pre-observation* forecast.
  - If the windowed surprise exceeds a pre-registered threshold relative to the in-family calibration (taken from study-001's in-family families only), return `OUT_OF_FAMILY` with reason `RESIDUAL_SURPRISE` and stop certifying until `retry` is called.
  - Fix the `bgr90/worlds.py` docstring, which calls the stress worlds "stochastic". `drift4` is deterministic and time-dependent: it shifts state `+1 mod n` every 11 steps.
- **Why:** drift4 produced 76 false certs, and 4/72 drift4 cases were *never* contradicted by the n≤4 family. A stationary-family margin (F2) cannot catch a time-indexed rule change. A residual test catches it statistically, and it is the only sound move short of adding a nonstationary family.
- **Proves it:** `tests/test_brute_abstention.py::test_residual_surprise_flags_drift4` **(new)**. On drift4 seeds, after the first rule shift, certification must stop within W steps. On cycle3/switch3/unstructured3/unaliased2 the false-alarm rate is reported, and it must be ≤ the pre-registered value.

### F5. Empty or collapsed version space and consistency against the surviving set
- **Files:** `bgr90/symbolic.py::SymbolicLearner.observe` / `_update`; `bgr90/adequacy.py::AdequacyLearner.observe` (the `legacy_valid=False` path).
- **Change:**
  - When `SymbolicLearner.count` drops to 0, or `AdequacyLearner.legacy_valid` flips to False, emit an explicit event `{kind:'family_contradicted', family:'n<=K', step}` **(new)** into a per-learner event log.
  - Any later certificate must name the family it is conditional on.
  - Add a consistency assertion: an issued certificate must be compatible with **every** surviving prefix (this is already true by construction in `predict_support`, but make it a checked invariant, `SymbolicLearner.check_certificate_against_belief` **(new)**, so regressions fail loudly).
- **Why:** today a v0.89 contradiction (`legacy_valid=False`; ood4 71/72) and a v0.90 contradiction are recorded in different shapes, and a reader can't see which family a certificate was conditional on.
- **Proves it:** `tests/test_brute_abstention.py::test_every_certificate_names_its_family_and_is_belief_consistent` **(new)**.

### F6. Coverage reported against error (risk–coverage) and consistent burn-in
- **Files:** `bgr90/evaluation.py` (`run_case`, `aggregate`).
- **Change:**
  - Count certificates and errors over `records[burn_in:]` only, the same window as log-loss. Study-001 counted burn-in certificates, for example ood5 21 and cycle3 11.
  - `aggregate` reports per family and mask rate:
    - coverage = certificates / post-burn-in predictions;
    - selective risk = wrong / certificates;
    - abstention counts by reason;
    - the v0.89 legacy coverage on the same steps.
  - Add a risk–coverage table to `RESULTS.json`.
- **Why:** in-family certificates fell from 7860 to 4068 (−48%) and the study reports that as raw counts only. The drop is the price of a larger hypothesis family, and it should be shown as a tradeoff, not hidden or "fixed" by weakening the gate.
- **Proves it:** `tests/test_brute_reporting.py::test_burn_in_excluded_consistently` **(new)** and `::test_aggregate_reports_coverage_and_selective_risk` **(new)**.

### F7. Probability floor: no score below uniform from a clamp
- **Files:** `bgr90/adequacy.py::AdequacyLearner.predict`; `bgr90/evaluation.py::run_case` (`new_ll=-log(max(1e-12, ...))`); `bgr89/evaluation.py::loss`.
- **Change:**
  - Replace the evaluator-side `max(1e-12, p)` with a **model-side, mass-preserving open-world reserve**: `p = (1-ε)·p_model + ε·uniform4`, with ε pre-registered (for example 0.02). Per-step loss is then bounded by `-log(ε/4)`.
  - Report both the ε-reserved loss and the unreserved loss, together with the uniform baseline ln 4.
  - When status is `OUT_OF_FAMILY`, the forecast is uniform **and labelled as such**.
- **Why:** ood5 2.288978 and drift4 2.188867 are worse than uniform (1.386) because 95 and 99 post-burn-in steps put ~0 mass on the actual code and were clamped to 1e-12 (≈27.6 nats). An honest reasoner that can't verify should be at worst uniform, not confidently wrong.
- **Proves it:** `tests/test_brute_reporting.py::test_no_probability_zero_on_any_code` **(new)** asserts `min(forecast.probabilities) ≥ ε/4` on all 7 families. A study-002 gate requires mean loss ≤ ln 4 + tolerance on ood5 and drift4.

### F8. Restore the v0.89 predictive-score comparison
- **Files:** `bgr90/adequacy.py` (`Forecast` gains `legacy_probabilities` **(new field)**; `predict` already computes `legacy_probs` but drops it); `bgr90/evaluation.py::run_case` (`legacy_ll` is set to None and never filled); `bgr90/evaluation.py::aggregate`.
- **Change:**
  - Record `legacy_ll` per step whenever `legacy_valid` is True.
  - Compute the paired per-step difference `new_ll − legacy_ll` with a seeded bootstrap CI. The seed is written into the result.
  - Also report the suffix baselines that `bgr89/evaluation.py::run_case` already scores (`bgr89/baselines.py::SuffixFrequency`, k = 1, 2, 4).
- **Why:** v0.90 claims an improvement over v0.89 but records no v0.89 predictive score per step. `results/PAIRED_ANALYSIS.json` compares false-cert counts only (old 78 / new 0) and has no generator.
- **Proves it:** `tests/test_brute_reporting.py::test_legacy_logloss_recorded_when_legacy_valid` **(new)**.

### F9. Generator scripts for every reported number; no literals in `verify_release`
- **Files:** `scripts/verify_release.py::verify`; new `scripts/make_gates.py` **(new)**, `scripts/make_paired_analysis.py` **(new)**, `scripts/make_reproducibility.py` **(new)**; `experiments/independent_audit.py::audit`.
- **Change:**
  - `results/GATES.json`, `results/PAIRED_ANALYSIS.json` (including its bootstrap interval [68,88]) and `results/REPRODUCIBILITY.json` must each be regenerated by a script from `RESULTS.json`/`SCIENTIFIC.json`, with the seed recorded.
  - `verify` currently asserts 26 times, including literal values (22176 observations, 6103 certificates, 140, 78, 0, 21 UI examples, last ledger event `promotion_gates`). It must instead re-run the generators and compare byte-equality.
  - `independent_audit.audit` returns `'unattested_public_certificates':0` as a literal; it must return the computed count.
  - Replace bare `assert` in `verify`, `independent_audit.audit`, `experiments/v90_independent_reference.py::audit_case`, and `scripts/open_world_counterexample.py::replay` with explicit `if …: raise VerificationError` **(new exception)**. Under `python -O`, every `assert` is stripped and the audit passes vacuously.
- **Why:** several headline numbers cannot be regenerated from the repo today, and the verifier checks constants rather than recomputing them.
- **Proves it:**
  - `tests/test_brute_repro.py::test_generators_reproduce_results_bytes` **(new)**;
  - `::test_verify_fails_under_tampered_results` **(new)**;
  - `::test_audit_not_vacuous_under_python_O` **(new)**, which runs the audit in a subprocess with `-O` on a tampered file and expects failure.

### F10. Timing-field bug in reproducibility
- **Files:** `experiments/run_study.py::no_time`.
- **Change:** add `total_elapsed_informational` to the stripped keys. Today only `elapsed_informational` and `time_informational_seconds` are stripped, so the top-level total, set in `run_study.run`, leaks into the "time-free" comparison.
- **Why:** gate G7 ("wall-clock timings excluded") is violated by the top-level key.
- **Proves it:** `tests/test_brute_repro.py::test_no_time_strips_all_timing_keys` **(new)** builds a result dict with all three keys and asserts none survive. Then two runs of a tiny plan must produce identical stripped hashes.

### F11. Honest public-certificate path (replace the hard-coded `scope_verified=False`)
- **Files:** `bgr90/adequacy.py` (`AdequacyLearner.__init__(…, scope_verified=False)`, `predict` (`public=conditional if self.scope_verified else None`), `retry` (resets to False), `diagnostics`); `bgr90/evaluation.py::run_case` (hard-codes `AdequacyLearner(..., scope_verified=False)` and `'scope_verified_externally':False`); `experiments/independent_audit.py::audit`; `scripts/demo.py::main`.
- **Change:**
  - Replace the Boolean with a `ScopeAttestation` **(new)** dataclass: `attester`, `family` (for example `deterministic_moore<=4_stationary`), `evidence_sha256`, `issued_at`, `valid_for_world_id`, `revoked`.
  - A public certificate requires all of:
    1. a non-revoked attestation whose family equals the learner family;
    2. F2 margin agreement;
    3. no F4 residual alarm;
    4. no F1 contradiction.
  - `retry` revokes the attestation (preserving the current `scope_verified=False` semantics).
  - The study plan lists which worlds are attested. In study-002, only the in-family worlds generated by `bgr89/worlds.py::world` with known n ≤ 4 can be attested, and **only by the evaluator**, never by the learner.
- **Why:** today zero public certificates can ever be issued. G2 passes vacuously, because the switch is hard-coded False in three places, and the audit returns a literal 0.
- **Proves it:**
  - `tests/test90.py::test_unverified_grammar_never_issues_public_cert` and `::test_lab_attestation_conditional_only_within_scope` stay green (existing);
  - `tests/test_brute_abstention.py::test_public_cert_requires_attestation_margin_and_no_alarm` **(new)**;
  - `::test_retry_revokes_attestation` **(new)**.

### F12. Release hygiene: no nested zips; the baseline lives in git
- **Files:** `scripts/verify_release.py::verify` (asserts `baseline/BGR-v0.89.0.zip`); `scripts/package_release.py::pack`; `MANIFEST.sha256`; `baseline/IDENTITY.json`; `.gitattributes`.
- **Change:**
  - The baseline becomes an **external pinned artifact** (path + sha256 `2ae5e464…4c1e4a2`, recorded in `FORK.md`). `verify` checks it only if present and otherwise reports `baseline: external (not present)`.
  - Regenerate `MANIFEST.sha256` for Brute without the baseline.
  - `pack` builds from `git archive <tag>` instead of zipping a tree that already contains the previous zip. The current chain nests v0.89 → … → v0.11 and is 66% of the 107.5 MB release.
  - Add `pyproject.toml` with pinned Python ≥3.11 / NumPy and a single `python -m unittest discover -s tests` entry.
- **Why:** in the fork, `python -m scripts.verify_release` currently fails with `FileNotFoundError: baseline/BGR-v0.89.0.zip` (expected, documented in `FORK.md`).
- **Proves it:** `python -m scripts.verify_release` passes in a clean clone of the tag. `tests/test_brute_repro.py::test_manifest_matches_tracked_files` **(new)**.

### F13. Align defaults
- **Files:** `bgr90/adequacy.py::AdequacyLearner.__init__` (`max_prefixes=200000`) vs `bgr90/symbolic.py::SymbolicLearner.__init__` / `bgr90/evaluation.py::run_case` (`160000`).
- **Change:** use a single constant, `DEFAULT_MAX_PREFIXES` **(new)**, in `bgr90/symbolic.py`.
- **Why:** a silent mismatch between the demo/library default and the study budget.
- **Proves it:** `tests/test_brute_repro.py::test_default_budgets_match_plan` **(new)**.

---

## 2. `open_world_counterexample`: it **passed**

James's reading was that it failed. It did not: `scripts/open_world_counterexample.py::audit_witnesses(seeds=120)` returned a passing status, `scripts/demo.py` runs `audit_witnesses(20)`, and `tests/test90_limit.py` (`FinitePrefixLimitTests`, 2 tests) passes.

**What it tests**
- `completion_pair(evidence, next_action)` builds two `WitnessMachine` chain machines. Each has k+2 states for a history of length k, and they differ only in the sink emission (0 vs 3).
- `replay` checks that both reproduce the same evidence.
- Conclusion: for an *unbounded* state family, any finite prefix admits two consistent completions that disagree on the next emission, so **no finite evidence can certify without a bound.** This is the theoretical reason public certificates need an external scope attestation.

**What it does not test**
- It never touches `SymbolicLearner` or `AdequacyLearner`. It uses its own `compatible`.
- Witness size grows with the history (up to 21 states for 0..19-length prefixes), so it says nothing about the *bounded* n=5 case that produced the 64 ood5 errors.
- It relies on `assert` (see F9).

**Strengthen it (F14):**
1. `scripts/open_world_counterexample.py::learner_witness_audit` **(new)**: for every study trace step where `SymbolicLearner(4)` certifies y, search with `SymbolicLearner(5)` for a consistent machine predicting ≠ y, giving a *bounded, minimal* divergent completion. Count the steps where one exists. This directly measures how many n≤4 certificates are unverifiable at n≤5, which is the F2 target.
2. Assert that `AdequacyLearner` with the F2 gate never certifies on those steps.
3. Run it in `tests/test90_limit.py` with explicit raises instead of `assert`, plus a `-O` subprocess check.

---

## 3. Architectural changes needed before a language adapter

Every point is grounded in the current code.

1. **Hard-coded binary alphabets.**
   - `bgr90/symbolic.py` encodes emissions as 2-bit codes, with `ALL=0b1111` as the full mask over 4 codes. `mask_for_observation(obs)` requires exactly 2 channels.
   - `bgr89/latent.py::code_to_bits`, `matches_observation` and `check_observation` assume 2 bits.
   - Transitions are indexed as `current*2+action` with actions in (0,1), and `Forecast.probabilities` is a 4-tuple.
   - `bgr90/quotient.py::minimize_moore` accepts emission codes 0..3 only.
   - **Change:** an `Alphabet` **(new)** object (`actions: tuple[str,...]`, `channels: tuple[ChannelSpec,...]`) that owns encoding/decoding, so masks become `2**|codes|`-wide bitsets.
2. **Enumerated finite-state family.**
   - `bgr89/latent.py::machine_catalogue(n)` enumerates n ∈ 1..3 only.
   - `bgr90/symbolic.py::SymbolicLearner` allows `max_states` 1..6, with partial-prefix rows capped by `max_prefixes`; `bgr90/quotient.py` caps n at 32.
   - The family is "deterministic, stationary Moore ≤ K", fixed in code.
   - **Change:** a `HypothesisFamily` **(new)** interface (`initialize`, `successors`, `support`, `contradicted`, `bound_saturated`, `scope_id`). Then F2's margin learner and F4's nonstationary family become pluggable members, not ad-hoc second instances.
3. **Observation/action interfaces.**
   - Inputs are bare Python ints and tuples (`observe(action, obs)` with `obs` like `(1, None)`).
   - Control flow runs on exceptions (`IncompatibleObservation`, `BudgetExceeded`, `GrammarContradiction`) and status strings.
   - **Change:** typed `Observation`/`Action` **(new)** records with validation at the boundary, and status as an enum instead of strings.
4. **Certificate API.**
   - The de facto output is `bgr90/adequacy.py::Forecast`, where `None` means several things at once (not a singleton, not supported, unattested).
   - There is no status enum, no reason code, no evidence fields, no schema version, and no serializer.
   - **Change:** the `brute/api` contract in §4.
5. **Scaling.**
   - `SymbolicLearner.belief` is a frozenset of `Prefix` rows and grows combinatorially with `max_states` and masking (peak 4089 rows in study-001 at n≤4; budget 160000; n is capped at 6).
   - `machine_catalogue` is exhaustive.
   - The bit-level family can't scale to language-sized alphabets. Structure (factorized channels, learned abstraction) must come *before* the reasoner, and the reasoner must keep abstaining when the structure is unverified.
6. **Abstention as first-class output.**
   - Today abstention is expressed as `conditional_certificate=None` plus a free-text `warning`.
   - It must become a typed result with a reason enum (`MARGIN_DISAGREES`, `BOUND_SATURATED`, `RESIDUAL_SURPRISE`, `BUDGET_EXHAUSTED`, `UNATTESTED_SCOPE`, `NOT_INITIALIZED`) so a downstream layer can pass it through verbatim.
7. **Cross-version imports.** `bgr90` imports `bgr89.latent` and `bgr89.worlds`. The core should be one package, `brute/core/` **(new)**, with an explicit dependency on a pinned legacy comparator, not on sibling version directories.

---

## 4. Language Adapter API

**Principle:** the language adapter **only states what Brute returned**. It never embellishes, never fills gaps, and never upgrades an abstention into an answer. This is enforced by schema validation, field-referenced templates, verbatim refusals, and a grounding checker test.

### 4.1 Contract (`api_version` = `"brute.api/1.0"`)

**Request** (`brute/api/schema/request.v1.json` **(new)**)
```json
{
  "type": "object",
  "required": ["api_version", "session_id", "op"],
  "properties": {
    "api_version": {"const": "brute.api/1.0"},
    "session_id":  {"type": "string"},
    "op":          {"enum": ["initialize", "observe", "predict", "retry", "snapshot"]},
    "action":      {"type": "string", "description": "symbol from Alphabet.actions"},
    "observation": {"type": "object", "additionalProperties": {"type": ["integer", "null"]},
                    "description": "channel name -> value or null (masked)"},
    "family":      {"type": "object", "properties": {"max_states": {"type": "integer", "minimum": 1, "maximum": 6},
                                                      "margin_states": {"type": "integer"},
                                                      "max_prefixes": {"type": "integer"}}},
    "attestation": {"$ref": "#/definitions/ScopeAttestation"}
  }
}
```

**Response** (`brute/api/schema/response.v1.json` **(new)**)
```json
{
  "type": "object",
  "required": ["api_version", "request_id", "status", "evidence"],
  "properties": {
    "api_version": {"const": "brute.api/1.0"},
    "request_id":  {"type": "string"},
    "status":      {"enum": ["CERTIFIED", "POSSIBLE_SET", "ABSTAIN", "OUT_OF_FAMILY", "ERROR"]},
    "certificate": {"type": ["object", "null"], "properties": {
        "value": {"type": "object", "description": "decoded emission, channel -> value"},
        "kind":  {"enum": ["conditional", "public"]},
        "conditional_on": {"type": "string", "description": "family scope_id, e.g. deterministic_moore<=4_stationary"}}},
    "support":     {"type": ["array", "null"], "items": {"type": "object"}},
    "probabilities": {"type": "array", "items": {"type": "number"}, "description": "with open-world reserve eps (F7)"},
    "reason":      {"enum": [null, "MARGIN_DISAGREES", "BOUND_SATURATED", "RESIDUAL_SURPRISE",
                             "BUDGET_EXHAUSTED", "UNATTESTED_SCOPE", "FAMILY_CONTRADICTED",
                             "NOT_INITIALIZED", "INVALID_REQUEST", "INTERNAL"]},
    "refusal_text": {"type": ["string", "null"], "description": "canonical sentence; adapters must pass verbatim"},
    "retractions": {"type": "array", "items": {"type": "object", "properties": {
        "step": {"type": "integer"}, "previous_value": {"type": "object"}, "reason": {"const": "falsified_by_observation"}}}},
    "evidence": {"type": "object", "required": ["step", "family_scope", "surviving_rows", "margin", "saturated",
                                                 "residual", "attestation_id", "source_sha256"],
      "properties": {
        "step": {"type": "integer"},
        "family_scope": {"type": "string"},
        "surviving_rows": {"type": "integer"},
        "margin": {"type": "object", "properties": {"states": {"type": "integer"}, "agrees": {"type": ["boolean", "null"]},
                                                    "support_size": {"type": ["integer", "null"]}}},
        "saturated": {"type": "boolean"},
        "residual": {"type": "object", "properties": {"window": {"type": "integer"}, "surprise": {"type": "number"},
                                                      "threshold": {"type": "number"}, "alarm": {"type": "boolean"}}},
        "legacy_family_alive": {"type": "boolean"},
        "attestation_id": {"type": ["string", "null"]},
        "evidence_count": {"type": "integer"},
        "source_sha256": {"type": "string", "description": "hash of the frozen core source"}}}
  }
}
```

**Status semantics**

| Status | When | `certificate` | `reason` |
| --- | --- | --- | --- |
| `CERTIFIED` | singleton support, margin agrees, unsaturated or margin-unsaturated, no residual alarm, family not contradicted | `kind:"conditional"`. `kind:"public"` **only** with a valid, non-revoked `ScopeAttestation` | null |
| `POSSIBLE_SET` | support has more than 1 code and the family is consistent | null | null (the set is in `support`) |
| `ABSTAIN` | singleton blocked by a gate, the budget is exhausted, or the scope is unattested for a public request | null | gate reason |
| `OUT_OF_FAMILY` | version space empty (F1/F5) or residual alarm (F4) | null; past certificates listed in `retractions` | `FAMILY_CONTRADICTED` / `RESIDUAL_SURPRISE` |
| `ERROR` | invalid request, unknown symbol, wrong schema version, internal exception | null | `INVALID_REQUEST` / `INTERNAL` |

**Errors and refusals**
- The service never raises across the boundary. Exceptions become `ERROR` with a stable `reason`.
- `refusal_text` is produced by the core from a fixed table keyed by `reason`, in `brute/api/refusals.py` **(new)**, for example `FAMILY_CONTRADICTED: "No machine in the declared family is consistent with the evidence; Brute will not predict."`. Adapters must reproduce it **byte-for-byte**.

**Versioning**
- `api_version` is semver-like: `brute.api/MAJOR.MINOR`.
- Adding optional fields is a MINOR change. Changing an enum or a required field is a MAJOR change.
- A mismatched MAJOR returns `ERROR/INVALID_REQUEST`.
- Schemas are hashed into `MANIFEST.sha256`, and `evidence.source_sha256` pins the core source.

### 4.2 Files that expose the surface

**New**

| Path | Purpose |
| --- | --- |
| `brute/__init__.py` | package root, `__version__ = "0.1.0"` |
| `brute/api/__init__.py` | the only public import surface: `handle(request: dict) -> dict`, `Status`, `Reason`, `API_VERSION` |
| `brute/api/schema.py` | dataclasses `Request`, `Response`, `Certificate`, `Evidence`, `ScopeAttestation`, `Status(Enum)`, `Reason(Enum)`; `validate_request`, `validate_response` |
| `brute/api/schema/request.v1.json`, `brute/api/schema/response.v1.json` | the JSON schemas above |
| `brute/api/service.py` | `BruteService`: sessions, wrapping `bgr90.adequacy.AdequacyLearner` (after F1–F5, F7, F11) and translating `Forecast` → `Response` |
| `brute/api/alphabet.py` | `Alphabet`, `ChannelSpec`: symbol ↔ code mapping; v0.1.0 ships the 2-action / 2-channel alphabet only |
| `brute/api/refusals.py` | canonical `refusal_text` table |
| `adapters/language/__init__.py` | adapter package (separate component) |
| `adapters/language/render.py` | `render(response: dict) -> list[Claim]`, where `Claim = {text, field_refs}`, from templates |
| `adapters/language/templates.py` | one template per (status, reason). Every slot is a JSON pointer into the response |
| `adapters/language/checker.py` | `check(response, claims) -> list[Violation]` |
| `tests/test_api_contract.py` | schema round-trip; every `Forecast` path maps to exactly one status; `ERROR` on bad input; version mismatch |
| `tests/test_adapter_boundary.py` | AST import-scan enforcement (see §4.3) |
| `tests/test_adapter_grounding.py` | grounding checker (see §4.3) |

**Existing files to touch**
- `bgr90/adequacy.py`: `Forecast` gains `status_code`, `reason`, `legacy_probabilities`, `evidence`, `retractions`; `AdequacyLearner.predict` / `observe` / `retry` / `diagnostics` change per F1–F5, F7, F8, F11.
- `bgr90/symbolic.py`: `SymbolicLearner.bound_saturated`, `check_certificate_against_belief`; snapshot fields for `evidence`.
- `bgr90/evaluation.py`: `run_case` / `aggregate` consume the status enum (F6–F8).
- `scripts/demo.py::main`: drive the demo through `brute.api.handle`, so the demo exercises the public surface.
- `scripts/verify_release.py`: verify schema hashes (F9, F12).
- `MANIFEST.sha256`: regenerated to include `brute/` and `adapters/`.

### 4.3 The adapter as its own component, with enforced boundaries
- **Dependency direction:** `adapters/language` → `brute.api` only. `brute.api` → `bgr90`/`bgr89` (later `brute.core`). Nothing in `brute/` or `bgr*/` imports `adapters`.
- **Adapter input:** the adapter takes only the response **dict** (JSON-decoded). It never receives learner objects.
- **`tests/test_adapter_boundary.py`:**
  - `test_adapter_imports_only_api`: parse every `adapters/**/*.py` with `ast`. Every `Import`/`ImportFrom` must be stdlib or start with `brute.api`. Fail on `bgr*`, `brute.core`, `experiments`, `scripts`, `numpy`.
  - `test_core_never_imports_adapter`: scan `bgr*/`, `brute/`, `experiments/`, `scripts/` for imports of `adapters`.
  - `test_adapter_has_no_side_channel`: the adapter module defines no reads of files or environment (AST check for `open`, `os.environ`, `importlib`).
- **`tests/test_adapter_grounding.py`:**
  - `test_every_claim_has_field_refs`: for responses produced from replayed study traces (all statuses), every `Claim.field_refs` is non-empty and each JSON pointer resolves in the response.
  - `test_claim_text_is_template_of_refs`: re-render each claim from its template and the referenced values. The text must match exactly, so no free text exists.
  - `test_refusal_passthrough_verbatim`: for `ABSTAIN` / `OUT_OF_FAMILY` / `ERROR`, the rendered output contains `refusal_text` byte-for-byte and **no** claim with a predicted value.
  - `test_checker_rejects_unbacked_sentence`: append a hand-written sentence (for example "The next reading will almost certainly be 1.") to the claims. `checker.check` must return a violation. The same applies to a claim whose cited field is null, and to a `kind:"public"` wording when `certificate.kind=="conditional"`.
  - `test_no_upgrade_of_status`: the adapter never says "certain"/"will" for `POSSIBLE_SET`, and never names a single value unless `status=="CERTIFIED"`.

### 4.4 How each soundness fix maps onto the API

| Fix | Status produced | Fields populated |
| --- | --- | --- |
| F1 contradiction + retraction | `OUT_OF_FAMILY` | `reason=FAMILY_CONTRADICTED`, `retractions[]`, `evidence.step`, `evidence.surviving_rows=0`, `refusal_text` |
| F2 margin gate | `ABSTAIN` (or `CERTIFIED` when agreeing) | `reason=MARGIN_DISAGREES`, `evidence.margin.{states,agrees,support_size}`, `support` |
| F3 saturation | `ABSTAIN` | `reason=BOUND_SATURATED`, `evidence.saturated=true`, `evidence.family_scope` |
| F4 residual test (drift4) | `OUT_OF_FAMILY` | `reason=RESIDUAL_SURPRISE`, `evidence.residual.{window,surprise,threshold,alarm}` |
| F5 collapsed space / named family | any | `certificate.conditional_on`, `evidence.family_scope`, `evidence.legacy_family_alive` |
| F7 open-world reserve | all | `probabilities` (min ≥ ε/4), uniform when `OUT_OF_FAMILY` |
| F11 attestation | `CERTIFIED` with `kind:"public"`, or `ABSTAIN/UNATTESTED_SCOPE` when a public cert is requested without one | `evidence.attestation_id`, `certificate.kind` |
| Budget (`BudgetExceeded`) | `ABSTAIN` | `reason=BUDGET_EXHAUSTED`, `evidence.surviving_rows` |

**Pre-registered target for study-002 through the API:** zero `CERTIFIED` responses whose value differs from the evaluator-only emission, across all 7 families. Every one of the 140 study-001 false certifications must surface as `ABSTAIN` or `OUT_OF_FAMILY` (or as a retraction, for the step that contradicts). Coverage and the abstention breakdown are reported per family (F6).
