# Deviation #183 (study-055, v0.52.0): pre-run declarations

Written before the source freeze (2026-10-31T19:52:19-04:00, box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_055 (plan/v0.52.0, commit
d26472c, ledger preregistration_055 dc2b69c; no amendment, no 055a) that the plan leaves open, and records the pre-run failures.
It changes no threshold, seed, cap, cube depth or gate. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_055 (d26472c, ledger dc2b69c), build_authorization_055 (ledger e8ac749, James's STANDING
   GO t133s553), certify/20c (7fd27d5), seedcheck_055 (three attempts, item 2), prefreeze_smoke_055 (item 9), then
   source_freeze_055, run_start_055, run_end_055, recount_055, reference_055, api_checks_055, tests_055, gates_055, #184. Lean
   process; the main run goes once with nohup and is never relaunched; a partial block is sealed as such.
2. **Seed check: two failures, then a pass at the 054 check point (Exact; Observed).** Attempt 1 (SEEDCHECK_055_ATTEMPT1_FAIL,
   99eec3f, ledger 9bfd929) failed: study-055's own tooling (brute_study_055, api_checks_055, commit 4836a6b) had been committed
   before the check and declares the smoke seeds; 0 target-range tokens, 0 overlaps. Rule L (efad643) then allowed 055 smoke-range
   tokens in study-055 own tooling only. Attempt 2 (SEEDCHECK_055_ATTEMPT2_FAIL, d1baa1f, ledger 018dafe) failed again: the
   attempt-1 ledger note named two smoke seeds and tests/test_scripts_055.py declares the four target range endpoints. Attempt 3
   (scripts/check_seeds_055_at.py, cd5563f) runs check_seeds_055 unchanged on the tracked tree at 7fd27d5 (build authorization +
   certify/20c, the same point at which study-054 ran its check, before any study tooling) in a scratch git worktree: PASS
   (SEEDCHECK_055.json 9e21079, ledger 0584065; 2713 files, 187 .gz decompressed, 0 standalone tokens, 0 pairwise or prior
   overlaps, all 15 negative controls refused). Every token found by attempts 1-2 lies in a study-055 file written after build
   authorization (Exact, from the two reports); none is a prior use. Inferred lesson: run the seed check before committing study
   tooling, as in 054.
3. **Arms and caps (Exact, from code).** scale20t: 6 worlds 12250001-12250006 (first N20C), API20C and API20C_b (certify/20c, two
   passes) and API16E20 (certify/16e) at bound 20, C = 50000, B = 2000000. compat20t: 6 eps-0 controls 12270001-12270006 (first
   NC20C), API20C against API16E at bound 16, C = 50000, B = 3000000. max_chunks None; hook None on every arm (conflict-only stop);
   wall_guard_case_s 900 s is a safety net, a firing is a hard kill (fails GDET55), never a label. Two concurrent 4-worker pools,
   max_tasks_per_child 1.
4. **Cube depth in the freeze (Exact).** cube_depth = 5 (certify20c.CUBE_DEPTH) is written into BRUTE_SOURCE_FREEZE_055 and
   checked by brute_common_055.check_freeze.
5. **canon20c and GDET55 (Exact).** canon20c(r) = dumps({'e': canon16e(r), 'cube': r['cube']}): certify/16e's canonical record plus
   the certify/20c cube summary (cubes, cube_sat, cube_unsat, depth 5 and the per-query cube log). GDET55: canon20c(API20C) ==
   canon20c(API20C_b) and equal conflicts_spent on every scale20t case, 0 hard kills. GFID55 (api_checks_055 fidelity) also compares
   the cube log of every API20C / API20C_b replay; the API16E20 / API16E records are replayed and reported, not gated.
6. **GCUBE55 audit (Exact rule).** REFERENCE_055 carries scripts/cube_audit_055.audit (independent of brute/: no solver, no
   certify20c import) over every API20C / API20C_b record of the block, decided or not: (a) the cube plan of each capped query is
   recomputed from the trace by brute-force restricted-growth colourings of positions 0..min(5, T+1)-1 and word-search apartness
   and must equal the logged live and pruned lists in order; (b) each pruned cube is shown UNSAT by an exhibited distinguishing
   word; (c) the record's chunk conflicts sum to conflicts_spent, and each cube query matches, in order, a logged call with 1 + sum
   cube_chunks chunks and conflict sum first + sum cube_conflicts. GCUBE55 passes iff the audit passes, is bound to the sealed
   results, and covers 2 x N20C + NC20C records. The 'cube' field of certify/16e records is the older Pool15 cube_counts statistic
   (Exact, from code) and is not read by GCUBE55 or GCUBE_stats55.
7. **GHOST55 no-network loop (Exact; Observed).** The no-network child runs a full Certifier20C loop (smoke seed 12290003, scale16,
   bound 16, C 50000, B 3000000) with sockets disabled. The inherited 054 tooling also required the loop to decide (ID or IDF);
   plan GHOST55 requires only no network, the frozen API files and the 16e / 16n / 16s / 20t closures unchanged and the certify20c
   sha bound. On the 055 seed the loop ended IDU at B (0 socket attempts), so api_checks_055 now accepts any completed certify/20c
   loop (ID, IDF or IDU) (15d68f1). Recheck of the ghost part alone: PASS (API_CHECKS_055_PREFREEZE_RECHECK.json, 829e0dd, ledger 8dd7021).
8. **Tests (Exact).** run_tests_0520 gates test_certify20c, test_certify20t, test_scripts_055, test_release_0520, the 16n / 16s /
   16e / 16d / 16 tests and test_scalesearch4_0260; test_scripts_054 and test_release_0510 are reported only.
9. **Prefreeze smoke (Observed).** Smoke (outside results/study-055, /tmp/s55/smoke): 12290001-02 scale20t (three arms),
   12290003-04 compat20t (two arms); 12290005-06 declared and unused. Smoke is never gated and never sets C, B or d. Every scale20t
   record (both seeds, all three arms) spent its 2M budget undecided (IDU); compat20t 12290004 ID on both arms, 12290003 IDU on both
   (compat equal 2/2). certify/20c split 25 capped queries into 1055 cubes, 245 pruned, all independently checked UNSAT. Determinism
   2/2, synthetic self-replay 10/10 exact, gates reproduce, verifier chain passes. Attempt 1 (PREFREEZE_SMOKE_GATES_055.json,
   e4d0278, ledger 6d7b208) is PASS false only through item 7 (api_checks_rc 1); it is kept as-is and not rerun; the ghost part was
   rechecked alone (item 7). H5 (gain) may fail at 20 states: recorded, not acted on.
10. **Cut (Exact rule; Inferred projection).** r_min = min(slowest smoke rate 6632.5/s, declared 4503/s) = 4503/s; worst case per
    job B / r_min + 10 s; LPT per 4-worker pool: scale20t 18 jobs worst 2270.7 s, compat20t 12 jobs worst 2028.7 s; run = 2270.7 s
    <= 3300 s. No cut: N20C = 6, NC20C = 6 (cut_consistent true). Cube bookkeeping did not lower the smoke rate below the declared one.
11. **Ghost closure scope (Exact).** GHOST55 compares the closures of certify16e, certify16n, certify16s and certify20t with
    API_CHECKS_054 and the frozen API sha256 files of every earlier freeze through FREEZE_054.
