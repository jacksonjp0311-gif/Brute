# Alignment check of v0.5.0 (read-only audit, 2026-10-25 07:20–07:30 EDT)

Scope: `main` at `87679e7` and tag `v0.5.0` (→ `8e03e03`). Surfaces checked: the GitHub release notes (`gh release view
v0.5.0`), `README.md`, `HANDOFF.md`, `CHANGELOG.md`, `RELEASE.json`, `results/study-007/{GATES,SEAL,PAIRED_ANALYSIS,
SECOND_IMPLEMENTATION_COUNT,PROB_SECOND_IMPLEMENTATION,REPRODUCIBILITY}.json`, and `experiments/BRUTE_PLAN_007.json`.
Auditor: the same agent that made the release (not independent). Sealed files, tags and frozen files are not changed by
this check. Severity: High = a claim is wrong or a failure is softened; Medium = a stale or misleading status surface;
Low = a labelling or wording gap; Info = no drift.

## Findings

| # | Where | Quote | Severity | Label | Action |
|---|---|---|---|---|---|
| A1 | `HANDOFF.md:7-9`, `:18` (at `87679e7`) | "**Released: v0.4.0** … **In progress: v0.5.0**"; "`main` \| `5c02a7b` = tag v0.4.0" | Medium | Exact (stale status: v0.5.0 was released at `8e03e03`) | Fixed in this errata commit |
| A2 | `HANDOFF.md:3` | "Last updated 2026-10-25 07:12 EDT" | Low | Exact (commit `d0516a0` was made ~07:15 EDT) | Fixed |
| A3 | `HANDOFF.md:120-125` "Roadmap goal" | "Next it needs depth …, a representation beyond enumeration, and breadth" | Low | Exact (stale since v0.5.0 made the region the engine) | Fixed |
| A4 | GitHub release notes, lead table rows 1–3 | "**MET.**", "**PARTLY MET.**", "**NOT DISTINGUISHED.**" | Low | Inferred (MET / PARTLY MET are owner-summary verdicts on priorities, not registered criteria, and carry no evidence label; the gate rows below them are labelled Observed). GM is not gated; G6b fails by its own registered threshold and was predicted to fail independently of M (plan `criteria.G6b_M_coverage_vs_v020.prediction`) | Not edited (notes wording was owner-specified); disclosed here |
| A5 | `README.md:35` | "Every claim in this README carries a label:" | Low | Exact (descriptive sections — How it works, Quickstart, Repository — are unlabelled) | Wording qualified in this errata |
| A6 | `docs/research/BRUTE_DEVIATIONS_007.md` | (no entry) | Low | Exact | Release-time process items (late ledger receipts for `v050_reference`/`v050_prob_reference`; `--no-ff` merge although a fast-forward was possible; release notes edited once at 07:13 EDT; README test section written after the release freeze) were in HANDOFF/ledger notes only. Added as Q8 |
| A7 | `docs/CLAIM_BOUNDARIES.md:1` | "# BGR v0.90 — Scientific claim boundaries" | Low | Exact (the only claim-boundary document is inherited from BGR; Brute's boundaries live in README "What Brute can't do yet", `RELEASE.json.validity` and every notes/tagline "not AGI") | Disclosed; a Brute claim-boundary doc is Open |

## Checked and found consistent (no drift)

- **No auto-promotion (Exact).** M is not the default anywhere: `brute/region_learner.py:38`, `brute/breadth.py:56`,
  `brute/api/service_v050.py:59` all default `policy='LU-R'`. No threshold, τ or budget was changed after `50e9321`
  (`BRUTE_RELEASE_FREEZE_050` locks the scoring scripts; `verify_release_050` regenerates GATES/PAIRED byte-for-byte).
- **Failures published, not tuned (Exact/Observed).** `GATES.json.failed` = [GX2, G3′, G6b] is copied verbatim into
  `RELEASE.json.gates_failed`, README status/gate table, CHANGELOG and release notes; no rerun or redefinition.
- **Numbers (Exact, cross-checked).** 25,344 GX1 steps / 0 mismatches; act3 checked 0.845269; GX3 257/257; G6b
  −0.079591 [−0.099615, −0.060224]; GM +0.026202 [0.010930, 0.042536]; 2,592 arm traces / 0; mutation 20/20;
  reproducibility 296/296; 213 tests — identical in GATES/count JSON, RELEASE.json, README, CHANGELOG and release notes.
- **Labels.** README defines all six labels (Exact/Observed/Simulated/Inferred/Rejected/Open) and labels the status,
  gate, scaling and can't-do surfaces; RELEASE.json and the release notes mark fits as Inferred and gates as Observed.

## Principles: which have a concrete mechanism in the repo

| Principle | Mechanism found | Status |
|---|---|---|
| Evidence-gated action | Certificates only when the region's projection collapses (Y1k + margin + saturation); otherwise ABSTAIN with a reason; SOLVER_BUDGET ⇒ ABSTAIN (GX3) | Exact (code + gates) |
| Claim boundaries on every surface | README can't-do list, RELEASE.json `validity`, "not AGI" tagline and notes | Present; dedicated Brute doc Open (A7) |
| Evidence labels | README label legend; labels on status/gate/discovery surfaces | Present; not on descriptive sections (A5) |
| No auto-promotion | Defaults unchanged; arms are opt-in; promotion would need a new pre-registered study | Exact for v0.5.0; no automated promotion machinery exists to audit |
| Failures published not tuned | Pre-registration, freezes, append-only hash-chained ledger, seals, deviations files | Exact (verifier); self-reported chronology, local unsigned chain |
| Human in the loop | Public certificates require an outside `ScopeAttestation` (`brute/core/learner.py:52`); every release is owner-requested | Partial: there is no approval step in code for releases or merges beyond the owner's chat instructions — **no concrete mechanism** beyond attestation |
| Governed memory | The ledger/manifest/seal chain governs the research record; the learner's only memory is the per-session version space | **No concrete "governed memory" mechanism** for a learner memory exists; the term does not appear in the repo |
| Bounded evolution | Families, caps and policies change only through a new pre-registered plan; no self-modification | Process only (no code enforcing it); the term does not appear in the repo |
