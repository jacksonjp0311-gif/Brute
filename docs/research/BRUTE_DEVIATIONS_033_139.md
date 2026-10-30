# Deviation #139 (study-033, v0.30.0): run record, clock and post-run findings

Written after the main run; it changes no threshold, gate or label. Times are box-local EDT (UTC-4). Labels: Exact,
Observed, Simulated, Inferred, Rejected, Open.

1. **One main run (Observed).** run_start_033 ledgered at 17:05:54 EDT; the runner (pid 302853, 8 workers) ran the 36
   main cases once from an empty checkpoint; total_elapsed_informational 116.0 s; push_checkpoint_033 took one snapshot
   (4b67a3b) and recorded the runner's exit at 17:07:53 EDT. No rerun, no resume, no tuning.
2. **Clock (Observed).** At 16:42 EDT the box read 11 s ahead of GitHub's Date header; at 17:09:41 EDT the box and the
   GitHub API Date header (21:09:41 GMT) agreed to the second. No stall was seen; ledger times are non-decreasing.
3. **A8 WRONG on 5 cases (Observed).** scale12 9920002, 9920005, 9920009, 9920012 and scale8 9910012. In every one, A8
   stopped 'unique' with n_min below the truth's reachable size (11, 11, 11, 10 of 12; 6 of 8); the final machine is
   consistent with the trace, and the truth stays consistent with every round (truth_inconsistent 0, recount and the CNF
   reference agree, words unsound 0). Every case where A8 stopped 'unique' with n_min equal to the truth's size was ID.
4. **Diagnosis (Inferred).** The 031 identify certificate proves "exactly one machine at the least consistent size", not
   "the truth". Active words remove the rivals at that size quickly; once one small machine remains, A8 stops, though a
   larger machine (the truth) is still consistent. The passive arms never reach uniqueness at those sizes, so they show
   AMB instead. The plan's "sound by construction" claim holds for elimination (no machine was removed without a real
   observation) but is Rejected for the stop rule: uniqueness at n_min is not identification.
5. **Residual AMB (Observed).** All 8 'indistinguishable' stops had same_future True (the two machines agree on every
   future input from their current states): start-state or unreached-past ambiguity that no experiment can resolve.
6. **IDU (Observed).** 4 of 6 scale16 cases ran out of the 10 s per-query cap (A8_capped_queries 4).
7. **Smoke (Exact).** The pre-freeze smoke crash and rerun are in #138 item 11; no other deviation.
