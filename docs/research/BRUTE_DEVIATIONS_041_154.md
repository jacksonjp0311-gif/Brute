# Deviation #154 (study-041, v0.38.0): build choices fixed before the source freeze

Written before the source freeze (2026-10-31T00:35:15-04:00, box-local EDT) and frozen with it. Nothing here changes a threshold or gate in
BRUTE_PLAN_041. Each item records a choice the plan left open, a reading of a criterion, or an observation made before any
main record was run. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are EDT (UTC-4).

0. **Authorization and seeds (Exact).** preregistration_041 (plan commit 18cc782, ledger 7f96b72, 00:11:14 EDT); seedcheck_041
   PASS (results/diag-041/SEEDCHECK_041.json, commit ada2447, ledger ad779d5, 00:19:12 EDT: perm12 10710001-12, control
   10760001-06, smoke 10780001-06 disjoint from 308 prior ranges, 0 standalone tokens, 16/16 negative controls refused) and
   build_authorization_041 (ledger 55c87e4, 00:19:23 EDT) under James's STANDING GO t133s553 (ledger 76b30d5). Seedcheck
   was ledgered before the build authorization, in the order the user gave.
1. **Hard per-call cap (Exact; user request "keep the per-call cap hard").** Every SAT call of every variant and arm runs in
   one child process per job (experiments/solver_proxy_041.SolverServer). A HardHook gives the solver its soft interrupt at
   the 9.0 s cap and kills the child (SIGKILL) 1.0 s later if the call has not returned. A killed call returns None and is
   read as capped (unknown), exactly like a soft cap. After a kill the proxy lazily starts a new child and replays the clause
   log into it, so later calls see the same CNF. GQB16's bound stays 10.5 s. The kill count is recorded per record.
   Observed on smoke: max call wall 9.29 s, 0 kills.
2. **E1 and E2 (Exact).** As the brute/encaudit16 docstring: E1 = E0 (Inc14, first-visit clauses, A14 lower bound) plus
   apartness clauses for every apart pair, no fixed colours; E2 = Inc15's fixed-colour greedy clique only (no first-visit
   clauses, no pair clauses beyond those the colours imply), start max(A14 bound, |C|). E0 = A14, E3 = A15, E4 = A15_cube.
3. **Instrumented subclasses (Exact).** The variants differ from the frozen classes only by (i) a solver factory (so the hard-kill
   proxy can be supplied) and (ii) per-call logging. tests/test_encaudit16_0380 shows identical clauses and verdicts to the
   frozen active14 / active15 / stop_check14 / stop_check15 on small traces.
4. **Phases (Exact).** At call level the phases are 'least', 'rival' and 'cube'; the 'future' and 'start' rival queries are
   merged as 'rival' at call level, while a record's last_phase still tells them apart. GPH16 (secondary) reads the call-level
   phases.
5. **GAUD_loc reading (Exact).** Cells (10540007,E3), (10540008,E3), (10540008,E4) are the GINC15 losses. A variant
   reproduces the loss if, in at least 2 of the 3 part-b repeats, it is unknown on at least 1 of the 2 traces where E0 decided
   in the same repeat; it matches E0 if, in at least 2 of 3 repeats, it gives E0's stop on both traces. GAUD_loc passes iff
   exactly one of E1 (apartness) / E2 (fixed-colour clique) reproduces the loss and the other matches E0.
6. **GAUD_time reading (Exact).** Per trace in parts a and c (42 traces), r = median(E3 call walls) / median(E0 call walls);
   a trace where either variant made no call is dropped and listed. Statistic mean(r); percentile bootstrap, random.Random(41),
   10000 resamples; pass iff the CI lower bound > 1.
7. **GAUD_sem reading (Exact).** Each replay is compared with the decided E0 partner for the same (part, study, key, seed,
   repeat). Gains (decided where E0 was unknown) and losses are reported, not failures; a failure is a decided verdict that
   contradicts E0's. Fresh records compare A15 and A15_cube against a decided A14.
8. **GPERM16 reading (Exact).** Unknown counts as a failure on fresh perm12 cases where A14 decided.
9. **G_PROC events (Exact).** preregistration, seedcheck, build_authorization, source_freeze, run_start, run_end, recount,
   reference, tests (all _041), in that order.
10. **Smoke (Exact/Observed).** Fresh arms on 10780001-06 (perm12 x4, control x2) plus replays of sealed study-039 scale14
    traces 10520001 and 10520002 under E0-E4 (10 replays, 18 arm records; 102.5 s). Observed: all 18 fresh records ID;
    10520001 unknown under every variant (matches sealed); 10520002 IDF 14 under E0, E1, E3, E4 and unknown under E2 (a loss,
    recorded, not tuned). E4 on 10520001 took 102 s (25 cube calls: 16 UNSAT, 0 SAT).
11. **Replays (Exact).** n_lo = 1; per-replay deadline = start + 240 s; job order part c, b, a, then fresh.
12. **GTI (Exact).** Gated modules: test_encaudit16_0380, test_scripts_041, test_release_0380. Reported only:
    test_scalesearch15_0370 (frozen; expected to fail, as in v0.37.0) and test_scalesearch14_0360.
13. **Runtime projection (Inferred).** results/diag-041/PREFREEZE_SMOKE_GATES_041.json: per-variant mean smoke replay wall
    (E0 10.0, E1 8.4, E2 9.7, E3 9.2, E4 55.7 s) x 48 main replays per variant plus fresh means: serial 4519.1 s, LPT makespan
    565.1 s on 8 workers, below the 1500 s rule, so NO reduction: E1 and E2 stay in part a. Caveat: smoke traces are scale14;
    scale16 replays may be slower. The run cap stays 1800 s.
14. **GS_ref scope (Exact).** REFERENCE_041 audits part c only, E1 and E2: 24 records over 12 traces; mutations seeded
    random.Random(410).
15. **Recount (Exact).** scripts/recount_041 rebuilds every replay from worlds_0xx.actions plus the sealed extra actions and
    checks readings, T, k/N, the sealed [check, n_min], model consistency, the label rule, queries, by_phase and truth.
16. **Pre-freeze gates test (Observed).** prefreeze_smoke_041 PASS: recount PASS (10 replays, 6 cases), reference on smoke
    PASS (20/20 mutations), gates INCOMPLETE_INPUT on smoke as designed; a synthetic complete block (smoke replays copied into
    parts a, c and b x3) was sealed, recounted, referenced and gated twice with identical output. Synthetic G10 / GS_ref fail
    by their fixed counts and GTI / G_PROC by design. No gate outcome on smoke is used.

What this deviation does not do: no threshold, gate or seed changes; lowobs and noise stay Open.
