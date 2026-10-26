# Study-011 rate math (before the source freeze)

BRUTE_PLAN_011 stop_rule.rate_math says: turn the smoke timings into a projected wall time for each stream before the source freeze. A mandatory stream that projects above 70% of its budget may have its budget or worker split changed once, as a disclosed deviation. Nothing changes after run_start.

Timings come from the shared 8-CPU box (Observed). The projections are Inferred. A factor of 2x is applied for contention, because 2x2 (4 workers), gti (2 workers) and feas (1 worker) run at the same time.

| stream | smoke measurement (Observed) | projection for the held-out run (Inferred) | budget | projected share |
|---|---|---|---|---|
| 2x2 (4 workers, mandatory) | 0.922 s CPU per case over 16 smoke cases (per-arm share: J9 7.08 s, SP8 6.07 s, A4 0.80 s, A2 0.81 s) | 792 x 0.922 / 4 = 183 s; about 365 s with 2x contention | 1800 s | about 20% |
| gti (2 workers, mandatory) | 970.6 s wall for the GTI smoke at 06:17-06:33 EDT (run_tests_090 incl. clean-tag runs); study-010 gti spent 1237 s under run load | 970-1400 s | 2400 s | 40-58% |
| repro_2x2 (2 workers, after 2x2) | 264 cases at the 2x2 rate | about 122 s; about 245 s with contention | 900 s | about 27% |
| g11_2x2 mandatory (2 workers, after 2x2) | mandatory_done at 1.9 s for the 16-case smoke | 216 cases: about 26 s; rest (576 cases): about 70 s; about 200 s total with contention | 1500 s | about 13% |
| feas (1 worker, optional) | 12 measurements in 2 s | 144 measurements: about 25 s | 1200 s | about 2% |

Critical path (Inferred): max(2x2 + max(repro, g11), gti) is about 1000-1400 s, which is 14-20% of the 7200 s cap.

**Decision.** No mandatory stream projects above 70% of its budget, so no budget or worker change is made (Exact: the budgets in scripts/run_study_011.py equal stop_rule.streams_and_budgets).

## What the smokes showed

- **GTI smoke verdict (Observed).** The smoke verdict was FAIL, clause (i). Three tests failed that the plan does not declare:
  - test_brute_repro.test_manifest_matches_tracked_files
  - test_release_080.test_fast_verify_passes
  - test_release_080.test_untampered_copy_passes

  The tree was dirty while the smoke ran (scoring-script drafts were untracked and the ledger had changed). Re-run on the clean committed tree at 06:36 EDT, the manifest test and the 080 fast-verify test both pass (Observed, 62 s). So the held-out run starts from a clean, committed tree, and nothing is committed until gti has finished.
- **Feasibility rate.** This is only a 2-second smoke. Its projection of 25 s comes from 12 measurements, not from n=8 at T=32 under load (Inferred).
- **Kill drill.** The watchdog killed the run at the deadline. It fired 0.002 s late, kill latency was 0.228 s, nothing survived and SIGKILL was not needed (Observed, results/study-011/KILL_DRILL_011.json).
