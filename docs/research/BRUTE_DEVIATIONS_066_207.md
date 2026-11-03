# Deviation #207 (study-066, v0.63.0): post-run record

Written after the gates (box-local EST, UTC-5, Nov 3 2026). It changes no threshold, seed, cap or gate and no sealed output.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Standing go t133s553 and t139s684.

0. **Framing (kept prominent).** Third and last of the 2-3 test versions James agreed on (noise AND size). No new reasoning power:
   certify/20p and certify/32p are unchanged, so the noisy arms can only match the noise-free ones. **All 14 gated criteria pass;
   status phrase from the flags: "certified (read_bits 2, N <= 24, iid bit noise eps <= 0.30, delta 0.001, sequential re-reads)".**
   The 24-state part rests on thin evidence: 1 of 4 worlds decided in either arm, 2 of 4 killed at 600 s, 2 equality pairs.
1. **Process (Exact; artifact commit / ledger commit).** preregistration_066 3954159, build_authorization_066 aba356b, seedcheck_066
   198d7a6 / bc07682, build c543ba0, prefreeze_smoke_066 3877950 / 44c4f57, deviation_206 71a4f6a / ce38811 (item 6 corrected
   02ae2dc before the freeze), freeze_066 2578574 / 0df1558, main_run_066 cd7afdd (launched once 10:13:15 EST, setsid nohup, pid
   2405899, never relaunched), seal 6a62a2d / run_end_066 ecfe9cb (sealed complete 10:29:52 EST, runner 996.2 s), recount 0eeacdf /
   0e6f46b, reference 6092a86 / 8125e7b, tests 7e09cdf / 9506b3b (once, nohup 10:31:54 EST), api_checks 056dc23 / a1cbb93 (once,
   nohup 10:33:44 EST, with --study), gates c56cff2 / 80f30c3.
2. **Two agent sessions (Observed; disclosed).** A watchdog-resumed session (executor-A) built, froze and launched the run; a second
   session (executor-B) attached at 10:15 EST. They coordinated through the scratch file /tmp/s66/STATE.txt: B claimed the post-run
   steps, A yielded at 10:30:56 EST. Before yielding, A added the three study-066 raw-file lines to .gitignore (committed with the
   seal, 6a62a2d) and ran study066_storage pack once; it refused (gz already written by B) and changed nothing. No ledger entry, tag
   or run was duplicated. A wrote a scratch plan-067 suggestion in /tmp/s67 (not a gated input).
3. **.gitignore omission (Observed).** The build commit did not add the study-066 ignore lines; they were added at seal time, as in
   earlier studies' seal commits. .gitignore is not in the source freeze.
4. **Result (Observed; recount labels).** C20 4/6 and S30 4/6 (Wilson 95% [0.30, 0.90] each); S30b equals S30 on 12660101 (1/1).
   C24 1/4 and S24 1/4 ([0.05, 0.70]); 12660202 decided in both, 12660204 budget-spent in both (n_min 20), 12660201 and 12660203
   KILL at 600 s in both arms. Every finished noisy record equals its control (GEQ 9/9: 6 at 20 states, 2 at 24 + S30b). 0 settled-bit
   errors over 2630 noisy observations. Reads 147003 vs 690503 fixed-rule (0.213x) in S30, 49644 vs 239137 (0.208x) in S24. WRONG 0
   of 17 finished records. Reference audited 11/11 decided records, 0 mismatches, 20/20 mutations, 9.0 s. Fidelity 6/6 exact.
5. **Kills (Observed + Inferred).** 4 of 21 jobs (all at 24 states) were killed at the 600 s job kill; the run still ended at 996 s,
   well inside the 2400 s cap, so the liveness fix from #205 worked. The killed worlds are undecided, not failures of soundness;
   with them the 24-state coverage is 1/4 (Inferred: the 24-state solve is wall-bound on this box, not read-bound).
6. **Small sample (Inferred).** n = 6 at 20 states and n = 4 at 24 states. The certification is the plan's rule applied to these
   gates, conditional on noise-free-except-iid-flips readings and true size <= the declared bound; it does not show broad 24-state
   coverage (upper Wilson bound 0.70, lower 0.05).
7. **Scope (Exact + Inferred).** An ID/IDF is exact only conditional on every settled reading being correct (probability >= 1 - delta
   under iid flips with eps <= eps_bar) and a true size at most the declared N. Reason (Inferred): a larger machine can copy the true
   machine on every visited state.
8. **Drafting (disclosed).** This deviation, the release text and plan 067 were drafted by the agent under the standing go, not
   reviewed by the user.
