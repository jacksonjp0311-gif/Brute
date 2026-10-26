# Brute v0.8.0: pre-registered plan for study-010 (BRUTE-080-ALIGN-010)

**Status:** pre-registered. No v0.8.0 code, held-out world, seed or run exists at the freeze commit.
The binding text is `experiments/BRUTE_PLAN_010.json`. If this page and the JSON differ, the JSON wins.
The ledger entry `preregistration_010` records the JSON's sha256 and the canonical-JSON sha256 of its `criteria` block.
Every prediction below is **Inferred** unless marked otherwise.

## Why this study
Study-009 (v0.7.0) passed 9 of 17 gates. It failed G3′ (stale false certificates after drift), G6b (SC7 coverage −0.050
vs v0.2.0), G11 (second implementation: no output in 9229 s), GX2″ (no-symmetry spot check over budget), GTI (never ran
in-cap) and G_RT (the 3 h cap fired 18 min 36 s late). Study-010 targets the cause, not the symptom, of each.

## Targets and hypotheses

| Target | Hypothesis (short) | Gate |
|---|---|---|
| (a) hard cap | An independent watchdog with a heartbeat enforces a 2 h wall-clock cap; streams completing after it score STUDY_BUDGET | **G_RT** |
| (b) verification in-cap | The second implementation audits a fixed mandatory sample (216 2x2 + 72 breadth traces) with 0 mismatches inside budget; the symmetric incremental xcheck covers all breadth cases; a 24-step no-symmetry spot check on 6 act3/sens3 cases completes | **G11, GX2_010** |
| (c) cause of stale certificates | A stale post-drift certificate is a model-class violation: the jump at d is silent (no event can fire at d), so ≥ 0.8 of non-drift false certificates sit at d+1 with no event at d | **GD** |
| (c′) price of silent-jump safety | **J8** = S7 ∧ jump-hull union == {c}. Sound against one silent jump by construction, but while fewer states are visited than the bound, a jump into a fresh state is consistent and the hull is all codes, so coverage collapses | G3′ (pass), G6b (fail) predicted |
| (d) G6b gap | **SP8** = SC7 certification with the **aligned lookahead LU-C**: the action score counts exactly what SC7 would certify next step (calm → tracked single support; otherwise Y1k), instead of LU-R's Y1k-only count | **G6b**, **GA1_010** |

**GA1_010:** some arm X ∈ {SP8, J8} passes G1, G2, G3′ and G6b on the same run. **Predicted FAIL** (J8 loses
coverage; SP8 keeps the silent-jump weakness).

## Arms
- **2x2:** J8, SP8 (new); SC7, A4 (v0.90 control), A2 (G6b baseline) frozen.
- **Breadth:** BSP8 (new, LU-C on k actions); B5, BSC7 frozen.
- Dropped from study-009: R6, C6, S7, A5, BS7 and the planning block (scored in study-009; disclosed).
- No new constant: τ6 1.645215321642, τ7 2.07944154168, factor 0.5, W 8, burn-in 8.

## Seeds (disjoint from every earlier range; max prior 2190030)
- 2x2: cycle3 3010001–024, switch3 3020001–024, unstructured3 3030001–024, unaliased2 3040001–024, ood4 3050001–024,
  perm4 3060001–024, ood5 3070001–024, drift4 3080001–048.
- Breadth: big6 3110001–024, sens3 3120001–024, act3 3130001–024, ood6s3 3140001–024.
- Smoke: 3190001–3190030 (or study-009 smoke 2190001–2190030).
- Masks 0.1 / 0.35 / 0.6; 44 steps (2x2), 64 steps (breadth).

## Gates (thresholds in the JSON)
GA1_010, G1, G2, G3′, G6b, GD, G4, G5, G7, G9, G10, G11, GX2_010, G12, G13, GTI, G_RT: 17 gated.

## Stop rule
- 2 h wall-clock cap from RUN_T0. Budgets: 2x2 1500 s, breadth 2400 s, gti 2400 s, g11_2x2 1500 s,
  g11_breadth 1500 s, gx2_sym 1200 s, gx2_spot 1200 s, repro 900/1500 s; at most 8 workers.
- Projection at 5% (360 s) is reported; budgets already bound every stream.
- Watchdog: heartbeat every 2 s; kill at the deadline; kill latency recorded; smoke kill drill must show ≤ 15 s.
- Any gate with inputs incomplete at the cap, or produced after it, is FAIL (STUDY_BUDGET). No extension, no rerun.

## Pre-freeze disclosure (summary)
- **Late cap (Inferred):** the VM was paused across the deadline; no file changed 22:41–23:22 EDT and the kernel log
  shows VM-fork reseed events. A watchdog inside the VM cannot fire during a pause, so the cap is also enforced at scoring.
- **Seen data (Observed):** every study-009 non-drift false certificate (S7 4/4, SC7 5/5) is at d+1 with no event at d.
- **Scratch prototype on study-009 smoke seeds only (Observed, smoke, n=20):** coverage A2 0.206, SC7 0.144, SP8 0.190;
  J8 0.000; 0 false certificates in-family. Held-out seeds of this plan were never generated.
- **Reference timing (Observed):** S7/SC7 audits ≤ 0.6 s per trace; BSC7 ≤ 13.7 s. The study-009 g11 overrun was the
  planning audit (Inferred).

## Deviations
Recorded in `docs/research/BRUTE_DEVIATIONS_010.md`, numbering continuing the project-wide sequence (from 27).
