# Brute v0.20.0 pre-registration: flat anytime schedule (study BRUTE-0200-FLAT-ANYTIME-022)

**Plan only.** No v0.20.0 code, reference, held-out world, seed or run exists at this commit, and building is not
authorised by it. `experiments/BRUTE_PLAN_022.json` is the binding text; this page is the readable copy, and the JSON wins
where they differ. Criteria hash: `experiments/BRUTE_PLAN_FREEZE_022.json`.

## Why (from study-021)

- *Exact (code, eps_bar 0.02, delta 0.01).* The v0.19.0 anytime margin m_a(b) against the planned margin m(B = 176):

  | bit | m_a(b) | m(176) |
  |---|---|---|
  | 10 | 2 | 3 |
  | 28 | 4 | 4 |
  | 56 | 7 | 5 |
  | 88 | 9 | 6 |
  | 176 | 13 | 9 |

  The 6/(π²b²) schedule spends delta too early.
- *Observed.* RGNA4 was sound, with 0 false certificates in 240 cases. Late coverage was 0.265 against 0.493 for RGNB4,
  and the early-window clause failed (dC_early28 −0.0040).
- *Open.* Why early coverage is lower although m_a ≤ m up to bit 28.

## What is tested

- **Headline arm RGNA5.** Per-bit crossing budget w(b) = delta·c / (b·ln²(b+1)), with c fixed in exact rationals so
  that Σw ≤ delta. The schedule is horizon-free. An Exact lemma and a DP reference come before any code.
- **GAS_flat (gated).**
  - (a) 0 false certificates on all 240 noisy main cases.
  - (b) CP95 upper bound ≤ 0.05.
  - (c) dC_late(RGNA5 − RGNA4) at eps 0.02 > 0, with CI lower bound > 0.
  - (d) C_late(RGNA5) ≥ 0.20, with CI lower bound > 0.15.
- **GAS_3action (gated).** RGNA5_3 has 0 false certificates on 96 alphabet3 cases, and CP95 ≤ 0.05.
- **Controls and process (gated).**
  - GAS_frozen_control: RGNA4's CI overlaps study-021's.
  - GS_a10, GS_ref10, GAPI10 (`brute.certify/9`), G_recount, G10, G12, G13, G_RT, G_HB.
  - GTI with K_0190, plus clause vi: no v0.20.0 release test or verifier may be in the tree at run_start.
- **Reported only.** R_early_diag (early-gap decomposition), the coverage-by-window trade-off curve, per-bit coverage, and
  stress at eps 0.05.

## Process (carried, plus the #107 fix)

- Release tooling is written only after run_end_022, and a pre-run check enforces this.
- Source freeze comes first, then the scoring freeze at least 600 s before run_start.
- The run is fully detached, with a watchdog and a sentinel, under a hard 2 h cap. There is no extension and no rerun.
  Gates whose inputs are incomplete at the cap are FAIL.
- Rate math uses the ×1.75 rule plus the mean path, on smoke seeds.
- Proposed held-out seed ranges are 88x0001–; their disjointness is checked before any run.
- Deviations are numbered from #108.

## Predictions (Inferred)

- GAS_flat (a)–(c) hold.
- (d) is likely to hold.
- RGNA5 stays below RGNB4 in the late window.
