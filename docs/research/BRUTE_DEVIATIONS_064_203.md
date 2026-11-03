# Deviation #203 (study-064, v0.61.0): post-run record

Written after the gates (box-local EST, UTC-5, Nov 3 2026). It changes no threshold, seed, cap or gate and no sealed output.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Standing go t133s553 and t139s684.

0. **Framing (kept prominent).** SIZE TEST of the v0.60.0 clique-anchored method: certify/32p (certify/20p with the declared
   bound allowed up to 32) on fresh 2-bit 24-state worlds at declared N 24, plus a certify/20p replication at N 20 checked by
   the new clique-pinned independent reference. **All 11 gated pass. Status: "certified (read_bits 2, N <= 24, clique-anchored)".**
   The headline bar was modest by design (P24 >= 2 of 6) and was met exactly: 2 of 6.
1. **Process (Exact; artifact commit / ledger commit).** capability_probe_064 66ad164, diag_ref_064 1c57422 / a890ae2,
   preregistration_064 ab4e77d / 248c5cd, build_authorization_064 5ead5ee, seedcheck_064 b6aebbf / 72f806a, build e4354aa,
   prefreeze_smoke_064 attempt 1 CRASHED (tooling bug in api_checks_064, fixed e330a6a, ledger 51ce907), attempt 2 652e4d4 /
   4b041d8, deviation_202 30765f5 / fcbe8ad, freeze_064 27c30fc / bd23702, main_run_064 d3a2d9d (launched once with nohup at
   04:17:17 EST, never relaunched), seal 8174302 / run_end_064 9be18c3, recount 8d50e81 / 39e3df8, reference 7e683f3 / db81aa2,
   tests b2a8a16 / d946f27, api_checks 9dca184 / 7ca393e, gates 1b8229b / c759bd4.
2. **Stalled executor (Observed; disclosed).** Prefreeze attempt 2 passed at about 02:12 EST but was not committed until a
   watchdog found the stall at 04:15 EST and resumed. Its output was committed as produced; it was not rerun.
3. **Main run time (Observed).** 15/15 jobs, 04:16:58-04:48:55 EST: 1917 s from launch (runner-internal 1826 s), above the
   LEAN ~30 min target but under the 2400 s MAIN_CAP_S hard cap; no partial seal was needed.
4. **B24 case kill (Observed; reported, not gated).** The time-capped control B24 (frozen certify/32b) on 12640202 hit the
   1800 s case kill (22 case-guard events) at 7.81M conflicts; plan 064 declares a B24 firing as disclosed, not a GDET64 failure.
   No P24, P20 or P20b record had a guard firing.
5. **Reference wrong-path launch (Exact; disclosed).** run_reference_064 was first launched at 04:49 EST with the study root
   (results/study-064) instead of results/study-064/main; it exited at once with no audit work and no output file. It was
   relaunched once with the correct path; that single run is the committed REFERENCE_064 (6/6 audited in 19 s).
6. **.gitignore (Exact).** The raw RESULTS.json / SCIENTIFIC.json / CHECKPOINT.jsonl of study-064 were not yet ignored; three
   .gitignore lines were added in the seal commit 8174302 (packed .gz files are tracked, as for 045-063).
7. **Result (Observed; recount labels).** P24 2/6 (12640204 ID at 2.82M conflicts, 12640206 IDF at 3.54M) [Wilson 95% 0.10,
   0.70]; the four misses are IDU at 8M with n_min 21-23. B24 0/2 (time-capped). P20 4/6 (3 ID, 1 IDF) [0.30, 0.90], replicating
   v0.60.0's 4/6; P20b identical to P20 on 12640101 (both IDU). WRONG 0 of 15. Reference 6/6 decided audited, 0 mismatches,
   20/20 mutations, complete in 19 s (GS_ref63's failure is fixed). XREF 1166 checks, 0 disagreements.
8. **Small sample (Inferred).** n = 6 per arm. The certification is a soundness statement (every ID/IDF exact conditional on
   noise-free readings and true size <= N), not a coverage claim: 4 of 6 24-state worlds remain undecided at 8M.
