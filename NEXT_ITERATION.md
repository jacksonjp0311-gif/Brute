# Brute v0.7.0 → v0.8.0: next iteration (proposal, not pre-registered)

Earlier notes: `docs/research/v0.5.0/NEXT_ITERATION_FROM_v0.4.0.md` and the per-version folders. Labels as in the README.

## Where v0.7.0 leaves things (Observed, study-009)

- **Soundness holds, coverage does not.** G1/G2 0 false certificates for every arm incl. P7, BS7, BSC7. G6b fails a
  fifth time; SC7 is the closest yet (−0.050 vs −0.03 required).
- **Post-drift staleness persists.** S7 4, SC7 5 non-drift false certificates on drift4 (D27).
- **Counts do not plan better than LU-R** (P7 −0.035 coverage, D28).
- **Breadth exactness is cheap with symmetry breaking** (316 s for all 288 cases, 0 mismatches, D26), not without it.
- **Runtime process failed.** The 3 h stop rule fired (late, cause Open); G11 produced no output; GTI never ran.

## Recommendation for v0.8.0 (Inferred; pre-register before any v0.8.0 code)

1. **Run discipline first.** Every stream must checkpoint and support seal-partial (the second implementation did
   not); project each stream's runtime on smoke data and pre-register the projection; GTI must not depend on the
   longest stream; a cap watchdog independent of the orchestrator loop (entry 21).
2. **Anticipatory drift certification.** Certify only if the forecast is constant on the fibre over the region
   extended by "a jump may have happened at the last step" (a one-step jump hull), measured against SC7 as the
   comparator; G3′ and G6b thresholds unchanged.
3. **Planner objective.** Score experiments by expected projection collapse of the next forecast coordinate (counts
   restricted to that coordinate), not by |R_t| reduction.
4. **GX2 factorial.** A small pre-registered incremental × symmetry factorial to attribute the D26 speed-up; make the
   no-symmetry spot check budgeted per case.
5. **G11 again**, as a checkpointed stream, so the v0.7.0 gap in second-implementation evidence is closed.

Deferred and still **Open**: stochastic worlds (credal regions); learned family selection; grounding beyond templates;
independent audit; why the stop rule fired late.
