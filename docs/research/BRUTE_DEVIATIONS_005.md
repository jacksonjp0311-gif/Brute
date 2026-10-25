# Recorded deviations: Brute v0.3.0 / study BRUTE-030-CHANGEPOINT-005

Pre-registration: `experiments/BRUTE_PLAN_005.json`, frozen by the commit that adds it on branch `plan/v0.3.0`
(from main `31a348e`). This file lists notes made at the freeze and every change made **after** it. Criteria are never
changed here; an original criterion is always reported as registered. Labels: Exact / Observed / Simulated / Inferred /
Rejected / Open.

## P0. Probe code that existed before the freeze (owner discipline check, 2026-10-25 00:00 EDT)

Exact. Before the plan commit the working tree held three **uncommitted** files, run only on study-004 seeds
(1330001..1390024; design data for v0.3.0). No study-005 seed was generated or run before the plan commit.

| File | sha256 at freeze | Used for |
|---|---|---|
| `brute/changepoint.py` | `0f4f290f…f043` | probe subclass of `ActiveBruteLearner` with switchable resync modes (full, known, unverified, knownunv, fullmin, knownmin, `-pl` = plain LU) and an optional untaken-branch check; picks the certification and policy rule |
| `docs/research/v0.3.0/design_probe/probe.py` | `87d78b36…483e` | runs arms on the 504 study-004 cases, stores per-step taken and counterfactual certificates |
| `docs/research/v0.3.0/design_probe/summarize.py` | `018ef92c…a57a` | per-arm tables (dual coverage, false and non-drift false certificates, log-loss, check/switch rates) |

Probe runs r1–r4 (outputs committed with the plan under `docs/research/v0.3.0/design_probe/outputs/`) are summarised in
the plan's `pre_freeze_disclosure`. `brute/changepoint.py` stays uncommitted until after the plan commit; the committed
version implements only Y1k + LU-R and the CHECK_RUN option, with the probe-only modes removed. Its pre-freeze bytes are
not committed (the hash above identifies them).

## P1. Bridge observations received before the freeze (bridge v0.2 @ `cced586`, not edited)

Recorded in the plan (`bridge_observations`) as implementation and diagnostic inputs; no criterion depends on them.
- O1: bridge untied experiment counts differ from the sealed study-004 traces for unstructured3 (bridge 0, traces
  15.35/case) and drift4 (0 vs 3.68). Open; R3 reports study-005 counts.
- O2: per-call cost on unstructured3 (~0.12 s experiment, ~0.11 s observe). R4 reports it.
- O3: no explicit "no proposal" after OUT_OF_FAMILY. brute.api/1.3 adds `proposal: NO_PROPOSAL`.

## D1. Storage of the sealed traces (same rule as study-004 D1)

Exact. `RESULTS.json` and `SCIENTIFIC.json` exceed GitHub's 100 MB per-file limit. They are committed as deterministic
gzip (level 9, mtime 0, no file name) of the exact sealed bytes (`*.json.gz`) and git-ignored in raw form;
`scripts/study005_storage.py restore` rebuilds them and checks them against `SEAL.json`. The seal is unchanged and binds
the raw bytes. Storage-only; no criterion or scoring rule is affected. `make_gates_005.py` and `make_paired_005.py` call
`ensure_raw()` and regenerate `GATES.json` / `PAIRED_ANALYSIS.json` byte for byte (`--check`).

## N1. Test-suite status at the source freeze and at release (Exact)

At the source freeze (`f7f3bd3`) the full suite ran 167 tests with 1 failure and 3 errors, none in study-005 code:
- 2 pre-existing at tag v0.2.0, by construction (frozen version checks): `test_brute_repro.test_verify_fails_under_tampered_results`
  and `test_release_011.test_fast_verify_passes`;
- 2 manifest-related (the MANIFEST is regenerated only at release): `test_brute_repro.test_manifest_matches_tracked_files`
  and `test_release_020.test_fast_verify_passes`.

At release the MANIFEST is regenerated. `RELEASE.json` moves to 0.3.0, so the frozen `test_release_020.test_fast_verify_passes`
(which asserts `RELEASE.json` version 0.2.0 and the study-004 gate lists) now fails **by construction**, in the same way
the v0.1.x tests did at v0.2.0 (study-004 N1). The unmodified v0.2.0 verifier still passes on the raw v0.2.0 tag tree
(`python -m scripts.verify_release_030 --frozen`). The count measured on a fresh clone is in the README Status table.

## R1. Results that fail a pre-registered gate (reported as registered; nothing changed)

- **G6b coverage non-inferiority vs v0.2.0: FAIL** (pre-registered as expected to fail). A3 − A2 pooled −0.098264,
  CI95 [−0.110885, −0.087267] against the bar ≥ −0.03 with CI lower ≥ −0.05 (design estimate −0.094). This is the
  price of change-robust certification (R1, DISCOVERIES D11).
- **G5 false-alarm limit: FAIL** (not anticipated). ood4: 5 of 72 cases (0.069 > 0.05) raise a RESIDUAL_SURPRISE alarm
  in both A3 and P3 (seeds 1470003, 1470014, 1470022 at mask 0.35; 1470020 at 0.35 and 0.6), while the n≤4 family is still
  supported. The alarm rule and τ are unchanged since v0.1.0; the frozen v0.1.1 control C, A2 and P2 alarm on exactly
  the same 5 cases (153 post-burn-in alarm steps each). Study-004's ood4 seeds had 0. *Inferred:* a tail of the τ
  calibration on these held-out seeds, not a v0.3.0 regression; it is reported as a failure regardless.
- **Extended drift4 block is not perfect for A3** (not gated): 38 false certificates of which 2 at non-drift steps,
  4 stale (step > 12, not a drift step), against A2 62 / 14 / 15 and E2 38 / 12 / 14. The main block is clean
  (A3 9 false, all at drift steps). Pre-registered limitation: Y1k does not protect a jump into a state whose edge for
  the queried action is still unknown.

## R2. Bridge observations (diagnostic only, plan P1)

O1: study-005 R3 reports A3 untied experiments per case unstructured3 9.68 and drift4 1.40 (A2 14.61 / 1.78), so the
sealed traces do have untied experiments on unstructured3; the bridge's 0 is a bridge-side difference (Open, not
investigated here; `/workspace/brute-bridge` not edited). O2: R4 mean per-call cost on unstructured3 is about 1 ms
(observe) and 0.3 ms (experiment) in the study runner (informational, not reproducible). O3: implemented in brute.api/1.3.
