# Brute v0.10.0 → v0.11.0: next iteration (proposal, not pre-registered)

The previous note is in `docs/research/v0.10.0/NEXT_ITERATION_FROM_v0.9.0.md`. Labels are as in the README. Nothing here is evidence until it is pre-registered and run on fresh seeds. The longer path is in `docs/ROADMAP_TO_GI.md`.

## Where v0.10.0 leaves things (Observed, study-012, 18 of 24 gated pass)

- **Transfer works when the prior is right.** TRp (a motif library from a same-family source) reached its first certificate 20.18 steps sooner than SP8 from scratch, seed-paired CI95 [19.18, 21.17]. It helped 270 of 288 cases and hurt none, and issued 0 false certificates in 20,027 (15,781 of them from the transfer rule). GT_b and GT_ref (288/288 audited, 0 mismatches) pass.
- **Transfer is unsound when the prior is wrong.** TRn (a rotated, unrelated-family library) issued 167 false certificates, all from the transfer rule (322 transfer-rule certificates), in 50 of 288 cases, before every one of its 288 cases disabled the library. It also "helped" (S_n 4.53 [3.37, 5.73]). GT_a and GT_c fail.
- **J10 recovers a little coverage and keeps lag ≥ 2 safety.** J10 − J9 +0.0090 [0.0059, 0.0122] (GJ10 pass). J10 has 0 non-drift lag ≥ 2 false certificates (G3L pass) and 1 at lag 1, so strict G3′ fails. J10 − A2 −0.1657 [−0.1767, −0.1551]: G6b fails and so does GA1_012.
- **7–8 states are sound but almost silent.** 0 false certificates in 193 (J10_78 24, SP8_78 169). Coverage is 0.35% / 0.12% (J10 at n7 / n8) and 1.6% (SP8 at n7), so the rule-of-three bound for J10_78 is only 0.125.
- **GTI fails as frozen** on 3 declared-in-advance test_release_080 failures (deviation #50). The K_080 reading (R_GTI_K080) passes. The 0.10.0 version bump also turns test_release_090's version and verify tests red, which v0.11.0 must declare up front.
- **Run discipline held.** 1,700 s of 7,200 s. Every stream completed, including g11's optional rest (108/108 traces), so R_G_RT_strict is true for the first time.

## Recommendation for v0.11.0 (Inferred; pre-register before code)

1. **Make transfer sound by construction.** Never replace the region with the library. Either (a) *intersect*: certify only if the answer is forced on the full region **and** on the library-restricted region, so that the library can only add evidence about *which* certificate to try first (planning), not license one; or (b) *verify the library first*: let the transfer rule certify only after the library has survived an applicability test (k observations consistent with at least one relabelled copy and with no library-external machine in the region with a different answer). Gate on 0 false certificates with TRn as the mandatory negative control. Prediction: (a) is sound (*Exact*, by the subset argument) but its speedup is *Open*.
2. **Use the library for experiment choice, not certification.** This is the cheapest sound route to speedup. Score its contribution separately (GT_b-planning).
3. **Declare the known-red frozen tests in the plan** (K_080 plus K_090: the test_release_090 version/verify tests), so that GTI measures isolation rather than version drift.
4. **big78 power:** run more steps per case (≥ 96) or fewer, larger cases so that a soundness pass has a rule-of-three bound ≤ 0.02.
5. **The G6b gap (~0.16 below v0.2.0) is structural for window hulls.** Stop gating window-hull arms on G6b. Test a surprise-triggered *local* re-check instead (Open).

Deferred and still **Open**: sub-machine concepts (ROADMAP_TO_GI v0.11+), stochastic worlds, grounding beyond templates, independent audit, and the cause of heartbeat gaps (one 44 s gap in study-012).

Nothing here shows general intelligence.
