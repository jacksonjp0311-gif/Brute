# v0.5.0 process notes (input for BRUTE_DEVIATIONS_007; times EDT, author-set)

- 05:25: while writing experiments/v050_reference.py the author printed the transition/emission tables of the four
  breadth worlds for held-out seed 1710001 (one per family) to eyeball the generator. No learner was run and no outcome
  was looked at; later smoke checks use seeds 901-903 (outside every study range). Disclosed, not a deviation of criteria.
- 05:30-05:41 (implementation, pre-freeze; smoke seeds 901-903 only): A5 vs A4 step-by-step on all eight 2x2 families x 3
  mask rates x seeds 901-903 = 3168 steps, 0 differences (Observed, smoke). ood6s3 smoke seed 901 has a minimal Moore
  machine of 4 states (EVALUATOR_ONLY field): declared-out-of-family worlds can be in-family in fact; the plan scores
  ood6s3 by declaration, recorded per case, no change.
- ~05:50 (pre-freeze fix to the second implementation, separate commit): the smoke count (324 arm traces, 24/24
  mutations detected) flagged 2 traces (sens3 903 0.1 B5/BP5, step 7): the residual equalled the smoke tau7 at 12 d.p.
  The plan defines residual = mean of the last W surprises rounded to 12 d.p. and alarm iff residual > tau; the brute
  learner does that; experiments/v050_reference.py reused the frozen v040_reference._Alarm, which compares the UNROUNDED
  mean. Residuals take discrete values and tau7 is itself a rounded residual, so ties are plausible on held-out data.
  Fix: v050_reference._Alarm12 (rounded) for the A5/M5 and breadth audits. The frozen A4 audit (v040_reference.audit_full)
  keeps the unrounded comparison: an exact tau6 tie in an A4 trace would be reported as a mismatch, not hidden.
  This changes the reference AFTER brute/ files exist (ordering rule (2)<(3) is kept for the original reference commit
  1b57efe; the fix commit is listed as a deviation).
- ~05:55 (pre-freeze, infrastructure; no science change): Checkpoint tolerates a torn final JSONL line (that job is redone);
  study SEAL also binds calibration_traces_sha256; added scripts/study007_storage.py, scripts/run_study_007.sh,
  scripts/make_freeze_007.py and the study-007 .gitignore entries (raw RESULTS/SCIENTIFIC/TRACES/checkpoints, committed as
  deterministic .json.gz bound by SEAL).
