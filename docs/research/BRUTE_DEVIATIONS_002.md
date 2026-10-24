# Recorded deviations: Brute v0.1.0 / study BRUTE-010-ABSTENTION-002

Pre-registration: `experiments/BRUTE_PLAN_002.json` (commit d402c75). The criteria C1–C11 were **not** changed after
registration. The items below are implementation differences from `BRUTE_v0.1.0_PLAN.md`; none touches a threshold.

1. **Code location.** Fixes live in new modules (`brute/core`, `brute/evaluation.py`, `experiments/brute_*`). The inherited
   `bgr*` packages, `experiments/run_study.py`, `experiments/independent_audit.py` and study-001 results are byte-identical
   to BGR v0.90.0 so study-001 stays reproducible under its own freeze (`experiments/SOURCE_FREEZE.json`).
2. **F10 (timing) and F13 (wall-clock) fixes** apply only to the new pipeline. Study-001 keeps its original timing fields.
3. **API wraps `BruteLearner`**, not the plan's `AdequacyLearner`, because the margin, saturation and residual gates live there.
4. **API status `ACKNOWLEDGED`** was added for operations that return no prediction.
5. **API request fields** `public` (bool, on predict) and `family {max_states, max_prefixes}` (on initialize) were added.
6. **`observe` returns `OUT_OF_FAMILY`** together with any retractions when a contradiction or residual alarm occurs.
7. **JSON schema validation** is a hand-written subset (type, enum, const, required, properties, additionalProperties,
   items, minimum, maximum) because no jsonschema dependency is allowed.
8. **Attestation** is accepted only on `initialize` and `retry`; `retry` never carries an earlier attestation forward.
9. **Probabilities after an alarm.** `BRUTE_PLAN_002` (authoritative) keeps the learner's probabilities after a residual
   alarm and uses uniform only after a contradiction; plan §4.4 says "uniform when OUT_OF_FAMILY". The study follows
   BRUTE_PLAN_002.
10. **Paired bootstrap parameters.** The plan records the bootstrap as a string ("paired, clustered by world seed, 2000
    resamples, seed 20261024"); `scripts/make_paired_analysis.py` checks that string and uses B=2000, seed 20261024.
11. **Release freeze.** API, adapter, generators and release checks are locked separately in
    `experiments/BRUTE_RELEASE_FREEZE_010.json` (they did not produce study-002 RESULTS).
12. **F14 (`learner_witness_audit`)** was not done. `scripts/open_world_counterexample.py` is unchanged.

## Criterion outcome reported, not tuned

C6 (open-world log-loss ≤ ln 4 on ood5 and drift4) **fails on ood5** (1.504767 > 1.386294). No threshold, ε, τ or
fallback was changed in response. It is carried into v0.2.0 (`NEXT_ITERATION.md`).
