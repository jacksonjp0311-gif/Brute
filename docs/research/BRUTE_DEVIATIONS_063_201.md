# Deviation #201 (study-063, v0.60.0): post-run record

Written after the gates (box-local EST, UTC-5, Nov 2 2026). It changes no threshold, seed, cap or gate and no sealed output.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Standing go t133s553 and t139s684.

0. **Framing (kept prominent).** Still the hard problem: original 2-bit readings, 20 states, declared N 20. The tested step was an
   ENCODING change (certify/20p: the exact maximum apartness clique is pinned to states 0..|C|-1 and re-pinned when it grows),
   against the budget-matched frozen certify/20b (B2) at B 8M conflicts. **The headline GP63 PASSES: P2 decided 4 of 6 fresh
   worlds, B2 decided 1 of 6.** But **GS_ref63 FAILS**: the independent CNF reference audit did not finish inside its
   pre-registered 1800 s, so certify/20p gets **no certification status** under the plan's status_wording_rule.
1. **Process (Exact; artifact commit / ledger commit).** diag_clique_063 4f6718c / 5137643, capability_probe_063 0dd7d4c /
   f25b5b3, preregistration_063 55433b5 / 676c574, build_authorization_063 22f6bf4, seedcheck_063 2f07631 / 02cbb28 (attempt 1
   FAIL published e62fa8d), prefreeze_smoke_063 f944504 / 0f5c47f, deviation_200 88cd0dd / b854da5, freeze_063 3b38471 / ab22527,
   main_run_063 fbd42d0 (launched once with nohup 19:43 EST, pid 2153785, never relaunched), seal 9b0eb06 / run_end_063 1efff3d
   (sealed 20:19 EST), recount d9b485b / 4b13db4, reference 2b29949 / 39c0b31, tests 9d53014 / cb0278f, api_checks a5d52f1 /
   44c14f8, gates 1534a3a / 51a787d.
2. **Interrupted agent session (Observed; disclosed).** The executor driving the run was interrupted at about 20:08 EST while the
   main run was at 9/14 jobs. The run process was not touched; a new executor waited for it to exit on its own. Nothing was
   relaunched or resumed; every later step (recount, reference, tests, api checks, gates) ran exactly once.
3. **Result (Observed; recount labels).** P2 4/6 ID (12630101-04) [Wilson 95% 0.30, 0.90]; B2 1/6 ID (12630104) [0.03, 0.56].
   P2 - B2 = 3; discordant pairs P2-only 3, B2-only 0; exact two-sided McNemar p = 0.25 (n = 6 is too small for p < 0.05). P2b
   identical to P2 on 2/2 (GDET63 [0.34, 1.00]). WRONG 0 of 14 records. P2's two misses (12630105, 12630106) are IDU at 8M with
   n_min 19. P2's decided records used 1.21-2.01M conflicts and 44-67 s each; B2's one decision used 2.22M and its five misses
   used the whole 8M at 1560-2100 s each (Observed walls, informational). Wall guard 0, case kill 0.
4. **GS_ref63 failure (Exact; published, not rerun).** run_reference_063 ran once on 8 workers with the plan budget 1800 s. It
   audited 2 of the 7 decided records (B2 12630104 and P2 12630104, 240-251 s each) with 0 mismatches and passed 20/20
   mutations, but 5 decided records (P2 12630101-03, P2b 12630101-02) were not audited and 7 records were not reached, so the
   gate's completeness clause fails. Inferred cause: the independent reference encoding has no clique anchoring, so it pays the
   same pigeonhole-style cost that slows B2; it is the unanchored solver re-proving what the anchored one proved. The replay
   fidelity check (GFID63) DID replay all 7 decided records exactly against the sealed RESULTS sha, and the recount found 0
   wrong labels against the true machines, so there is no evidence of an unsound certificate, only an unfinished independent audit.
5. **Status (Exact).** 8 of 9 gated pass (GS63_sound, GP63, GDET63, GFID63, GHOST63, G_recount63, GTEST63, G_PROC63);
   GS_ref63 fails. certified_readbits2_N20_clique false; sound_no_2bit_gain false (it requires every gate except GP63).
   status_phrase from the flags: "not certified, no certification status (failing gates: GS_ref63)". G_RT is checked at release.
6. **Small sample (Inferred).** n = 6 (cut from 8 by #200 to fit the cap). The gain is the first observed 2-bit 20-state gain over
   the frozen solver in this project's studies, but it rests on 6 worlds and McNemar p = 0.25.
7. **Pre-release exploration for plan 064 (disclosed; not evidence for any 063 gate).** After the gates, scripts/probe_064.py
   (sha256 0f1bd4e7717b...) was launched at 20:54 EST on spent seeds (study-061 24-state seeds 12610101-04 with their original
   2-bit emissions) to test clique anchoring at 24 states for plan 064. It is uncommitted at release time and will be committed
   with its sha on plan/v0.61.0.
8. **Scratch drafting (disclosed).** Notes and helper shell lines live in /tmp/s63; nothing there is a gated input.
9. **Scope (Exact + Inferred).** An ID/IDF is exact only conditional on noise-free readings and a true size at most the declared
   N = 20. Reason (Inferred): a larger machine can copy the true machine on every visited state.
