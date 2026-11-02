# Deviation #192 (study-059, v0.56.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 2 2026). It fixes readings of experiments/BRUTE_PLAN_059.json
(plan/v0.56.0, commit 37aea67, ledger preregistration_059; no amendment; the plan is locked) that the plan leaves open. It changes
no threshold, seed, cap (C 50000, B 2000000, K 400), worker count, job order or gate. Labels: Exact, Observed, Simulated,
Inferred, Rejected, Open.

0. **Framing (kept prominent).** This study is a **target change**: 4-bit readings at 20 states, now read through iid bit noise
   (eps <= eps_bar) and a majority front end (certify/20n over the frozen certify/20b). It is not progress on the 2-bit problem.
   **2-bit readings at 20 states stay Open whatever happens.** GATES_059 carries this sentence as its framing field.
1. **Process (Exact).** preregistration_059 (37aea67, 12:09:51 EST), build_authorization_059 (f5bc938, 12:10:48 EST; standing go
   t133s553 and t139s684), seedcheck_059 (f7b0c41, ledger 3071a28, 12:21:25 EST; PASS, 15 negative controls), tooling
   f372d22 .. 6d98166, prefreeze smoke attempt 1 (f506b4c, ledger 53502e9; also prefreeze_smoke_059, e88fc60), then
   deviation_192, freeze_059, main_run_059, run_end_059, recount, reference, api_checks, tests, gates, #193. The main run goes
   once with nohup and is never relaunched. Times are ledger note times, not process start times.
2. **Disclosure: build order (Observed).** certify20n.py, worlds_059, brute_common_059 and brute_study_059 (f372d22 .. a6d510d)
   were drafted while seedcheck_059 was running and committed after it; during development one non-fresh test ran on sealed
   study-053 seed 12530002 (not a study-059 seed). Neither touches a study-059 main or smoke seed. No main seed (12590001-12)
   has been run by any tool before the main run; 12590053 is used only by the no-network run.
3. **G_PROC event names (Exact rule).** preregistration_059 < build_authorization_059 < seedcheck_059 < prefreeze_smoke_059 <
   deviation_192 < freeze_059 < main_run_059, as a subsequence of the ledger.
4. **k rule (Exact).** Observation t (initial reading t=1) is read k_t times, k_t the least odd k with
   read_bits*exp(-2k(1/2-eps_bar)^2) <= delta*6/(pi^2 t^2); delta 0.001. Union bound over bits and observations gives majority
   errors <= delta total under the noise model (Inferred). C4 uses k=1 and no noise.
5. **Truth labels (Exact rule).** Labels are scored against the clean world. A decided model not bisimilar to the truth is WRONG.
   Stop 'none' (the front end refused to continue) is NOFIT: a refusal, never WRONG, never decided. The reference does not audit
   NOFIT records (it maps them to 'unknown'); none occurred in smoke.
6. **GMAJ59 (Exact rule).** Sum of maj_errors over every observation of N4_05, N4_10, N4_10b equals 0 (recount values if
   G_recount passes). NEG4 majority errors are reported only.
7. **GFID59 / GHOST59 (Exact rule; supersets, disclosed).** GFID59: api_checks_059 equiv (a) 20n reads=1 equals 20b at read_bits
   2/3/4 on 6 small worlds each, (b) 20n read_bits 2 equals 16n on eps 0.05 reads on 6 worlds, (c) 12 constructor and 5 observe
   refusals; plus the no-network run and an exact replay of every decided main record (C4 via 20b; noisy arms via 20n with the
   noise regenerated from the seed). GHOST59: closure scan of brute.api.certify20n, frozen sha of certify14/16/16d/16e/16n/20b
   unchanged against FREEZE_058, and a no-network 20n loop on seed 12590053 (smoke: 0 socket attempts, label ID).
8. **GS_ref (Exact rule).** REFERENCE_059 (random.Random(590), m = 16 per family), budget 1800 s on 8 workers; the noisy arms are
   audited on their majority trace; a NEG4 WRONG is counted as a misfire in the report, not a gated mismatch.
9. **Flags and wording (Exact rule).** certified_noisy_readbits4_N20 iff every gate in GATES_059 passes; sound_not_certified_noisy
   iff every gate except GN_keep59 and/or GN05_59 passes. status_phrase: "certified (read_bits 4, iid bit noise eps <= eps_bar
   <= 0.15, N <= 20)", "sound but not certified", or "not certified, no certification status (failing gates: ...)". Claims are
   conditional on the declared N (Inferred reason: a larger machine can copy the true machine on every visited state).
10. **Cut decision (Observed + Inferred).** Smoke (12590051-52, 10 jobs, 8 workers): slowest rate 24636 conflicts/s, worst per
    job 91.2 s, worst projected run 729.5 s <= 3300 s. **No cut: N59 = 12.** Smoke records (Observed, not evidence for any gate):
    every arm ID on both seeds with identical masks, rounds and conflicts (1193197 and 1806560); majority errors 0 in every arm,
    NEG4 included; reads_total 203/234 (C4) vs 11273-17176 (noisy).
11. **Known risk (Observed, published now).** NEG4 (eps 0.25 against eps_bar 0.10) had 0 majority errors in smoke, so the negative
    control may show no WRONG; that is a weak control at this k, and it will be published as is.
