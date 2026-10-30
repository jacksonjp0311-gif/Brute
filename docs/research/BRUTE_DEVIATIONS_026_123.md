# Deviation #123 (v0.23.0 build): definitions BRUTE_PLAN_026 left open, fixed before any held-out data

Logged 2026-10-30 EDT, after seedcheck_026 and before the S2 code commit, the freeze and run_start_026. No held-out
seed (9210001-9240006) has been drawn. Timing below comes only from smoke seeds 9290001-9290030 and the scratch probe
seeds 9299001+, which lie outside every range (Observed, informs design only; not used by any gate).

1. **S2 as built (`brute/scalesearch.py`).** One incremental glucose4 solver per arm; clauses only added; queries by
   assumption selectors. BFS-canonical symmetry breaking (Ulyantsev-style parent / minimal-action clauses) over a used-
   state prefix u[0..15]. Implied distinguishability clauses (path rule: positions whose observed futures along a common
   action word conflict cannot share a state). Exact witnesses without a solve: a pool of consistent models simulated
   forward; redirection of a never-exercised transition; and a "suffix chain" machine (copy the last L+1 path states into
   fresh states, enter through the edge used at step T-L-1, send the last copy to a state with the wanted code), accepted
   only after a full simulation on the trace. Deepening (assumption "not u[n]") is used for feasibility only, 1 s per
   level, then the full <= 16 search. A greedy fold of the trace or the last refuted pool model sets solver phases only.
   Every "possible" answer has a concrete machine behind it; every "impossible" answer is an UNSAT proof of the full
   <= 16 region; answers therefore equal RegionK(16) supports wherever both finish (Exact by construction; checked by
   GSC a and GS_ref12). Smoke timing (Observed): fast at 8 states, a hard band near the true state count at 12-16 states.
2. **Worlds (`experiments/worlds_026.py`).** scale_n: rejection draw from Random(seed*130363 + 4026 + n) of uniform
   transitions (k = 3), uniform start and uniform emissions over 4 codes; accept iff strongly connected and minimal
   (experiments.worlds_007.minimal_states == n). control_cycle3: the frozen worlds_013 cycle3 family (k = 2).
3. **Observations and noise.** Fully observed (no masking). Reading t = latent code bits XOR flips; flips from
   Random((seed*1000003 + round(1000 eps)*7919 + 26) mod 2^64), Bernoulli(eps) per bit; eps 0 has no flips. Horizon 176
   actions, readings 0..176. The support at step i (i = 0..175) uses readings 0..i; its truth is the latent code after
   action b from the state at time i, for every action b.
4. **Actions.** SP8 is a 2-action learner; the scale worlds have 3 actions. All arms use the declared uniform random
   policy Random(seed*72031 + 26 + 7*round(1000 eps)) (open-loop, identical across arms). SP8 is not run.
5. **Arms.** S1 = frozen brute.region.RegionSpace(16, k, s=2) (exactly the object bigstate.big() installs; no learner
   needed). S2 = ScaleRegion(16, k). RGB6_on_S2 = brute.scalebetting.ScaleBettingSpace: frozen BettingLRBound(16, k,
   eps_bar 0.02, delta 0.01) unchanged, support region ScaleTolerant(16, readings, actions, T6) rebuilt per step. RGB6 runs
   on every eps > 0 case (main eps 0.02 and stress eps 0.05; clause d "stress included"); it is not run at eps 0.
6. **Budgets.** Per query 10 s wall (S2/ScaleTolerant: chunked conflict budgets, 20000 conflicts per chunk; S1: frozen
   conflict budget, a query whose wall time exceeds 10 s is counted UNKNOWN and its answer discarded). Per case: eps 0:
   S2 55 s then S1 55 s; eps > 0: S2 40 s, S1 40 s, RGB6 35 s, in that order. An arm stops at its deadline (checked
   between calls); its remaining planned queries count as UNKNOWN. Identification (item 8) gets 10 s after S2's arm.
   8 workers, largest worlds first, checkpoint per case, whole run under timeout 1800.
7. **Metrics.** Query = one support(b) at one step: 176*k planned per arm per case. U = UNKNOWN queries / planned
   (not-run counts as UNKNOWN). A case finishes exactly (X) iff its U count is 0. X per (arm, family) over the 24 main
   cases (both eps; 12 for control), Wilson 95% CI; also reported per eps. Certificate: rgn_decide(i+1, burn_in 8,
   support) (singleton after the burn-in) for S1, S2 and RGB6; false iff it differs from the latent code. C_late =
   RGB6 certificates / queries over steps 89..176 (support index 88..175) at eps 0.02.
8. **ID.** ScaleRegion.identify() at step 176: least state count n_min, then a blocking clause on the found
   BFS-canonical model; ID = 1 iff the model is unique at n_min AND equals the BFS canonical form of the true machine
   (same transition table and emissions). Unexercised transitions make it non-unique (ID 0).
9. **Clause a.** For every query where S1 and S2 both have 0 unknowns, the supports are equal (None == None for a
   contradicted region). Queries where either is UNKNOWN or not run are excluded and counted.
10. **G10.** On every control_cycle3 case: S2 and S1 both have U = 0 and clause a holds on all queries.
11. **GS_ref12 (`experiments/v0230_reference.py`).** SAT-free reference for scale8: depth-first search over trace
    positions (first-visit state numbering, <= 16 states, deterministic transitions, emissions checked), one search per
    (query, code), node budget 20000. Decided answers are compared with S2 on every scale8 query; undecided ones are
    counted (coverage published). Pass: 0 mismatches and coverage > 0. Mutation test: 20 seeded mutations of S2 answers on
    decided queries, each must be detected (20/20).
12. **G_recount.** scripts/recount_026.py regenerates every world and trajectory from the seed and recounts false
    certificates from the stored certificates, independently of the runner's counts.
13. **G_RT.** The main run ends within 1800 s with all 93 cases checkpointed; otherwise every data gate fails.
