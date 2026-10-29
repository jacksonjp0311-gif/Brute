# Brute v0.20.0 → v0.21.0: next iteration (proposal; docs only)

The previous note is in `docs/research/v0.20.0/NEXT_ITERATION_FROM_v0.19.0.md`. Labels are as in the README. Nothing
here counts as evidence until it runs on fresh seeds. The pre-registered plan is `experiments/BRUTE_PLAN_024.json` and
`docs/research/v0.21.0/PLAN_024.md`: a plan only, with nothing built.

## Where v0.20.0 leaves things (Observed, study-023, 12 of 13 gated pass)

- **The likelihood-ratio anytime bound is sound and useful (GLR a-e pass).**
  - RGL4: 0 false certificates on 240 noisy main cases; CP95 0.0124.
  - C_late at eps 0.02: 0.417 [0.376, 0.459], +0.192 over RGNA4.
  - Stress: 0 false certificates on 30 cases.
- **It still trails the planned horizon.** RGNB4's C_late is 0.530, so dC_late is -0.113 [-0.155, -0.073].
- **Early coverage is near zero for every noise-robust arm.** C_early28 at eps 0.02: RGL4 0.0024, RGNA4 0.0003,
  RGNB4 0.0039. Why is *Open*.
- **G_HB FAIL.** 6 gaps over 10 s, max 47.6 s. The dry run showed the same pattern, so a host pause is likely
  (*Inferred*).
- **GCC FAIL (#112).** A git-history clause cannot be evaluated in a git-archive tree.
- **False-start orchestrator (#111).** The launch shell had leaked dry-run settings.

## Proposal for v0.21.0 (headline GLS: a horizon-stitched likelihood-ratio bound)

1. **RGL5: stitch the LR bound over a geometric grid of horizons** (28·2^k), spending delta_k ∝ 1/((k+1)(k+2)).
   - It is still anytime, but inside each epoch it uses a planned-horizon threshold.
   - An exact lemma and a DP reference come before any code.
   - Gate GLS:
     - soundness as in GLR (a), (b);
     - dC_late(RGL5 - RGL4, eps 0.02) mean ≥ 0.04, CI lower > 0;
     - dC_late(RGL5 - RGNB4, eps 0.02) CI lower > -0.06.
2. **Early-window diagnostic (reported, ungated).** For each step ≤ 28, report the minimum number of consistent
   observations a robust arm needs before it can certify a bit, against what the trace supplies.
3. **Process fixes (gated, from #111 and #112).**
   - The launcher refuses to start if any dry-run hook is set.
   - The orchestrator logs its resolved directory on its first line.
   - Gate clauses that read git history read a tracked commit-order file written before the freeze.
   - The clean clone runs on a `git clone`.
4. **Heartbeat.** G_HB stays at 10 s with no loosening. A host-pause probe runs before the run, and its result is
   reported.
5. **Carried over.** Hard 2 h cap, independent watchdog, sentinel, frozen resume rule, rate math with the x1.75 rule,
   and release tooling committed after run_end.
