# Deviation #199 (study-062, v0.59.0): post-run record

Written after the gates (box-local EST, UTC-5, Nov 2 2026). It changes no threshold, seed, cap or gate and no sealed output.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Standing go t133s553 and t139s684.

0. **Framing (kept prominent).** BACK ON THE HARD PROBLEM: 2-bit readings at 20 states, declared N 20. The tested step was a
   POLICY change (probe-word windows, certify/20w, arm W2) against the budget-matched frozen certify/20b (B2) at B62 = 8M
   conflicts. **It failed: W2 decided 0 of 3, the same as B2. 2-bit readings at 20 states stay Open.**
1. **Process (Exact; artifact commit / ledger commit).** preregistration_062 43d877d, budget_probe_062 afa4f2e / 480c61b,
   build_authorization_062 f9fea49, seedcheck_062 0bafcfd / b6f5bdd, prefreeze_smoke_062 6099c63 (attempt 1 b220fdb, attempt 2
   44ec370, event d2f983b), deviation_198 0a4572a / 144d37e, freeze_062 4f9fbcc (686 files) / 32b2617, main_run_062 b61e881
   (launched once with nohup at 18:08:44 EST, pid 2089976, never relaunched), seal 3a22432 / run_end_062 bbcf67a (sealed
   18:40:19 EST, runner 1894.5 s), recount 69bd25e / b37a0f6, reference 7ced8b5 / aa52ccf, tests 2c3bf0a / dae8f22,
   api_checks 80b4186 / 68b7d11, gates 6e75d3e / eb850a9.
2. **Interrupted tool calls (Observed; disclosed).** Agent sessions were interrupted (about 17:51 and 18:43 EST) and several
   tool calls came back "Aborted". No running process was killed and nothing was relaunched: the prefreeze smoke attempt 2,
   the main run, the official tests (nohup 18:42:32 EST) and api_checks_062 (nohup 18:43:33 EST) each ran exactly once and
   their complete output was committed as-is.
3. **Prefreeze smoke attempt 1 (Observed; already in #198 item 8).** It was killed by the agent's own 220 s shell timeout and
   wrote nothing; attempt 2 ran under nohup and passed. Both are in the ledger.
4. **Stale docstring in frozen tooling (Observed; disclosed, not edited).** scripts/study062_storage.py still shows the usage
   line "python scripts/study061_storage.py pack | restore". The file is frozen, so the text stays; its code packs and
   restores study-062 and that is what the fresh-clone verify runs.
5. **Scratch drafting (disclosed).** This deviation and #198 were drafted in /tmp/s62 before being committed; nothing there is
   a gated input. All tooling is in the repo.
6. **Result (Observed; recount labels).** B2 0/3, W2 0/3 (Wilson 95% [0.00, 0.56] each), W2b 0/2 and identical to W2 on both
   seeds (GDET62 2/2, [0.34, 1.00]). W2 - B2 = 0, discordant pairs 0/0, exact McNemar p = 1.0. WRONG 0 of 8 records
   [0.00, 0.32]. All eight records are IDU (budget spent, ~8.0M conflicts each). B2 reached n_min 19 on all 3 seeds; W2 reached
   n_min 18 on 12620102 and no n_min on 12620101 and 12620103. W2 ran 10-19 rounds vs B2's 21-44 (Inferred: the appended
   windows make each round's SAT calls dearer, so the window policy buys fewer rounds per budget). Wall guard 0, case kill 0.
7. **Small sample (Inferred).** n = 3 (cut from 12 by #198 to fit the 60 min cap). 0/3 does not show W2 never helps (upper
   Wilson bound 0.56); it shows no gain was observed. The probe's one W2 win (58 seed 12530003 at 8M) did not repeat on fresh
   seeds.
8. **Gates (Exact).** 8 of 9 gated pass: GS62_sound, GDET62, GFID62 (vacuous: 0 decided records to replay; equiv and 0 socket
   attempts pass), GHOST62, GS_ref (vacuous: 0 decided, nothing to audit), G_recount, GTEST (135 tests, 14 modules, 12 gated),
   G_PROC. **GW62 fails.** certified_readbits2_N20_windows false; status phrase from the flags: "sound but no 2-bit gain".
   G_RT is checked at release.
9. **Post-seal exploration on sealed seeds (disclosed; not evidence for any 062 gate).** After the seal, scripts/
   diag_clique_063.py rebuilt the sealed traces and measured the apartness clique (greedy 16-18 on the final traces, exact
   maximum 17-18, true states visited 19-20), and scripts/probe_063.py tests two clique-based encoding changes on the spent
   seeds 12620101-03 and 12530003 for plan 063. Both are labelled non-fresh and feed only the plan-063 choice.
10. **Scope (Exact + Inferred).** An ID/IDF is exact only conditional on noise-free readings and a true size at most the
   declared N = 20. Reason (Inferred): a larger machine can copy the true machine on every visited state.
