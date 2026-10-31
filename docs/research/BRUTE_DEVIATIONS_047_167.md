# Deviation #167 (study-047, v0.44.0): pre-run declarations

Written before the source freeze (2026-10-31, box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_047 (commit 168e821) that the
plan leaves open. It changes no threshold, seed or gate. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_047 (plan 168e821), build_authorization_047 (06:42:53 EDT, cites James's STANDING GO
   t133s553, ledger 76b30d5), seedcheck_047 (06:50:16 EDT, commit 2cf91a6: 30 fresh cases, 334 prior ranges, 0 overlaps),
   cap_calibration_047 (06:52:34 EDT, commit d615dcc). Then source_freeze_047, run_start_047, run_end_047. The process is lean:
   there is no release freeze. The resume clause is not approved, so an interrupted run is never relaunched.
2. **A smoke seed was used before the seedcheck (Exact).** Before seedcheck_047, one certify/16d API sanity call ran on smoke
   seed 11570005. It is a smoke-range seed (11570001-11570006), not a target seed, and it is never gated. Declared, not hidden.
3. **Cap calibration (Exact).** It ran in process, using the frozen active16 at the 046 settings with a g3 conflict-logging
   factory. It used only the smoke range and the 4 scale16 smoke cases with a solve wall of at least 1 s. Their median rate was
   32761.8 conflicts/s, which gives C = 294000 conflicts per call and B = 240/9 x C = 7840000 conflicts per case
   (results/diag-047/CAP_CALIBRATION_047.json). C, B and that file's SHA go into the freeze.
4. **The single-call reading of "chunk by chunk" (Exact).** certify/16d gives each SAT call one
   solve_limited(conf_budget = min(C, conflicts left)). It does no adaptive chunking and checks no clock between chunks. The
   calibration's 2000-conflict chunk is used only to round C.
5. **The wall guard is not tuned (Exact).** The guard stays at 30 s per call (passed to the host hook) and 600 s per case
   (checked before each call), as the plan fixes it. A guard that fires makes the call unknown and sets record['wall_guard'].
   **GDET scope:** a firing on any API16D or API16D_b main record is a GDET failure (plan what_counts_as_failure). Firings on
   replays or probes are reported.
6. **The smoke fired the guard on scale20 (Observed).** Smoke 11570001 fired once (max call 40.8 s, 618872 conflicts, 67.9 s).
   Smoke 11570002 fired 3 times (2398614 conflicts, 255.8 s). Both ended IDU/unknown. Under the no-tuning rule nothing was
   changed. **Reading (Inferred):** at N = 20 a single capped call (C = 294000) can run longer than 30 s on this host, because the
   scale20 conflict rate is lower (slowest 9113/s, against 17333/s on scale16).
7. **Canonical record for GDET (Exact).** canon16d (experiments/brute_study_047.py) holds no wall fields.
   - Arm fields: label, stop, n_min, model, s1, T_final, used, extra_acts, extra_masks, words, capped, conflicts_spent and
     wall_guard.
   - Fields for every round: T, n_min, check, M1, s1, word, M2, s2, obs, capped, call_conflicts and call_capped.
8. **API16D_b (Exact).** API16D_b is the same code as API16D. It runs the same cases in reverse seed order, as separate jobs in
   fresh worker processes (max_tasks_per_child=1).
9. **Replay difference classes (Exact).** These classes are used by GFID16D(ii) and GFID_wall:
   - none: label, n_min, canonical model and executed words are all equal; capped counts may differ.
   - infidelity: anything else, when neither record has a capped call.
   - cap-timing: the words are equal, but label, n_min or model differ after a capped call.
   - word-divergence: the words differ after a capped call.
10. **The budget overrun and the B50 probe (Exact).** The B50 probe (control 11570005, K 128, budget 50 conflicts) exercises a
    case budget below what the passive prefix needs. In smoke it decided ID with 87 conflicts, because a call that has started
    runs to min(C, budget left) and the budget check happens before each call. The case budget can therefore be overrun by at
    most one call's work. Reported, not gated.
11. **Missing stops are reported only (Observed).** The smoke shows the stops ID, K_spent and unknown. IDF and AMB did not
    appear. PREFREEZE_SMOKE_GATES_047 lists them as missing and does not require them. The K_spent and unknown stops are also
    exercised by tests/test_certify16d.py on the development world.
12. **GQB22 scope (Exact).** GQB22 bounds the main A16_N and API16D max call walls (10.5 s and 30 s). The API16 replay walls
    (part a2) are reported, not gated, because API16 is the 046 arm and is not the subject of this study.
13. **Worst-case projection definition (Exact) and the cut decision (Exact, applied).** The plan's runtime_estimate assumed
    240 s per fresh job. That premise does not hold for the conflict-budget arms (Rejected by the smoke): their budget is B
    conflicts, not 240 s, and smoke scale20 11570002 ran 255.8 s. The pre-freeze worst case is therefore defined as follows
    (scripts/prefreeze_smoke_047.py, Inferred):
    - Wall arms (A16_N and API16) on scale16 count 250 s each (240 s budget plus 10 s).
    - API16D and API16D_b on scale16 and scale20 count min(600 s guard, B / r_min(key) + 10 s), where r_min is the slowest smoke
      conflict rate for that key: 17332.9/s on scale16 and 9112.8/s on scale20.
    - Everything else counts its smoke mean.
    - The total is an LPT schedule over 8 workers.

    Result: with part d, 4836.2 s, which is above 3600 s. **The declared cut rule fires.** Part d (scale20, 12 cases) is dropped
    before the freeze by setting experiments/brute_study_047.py CUT_D = True (commit 44e4380), and nothing else is cut.
    Consequences:
    - GS20_sound is "not run" (pass = None, na).
    - GS20_rate is not reported.
    - G_RT covers 126 jobs.
    - The post-cut worst case is still 4023.9 s, above 3600 s, but the rule cuts only part d. G_RT may fail, and a failure will
      be published.
    - The mean-based LPT projection is 236.8 s without part d (480.3 s with it).
14. **Guarantee (Inferred).** certify/16d's ID and IDF labels are exact only on two conditions: the readings are noise-free, and
    the true machine has at most the declared N states (N <= 20 in the API; 16 is used in this run). The reason it is
    conditional: a larger machine can copy the true machine on every visited state, so no finite trace rules out every larger
    machine.

## What Brute can't do yet
- It cannot certify past the declared N. Every label is conditional on the size bound.
- It has no noise model. Noisy readings void the guarantee.
- Scale 20 is untested in this study (part d cut). Smoke shows that the 30 s call guard fires there at C = 294000 (Observed, 2/2).
- Determinism across hosts is claimed only for the conflict counter. When the wall guard fires, the record is host-dependent.
