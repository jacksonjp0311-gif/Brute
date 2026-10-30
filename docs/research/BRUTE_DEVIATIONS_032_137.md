# Deviation #137 (study-032, v0.29.0): post-run record

Written after the run. Nothing here changes a threshold in BRUTE_PLAN_032, a frozen file or a sealed result. Labels:
Exact, Observed, Simulated, Inferred, Rejected, Open. Times are box-local EDT (UTC-4), 2026-10-30.

1. **Run (Observed).** One launch at 16:09:44 (ledger run_start_032 fb5519c), pid 265424, 8 workers. Complete 48/48,
   1246.3 s of 1800 s, normal exit (run log c67472e, ledger run_end_032 08a622c). Five checkpoint snapshots were pushed
   (2d16eb1, 73aea83, ceb71ab, 90450b9, 0ec1f9b). No relaunch, and nothing resumed.
2. **Pre-freeze fix (Exact).** scripts/make_freeze_032.py carried the study id "BRUTE-0280-ROBUST-PERCEPTION-032" (a
   copy slip from the 031 tooling). It was corrected to BRUTE-0290-... and the two outputs of the first attempt (never
   committed) were removed before the freeze was regenerated and committed in fd17c82. No result was produced in between.
3. **Box clock (Observed).** Checked against /proc/uptime and the GitHub API Date header at 16:02:58, 16:07:50,
   16:11:32, 16:12:00, 16:15:25, 16:15:53, 16:23:17, 16:26:53, 16:30:38 and 16:33:55 EDT. The box clock stayed within 8 s
   of the GitHub header at every check (a header is rounded to whole seconds and may come from an edge cache). Worker CPU
   time matched wall time (about 5:40 per worker at 5:49 elapsed). **No stall.** One anomaly was in the tool, not the
   box: two idle tool waits reported as 200 s and 240 s covered only 28 s and 20 s of box time (and GitHub time). After
   that, waits were done with `sleep` inside the shell (200-220 s, all ≤ 240 s).
4. **Gates (Observed; GATES_032.json 7c4d197, `--check` reproduces).** 6 of 9 pass: GQB7, GS_ref, GTI, G_PROC, G_RT,
   G_recount. GRP7_headline, GNR7 and G10 fail.
   - GRP7 a PASS: F_truth(S7) is 0 on all 45 checked cases (27 noisy within B, 18 clean and control). 3 noisy_scale8
     cases fell outside B (realised flips above B(t) at some reading: 9810001, 9810006, 9810012), and S7 had F_truth 0
     on those too.
   - GRP7 b PASS: paired U_inf(S7) - U_inf(S5) at noisy_scale12 is -0.109 [-0.154, -0.054].
   - GRP7 c PASS: paired U_inf(S7) - U_inf(S1) is -0.178 [-0.283, -0.084].
   - GRP7 d **FAIL**: X_inf(S7, noisy_scale12) is 0/12 [0, 0.242], against a bar of 3/12. Every arm scores 0/12 here.
   - GRP7 e PASS: S7 reported grammar_contradicted on 0 within-B noisy cases.
   - GNR7 **FAIL**: at clean scale12, U(S7) - U(S5) is +0.362 [0.348, 0.377], against a bar of ≤ +0.05 with CI upper
     ≤ +0.08. S5_in_S7 had 0 mismatches over 5566 eps-0 queries compared.
   - G10 **FAIL**: on controls, S7's unknown counts are 53, 53, 5, 28, 32 and 9 (U 0.085 [0.042, 0.129]), with F_truth 0.
     S5, S1 and S7_contra have U 0 and X 6/6.
   - GQB7 PASS: the S7 max query is 9.35 s (bound 10.5 s). Informational: S7_contra peaked at 10.68 s and S5 at 10.46 s.
   - GS_ref PASS: 6336 S7 queries, 3526 exact and 2305 decided by the reference, 0 mismatches, mutations 20/20.
     decided_impossible_codes is 0: on noisy_scale8 the reference never confirmed that an S7 answer ruled a code out.
5. **Other arms (Observed).** F_truth: S7_contra 0, S5 0, S1 12 (S1 F 5). S1's false certificates fall on noisy traces
   (scale8 5, scale12 3, scale16 4), 10 of them on within-B cases. U_inf at noisy_scale12: S7 0.467 [0.437, 0.499],
   S7_contra 0.673 [0.567, 0.791], S5 0.576 [0.542, 0.609], S1 0.644 [0.560, 0.749].
   Whole-trace contradiction verdicts (grammar_contradicted): S1 on 4 noisy cases (9810001, 9820003, 9820007, 9830002;
   3 within B); S7_contra on 3 (9820003, 9820007, 9820010; all within B); S5 and S7 on 0. Clean-trace no-regression:
   U(S7_contra) - U(S5) at clean scale12 is +0.0006 [0, 0.0019], and S7_contra keeps X 6/6 on the controls.
6. **Mechanism (Inferred, from counters; not gated).** The flip budget is fixed by the declared eps (B_end 27) and also
   applies on clean traces, so S7 keeps every machine that needs up to 27 flipped readings. That widens what has to be
   searched: S7/S5 throughput at clean scale12 is 0.53 (median, [0.49, 0.56]) and on controls 0.10. S7 also reaches
   fewer exact answers there (1880 vs 3028). The same widening is what lowers noisy U: S7 never goes vacuous through a
   contradiction. But X_inf stays 0, because no noisy case is finished within 55 s. The result: robust inference is
   sound inside the budget (Observed), but at this budget it pays for noise tolerance on clean traces (Observed), and it
   does not finish noisy worlds (Observed).
7. **Not tuned (Exact).** S7 is exactly as frozen. Nothing was rerun. The failures are published as measured.
