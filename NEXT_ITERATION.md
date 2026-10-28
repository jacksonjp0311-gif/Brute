# Brute v0.19.0 → v0.20.0: next iteration (proposal; docs only)

The previous note is in `docs/research/v0.19.0/NEXT_ITERATION_FROM_v0.18.0.md`. Labels are as in the README. Nothing here
counts as evidence until it runs on fresh seeds.

## Where v0.19.0 leaves things (Observed, study-021, 12 of 14 gated pass)

- **The anytime margin is sound (GAH_anytime a, b, d pass).** RGNA4: 0 false certificates on 240 noisy main cases, CP95
  upper 0.0124; C_late(eps 0.02) 0.265 [0.215, 0.317]; stress (eps 0.05) 0 false on 120 cases.
- **It does not certify earlier (clause c FAIL).** dC_early28(RGNA4 - RGNB4, eps 0.02) = -0.0040 [-0.0068, -0.0018];
  late it gives up 22.8 points (RGNB4 0.493).
- **Why (Exact from code, eps_bar 0.02, delta 0.01).** The 6/(π²b²) schedule spends most of delta in the first bits, so
  its margin m_a(b) grows faster than the planned margin: m_a vs m(B = 176) is 2 vs 3 at bit 10, 4 vs 4 at bit 28, 7 vs 5
  at bit 56, 9 vs 6 at bit 88, 13 vs 9 at bit 176. Why early coverage is still lower when m_a ≤ m before bit 28 is *Open*.
- **GTI FAIL (#107)** came from committing release tests before run_start. Heartbeat clean (3.3 s); run 4801 s of 7200 s.

## Proposal for v0.20.0 (headline GAS: a flatter anytime schedule)

1. **Heavier-tailed schedule (RGNA5).** Spend delta per bit ∝ 1/(b·ln²(b+1)), normalised so the sum is at most delta. It is
   still horizon-free, and spends more than 1/b² late. Exact lemma and DP reference before code.
   - Gate GAS: soundness as GAH (a, b); usefulness C_late(RGNA5, eps 0.02) - C_late(RGNA4) > 0 with CI lower > 0.
   - Reported: the gap to RGNB4 at each window; the early-window puzzle above, as a diagnostic.
2. **3-action alphabet at 88 steps (reported, soundness-gated).** RGNA5_3 on 96 cases; 0 false certificates required.
3. **GTI tooling-order rule.** Release tests enter the tree only after run_end; GTI fails a run that finds a
   test_release file for the version under test at start. A pre-run check enforces it.
4. Carried: hard 2 h cap, independent watchdog, sentinel, frozen resume rule, rate math with the x1.75 rule.
