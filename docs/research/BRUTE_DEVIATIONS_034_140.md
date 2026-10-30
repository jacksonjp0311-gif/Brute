# Deviation #140 (study-034, v0.31.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_034. Each item records
a choice the plan left open, a reading of a criterion, or a process slip, made before any main case was run. Labels:
Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4).

1. **Definitions (Exact).** As in scripts/make_gates_034.py. GA9 b and GCH9 are paired over the 12 scale12 seeds (per
   seed 1 if ID, else 0), seed-bootstrap 95% CI with random.Random(34), 10000 resamples. Wilson 95% CIs on every count.
2. **ID means behaviour equality (Exact; reading).** The plan defines ID as "a single behaviour class from the start
   state up to N, equal to the truth". A9 / A9_random label ID when both bounded searches are UNSAT for every n = n_min..N
   and M1 is behaviourally equal to the truth from the start state (product BFS), WRONG if the searches are UNSAT but M1
   is not. The 033 canonical (state-for-state) comparison is kept only as the descriptive field canonical_match, because
   a machine with unreachable or duplicate states can be behaviourally equal without being canonically equal.
3. **Encoding (Exact).** brute/scalesearch9.differ9: the frozen S1 region encoding for the trace plus a symbolic word of
   L = N + n_M1 - 1 steps (one-hot actions; M2 states; M1 states from M1's fixed table) and a disjunction "codes differ at
   some step j <= L". This is complete: two Moore machines of sizes n and n1 that differ have a separating word of length
   <= n + n1 - 2 < L. Mode 'future' starts M2 at its state after the trace and M1 at s1; mode 'start' starts both at 0.
   A SAT answer is decoded and re-simulated; a decode that fails the check raises (never silently accepted).
4. **Search order and verdicts (Exact).** search9 tries n = n_min..N in order and stops at the first SAT; every verdict is
   recorded as [n, SAT | UNSAT | UNKNOWN]. stop_check9: future SAT -> AMB (continue with a word); future UNSAT at every n
   and start SAT -> IDF; both UNSAT at every n -> ID; any UNKNOWN (10 s cap) -> unknown -> IDU; no M1 -> none -> WRONG.
5. **Words and K (Exact).** On a future SAT the shortest separating word of M1 and M2 from their current states (product
   BFS) is executed through the step-only wrapper; if it is longer than K - used (K = 64), A9 stops K_spent, labelled AMB.
6. **A9_random (Exact).** The passive prefix plus exactly A9's extra-action count (capped at K) of actions from
   random.Random(seed*91034+34), then one stop_check9 without further actions; a future SAT is AMB.
7. **Budget (Exact; reading).** 120 s per arm per case (as #138 item 5), 10 s hard cap per SAT query; GQB9 bound 10.5 s.
8. **Reference (Exact).** experiments/v0310_reference.py shares no code with brute/: plain CNF solved with CaDiCaL,
   first-visit state order along the trace without the 'every state visited' constraint, a pair unrolling with a
   monotone 'already differed' flag. scripts/run_reference_034.py audits arm A9 on every scale8 case: n_min (via the
   frozen v0300 reference), every stored verdict, a direct size-N check of every final all-UNSAT list, the label, and
   the words; 20 mutations from random.Random(310). Process slip (Observed): the first draft had no symmetry breaking;
   its unit test ran into the 900 s `timeout` at 17:48 EDT (killed by the timeout, no data involved); first-visit order
   was added and the test then passed in about 2 s. No plan seed was used.
9. **GDIAG8 not exercised (Exact).** If A8 has 0 recounted WRONG on the 36 cases, GDIAG8 has pass None and status
   'not exercised': it is in neither gates_passed nor gates_failed; RELEASE.json lists it under gates_not_exercised and
   scripts/verify_release_0310.py checks that list.
10. **Seeds (Exact).** Seedcheck PASS (results/diag-034/SEEDCHECK_034.json, ledger seedcheck_034) before any seed was used.
   Seeds used before the freeze are all in the 034 smoke range 10090001-10090030, outside every plan range: smoke block
   10090001-10090006; unit tests 10090029 (control) and 10090030 (scale8); dev checks 10090007 (scale12: A9 ID with 4
   actions, query max 1.6 s; A9_random AMB, A8 ID, S5 AMB, S1 AMB; 9.5 s) and 10090008 (scale16: A9, A9_random and A8
   IDU with query max about 10.2-10.3 s; S5 AMB; S1 IDU; 72 s). Observed; not gated, no tuning followed.
11. **Smoke (Observed).** results/diag-034/PREFREEZE_SMOKE_GATES_034.json, PASS (recount, reference 20/20, gates --check
   reproduces on the relabelled block). Labels: scale16 10090001 A9 IDU, A8 WRONG; scale12 10090002 and 10090003 A9 ID,
   A8 ID, S5 AMB; scale8 10090004 A9 IDF; scale8 10090005 and control 10090006 all arms ID. Smoke wall about 200 s with
   6 workers (scale16 case 53 s).
12. **Expected limit (Inferred).** When the truth's minimal size is below the declared N, certifying "no other machine
   up to N" needs words that probe states the truth does not have; A9 then tends to stop K_spent (AMB). Observed only in
   synthetic unit tests; this is inherent to the stop rule, not tuned.
13. **Clock (Observed).** At 17:18:54 EDT the box was about 6 s ahead of GitHub's Date header; no stall seen.
