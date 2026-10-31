# Deviation #153 (study-040, v0.37.0): post-run record

Written after the main run, recount, reference, tests and gates. Nothing here changes a gate, threshold, sealed file or
frozen file. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4), 2026-10-30.

1. **Run (Observed).** One main run, started 23:37:20 (ledger f0cf26d, frozen source 9001029), 42/42 cases, 126/126 jobs,
   374.1 s of 1800 s, normal exit about 23:43:37; sealed b1da397 (ledger c14e217); 2 checkpoint snapshots pushed (66b9a3a,
   c2f4f3a). Nothing was relaunched or resumed.
2. **Agent interruption (Observed; no effect on data).** The agent session was interrupted while the reference audit
   (run_reference_040, started 23:45:33) was running. The process was not touched; it finished on its own at about 23:50
   and wrote results/study-040/main/REFERENCE_040.json. On resumption the file was checked complete (schema v37_0, 12
   cases, 9 decided, 3 not reached, 123 verdicts, 175 words, 0 mismatches, mutations 20/20, PASS, results sha matching the
   seal; the log ended with its summary line) and committed as is (fc93389, ledger fca9c91). It was NOT rerun.
3. **GINC15 and GTI fail as predicted pre-freeze (Observed).** The official suite (TEST_SUITE_040, 1a092da, ledger
   08cac8a) gives 10/11 modules ok; test_scalesearch15_0370 fails exactly the 3 checks recorded in #152 item 8 (perm12
   10540007 A15; 10540008 A15 and A15_cube: stored A14 ID n_min 12 vs unknown n_min 12). No decided verdict disagrees with
   A14; the failures are caps. GTI fails because that module fails. Not rerun, not tuned.
4. **GQB15 fails (Observed).** One A15_cube call on lowobs12 10630011 took 11.014 s against the 10.5 s bound (cap 9.0 s);
   A15 max 9.132 s, A14 max 9.250 s. The cap is enforced by the host timer hook between solver callbacks, so one call can
   overrun it (Inferred: a long uninterruptible solver step under 8-worker load); plan 040 limitation 5 noted that GQB bounds
   each call, not each step.
5. **Mechanism at 16 states (Observed / Inferred).** scale16 (12 cases): A15_cube 3/4/0/0/5 (ID/IDF/AMB/WRONG/IDU), A15
   1/2/0/0/9, A14 2/2/0/0/8. A15 without the cube LOST two A14 decisions (10610003, 10610007 ID/IDF for A14, IDU for A15 on a
   capped rival query) and gained one (10610002). The cube split turned four capped A15 cases into decisions (10610001,
   10610004 IDF; 10610006, 10610012 ID); on scale16 it made 153 cube calls: 0 SAT, 144 UNSAT, 9 capped. So the cube split
   works as a cap remedy (Observed), but the apartness/fixed-colour encoding is itself slower than A14 on some traces
   (Observed here and in GINC15), so the net paired ID gain is +0.083 [-0.167, 0.333] (c fails) and 9/12 cases still hit a
   cap at least once (d fails under the literal reading of #152 item 4).
6. **lowobs12 (Observed).** Every arm IDU on 12/12. A14 stopped on a capped least-machine query on all 12 with 0 extra
   actions; A15_cube used 14.8 extra actions on average (GFAM15 is exercised) and made 253 cube calls (12 SAT, 136 UNSAT,
   105 capped). One-bit observations at 12 states are beyond these SAT queries at a 9 s cap (Inferred).
7. **Seed variability (Observed).** A14 on the 040 scale16 seeds decided 4/12, against 0/12 on the 039 seeds: n = 12 per
   family is small, and the paired design (same seeds for every arm) is what c relies on.
8. **Branches fired (plan 040 next_if_fail).** GINC15 failed, so "the encoding changed semantics: an encoding audit, not a
   new arm" fires (here the semantics are unchanged on decided verdicts; the change is in cost). GFAM15 failed while b
   passed, so "the gain is family-specific" fires. b passed, so neither 'b fails' branch fires. GREP15 passed.
9. **What this does not show (Open).** Whether the slow-down comes from the apartness clauses, the fixed colours, or the
   raised size-search start; whether the GINC15 cap misses are stable under repeats; whether cubes on another position help.
