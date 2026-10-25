# Brute discoveries log

Each entry gives the exact math, the data and command that reproduce it, and an evidence label: **Exact**,
**Observed**, **Simulated**, **Inferred**, **Rejected** or **Open**. "Design data" means study-003 seeds (1230001..1290024),
replayed post hoc. The probes live in `docs/research/v0.2.0/design_probe/` and their outputs in `outputs/`.

Common notation:

- `R_k(t)` is the set of n≤k Moore-machine prefixes (rows) consistent with the evidence up to step t.
- `S_k(a) = ∪_{r∈R_k} codes_r(a)` is the predicted support for action a.
- CERTIFIED(b) means:
  - `S_4(b) = {x}` and `S_5(b) = {x}`;
  - not every row of `R_4` uses all 4 states;
  - no alarm and no contradiction.
- Dual coverage is `(1/2T) Σ_t Σ_{b∈{0,1}} 1[CERTIFIED_t(b)]` over post-burn-in steps.

## D1: Targeted collapse beats volume bisection

- **Math.**
  - The entropy policy picks `argmax_a H(w_a)`, where `w_a(c) ∝ Σ_{r∈R} 1[c∈codes_r(a)]/|codes_r(a)|`, summed over the
    family and the margin.
  - The lookahead (LU) policy picks `argmax_a (1/|S_4(a)|) Σ_{c∈S_4(a)} N(a,c)`, where
    `N(a,c) = #{b : CERTIFIED(b) after R_4,R_5 ← R_4,R_5 ∩ {obs(a)=c}}`.
- **Data (Simulated, design data, 72 cases per family).** Dual coverage, passive → H → LU:
  - cycle3: 0.205 → 0.238 → 0.317;
  - unaliased2: 0.100 → 0.049 → 0.232.

  H lowers dual coverage on unaliased2 and ood4.
- **Reading (Inferred).** Splitting the region evenly does not shrink its projection onto the coordinate being
  queried. Choosing the cut that makes the projection a single point does.
- **Reproduce.**
  - `python docs/research/v0.2.0/design_probe/probe.py cycle3 passive,H`
  - `python docs/research/v0.2.0/design_probe/probe2.py cycle3 F,M,LA,LH 24`
- **White paper:** yes, if study-004 confirms it (G6).

## D2: The known-region attractor (on-policy ≫ dual coverage)

- **Math.** On-policy coverage is `(1/T) Σ_t 1[CERTIFIED_t(a_t)]`. Under LU, `a_t` maximises the certifiability of the
  next step, so it is biased towards actions that are already certifiable.
- **Data (Simulated).** On-policy coverage against dual coverage under LU:
  - cycle3: 0.551 against 0.317;
  - unaliased2: 0.448 against 0.232.

  Under passive the two are about equal (0.197 against 0.197).
- **Reading (Inferred).** The policy exploits the regions it already knows. On-policy coverage overstates learning, so
  only dual coverage is gated.
- **Reproduce:** `python docs/research/v0.2.0/design_probe/probe6.py cycle3 LU`.
- **White paper:** as part of D1.

## D3: Active policies increase drift-jump exposure

- **Data (Simulated).** drift4 taken-action false certificates:
  - passive: 4 (0 at non-drift steps);
  - LU: 13 (1 at a non-drift step: seed 1290002, mask 0.1, step 13, right after the step-12 jump).

  Log-loss rises from 1.1556 to 1.1729.
- **Reading (Inferred).** A policy that steers into certifiable regions has more certificates at risk when the world
  changes without a signal, and it can certify once more on the stale model before the contradiction lands. This is
  the cost of exploitation without a change detector.
- **Reproduce:** `python docs/research/v0.2.0/design_probe/probe6.py drift4 LU`.
- **White paper:** together with D2, as "safe exploitation under non-stationarity".

## D4: Weighting invariance of the one-step lookahead

- **Math.** LP weights `N(a,c)` by published probability `p(c)`; LU weights each `c` by `1/|S_4(a)|`.
- **Data (Simulated).** LP and LU gave identical metrics on all 504 design cases, across 7 families (on, dual, wrong,
  ll, peak rows, agreement), so the decisions were identical.
- **Reading (Inferred).** `argmax_a` is decided mostly by whether some `c` gives `N>0` at all. When both actions score
  above 0, the order rarely flips under reweighting. **Open:** prove or bound this.
- **Reproduce:** `probe5.py <fam> LP` (needs `probe3`) against `probe6.py <fam> LU`.
- **White paper:** no; a footnote.

## D5: Window rebuild helps drift forecasting a little (passive)

- **Data (Simulated).** passive drift4 log-loss goes from 1.1556 to 1.142 when suffix-1 is restricted to the support of
  an n≤4 learner restarted at each contradiction.
- **Reproduce:** the `llw` field of `probe.py drift4 passive`.
- **White paper:** no.

## Study-004 entries (Observed; sealed `results/study-004/SCIENTIFIC.json`, sha `499e29a4…`, 504 held-out cases)

