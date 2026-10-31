# Deviation #159 (study-043, v0.40.0): build choices fixed before the source freeze

Written before the source freeze (2026-10-31T02:48:38-04:00, box-local EDT) and frozen with it. Nothing here changes a threshold, gate or seed in
BRUTE_PLAN_043 (plan commit d9b8538). Each item records a choice the plan left open, a reading of a criterion, a correction, or
an observation made before any main record was run. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are EDT (UTC-4).

0. **Authorization (Exact).** preregistration_043 (d9b8538, 02:28:04 EDT); build_authorization_043 (d9b8538, 02:28:56 EDT) under
   James's STANDING GO t133s553 (ledger 76b30d5). Maintainer order kept: lowobs first; certify/16 after the N-free stop.
1. **Seedcheck erratum and adjudication (Exact).** seedcheck_043 FAILED (results/diag-043/SEEDCHECK_043.json, 486d6ab, ledger
   9226c54, 02:39:48 EDT): all_outside_043_ranges is false because one standalone token, 10980005, lies in the SMOKE range, at
   results/study-023/HB_SENTINEL_023.jsonl line 1261. Every other clause held: no pairwise or prior overlaps (317 prior ranges),
   832 files scanned, 18/18 negative controls refused, 12 + 12 + 6 = 30 cases, eps 0. The failed file is kept as is. A new
   check, scripts/check_seeds_043b.py, re-reads that line and finds the value only at JSON path cpu_jiffies.user (a CPU counter,
   not a seed), in the smoke range only, never a target range, and the listed set equals the declared erratum exactly:
   seedcheck_043b PASS (SEEDCHECK_043B.json, b0a20c2, ledger fcffb76, 02:40:31 EDT). G_PROC requires seedcheck_043b after
   seedcheck_043. Smoke seed 10980005 (a control case) is used as planned; the counter value cannot carry information about it.
2. **Recount adapter (Exact).** scripts/recount_043.py is new because the 042 recount dispatches worlds through worlds_039, which
   has no lowobs12. It is recount_042 logic with experiments/worlds_043 dispatch (lowobs12 -> worlds_040, scale16 -> worlds_039,
   control_cycle3 -> worlds_026), equal to the frozen generators by tests/test_worlds_043. Writes RECOUNT_043.json.
3. **GS_ref scope (Exact).** run_reference_043 audits A16 main records of lowobs12 AND scale16_rep (plan: decided lowobs12 cases),
   so the 20-mutation test has a non-empty pool if lowobs decides nothing. Pass: 0 mismatches, decided > 0 overall, 20/20;
   decided and records are reported per key. Mutations seeded random.Random(430).
4. **A14 (Exact).** A14 = encaudit16 E0, as in 042, equal to the frozen brute/scalesearch14 active14 by the frozen 041 tests.
   A16 = brute/scalesearch16 unchanged from v0.39.0. Hard cap 9.0 s, SIGKILL 1.0 s later; GQB18 bound 10.5 s.
5. **Smoke, probes, cut rule (Exact).** 24 jobs: fresh 10980001-06 (lowobs12 x2, scale16_rep x2, control x2) x A16/A14; replays
   of sealed 040 scale16 traces 10610001/04/08/12 under both arms; probes K0 = scale16_rep 10980003 with K = 0, B05 = scale16_rep
   10980004 with a 0.5 s budget. LPT cut rule: if the projection exceeds 1800 s, scale16_rep is cut to its first 6 seeds.
6. **GLO_cause (Exact).** Secondary, per lowobs12 case and arm: stop, label, n_min, used, n_rounds, capped calls, last phase,
   query_max_s. GT17 and GPH18 as in the plan; secondary only.
7. **GTI (Exact).** Gated: test_worlds_043, test_scripts_043, test_release_0400. Reported only: test_scalesearch16_0390,
   test_encaudit16_0380, test_scalesearch14_0360.
8. **Prefreeze PASS term (Exact).** results/diag-043/PREFREEZE_SMOKE_GATES_043.json (65ce3fe) records PASS false. Its only false
   term is authorization_exceptions == 1, copied from the 042 smoke. In 042 a plan_erratum entry sat between preregistration and
   build_authorization, so build_authorization named an earlier commit (1 exception). In 043 build_authorization directly
   follows preregistration and names the same commit, which is not a back-reference: 0 exceptions is the correct count, and the
   real chain passed (6 links). Every other term is true. The file is not regenerated; this item is the reading.
9. **Pre-freeze smoke (Observed).** Stops present: ID 4, IDF 2, AMB 3, K_spent 2, unknown 13. Recount PASS (8 replays, 8 cases,
   AMB rule 5 times, 57 words, 0 unsound, 0 mismatches). Reference smoke 1/4 decided (lowobs 0/2) and probe (K_spent as AMB)
   0 mismatches, 20/20 mutations each. Synthetic main gated twice, identical; release_ok on a synthetic RELEASE passes.
   Smoke fresh: lowobs12 10980001/02 IDU in both arms (A14 stops after its first least-model call hits the 9.0 s cap, used 0;
   A16 used 18 and 5, then a capped call); scale16_rep 10980003 A16 IDF / A14 IDU, 10980004 IDU both; control ID both.
   Smoke outcomes are not gated and nothing was tuned.
10. **Runtime projection (Inferred).** Mean smoke fresh wall x 60 jobs: serial 1724.2 s, LPT 219.4 s on 8 workers; worst case
   (every scale16_rep job at 250 s) 829.3 s. Below 1800 s: NO cut; scale16_rep keeps all 12 seeds.

What this deviation does not do: no threshold, gate or seed changes. The N-free stop, certify/16 and noise stay Open.
