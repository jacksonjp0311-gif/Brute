# Deviation #198 (study-062, v0.59.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 2 2026). It fixes readings of experiments/BRUTE_PLAN_062.json
(plan/v0.59.0, commit 43d877d, ledger preregistration_062; the plan is locked and not amended) and declares ONE departure from
it (item 4: fewer seeds than the plan's cut rule allows). It changes no cap (C 50000, B62 8000000, K 400, read_bits 2, N 20,
probe word (0, 1)), worker count or job order rule. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** This study is BACK ON THE HARD PROBLEM: 2-bit readings at 20 states, Open since v0.55.0. It is a
   **policy change** (which actions are taken: probe-word windows), not a new solver or encoding; certify/20w wraps the frozen
   certify/20b. A pass would be the first 2-bit 20-state decisions by this solver under a declared N, nothing wider. The guarantee
   stays conditional on the declared N (Inferred reason: a larger machine can copy the true machine on every visited state).
1. **Process (Exact, ledger note times, EST).** preregistration_062 (17:02:08), budget_probe_062 (17:44:50), build_authorization_062
   (17:45:03; standing go t133s553 and t139s684, user 17:02 EST), seedcheck_062 (17:50:41; PASS), tooling 6827f7e .. 0b3b091 and
   9b0db6f (one commit per file), prefreeze_smoke_062_attempt1 (killed, no output), _attempt2 (PASS) and prefreeze_smoke_062
   (6099c63 artifact), then deviation_198, freeze_062,
   main_run_062 (once, nohup, never relaunched). The ledger "commit" field is HEAD at ledger time.
2. **Budget probe (Observed, exploratory, sealed 058 seeds 12530001-04 only).** Ran once 17:04:38-17:42:29 EST (2273.2 s) with
   scripts/probe_062.py, committed at aded714 before the probe; the W2 policy in the probe is a local class (_W2Probe) in that
   script, not brute/api/certify20w.py, which was committed later (6827f7e) and is what the main run uses (GFID62 checks it).
   W2 at 8M decided 1/4 (12530003 ID, n_min 20, 5,640,260 conflicts, 581.1 s); B2 at 8M 0/4; both 0/4 at 2M. WRONG 0, wall guard
   0. Max walls at 8M: W2 2051.2 s, B2 2041.6 s. **The B62 rule was met at 8M** (smallest probed B with W2 >= 1/4), so
   B62 = 8000000 (Exact). Probe results are not evidence for any gate.
3. **Disclosure: drafting before authorization (Observed).** The 062 tooling (certify20w.py, the study runner and common module,
   the gate/recount/reference/api-check/freeze/smoke/test/verify scripts and their tests) was drafted **untracked inside the repo**
   (not in scratch) while the probe ran, before budget_probe_062 and build_authorization_062 were ledgered; none of it was
   committed before build_authorization_062. scripts/check_seeds_062.py was dry-run once before authorization (nothing from it
   committed); the official seedcheck ran after authorization. No main seed (12620101-12620112) has been run by any tool
   before the main run; smoke uses 12620301-02 and the no-network check 12620303. Logs are in /tmp/s62 (scratch, not evidence).
4. **Cut decision (Observed + Inferred), DEPARTURE FROM THE PLAN, declared now.** Projection (BUDGET_PROBE_062 max walls at B62
   x 1.25: 2564.0 s per W2/W2b job, 2552.0 s per B2 job; LPT on 8 workers; cap 3300 s for the user's "about 60 min"):
   (N_W2B, N_SEEDS) = (6, 12) 30 jobs, (2, 12) 26 jobs and (2, 8) 18 jobs all need at least 3 LPT rounds (> 7600 s). **The plan's
   cut rule is exhausted.** The user's instruction (17:02 EST) is "Cap the main run at about 60 min; any cuts must be declared
   before the freeze." Added step (2, 3): 8 jobs, one LPT round, about 2564 s <= 3300 s. **Declared: N_SEEDS = 3 (seeds
   12620101-12620103 on W2 and B2), N_W2B = 2 (12620101-12620102).** Seeds 12620104-12620112 stay reserved and unused. Gates scale
   as follows (fixed now, before data): GW62 needs W2 ID+IDF >= ceil(4 x 3 / 12) = 1 of 3 AND W2 - B2 >= ceil(3 x 3 / 12) = 1
   (same rates as the plan's 4/12 and 3); GDET62 needs 2/2 identical and no wall guard or case kill in W2/W2b; GS62_sound covers
   8 records. **The CIs are very wide** (1/3 has Wilson [0.06, 0.79]; 0/3 has [0.00, 0.56]); a pass at n = 3 is weak evidence and
   is published as such; the exact McNemar p cannot fall below 0.25 at n = 3.
5. **Hard kill (Exact).** Per-case hard kill HARD_KILL_S = 3000 s (above 1.25 x the slowest probe job at B62, 2564.0 s; one LPT
   round keeps the run under about 50 min plus overhead). The 30 s per-call wall guard is unchanged. A case kill or guard firing in
   W2/W2b fails GDET62 and is published, never cut after the fact; one in B2 is reported.
6. **G_PROC (Exact rule).** preregistration_062 < budget_probe_062 < build_authorization_062 < seedcheck_062 <
   prefreeze_smoke_062 < deviation_198 < freeze_062 < main_run_062, as a ledger subsequence.
7. **Truth labels, GFID62, GHOST62, GS_ref, flags (Exact rule).** As in make_gates_062: ID from the start state, IDF from the
   current state, a decided non-equivalent model is WRONG; IDU, AMB, K_spent are not soundness failures. GHOST62 binds the
   certify20w sha in API_CHECKS_062 to BRUTE_SOURCE_FREEZE_062 and checks the frozen api shas against BRUTE_SOURCE_FREEZE_061.
   GS_ref reference budget 1800 s. certified_readbits2_N20_windows iff every gate passes -> "certified (read_bits 2, N <= 20,
   windows)"; sound_no_2bit_gain iff every gate except GW62 passes -> "sound but no 2-bit gain"; else "not certified, no
   certification status (failing gates: ...)". Claims are conditional on the declared N.
8. **Smoke (Observed, not evidence).** 12620301-02 on W2, B2 and W2b at B 2M (17:51-17:56 EST): 6/6 IDU/unknown, W2 == W2b on both
   seeds, wall guard 0, walls 230.8-298.7 s; on 12620302 all arms spent the budget in round 1 (no extra actions), on 12620301 W2
   used 27 actions vs B2 24. The prefreeze script's attempt 1 was stopped by my own 220 s shell timeout and wrote nothing;
   attempt 2 (nohup) PASS, ledgered as prefreeze_smoke_062_attempt1/attempt2 and prefreeze_smoke_062.
9. **Known risks (Inferred, published now).** The probe decided only 1/4 with W2 at 8M on the hardest-known 058 seeds; with 3
   fresh seeds, W2 may decide 0/3 (GW62 fails, "sound but no 2-bit gain") and B2 may tie. If GW62 fails, the plan's next_if_fail
   applies (window signatures as explicit apartness clauses or entropy-chosen actions), not a budget-only step.
