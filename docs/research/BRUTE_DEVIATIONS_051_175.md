# Deviation #175 (study-051, v0.48.0): pre-run declarations

Written before the source freeze (2026-10-31, box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_051 (commit e510673) that the
plan leaves open. It changes no threshold, seed, cap, eps, eps_bar or delta, and no gate. Labels: Exact, Observed, Simulated,
Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_051 (ledger 3d12d84, plan e510673), build_authorization_051 (ledger 2dc85ec, 12:43 EDT,
   cites James's STANDING GO t133s553, ledger 76b30d5), seedcheck_051 (ledger 303ac1d; SEEDCHECK_051 at 2aa2832: 30 cases 12/6/12,
   354 prior ranges, 0 overlaps, 17 negative controls refused), then prefreeze_smoke_051, source_freeze_051, run_start_051,
   run_end_051, recount_051, reference_051, api_checks_051, tests_051, gates_051. Lean process. The resume clause is not approved: an
   interrupted run is never relaunched; a partial block is sealed as such.
2. **Caps are the plan's (Exact).** scale20: C20 = 12000, B20 = 2000000, family_bound 20 (certify/16s). Controls and part c: C =
   50000, B12 = 3000000, family_bound 12. noise12: C = 50000, B12N = 1500000 (certify/16n, eps 0.05, eps_bar 0.10, delta 0.001, the
   anytime k rule of #173 item 4, unchanged). max_chunks None. Guards 600 s per case and 30 s per chunk, host safety only; any firing
   fails GDET51 / GQB25 and is never a label. Phase A: the 24 scale20 jobs on 4 workers; phase B: controls, part c and noise12 on 8
   workers after phase A ends.
3. **The BFS reading (Exact, from code; the plan's wording is not implementable literally).** The plan says certify/16s numbers the
   states "in BFS order of the hypothesis automaton". certify/16e's first-visit clauses already number every trace-visited state by
   first-visit time, and a BFS order over ALL states generally contradicts that numbering (a BFS order can put an unvisited state
   before a visited one), so adding both would be UNSOUND (Rejected: it could turn a SAT instance UNSAT). brute/api/certify16s.py
   (commit 39615bd) applies the BFS-canonical part to the unvisited block only: vis[q] activation literals (a fresh literal per
   trace length, passed as an assumption), prefix-OR minimum-visited-parent variables f[j][r], and for every adjacent unvisited pair
   (j, j+1): emission(j) <= emission(j+1), and on equal emission minparent(j) <= minparent(j+1). Encoding id
   'a16d+unvisited_bfs_v1'.
   Soundness (Exact by argument): permuting unvisited states leaves every trace-row, first-visit, apartness, transition and reading
   clause satisfied and carries each state's (emission, minimum visited parent) key with it; sorting the unvisited block by that key
   is such a permutation, so every model of the certify/16e instance has a renamed copy satisfying the new clauses. Verdicts are
   unchanged; models may differ by renaming. Whether the clauses lower the conflicts needed is Open (GS20_rate51).
4. **canon16s and GDET51 (Exact).** canon16s = the canon16e fields plus 'encoding' and 'sym_clauses', wall fields excluded. GDET51
   compares canon16s(API16S) with canon16s(API16S_b) on the 12 scale20 cases, canon16e on the 6 controls, canon16n on the first N12B
   noise12 cases; byte-equal, plus 0 guard firings.
5. **GCOMPAT16S (Exact).** Part c (API16S_c, certify/16s at family_bound 12 on the 6 control traces) is compared with the part-k
   API16E record of the same seed: labels equal and, when the label is ID or IDF, the same machine after BFS-canonical renaming from
   state 0 (recount_051.bfs_form over the record's 'model' [transitions, emissions], initial state 0). Machines are compared in
   canonical form, not byte-equal, because #175 item 3 allows a renamed model. Counted on the first NCOMPAT controls.
6. **Reference scope (Exact).** run_reference_051 audits every decided record of the S, E and N arms against the clean hidden truth
   at its family bound: the 12-state records in one pool on 8 workers with budget_12_s = 2400, then each decided scale20 record one
   at a time with budget_20_s_per_record = 1800, outside G_RT; one 20-mutation test. Part c (API16S_c) is outside GS_ref; it is
   recounted and compat-checked by item 5.
7. **GFID51 counts 30 records (Exact).** api_checks_051 replays 12 API16S records (4 workers; encoding and sym_clauses must also
   match), 6 API16E and 12 API16N (8 workers): 12 + 6 + 12 = 30. API16S_c and the _b passes are not replayed (the _b passes are
   covered by GDET51, part c by GCOMPAT16S).
8. **GHOST51 (Exact).** Frozen module shas: certify16, 16d (and 14) from FREEZE_047, 16e from FREEZE_049, 16n from FREEZE_050; the
   16e and 16n import closures must equal those recorded in results/study-050/API_CHECKS_050.json; new modules are the certify16s
   closure minus the certify16e closure; a network-free subprocess runs Certifier16S on smoke seed 11890003.
9. **Runner freeze check (Exact).** experiments/brute_study_051.run() refuses a main run unless the freeze's (n_noise12_b,
   n_compat) equal the runner's (N12B, NCOMPAT), so the cut decision cannot drift after the freeze.
10. **Cut projection (Inferred; plan runtime_estimate).** scripts/prefreeze_smoke_051.py: every job's worst case is min(600 s, B /
    r_min + 10 s); r_min(scale20) = min(slowest smoke API16S / API16S_b rate over records with case wall >= 1 s, 4503/s);
    r_min(12 states) = 30256/s as declared (the plan substitutes only the certify/16s rate; the smoke's 12-state rate is reported,
    not used). Total = LPT(phase A, 4 workers) + LPT(phase B, 8 workers). The first of (N12B, NCOMPAT) = (12, 6), (6, 6), (6, 3)
    with total <= 3600 s is required; never scale20, never after the freeze.
11. **Cut decision (Observed; filled from the smoke before the freeze).** CUT_DECISION_PLACEHOLDER
12. **Claim scope (Inferred).** Every ID / IDF is conditional on the declared N (20 for scale20, 12 otherwise) and, for noise12, on
    the iid-flip model with eps <= eps_bar. Without the size bound no finite trace suffices: a larger machine can copy the true
    machine on every visited state and differ only on states the trace never reached.
