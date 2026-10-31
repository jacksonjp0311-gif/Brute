# Deviation #163 (study-045, v0.42.0): build choices fixed before the source freeze

Written before the source freeze (2026-10-31T05:09:42-04:00, box-local EDT) and frozen with it. Nothing here changes a threshold,
gate or seed in BRUTE_PLAN_045 (plan commit 27d7946). Each item records a choice the plan left open, a reading of a criterion, a
narrowed scope, or an observation made before any main record was run. Labels: Exact, Observed, Simulated, Inferred, Rejected,
Open. Times are EDT (UTC-4).

0. **Authorization (Exact).** preregistration_045 (27d7946, 04:42:25 EDT); build_authorization_045 (27d7946, 04:44:54 EDT) under
   James's STANDING GO t133s553 (ledger 76b30d5), ledgered before seedcheck_045 (8162b85, PASS). The maintainer asked for the
   lean process, one run, the reference scoped to fit roughly within the run budget (item 4), and an honest bounded-claim label
   (item 7).
1. **A16_nf readings (Exact).** brute/nfstop18.py (new; scalesearch14 / scalesearch16 untouched, imported only). The plan says
   the wrapper calls "stop_check14/active16 unchanged". It cannot: their rival bound is the argument N, which also bounds the
   least-model search. So active18 copies active16's loop line for line on one Pool16 and calls stop_check18, which is
   stop_check14 with two changes only: least14 runs n = n_lo..CEIL18 = 16 (a compute ceiling, never claimed), and both rival
   searches (future, start) call search14 with the top size B = n_min + delta instead of N. The separating-word length follows
   search14's own rule at that bound. B is not clipped at the ceiling. Encoding, clauses, cube split, distinguishing word,
   K = 128, soft cap 9.0 s, budget 240 s are those of A16. A16_N runs scalesearch16.active16 as frozen with N = 16.
2. **Recount bound (Exact).** scripts/recount_045.py applies the frozen label043 rule with N_eff = the family size for A16_N and
   N_eff = n_min + delta for A16_nf1 / A16_nf2. It checks delta, the case bound and every round's bound, and used ==
   words_executed_length.
3. **future_match (Exact).** Each fresh arm record carries future_match: the returned model from s1 against the true machine from
   its true final state (truth_state_final). recount_045 recomputes it independently by product-automaton reachability; the
   reference recomputes it as future_match_ref. A misfire is a WRONG label, or an IDF label with future_match false. An ID label
   is checked against the canonical truth from state 0 by label043 (a wrong ID is WRONG).
4. **Reference scope, declared now (Exact).** The plan's GS_ref says "every decided case in every arm". The 044 audit took about
   31 min. scripts/run_reference_045.py therefore runs under one wall budget BUDGET_S = 1800 s (about the 3600 s run budget's
   half; roughly the run's expected scale), 8 worker processes (multiprocessing.Pool, apply_async, FIFO). Order: A16_nf2, then
   A16_nf1, then A16_N; within an arm control first, then scale16, each by seed. At the budget the pool is terminated; unfinished
   records are listed as not_audited. On an nf arm a stop mismatch [stop, ID, WRONG] is bucketed as a misfire (GNF_misfire), not a
   reference mismatch. 20 mutations, random.Random(450). PASS = 0 counted mismatches on audited records AND every decided
   A16_nf2 record audited AND 20/20 mutations detected (vacuous pass stated if nothing is decided). GNF_bound additionally needs
   every decided A16_nf1 and A16_nf2 record audited. **This weakens the plan's GS_ref**: A16_N records may be left unaudited if
   the budget runs out. GATES reports 'complete' and the not_audited list; the release text must say so if complete is false.
   Projection (Inferred, item 9): about 161 s LPT on 8 workers, so complete = true is expected.
5. **GNF_agree equivalence (Exact).** "Same stop kind and an equivalent canonical model": for ID, both models equal as canonical
   machines from state 0; for IDF, equal behaviour from the current states, i.e. both future_match true. Bar 8/12 and 90% unchanged.
6. **Smoke and probes (Exact).** 24 jobs. Fresh smoke seeds 11290001-06 (scale16 x 4, control x 2) x 3 arms. Replays of the
   sealed 040 scale16 traces 10610001/04/08/12 under A16_N only (the nf arms have no replay path). Probes K0 (K = 0) and B05
   (0.5 s budget), both on control 11290005 under A16_nf2. GQB20 bound 10.5 s for every arm.
7. **Labels and the bounded claim (Exact).** An nf ID / IDF is the plan's ID_d / IDF_d: the model is unique (from the start, or in
   its future behaviour) among machines with at most n_min + delta states that are consistent with the trace. It is a bounded
   claim, not full N-freedom: a larger true machine is not ruled out, and the least-model search still uses the ceiling 16.
   RELEASE.json, README, CHANGELOG and the release notes must use this wording.
8. **Commit chain (Exact).** build_authorization_045 names the preregistration commit itself and nothing lies between, so
   verify_release_0420.chain must report 0 authorization exceptions. The pre-freeze test did (5 links, 0 exceptions).
9. **Pre-freeze smoke and runtime projection (Observed / Inferred).** results/diag-045/PREFREEZE_SMOKE_GATES_045.json (11e600b)
   has PASS true. Stops present: ID 6, IDF 7, AMB 3, K_spent 4, unknown 4; none missing. Recount PASS (333 words, 0 mismatching
   cases). Reference smoke: 14 decided, 14 audited, 0 mismatches, 0 misfires, 20/20 mutations, 82 s; probe 2 decided, PASS.
   Synthetic main block: gated twice with identical output; release_ok passes. Real chain: 5 links, 0 exceptions.
   Mean smoke fresh wall per job (Observed): A16_N/scale16 32.8 s, A16_nf1/scale16 174.5 s, A16_nf2/scale16 84.6 s, controls
   about 0.1 s. Over 54 main jobs (Inferred): serial 3505.5 s, LPT 447.5 s on 8 workers; worst case (every scale16 job at 250 s)
   1250.0 s. Both are below the 3600 s G_RT bar; the plan has no cut rule and none is used.
10. **Observed before the freeze, not acted on (Observed / Inferred).** On the smoke, A16_N was ID on 4/4 scale16 and 2/2
   controls. A16_nf1 and A16_nf2 decided 0/4 scale16 (AMB at K_spent 2, unknown 2 each) and were IDF, not ID, on both controls
   and both probes. Inferred reading for the controls: with a bound above the true size, a larger consistent machine with a
   different start exists, so the start search finds a rival and the stop is IDF (future_match true; not a misfire). Inferred
   reading for scale16: the nf rival searches pick small rivals whose separating words differ from A16_N's, so the traces
   diverge and K runs out; the mechanism is Open. **Expected consequences, stated before the freeze:** G10 ("every arm ID on
   each control") will likely fail for the nf arms, and GNF_agree ("same stop kind", bar 8/12) will likely fail. The gates are
   not changed, nothing is tuned, and delta stays 1 and 2 as declared. Plan 045's next_if_fail branch decides what follows.

What this deviation does not do: change any threshold, gate, seed or delta. Full N-freedom, certify/16 and noise stay Open.
