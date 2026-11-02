# Deviation #190 (study-058, v0.55.0): pre-run declarations

Written before the source freeze (box-local EST, UTC-5, Nov 2 2026). It fixes readings of experiments/BRUTE_PLAN_058.json
(plan/v0.55.0, commit ee52a61, ledger preregistration_058 b959bf7; no amendment; the plan is locked) that the plan leaves open.
It changes no threshold, seed, cap (C 50000, B 2000000, K 400), worker count, job order or gate. Labels: Exact, Observed,
Simulated, Inferred, Rejected, Open.

0. **Framing (kept prominent).** This study is a **target change**: it asks whether wider readings (3 or 4 bits, random
   emissions) let the frozen certify/16e machinery decide 20-state worlds. It is not progress on the 2-bit problem. **2-bit
   readings at 20 states stay Open whatever happens.** GATES_058 carries this sentence as its framing field.
1. **Process (Exact).** preregistration_058 (ee52a61, ledger b959bf7), build_authorization_058 (ledger 8aaee3a; standing go
   t133s553 and t139s684), seedcheck_058 (c25053c, ledger 8d2a497; PASS), study tooling (9867e2e .. 8305ed4, committed only after
   seedcheck_058), prefreeze smoke attempt 1 (509098c, ledger d2072e3; also ledgered as prefreeze_smoke_058, 12f9c14), then
   deviation_190, freeze_058, main_run_058, run_end_058, recount, reference, api_checks, tests, gates, #191. The main run goes
   once with nohup and is never relaunched.
2. **G_PROC event names (Exact rule).** G_PROC checks the ledger order preregistration_058 < build_authorization_058 <
   seedcheck_058 < prefreeze_smoke_058 < deviation_190 < freeze_058 < main_run_058 (the plan's "prefreeze smoke" and
   "deviation #190" read as those event names).
3. **G_RT (Exact rule).** G_RT (verify_release_0550 in the repository and in a fresh clone of the tag) is a release-time check
   and is not inside GATES_058 (the gates file exists before the tag). It is run and reported at release; if it fails there is
   no release claim, and that is published.
4. **GFID58 (Exact rule).** PASS iff api_checks_058 equiv PASS (certify/20b at read_bits 2 equals certify/16e record-for-record
   on 6 small worlds, seeds 5800-5805, n 3-6; 8 constructor refusals and 3 observe refusals all refused), its no-network run
   passes, and every decided (ID or IDF) main record replays exactly through the public interface. The plan's 20-state
   equivalence is read as these small worlds (a 20-state 2-bit equivalence would spend B per world for an IDU-vs-IDU match).
5. **GHOST58 is a superset (Exact rule; disclosed).** GHOST58 = api_checks ghost PASS58: (a) the plan's AST scan, run as a
   static closure scan of brute.api.certify20b (no os, io, threading, subprocess, socket or multiprocessing import and no
   open() call in it or its brute imports); (b) certify14/16/16d/16e unchanged against their freeze sha256; (c) a no-network
   loop on smoke seed 12550003, scale20r4, read_bits 4, with socket use refused (Observed in smoke: 0 socket attempts, label
   IDU). (b) and (c) are stricter than the plan; a failure in either fails GHOST58.
6. **GS_ref (Exact rule).** Scope budget 1800 s on 8 workers, m = 2**read_bits per family; PASS iff complete, 0 mismatches, not
   vacuous and 20/20 mutations detected (random.Random(580)).
7. **Flags and wording (Exact rule).** certified_readbits_N20 iff every gate in GATES_058 passes; sound_not_certified_readbits
   iff every gate except GB_gain58 and/or GB3_58 passes (SOFT = those two). status_phrase: "certified (read_bits 3 and 4,
   N <= 20)", "sound but not certified", or "not certified, no certification status (failing gates: ...)". Claims are
   conditional on the declared N (Inferred reason: a larger machine can copy the true machine on every visited state).
8. **Cut decision (Observed + Inferred).** Smoke (12550001-02, 10 jobs, one 8-worker pool): slowest rate 6591 conflicts/s,
   worst per job B/r + 10 = 313.4 s, LPT of 60 jobs on 8 workers = 2507.5 s <= 3300 s. **No cut: N58 = 12.** Smoke was not
   gated and set no cap. Smoke records (Observed, not evidence for any gate): B4 ID on both seeds, B3 ID on one, B2 and B2R
   unknown on both; no wall guard; B4 vs B4_b identical.
9. **Known risk (Observed, published now).** In smoke and the pre-plan probe, B4 decisions used 1.3-1.5M of the 2M conflicts.
   GB_gain58 may fail on margin; it will be published as is.
