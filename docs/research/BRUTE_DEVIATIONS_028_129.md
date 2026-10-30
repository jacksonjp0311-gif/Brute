# Deviation #129 (study-028, v0.25.0): process events after the source freeze

Written after the run. Nothing here changes a gate, a threshold, a frozen file or a sealed result. Labels as in #128.

1. **Run completed without interruption (Observed).** run_start_028 was ledgered at 12:32 EDT and the runner
   launched once, detached: 51/51 cases in 1053.8 s against a 1800 s cap, with a normal exit. The snapshot pusher
   pushed 4 snapshots (17, 32, 43 and 51 cases; 2da1821, 6724ce3, a208439, 6423e6d) and stopped after the runner
   exited. At 12:38 EDT a monitoring tool call (a sleep) was aborted by the host. The live run and the pusher were
   unaffected (checked with ps), and nothing was relaunched. The resume-after-reboot clause was not needed and
   remains NOT approved.
2. **Frozen gate script cannot read wall-clock fields (Exact).** scripts/make_gates_028.py reads case records from
   SCIENTIFIC.json. no_time() strips every *_informational key from that file, so GQB raised KeyError on
   'query_max_informational' before any gate was computed, and no GATES file was written. This is the same input
   defect that #127 item 3 recorded for the v0.24.0 diagnosis. It should have been caught by a pre-freeze test that
   ran make_gates on a sealed smoke block. test_scripts_028 only ran it on an empty directory. Fix (new files,
   frozen files untouched):
   - scripts/make_gates_028b.py imports the frozen gate module and calls it unchanged (same code, same thresholds).
     The only difference is that it hands the module the sealed RESULTS.json after checking two things:
     sha256(RESULTS.json) equals the seal, and no_time(RESULTS.json) equals SCIENTIFIC.json byte-for-content.
     It writes results/study-028/GATES_028.json and records `scored_by`.
   - scripts/verify_release_0250b.py repeats the frozen verifier's checks. It replaces step 4 with
     make_gates_028b --check and also checks that the frozen make_gates_028.py and verify_release_0250.py are
     unchanged against BRUTE_SOURCE_FREEZE_028. The release is verified with 0250b.
   The crash happened before any gate was computed, so the fix was not chosen with knowledge of a gate outcome
   (Exact: the only result seen before the fix was the recount's F totals).
3. **api_check runtime (Observed).** api_check_028 (4 scale8 cases, 60-step cap, 4 processes) finished in 1.5 s
   with 4/4 equal. It was started once, in the background, under `timeout 1200`.
4. **S1 false certificates (Observed).** The recount finds F(S1) = 3, all on stress (eps 0.05) cases. S1 has no
   noise model, and clause d gates S3 only. This is published, not gated.
