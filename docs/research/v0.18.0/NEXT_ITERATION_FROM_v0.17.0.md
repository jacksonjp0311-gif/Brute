> **Status (2026-10-27):** pre-registered as `experiments/BRUTE_PLAN_020.json` on `plan/v0.18.0` (docs only; not built).

# Brute v0.17.0 → v0.18.0: next iteration (to be pre-registered as BRUTE_PLAN_020 on `plan/v0.18.0`; ledger preregistration_020)

The previous note is in `docs/research/v0.17.0/NEXT_ITERATION_FROM_v0.16.0.md`. Labels are as in the README. Nothing here counts as evidence until it runs on fresh seeds.

## Where v0.17.0 leaves things (Observed, study-019, 12 of 13 gated pass)

- **The sequential margin is sound.** RGNB4 0 false certificates on 240/240 noisy main cases, 0 boundary crossings, CP95 upper bound 0.0124 (GNB a, b PASS). GA3 (3 actions) PASS: RG4_3 0 false at eps 0, RGNB4_3 0 case-false at eps 0.02 (CP95 0.0605).
- **It does not recover coverage (GNB c, d FAIL).** dC(RGNB4 − RGN4) at eps 0.02 = +0.0017 [−0.0005, +0.0041]; C(RGNB4) at eps 0.02 = 0.052 [0.041, 0.065] < 0.10.
- **The gap is not about eps.** C(RGNB4) is 0.055 at eps 0, against RG4 0.453 and the oracle RGN4_or 0.339 at eps 0.02 (Observed). Any margin m ≥ 1 already costs most of the coverage on 44-step traces: with one tolerated mismatch, a wrong hypothesis that differs from the truth on a single observed bit survives and keeps the support non-singleton (Inferred from the eps-0 numbers; not separately measured).
- **All process gates passed**: GS_ref7 (mutation 20/20), G12 152/152, GTI 691 tests, heartbeat max gap 2.0 s, RUN_DONE at 1274 s of 7200 s. Rate math over-projected by 1.5–1.95x.

## What GNB (c) and (d) mean

- **(c)** asked whether recomputing the margin from the bits seen so far certifies more than the fixed planned-bits margin. It did not by a measurable amount: both margins are ≥ 1 almost from the start, and the step from m = 1 to m = 4 matters far less than the step from 0 to 1.
- **(d)** is the usefulness bar carried from study-018 (mean C ≥ 0.10 at eps 0.02 with CI lower > 0.05). Neither tolerant arm has reached it.

## Proposal for v0.18.0 (depth headline; docs only until BRUTE_PLAN_020 is frozen)

1. **Depth (headline GLH): horizon.** A wrong hypothesis gathers mismatches at a rate set by how far it is from the truth; the sequential boundary grows like eps_bar·b + O(√b). On longer traces the separation should open. Run RGNB4 (frozen, v0.17.0) and RGN4 on 88-step traces and score coverage on steps 45–88 at eps 0.02. Gate: soundness (a, b as GNB) and mean late-window C ≥ 0.10 with CI lower > 0.05. Report the per-step coverage curve. *Open.*
2. **Breadth (reported): per-bit partial certificates.** Certify each bit of the 2-bit reading when every surviving hypothesis agrees on it. Same conditional soundness; coverage scored per bit. *Open.*
3. **The same discipline:** fresh seed ranges (86xxxxx), a numpy second implementation, rate math, a source freeze, a scoring freeze ≥ 600 s before run_start, one held-out run under a 2 h cap, a new additive API (`brute.certify/8`) only if needed.

## Fixes carried into BRUTE_PLAN_020

1. Ledger receipts must name the artifact as source (study-019 needed correction receipts for run_end, seal, gates and clean_clone).
2. Declare K_0170 (test_release_0170 version / API / RELEASE.json key tests after the bump) in GTI.
3. Strip SMOKE from the GTI environment in dry runs (study-019's dry-run GTI failed only on that leak).

## No CI

Brute has no `.github` directory and uses no GitHub Actions; add no workflows.
