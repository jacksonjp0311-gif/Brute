# BRUTE_PLAN_020: v0.18.0 horizon study (pre-registered, not built)

Study `BRUTE-0180-HORIZON-020`. The JSON `experiments/BRUTE_PLAN_020.json` wins if this page differs. Plan sha256 `47c2fd6cbe8c786d588e250155bc2783650373aea81facd3c1647f7a92a265aa`; criteria hash `3ec898f2323b246667c06cce95ddb5586b7a1f8f183e2c474ff2af9919f3bd6f`.

**Build status:** not started. Building needs a new owner request.

## Question
Does the frozen v0.17.0 sequential-margin region (RGNB4) become useful at eps 0.02 on 88-step traces? (Open)

## Gated criteria
- **GLH_horizon**: {"a": "RGNB4 0 false certificates on all 240 noisy main cases (eps 0.01, 0.02) over all 88 steps", "b": "CP95 upper bound on the case-level false rate <= 0.05", "c": "C_late(RGNB4) at eps 0.02 >= 0.10", "d": "its 95% CI lower bound > 0.05"}
- **GLH_early_control**: C over steps 1-28 of RGNB4 at eps 0.02 reproduces the study-019 value within its CI (frozen-code check)
- **GS_a8_soundness**: RGNB4 0 false at eps 0 on all 120 cases over 88 steps
- **G_recount**: independent numpy second implementation recounts every gated number exactly
- **GS_ref8_reference_audit**: reference audit on all gated cases, 0 mismatching; mutation kill >= 20/20
- **GAPI8**: brute.certify/7 unchanged; brute.certify/8 added only if needed, additive, host-agnostic
- **G10_compute**: as study-019
- **G12_reproducibility**: repro set re-run bit-identical
- **G13_frozen_controls_reproduce**: frozen v0.17.0 controls reproduce
- **GTI_test_isolation**: full suite passes with declared K_0170; undeclared failures []
- **G_RT_study_runtime**: held-out run within the 2 h cap
- **G_HB_heartbeat_gap**: heartbeat max gap <= 10 s

## Reported only
- C_curve per step
- per-bit coverage and false counts
- stress eps 0.05
- RG4 / RGN4_or / SP8 coverage
- rate math projected vs observed

## Seeds
Held-out: {"cycle3": [8610001, 8610024], "switch3": [8620001, 8620024], "unaliased2": [8630001, 8630024], "ood4": [8640001, 8640048]}. Smoke: 8690001-8690030.

## Process
- source freeze before the scoring freeze; scoring freeze >= 600 s before run_start
- one held-out run
- ledger sources must name ARTIFACTS (e.g. results/study-020/SEAL.json), not producing scripts (fix from v0.17.0)
- declare K_0170 in the test-isolation rules
- strip SMOKE from the GTI environment in dry runs
- no GitHub Actions or workflows
- push after every step; no force-push

## What counts as failure
- any gated criterion not meeting its threshold is FAIL and is published as FAIL everywhere
- GLH (c) or (d) FAIL means longer horizons do not make the sequential margin useful at eps 0.02
- GLH (a) or GS_a8 FAIL would refute the conditional lemma or the implementation at long horizons

Labels: claims are Exact / Observed / Simulated / Inferred / Rejected / Open; the predictions here are Inferred or Open.
