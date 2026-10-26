# Study-013 (v0.11.0) deviations and disclosures

Numbering continues project-wide. Study-012 ended at #51 (docs/research/BRUTE_DEVIATIONS_012.md).
Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

**#52: branch base.** The owner asked for plan/v0.11.0 to come from main `b935fff`. The branch is `b935fff` plus two
commits that came before the plan:

- `e0aa431`: the exploratory applicability diagnostic on SEEN data (scripts/diag_applicability_013.py,
  results/diag-013/APPLICABILITY_DIAG_SEEN.json, docs/research/BRUTE_DIAG_APPLICABILITY_013.md). It calibrates one
  constant, M_app (frozen at 6 = seen boundary 4 + margin 2).
- `373e8d0`: its ledger receipts.

Neither commit adds learner code. Exact: `git merge-base --is-ancestor b935fff <plan commit>`.

**Disclosure (not a deviation): known test failures declared in advance.** K_080 and K_090 (three tests each, the
superseded-release version / verify tests) are part of the frozen GTI criterion (Observed failing on the v0.10.0 tree
at 10:10 EDT before the plan). After the 0.11.0 bump, test_release_0100 is expected to fail the same way
(R_K0100_after_release, not gated).
