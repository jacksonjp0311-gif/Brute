# Deviation #185 (study-056, v0.53.0): pre-run declarations

Written before the source freeze (box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_056 (plan/v0.53.0, commit 16e0793, ledger
preregistration_056 002a69a; no amendment) that the plan leaves open, records the pre-run defects found and fixed, and records the
pre-run finding that certify/20l spends its action budget K early. It changes no threshold, seed, cap (K, B, C), worker count, order
or gate. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_056 (16e0793, ledger 002a69a, 21:29 EDT), build_authorization_056 (ledger 6fd32fb, James's
   STANDING GO t133s553), certify/20l (009cb62), seedcheck_056 (item 2), study tooling (d582099, 7e9035a, 4547b5b, 508bd52), the pre-run
   fixes of items 12-16, four prefreeze smoke attempts (item 17), then source_freeze_056, run_start_056, run_end_056, recount_056,
   reference_056, api_checks_056, tests_056, gates_056, #186. Lean process; the main run goes once with nohup and is never relaunched.
2. **Seed check (Exact; Observed).** check_seeds_056 (ac4c006) was committed and run on the tracked tree at ac4c006, after
   build authorization and certify/20l and BEFORE any study tooling (the 055 lesson): PASS (SEEDCHECK_056.json 4551d6f, ledger
   e9ee97c; 2756 files, 190 .gz, 0 tokens in the 056 ranges, 12 cases). Rule L (efad643, study-own tooling may name its own smoke
   range) is carried over unchanged.
3. **Arms and caps (Exact, from code).** scale20t: 6 worlds 12330001-12330006, API20L and API20L_b (certify/20l, two passes) and
   API16E20 (certify/16e) at bound 20, C = 50000, B = 2000000. compat20t: 6 eps-0 controls 12350001-12350006, API20L against API16E
   at bound 16, C = 50000, B = 3000000. K = 128 (certify/16e's K, plan design.api "same ... K as certify/16e"). max_chunks None;
   hook None (conflict-only stop); wall_guard_case_s 900 s is a hard kill (fails GDET56), never a label. Two concurrent 4-worker pools.
   HYP_ROUNDS = 3 is written into the freeze with n_scale20t and n_compat20t.
4. **Homing reading (Exact rule, fixed before data).** The plan's "homing word h ... the shortest word that the learner's table
   distinguishes after each step" is read for a no-reset walk as an adaptive homing sequence: from the current position T, (1) if T
   matches two or more basis rows, the witness word of the first two (basis order); (2) else, T identified with row i and a cell (i, a)
   missing: [a] (lowest a); (3) else the shortest-lex path in H's known cells from i to the nearest row with a missing cell, then that
   action; (4) else none. Rows are trace positions (access by walk), columns are the separating witness words used so far.
5. **Identification and propagation (Exact).** Candidate rows = rows not apart from the position on the trace (scalesearch15
   apartness); then HYP_ROUNDS = 3 passes of: rows whose partial H reproduces the next 2 x rows readings, and forward propagation from
   an identified predecessor along a known, conflict-free cell. One candidate left = identified. Identification only chooses actions
   and H; it is never trusted.
6. **Hypothesis defaults (Exact).** H state i = basis row i; emission = lowest code of the row's reading; delta(i, a) from the first
   identified occurrence in trace order; a missing cell defaults to a self-loop. A filling word that does not fit in K goes straight
   to the equivalence check (the table is then not closed; item 17).
7. **AMB when rows exceed N (Exact).** More than N pairwise-apart rows: stop AMB with the table published (no claim).
8. **K accounting (Exact).** Fill words and counterexample words both spend K (one walk, no reset). A counterexample longer than the
   K left stops K_spent, audited as the AMB it ended on (as certify/16e).
9. **Equivalence check (Exact).** certify/16e's rival query (scalesearch14.search14, Pool16E, chunked conflict-counted solve) at
   sizes n_min..N with M1 = H (or the repaired M1, item 13), 'future' then 'start'; labels exactly as certify/16e (LABEL_OF_STOP).
10. **GHOST56 no-network loop (Exact).** Any completed certify/20l loop (ID, IDF, IDU or AMB) with 0 socket attempts passes; the plan
    does not require a decision (the 055 lesson, #183 item 7).
11. **Smoke allocation (Exact).** Smoke seeds 12370001-02 scale20t (three arms), 12370003-04 compat20t (two arms), 12370005-06
    declared and unused; outside results/study-056; never gated; never sets K, B, C, the homing rule or any order.
12. **Fix A, recount contract (real defect; before any smoke; 72dc0b3).** A fresh API20L record (DEV seed 10051001, compat) failed
    the frozen recount_047 contract: (a) the round M1 was H, which can contradict the trace (BAD_AMB_K_spent / M1_inconsistent,
    model_inconsistent); (b) fill words count in 'used' but are not round words (used_vs_words). Fix (a): certify20l._check tests H
    against the trace (scalesearch.simulate); if inconsistent, M1 = scalesearch14.least14 (least trace-consistent machine at sizes
    len(basis)..N, conflicts counted in the same budget; 'unknown' or 'none' -> stop unknown), M1_source 'sat_repair' in the round
    and table log, else 'table'. The plan's "no least-machine SAT search" is thereby relaxed for an inconsistent H only; soundness is
    unchanged (labels still come only from UNSAT rival proofs). Fix (b): recount_056 (not frozen) accepts, for API20L / API20L_b
    only, used = executed round words + table fill_steps (reported as fill_steps, used_ok_056); fill words are replayed and checked
    walked by GTABLE56. table_audit_056 checks a repaired M1 (consistent with the prefix, size len(basis)..N, s1 its state) and checks
    the counterexample against it. brute_study_056 copies M1_source into the frozen arm_active rounds.
13. **Fix B, n_min (real defect; found by prefreeze attempt 2's GS_ref; d4c66d7).** The record's n_min was len(basis), a lower bound;
    the frozen GS_ref audit (run_reference_047) recomputes n_min as the least consistent size and found 4 mismatches (e.g. 14 vs 16).
    Now n_min = least14's size after a repair (least14 searches up from len(basis), so its size is the least) and len(basis) when H
    itself is consistent (H has len(basis) states, the lower bound, so it is exact); the rival searches start at n_min. Plan text
    checked: design.solver names the table rows as the size lower bound; the field n_min keeps its frozen meaning (least size).
14. **Fix C, smoke progress log (defect in tooling; ffb541a).** The runner's progress line took len() of the integer counterexample
    count and crashed (attempt 1). Records unchanged.
15. **Fix D, api_checks_056 CLOSURE_055 (defect in tooling; 77fabe7).** The ghost check referred to an undefined CLOSURE_055 and
    crashed the first scoring of attempt 2 (log kept as PREFREEZE_SMOKE_056_ATTEMPT2_SCORING_CRASH.log). Now results/study-055/
    API_CHECKS_055.json.
16. **Fix E, prefreeze PASS formula (real defect; the one fix allowed after attempt 3; aa266bb).** prefreeze_smoke_056's PASS
    required `all(smoke compat pairs equal)`. Plan text checked: smoke_range reads "pre-freeze smoke and projection only; never gated",
    and the receipt's own note says "gate outcomes on smoke are recorded, not required"; requiring GCOMPAT20L56's outcome on the smoke
    gates the smoke on a method outcome. The clause (inherited from 052-055, where smoke compat happened to be equal) now checks that
    compat was computed under compat_rule_056 with both labels present; the count is recorded as smoke_compat_equal. Attempt 3 is
    not re-scored; it stays PASS false. Stated plainly: Fix E loosens a PASS clause and was made AFTER attempt 3 failed on that
    clause. It is acceptable only because plan 056 says the smoke is never gated: it hides nothing gated (GCOMPAT20L56 is scored on
    the 6 main controls only, under the unchanged rule and threshold 6/6). The smoke compat results, AMB vs ID (12370003) and AMB vs
    IDF (12370004), are an early warning (Inferred) that GCOMPAT20L56 will likely fail in main.
17. **Prefreeze smoke attempts (Exact; every receipt published, every attempt ledgered as prefreeze_smoke_056_attemptK).**
    attempt 1: runner crash (8b31cfa, ledger 54ca8fb; Fix C). attempt 2 (smoke2, scored as-is once after Fix D): PASS false,
    reference_rc 1, GS_ref 4 n_min mismatches (d4670d8, ledger 5935618; Fix B). attempt 3 (smoke3, scored as-is once): PASS false;
    every clause holds (recount_rc 0, reference_rc 0, GS_ref 0 mismatches, mutations 20/20, api_checks PASS, fidelity 6/6 + 4/4 exact,
    determinism 2/2, hook arms 0, release_ok, verifier chain passed) except smoke compat equality, 0/2 (12370003 API20L AMB vs API16E
    ID; 12370004 AMB vs IDF) (d7bafe2, ledger 59bc103; Fix E). attempt 4 (smoke4, one smoke after Fix E, scored as-is once): PASS true, every clause
    holds; smoke compat 0/2 equal (same labels as attempt 3), recorded (f6b2801, ledger af3e92a; also ledgered as
    prefreeze_smoke_056, d74de10, the receipt this freeze relies on). This was the last attempt allowed.
18. **Finding: API20L spends K before the table closes (Observed on smoke3; not a defect; K unchanged).** fill_steps of K = 128:
    scale20t 12370001 126 (both passes; 16 rows, 2 columns, 1 hypothesis, 0 counterexamples, AMB/K_spent), 12370002 128 (13 rows,
    3 columns, 1 hypothesis, then the check spent B: IDU/unknown, 2004056 conflicts); compat20t 12370003 128 (14 rows; AMB/K_spent),
    12370004 93 (11 rows, 10 counterexamples, 11 hypotheses; AMB/K_spent). Every first hypothesis was trace-inconsistent, so M1 came
    from the SAT repair (item 12). API16E decided both compat controls (ID, IDF) with the same K. Reading (Inferred): with one walk
    and no reset, filling a table for 14-20 states costs about K by itself, so certify/20l reaches its first equivalence check with
    almost no K left for counterexamples. The plan text is consistent with this (K is certify/16e's K by design.api; filling and
    counterexample words both spend it, item 8), so it is reported as a finding, not fixed. K, B, C, seeds, arms and orders are not
    changed to avoid it. Expected consequence (Inferred, declared pre-run): GS20L_gain56 and GCOMPAT20L56 are likely to fail; per
    next_if_fail, "the table is what runs out" is the likely branch.
19. **Runtime cut (Exact).** Smoke projection at the slowest rate r_min 4503/s: worst 2270.7 s (N20L = 6, NC20L = 6) <= 3300 s, so no
    cut: N20L = NC20L = 6, 30 jobs.
20. **compat_rule_056 (Exact).** compat_rule_056 was introduced after the 055 compat failure (#184 item 5) and is not retroactive:
    it is applied only to GCOMPAT20L56 and to the read-only recheck_12270005; GATES_055 and every 055 file are unchanged.
21. **Numbering (Exact).** This file is the pre-run deviation (the instructions of 22:20 EDT and 00:02 / 00:53 EDT call it "#186"); make_freeze_056 freezes it
    under the number 185. The post-run deviation is #186 and repeats item 18.
