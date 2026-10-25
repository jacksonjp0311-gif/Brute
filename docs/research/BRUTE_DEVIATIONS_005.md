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
