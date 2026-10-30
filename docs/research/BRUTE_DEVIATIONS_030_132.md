# Deviation #132 (study-030, v0.27.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_030. Each item records
a choice the plan left open, or a reading of a criterion, made before any main seed was run. Only smoke seeds
9690001-9690007 and the scratch-diagnosis replays of study-029 seeds were run. Labels: Exact, Observed, Simulated,
Inferred, Rejected, Open.

1. **Definitions (Exact).** As in scripts/make_gates_030.py: U(arm, case) = UNKNOWN queries / planned queries, where an
   unrun query counts UNKNOWN; X = cases with U_count 0; TP(arm, case) = exact answers / arm wall seconds, with identify
   excluded; GQB5 = S5 max(query_max, observe_max) <= 10.5 s on every main case; GSC5 b = paired mean over the 12 scale12
   eps-0 seeds of U(S5) - U(S1) <= -0.08, with the seed-bootstrap 95% CI upper end < 0 (Random(30), 10000 resamples);
   GSC5 c = X(S5, scale12) >= 5 of 12; GSC5 d = recounted F(S5) = 0 over main and stress; G10 = S5 U 0 and 0 clause-a
   mismatches on every control case; GS_ref = REFERENCE_030 on arm S5 (scale8): 0 mismatches and mutations 20/20.
2. **Overlap concern (Exact).** seedcheck_030 (2f34fcd) passed before any seed was drawn: the plan's seed ranges are
   disjoint from every earlier study and from each other.
3. **Hard cap uses conflict and propagation budgets (Exact; reading of the plan).** The plan says each chunk is bounded
   "by a conflict budget sized so that a chunk cannot pass the remaining cap". Conflicts are not a time unit, and the
   scratch diagnosis (OVERRUN_DIAG_030, Observed: the 029 overruns of 12-15 s did not reproduce standalone, max 8.55 s;
   Inferred: conflict-only chunks overrun under 8-worker contention) showed that a conflict budget alone cannot bound
   wall time. Each S5 chunk therefore carries the S4 conflict chunk and also a propagation budget of
   max(2000, rate x min(0.25 s, 0.5 x time left)); the rate is min(measured, 0.5 old + 0.5 measured), starting at 1e6/s;
   no chunk starts with under 0.05 s left. The S1 per-solve budget CONF is counted in conflicts actually used.
4. **Build check (Exact; reading).** The plan says the region build "checks the wall clock". The frozen S1 RegionK build
   cannot be interrupted, so S5 checks before building: it skips the build (query UNKNOWN, build_skips + 1) when 2 x the
   last measured build rate x size exceeds the time left. Builds measured at <= 0.05 s in the diagnosis.
5. **S5_softcap = study-029 S4_nosym (Exact).** S5 with hard_cap False runs the S4 _solve unchanged with symmetry off.
6. **Stress arms (Exact).** Stress (eps 0.05, 40 s per arm) runs S5, S4 and S1, as the plan's "stress checks F only";
   S5_softcap runs on eps 0 only (55 s per arm).
7. **identify keeps symmetry (Exact).** S5 uses the S4 identify_trace, whose first-visit symmetry gives canonical state
   names; uniqueness needs it. ID is scored as an exact match only.
8. **No API gate and no certify15 (Exact).** The plan lists none; nothing was built for them (lean process).
9. **Workers (Exact).** 8 workers on an 8-core box, as study-029.
10. **Smoke reading (Observed; Inferred forecast).** 7 smoke cases, 8 workers, 230 s. eps 0 U counts (of 528):
    scale12 9690003 S5 150, S5_softcap 151, S4 203, S1 220 (d = -0.13); scale16 9690001 S5 107, S5_softcap 108, S4 183,
    S1 187; scale8 and control 0 for all arms. F(S5) = 0. S5 query maxima within the cap. GSC5 b may PASS; GSC5 c
    (X >= 5 of 12 at scale12) looks unlikely, since the smoke scale12 case has 150 UNKNOWN (Inferred). Noisy stress: S5
    ran out of its 40 s arm budget (U 336-351 on scale12/16, 230 on scale8) where S4 finished (U 0-205): without
    symmetry clauses the noisy search is slower. The build skips (105-339) are fast UNKNOWNs once the arm budget is
    almost spent (Observed in a scratch replay of 9690002: time left 0.03 s at every skip), not a guard fault. Stress is
    gated on F only. Nothing was tuned after this reading.
11. **Runtime risk (Inferred).** Upper bound about 42 x 220 s + 9 x 120 s over 8 workers = 1290 s plus identify, against
    the 1800 s G_RT cap. If the cap is hit, the runner seals the partial block and G_RT fails. There is no relaunch.
12. **Pre-freeze gates test (Observed).** results/diag-030/PREFREEZE_SMOKE_GATES_030.json: make_gates_030 on the sealed
    smoke block and on a main/stress relabel (re-sealed with the runner _write and a stand-in freeze hash): no crash,
    --check reproduces both, data gates INCOMPLETE_INPUT as expected (7 of 51 cases).
13. **Test threshold (Exact).** tests/test_scalesearch5_0270 test_random_small requires >= 150 compared queries (it
    reached 196); this is a sample-size floor only.
14. **Carried nit (Open).** The study-029 ledger notes give test counts 58/57; the true counts were 59/58. The ledger is
    append-only and is not edited.
