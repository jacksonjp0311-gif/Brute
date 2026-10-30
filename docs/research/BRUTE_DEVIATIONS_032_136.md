# Deviation #136 (study-032, v0.29.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_032. Each item records
a choice the plan left open, a reading of a criterion, or a process slip, made before any main case was run. Labels:
Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4).

1. **Definitions (Exact).** As in scripts/make_gates_032.py. U(arm, case) = UNKNOWN queries / planned queries (an unrun
   query counts UNKNOWN). U_inf = U, except that a case whose arm ends with status grammar_contradicted counts every
   planned query UNKNOWN. X_inf = cases with U_inf count 0. GRP7 b/c are paired over the 12 noisy_scale12 seeds with the
   seed-bootstrap 95% CI (Random(32), 10000 resamples); GRP7 d is X_inf(S7, noisy_scale12) >= 3 of 12.
2. **Flip budget unit (Exact; reading).** t in B(t) = ceil(0.05 t + 2 sqrt(0.05 t)) counts sensor readings (2 bits per
   reading, each flipped independently in experiments.worlds_026.flips), so B at the end of a 176-step trace (177
   readings, 354 bits) is 27. S7 uses B(sensor readings observed so far) at every step.
3. **within_B (Exact; reading).** A noisy case is within B iff its realised prefix flips are <= B(sensor readings so far)
   at every reading (the condition under which S7 is sound against the true machine at every step).
4. **F_truth (Exact; reading).** F_truth(arm, case) = exact supports that exclude the true next code (truth_missing).
   This is a superset of the singleton-certificate F (rgn_decide) and is what GRP7 a and G10 gate; F is also recounted.
5. **Budget (Exact; reading).** The plan's "55 s per step ... as in studies 028-031" is read as 55 s per arm per case
   (that is how 028-031 ran; per step would be about 2.7 hours per arm). Same 55 s at eps 0 and 0.05; 10 s per-query
   hard cap from S5. Runtime estimate 48 x 4 x 55 / 8 = about 1320 s (G_RT cap 1800 s).
6. **GNR7 mismatch (Exact; reading).** A mismatch is a query both S7 and S5 answered exactly at eps 0 where S5's support
   is not a subset of S7's (S7 may be weaker, never contradicting). Equal supports are counted descriptively. The
   mismatch count is over every eps-0 case (clean and control); the U contrast is over the 6 clean scale12 seeds.
7. **S7_contra (Exact; reading).** "At each step, a symmetry-on whole-trace consistency check": after each observe, if
   the witness pool is empty, a symmetry-on brute.scalesearch5._Region5 is solved with no query; UNSAT sets
   grammar_contradicted. A nonempty pool already proves consistency, so the check is skipped. Its solves count in the
   arm's counters (contra_checks, contra_unknown).
8. **Worlds (Exact).** noisy_scaleN uses the frozen experiments.worlds_026 scaleN world at the same seed; the noise and
   action streams are those of worlds_026 at eps 0.05; clean regression cases are the same seeds at eps 0.
9. **Smoke (Exact).** The smoke block is 6 cases on 9890001-9890006 (16/0.05, 16/0, 12/0.05, 12/0, 8/0.05, control).
   tests/test_scripts_032 also runs 9890029 and 9890030 (smoke range) with a reduced per-arm budget (test only).
10. **GS_ref reference (Exact).** experiments/v0290_reference.py is a SAT-free DFS (first-visit state numbering, any of
    4 codes per new state, flips = popcount(code XOR reading), pruned above B) with a 20000-node budget per (query,
    code), 110 s per case, audited on every noisy_scale8 case. Every exact S7 answer is checked code by code (a code
    proved possible that S7 excludes, or proved impossible that S7 keeps, is a mismatch), so partially decided queries
    are checked too. Mutations: 20 seeded single-code flips of decided supports.
11. **G_PROC (Exact).** PROC_ORDER = preregistration_032, build_authorization_032, seedcheck_032, source_freeze_032,
    run_start_032 (no scratch diagnosis step in this study).
12. **Process slips (Exact; disclosed).** (a) Before seedcheck_032 was ledgered (25ce5a7, 16:01:58), a scratch test ran
    S7 and S5 for 40 steps on smoke seed 9890001 (scale8 world, eps 0 and 0.05; it showed 19 realised flips); smoke seeds
    are allowed but the run preceded the seedcheck. (b) Before 25ce5a7, flip_profile(9820001, 0.05) was called on a
    target seed: noise draws only, no arm run; it gave realised 15, B_end 27, within_B True. (c) At 16:04 (after the
    seedcheck, before the freeze) W.trajectory(9810001, scale8, 0.05) was called on a target seed to check the readings
    format: no arm run. No result of (a)-(c) was used to change any design choice or threshold.
13. **Smoke observations (Observed; no tuning).** On the 6 smoke cases (230 s, 8 workers): recount PASS; S5_in_S7
    mismatches 0 on every case; F_truth(S7) 0; S7 grammar_contradicted 0; S7 U was above S5 U on 5 of 6 cases (for
    example clean scale16 226 vs 1, control 61 vs 0 of 352, noisy scale12 259 vs 240). The reference on smoke 9890005
    (noisy scale8): 259 exact S7 answers, 183 decided, 0 mismatches, mutations 20/20, but every decided S7 support was
    all 4 codes (decided_impossible_codes 0): with B up to 27 the S7 answers are sound but mostly vacuous (Inferred).
    So G10 and GNR7 are at risk and GRP7 b is unlikely (Inferred). The S7 design is the plan's and was not changed.
14. **Box clock (Observed).** At 15:55 and again at 16:02:58 and 16:07:50 the box clock agreed with process elapsed time
    (/proc/uptime deltas 470.9 s and 291.9 s) and at 16:02:58 with the GitHub API Date header (20:02:58 GMT). No stall
    seen before the freeze.
