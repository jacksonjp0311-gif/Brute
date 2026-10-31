# Deviation #168 (study-047, v0.44.0): post-run record

Written after the gates (2026-10-31T07:58-04:00, box-local EDT). Nothing here changes a gate outcome, threshold or seed. Labels:
Exact, Observed, Simulated, Inferred, Rejected, Open. Times are EDT (UTC-4).

1. **Run (Exact).** source_freeze_047 (freeze commit bfd3a5b, 225 files, cut_d true; ledger a6fe216); run_start_047 (ledger
   8dffef4, 07:21:32 EDT); one main run, PID 968081, 126/126 jobs (18 fresh cases x 3 arms = 54, 72 replays), 661.6 s of 3600 s,
   normal exit. The session was interrupted while the run was live; the run was not relaunched, restarted or killed, and was
   waited on until it exited. Three checkpoint snapshots (0ddf98b, c3eea46, 865fc83); seal 89ea522; run_end_047 (ledger 8b12597).
   The resume clause was not used. No edit to frozen code during the run.
2. **Outcome (Exact).** 12 of 14 exercised gates pass; GS20_sound is not run (part d cut, #167 item 13).
   - **GDET FAILS** on its wall_guard clause. canon16d is byte-identical between API16D and API16D_b on 18/18 fresh cases
     [0.82, 1.00], with 0 wall_guard firings in the main block, but the guard fired 7 times (calls) on 3 API16D a3_046 replay
     records (11230004: 2, 11230008: 4, 11230009: 1). The rule counts firings on every API16D / API16D_b record (a3, b, d).
   - **GQB22 FAILS.** A16_N max logged call 16.718 s against 10.5 s (6 main scale16 A16_N records over; 7 hard kills); API16D max
     43.778 s against the 30 s guard (the 3 a3_046 records above). Main-block API16D max 17.553 s, API16D_b 14.948 s.
   - Pass: GFID16D ((i) self-replay 18/18 [0.82, 1.00]; (ii) 19/19 uncapped a3 replays same label, n_min and model [0.83, 1.00]),
     GFID_wall (0 infidelity in a1 and a2; same 16/18 each [0.67, 0.97]), GAPI16D_fresh (API16D scale16 ID+IDF 10/12
     [0.55, 0.95], WRONG 0; same label as A16_N 8/12 [0.39, 0.86]), GAPI16_compat, GHOST16D, G10 (6/6 controls ID in all three
     arms), GS_ref (48 decided, 48 audited, 0 mismatches, 20/20 mutations, 517 s of 1800 s), G_sound (1498 words, 0 unsound),
     G_recount, GTI, G_PROC, G_RT (661.6 s).
3. **What the GDET failure is (Observed).** The deterministic conflict cap did what it was built for on fresh data (18/18
   identical). The guard firings are all in part a3_046 (replaying sealed 046 traces), on calls that ran slower than
   294000 conflicts per 30 s (rates 6716 to 9797 conflicts/s against a median capped call of 13.8 s). A fired call's outcome
   depends on the clock, so those records are not wall-free. The three affected replays are IDU on both sides. **Reading
   (Inferred):** the cap C = 294000 is too large for the slowest calls under 8-worker load; the clock enters only through the
   guard. This is the nondeterminism source plan 047's GDET branch asks for, but it is not yet proven (Open): a run with a cap
   small enough that the guard never fires has not been done.
4. **What the GQB22 failure is (Observed).** The A16_N 9 s wall cap overran to 16.7 s on 6 main records (046: 10.033 s), and the
   API16D guard is a check, not a kill, so one guarded call ran 43.8 s. **Reading (Inferred):** CPU contention, with three
   arms and the slow a3 replays sharing 8 workers, stretched kill latency; not shown (Open).
5. **Branch taken (Exact).** Plan 047 next_if_fail, first clause: "GDET fails: the conflict cap is not deterministic on this
   solver; find the nondeterminism source before anything else." GFID16D and GFID_wall pass, so the wrapper-fidelity and
   erratum clauses do not apply; WRONG is 0 and GAPI16D_fresh passes, so neither GAPI16D_fresh clause applies; GS20_sound was not
   run. certify/16d ships in v0.44.0 as an additive, **uncertified** API (brute/api/certify16d.py). certify/14 stays the latest
   certified API; certify/16 (v0.43.0) stays uncertified.
6. **H1 to H5 (Observed).** H1 supported: 0 infidelity-class differences in a1/a2 (cap-timing 1 and 2, word-divergence 1 and 1).
   H2 supported on fresh data, not wall-free on a3 (item 3). H3 supported (GFID16D). H4 supported: 10/12 decided, at or above
   A16_N's 046 7/12; A16_N decided 8/12 here (GREP16d; 043 9/12, 045 10/12, 046 7/12). H5 not tested (part d cut).
7. **Cost (Observed, GAPI_cost).** Main scale16 arm wall: API16D 421.4 s (680 calls, 6 capped, 9932495 conflicts), API16D_b
   429.2 s (same calls and conflicts), A16_N 549.6 s (798 calls, 21 capped). a3_046 API16D 1195.3 s (23 capped).
8. **Runtime projection (Observed, Rejected premise).** The #167 projection rate for scale16 (17332.9 conflicts/s, smoke) was
   above what the run saw under load (slowest full-cap call 11155/s; guarded calls lower). The worst-case definition is
   therefore optimistic under load; plan 048 uses the run's rates.
9. **N-conditional claim (Exact; Inferred reason).** Every certify/16d ID / IDF holds only for true size at most the declared N,
   with noise-free readings. A larger machine can copy the true one on every visited state, so a size bound is inherent. Every
   decided label in this study was audited true at its bound (GS_ref).
10. **Ledger notes (Exact).** recount_047 (4968e1a, ledger 673706e); reference_047 (f1843ce, ledger f7a0b65); api_checks_047
    (7a81e0b, ledger 8c8f0bc; fidelity 18/18 exact, 0 socket attempts); tests_047 (ledger 8df4067; 77 tests, 8 modules);
    gates_047 (c0b59d5, ledger 9b28e89). The 045 and 046 raw studies were restored from their committed archives before the
    tests.

What Brute can't do yet: a wall-free deterministic certificate at 16 states under load (GDET), a hard per-call time bound
under 8-worker load (GQB22), anything at 20 states (part d cut), noisy readings, lowobs12 beyond A16, or a claim without a
declared N.

What this deviation does not do: no rerun, no tuning, no gate change.
