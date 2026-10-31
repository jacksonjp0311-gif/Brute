# Deviation #169 (study-048, v0.45.0): pre-run declarations

Written before the source freeze (2026-10-31, box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_048 (commit 4dea7ef) that the
plan leaves open. It changes no threshold, seed, cap or gate. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_048 (plan 4dea7ef), build_authorization_048 (ledger commit 69bfe02, 08:03 EDT, cites James's
   STANDING GO t133s553, ledger 76b30d5), seedcheck_048 (ledger commit 83744b5, 08:08 EDT; SEEDCHECK_048 at 91dd25e: 26 fresh cases,
   2464 files scanned, 339 prior ranges, 0 overlaps). Then source_freeze_048, run_start_048, run_end_048. Lean process, no release
   freeze. The resume clause is not approved: an interrupted run is never relaunched; a partial block is sealed as such.
2. **Caps are the plan's, not calibrated (Exact).** C = 50000 conflicts per call everywhere; B = 1500000 conflicts per case for scale16
   and control, 1000000 for scale20; K = 128; solver g3; wall guard 30 s per call and 600 s per case. The 047 runner reads the 047
   calibration file in caps(); the 048 module rebinds `brute_study_047.caps` to return (C48, B16) and passes the per-key budget
   explicitly to `run_fresh`. The rebinding happens at import, so it holds in every forked worker. Every record carries
   conflict_cap and budget_conflicts, and the runner and recount refuse a record whose caps differ.
3. **Seedcheck tokens (Exact).** 0 standalone occurrences of any 048 seed in prior files; 9 occurrences embedded inside longer
   numerals ("ANY" scan) were inspected and are not seeds. Declared, not hidden.
4. **Job order (Exact).** 70 main jobs: scale20 API16D (8), scale16 API16D (12), part r replays (scale16 then control, 18), control
   API16D (6), then API16D_b on scale20, scale16 and control in reverse seed order (26). Pool of 8 workers, one task per child.
5. **Part r classification (Exact).** Each API16D replay of a sealed 046 A16_N trace (recount_048, via recount_047.replay_check)
   is classed none, cap-timing, word-divergence or infidelity and reported in GR_class (secondary). GWALL_r gates only guard firings
   on the 18 replays.
6. **GDET48 scope (Exact).** canon16d(API16D) == canon16d(API16D_b) on the 18 fresh scale16 + control cases and the N20 scale20 cases,
   AND wall_guard false on every record in parts a, r and d (replays included). A firing anywhere fails GDET48.
7. **GS20_sound (Exact).** Pass iff scale20 WRONG = 0 and every decided scale20 record is audited by the reference at bound 20 with
   0 mismatches. With 0 decided records the pass is reported as vacuous (pass true, vacuous true); if part d were cut it is
   "not run" (pass null).
8. **Reference (Exact).** scripts/run_reference_048.py calls the frozen run_reference_047 main with --budget 2400 and output name
   REFERENCE_048.json on 8 workers. The schema string inside that file stays brute.reference.v44_0 (the frozen writer's); this is
   cosmetic, the file name and plan budget identify the version.
9. **GHOST48 (Exact).** api_checks_048: the 047 ghost check, plus the import closure equal to API_CHECKS_047's (42 modules), certify16d
   sha equal to the 047 freeze, 0 socket attempts. GFID48 drives every API16D main record (expected 18 + N20) through A47.drive.
10. **Projection and step-down (Inferred; results/diag-048/PREFREEZE_SMOKE_GATES_048.json).** r_min(key) = min(slowest smoke rate,
    047 loaded rate): scale16 min(15226, 6716) = 6716/s, scale20 min(14570, 3528) = 3528/s. Per job worst min(600, B/r_min + 10) s;
    controls at the smoke mean. Worst-case LPT on 8 workers: N20=8 -> 1753.6 s (serial 13096 s), 6 -> 1520.3, 4 -> 1460.2, 0 -> 1166.7.
    1753.6 <= 3600, so **N20 = 8, no cut**. The runner's N20 is 8 (step_down_consistent true).
11. **Smoke (Observed, never gated, never tuned).** 13 jobs (seeds 11590001-06 both arms, replay of 11230004), 0 guard firings,
    canon16d equal on all 6 cases. Controls ID in about 0 s. scale16 11590001/02 IDU/unknown on both arms (428k / 242k conflicts,
    28 s / 7 s); scale20 11590003/04 IDU/unknown (266k / 228k, 13.8 s / 15.6 s). The replay was IDU, class word-divergence, 12.5 s.
    Every non-control smoke record stopped unknown well under its case budget. **Reading (Inferred):** at C = 50000 many single calls
    hit the per-call cap and return unknown, so GAPI16D_fresh48 (ID+IDF >= 7/12) may fail. Per the plan nothing is changed; this is
    recorded now so the outcome cannot be read as a surprise.
12. **Tooling reused (Exact).** The 048 runner imports the frozen 047 modules rather than copying them; new behaviour is only in
    048 files. .gitignore gains study-048 raw RESULTS/SCIENTIFIC/CHECKPOINT lines (not a frozen file); raw files are packed as
    deterministic gzip by study048_storage and restored for verification.
