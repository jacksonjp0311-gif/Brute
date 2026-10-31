# Deviation #173 (study-050, v0.47.0): pre-run declarations

Written before the source freeze (2026-10-31, box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_050 (commit dd1c41f) that the
plan leaves open. It changes no threshold, seed, cap, eps, eps_bar or delta, and no gate. Labels: Exact, Observed, Simulated,
Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_050 (09:33 EDT, plan dd1c41f, ledger 7c7aa33), build_authorization_050 (ledger 2910ecd,
   09:34 EDT, cites James's STANDING GO t133s553, ledger 76b30d5), seedcheck_050 (ledger 18f2bee; SEEDCHECK_050 at d02f816: 42 cases
   24/6/12, 349 prior ranges, 0 overlaps), prefreeze_smoke_050 (ledger 051e85e; result at ff5fbd6). Then source_freeze_050,
   run_start_050, run_end_050, recount_050, reference_050, api_checks_050, tests_050. Lean process. The resume clause is not
   approved: an interrupted run is never relaunched; a partial block is sealed as such.
2. **Caps are the plan's (Exact).** C = 50000 conflicts per chunk; B20 = 4000000 per scale20 case; B12 = 1500000 per control and
   noise12 case; max_chunks None on every arm except as below; family_bound 20 (scale20) and 12 (control, noise12). Guards 30 s per
   chunk and 600 s per case, as #171 item 3; any firing fails GDET50 / GQB25.
3. **The re-read question is settled: the frozen generators do NOT allow a re-read (Exact, from code).** worlds_026.flips fixes one
   flip pattern per reading index t of a precomputed trajectory, and brute_study_033.StepWorld has only reset() / step(), noise-free;
   neither can return a second, independently noisy reading of the same state without acting. By the plan's own rule
   (design.reread_assumption) a new module was added before any 050 seed was used: experiments/worlds_050.py (commit c0929fc),
   NoisyStepWorld. reset() / step(a) move the hidden state; read() returns the current emission with each of its S_BITS bits
   flipped independently with probability eps, never moves the state, and draws flips from random.Random seeded by (seed, eps, tag
   50), independent of the hidden truth. scale20 comes from the frozen worlds_047; control and noise12 hidden machines from the
   frozen worlds_026 'scale12' generator (the plan's "clean 12-state worlds"). No frozen file is edited. The iid-flip model is an
   assumption about the world (Inferred), not something the run tests.
4. **k rule (Exact; stated more strongly than the plan).** The plan writes T exp(-2k(1/2-eps_bar)^2) <= delta with T the number of
   observations; T is not known in advance, so certify/16n uses the anytime form: k_t is the smallest odd k with
   2 exp(-2k(1/2-eps_bar)^2) <= delta 6/(pi^2 t^2) for observation t (t = 1 is the initial reading). Summed over t the per-observation
   bound is <= delta for any T (Exact, sum 1/t^2 = pi^2/6). The factor 2 is the union over the S_BITS = 2 bits of a reading, each
   bit's majority of k iid reads wrong with probability <= exp(-2k(1/2-eps)^2) <= exp(-2k(1/2-eps_bar)^2) when eps <= eps_bar
   (one-sided Hoeffding; Exact under the iid model).
   eps_bar 0.10, delta 0.001: k_1 = 27, k_10 = 41, k_100 = 55, k_1000 = 69, k_5000 = 79. Every k_t >= the plan's T-form value for
   T <= t (Exact), so the plan's guarantee is implied.
5. **Noise arms (Exact).** API16N and API16N_b: eps 0.05, anytime k, same noise seed on both passes (so GDET50 compares
   byte-identical canon16n). API16N_c (part c): eps 0, reads 1 on the 6 control traces; GCOMPAT16N requires canon16e(API16N_c) byte-
   equal to the main control API16E record. Per-bit majority errors on the prefix raise a VerificationError ('API16D prefix masks
   differ') inside the frozen 047 prefix check; the runner catches it and records label WRONG, stop 'majority_error' (counted as WRONG
   by GN12_sound; Exact). Active-phase majority errors are counted in majority_errors and the recount flags any nonzero count.
   The arm field 'delta' keeps its 047 meaning (family-bound offset, None); the majority failure probability is 'noise_delta'
   (renamed at 354e688, before any 050 main seed was used, because the 047 recount checks 'delta'; Exact).
6. **Fidelity for API16N (Exact).** api_checks_050 replays each API16N record through a fresh Certifier16N, rebuilding the readings
   from the recorded vote vectors (k_t reads with the recorded per-bit counts); exact = byte-equal canon16n. API16E records replay
   through Certifier16E as in 049.
7. **Reference (Exact).** run_reference_050 audits every decided record (scale20, control, noise12 by both arms; part c is recounted
   and compat-checked, not audited) against the clean hidden truth at its family bound, budget 2400 s, 20 mutations. A
   majority_error record has no extra_acts; the frozen 047 view() would raise on it. Accepted risk (Inferred: probability of a
   prefix majority error <= delta = 0.001 per case, the record is then WRONG and fails GN12_sound regardless).
8. **Projection and cut (Inferred; results/diag-050/PREFREEZE_SMOKE_GATES_050.json, commit ff5fbd6).** Plan runtime_estimate: per job
   worst min(600, B/r_min + 10) s, r_min = min(slowest smoke rate, declared): scale20 min(10449.2, 8766) = 8766/s -> 466.3 s;
   12 states min(13011.0, 6716) = 6716/s -> 233.3 s (controls and part c by the same rule, more conservative than the plan's "about
   60 s"). Worst-case LPT on 8 workers: (N12B 12, N20B 12) 3498.3 s; (6, 12) 3264.9; (6, 6) 2799.0. 3498.3 <= 3600, so **no cut:
   N20B = 12, N12B = 12**, 78 main jobs. The runner's values match (cut_consistent true). The projection script's rates were set to
   the plan's declared 8766/6716 before the scale20 smoke records finished (an earlier draft used 049's 3528/s; Exact, diff at ff5fbd6).
9. **Smoke (Observed, never gated, never tuned).** A first smoke launch (09:46 EDT) was stopped after 10 of 14 jobs because the
   runner wrote 'delta' on noise arms (item 5); it was moved aside, not used. The second smoke (09:51-09:59 EDT, 14 jobs): 0 guard
   firings, determinism 6/6, part c compat 2/2, majority errors 0; scale20 11810001 IDU at 4000910 conflicts, 11810002 ID at 2412828;
   controls IDF / AMB; noise12 ID / ID. Reference on smoke: 10 decided, 10 audited, 0 mismatches, 20/20 mutations, 469 s.
10. **Gates added or read (Exact).** GTI: SEEDCHECK_050 PASS and its sha in FREEZE_050. GTEST added: gated modules of
   run_tests_0470 pass. G_PROC: ledger subsequence preregistration, build_authorization, seedcheck, prefreeze_smoke, source_freeze,
   run_start, run_end, recount, reference, api_checks, tests (all _050) in commit order. GHOST50: closures of certify14/16/16d/16e
   unchanged (shas against FREEZE_047 / FREEZE_049), the only newly imported module brute.api.certify16n, 0 socket attempts.
11. **Open.** Whether iid flips hold on any real host; N-freedom; whether B20 4M decides scale20 broadly (smoke 1/2).
