# Brute roadmap: toward geometric reasoning

Labels: **Exact**, **Observed**, **Simulated**, **Inferred**, **Rejected**, **Open**. Updated with every release.

| Stage | Capability | Status |
| --- | --- | --- |
| v0.1.0 | Exact version space (row enumeration) and certification as collapse of the region's projection, with a margin check | Observed (study-002) |
| v0.1.1 | Calibrated open-world forecast after the region is empty (contradiction) | Observed (study-003) |
| v0.2.0 | Active cuts: choose the action that collapses a projection; window rebuild after contradiction | Observed (study-004): coverage +0.115 pooled, 0 in-family errors; G3′ failed (3 stale certificates one step after a drift) |
| v0.3.0 | Change-point-aware certification (no certificate on a region younger than k steps after a surprise or contradiction); exploration that values the untaken branch (D7); measure a compact region representation against enumeration | Open (proposal in NEXT_ITERATION.md) |
| later | Symbolic / lattice / SAT region representations; n≥6; richer action and sensor alphabets; multi-step experiment design; learned family selection | Open |

**Position after v0.2.0 (Inferred).** Brute now closes a loop: it maintains an exact region, chooses the cut
that most collapses the region's projections, certifies only on collapse, and withdraws certificates when the region
empties. That is the skeleton of a geometric reasoner (*Observed* on a toy domain). What is missing for anything general:
(1) time — the region assumes a stationary world, and the only failures are stale certificates after a change (D8);
(2) depth — the experiment is one step and greedy (D7); (3) representation — enumeration caps the class at n≤5 (D10);
(4) breadth — one toy domain, no language grounding beyond templates.

**Earlier position (Inferred).** Brute is a verified-abstention reasoner on a toy domain. Its geometric core is exact region
maintenance plus projection tests. The gap to general geometric reasoning is mostly representational: regions are
enumerated rows, not compact shapes, and model-class growth is manual. It is not general intelligence.
