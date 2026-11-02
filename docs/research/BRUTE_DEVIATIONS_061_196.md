# Deviation #196 (study-061, v0.58.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 2 2026). It fixes readings of experiments/BRUTE_PLAN_061.json
(plan/v0.58.0, commit 359ae41, ledger preregistration_061; the plan is locked and not amended) and declares ONE departure from
it (item 4: fewer S24 seeds). It changes no cap (C 50000, B61 24000000, K 400, read_bits 4), worker count or job order rule.
Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** This study is still a **target change** (random 4-bit readings) and a **budget study of the same
   solver** (certify/32b frozen at v0.57.0). **2-bit readings at 20 states stay Open whatever happens.**
1. **Process (Exact, ledger note times, EST).** preregistration_061 (359ae41, 14:58:36), budget_probe_061 (d1bd376, 15:42:48),
   build_authorization_061 (d54fcf5, 15:42:56; standing go t133s553 and t139s684), seedcheck_061 (85fcae7, 15:48:40; PASS),
   tooling 8e331a8 .. d686ce3 (one commit per file), prefreeze_smoke_061_attempt1 (d1d7dda, 15:59:49) and prefreeze_smoke_061
   (42a150c, 15:59:51), then deviation_196, freeze_061, main_run_061 (once, nohup, never relaunched).
2. **Budget probe (Observed, exploratory, sealed 060 seeds only).** Ran once 15:00:07-15:40:37 EST. n 24: 16M decided 2/4,
   24M decided the same 2/4 (12600103, 12600109; 12600101 and 12600102 IDU; 12600102 hit the probe's 2100 s guard at 22.28M
   conflicts). n 32: 0/2 at both. WRONG 0. **The B61 rule was not met** (no probed B decided >= 3/4), so B61 = 24000000 by the
   rule's own fallback (Exact). Inferred: on these hard seeds, 24M bought nothing over 16M.
3. **Disclosure: scratch drafting (Observed).** All 061 tooling was drafted in the scratch directory /tmp/s61 while the probe ran
   (14:59-15:45 EST), before budget_probe_061 and build_authorization_061 were ledgered. Nothing from /tmp/s61 was committed
   before build_authorization_061; it was copied into the repo after it and committed after seedcheck_061. The probe used only
   sealed study-060 seeds. No main seed (12610101-12, 12610201-04) has been run by any tool before the main run; 12610303 is
   used only by the no-network run; smoke used 12610301-02.
4. **Cut decision (Observed + Inferred), DEPARTURE FROM THE PLAN, declared now.** Projection (BUDGET_PROBE_061 max walls at
   B61 x 1.25: 2631.6 s per 24-state job, 2710.3 s per 32-state job; LPT on 8 workers; cap 3300 s for the user's "about 60 min"):
   (N32, N24B, N24) = (4, 6, 12) 7973.4 s; (0, 6, 12) 7894.8 s; (0, 3, 12) 5263.2 s. **The plan's cut rule is exhausted.**
   The plan says S24 is never cut; the user's instruction (14:59 EST, repeated 15:49 EST) is to use fewer seeds or drop the
   32-state arm rather than exceed the cap, declared before the freeze. Added step (0, 2, 6): 8 jobs, 2631.6 s <= 3300 s.
   **Declared: N32 = 0 (S32 dropped), N24 = 6 (seeds 12610101-12610106), N24B = 2 (12610101-12610102).** Seeds
   12610107-12610112 and 12610201-12610204 stay reserved and unused. Gates scale as follows (fixed now, before data):
   GN24_61 needs S24 ID+IDF >= ceil(10 x 6 / 12) = 5 of 6 (same rate as the plan's 10/12); GDET61 needs 2/2 and no wall guard
   in S24/S24b; GS61_sound covers 8 records. The CIs are wider than planned (5/6 has Wilson [0.44, 0.97]). S32_report is not
   exercised (no S32 records).
5. **Hard kill (Exact).** Per-case hard kill HARD_KILL_S = 3000 s (above 1.25 x the slowest probe job at B61, 2631.6 s; one LPT
   round keeps the run under about 52 min plus overhead). The 30 s per-call wall guard is unchanged. A case kill or guard firing
   in S24/S24b fails GDET61 and is published, never cut after the fact.
6. **G_PROC (Exact rule).** preregistration_061 < budget_probe_061 < build_authorization_061 < seedcheck_061 <
   prefreeze_smoke_061 < deviation_196 < freeze_061 < main_run_061, as a ledger subsequence.
7. **Truth labels, GFID61, GHOST61, GS_ref, flags (Exact rule).** As in make_gates_061 and #194: ID from the start state, IDF from
   the current state, a decided non-equivalent model is WRONG; IDU, AMB, K_spent are not soundness failures. GHOST61 binds to
   BRUTE_SOURCE_FREEZE_060 (certify32b and frozen api shas), A16D_MAX_BOUND still 20. REFERENCE_061 random.Random(610).
   certified_readbits4_N24 iff every gate passes -> "certified (read_bits 4, N <= 24, B61)"; sound_not_certified_N24 iff every
   gate except GN24_61 passes -> "sound but not certified at B61"; else "not certified, no certification status (failing
   gates: ...)". Claims are conditional on the declared N (Inferred reason: a larger machine can copy the true machine on every
   visited state).
8. **Smoke (Observed, not evidence).** 12610301-02 on S24, S24b, S32 at B 2M: 6/6 IDU/unknown, S24 == S24b on both seeds, wall
   guard 0, walls 67.8-163.8 s.
9. **Known risks (Inferred, published now).** The probe seeds were the hardest 060 seeds; fresh seeds may be easier (060 decided
   8/12 at 8M). With 6 seeds, one more IDU than allowed fails GN24_61 ("sound but not certified at B61").
