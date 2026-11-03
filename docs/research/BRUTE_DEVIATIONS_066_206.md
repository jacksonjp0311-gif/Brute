# Deviation #206 (study-066, v0.63.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 3 2026). It fixes readings of experiments/BRUTE_PLAN_066.json
(plan/v0.63.0, ledger preregistration_066 at 3954159; the plan is locked and not amended). It changes no cap (C 50000, B 8000000,
K 400, read_bits 2, node cap 200000, delta 0.001), arm noise (S30/S24 eps 0.30, eps_bar 0.35), bound (20 / 24), worker count (7),
job kill (600 s), case guard (1800 s), main-run cap (2400 s), case counts (6 C20, 6 S30, 4 C24, 4 S24, 1 S30b = 21) or job order.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** Third and last of the 2-3 test versions James agreed on (Nov 2, 20:10 EST: larger sizes and noise,
   good ideas over budget bumps). The method change is none: certify/32s is certify/20s's sequential re-read front end on an unchanged
   certify/32p. The runner change is the liveness fix from #205 (process-per-job with a SIGKILL at 600 s, KILL = complete undecided).
1. **Process (Exact, ledger note times, EST).** preregistration_066 and build_authorization_066 (08:48; standing go t133s553 and
   t139s684), seedcheck_066 (08:59, PASS), build commit c543ba0, prefreeze_smoke_066 (PASS, ledgered at 44c4f57), then deviation_206,
   freeze_066, main_run_066 (once, nohup, never relaunched).
2. **Disclosures (Observed).** (a) The plan was drafted by the agent under the standing go and not reviewed by the user.
   (b) Build work stalled from about 09:12 to 10:10 EST (no process, nothing committed); a watchdog resumed it. No main seed was run
   during the gap. (c) The pre-freeze smoke ran at about 09:00-09:12 EST on the build while it was still UNCOMMITTED; the build was
   committed afterwards (c543ba0). The smoke is a tooling check, never gated. (d) Between the smoke and the build commit one tooling
   test was fixed: tests/test_scripts_066.Runner.test_kill_path's stand-in job returned n=1, k=3, while the runner's KILL record
   carries the world's real n and k, so merge() correctly refused the mismatched group. The stand-in now uses the real world's n/k.
   The runner, recount and gates were not changed. (e) No main seed (12660101-06, 12660201-04) has been run by any tool; the smoke
   used 12660301, api_checks use smoke seeds 12660301-02.
3. **New definitions (Exact).** certify/32s = certify/20s threshold/settle (imported) on Certifier32P(family_bound 1..32).
   KILL record: label and stop 'KILL', undecided, no model, no trace; counts in denominators, never as decided (plan incomplete_rule).
4. **Runtime (Observed + Inferred).** Smoke walls at B 2M: C20/S30/S30b 69-70 s, C24/S24 78 s (undecided at 2M). At B 8M (4x) the
   Inferred 20-state wall is a few hundred seconds and some 24-state jobs may reach the 600 s kill; that is a recorded KILL outcome, not
   a missing input. Worst case 3 waves x 600 s = 1800 s < 2400 s cap. No cut rule (plan runtime_projection).
5. **Release tests (Exact, deviation #107 rule).** tests/test_certify32s.py, tests/test_scripts_066.py and tests/test_release_0630.py
   are tooling / API tests on synthetic input or the development seed 10051001, committed before the freeze and frozen. TEST_SUITE_066
   runs once, after the run.
6. **Known risks (Inferred).** GN24_66 needs S24 >= 1 decided and >= C24 - 1; study-064's noise-free certify/32p decided 2 of 6
   2-bit 24-state worlds at 8M (P24 ID+IDF 2), so with 4 seeds C24 = S24 = 0 is plausible and GN24_66 may fail (published as a size
   limit). GEQ66 needs at least 2 finished 24-state pairs; if kills remove them GEQ66 fails and the version is not certified.
   (Correction before the freeze: the first committed text of this item wrongly said 24-state 2-bit worlds had never been decided.)
