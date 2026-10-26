# Brute v0.8.0 → v0.9.0: next iteration (proposal, not pre-registered)

The previous note is in `docs/research/v0.8.0/NEXT_ITERATION_FROM_v0.7.0.md`. Labels are as in the README. Nothing here is evidence until it is pre-registered and run on fresh seeds.

## Where v0.8.0 leaves things (Observed, study-010, 12/17 gated pass)

- **Alignment works for coverage.** SP8 is SC7 with a lookahead (LU-C) that counts what SC7 would actually certify.
  - It is the first arm to pass G6b: SP8 − A2 −0.0167 [−0.0228, −0.0113].
  - Against SC7 it gains +0.0345 [0.0272, 0.0420]. On breadth, BSP8 − BSC7 is +0.0195 [0.0100, 0.0297].
- **Alignment does not make it safe.** SP8 issues 3 non-drift false certificates on drift4 (SC7 4). None was public.
- **The one-step jump hull is safe but useless.** J8 has 0 drift4 false certificates and 0 coverage in every family. On drift4, 69% of hull steps admit every code.
- **The silent-jump hypothesis H_c is refuted on fresh seeds.** Only 2 of 7 non-drift false certificates are at d+1 with no event at d (GD clause i), although the replay on sealed study-009 data found 9/9. The 7 events come from only 4 drift4 seeds, and SC7 and SP8 share 3 of them. Per certificate, the lags after the drift are 1, 1, 2, 2, 2, 4 and 4 steps. The lag-1 pair is plain `Y1k`. The rest are `tracked-calm` (lag 2) or `Y1k-recent` (lag 4), all on the taken action.
- **Run discipline works.**
  - The whole study took 1,970 s against a 7,200 s cap.
  - G11 passed in-cap (648/648 and 144/144, mutation 20/20), GX2_010 passed (100% of steps, 0 mismatches), and GTI passed in-cap.
  - G_RT fails only on an optional phase that hit its own budget.

## Recommendation for v0.9.0 (Inferred; pre-register before any v0.9.0 code)

1. **First, a lag diagnostic on seen data.** Before any new rule, classify every drift4 non-drift false certificate in sealed studies 008–010 by:
   - lag after the drift;
   - certifying rule (`Y1k-recent` / `tracked-calm`);
   - which event, if any, fired in between;
   - whether the true machine left the region before or after the certificate.

   Label this *Observed* on seen data, not v0.9.0 evidence, as in the study-009 replay. The v0.8.0 lesson is that seen-data replays can mislead: 9/9 became 2/7. So the v0.9.0 hypothesis must be stated with a fresh-seed prediction and a pass threshold.
2. **A k-step jump hull, used only where it can matter.** J8 applied the hull everywhere and lost all coverage. A candidate J9 combines:
   - SP8's certification and LU-C;
   - a hull check only for certificates issued within L steps after an observation that left the region's projection unchanged (an unsurprising step, where a jump could hide).

   L is fixed from the lag diagnostic. Gate it on G3′ + G6b as GA1, with SP8 as the comparator. Prediction: Open.
3. **Region re-entry after a jump.** Maintain a second region conditioned on "one jump at some step in the last W". Certify only when both regions agree on the code. This tests whether the stale certificates are model-class violations over a longer window.
4. **G_RT semantics, pre-registered and not retroactive.** Split G_RT (i) into:
   - mandatory work complete inside the cap (gated);
   - optional phases complete (reported).

   v0.8.0 stays FAIL.
5. **Clean-clone check before the run.** Add a test that every sealed file a scoring script reads is tracked by git. RUN_STATE_010 was ignored (DEVIATIONS_010 #34). Add a `verify_release_090 --long` that re-runs G11 on a pre-registered sample inside its own cap.
6. **One step toward breadth (ungated feasibility).** Measure SAT region cost at 7–8 states with symmetry breaking, so that a later study can widen the model class. The projection is reported, not gated.

Deferred and still **Open**:
- stochastic worlds (credal regions);
- learned family selection and model-class growth;
- grounding beyond templates;
- independent audit;
- the cause of the VM heartbeat gaps.

Nothing here shows general intelligence. Each step only widens what the system can certify soundly.
