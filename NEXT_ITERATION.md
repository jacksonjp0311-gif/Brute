# Brute v0.9.0 → v0.10.0: next iteration (proposal, not pre-registered)

The previous note is in `docs/research/v0.9.0/NEXT_ITERATION_FROM_v0.8.0.md`. Labels are as in the README. Nothing here is evidence until it is pre-registered and run on fresh seeds.

## Where v0.9.0 leaves things (Observed, study-011, 15/17 gated pass)

- **The window hull makes certification drift-safe.** J9 (SP8 plus a selective K=4 window hull) issued 0 non-drift false certificates on drift4, at any lag. Strict G3′ passed for the first time on any arm (SP8 16, v0.9.0 control 323). Its 8 false certificates (6 taken, 2 counterfactual) are all at drift steps themselves, which no causal rule can avoid.
- **It costs almost all coverage.** J9 − A2 −0.1918 [−0.2073, −0.1772]; J9 − SP8 −0.1660 [−0.1803, −0.1520]. J9 coverage is 0.067 on cycle3 (SP8 0.286), 0.064 switch3, 0.029 unstructured3, 0.021 perm4, 0 unaliased2. On cycle3, 38% of hull steps admit every code; on drift4, 68%.
- **SP8's false certificates are not mostly lag-1 this time.** SP8 non-drift lags {1:11, 2:3, 3:1, 4:1, 6:1, 8:1}. The seen-data diagnostic (23/28 at lag 1) over-predicted the lag-1 share (11/18 fresh).
- **Run discipline held.** 1,812 s of 7,200 s; every mandatory stream complete; GTI clean; G11 mandatory 0 mismatches, mutation 20/20; GLV 33 cases 0 mismatches in 363 s.
- **7–8 states are cheap to decide.** All n6–n8 feasibility cells were feasible with millisecond median solve times (ungated).

## Recommendation for v0.10.0 (Inferred; pre-register before code)

1. **Make the hull informative instead of tighter.** The hull fails mostly because K-step windows admit every code. Candidate J10: certify when the window hull agrees, *or* when SP8 certifies and no observation in the window is unexplained by the current region (a surprise test), and gate GA1 on G3L + G6b against SP8. Prediction: Open.
2. **Measure the coverage loss mechanism first, on seen data** (study-011, labelled exploratory): for each J9 downgrade, record whether the hull was all-codes, which window step widened it, and whether SP8's certificate there was true.
3. **Widen the model class to 7–8 states** in one family, using the feasibility numbers; gate soundness only.
4. **Keep the mandatory/optional G_RT split; give g11's optional rest its own cap stamp** so R_G_RT_strict can pass.
5. **Commit order:** commit scoring scripts strictly after the source freeze (DEVIATIONS_011 #43), and freeze the release verifier only after a dry run on a clone (#44).

Deferred and still **Open**: stochastic worlds; learned family selection; grounding beyond templates; independent audit; the cause of VM heartbeat gaps.

Nothing here shows general intelligence.
