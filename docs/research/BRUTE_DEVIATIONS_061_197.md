# Deviation #197 (study-061, v0.58.0): post-run record

Written after the gates (box-local EST, UTC-5, Nov 2 2026). It changes no threshold, seed, cap or gate and no sealed output.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open. Standing go t133s553 and t139s684.

0. **Framing (kept prominent).** STILL A **TARGET CHANGE**: 4-bit random readings at declared N 24, now at a 24M conflict
   budget (B61) instead of 8M. It says nothing new about the original problem: **2-bit readings at 20 states stay Open.**
1. **Process (Exact; artifact commit / ledger commit).** preregistration_061 359ae41 / 8cfc3c4, budget_probe_061 d1bd376 /
   d54fcf5, build_authorization_061 00a8cfb, seedcheck_061 85fcae7 / 94a9fa5, prefreeze_smoke_061 d1d7dda (attempt 1 42a150c,
   event 71c8fff), deviation_196 f64f6dc / 6ae8c60, freeze_061 4b2c182 (654 files) / 5a56eb8, main_run_061 b05153d (launched
   once with nohup at 16:00:54 EST, pid 2010248, never relaunched), seal 61ec5eb / run_end_061 0c51e74 (sealed about 16:22 EST,
   runner 1316.2 s), recount a45224a / bad4193, reference 4e3806c / 472e432, tests 1e69713 / 6849401, api_checks 4cbf2e7 /
   29ce71c, gates ccfc49f / 727df07.
2. **Interrupted tool calls (Observed; disclosed).** Two agent sessions were interrupted (about 15:49 and 16:31 EST). A
   multi-commit loop and a sleep-only call came back "Aborted". No running process was killed and nothing was relaunched:
   the main run, the official tests (nohup 16:27:35 EST) and api_checks_061 (nohup 16:31:00 EST, exited by 16:54:57 EST)
   each ran exactly once and their complete output was committed as-is.
3. **Stale docstrings in frozen tooling (Observed; disclosed, not edited).** scripts/verify_release_0580.py line 3 still says
   "version 0.57.0" (the code checks VERSION = '0.58.0'); scripts/make_gates_061.py says it was "built from
   scripts/make_gates_061.py" (meant 060) and its GN24_61 line says ">= 10 of n24" while the code and GATES_061 use the #196
   scaled rule ceil(10 n24 / 12) = 5 of 6. Both files are frozen, so the text stays; code behaviour is what is gated.
4. **Scratch drafting (disclosed, as in #196).** Tooling and the v0.59.0 plan generator were drafted in /tmp/s61 (incl.
   /tmp/s61/p62/mk.py and the smoke output /tmp/s61/smoke) before being committed; nothing there is a gated input.
5. **Result (Observed; recount labels).** S24 decided 6/6 (5 ID, 1 IDF 12610103) Wilson 95% [0.61, 1.00], gate >= 5 of 6;
   S24b identical 2/2 [0.34, 1.00]; WRONG 0 of 8 records [0.00, 0.32]. Decided conflicts 3.21-15.13M; seed 12610101 needed
   15.13M (above the v0.57.0 8M budget). Wall guard 0, case kill 0. Walls 186-1316 s; runner 1316.2 s, inside the 60 min cap.
6. **Small sample (Inferred).** n = 6 is half the plan's 12 (cut by #196 to fit the cap). The lower Wilson bound 0.61 is weaker
   than a 10/12 result would give. The probe's two hard 060 seeds (12600101, 12600102) stayed IDU at 24M, so the 24M budget
   does not decide every 24-state world; 6/6 fresh seeds is not "always".
7. **S32 (Open).** Dropped by #196 (N32 = 0); the probe decided 0/2 at 16M and 24M. Declared N 32 stays Open.
8. **Gates (Exact).** 9/9 gated pass: GS61_sound, GN24_61, GDET61, GFID61 (8/8 exact replays, equiv, 0 socket attempts),
   GHOST61, GS_ref (8/8 audited, 0 mismatches, 20/20 mutations, 142.1 s), G_recount, GTEST (130 tests, 13 modules, 11 gated),
   G_PROC. certified_readbits4_N24 true; status phrase "certified (read_bits 4, N <= 24, B61)". G_RT is checked at release.
9. **Scope (Exact + Inferred).** An ID/IDF is exact only conditional on noise-free readings and a true size at most the
   declared N = 24. Reason (Inferred): a larger machine can copy the true machine on every visited state.
