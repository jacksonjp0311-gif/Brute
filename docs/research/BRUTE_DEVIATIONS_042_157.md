# Deviation #157 (study-042, v0.39.0): build choices fixed before the source freeze

Written before the source freeze (2026-10-31T02:05:50-04:00, box-local EDT) and frozen with it. Nothing here changes a threshold, gate or seed in
BRUTE_PLAN_042 (plan commit c5cf6bd). Each item records a choice the plan left open, a reading of a criterion, a correction, or
an observation made before any main record was run. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are EDT (UTC-4).

0. **Authorization and seeds (Exact).** preregistration_042 (c5cf6bd, 01:30:47 EDT); plan_erratum_042 (29ef4d5, 01:31:10 EDT);
   build_authorization_042 (01:32:21 EDT) under James's STANDING GO t133s553 (ledger 76b30d5); seedcheck_042 PASS
   (results/diag-042/SEEDCHECK_042.json, 8247cf7, ledger c0f381b, 01:38:29 EDT): scale16 10810001-12, perm12 10820001-12,
   control 10860001-06, smoke 10880001-06, disjoint from 312 prior ranges; 818 files scanned, 0 standalone tokens in 042 ranges;
   18/18 negative controls refused; erratum 1 (10870058, the study-023 HB_SENTINEL cpu counter) listed.
1. **Correction to the seedcheck ledger note (Exact).** The seedcheck_042 ledger note says "98 listed" standalone 108xxxxx
   tokens; SEEDCHECK_042.json lists 99 (standalone_tokens_108_block and erratum_1.listed_108_block both have 99 entries). The
   file is the record; the ledger entry is append-only and is not edited. All 99 are outside the 042 ranges.
2. **A16 (Exact).** brute/scalesearch16: E1's apartness clauses (encaudit16 variant E1: Inc14 first-visit clauses, A14 lower bound,
   plus one clause set per apart pair, no fixed colours) and the cube split applied only to a query that hits the 9.0 s cap.
   No greedy clique. A14 = encaudit16 E0 (active_audit('E0') / stop_check_audit('E0')), equal to the frozen active14 by the
   frozen 041 tests. Hard per-call cap as in 041 (#154 item 1): soft interrupt at 9.0 s, SIGKILL 1.0 s later; GQB17 bound 10.5 s.
3. **AMB-at-stop recount rule (Exact).** An AMB stop (or a K_spent stop whose last round is AMB) is valid iff: the stored future
   verdict list ends SAT at n*; M1 is consistent with the trace and s1 is M1's current state; the independent plain-CNF reference
   exists_different(acts, codes, n*, k, 4, M1, s1, 'future', L = N + |M1| - 1) is True. For K_spent additionally: M2 is
   consistent and the last word separates M1 and M2 at its last symbol only. (|word| > K - used is a property of the runner's
   stop, recorded, not re-derived.) Anything else is BAD_AMB and a recount mismatch.
4. **GRR041 (Exact / Observed).** scripts/recount_041b re-applies the frozen 041 recount with item 3 added to the sealed 041
   study; output results/diag-042/RECOUNT_041B.json (post-run, secondary). Observed on a scratch run before the freeze: the 25
   frozen BAD_stop replays all become AMB, 0 mismatches over 240 replays and 18 cases. Reported only; no 041 gate changes.
5. **GS_ref adapter (Exact).** scripts/run_reference_042 audits main scale16 A16 records. A K_spent record is audited as AMB
   (its last-round M1/s1, from the record); s1 always comes from the record. Mutations seeded random.Random(420), 20 per run.
6. **GT16 reading (Exact).** Per main case with calls in both arms, r = mean(A16 call walls) / mean(A14 call walls); statistic
   mean(r); seed bootstrap random.Random(42), 10000 resamples. H3 read: upper CI < 2. Secondary only.
7. **G_PROC reading (Exact).** preregistration, seedcheck, source_freeze, run_start, run_end, recount (all _042) must appear as a
   subsequence of the ledger; extra events (erratum, build authorization, deviations) are allowed.
8. **Gate independence (Exact).** Each gate reads its own inputs; G10 and G_sound do not depend on G_recount passing (the 041
   lesson). G16 and GPERM17 use recount labels if G_recount passes, else study labels with the failure stated (plan rule).
9. **Commit-order check (Exact).** verify_release_0390.chain keeps the 0380a rule: a build_authorization_042 entry may name the
   preregistration commit if that commit is an ancestor of the previous entry; no other entry may go back. Tested on a toy
   repo (tests/test_release_0390) and on the real ledger entries (prefreeze smoke: passed, 1 exception).
10. **Smoke composition (Exact).** 24 jobs: fresh 10880001-06 (scale16, scale16, perm12, perm12, control, control) x A16/A14;
   replays of the sealed 040 scale16 traces 10610001, 10610004, 10610008, 10610012 under both arms (10610008 was added because
   E1 ended IDF there in 041); two probes through the real code path: K0 = scale16 10880002 with K = 0, B05 = scale16 10880001
   with a 0.5 s case budget. The first smoke used perm12 10880003 for K0; it ended ID with no AMB round (no K_spent), so the
   probe was moved before the freeze. Smoke and probes are never gated.
11. **Bug found by the prefreeze smoke (Exact).** make_gates_042 checked tuple(case arms) == ('A16','A14'), but write_new sorts
   JSON keys, so every sealed case reads ('A14','A16') and the gates would have reported INCOMPLETE_INPUT on a real main block.
   Fixed to an arm-set check (commit 8445e48) before the freeze; the prefreeze PASS now requires the synthetic gates to be
   complete and to use recount labels.
12. **Pre-freeze smoke (Observed).** results/diag-042/PREFREEZE_SMOKE_GATES_042.json PASS: stops present ID 11, IDF 1, AMB 3,
   K_spent 2, unknown 7; recount PASS (8 replays, 8 cases, AMB rule applied 5 times, 64 words, 0 unsound, 0 mismatches); reference
   smoke 2/2 decided and probe (K_spent audited as AMB) 0 mismatches, 20/20 mutations each; synthetic main (6 fresh smoke cases)
   sealed, recounted, referenced and gated twice with identical output; release_ok on a synthetic RELEASE passes. Smoke fresh:
   scale16 10880001 A16 ID / A14 unknown; 10880002 ID in both. No gate outcome on smoke is used.
13. **Runtime projection (Inferred).** Mean smoke fresh wall per (arm, key) x 60 main jobs: serial 996.9 s, LPT 128.2 s on 8
   workers; worst case (every scale16 job at 250 s) 753.0 s. Both below 1800 s, so NO cut: scale16 keeps all 12 seeds.
14. **GTI (Exact).** Gated: test_scalesearch16_0390, test_scripts_042, test_release_0390. Reported only: test_encaudit16_0380,
   test_scalesearch14_0360.

What this deviation does not do: no threshold, gate or seed changes; lowobs, noise and the N-free stop stay Open.
