# Deviation #138 (study-033, v0.30.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_033. Each item records
a choice the plan left open, a reading of a criterion, or a process slip, made before any main case was run. Labels:
Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4).

1. **Definitions (Exact).** As in scripts/make_gates_033.py. Labels follow the 031 rule: IDU if the arm's search ran out
   of budget; else AMB if a second non-isomorphic consistent machine was found at n_min; else ID if the single class
   equals the truth (canonical BFS); else WRONG. GAE8 b and GCH8 are paired over the 12 scale12 seeds (per seed 1 if ID,
   else 0), seed-bootstrap 95% CI with random.Random(33), 10000 resamples. 4/12 passes b (0.333 >= 0.33); 2/12 does not
   pass GCH8 (0.167 < 0.17), 3/12 does.
2. **Identify probe inside A8 (Exact; reading).** The plan says "S5 encoding, symmetry-free". A8 uses
   brute.scalesearch8.identify8: the 031 identify probe (brute.scalesearch6 _RegionID with first-visit symmetry
   breaking, the 031 blocking clause, a second-machine solve) with a 10 s per-query hard cap and a chunked restart from
   the previous round's n_min (n_min cannot fall as the trace grows). Symmetry breaking is needed so that the second
   machine is non-isomorphic to the first; "symmetry-free" is read as "no extra symmetry assumptions beyond the probe".
   The 10 s per-query cap is the plan's budget clause; S5 runs the 031 probe unchanged (no per-query cap, as in 031).
3. **No distinguishing word (Exact; reading).** If the product BFS of M1 and M2 from their current states finds no word,
   the round stops 'indistinguishable' (the plan's "else stop and report"); the case is AMB, because both machines remain
   consistent with every possible future observation. The round records, descriptively, same_future (M1 and M2 are the
   same machine from their current states, so they differ only in the start state or the unreached past) and
   M1_future_match. Observed on dev seeds 4242-4244 (not plan seeds): every such stop had same_future True.
4. **K_spent (Exact).** If the next word is longer than the remaining action budget (K = 64), A8 stops 'K_spent' without
   executing it; the case is AMB (a second machine is still consistent).
5. **Budget (Exact; reading).** "120 s per case, the same for every arm" is read as 120 s per arm per case (each arm gets
   its own 120 s). Runtime estimate: 36 cases, 4 arms, up to 120 s each on 8 workers (plan: 1000-1500 s; G_RT cap 1800 s).
6. **A8_random (Exact).** The passive prefix plus exactly A8's extra-action count (capped at K) of uniform random actions
   from random.Random(seed*91033+33), continuing from the prefix end state, then one identify8 call (start n 1, same cap).
7. **S1 (Exact).** brute.scalesearch4.identify_trace, unchanged (frozen); AMB if not unknown, n_min found and not unique.
8. **No per-step support arms (Exact).** Study 033 gates identification labels only; the per-step support U of 026-032 is
   not computed and not gated.
9. **Soundness record (Exact).** Per A8 round the runner records word_sound (both machines' outputs on the word equal
   before its last action and differ after it, and equal the predictions made before execution), M1/M2 consistency with
   the round's trace, truth consistency with every round prefix and every arm's final trace. recount_033 recomputes all
   of these independently from the seed; run_reference_033 rechecks scale8 A8 with an independent CNF (CaDiCaL) and
   product BFS (shortest-word length), plus 20 seeded mutations (label, n_min +1/-1, one action of an executed word).
10. **Smoke (Exact; Observed).** The smoke block is 6 cases on 9990001-9990006 (scale16, scale12 x2, scale8 x2, control).
    Test fixtures use 9990029/9990030. Seedcheck_033 passed before any of them ran.
11. **Smoke finding and fix (Observed; process).** The first smoke run (started 16:59 EDT) crashed on a K_spent round:
    the runner read the predictions of a word that is not executed. Fixed in experiments/brute_study_033.py (8b23acf;
    predictions are compared only when present); the smoke block was run once more (17:02 EDT) from an empty output directory and
    passed (results/diag-033/PREFREEZE_SMOKE_GATES_033.json). This is a pre-freeze build fix, not a main-block rerun.
12. **Process (Exact).** LEAN: build_authorization_033 under James's STANDING GO (t133s553, ledger 76b30d5); seedcheck_033
    before any seed; the source freeze (make_freeze_033) before run_start_033; one main run, no tuning, no reruns, no
    resume (the runner refuses a non-empty main checkpoint).
