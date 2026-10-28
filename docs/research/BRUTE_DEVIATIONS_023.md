# Study-023 deviations (#108 onward)

Numbering continues after #107 (BRUTE_DEVIATIONS_021.md). Nothing frozen is edited; the ledger stays append-only. Each
deviation is written at the time it arises; later ones go in new files (BRUTE_DEVIATIONS_023_*.md).

## #108 Pre-code implementation details of RGL4 (written before brute/lrregion.py; Exact)
1. **Capped witness search.** The plan says T_L = min_n(w_n + D_n) - 1 with "smallest w found by feasibility search;
   any witness is valid". The implementation searches w upward only while w + D_n - 1 is below the current cap
   (m_a(b) and then the best witness already found at this step), carrying the start point s_n between steps. With no
   UNKNOWN witness solves this equals the uncapped rule exactly (LR_LEMMA_023, "Exact per-step rule"); with UNKNOWNs T
   can only be larger (more conservative). It changes no T value that the uncapped rule would give.
2. **Learner constants are read from BRUTE_PLAN_021.json.** BRUTE_PLAN_023.json states "mask_rate": "as study-021"
   (likewise the horizon, burn-in and learner) as text. The runner takes mask_rate 0.35, burn_in 8, 88 steps and the
   learner plan from the frozen BRUTE_PLAN_021.json, and the study-023 freeze hashes both plan files.
3. **Reference strength.** The reference enumerates every n-state machine for all n <= 4 (the plan asks for n <= 3 plus a
   witness recheck for n = 4); both checks are run. fmin_4 is also checked equal to the frozen v0170 costs_tables lo.
4. **Witness record.** Every witness found is stored (n, w, d, e with start state 0, decoded from the SAT model). States
   never visited carry the solver's arbitrary rows; the recheck simulates only the visited path.
