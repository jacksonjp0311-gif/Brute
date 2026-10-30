# Deviation #124 (study-026, v0.23.0): implementation details fixed before the source freeze

Written after the code and the smoke runs (seeds 9290001+, outside results/) and **before** `source_freeze_026` and
`run_start_026`. No target-range seed has been run. Nothing here changes a GSC threshold, a budget, a family, a seed or
the case count of the plan or of deviation #123; it records how the frozen code realises them. Labels: Exact = holds
by construction of the code; Observed = seen in the smoke only (not gated evidence).

1. **Arm deadlines include update time (Exact).** For S1 and RGB6, `observe` (rebuild) time is charged against the arm
   deadline, not against any single query; a query that starts before the deadline may finish after it. S2 `observe`
   receives the arm deadline. Queries not started before the deadline are NOT RUN (unk -1) and count as UNKNOWN.
2. **No certificate from an inexact support (Exact).** A support with unk != 0 is never certified, for every arm.
3. **S2 observes the final action (Exact).** S2 observes action 176 so that identify sees all 176 actions and 177
   readings; S1 and RGB6 stop after the last query. This changes no gated quantity of S1 or RGB6.
4. **Smoke layout (Exact).** The smoke block uses seeds 9290001+, 11 jobs, and must be written outside
   results/study-026; the runner refuses a smoke output inside the study directory.
5. **Reference audit (GS_ref12) (Exact).** run_reference_026 audits the scale8 cases with 8 processes, a node budget of
   20000 per query, a case cap of 110 s, and visits queries in a stride-7 order; queries it cannot decide in budget are
   counted as undecided or not reached and are not compared. The mutation test alters 20 copied S2 answers and must
   detect 20/20.
6. **The reference audit is one-sided in practice (Observed, smoke).** In the smoke the reference decided 0
   impossible codes (with n_max 16 > n, unexercised transitions keep every code possible), so it can catch a dropped
   possible code but not an added impossible one. This is reported with GS_ref12, not hidden.
7. **Scoring scripts (Exact).** recount_026 recomputes truth from seeds and re-derives certificates from stored
   supports; api_check_026 streams brute.certify/12 search='s2' on 4 scale8 eps-0 main cases (exact vs S2) and 2
   scale8 eps-0.02 cases (betting vs RGB6, first min(steps_done, 40) steps) and compares only queries exact on both
   sides; make_gates_026 recomputes clause a from the stored records rather than trusting the runner's own count.
8. **Expected weak results published as is (Observed, smoke).** In the smoke S2 was slower than S1 at scale12 eps 0 and
   certificates were near 0 for every arm. Clause b may fail; that will be published, not tuned.
