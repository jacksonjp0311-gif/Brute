# Deviation #202 (study-064, v0.61.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 3 2026). It fixes readings of experiments/BRUTE_PLAN_064.json
(plan/v0.61.0, ledger preregistration_064 at ab4e77d; the plan is locked and not amended) and declares the plan's own cut rule as
applied. It changes no cap (C 50000, B 8000000, K 400, read_bits 2, declared N 24 / 20, node cap 200000), worker count (6), case
kill (1800 s), main-run cap (2400 s) or job order rule. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** A SIZE TEST of the v0.60.0 method (clique-anchored symmetry breaking), first of the 2-3 versions
   James agreed on (Nov 2, 20:10 EST: larger sizes and noise, good ideas over budget bumps). certify/32p is certify/20p with the
   certify/32b bound change only; B is unchanged at 8M. The probe decided 1 of 4 sealed 24-state worlds, so GP24_64 (2 of 6) is
   roughly a coin flip. The new piece is the clique-pinned independent reference (experiments/v0610_reference.py), the fix for
   the GS_ref63 failure. Claims stay conditional on the declared N.
1. **Process (Exact, ledger note times, EST).** capability_probe_064 (00:32:28, exploratory, sealed study-061 seeds only),
   diag_ref_064 (00:32:30, exploratory, sealed 063 copy), preregistration_064 (00:33:31), build_authorization_064 (00:33:32;
   standing go t133s553 and t139s684), seedcheck_064 (00:44:26, PASS), tooling e4354aa (21 tests OK), prefreeze_smoke_064_attempt1
   (01:02:51, CRASHED, tooling bug fixed at e330a6a), prefreeze_smoke_064 (attempt 2 PASS; run finished 02:12:38, committed and
   ledgered 04:15:58), then deviation_202, freeze_064, main_run_064 (once, nohup, never relaunched).
2. **Disclosures (Observed).** (a) The plan was drafted by the agent under the standing go and not reviewed by the user. (b) The
   capability probe was launched (20:54 EST Nov 2) before its script was committed and the reference diagnostic was run (00:20 EST)
   before its commit; their recorded script shas equal the committed files. (c) Prefreeze attempt 1 crashed in
   api_checks_064.equiv (a bytes canonical dump was hashed with .encode()); the one-line fix e330a6a was ledgered with attempt 1;
   recount and the smoke reference had passed in attempt 1. (d) The executor stalled between 02:12 and 04:15 EST; attempt 2's
   output was untouched in that gap (mtime 02:12:38) and nothing was rerun. (e) No main seed (12640101-06, 12640201-06) has been
   run by any tool; smoke used 12640301-02, the no-network check uses 12640303.
3. **Cut decision (Observed + Inferred), the plan's own rule.** Projection (Inferred, PREFREEZE_SMOKE_GATES_064): every job = 1.25 x
   the slowest of its arm (probe at B 8M for P24/B24, sealed 063 P2 walls for P20/P20b), B24 capped at 1830 s, LPT on 6 workers,
   cap 2400 s. (N_P20B, N_B24) = (2, 3) 3120.4 s, (1, 3) 2903.6 s, **(1, 2) 2583.6 s: the cut is exhausted and still above the
   2400 s cap under the pessimistic projection. Declared: N_P20B = 1 (12640101), N_B24 = 2 (12640201-02), N_SEEDS = 6; 15 jobs.**
   The realistic makespan (Inferred) is about 1850-2100 s, dominated by the two B24 case kills. If the run reaches 2400 s it is
   sealed partial and every data gate fails INCOMPLETE_INPUT (published, never relaunched). The runner was set to (1, 2) at
   e4354aa before any prefreeze run; attempt 2 confirmed cut_consistent.
4. **Gates at the cut (Exact, plan formulas).** GP24_64: P24 ID+IDF >= 2 of 6; GP20_64: P20 ID+IDF >= 3 of 6; GDET64: P20 ==
   P20b on 1 of 1 seeds and no case kill in P24, P20 or P20b. CIs are wide (2/6 Wilson 95% [0.10, 0.70]).
5. **Stop and kill (Exact).** Conflict-only stop, no hook; per-case kill 1800 s, 30 s per-call wall guard. A firing in P24, P20 or
   P20b fails GDET64 and is published; one in B24 is reported (expected: B24 needs about 1800-2100 s at 8M on the probe), so B24
   records may end undecided before 8M as a time-capped control.
6. **G_PROC64 (Exact rule).** preregistration_064 < build_authorization_064 < seedcheck_064 < prefreeze_smoke_064 < deviation_202
   < freeze_064 < main_run_064 as a ledger subsequence with parseable non-decreasing note times.
7. **Release tests (Exact, deviation #107 lesson).** tests/test_release_0610.py and tests/test_scripts_064.py are tooling tests
   committed before the freeze (e4354aa) and frozen; they test the release tooling on synthetic input, not the results. No test
   that reads study-064 results is written or committed before the main run ends. TEST_SUITE_064 is run once, after the run.
8. **Smoke (Observed, not evidence).** 12640302 (scale20): P20 and P20b ID, identical, 1,010,030 conflicts, 27.8 / 28.0 s, clique
   19. 12640301 (scale24): P24 IDU/unknown at 2M (233.2 s, clique 14), B24 IDU/unknown (214.7 s). Wall guard 0.
9. **Known risks (Inferred).** P24 may decide fewer than 2 (GP24_64 fails; then "certified (read_bits 2, N <= 20,
   clique-anchored)" is still possible if every other gate passes). The pinned reference shares the pinning idea with certify/20p
   (not code); GXREF64 is the mitigation.
