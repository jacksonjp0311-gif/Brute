# Deviation #194 (study-060, v0.57.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 2 2026). It fixes readings of experiments/BRUTE_PLAN_060.json
(plan/v0.57.0, commit 1893218, ledger preregistration_060; no amendment; the plan is locked) that the plan leaves open. It changes
no threshold, seed, cap (C 50000, B 8000000, K 400, read_bits 4), worker count, job order or gate. Labels: Exact, Observed,
Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** This study is a **target change**: random 4-bit readings, now at declared size 24 (gated) and
   32 (reported). It is not progress on the 2-bit problem. **2-bit readings at 20 states stay Open whatever happens.** GATES_060
   carries this sentence as its framing field.
1. **Process (Exact, ledger note times).** budget_probe_060 (a6d1eb0, 13:33:41 EST; exploratory, non-fresh), preregistration_060
   (1893218, 13:36:48 EST), build_authorization_060 (455f215, 13:36:52 EST; standing go t133s553 and t139s684), seedcheck_060
   (7f086d7, 13:47:56 EST; PASS), tooling d41f3dc .. d13ef5a, prefreeze smoke attempt 1 (ef69a9a, 13:57:09 EST; also
   prefreeze_smoke_060, 13:57:11 EST), then deviation_194, freeze_060, main_run_060, run_end_060, recount, reference, tests,
   api_checks, gates, #195. The main run goes once with nohup and is never relaunched. Times are ledger note times, not
   process start times (ps start times on this box are offset).
2. **Disclosure: build order (Observed).** All 060 tooling was drafted in a scratch directory while the budget probe ran and
   was committed after seedcheck_060. The probe and its reference probe used only sealed study-058 seeds 12530001-12530004 and an
   in-process patch of certify16d.A16D_MAX_BOUND in the probe process only; certify/32b does not patch it (GHOST60 checks this).
   No main seed (12600101-12, 12600201-12) has been run by any tool before the main run; 12600303 is used only by the
   no-network run.
3. **G_PROC event names (Exact rule).** preregistration_060 < build_authorization_060 < seedcheck_060 < prefreeze_smoke_060 <
   deviation_194 < freeze_060 < main_run_060, as a subsequence of the ledger. The older v0.6.0 events release_060 and
   release_freeze_060 are different names and are not part of this rule.
4. **Truth labels (Exact rule).** ID is checked from the start state and IDF from the current state against the true machine
   (bisimulation on the reachable part); a decided model not equivalent is WRONG. IDU (budget spent), AMB and K_spent are not
   failures of soundness. Labels are behaviour-based: true_size may be below n (seed 12600302 at n 24 has n_min 22 at 2M).
5. **GDET60 (Exact rule).** canon60 = the no_time view of each record (same as canon59): S24 and S24b byte-identical on every
   scale24w seed, and wall_guard 0 in every S24 and S24b record. S32 guard firings and 3600 s case kills are reported only.
6. **GFID60 / GHOST60 (Exact rule).** As in make_gates_060: 18 small-world equivalences 32b == 20b (read_bits 2/3/4, 6 each,
   plus one-shot), bounds 21..32 accepted, 8 refusals, no-network run (0 socket attempts), exact replay of every decided main
   record; ghost: closure scan, frozen api shas against FREEZE_059, A16D_MAX_BOUND still 20, bound to certify32b.py's sha in
   BRUTE_SOURCE_FREEZE_060.
7. **GS_ref (Exact rule).** REFERENCE_060 (random.Random(600)), block main, budget 3600 s on 8 workers, 20/20 mutations; vacuous
   only if nothing is decided.
8. **Flags and wording (Exact rule).** certified_readbits4_N24 iff every gate in GATES_060 passes; sound_not_certified_N24 iff
   every gate except GN24_60 passes. status_phrase: "certified (read_bits 4, N <= 24)", "sound but not certified", or "not
   certified, no certification status (failing gates: ...)". N 25..32 gets no status from this study. Claims are conditional on
   the declared N (Inferred reason: a larger machine can copy the true machine on every visited state).
9. **Smoke settings (Exact).** Smoke ran at B 2000000 (SMOKE_B60) on seeds 12600301-02 on all three arms (6 jobs, 8 workers) as a
   tooling check only. It cannot set B: the probe showed 24 states need about 3-4M conflicts.
10. **Cut decision (Observed + Inferred).** Projection from the probe (BUDGET_PROBE_060 max walls at B 8M x 1.25: 323.8 s per
    24-state job, 2938.6 s per 32-state job; LPT on 8 workers): N32 = 6 gives 3262.4 s <= 3300 s. **No cut: N24 = 12, N32 = 6.**
    Load check (reported): smoke walls 79.8-80.8 s (n 24) and 282.1-355.8 s (n 32) vs probe 2M max 79.3 s and 345.3 s, within
    1.5x. Smoke records (Observed, not evidence for any gate): every record IDU/unknown (expected at B 2M), S24 == S24b on both
    seeds, wall guard 0; S32 seed 12600301 spent 2499190 conflicts (one chunk past B, as the conflict-only stop allows).
11. **Known risks (Observed, published now).** (a) The projection is within 1.2% of the cap: a slower S32 job can push the main
    run past 60 min; each case is still capped by the 3600 s hard kill, which would be published, not cut after the fact.
    (b) The probe decided 0/4 at 32 states at B 8M, so S32 is expected to decide little or nothing.
