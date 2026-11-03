# Deviation #200 (study-063, v0.60.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 2 2026). It fixes readings of experiments/BRUTE_PLAN_063.json
(plan/v0.60.0, commit 55433b5, ledger preregistration_063; the plan is locked and not amended) and declares the plan's own cut
rule as applied, plus one post-failure seedcheck rule (item 3). It changes no cap (C 50000, B 8000000, K 400, read_bits 2, N 20,
node cap 200000), worker count (6), case kill (2400 s) or job order rule. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** BACK ON THE HARD PROBLEM: 2-bit readings at 20 states, Open since v0.55.0. This is a **pool
   change** (certify/20p anchors symmetry breaking on an exact max apartness clique and re-pins when it grows), not a new action
   policy, not a new solver; B2 is the budget-matched frozen certify/20b control. A pass would mean certify/20p decides 2-bit
   20-state worlds under a declared N at the stated rate, nothing wider. The guarantee stays conditional on the declared N
   (Inferred reason: a larger machine can copy the true machine on every visited state).
1. **Process (Exact, ledger note times, EST).** capability_probe_063 (19:17:38, exploratory, sealed seeds only),
   preregistration_063 (19:17:42), build_authorization_063 (19:18:36; standing go t133s553 and t139s684, user 19:18 EST),
   certify20p and its test (186d456, c35c4f4, d62e976), seedcheck attempt 1 FAIL (published, e62fa8d), seedcheck_063 (19:33:11,
   attempt 2 PASS), tooling 6c02e14 .. 67ca9e3 (each script committed before it was run), prefreeze_smoke_063 (19:43:05, PASS),
   then deviation_200, freeze_063, main_run_063 (once, nohup, never relaunched). The ledger "commit" field is HEAD at ledger time.
2. **Disclosures (Observed).** (a) The plan text was drafted by a scratch writer before preregistration. (b) tests/test_certify20p.py
   was run once before it was committed (d62e976); the committed file is the one that ran. (c) api_checks_063.equiv() was run
   once directly after its commit (9c42107) as a tooling check: PASS, 18/18 sound, 9/9 n_min agreement where both decide. None of
   these touch a main seed. No main seed (12630101-12630106) has been run by any tool; smoke uses 12630301-02, the no-network
   check 12630303. Logs in /tmp/s63 (scratch, not evidence).
3. **Seedcheck, post-failure rule M (DEPARTURE, declared).** Attempt 1 (scripts/check_seeds_063.py, ede7b9b) FAILED: its only hit
   was the 063 target token 12630101 in RESEARCH_LEDGER.jsonl line 1261, which is the preregistration_063 note itself ("fresh
   seeds 12630101-08"), i.e. the plan echoing its own range, not a prior use. Published as
   results/diag-063/SEEDCHECK_063_ATTEMPT1_FAIL.json. Attempt 2 (scripts/check_seeds_063_m.py) rescans the fixed commit ede7b9b in
   a temporary worktree with one added rule M: a ledger token is allowed only if EVERY ledger line holding it is event
   preregistration_063 citing experiments/BRUTE_PLAN_063.json and the token is in a declared 063 range. Every other prior source
   and every negative control is unchanged; attempt 2 PASSED (results/diag-063/SEEDCHECK_063.json). Rule M was written after
   seeing the failure; that is why it is declared here.
4. **Cut decision (Observed + Inferred), the plan's own rule.** Projection (Inferred): worst job = 1.25 x the slowest P2 job of the
   capability probe at B 8M (506.6 s -> 633.2 s for P2/P2b) and 1.25 x the slowest B2 job of the sealed 062 main block (1613.5 s ->
   2016.8 s); LPT on 6 workers; cap 3300 s for the user's "about 60 min". (N_P2B, N_SEEDS) = (3, 8) 4033.6 s, (2, 8) 4033.6 s,
   **(2, 6) 3283.2 s <= 3300 s. Declared: N_SEEDS = 6 (12630101-12630106 on P2 and B2), N_P2B = 2 (12630101-02), 14 jobs.**
   Seeds 12630107-08 stay reserved and unused. The runner was set to (2, 6) at 67ca9e3, before the prefreeze run, which confirmed
   cut_consistent. Gates at n = 6 (plan formulas): GP63 needs P2 ID+IDF >= ceil(3 x 6 / 8) = 3 of 6 AND P2 - B2 >= ceil(2 x 6 / 8)
   = 2. **The CIs are wide** (3/6 has Wilson 95% [0.19, 0.81]; 0/6 has [0.00, 0.39]); the exact McNemar p cannot fall below
   0.031 at n = 6.
5. **Stop and kill (Exact).** Conflict-only stop, no hook; per-case hard kill 2400 s, 30 s per-call wall guard. A guard firing or
   case kill in P2/P2b fails GDET63 and is published, never cut after the fact; one in B2 is reported (a B2 job near the full 8M
   budget can reach about 1600-2000 s, Inferred from 062).
6. **G_PROC63 (Exact rule).** preregistration_063 < build_authorization_063 < seedcheck_063 < prefreeze_smoke_063 < deviation_200
   < freeze_063 < main_run_063, as a ledger subsequence with parseable non-decreasing note times.
7. **Truth labels, GFID63, GHOST63, GS_ref63, flags (Exact rule).** As in make_gates_063: ID from the start state, IDF from the
   current state, a decided non-equivalent model is WRONG; IDU, AMB, K_spent are not soundness failures. GFID63 replays every
   decided record through its own arm's API (P2/P2b: certify/20p with the recorded node cap). GHOST63 binds the certify20p sha in
   API_CHECKS_063 to BRUTE_SOURCE_FREEZE_063 and checks the frozen api shas against BRUTE_SOURCE_FREEZE_062. GS_ref63 reference
   budget 1800 s. certified_readbits2_N20_clique iff every gate passes -> "certified (read_bits 2, N <= 20, clique-anchored)";
   sound_no_2bit_gain iff every gate except GP63 passes -> "sound but no 2-bit gain"; else "not certified, no certification
   status (failing gates: ...)". Claims are conditional on the declared N.
8. **Smoke (Observed, not evidence).** 12630301-02 on P2, B2 and P2b at B 2M (19:32-19:38 EST): 6/6 IDU/unknown, P2 == P2b on both
   seeds, wall guard 0; P2 walls 60.9 / 74.6 s vs B2 244.6 / 138.0 s; P2 pinned cliques of 18 and 16 (4 and 2 re-pins) and used
   105 / 83 actions vs B2 60 / 75. prefreeze_smoke_063 attempt 1 PASS (one attempt).
9. **Known risks (Inferred, published now).** The probe decided 3/4 with P2 at 8M on spent seeds, but one of them (12620101) ended
   IDU; with 6 fresh seeds P2 may decide fewer than 3 (GP63 fails, "sound but no 2-bit gain"). If GP63 fails, the plan's
   next_if_fail applies; it is published, not re-run.
