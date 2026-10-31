# Deviation #171 (study-049, v0.46.0): pre-run declarations

Written before the source freeze (2026-10-31, box-local EDT, UTC-4). It fixes readings of BRUTE_PLAN_049 (commit 611dc9e) that the
plan leaves open. It changes no threshold, seed, cap or gate. Labels: Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **Process (Exact).** preregistration_049 (08:33 EDT, plan 611dc9e), build_authorization_049 (ledger commit e473fb8, 08:34 EDT,
   cites James's STANDING GO t133s553, ledger 76b30d5), seedcheck_049 (ledger commit 94aca8b, 08:40 EDT; SEEDCHECK_049 at c458de5:
   26 fresh cases 12/6/8, 344 prior ranges, 0 overlaps, all tokens allowed). Then source_freeze_049, run_start_049, run_end_049.
   Lean process. The resume clause is not approved: an interrupted run is never relaunched; a partial block is sealed as such.
2. **Caps are the plan's (Exact).** C = 50000 conflicts per chunk; B = 1500000 conflicts per case for scale16 and control, 1000000 for
   scale20; MAX_CHUNKS API16E / API16E_b None (resume until answered or B spent), API16E_c1 1 (certify/16d behaviour). Every record
   carries conflict_cap, budget_conflicts and max_chunks; runner and recount refuse a record whose caps differ.
3. **Guards (Exact).** The 30 s guard applies per chunk through the solve hook in certify16e._chunk_solve; the 600 s case guard is
   checked before each chunk. Both are wall-clock and fire only as guards (wall_guard true); any firing fails GDET49 / GQB24.
4. **Reuse by rebinding (Exact).** brute_study_049 imports the frozen 047/048 modules and rebinds S47.caps, ARMS, D_ARMS and _api16d to
   the 049 values at import, so every forked worker sees them. Per-call chunk fields are copied from certify16e._STATE (one job per
   process, maxtasksperchild 1). canon16e = canon16d plus call_chunks and chunk_conflicts; wall fields stay informational.
   recount_049 and run_reference_049 rebind R47.ORDER = (API16E, API16E_b) and DELTA = None per arm; reference budget 2400 s.
5. **Parts r and c (Exact).** Part r runs API16E on the 26 sealed 048 traces (scale16 11510001-12, control 11530001-06, scale20
   11610001-08 when R20). Part c runs API16E_c1 on the same 26; GCOMPAT16D requires canon16d(c record) byte-equal to the sealed 048
   record on all 26. GR49_sound fails on any contradiction: a replay label ID/IDF/IDU whose word set disagrees with a sealed decided
   label, or any WRONG. Parts r and c are recounted, not reference-audited (their decided sealed counterparts were audited in 048).
6. **GHOST49 (Exact).** The 048 ghost check plus: certify16d closure unchanged, the only newly imported modules are brute.api and
   brute.api.certify16e, certify16e sha equal to the 049 freeze, 0 socket attempts.
7. **Projection and cut order (Inferred; results/diag-049/PREFREEZE_SMOKE_GATES_049.json, commit 7143e71).** Per job worst
   min(600, B/r_min + 10) s with r_min = min(slowest smoke rate, declared rate): scale16 min(10771.8, 6716) = 6716/s, scale20
   min(8851.5, 3528) = 3528/s. Part c and controls at their smoke mean (the scale20 part c at the largest part c smoke mean, 10.7 s).
   Worst-case LPT on 8 workers: (R20 True, N20 8) 2047.1 s; (False, 8) 1753.6; (False, 6) 1520.3; (False, 4) 1460.2; (False, 0)
   1166.7. 2047.1 <= 3600, so **R20 = True, N20 = 8, no cut**; 104 main jobs. The runner's values match (cut_consistent true).
8. **Smoke (Observed, never gated, never tuned).** 16 jobs, 0 guard firings, determinism true on all 6 fresh smoke cases, canon16d equal
   on both part c smoke traces. Controls 11690005/06 ID in 4 chunks. scale16 11690002 **ID** after 51 chunks, 1155764 conflicts (49 s);
   11690001 IDU/unknown after 70 chunks, 1500151 conflicts (budget spent, 138 s). scale20 11690003/04 IDU/unknown, 60 / 30 chunks,
   1010880 / 1001779 conflicts (budget spent, 101 / 113 s). Part r scale16 11510002 AMB/K_spent in 86 chunks (sealed 048 AMB too;
   canon16d differs because chunks resume); part c 11510002 AMB/K_spent with canon16d equal. Reference smoke 6/6 decided audited, 0
   mismatches; recount, API checks and the verifier chain pass. **Reading (Inferred):** resumption converts some scale16 cases to ID,
   but many scale16 and all smoke scale20 cases spend B; GAPI16E_fresh49 and GS20 may be count-limited. Nothing is changed.
9. **Tests (Exact).** tests/test_certify16e.py tests resumption on a stand-in solver (control worlds answer in one chunk even at small
   caps, so the real solver cannot exercise a cap there). test_scripts_049 and test_release_0460 are new; the frozen 048/0450 tests are
   reported, not gated.
10. **Storage (Exact).** .gitignore gains study-049 raw RESULTS/SCIENTIFIC/CHECKPOINT lines (not a frozen file); raw files are packed
    as deterministic gzip by study049_storage and restored for verification.
