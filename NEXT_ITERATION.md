# Brute v0.11.0 → v0.12.0: next iteration (proposal, not pre-registered)

The previous note is in `docs/research/v0.11.0/NEXT_ITERATION_FROM_v0.10.0.md`. Labels are as in the README. Nothing here counts as evidence until it is pre-registered and run on fresh seeds. The longer path is in `docs/ROADMAP_TO_GI.md`.

## Where v0.11.0 leaves things (Observed, study-013, 22 of 26 gated pass)

- **Applicability testing cuts wrong-prior errors but does not remove them.** False certificates fell as the confirmation threshold rose: TR (M = 0) 137 in 39 cases, AT4 (M = 4) 6, AT (M = 6) 3 in 1 case. The remaining case is one cycle3 hypothesis that is observationally aliased with a switch3 target for 7 informative predictions. GS_a, GS_c and GST fail.
- **The right library still speeds things up under AT.** ATp S 6.64 [5.73, 7.54], 0 false in 10,202. That is about a third of the unsafe v0.10.0 rule's speedup (TRp 21.15).
- **DR is sound but adds nothing.** DR ⊆ SP8 is *Exact*, with S = 0 in every case. **LX is sound but slower** (S −1.32 [−2.19, −0.50]).
- **G6b passes on SP8**, strict G3′ passes, GTI passes with K_080/K_090 declared, and big78 has power (0 of 360).
- **The embeddable API `brute.certify/1` exists and is tested** (GAPI). It is still a single-family library call.

## Recommendation for v0.12.0 (Inferred; pre-register before code)

1. **Make the license disagreement-based, not count-based.** Let the transfer rule fire only when the region holds no machine *outside* the library's span that disagrees on the queried reading, which is a margin check of the library against the full region. An aliased hypothesis then cannot license an answer the full region does not force. Prediction: sound by construction (*Exact*, subset argument), with speedup *Open*. DR showed the plain intersection gives S = 0, so the license must also be allowed to *choose* among answers SP8 leaves open, and only when the library is uniquely consistent. Pre-register both the false-certificate bound and the speedup.
2. **Use the library to pick discriminating experiments.** LX chose actions that confirm the library. Instead, choose the actions on which library hypotheses and the full region disagree most, so that a wrong prior is falsified fast. Gate it on ATn-style aliasing seeds.
3. **Add an aliasing stress block.** Make the seed 6120009 pattern (a wrong-family motif aliased with the target for at least 7 steps) an explicit pre-registered block, so that wrong-library soundness has power beyond 1 case in 288.
4. **Grow the API:** `brute.certify/2` with a family descriptor (states, mask bits, actions) chosen at call time, and an explicit `reason` on UNKNOWN. Keep it host-agnostic, with a contract test per version.
5. **Investigate the heartbeat gaps** (335 s and 94 s in study-013) before the next GTI budget is set.

Deferred and still **Open**: sub-machine concepts, stochastic worlds, grounding beyond templates, and independent audit.

Nothing here shows general intelligence.
