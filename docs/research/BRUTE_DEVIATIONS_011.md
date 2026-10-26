# Study-011 (v0.9.0) deviations and disclosures

Numbering continues from study-010 (#39). Each item says what differs from the frozen plan (`experiments/BRUTE_PLAN_011.json`) or from the owner order, or what the plan left open and how it was decided before data. Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

**#40: branch base.** The owner order says to branch plan/v0.9.0 from main 70cb351. The branch was cut from origin/main f79c925, the fast-forward child of 70cb351 that adds only `HANDOFF.md` and `MANIFEST.sha256` (no code, no result). `git merge-base --is-ancestor 70cb351 f79c925` holds (Exact). The seen-data lag diagnostic (a5ef9c8, 0c3f348) was committed before the plan by owner order; it is analysis code, not v0.9.0 learner code (Exact).
