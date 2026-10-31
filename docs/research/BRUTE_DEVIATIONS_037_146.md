# Deviation #146 (study-037, v0.34.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_037. Each item records
a choice the plan left open, a reading of a criterion, or a process slip, made before any main case was run. Labels:
Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4).

1. **Authorization and seeds (Exact).** build_authorization_037 was ledgered (ledger b789fb9, 2026-10-30 20:09 EDT) under
   James's STANDING GO t133s553 (ledger 76b30d5), plan BRUTE_PLAN_037 at plan/v0.34.0 de168d1 (ledger 9d6a70e).
   seedcheck_037 PASS (results/diag-037/SEEDCHECK_037.json, commit 18b3e90, ledger dbbc74a: 752 files scanned, 0 standalone
   103xxxxx tokens, 25 embedded, 16/16 negative controls refused, 42 cases) before any 037 seed was used. The plan declares
   no smoke range; scripts/check_seeds_037.py declares the smoke range 10390001-10390030 (outside every plan range and
   every earlier range); the smoke block uses the first 7 (noisy_scale12 x2, clean_scale12 x2, noisy_scale8 x2, control x1).
2. **Sound stop, reading of the plan (Exact; reading).** The plan says: confirmation at B_max for a machine with <= N states
   and <= B_max flips that differs from M from the START state; "SAT -> execute the separating word ... and continue;
   UNSAT -> ID; capped -> IDU". brute/scalesearch12.confirm12 implements it as two frozen search10 queries at B_max:
   (a) 'future' mode for n = 1..N (a rival that differs from M's current state after the executed actions). A future-distinct
   rival is always start-distinct (its separating word w after acts gives the start word acts+w), and its word can be
   executed from the current state, so SAT -> execute the word (AMB round) and continue; capped -> IDU ('unknown').
   (b) only when (a) is all UNSAT and the check claimed ID: 'start' mode for n = 1..N. A rival that differs only from the
   start state has no executable word (there is no reset), so SAT -> IDF (identified from the current state, not from the
   start), UNSAT -> ID, capped -> IDU. An IDF claim needs only (a). When the least-B search already ran at B = B_max, the
   ordinary check is the confirmation (no extra query). The confirmation verdicts are stored per round ('confirm') and
   re-derived by recount_037 and run_reference_037.
3. **Probe order (Exact).** search 'double': candidates lo, then max(c + 1, 2c), capped at B_max with B_max always
   included (0, 1, 2, 4, 6 for B_max 6; 0, 1, 2 for B_max 2), stopping at the first SAT, then bisection in
   (last UNSAT, first SAT]. All UNSAT -> 'none'; the first capped probe -> 'unknown'. Every probe is recorded as
   [B, True/False/None]. A12_r3_nostop uses the same probe order with the frozen A11 stop ('a11').
4. **Timer, B_max and eps (Exact).** QUERY_S = 9.0 s per SAT query for all arms (plan query_timer_s), host TimerHook from
   the 035 module; GQB12 bound 10.5 s. B_max(r) = flip_budget(354, majority_rate(0.05, r)) with the frozen rule: r5 = 2,
   r3 = 6; S7 27. The declared eps 0.05 is used for B_max on every case, clean ones included (the arm does not know a case
   is clean); the world's eps is 0 on clean_scale12 and control as the plan says.
5. **Release-verify fix (Exact; process fix asked for in the build task).** The fresh-clone test runs of v0.32.0 and
   v0.33.0 both first refused (run_tests_0320/0330 default output was the tracked TEST_SUITE file; ledger
   fresh_clone_verify_0330 records it). scripts/run_tests_0340.py now writes to a fresh scratch file in the system temp
   dir by default (brute_tests_0340_<pid>_<ns>.json, never inside the tree); the official GTI input is written only with
   an explicit --output results/study-037/TEST_SUITE_037.json (or --official). tests/test_release_0340.py checks both
   (scratch default outside the repository, refusal to overwrite). verify_release_0340 does not run the suite.
6. **G_PROC order (Exact; reading).** The plan's G_PROC order runs plan -> authorization -> seedcheck -> freeze -> run_start
   -> run_end -> recount -> reference -> tests -> gates. make_gates_037 checks the events through tests_037 (gates_037 is
   the step that reads them and is ledgered after GATES_037.json is written).
7. **GSAFE12 pre-check (Exact).** tests/test_scalesearch12_0340.test_GSAFE12_sealed_036_trace replays the sealed 036
   A11_r3 trace of noisy_scale8 10210002 (T 181, the 036 check claimed ID at B 1, n_min 8): confirm12 at B_max 6 returns
   AMB; future-mode verdicts UNSAT for n = 1..7 and SAT at n = 8, so a start-distinct rival within B_max exists and A12
   does not claim ID at B 1. This is the GSAFE12 criterion; the gate reads it from TEST_SUITE_037 (inside GTI).
8. **Debug run on a published seed (Observed; disclosed).** One debug run_case used the 036 smoke seed 10290001 (already
   published, no 037 seed spent) as noisy_scale8 to check the runner end to end: 149.6 s; A12_r5 IDF (confirmations
   AMB, AMB, AMB, IDF), A12_r3 and A12_r3_nostop IDU (B 4), A11_r3 IDU (B 2, one capped probe), A11_r5 IDF, S7 IDU; max
   query walls about 9.03-9.12 s. Development tests use old seeds 10050001 and 10090005. Nothing was tuned on any of them.
9. **Ledger slip (Exact; disclosed).** The preregistration_037 note (ledger 9d6a70e) starts with a doubled timestamp
   ("2026-10-30T20:09:02-04:00 EDT 2026-10-30T20:08:59-04:00 EDT ..."): the helper prepends the clock time and the note
   text already carried one. The ledger is append-only; it stays as written. make_gates_037 parses the first 25 characters.
10. **Clock (Observed).** Box clock vs GitHub's Date header: 20:09:56 EDT vs 00:10:23 GMT at build authorization;
    20:32:29 EDT vs 00:32:16 GMT during the build (offsets within about 30 s, sign changed; cause Open, no stall seen).
11. **Pre-freeze smoke and runtime rule (Inferred; filled from results/diag-037/PREFREEZE_SMOKE_GATES_037.json).** The
    plan drops A12_r3_nostop before the freeze if the pre-freeze projection exceeds 1500 s. See item 12.
