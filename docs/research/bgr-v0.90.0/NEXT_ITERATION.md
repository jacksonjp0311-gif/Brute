# BGR v0.91 — From fixed model classes to revisable causal grammars

## Why v0.90 changes the research direction

v0.90 expanded four-state hidden-world support without enumerating 16,777,216 labelled complete machines. It eliminated 78 former conditional false claims on 72 unseen four-state cases, but still issued 140 incorrect conditional claims in five-state and nonstationary stress cases. A separate public certificate gate abstained on every unattested world; this is safer downstream behavior but **not** learned OOD detection. A constructive counterexample shows finite observations cannot prove unbounded model adequacy.

## Required progression

1. **Adaptive grammar lattice:** jointly track several explicitly disjoint causal hypothesis families, including deterministic width-changing Moore machines, stochastic emissions/transitions, delayed effects and nonstationary contingencies. Escalate in a receipt-preserving way after contradictions. Never silently repurpose a failed prior certificate as truth.
2. **Prediction set validity and calibration:** distinguish bounded-support conditional guarantees from probabilistic coverage estimates and out-of-family abstention. Evaluate whether adaptive grammar weighting improves both sharpness and error under distribution shift, not merely abstention rate.
3. **Learned predictive quotient:** infer equivalence classes from partial evidence (not a reference table), explicitly marking tentative versus verified abstraction. Reject alias-induced false state merges under future action interventions.
4. **Transfer:** reuse verified compact predictive motifs from v0.88, but use target-data contradiction gates to prevent negative transfer, measuring improvement versus scratch and incompatible-source priors at equal CPU and observations.
5. **Goals and action selection:** choose safe experiments that distinguish competing grammar families, then achieve unfamiliar goals efficiently using learned predictive-state beliefs. Compare with strong external partially observable baselines and report failed tasks and resource budgets.
6. **External benchmark:** freeze the same learner interface, apply to independent POMDP/ARC-style environments without designer-provided action semantics or hidden family hints, and audit actual transfer.

**Promotion gates:** no unqualified certainty absent a genuinely validated scope, independently replayed learning and abstentions, predictive gains in novel grammars rather than only familiar generators, negative transfer controlled, equal computational-budget comparisons, durable source/evidence/failure receipts, clean independent package acceptance.

**Only BGR. No language interface yet. BitWatts physical energy measurement deferred. AGI remains an unproven long-term objective.**