Arms: **A** = active (LU lookahead), **P** = same learner with the fixed passive actions, **C** = frozen v0.1.1 on P's
sequence. Paired analysis: `results/study-004/PAIRED_ANALYSIS.json` (2,000 seed-clustered resamples, seed 20261025).
Reproduce everything: `python scripts/study004_storage.py restore && python scripts/make_paired_004.py --check &&
python scripts/make_gates_004.py --check`.

### D6: Targeted collapse confirmed on held-out seeds (confirms D1)

- **Math.** Gain = mean over (case, post-burn-in step) of `dual_A − dual_P`, with dual as above, at an identical step
  budget (45 steps per case, same seeds and masks).
- **Data (Observed).** Pooled gain **0.115355**, CI95 [0.10409, 0.127123] (design estimate 0.115). Per family, dual
  coverage P → A: cycle3 0.193 → 0.314; switch3 0.162 → 0.293; unstructured3 0.086 → 0.205; unaliased2 0.072 → 0.236
  (3.3×); ood4 0.004 → 0.046 (11×). Every per-family CI excludes 0. Zero false certificates (taken, counterfactual or
  public) in the five in-family families for A, P and C.
- **Reading (Inferred).** Choosing the cut whose answer collapses the region's projection is worth roughly as much
  coverage as v0.1.0 lost to the margin gate on the hard families, with no change to the certification rule. Soundness
  carried over, as predicted by construction.
- **White paper: yes.** The headline result of v0.2.0.

### D7: The attractor is real, and it trades away counterfactual knowledge (confirms D2)

- **Data (Observed).** On-policy coverage is about twice dual coverage under A (cycle3 0.539 against 0.314; unaliased2
  0.461 against 0.236); under P the two are equal (0.197 / 0.193). Certificates for the action *not* taken fall under A:
  cycle3 233 against 495 for P, switch3 184 against 439, unaliased2 29 against 206. In-family log-loss nevertheless
  improves: A − C ranges from −0.012 (unaliased2, CI [−0.019, −0.007]) to −0.042 (switch3, CI [−0.054, −0.030]).
- **Reading (Inferred).** A one-step lookahead keeps returning to actions it can already certify; it learns the taken
  branch well and the other branch less. Dual coverage still rises because the taken branch gains more than the
  other branch loses. **Open:** a multi-step objective that values the untaken branch.
- **White paper:** with D8, as "safe exploitation under non-stationarity".

### D8: Exploitation certifies on a stale model right after an unannounced change (confirms D3; G3′ fails)

- **Data (Observed).** drift4 taken-action false certificates: **A 24 of 221**, P 1 of 16, C 1 of 16 (v0.90 on P's
  trace: 81). Wrong-certificate steps for A: step 12 ×15, **step 13 ×3**, step 23 ×5, step 34 ×1 (drift steps are 12,
  23, 34). The three non-drift errors are seeds 1390010 (mask 0.1), 1390011 (mask 0.1) and 1390016 (mask 0.35), all at
  step 13, one step after the step-12 jump. A also issued 13 certificates at post-jump step 13 (`R2_post_jump`), 3 of them
  wrong. All 24 were later withdrawn (124 retractions: 19 falsified, 70 scope withdrawn, 35 unverifiable masked).
  Selective risk on drift4: A 0.122, P 0.077.
- **Reading (Inferred).** At step 13 the n≤4 region had not yet been emptied by the post-jump evidence (it was not
  contradicted, or Brute would have abstained), so the stale region still projected to a single point. More
  certificates in force means more exposed when the world changes, and that stale projection lasts at least one step. No causal learner can avoid the first error at a silent jump; the
  step-13 errors are the avoidable ones — they need a change-point test that withholds certification while the
  evidence for the current region is younger than a few steps after a surprise, or a margin that includes
  "recently changed" machines.
- **White paper: yes,** with D7.

### D9: The window rebuild beats the frequency table on drift (refines D5)

- **Data (Observed).** drift4 log-loss: A 1.034239, P 1.056963, C (v0.1.1) 1.06755. P − suffix-1 = −0.124285, CI95
  [−0.261194, −0.000571]: the first drift forecast in Brute whose interval excludes the suffix-1 baseline (v0.1.1 in
  study-003: [−0.153, +0.107]). P − C = −0.0106, CI [−0.037, +0.016] — not distinguishable from v0.1.1 on these seeds.
  `window_n4` served 1,006 of A's post-burn-in drift4 steps after 105 window restarts. ood5 does not regress: A 0.665014,
  P = C 0.67712.
- **Reading (Inferred).** Restarting a small exact learner at each contradiction is a cheap, causal change-point model.
  The margin over v0.1.1 is too small to claim; the margin over the frequency table is just clear of 0.
- **White paper:** no; a section of the D8 paper at most.

### D10: Lookahead cost stays inside the row budget

- **Data (Observed).** Peak rows 103,814 of 160,000 (unstructured3, margin and lookahead copy); 0 lookahead budget hits;
  0 budget exhaustions in any arm.
- **Reading (Inferred).** One-step lookahead fits the budget at n≤5; a two-step lookahead or n≤6 would not without a
  new representation (ROADMAP).
- **White paper:** no.
