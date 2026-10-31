# Deviation #165 (study-046, v0.43.0): build choices fixed before the source freeze

Written before the source freeze (2026-10-31T06:02:28-04:00, box-local EDT) and frozen with it. Nothing here changes a threshold,
gate or seed in BRUTE_PLAN_046 (plan commit 7d691cc). Each item records a choice the plan left open, a reading of a criterion, a
narrowed scope, or an observation made before any main record was run. Labels: Exact, Observed, Simulated, Inferred, Rejected,
Open. Times are EDT (UTC-4).

0. **Authorization (Exact).** preregistration_046 (7d691cc, 05:34:39 EDT); build_authorization_046 (7d691cc, 05:35:36 EDT) under
   James's STANDING GO t133s553 (ledger 76b30d5), ledgered before seedcheck_046 (1b0ce4b, 05:40:34 EDT, PASS). The maintainer
   asked for the lean process, one run, an additive host-agnostic API (certify/14 unchanged) and an N-conditional claim (item 7).
1. **Replay comparison (Exact).** GAPI16_replay "same" = same label (recounted API16 label against the sealed 045 A16_N label),
   same n_min, and an equal canonical model from state 0 (recount_033.canon), plus T_final. same_step (same stop step) and
   words_equal (identical executed words) are reported, not gated. Open risk: on sealed cases that were capped in 045 the
   per-call cap is a wall clock, so a replay may take a different branch at a cap; this is not tuned and is published as found.
2. **Readings (Exact).** brute/api/certify16.py (new). Readings are bit pairs mapped through brute.region.codes_mask, as in the
   A16_N runner. search='a16' (default) runs the A16_N path; any other search delegates to certify14 unchanged, keeping
   certify14's own defaults (only arguments the caller gave are passed on, via _given); the 'region' search must be named.
3. **Host cap (Exact).** The 9.0 s per-call cap and solver supply are host concerns: the runner passes HardHook as `hook` and the
   server factory as `factory`, both public constructor parameters. The core does no I/O, threads, subprocess or os.
4. **GAPI14_compat and GHOST16 method (Exact).** scripts/api_checks_046.py. Compat: tests.test_scalesearch4_0260 (the only test
   module importing certify14; 14 tests) must return 0 with >0 tests, and the 5 frozen CERTIFY14_SAMPLE_046 cases must be
   byte-equal through certify16 (3 s4, 1 s3, 1 region). Ghost: the AST import closure of certify16 minus certify14's closure
   (newly imported: certify16, encaudit16, scalesearch5, 7, 8, 9, 10, 14, 15, 16) must have no forbidden import (os,
   subprocess, threading, multiprocessing, socket, signal, asyncio, io, shutil, tempfile, pathlib, urllib, _thread, concurrent)
   or call (open, exec, eval, __import__), and a no-network subprocess (socket patched to raise) on dev seed 10050003
   control_cycle3 must decide with 0 socket attempts. It runs once after the freeze into results/study-046 and records
   certify16_sha256; the gates require it to equal the freeze's and the current sha.
5. **Reference scope (Exact).** scripts/run_reference_046.py: the decided fresh main records at N = family size (16 / 3), both
   arms, one wall budget BUDGET_S = 1800 s, 8 workers, order API16 then A16_N (control first, then scale16, by seed); 20 seeded
   mutations (random.Random(460)). Unfinished records are not_audited and GS_ref then fails (no weakening of the plan).
   Projection (Inferred, from the smoke): LPT 356.6 s, serial 2567.6 s, so complete = true is expected.
6. **Seeds seen before the freeze (Observed).** During the build, sreplays 11130005 (scale16) and 11190001 (control) were run
   in the smoke, and fresh main seeds scale16 11230001 and control 11270001 were run interactively once while debugging the
   wrapper. Nothing was tuned on them; their main records will be produced fresh by the gated run.
7. **The N-conditional claim (Exact wording; Inferred reason).** A certify16 ID / IDF holds only relative to the declared bound N
   (family_bound): the model is unique among machines with at most N states consistent with the trace. Reason (Inferred): a
   machine with more states can copy the true machine on every visited state and differ only on unvisited ones, so no finite
   trace rules it out; a size bound is inherent, not a defect of this API. RELEASE.json, README, CHANGELOG and the release
   notes must say so.
8. **Pre-freeze smoke (Observed / Inferred).** results/diag-046/PREFREEZE_SMOKE_GATES_046.json (31dd85d) has **PASS false**:
   stops present ID 12, IDF 2, unknown 2; **AMB and K_spent missing**. The probes K0 and B05 on control 11370005 decided ID from
   the passive prefix (0.1 s), so they did not reach those stops. Coverage instead (Exact): tests/test_certify16.py asserts
   K_spent -> AMB (K = 0 on a 2-step prefix) and unknown -> IDU (budget 1e-6). The smoke is not rerun. Everything else ran:
   api_checks PASS, recount PASS (0 mismatches, 126 words), reference smoke 10/10 audited, probe 2 decided, 20/20 mutations,
   synthetic release_ok true, real chain 5 links 0 exceptions. Both sreplays were same = True (ID). Smoke labels: API16 and A16_N
   agree on all 4 scale16 (ID, IDF, ID, unknown) and both controls (ID).
   Runtime (Inferred): mean fresh scale16 wall API16 98.7 s, A16_N 103.6 s; over 54 main jobs serial 3614.4 s, LPT 498.5 s on 8
   workers, worst case (every scale16 job at 250 s) 1250 s; all below the 3600 s G_RT bar.
9. **Recount key fix (Exact).** The smoke recount reported cases 7 for 8 records: it keyed records block/key/seed, so the two
   probes on the same seed collided. scripts/recount_046.py (not yet frozen) now appends /probe when a record has one (579960b);
   on a scratch copy of the smoke it reports 8 cases, 126 words, PASS. Main records have no probe field, so main is unaffected.
10. **Commit chain (Exact).** build_authorization_046 names the preregistration commit itself; verify_release_0430.chain must
   report 0 authorization exceptions (pre-freeze: 5 links, 0 exceptions).

What this deviation does not do: change any threshold, gate or seed. Scale-20, noise and an N-free claim stay Open.
