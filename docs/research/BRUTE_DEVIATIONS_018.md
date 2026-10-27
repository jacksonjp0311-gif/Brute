# BRUTE study-018 deviations (BRUTE-0160-NOISY-OBSERVATION-018)

Numbering continues project-wide (study-017 ended at #96). Every entry here is written BEFORE the code it governs and
before the source freeze; no held-out seed (8410001-8440048) has been generated, simulated or inspected. Later
deviations go in `BRUTE_DEVIATIONS_018_ADDENDUM_<k>.md` (this file is ledger-hashed and is never edited).

## #97 Pre-code design disclosures (decision rule, certificate unit, GN0, flip array, m, arms)

Written after the seed check (`seedcheck_018`) and before `experiments/v0160_reference.py`, `brute/noisyregion.py` and
`brute/api/certify6.py` exist.

1. **RGN decision rule.** At step t and action b, RGN4(m) certifies code c iff t > burn_in (8), the tolerant region is
   feasible (status supported) and its support for action b is the singleton {c}. There is **no SP8 passthrough and
   no SP8-support filter** (unlike RG = frozen `rg_decide`): the SP8 learner is noise-unaware, so either would import
   its unsoundness into the headline arm. A SAT UNKNOWN (conflict budget) counts the code as possible (frozen
   conservative semantics); an infeasible region (more than m flips needed) certifies nothing. Label: Exact (definition).
2. **Certificate unit.** As in studies 014-017: one certificate per (step, action) = the predicted full 2-bit latent
   code of the next reading; coverage C = certificates / 88 with 88 = 44 steps x 2 actions (the plan's "latent bits"
   and "reading-bits" wording means these 88 (step, action) slots). A certificate is false iff it differs from the
   evaluator-only latent (noise-free) code. Label: Exact (definition).
3. **GN0 is scored as written and is predicted to FAIL.** RG4 (frozen `rg_decide`) passes SP8 certificates through at
   every step, including burn-in, and filters region singletons by the SP8 support; RGN4_0 does neither (item 1). On
   seen data (sealed study-017 transfer, RG4 vs region-only rule) RG4 had 4,602 certificates against 4,599 for the
   region rule, the 3 extra being burn-in SP8 passthroughs; so certificate-for-certificate equality on 120 eps = 0
   cases is expected to fail on a few burn-in slots. Prediction for GN0: Inferred FAIL (the plan's "Exact PASS"
   prediction was wrong at the time of writing; it is not changed). Reported in addition, NOT replacing GN0:
   - R_gn0_support (Exact check): RGN4_0 supports equal the frozen `RegionSpace(4)` supports at every step of every case
     (same CNF with every flip forced to 0);
   - R_gn0_post_burn: RGN4_0 == RG4 certificate-for-certificate at every t > burn_in on the eps = 0 cases (Inferred PASS).
4. **Learner configuration.** Plan 018 has no `tau6` / `mask_rates` keys; the frozen SP8 learner configuration is the
   study-013 plan (as in 014-017), read by `experiments/brute_common_018.learner_plan`, which asserts burn_in = 8,
   44 actions per case and mask 0.35 in plan 013's mask rates, and uses plan 013's tau6 = 1.645215321642.
5. **Flip array.** `F = numpy.random.default_rng([seed, round(1000*eps), 18]).random((45, 2)) < eps`; row 0 is the
   initial reading, row i+1 the reading after action i (step i+1); column j is bit j (bit 0 = code >> 1, bit 1 =
   code & 1, as `codes_mask`). A bit is flipped iff it is observed (not masked) and F is True there; masked bits stay
   None. Realized flips = number of flipped observed bits (Exact count, recorded). eps = 0 draws the same array and
   flips nothing.
6. **B and m.** B = number of observed (non-None) bits over the 45 readings, recomputed from the mask before the first
   action and checked equal to the count on the trajectory. m = smallest integer with P(Bin(B, 0.02) > m) <= 0.01,
   with `fractions.Fraction` arithmetic (identical function in the runner and in `brute/api/certify6.py`; the reference
   recomputes it independently).
7. **Arms.** RGN4_or uses m = realized flips; when that equals 0 or m its supports are those of RGN4_0 / RGN4 (same CNF,
   shared and marked `shared_with`), otherwise it is solved separately. RG4 is the frozen `rg_arm` on the frozen
   `RegionSpace(4)` supports of the noisy observations. SP8 is the frozen learner on the noisy observations (it may
   become grammar-contradicted; its counts are reported).
8. **Blocks and smoke.** One `transfer` stream: the 360 main cases (family order cycle3, switch3, unaliased2, ood4;
   eps 0, 0.01, 0.02) followed by the 120 stress cases (eps 0.05). Smoke layout: `scripts/check_seeds_018.py`
   (8490001-08 rate-math sample x 4 eps = 32 cases, 8490009-12 API test, 8490013-15 kill drill).

Labels: items 1, 2, 5, 6, 7 Exact (definitions); item 3 prediction Inferred, seen-data counts Observed; item 4 Exact.
