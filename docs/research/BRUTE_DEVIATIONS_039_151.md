# Deviation #151 (study-039, v0.36.0): run record and post-run findings

Written after the main run. It changes no threshold, gate or label. Times are box-local EDT (UTC-4). Labels used:
Exact, Observed, Simulated, Inferred, Rejected, Open.

1. **One main run (Observed).** run_start_039 was ledgered at 22:36:33 EDT (aef5112) on frozen source afc8eff (ledger
   c066e4c). The runner (pid 556558, 8 workers) ran 54 cases / 162 (case, group) jobs once from an empty checkpoint and
   exited normally about 22:41:47 EDT; total_elapsed_informational 309.6 s of the 1800 s cap. push_checkpoint_039 pushed
   two snapshots (0d20c04, 161 jobs, 22:41:40; 963501f, 162 jobs, 22:41:47). Seal 44f79e3, run_end_039 ledger 33608a0.
   Nothing was relaunched, resumed or rerun; the resume clause was not used (not approved). The pre-freeze projection
   (312.1 s LPT, #150 item 5) was within 1% of the actual wall; no runtime amendment was needed or declared.
2. **Post-run chain (Observed).** recount 879d6ac (ledger f284031: 54 cases, 743 words, 0 unsound, 0 truth-inconsistent,
   0 label mismatches); reference cd54bae (ledger e6a571b: A14 on scale14, 12 cases, 8 decided, 4 not reached at the cap,
   114 verdicts, 102 words, 0 mismatches, mutations 20/20, 222.5 s); official tests 66c8652 (ledger d87ce10: 10 modules,
   70 tests, all ok); gates 12ab5d2 (make_gates_039 --check reproduces).
3. **Headline failure (Observed).** GC14_headline fails on b and c; a and d pass.
   a: recounted WRONG 0 for A14 and A14_k64 on all 54 cases, no label mismatch.
   b: ID+IDF(A14, scale16) 0/12, Wilson [0.00, 0.24] (bar >= 4). All 12 are IDU with a capped rival query (stop 'unknown').
   c: paired ID(A14) - ID(A9) on scale16 -0.083, seed bootstrap [-0.25, 0.00] (bar +0.25, CI lower > 0); A9 had 1 ID.
   d: ID+IDF(A14, scale14) 8/12, Wilson [0.39, 0.86] (bar >= 6).
4. **What passed (Observed).** GFAM14 (perm12 A14 ID 12/12 [0.76, 1.00], WRONG 0), GREP14 (scale12 ID+IDF A14 12 vs A9 11),
   GCH14 (pooled scale14+16 ID(A14) - ID(A14_random) +0.292 [0.125, 0.458], bar 0.17), GINC14 (36 sealed 034 cases, 307
   verdicts, 0 mismatches), GQB14 (max 9.563 s, A14_k64; bar 10.5 s; A9 10.281 s reported), G_sound (743 words, 0 unsound),
   G10 (6/6 controls ID, all arms), GS_ref, GTI, G_PROC, G_RT (309.6 s), G_recount. Secondary GK14 and GACT14 reported only.
5. **Which plan-039 branches fire (Inferred).** a passed: no encoding audit. b failed with caps dominant (12/12 A14 scale16
   cases capped; K_spent 0 on every scale16 case): the 'per-size cube split or symmetry-free fixed-start encoding' branch
   fires. d passed and b failed: 14 states is the current ceiling of this encoding, reported as such. GFAM14 and GREP14
   passed: neither the perm12 diagnosis nor the A14_k64 localisation branch fires.
6. **perm12 is nearly passive (Observed; Inferred consequence).** A14 used 0.67 extra actions on average on perm12 (10 of
   12 cases needed none). GFAM14 therefore says little about chosen experiments on a second family; a harder second family
   is Open and is named in plan 040.
7. **Incremental instance (Observed).** A14 vs A9 labels differ in 3 cases (scale12 +1 ID via A9 K_spent AMB; scale14 one
   seed each way; scale16 A9 +1 ID). The incremental instance lowers per-query max (A14 scale16 9.09 s mean vs A9 9.63 s) but
   does not bring the n = 16 rival query under the 9 s cap.
8. **A14_random (Observed).** By design it spends A14's extra-action count (GACT14 'used' is identical); it gets AMB 28 of 54,
   ID 16, so the chosen experiments carry the identification on scale12/14 (contrast +0.83 and +0.58).
9. **Clock (Observed).** Box clock vs GitHub's Date header is checked at release time; see the release ledger notes.
