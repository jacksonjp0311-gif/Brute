# Deviation #204 (study-065, v0.62.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 3 2026). It fixes readings of experiments/BRUTE_PLAN_065.json
(plan/v0.62.0, ledger preregistration_065 at 1d92afa; the plan is locked and not amended). It changes no cap (C 50000, B 8000000,
K 400, read_bits 2, declared N 20, node cap 200000, delta 0.001), arm noise (eps / eps_bar 0.10/0.15, 0.20/0.25, 0.30/0.35),
worker count (6), case kill (1800 s), main-run cap (2400 s) or job order. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** A NOISE TEST of the v0.60.0 method, second of the 2-3 versions James agreed on (Nov 2, 20:10 EST:
   larger sizes and noise, good ideas over budget bumps). The SAT side is unchanged (certify/20s wraps an unchanged certify/20p), so
   this version cannot decide more worlds than noise-free certify/20p; the claim under test is that per-bit sequential re-reads
   remove the noise penalty at a fraction of the fixed-k read cost, with the same delta 0.001 guarantee, up to eps 0.30 at 2 bits.
1. **Process (Exact, ledger note times, EST).** preregistration_065 (05:04:07), build_authorization_065 (05:04:08; standing go
   t133s553 and t139s684), seedcheck_065 (06:18:39, PASS), build commit 3903a0b (new tests: certify20s 8, scripts_065 11,
   release_0620 12, all OK), prefreeze_smoke_065 (PASS, ledgered at ac9482c), then deviation_204, freeze_065, main_run_065 (once,
   nohup, never relaunched).
2. **Disclosures (Observed).** (a) The plan was drafted by the agent under the standing go and not reviewed by the user.
   (b) The v0.61.0 release-closing ledger entries (release_0610 c8a3911, fresh_clone_verify_064, handoff_released_064) were written
   after preregistration_065 because v0.61.0 finished releasing after plan 065 was pre-registered. release_0610 names c8a3911, which
   is not a descendant of the 065 commits, so the 065 commit-order chain (scripts/make_freeze_065.entries, verify_release_0620.chain)
   excludes exactly these three events. G_PROC65 needs only the 065 subsequence with non-decreasing note times, which holds.
   (c) A sanity run of the runner at B 300k on smoke seed 12650301 (S30 and C20 only, IDU at about 13 s) was made while building
   the runner, before the smoke; smoke seeds are never gated. (d) No main seed (12650101-06) has been run by any tool; smoke used
   12650301, api_checks use 12650301-02 (equivalence) and 12650303 (no-network run).
3. **New definitions (Exact).** certify/20s: threshold m_t = smallest m with 2 r^m/(1+r^m) <= delta 6/(pi^2 t^2), r =
   eps_bar/(1-eps_bar) (per-bit random-walk / SPRT stopping; the 2 bits share the observation's delta share by a union bound);
   settle() = first read at which |#1 - #0| >= m_t for each bit; observe() accepts only an exact stopping sequence (every bit settled,
   the last read settling the last bit); READ_CAP 100000. The recount checks thresholds with exact fractions and a pi^2 bracket
   (scripts/recount_065.m_exact; agreement on t 1..500 at 0.15, 0.25, 0.35 and 1500 checks in api_checks_065).
   Fixed-rule counterfactual = sum over the record's observations of certify20n.reads_for(t, eps_bar, delta, 2).
4. **Cut decision (Observed + Inferred), the plan's own rule.** Projection (Inferred, PREFREEZE_SMOKE_GATES_065): each arm's n jobs
   take the n largest sealed study-064 P20 case walls (427.6, 303.5, 251.8, 205.2, 50.4, 46.8 s) times 1.25, LPT on 6 workers:
   (N_S20, N_S10) = (6, 6) 1170.3 s <= 2000 s, so **no cut: 25 jobs (6 C20, 6 S30, 6 S20, 6 S10, 1 S30b)**. cut_consistent true.
5. **Gates (Exact, plan formulas).** GN65: S30 ID+IDF >= 3 of 6 and >= C20 - 1 (headline, the only soft gate); GN_low65: S10 and
   S20 each >= C20 - 1; GREAD65: pooled reads <= 0.35 x fixed rule in each of S10, S20, S30; GMAJ65: recounted settled-bit errors
   0; GEQ65: every noisy record's read-free canonical record equals C20's on the same seed; GDET65: S30 == S30b on 12650101 and no
   case kill. Status phrases per the certification rule (make_gates_065.status_phrase).
6. **Release tests (Exact, deviation #107 lesson).** tests/test_release_0620.py, tests/test_scripts_065.py and
   tests/test_certify20s.py are tooling / API tests committed before the freeze (3903a0b) and frozen; they use synthetic input or
   the development seed 10051001, never study-065 results. TEST_SUITE_065 is run once, after the run.
7. **Smoke (Observed, not evidence).** 12650301 at B 2M: every arm ID, 1,624,044 conflicts, about 72 s per record; every noisy
   record equal to C20 read-free; reads S10 5295 vs 26061 fixed (0.20), S20 11276 vs 50767 (0.22), S30 29845 vs 140403 (0.21);
   0 settled-bit errors; S30 == S30b. Wall guard 0. Synthetic gate run: all data gates pass, reproduce byte-for-byte.
8. **Known risks (Inferred).** Decisions are bounded by certify/20p (study-064 P20 decided 3 of 6 at 8M on other seeds), so GN65
   (3 of 6) is near a coin flip on fresh seeds; a GN65 failure with all hard gates passing still yields the eps <= 0.20 phrase.
   A settled-bit error is possible in principle (bounded by delta 0.001 per record) and would fail GMAJ65 and GEQ65, published.
