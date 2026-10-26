# Study-012 (v0.10.0) deviations and disclosures

Numbering continues project-wide. Study-011 ended at #47 (docs/research/BRUTE_DEVIATIONS_011_R1.md).
Evidence labels: Exact / Observed / Simulated / Inferred / Rejected / Open.

**#48: branch base.** The owner asked for plan/v0.10.0 to come from main `13daa32`. The branch is `13daa32` plus
two commits that came before the plan:

- `6494a35`: the exploratory downgrade diagnostic. It contains scripts/diag_downgrade_012.py,
  results/diag-012/DOWNGRADE_DIAG_SEEN.json and docs/research/BRUTE_DIAG_DOWNGRADE_012.md.
- `a52313b`: the ledger receipts for that diagnostic.

Neither commit adds learner code. The order (diagnostic first) is the owner's. Exact:
`git merge-base --is-ancestor 13daa32 <plan commit>`.

**Disclosure (not a deviation): the transfer track was added before the freeze.** The owner's steering
(TRANSFER/ABSTRACTION track, ROADMAP_TO_GI.md) arrived while BRUTE_PLAN_012 was still unfrozen. The track is
therefore part of the frozen plan, so it needed no addendum.

**Disclosure (not a deviation): J10 differs from the NEXT_ITERATION.md proposal.** That proposal was a
surprise-gated hull, and surprise gating was **Rejected** on seen data by the diagnostic. J10 is instead the
exact jump-window *support* rule. This is recorded in plan `pre_freeze_disclosure`.
