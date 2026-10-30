# Deviation #143 (study-035, v0.32.0): run record, clock and post-run findings

Written after the main run. It changes no threshold, gate or label. Times are box-local EDT (UTC-4). Labels used:
Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **One main run (Observed).** run_start_035 was ledgered at 18:53:55 EDT (3588e27) on frozen source 1764462. The runner
   (pid 377755, 8 workers) ran the 48 main cases once from an empty checkpoint; it exited normally at 18:59:38 EDT.
   total_elapsed_informational was 342.7 s of the 1800 s cap. push_checkpoint_035 took two snapshots (aafa3c7 at 45
   cases, ade7093 at 48). No rerun, no resume, no tuning. The pre-freeze projection (318 s, deviation #142 item 16) was
   about 7% low; no runtime amendment was needed.
2. **Interruption (Observed).** The session was interrupted after the reference audit had written
   results/study-035/main/REFERENCE_035.json (exit code 0, PASS) but before it was committed. On resume the file was
   inspected: complete (12 of 12 noisy_scale8 cases, 12 decided, 0 undecided, 0 mismatches, mutations 20/20, results
   sha matches the seal). It was committed as written (3cce54f, ledger 63418ca); the audit was not rerun.
3. **Headline failure (Observed).** GA10 fails on all four clauses. a: A10 WRONG 0 of 48, S7 WRONG 0 of 48, but S5 WRONG
   15 of 24 noisy cases (all within budget), and the plan gates S5 in clause a. b: ID(A10) - ID(S7) on noisy12 0.00,
   bootstrap CI [0.00, 0.00]. c: ID + IDF(A10, noisy12) 0 of 12. d: IDU(A10, noisy12) 12 of 12.
4. **Diagnosis (Observed, then Inferred).** On all 24 noisy cases A10's first round found the B = 0 search UNSAT
   (check 'none'), then the upward least-budget search (B = 1, 2, ...) hit the 10 s in-solver cap after 9 to 12 queries,
   before reaching the true flip count (13 to 23 flips in 177 readings). raise_status was 'unknown', so B stayed 0, no
   word was executed (0 extra actions) and the stop was IDU. Inferred: proving UNSAT for B just below the least budget
   is the hard part of a cardinality-bounded search, so the upward search pays the most expensive queries first; at 0.05
   noise the needed budget is far above what a 10 s query can refute. A10_fixed and S7 (B = 27 from the start) also
   timed out on every noisy case, and on every clean scale12 case.
5. **Adaptivity on clean traces (Observed).** GNR10 passes: on clean scale12 and controls A10's labels equal A9's on all
   18 compared cases and B_final is 0 on every clean case. GAD10 passes: ID(A10) - ID(A10_fixed) on clean12 is +0.58
   [0.33, 0.83] (A10 ID 7/12, A10_fixed 0/12) and 0.00 on noisy12. This is the clean cost of a fixed budget removed, not a
   noisy gain.
6. **GQB10 failure (Observed).** Two S7 queries exceeded the 10.5 s bound (noisy_scale8 10110001 10.523 s, 10110003
   10.538 s). Every A10, A10_fixed, A9 and S5 query was below 10.5 s (A10 max 10.289 s). Inferred: the in-solver
   interrupt (g3) is reached late inside a long propagation on the largest CNFs.
7. **A9 on noisy traces (Observed).** A9 stopped 'none' on all 24 noisy cases (no machine of size up to N fits the noisy
   trace exactly), which label9 maps to WRONG. These are reported, not gated, as the plan states (A9 is not in clause a).
8. **16 states (Observed; secondary).** G16 fails: A10 ID 0 of 6 [0.00, 0.39], all IDU (query cap), WRONG 0.
9. **Reference strength (Inferred).** Because A10 reached IDU on every noisy_scale8 case after the B = 0 check, the
   reference had one decided item per case (the B = 0 'none' verdict). GS_ref passes, but it did not exercise raised-B
   verdicts, words or least-B values on main data.
10. **Clock (Observed).** At 19:04:42 EDT the box clock matched GitHub's Date header (23:04:42 GMT) to the second; no
   stall.
