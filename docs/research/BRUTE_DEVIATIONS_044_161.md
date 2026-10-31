# Deviation #161 (study-044, v0.41.0): build choices fixed before the source freeze

Written before the source freeze (2026-10-31T03:54:25-04:00, box-local EDT) and frozen with it. Nothing here changes a threshold, gate or seed in
BRUTE_PLAN_044 (plan commit d55ec61). Each item records a choice the plan left open, a reading of a criterion, a correction, or
an observation made before any main record was run. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are EDT (UTC-4).

0. **Authorization (Exact).** preregistration_044 (d55ec61, 03:03:59 EDT); build_authorization_044 (d55ec61, 03:04:48 EDT) under
   James's STANDING GO t133s553 (ledger 76b30d5). The maintainer asked for the lean process, a single run, and the plan's cut rule
   applied at 1800 s (item 3).
1. **A16_xf reading (Exact).** brute/lowobspolicy17.py (new; scalesearch16 untouched). The plan says the schedule runs "from the
   start". The world has no reset, so the schedule runs from the state where the passive trace ends. The schedule is every action
   word of length 1, then 2, then 3, in lexicographic order over 0..k-1, concatenated and cut at E = 32 actions. For k = 3 these
   words hold 3 + 18 + 81 = 102 actions, which is at least 32, so the random length-6 tail is never reached and no random number
   is drawn. For k <= 2 the tail is drawn from random.Random(seed of the case). Controls have k = 2, so they get the tail. The
   schedule stops early only if the deadline passes. Then active16 runs as frozen with K - (executed) experiments, the same cap,
   deadline, solver and hook. Record fields: used = every executed action (counted against K = 128); xf_used = the schedule
   part; words_used = the separating-word part; xf_actions = the schedule actions. recount_044 recomputes the schedule
   independently and checks that the executed prefix equals it, that xf_used = 32 unless the stop is unknown, that xf_used = 0
   for A16_c9 and A16_c30, and that words + xf_used = used.
2. **Seedcheck failure and post-scan adjudication (Exact).** seedcheck_044 FAILED (results/diag-044/SEEDCHECK_044.json, 81d6150,
   ledger 4616eaf). One standalone token in a 044 target range, 10930001 (the first lowobs12 seed), was found at
   results/diag-043/SEEDCHECK_043.json negative_controls/17/1. That is the 043 seedcheck's own list of refused probe seeds.
   The 043 rule J (cpu_jiffies only) does not cover it. The failed file is kept as is. scripts/check_seeds_044b.py
   (SEEDCHECK_044B.json, 3a3f0ec, ledger 6a4c5d7) checks that the token occurs only at that path, inside a probe that was
   refused, and that every other clause holds. It records the git blob of check_seeds_043.py (949fa17c). PASS.
   **This rule was written after the scan.** The plan note asks for adjudication rules "before the scan". This item declares that
   departure. The value is a negative-control input of a checker, not a seed that was run, and cannot carry information
   about world 10930001. G_PROC requires seedcheck_044b after seedcheck_044. Lesson for plan 045 (Inferred): choose seeds
   absent from earlier negative-control lists, or declare a negative-probe rule in the plan.
3. **Cut trigger (Exact).** The plan's runtime_estimate cuts A16_c30 to the first 8 lowobs12 seeds if the LPT projection exceeds
   3600 s (bar >= 2/8 with gain >= 2 on those seeds). The maintainer lowered the trigger to 1800 s for this run. The rule,
   the bar and the seeds are otherwise unchanged. G_RT stays 3600 s, as pre-declared.
4. **Scope of recount, reference and GS_ref (Exact).** scripts/recount_044.py (a new file) uses label043 and recount_replay043.
   scripts/run_reference_044.py audits the main records of all three arms on lowobs12, with mutations seeded by
   random.Random(440), and reports decided records per arm and per key. GS_ref passes with 0 mismatches and 20/20 mutations
   detected. If no lowobs12 record is decided, the pass is vacuous: there is nothing to audit, and GATES states that explicitly
   (vacuous = true). This vacuous pass is allowed by the plan and is stated, not hidden.
5. **Smoke and probes (Exact).** 24 jobs. Fresh smoke seeds 10990001-06 (lowobs12 x 4, control x 2) x 3 arms. Replays of the
   sealed 040 scale16 traces 10610001/04/08/12 under A16_c9 only. Probes K0 (K = 0) and B05 (0.5 s budget), both on control
   10990005 under A16_c9. Hard kill 1.0 s after each soft cap. GQB19 bound = cap + 1.5 s (10.5, 31.5, 10.5).
6. **GTI (Exact).** Gated modules: test_lowobspolicy17, test_scripts_044, test_release_0410. Reported only: test_worlds_043,
   test_scalesearch16_0390, test_scripts_043. A development run of all six passed: 5, 10, 9, 5, 5 and 9 tests (Observed; this
   run was a scratch file outside the tree).
7. **Pre-freeze smoke (Observed).** results/diag-044/PREFREEZE_SMOKE_GATES_044.json (abddc72) has PASS true.
   - Stops present: ID 8, IDF 1, AMB 3, K_spent 1, unknown 11; none missing. The probes decided ID at once, so K_spent comes only
     from A16_c30 on lowobs12 10990002 (AMB, K_spent, used 123).
   - Recount PASS: 0 mismatches, 78 words checked, 0 unsound.
   - Reference: smoke 7 decided and probe 2 decided, 0 mismatches, 20/20 mutations each.
   - Synthetic main block: gated twice with identical output; release_ok passes.
   - Real chain: 6 links, 0 authorization exceptions. That is the expected count, because build_authorization_044 names the
     preregistration commit itself.
   - Smoke lowobs12, ID+IDF: A16_c9 0/4, A16_c30 0/4 (1 AMB), A16_xf 0/4. Every A16_xf lowobs12 case ran the full 32-action
     schedule; most then hit the cap on the first least-model call, with words_used 0. The exception is 10990002, with words_used 47.
   - Smoke outcomes are not gated, and nothing was tuned.
   - The first prefreeze attempt hit my 700 s shell timeout during its synthetic reference step and wrote nothing. It was rerun
     unchanged in the background. This is tooling, not the gated run.
8. **Runtime projection (Inferred).** Mean smoke fresh wall per job: A16_c9/lowobs12 38.2 s, A16_c30/lowobs12 130.1 s,
   A16_xf/lowobs12 32.0 s, controls about 0.1 s.
   - Over 54 main jobs: serial 2405.6 s, LPT 308.6 s on 8 workers.
   - Worst case (lowobs12 A16_c30 at 610 s, the other lowobs12 jobs at 250 s): 1720.0 s.
   - Both are below 1800 s, so **NO cut**: A16_c30 runs on all 12 lowobs12 seeds, with the 3/12 bar and a gain of at least 2.
   - Post-run reference cost (Observed): one decided lowobs12 AMB record took about 280 s to audit.

What this deviation does not do: change any threshold, gate or seed. The N-free stop, certify/16 and noise stay Open.
