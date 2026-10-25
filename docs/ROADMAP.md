# Brute roadmap: toward geometric reasoning

Labels: **Exact**, **Observed**, **Simulated**, **Inferred**, **Rejected**, **Open**. Updated with every release.

| Stage | Capability | Status |
| --- | --- | --- |
| v0.1.0 | Exact version space (row enumeration) and certification as collapse of the region's projection, with a margin check | Observed (study-002) |
| v0.1.1 | Calibrated open-world forecast after the region is empty (contradiction) | Observed (study-003) |
| v0.2.0 | Active cuts: choose the action that collapses a projection; window rebuild after contradiction | Observed (study-004): coverage +0.115 pooled, 0 in-family errors; G3′ failed (3 stale certificates one step after a drift) |
| v0.3.0 | Fibre-robust certification (Y1k: a certificate must be constant on the fibre of the region over the latest observation) and the LU-R lookahead scored with it | Observed (study-005): G3′ passes (0 stale certificates on the gated drift4 block, 0 in-family errors); coverage −0.098 vs v0.2.0 (G6b failed, as pre-registered); G5 failed (τ alarm on 5/72 ood4 cases, unchanged rule); D7=D8 test OPEN |
| v0.4.0 | Exact H-representation of the version space (`ConstraintRegion`, CNF + symmetry breaking) verified decision-identical to enumeration; recalibrated, resumable alarm; two-step lookahead / two-step fibre candidates; perm4 family; powered D7/D8 | Observed (study-006): GR1/GR1b 0 mismatches in 1.25 M items; clauses ~n^1.6 vs rows ~n^8.5 (few points; SAT time noisy); 15/16 gates; G5 passes; G6b′ fails (−0.104, pre-registered); D2/F2 fail (F2 unsound); D7/D8 OPEN (R 0.63); representation not yet the learner's engine |
| v0.5.0 | The learner on the constraint region (n≤6 margin, n≤5 family); sound multi-step fibre; effective resume; one stochastic or larger-alphabet family | Open (proposal in NEXT_ITERATION.md) |
| later | n≥6 and richer action and sensor alphabets on the compact representation; stochastic worlds with credal regions; deeper experiment design; learned family selection; grounding beyond templates | Open |

**Position after v0.4.0 (Inferred).** Of the four gaps, (3) representation moved most: the region now has an exact
constraint description whose size grows polynomially in the state bound (*Observed* on few points), so the object the
reasoner manipulates is a geometric set of cuts rather than a list of machines — but the learner still runs on the list,
so nothing Brute decides has changed yet (*Exact*). (2) depth — tested and negative: one more lookahead step costs
coverage, and a two-step fibre breaks soundness (*Observed*). (1) time — the alarm no longer misfires on the new family,
and resume is safe but idle. (4) breadth — one new family (perm4) inside the same toy alphabet. v0.5.0 should put the
learner on the representation and push past n ≤ 4. It is not general intelligence.

**Position after v0.3.0 (Inferred).** The loop now has a notion of time that is geometric rather than a timer:
a certificate must hold on the whole fibre of the region over what was just seen, so a silent change cannot leave a
stale certificate standing on the gated block (*Observed*). Two of the four gaps named after v0.2.0 moved: (1) time —
partly closed, at a large coverage price (D11, D12) and with a residue after jumps into unexplored states; (2) depth —
unchanged, and study-005 suggests depth is now the lever for coverage, not more checking (D13). (3) representation —
unchanged, and now the binding constraint: a multi-step fibre or a two-step lookahead does not fit enumeration (D10).
(4) breadth — unchanged. v0.4.0 targets (1)–(3) together and takes the first step on (4). It is not general intelligence.

**Position after v0.2.0 (Inferred).** Brute now closes a loop: it maintains an exact region, chooses the cut
that most collapses the region's projections, certifies only on collapse, and withdraws certificates when the region
empties. That is the skeleton of a geometric reasoner (*Observed* on a toy domain). What is missing for anything general:
(1) time — the region assumes a stationary world, and the only failures are stale certificates after a change (D8);
(2) depth — the experiment is one step and greedy (D7); (3) representation — enumeration caps the class at n≤5 (D10);
(4) breadth — one toy domain, no language grounding beyond templates.

**Earlier position (Inferred).** Brute is a verified-abstention reasoner on a toy domain. Its geometric core is exact region
maintenance plus projection tests. The gap to general geometric reasoning is mostly representational: regions are
enumerated rows, not compact shapes, and model-class growth is manual. It is not general intelligence.
