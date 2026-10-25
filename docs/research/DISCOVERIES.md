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

(Study-004 adds Observed entries below once it is sealed.)
