# Deviation #141 (study-034, v0.31.0): run record, clock and post-run findings

Written after the main run. It changes no threshold, gate or label. Times are box-local EDT (UTC-4). Labels used:
Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **One main run (Observed).** run_start_034 was ledgered at 17:56:34 EDT (5ab16bd). The runner (pid 336562, 8 workers)
   ran the 36 main cases once from an empty checkpoint. total_elapsed_informational was 124.8 s of the 1800 s cap.
   push_checkpoint_034 took one snapshot (ffdb5b5). The runner log was last written at 17:58:42 EDT. There was no rerun,
   no resume and no tuning.
2. **Ledger note slip (Exact).** The run_end_034 note (75b3eae) says "about 4 min wall". The real wall time from launch
   to runner exit was about 2 min 8 s (17:56:34 to 17:58:42 EDT). The ledger is append-only, so this item is the
   correction. The 4 min figure was the time to my first poll, not the run.
3. **Earlier ledger call failure (Exact).** The first run_start_034 attempt named a source path that did not exist yet
   (results/study-034/main), so append_ledger failed. Because the commands were chained with &&, neither the runner
   nor the pusher launched (checked with pgrep). The ledger and tree were unchanged. The retry used
   experiments/BRUTE_SOURCE_FREEZE_034.json as the source, following the 033 precedent. The main block was launched
   once only.
4. **Clock (Observed).** At 18:05:34 EDT the box read about 9 s ahead of GitHub's Date header (22:05:25 GMT). Deviation
   #140 had noted about 6 s ahead. No stall was seen, and ledger times are non-decreasing (G_PROC).
5. **GQB9 fails (Observed).** On scale12 10020005, one A9 SAT query took 10.888 s against the 10.5 s bound. A8 (10.41 s)
   and A9_random (10.53 s) came close to the bound or crossed it too. The 10 s per-query cap is checked between solver
   calls, so one call can run past it. Inferred cause: overshoot inside a single CaDiCaL call. The gate stays failed and
   is published as is.
6. **GDIAG8 was exercised and passes (Observed).** A8 gave 2 WRONG labels: scale16 10030003 (n_min 14 of 16) and scale12
   10020007 (n_min 11 of 12). Both stopped 'unique' below the truth's reachable size. This repeats the #139 diagnosis.
   A9 gave 0 WRONG on all 36 cases.
7. **IDF (Observed).** All 5 A9 IDF cases (4 scale8, 1 scale12) have M1_future_match. The final machine matches the
   truth on every future from the current state, so the remaining ambiguity is only the start state.
8. **scale16 (Observed).** A9 gave ID 0/6 on scale16: 4 IDU (query cap) and 2 AMB (K_spent: the next separating word
   was longer than the remaining budget of K = 64). A8 got 1 scale16 ID (10030004), on a case where A9 was IDU. No
   headline clause covers scale16.
9. **Smoke (Exact).** Nothing to add to #140 item 11.
