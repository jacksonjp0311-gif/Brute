# Study-014 (v0.12.0) deviations and disclosures

Numbering continues project-wide. Study-013 ended at #58 (docs/research/BRUTE_DEVIATIONS_013_ADDENDUM.md).
Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

**#59: branch base.** plan/v0.12.0 starts from main `9edbc03` (v0.11.0 plus post-tag docs) with four commits that came
before the plan (ef865e7):

- `d613662` / `440a067`: license diagnostic part a on SEEN data (scripts/diag_license_014.py,
  results/diag-014/LICENSE_DIAG_SEEN.json, docs/research/BRUTE_DIAG_LICENSE_014.md) and its ledger receipt.
- `59c3560` / `6e8098a`: part b (scripts/diag_license_014b.py, results/diag-014/LICENSE_DIAG_SEEN_B.json,
  docs/research/BRUTE_DIAG_LICENSE_014B.md) and its ledger receipt.

They add analysis code only, no learner code. Exact: `git merge-base --is-ancestor 9edbc03 ef865e7`. The plan's
branch_base field cites them.

**#60: certify/2 reason when there is no library.** api_definition says "the reason is the FIRST failing condition in
DLF order" and lists eight reasons, including 'no-library'. Read literally, once the FB region check fails the first
failing condition is always the region, so the library reasons could never be reported. The implementation (written
before any v0.12.0 run and before the source freeze) reports this instead:

- 'burn-in', then 'sp8-support-unavailable';
- with no library: the failing region condition ('region-not-singleton' or 'outside-sp8-support'), because without a
  library DLF is RG4;
- with a library: the failing license condition ('library-refuted', 'library-split', 'outside-sp8-support',
  'bounded-region-not-singleton').

'no-library' stays in REASONS but is never returned. This changes only the reason text. It does not change status,
answer or rule, so no gate input changes (Exact: tests/test_api_certify2_0120 (ii) and (iii)).

**Disclosure (not a deviation): frozen learner configuration.** The frozen experiments.brute_study_012 /
brute_study_013 functions read study-013 plan keys (plan_view, in_family_2x2, actions_per_case_2x2). Study 014 hands
them the BRUTE_PLAN_013 dict through experiments.brute_common_014.learner_plan, which asserts tau6, tau7, burn_in,
actions per case and mask rates equal plan 014's. Seeds are checked by scripts/check_seeds_014 before any case runs.

**#61: g11 worker split (rate math, once, before the source freeze).** stop_rule.rate_math allows one budget / worker
change before the freeze if a mandatory stream projects above 70% of its budget. Smoke timings (smoke seeds 7190001
and 7190005 at mask 0.1, 0.35 and 0.6, one process each, plus the sm14b dry run; docs/research/v0.12.0/RATE_MATH_014.md)
give a mean reference audit of about 12.4 s per case (mask 0.6 up to 27.8 s). With the registered 2 workers g11
projects to about 1,910 s (288 x 12.4 / 2 plus the 20-case mutation test), 80% of its 2,400 s budget. The change: g11
runs with **4 workers** (budget unchanged at 2,400 s). g11 starts only after transfer ends, so at most
gti 2 + repro 2 + g11 4 = 8 worker processes run at once, which keeps the registered 8-process limit (the orchestrator
enforces it through MAX_WORKERS). Nothing else changes: no budget, stream, order, seed, threshold or gate. Projection
with 4 workers: about 955 s (40%). Made before the source freeze and before any held-out seed was generated.
