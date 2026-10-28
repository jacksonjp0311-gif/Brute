# Brute v0.18.0 → v0.19.0: next iteration (proposal; docs only)

The previous note is in `docs/research/v0.18.0/NEXT_ITERATION_FROM_v0.17.0.md`. Labels are as in the README. Nothing here
counts as evidence until it runs on fresh seeds.

## Where v0.18.0 leaves things (Observed, study-020, 10 of 12 gated pass)

- **Long horizons make the sequential margin useful (GLH_horizon PASS).** On 88-step traces, RGNB4 has:
  - 0 false certificates on all 240 noisy main cases, with 0 margin crossings and a CP95 upper bound of 0.0124;
  - C_late(eps 0.02) = 0.482 [0.430, 0.537], against the 0.10 bar;
  - a late-window gain over RGN4 of dC +0.053 [0.043, 0.063].

  For comparison, on 28-step traces in study-019 it reached only C 0.052.
- **Partial answers help (reported).** Per-bit late coverage is 0.596 at eps 0.02, with 0 false bits on the 360 main cases.
- **The early-window control fails (GLH_early_control FAIL).** C over steps 1-28 is 0.0025, against study-019's 0.052.
  The mechanism is Exact from code: `boundary(B)` spends the crossing budget as delta·b/B. At B = 176 the margin is
  m = 4 at bit 28 and 5 at bit 56; at B = 56 it is 3 and 4. A longer planned horizon therefore buys late coverage with
  early coverage. The control was mis-specified (#106).
- **G_HB failed** because of the box restart (1083.5 s) and four 27-58 s gaps after the relaunch. The frozen resume rule
  worked: every stream resumed from its checkpoint, and the run finished at 6740 s of the 7200 s cap.
- **Stress** (eps 0.05, no guarantee): RGNB4 was false on 5 of 120 cases and RGN4_or on 0.

## Proposal for v0.19.0 (depth headline GAH: anytime margin)

1. **Anytime boundary (RGNA4).** Spend the crossing budget with a horizon-free schedule, delta·6/(π²·b²) per bit (sum ≤
   delta). No planned B is needed, and early margins do not grow with the horizon.
   - Gates: soundness as GLH (a, b) on 88-step noisy main cases (Exact lemma written before code).
   - Usefulness: C_early28(RGNA4, eps 0.02) > C_early28(RGNB4) with CI lower > 0, and C_late(RGNA4) ≥ 0.10.
   - Reported: the anytime-vs-planned trade-off curve.
2. **Streaming API `brute.certify/8`.** Callers can ask for certificates without declaring the trace length.
3. **Breadth (reported or soundness-gated).** 3 actions at 88 steps.
4. **Process.**
   - A pre-registered resume drill (kill and relaunch inside the smoke).
   - G_HB stays as frozen (max gap ≤ 10 s). Restart gaps are reported separately and are not excused.
   - The early control is replaced by a same-B frozen-code check.
5. **Same discipline.** Fresh disjoint seeds, a numpy reference, rate math, a source freeze, a scoring freeze ≥ 600 s
   before run_start, a 2 h cap, the watchdog and the sentinel.

## No CI

No `.github` directory and no GitHub Actions workflows.
