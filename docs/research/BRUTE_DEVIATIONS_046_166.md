# Deviation #166 (study-046, v0.43.0): post-run record

Written after the gates (2026-10-31T06:23-04:00, box-local EDT). Nothing here changes a gate outcome, threshold or seed. Labels:
Exact, Observed, Simulated, Inferred, Rejected, Open. Times are EDT (UTC-4).

1. **Run (Exact).** source_freeze_046 (ledger f3a8948, 06:03:20 EDT, freeze commit dcfb009, 195 files); run_start_046 (ledger
   c79b6ee, 06:03:33 EDT); one main run, 54/54 jobs (36 fresh arm jobs on 18 cases, 18 replays), 319.8 s of 3600 s, normal exit
   about 06:08:56 EDT; two checkpoint snapshots (70e10f2, 8dd4720); seal 6b947df; run_end_046 (ledger d18a506, 06:10:36 EDT).
   Nothing relaunched; the resume clause was not used. No edit to frozen code during the run.
2. **Outcome (Exact).** 10 of 12 gates pass. **GAPI16_replay FAILS**: same on 17/18 [0.74, 0.99] (bar 18/18); same_step 16/18,
   words_equal 17/18. **GAPI16_fresh FAILS on count**: API16 scale16 ID+IDF 6/12 [0.25, 0.75] (bar 8/12); WRONG 0; same label as
   A16_N on 11/12 [0.65, 0.99] (bar 11/12, met). GAPI14_compat, GHOST16, G10 (12/12 control ID), GQB21 (max call 10.033 s API16,
   10.015 s A16_N against 10.5 s; 2592 calls; 2 hard kills), GS_ref (25 decided, 25 audited, complete, 0 mismatches, 20/20
   mutations, 614.1 s of 1800 s), G_sound (638 words, 0 unsound), G_recount, GTI, G_PROC and G_RT pass.
3. **The replay failure (Observed).** 11130006 (scale16): API16 IDU (stop unknown, last phase start, 108.2 s) against the
   sealed 045 A16_N ID. The executed words are identical, n_min 16 and the canonical model are equal, T_final 295 both; API16 hit
   the 9 s cap on 5 calls, the sealed run on 3, and the start search ended at a cap. Also: 11130008 kept its label (IDU) but its
   words diverged at word 6 (capped 3 / 3); 11130002 kept label and words with capped 8 / 6. All 13 replays with no capped call
   on either side were identical in label, step and words. **Reading (Inferred):** the per-call cap is a wall-clock limit, so a
   capped query can end differently on a rerun; the divergence follows cap timing, not the wrapper's logic. This was the Open
   risk declared in #165 item 1. It is not proven: an A16_N self-replay (the same code twice) was not run, so wrapper infidelity
   is not ruled out (Open).
4. **The fresh count (Observed).** On the same 12 fresh worlds A16_N itself decided 7/12 [0.32, 0.81] (ID 3, IDF 4; unknown 5),
   below its 045 result 10/12 and 043 9/12 (GREP16c, reported). The one disagreement, 11230005, is API16 IDU (capped unknown,
   2 capped calls) against A16_N IDF (1 capped call). **Reading (Inferred):** the count shortfall is mostly a property of these
   fresh worlds at the 240 s budget, shared by both arms, plus one cap-timing difference; GAPI16_fresh's bar of 8/12 was not met
   by the reference arm either.
5. **Branch taken (Exact).** Plan 046 next_if_fail, first clause: "GAPI16_replay fails: the wrapper is not faithful; fix
   fidelity before anything else and re-plan." The third clause (count only, replay passing) does not apply because replay
   failed. WRONG is 0, so the soundness clause does not apply. GAPI14_compat and GHOST16 pass, so the fourth clause does not
   apply: certify/16 ships in v0.43.0 as an additive, **uncertified** API (brute/api/certify16.py); certify/14 stays the latest
   certified API. Scale-20 waits.
6. **Cost (Observed, GAPI_cost).** Summed scale16 arm wall: API16 663.2 s (809 calls, 26 capped), A16_N 655.1 s (823 calls, 25
   capped); replay scale16 582.8 s (888 calls, 19 capped). Wrapper overhead is within noise.
7. **N-conditional claim (Exact; Inferred reason).** As #165 item 7: every certify/16 ID / IDF holds only for true size at most
   the declared N, with noise-free readings. A larger machine can copy the true one on every visited state, so a size bound is
   inherent. Every certify/16 label in this study was audited true at its bound (GS_ref).
8. **Ledger notes (Exact).** api_checks_046 (884dfc3, ledger 78bec36) ran once after the freeze; certify16 sha a46ac7db equals
   the freeze. tests_046 (bb14079, ledger 97055b4) after reference_046 (09d3e31, ledger 9f89156), as in 044 and 045. The
   reference_046 ledger note's counts were written before reading the file and then checked against it (25 decided, 25 audited).

What this deviation does not do: no rerun, no tuning, no gate change. Wrapper fidelity under a deterministic cap, scale-20,
noise and an N-free claim stay Open.
