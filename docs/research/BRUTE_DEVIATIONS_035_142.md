# Deviation #142 (study-035, v0.32.0): build choices fixed before the source freeze

Written before the source freeze and frozen with it. Nothing here changes a threshold in BRUTE_PLAN_035. Each item records
a choice the plan left open, a reading of a criterion, or a process slip, made before any main case was run. Labels:
Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4).

1. **Definitions (Exact).** As in scripts/make_gates_035.py. GA10 b and GAD10 are paired per seed (1 if ID, else 0),
   seed-bootstrap 95% CI with the make_gates_034 helper (random.Random(34) reused, 10000 resamples). Wilson 95% CIs on
   every count.
2. **Cap hook (Exact).** The host timer hook (10 s per SAT query) is applied to every arm. A9 and S5 receive it through
   host-side patches in experiments/; no frozen brute/ source is changed. brute/ stays host-agnostic (no I/O, threads).
3. **Solver (Exact; deviation from the plan text).** The plan names CaDiCaL solve_limited with expect_interrupt. In
   pysat 1.9.dev17 the CaDiCaL 1.9.5 interrupt did not return in dev tests (Observed), so the arms use Glucose3 (g3),
   whose interrupt returns. The reference keeps CaDiCaL 1.9.5 with conf_budget chunks and a 30 s limit per query.
4. **World (Exact).** NoisyWorld over the step-only worlds_026 wrapper, with common random numbers per seed, so every arm
   sees the same flip sequence for the same action sequence.
5. **Declared rate (Exact).** eps_declared 0.05 for A10_fixed and S7; B_max = 27 for A10 (B_end(0.05) for the horizon).
6. **S7 and S5 (Exact).** S7 = identify10 with B = 27 and n_max = 16; S5 = identify6 on the noisy readings, unchanged.
7. **A10_fixed (Exact).** A10 with adaptive=False and B0 = 27 from the first round.
8. **Labels (Exact).** As label9 (034); a stop with no M1 ('none') is WRONG.
9. **Within budget (Exact; reading).** Per arm: the truth's flip count over that arm's final trace (actions and readings)
   is <= 27. GA10 a uses each arm's own within-budget set; the recount's within_budget is the one gated.
10. **K and N (Exact; reading).** Majority re-reads count against K. N is the nominal family size (8, 12 or 16).
11. **bmin10 (Exact).** The least SAT budget is found by an upward search 1..B_max (as the plan text), not bisection.
12. **Reference (Exact; process slip, Observed).** experiments/v0320_reference.py shares no code with brute/. The first
   draft encoded a reading flip as one clause per reading (a disjunction), so a 2-bit difference needed only one flip.
   The 2-bit enumeration unit test caught it before any data; the fix (commit 461e1c3) adds one flip clause per differing
   bit when B > 0; the scratch check then gave 360 checks, 0 bad. Undecided reference queries (30 s) are not mismatches.
   GS_ref is 'not exercised' (pass None) if the reference decides 0 items (with 0 mismatches and 20/20 mutations).
13. **Gates (Exact).** G16 is reported under 'secondary' (plan: 16 states secondary), not in gates_passed/failed.
14. **Seeds (Exact).** Seedcheck PASS (results/diag-035/SEEDCHECK_035.json, ledger seedcheck_035) before any 035 seed was
   used. Before the freeze only the smoke block 10190001-10190008 (inside the 035 smoke range) was used; unit tests and
   dev checks used old seeds only (10050001, 1007xxxx, 1009xxxx; tests 10050001 and 10090005). No main seed was drawn.
15. **Smoke (Observed).** results/diag-035/PREFREEZE_SMOKE_GATES_035.json, PASS: recount 0 mismatches (57 words checked,
   0 unsound), reference on the 2 noisy_scale8 cases 2 decided, 0 mismatches, mutations 20/20, gates --check reproduces
   on the relabelled block. Labels: A10 ID 2, AMB 1, IDU 5; A10_fixed ID 1, IDU 7; A9 ID 2, AMB 2, WRONG 4; S7 ID 1, IDU
   7; S5 ID 1, AMB 3, WRONG 3, IDU 1. Every noisy smoke case was IDU for A10. Not gated, no tuning followed.
16. **Runtime (Inferred; no amendment).** Smoke launched 18:48:10 EDT with 8 workers, wall 134.4 s (scale16 case). Mean
   case wall by key: scale16 134.4 s, noisy12 40.3 s, clean12 44.1 s, noisy8 54.7 s, control 1.2 s; projection for the
   48 cases: serial 2483 s, ideal parallel 310 s, greedy 8-worker makespan 318 s, against the 1800 s cap. The projection
   does not exceed the cap, so no runtime amendment is declared; workers stay 8 and the case count stays 48. Risk
   (Inferred): the smoke ran 8 cases on 8 workers, so per-case contention matches the run, but means over 1-2 cases per
   key are noisy; the worst case is set by the per-arm budgets, not by the mean.
17. **Clock (Observed).** At 18:52:59 EDT the box was about 5 s ahead of GitHub's Date header (22:52:54 GMT); no stall.
