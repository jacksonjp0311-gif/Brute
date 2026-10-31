# Deviation #177 (study-052, v0.49.0): pre-run declarations

Written before the source freeze (2026-10-31T14:50:24-04:00, box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_052 (plan/v0.49.0, commit f43e1ba)
that the plan leaves open. It changes no threshold, seed, cap, eps, eps_bar or delta, and no gate. Labels: Exact, Observed,
Simulated, Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_052 (plan f43e1ba), build_authorization_052 (ledger 42fe78a, cites James's STANDING GO
   t133s553, ledger 76b30d5), seedcheck_052 (ledger e90480f; SEEDCHECK_052 at 83b0030), then prefreeze_smoke_052,
   source_freeze_052, run_start_052, run_end_052, recount_052, reference_052, api_checks_052, tests_052, gates_052. Lean process.
   The resume clause is not approved: an interrupted run is never relaunched; a partial block is sealed as such.
2. **Arms and caps are the plan's (Exact).** noise12: 24 worlds (seeds 11930001-11930024), API16N and API16N_b (certify/16n, eps
   0.05, eps_bar 0.10, delta 0.001), C = 50000, B = 1500000. noise12_bar: the first N12BAR of 12 worlds (11950001-11950012) at eps
   0.10 = eps_bar, API16N_bar once, same caps. compat: 6 controls (11970001-11970006), API16N_c (certify/16n at eps 0, one read per
   observation) against API16E (certify/16e), C = 50000, B = 3000000. max_chunks None. Guards 600 s per case and 30 s per chunk are
   host safety only; any firing fails GDET52 / GQB26 and is never a label.
3. **One phase and job order (Exact, from code).** One process, WORKERS 8, all 72 jobs in one pool: compat jobs first, then
   noise12, then noise12_bar (experiments/brute_study_052.py, b9bc437). The runner stores each case's arms in job order, so a
   compat case's arms read (API16E, API16N_c); gates compare arm sets (item 11).
4. **N12BAR cut (Exact rule; Observed decision).** Cut order N12BAR 12 -> 6, never noise12, never after the freeze. Projection
   (Inferred; scripts/prefreeze_smoke_052.py): r_min = min(slowest smoke rate over records with case wall >= 1 s, 29194/s
   declared) = 27644.1/s; every job's worst case min(600 s, B / r_min + 10 s); LPT on 8 workers. Worst-case total for N12BAR = 12:
   686.9 s <= 3600 s, so **no cut**; N12BAR = 12 equals the runner (cut_consistent true). The runner refuses a main run unless the
   freeze's n_noise12_bar equals N12BAR.
5. **Compat rule (Exact; plan GCOMPAT16N52).** Per control, with recounted labels: labels equal; for ID, the same machine after
   BFS-canonical renaming from start state 0; for IDF, future_match true on both records and the same machine rooted at the
   current state s1 (isomorphism from s1); otherwise label equality only (scripts/recount_052.py compat_rule, 5395e3c). canon16e
   equality is reported, not gated. This IDF-equivalence rule was introduced after study-051's GCOMPAT16S / G10 IDF failures; it is
   applied only to study-052 data and not retroactively: GATES_051 and every earlier gate file stand as published.
6. **GFID52 replays all 72 records (Exact).** api_checks_052 replays 2 x 24 noise12 + N12BAR noise12_bar + 2 x 6 compat records on
   8 workers (N-arm observations rebuilt from the recorded votes); with no cut nfid = 72. Records stopped by majority_error are
   skipped and reported.
7. **G_sound addition (Exact).** G_sound also requires 0 WRONG on the compat arms (API16N_c and API16E). This is stricter than the
   plan's wording, never looser.
8. **Seedcheck token widening (Exact).** check_seeds_052 widens the standalone-token pattern to the 11 and 12 prefixes because the
   smoke range starts with 1203; rules J and K were declared before the scan. Result: 0 standalone tokens in the 052 ranges, 359
   prior ranges, 0 overlaps, PASS.
9. **GN12_pool sources (Exact).** Reported only, never gated: study-050 from GATES_050 gate GN12_sound, study-051 from GATES_051 gate
   GN12_sound51 (both 11/12 ID+IDF with 0 WRONG on 24 records), plus the 052 eps-0.05 API16N records. Different cases, not a paired
   comparison.
10. **GHOST52 (Exact).** Frozen module shas: certify14, 16, 16d (FREEZE_047), 16e (FREEZE_049), 16n (FREEZE_050), 16s (FREEZE_051);
    the 16e, 16n and 16s import closures must equal API_CHECKS_051; api certify16n_sha256 equals the current file, the 050 freeze
    sha and the 052 freeze sha. A network-free subprocess runs Certifier16N on smoke seed 12030002 at eps 0.05.
11. **Pre-freeze tooling fix (Observed).** The first prefreeze_smoke_052 attempt gated its synthetic block as INCOMPLETE_INPUT:
    make_gates_052 compared arm lists in order (API16N_c, API16E) while the runner stores (API16E, API16N_c). Fixed before the
    freeze to compare arm sets (9a3a230, with a regression test); the attempt-1 output was not committed (kept at
    /tmp/s52/prefreeze_attempt1.json, box only). Attempt 2 (9599362): PASS true. Synthetic gate failures, all by design or by
    smoke size: GN12_sound52 (>= 8/24 cannot hold on 2 smoke cases), GTI, GTEST, G_PROC. The note's mention of GHOST52 and G_RT as
    by-design failures is stale: both passed on the synthetic block (Observed).
12. **Smoke (Observed, seeds 12030001-12030006, never gated).** noise12 2/2 ID or IDF with passes identical, noise12_bar 2/2 ID or
    IDF, compat 2/2 equal under item 5 (one ID, one IDF), 0 majority errors, 0 guard firings.
13. **Claim scope (Inferred).** Every ID / IDF is conditional on the declared N = 12 and on iid flips with eps <= eps_bar; it holds
    with probability >= 1 - delta per record. Without the size bound no finite trace suffices: a larger machine can copy the true
    machine on every visited state and differ only on states the trace never reached.
