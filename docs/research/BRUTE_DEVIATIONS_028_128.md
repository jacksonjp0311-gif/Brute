# Deviation #128 (study-028, v0.25.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_028. Each item
records a choice the plan left open, or a reading of a criterion, made before any held-out seed was run. Labels: Exact,
Observed, Simulated, Inferred, Rejected, Open.

1. **S3 solver chosen by a pre-declared rule (Exact rule; Observed result).** Rule, written before the choice:
   require 0 UNKNOWN on the control smoke seeds, then take the lowest summed UNKNOWN on scale8 + scale12 smoke seeds
   9490001-9490004. cd195 alone, m22 alone, m22+cd195 and mcb+cd195 each left at least one UNKNOWN on a 3-state
   control. mcb (summed U 23) and m22+mcb (22) did not. Chosen: `m22+mcb` (a two-solver portfolio).
   S2 summed U on the same seeds was 10, so no S3 choice beat S2 on smoke (Observed). GSC3 b is therefore likely to
   FAIL (Inferred). The run goes ahead as locked and the result will be published. Source:
   results/diag-028/S3_PORTFOLIO_028.json.
2. **Scratch S2 ablation (Observed; informational).** S2's extra machinery (hint, distinguishability clauses, chain)
   is not a significant net cost. The 8-state S1 advantage comes from per-query engine speed and the Glucose
   budget overruns: Glucose honours conf_budget only at restarts, and chunks overran by up to 115x. Source:
   results/diag-028/S2_ABLATION_028.json.
3. **Capped deepening in S3 (Exact).** Per-step n_lo deepening is off the per-step path. An observe step that needs
   a new model makes ONE capped attempt (DEEPEN_S seconds in total, not per level), starting from the cheapest proven
   bound (max of n_lo and a greedy clique bound). Full deepening runs only in identify. In the ablation, per-level
   deepening caused the worst observe overruns, and removing it entirely raised U at 12 states.
4. **GQB reading (Exact; strict).** GQB is gated on max(query_max, observe_max) for S3 on every main case, ≤ 10.5 s.
   This covers both support queries and observe work.
5. **Adaptive chunk (Exact).** Every S3 solve runs in conflict chunks (CHUNK0 = 2000). Each solver's chunk is shrunk
   from its measured seconds per conflict so that one chunk fits in SAFETY x the time left. There is a wall check
   before every chunk, and the portfolio solvers take turns one chunk at a time (no threads). Fixed in
   brute/scalesearch3.py.
6. **CI method (Exact).** For U and the paired GSC3 b difference: a seed bootstrap, 10000 resamples,
   random.Random(28), percentile 95% interval. X and ID use Wilson 95% intervals. U per case = UNKNOWN / planned,
   and an unrun query counts as UNKNOWN.
7. **Arms and budgets (Exact).** eps 0: S3 55 s, S3_tight 25 s, S2 55 s, S1 55 s. Stress (eps 0.05): S3, S2 and S1
   at 40 s each. RGB6 is dropped (its question was settled in v0.24.0). Identify runs with a 10 s cap for the exact
   arms. Worst-case runtime estimate: about 1290 s on 8 workers (Simulated from budgets), cap 1800 s.
8. **GSC3 a (Exact).** Recomputed from records: for every query both arms decided, S3's supports must equal S2's
   and S1's. Every exact S3 support at eps 0 on main must also contain the latent next code, checked against a world
   regenerated from the seed through worlds_026.
9. **G10 strict (Exact).** Every control eps-0 case needs S3 U_count = 0 (no solver UNKNOWN and no unrun query)
   and clause a mismatches = 0. The not_run / solver_unknown split is reported.
10. **GAPI13 stream check capped and parallel (Exact).** api_check_028 runs Certifier13 search='s3' over the first
    4 scale8 eps-0 main cases. It is capped at 60 steps per case and uses 4 processes, and it compares against the
    sealed arm S3 records.
11. **GS_ref13 mapping (Exact).** The v0.23.0 reference cross-check audits an arm in the S2 slot, so arm S3 is
    mapped into that slot. The mutation test uses seed 250 and must detect 20/20.
12. **Commit helper (Exact).** c.sh refused to commit when untracked files existed. The new pc.sh parks untracked
    files that are not listed, commits only the listed files plus MANIFEST, and restores the parked files. It still
    refuses if any tracked file has unlisted modifications, so no unrelated edit can be swept into a commit.
13. **Smoke range (Exact).** The smoke and diagnostic seeds are 9490001-9490012. They are disjoint from every
    held-out seed (SEEDCHECK_028). Smoke output goes outside results/study-028.
14. **Manual cap enforcement (Exact).** There is no watchdog script. The run is monitored, and if wall time reaches
    1800 s it is stopped and sealed partial with `--snapshot`. G_RT and the data gates then FAIL, and nothing is
    relaunched. The resume-after-reboot clause remains NOT approved.
