# Study-017 deviations, addendum 2 (#96)

Written after BRUTE_SOURCE_FREEZE_017 (commit 0b3ad52) and before the scoring freeze and run_start_017. No held-out seed
has been run. BRUTE_DEVIATIONS_017.md (#86-#91) and ADDENDUM_1 (#92-#95) are unchanged and stay in force.

**#96 (disclosure, no rescoring): a stale assertion in a frozen new test.** The GTI smoke
(results/smoke-017/GTI_SMOKE_017.json, run_tests_0150 on the pre-freeze tree, wall 3200 s) failed exactly one undeclared
test: `test_scripts_017.Orchestrator017.test_streams`. Line 93 of tests/test_scripts_017.py still expects the stream
table entry `'g11': (4, 2400, ['transfer'])`; deviation #92 set G11_WORKERS = 6, and lines 95-96 of the same test
assert 6. The orchestrator is right and the line-93 literal is stale (Exact). tests/test_scripts_017.py is listed in
BRUTE_SOURCE_FREEZE_017 and is not edited.

Consequence, declared in advance: GTI_test_isolation clauses (i) only declared failures and (v) new tests pass are
expected to FAIL in the held-out run on that one test. GTI is scored as registered and the failure is published; no
known-failing entry is added and no verdict is changed (Inferred, prediction).

Corrective test outside the freeze: tests/test_streams_017_R1.py asserts the correct stream table
(transfer 4w 3000 s, gti 2w 3600 s, repro 2w 1500 s after transfer, g11 6w 2400 s after transfer) and is bound by the
scoring_freeze_017 ledger entries and, at release, by BRUTE_RELEASE_FREEZE_0150. It is reported, not a gate.

Timing note (Observed): the GTI smoke took 3200 s of the 3600 s gti budget on a box that was also running the mutation
smoke. A GTI STUDY_BUDGET overrun in the held-out run is possible and would be published. Budget unchanged.
