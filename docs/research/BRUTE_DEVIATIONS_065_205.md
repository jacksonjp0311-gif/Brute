# Deviation #205 (study-065, v0.62.0): post-run record

Written after the gates (box-local EST, UTC-5, Nov 3 2026). It changes no threshold, seed, cap or gate and no sealed output.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Standing go t133s553 and t139s684.

0. **Framing (kept prominent).** NOISE TEST of the v0.60.0 clique-anchored method: certify/20s (sequential per-bit re-reads,
   a random-walk / SPRT stopping rule) in front of an unchanged certify/20p on 2-bit 20-state worlds at eps 0.10 / 0.20 / 0.30.
   **The main run hit its 2400 s cap and was sealed PARTIAL (21 of 25 jobs). By the frozen gate rule every data gate FAILS
   INCOMPLETE_INPUT: 3 of 13 gates pass (GHOST65, GTEST65, G_PROC65). Status: not certified.** Nothing was relaunched.
1. **Process (Exact; artifact commit / ledger commit).** preregistration_065 1d92afa / 1886575, build_authorization_065 0ffdbe1,
   seedcheck_065 (PASS), build 3903a0b, prefreeze_smoke_065 (PASS, ac9482c), deviation_204 c16fa46, freeze_065 d62bc92 / 68f0228,
   study065_storage.py 28159f1 (the frozen storage file was left out of the build commit; its sha equals the freeze entry),
   main_run_065 340c785 (launched once with nohup at 06:47:39 EST), seal 4e9e46b / run_end_065 a8b1a13, recount e3a5dcb / d431dc1,
   reference 0f5c104 / 8e87302, tests 06f5a2c / a0d259e, api_checks 1154eb4 / b323f80, gates 4c781c6 / fa515ef.
2. **Cap hit and partial seal (Exact).** 21 jobs finished in the first ~6 min (30-74 s each). The four jobs on main seed
   12650105 (C20, S30, S20, S10) never finished; the capwatch killed the run at 07:46:14 EST (2400 s) and sealed partial at
   07:46:20 (SEAL complete false, missing_job_keys = the four 12650105 jobs). The plan's 2400 s cap was enforced as declared.
3. **Stalled executor (Observed; disclosed).** Nothing happened between the partial seal (07:46:20) and a watchdog resume at about
   08:17 EST. Every later step used the sealed bytes as they were.
4. **The 1800 s case kill did not end the 12650105 jobs (Observed; Open).** The case wall guard is checked only between conflict
   chunks (50000 conflicts each). A post-run scratch diagnostic (not gated; /tmp/s65/diag, single process, seed 12650105 C20 run
   again, the seed is already spent) shows the first least-size query alone running thousands of chunks with chunk wall
   growing from 4.4 s to over 8 s within 4 minutes on an idle core; the conflict rate on this world is about 3x slower than
   on the other five and degrades as the run goes on. With 6 workers sharing the host the 8M budget was not reached in 58 min.
   Whether the guard fired late or not at all is Open; see the diagnostic note in v0.63.0's plan.
5. **api_checks launches (Exact; disclosed).** api_checks_065 was first launched without --study (it wrote an
   API_CHECKS_065.json with no fidelity block; uncommitted, moved to /tmp/s65/API_CHECKS_065_nostudy.json), then with the study
   root (crashed before writing anything), then once with results/study-065/main. Only the third run is committed. ghost,
   equiv and threshold are deterministic checks on smoke seeds and matched between the first and third runs.
6. **Ledger slip (Exact).** The first run_end_065 ledger attempt used a directory as the source and errored before writing; it
   was ledgered against main/SEAL.json instead. The seal commit itself was not changed.
7. **What the completed records show (Observed; NOT gated, n = 5 worlds).** On the 5 finished seeds every arm decided the same 5
   (4 ID, 1 IDF); recount PASS on all 21 records (0 mismatches, 0 WRONG, 0 settled-bit errors); every noisy record's inner record
   equals C20's on the same seed (16 of 16); S30 == S30b on 12650101; reference audited 21 of 21 decided records, 0 mismatches,
   20/20 mutations in 24 s; replay fidelity 16/16 exact. Pooled reads vs the fixed-k rule on the same observations:
   S10 21101 vs 104362 (0.20x), S20 44684 vs 203196 (0.22x), S30 118749 vs 561880 (0.21x), all under the 0.35x bar. This is
   the strongest evidence so far that sequential re-reads remove the noise penalty at about a fifth of the read cost, up to
   eps 0.30 at 2 bits, but it is evidence on 5 worlds with one world missing, not a gate pass.
8. **Lesson (Inferred).** Pricing the run on wall time while bounding each case only by conflicts left one hard world able to
   sink the whole study. The next plan must make every case end on a deterministic bound that fits the cap, and must count a
   case that hits it as undecided (IDU), not as missing input.
